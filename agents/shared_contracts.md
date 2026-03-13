# Shared Data Contracts

## Standard Agent Status

- `success`
- `partial`
- `needs_input`
- `failed`

## Shared Inquiry Object (minimum)

- `message_id`: string
- `thread_id`: string
- `date`: ISO 8601 string
- `sender_name`: optional string
- `sender_email`: string
- `company_name`: optional string
- `subject`: string
- `cleaned_body`: string
- `country`: optional string
- `product`: optional string
- `product_specs`: optional string
- `quantity`: optional string
- `unit`: optional string
- `incoterm_if_any`: optional string
- `destination_port_if_any`: optional string
- `contact_details`: optional string
- `detected_intent`: optional string

## Contract Rules

- Specialists must return structured outputs with a `status` field.
- When required fields are missing, return `needs_input` with explicit missing field notes.
- If work is possible with caveats, return `partial` and list assumptions.
- Orchestrator merges specialist outputs; specialists do not assume orchestration ownership.
