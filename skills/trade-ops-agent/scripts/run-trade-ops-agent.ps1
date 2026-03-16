param(
    [string]$WorkspaceRoot = "",
    [string]$RunDate = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
    $WorkspaceRoot = Join-Path $projectRoot "trade_ops"
}

if ([string]::IsNullOrWhiteSpace($RunDate)) {
    $runDateValue = Get-Date
} else {
    $runDateValue = Get-Date $RunDate
}
$runDateText = $runDateValue.ToString("yyyy-MM-dd")

$inputDir = Join-Path $WorkspaceRoot "input"
$configDir = Join-Path $WorkspaceRoot "config"
$outputDir = Join-Path $WorkspaceRoot "output"
$statePath = Join-Path $WorkspaceRoot "state.json"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

function Read-JsonOrDefault {
    param(
        [string]$Path,
        [hashtable]$Default
    )
    if (Test-Path $Path) {
        return Get-Content -Raw -Path $Path | ConvertFrom-Json
    }
    return $Default
}

function Get-CustomerType {
    param([string]$Message, [int]$Qty)
    $text = ($Message | ForEach-Object { $_.ToLowerInvariant() })
    if ($Qty -ge 1000 -or $text -match "distributor|wholesale|agent|bulk|container|exclusive") {
        return "A-KeyAccount"
    }
    if ($Qty -ge 200 -or $text -match "sample|oem|private label|custom") {
        return "B-Growth"
    }
    return "C-LongTail"
}

function Get-FollowUpPlan {
    param([string]$CustomerType)
    switch ($CustomerType) {
        "A-KeyAccount" { return "D0 quote, D1 call, D3 technical sheet, D7 negotiation" }
        "B-Growth" { return "D0 quote, D2 reminder, D5 offer sample order" }
        default { return "D0 quote, D3 reminder, D7 archive if no response" }
    }
}

function Get-DiscountRate {
    param([int]$Qty)
    if ($Qty -ge 3000) { return 0.18 }
    if ($Qty -ge 1000) { return 0.12 }
    if ($Qty -ge 500) { return 0.08 }
    if ($Qty -ge 200) { return 0.05 }
    return 0.00
}

$pricingRulesPath = Join-Path $configDir "pricing-rules.json"
$pricingRules = Read-JsonOrDefault -Path $pricingRulesPath -Default @{
    fallbackUnitPrice = 5.5
    defaultCurrency = "USD"
    shippingPerOrder = 90
}

$inquiriesPath = Join-Path $inputDir "inquiries.csv"
$catalogPath = Join-Path $inputDir "mic-products.csv"
$pagesPath = Join-Path $inputDir "site-pages.csv"

if (-not (Test-Path $inquiriesPath)) { throw "Missing input file: $inquiriesPath" }
if (-not (Test-Path $catalogPath)) { throw "Missing input file: $catalogPath" }
if (-not (Test-Path $pagesPath)) { throw "Missing input file: $pagesPath" }

$inquiries = Import-Csv -Path $inquiriesPath
$catalog = Import-Csv -Path $catalogPath
$pages = Import-Csv -Path $pagesPath

$processedInquiries = @()
foreach ($row in $inquiries) {
    $qty = 0
    if ($row.request_qty) { $qty = [int]$row.request_qty }
    $unitPrice = if ($row.base_unit_price) { [double]$row.base_unit_price } else { [double]$pricingRules.fallbackUnitPrice }
    $discount = Get-DiscountRate -Qty $qty
    $finalUnitPrice = [math]::Round($unitPrice * (1 - $discount), 2)
    $productAmount = [math]::Round($finalUnitPrice * $qty, 2)
    $shipping = [double]$pricingRules.shippingPerOrder
    $totalAmount = [math]::Round($productAmount + $shipping, 2)
    $customerType = Get-CustomerType -Message $row.inquiry_message -Qty $qty
    $followUp = Get-FollowUpPlan -CustomerType $customerType

    $emailBody = @"
Subject: Quotation for $($row.product_name)

Hi $($row.contact_name),

Thanks for your inquiry. Based on your requested quantity ($qty pcs), please find our quote:
- Product: $($row.product_name)
- Unit Price: $finalUnitPrice $($pricingRules.defaultCurrency)
- Product Amount: $productAmount $($pricingRules.defaultCurrency)
- Shipping: $shipping $($pricingRules.defaultCurrency)
- Total: $totalAmount $($pricingRules.defaultCurrency)
- Lead Time: 10-15 days
- Payment: T/T

If you confirm target specs and shipping address, we can issue a PI today.

Best regards,
Sales Team
"@

    $processedInquiries += [pscustomobject]@{
        inquiry_id = $row.inquiry_id
        company_name = $row.company_name
        contact_name = $row.contact_name
        product_name = $row.product_name
        request_qty = $qty
        customer_type = $customerType
        follow_up_plan = $followUp
        unit_price = $finalUnitPrice
        total_price = $totalAmount
        quote_currency = $pricingRules.defaultCurrency
        email_draft = $emailBody.Trim()
    }
}

$analysisPath = Join-Path $outputDir ("customer-analysis-" + $runDateText + ".md")
$keyCount = @($processedInquiries | Where-Object { $_.customer_type -eq "A-KeyAccount" }).Count
$growthCount = @($processedInquiries | Where-Object { $_.customer_type -eq "B-Growth" }).Count
$longTailCount = @($processedInquiries | Where-Object { $_.customer_type -eq "C-LongTail" }).Count

$analysisMd = @"
# Customer Analysis - $runDateText

- Total inquiries: $($processedInquiries.Count)
- A-KeyAccount: $keyCount
- B-Growth: $growthCount
- C-LongTail: $longTailCount

## Priority Actions
- Focus first on A-KeyAccount with call + technical response in 24h.
- Convert B-Growth with sample offer and lead-time commitment.
- Use batch follow-up for C-LongTail to control time cost.
"@
Set-Content -Path $analysisPath -Value $analysisMd -Encoding UTF8

$quotePath = Join-Path $outputDir ("inquiry-quote-pack-" + $runDateText + ".csv")
$processedInquiries | Select-Object inquiry_id,company_name,contact_name,product_name,request_qty,customer_type,follow_up_plan,unit_price,total_price,quote_currency,email_draft | Export-Csv -Path $quotePath -NoTypeInformation -Encoding UTF8

$state = Read-JsonOrDefault -Path $statePath -Default @{ mic_last_index = 0 }
$startIndex = [int]$state.mic_last_index
$dailyCount = 40

if ($catalog.Count -eq 0) { throw "mic-products.csv is empty." }

$micToday = @()
for ($i = 0; $i -lt $dailyCount; $i++) {
    $idx = ($startIndex + $i) % $catalog.Count
    $micToday += $catalog[$idx]
}

$newIndex = ($startIndex + $dailyCount) % $catalog.Count
$newState = @{ mic_last_index = $newIndex }
$newState | ConvertTo-Json | Set-Content -Path $statePath -Encoding UTF8

$micOutputPath = Join-Path $outputDir ("mic-daily-40-" + $runDateText + ".csv")
$micToday | Select-Object product_id,product_name,mic_url,target_market,owner | Export-Csv -Path $micOutputPath -NoTypeInformation -Encoding UTF8

$siteTasks = @()
foreach ($page in $pages) {
    $needsText = ($page.needs_content -eq "1")
    $needsImage = ($page.needs_image -eq "1")
    if (-not ($needsText -or $needsImage)) { continue }

    $task = [pscustomobject]@{
        page_slug = $page.page_slug
        page_url = $page.page_url
        content_task = if ($needsText) { "Rewrite with stronger value proposition, 3 benefit bullets, CTA at top and bottom." } else { "" }
        image_task = if ($needsImage) { "Add 1 hero image + 2 detail images; keep style industrial, clean background, product focus." } else { "" }
        seo_keyword = $page.seo_keyword
        publish_priority = if ($page.priority) { $page.priority } else { "medium" }
    }
    $siteTasks += $task
}

$siteTaskPath = Join-Path $outputDir ("site-update-tasks-" + $runDateText + ".csv")
$siteTasks | Export-Csv -Path $siteTaskPath -NoTypeInformation -Encoding UTF8

$summaryPath = Join-Path $outputDir ("run-summary-" + $runDateText + ".md")
$summary = @"
# Trade Ops Agent Run Summary ($runDateText)

- Inquiry pack: $quotePath
- Customer analysis: $analysisPath
- MIC daily list (40): $micOutputPath
- Site update tasks: $siteTaskPath
- Next MIC start index: $newIndex
"@
Set-Content -Path $summaryPath -Value $summary -Encoding UTF8

Write-Output "Completed run for $runDateText"
Write-Output "Summary file: $summaryPath"


