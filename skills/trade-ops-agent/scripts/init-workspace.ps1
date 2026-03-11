param(
    [string]$WorkspaceRoot = "D:/Backup/Documents/Playground/trade_ops"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$inputDir = Join-Path $WorkspaceRoot "input"
$configDir = Join-Path $WorkspaceRoot "config"
$outputDir = Join-Path $WorkspaceRoot "output"

New-Item -ItemType Directory -Force -Path $WorkspaceRoot,$inputDir,$configDir,$outputDir | Out-Null

$inquiriesCsv = @"
inquiry_id,company_name,contact_name,product_name,request_qty,base_unit_price,inquiry_message
INQ-001,Northline Trading,Anna,Hydraulic Fitting,1200,4.8,"We are distributor and need long-term supply for 1200 pcs monthly."
INQ-002,Beta Industrial,Sam,Steel Valve,320,8.5,"Need OEM customization and sample first."
INQ-003,QuickParts,Leo,Pipe Clamp,80,2.2,"Please send your best price and delivery time."
"@
Set-Content -Path (Join-Path $inputDir "inquiries.csv") -Value $inquiriesCsv -Encoding UTF8

$micCsv = @"
product_id,product_name,mic_url,target_market,owner
P-001,Hydraulic Fitting,https://example.com/mic/p-001,US,Amy
P-002,Steel Valve,https://example.com/mic/p-002,EU,Amy
P-003,Pipe Clamp,https://example.com/mic/p-003,SEA,Tom
P-004,Brass Adapter,https://example.com/mic/p-004,US,Tom
P-005,Oil Seal,https://example.com/mic/p-005,EU,Lisa
P-006,Check Valve,https://example.com/mic/p-006,SEA,Lisa
P-007,Thread Coupling,https://example.com/mic/p-007,US,Amy
P-008,Tube Connector,https://example.com/mic/p-008,EU,Tom
P-009,Pressure Gauge,https://example.com/mic/p-009,SEA,Lisa
P-010,Ball Valve,https://example.com/mic/p-010,US,Amy
"@
Set-Content -Path (Join-Path $inputDir "mic-products.csv") -Value $micCsv -Encoding UTF8

$pagesCsv = @"
page_slug,page_url,seo_keyword,needs_content,needs_image,priority
home,https://example.com,industrial fittings supplier,1,1,high
hydraulic-fittings,https://example.com/hydraulic-fittings,hydraulic fitting manufacturer,1,1,high
steel-valves,https://example.com/steel-valves,steel valve wholesale,1,0,medium
contact,https://example.com/contact,contact industrial supplier,0,1,low
"@
Set-Content -Path (Join-Path $inputDir "site-pages.csv") -Value $pagesCsv -Encoding UTF8

$pricingJson = @"
{
  "fallbackUnitPrice": 5.5,
  "defaultCurrency": "USD",
  "shippingPerOrder": 90
}
"@
Set-Content -Path (Join-Path $configDir "pricing-rules.json") -Value $pricingJson -Encoding UTF8

$stateJson = @"
{
  "mic_last_index": 0
}
"@
Set-Content -Path (Join-Path $WorkspaceRoot "state.json") -Value $stateJson -Encoding UTF8

Write-Output "Initialized workspace: $WorkspaceRoot"

