# Input File Schema

## inquiries.csv
Required columns:
- inquiry_id
- company_name
- contact_name
- product_name
- request_qty
- base_unit_price
- inquiry_message

## mic-products.csv
Required columns:
- product_id
- product_name
- mic_url
- target_market
- owner

## site-pages.csv
Required columns:
- page_slug
- page_url
- seo_keyword
- needs_content (0 or 1)
- needs_image (0 or 1)
- priority (high/medium/low)

## pricing-rules.json
Required keys:
- fallbackUnitPrice
- defaultCurrency
- shippingPerOrder

## state.json
Required keys:
- mic_last_index
