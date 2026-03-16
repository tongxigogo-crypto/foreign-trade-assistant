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
- `sender_ip_country_if_available`: optional string
- `is_new_customer_hint`: `yes|no|unknown`
- `customer_role_hint`: `trader|engineering_contractor|end_user|unknown`
- `product_direction`: `specified|needs_recommendation|unknown`
- `explicit_problem_or_blocker`: optional string

## Shared Customer Analysis Object (advisory)

- `market_snapshot.region`: string
- `market_snapshot.demand_signals`: string[]
- `market_snapshot.usage_habits`: string[]
- `market_snapshot.market_price_range`: string
- `market_snapshot.china_export_exworks_range`: string
- `company_background.provided_company_name`: string
- `company_background.founding_year`: string
- `company_background.size_band`: string
- `company_background.core_industry`: string
- `company_background.main_products`: string[]
- `company_background.credit_signals`: string[]
- `company_background.confidence`: `low|medium|high|unknown`

## Shared Followup Delta Object

- `change_type`: `new_demand|new_issue|routine_update|unknown`
- `summary`: string
- `best_reply_approach`: string

## Shared Weekly Review Object

- `period_start`: ISO date
- `period_end`: ISO date
- `new_customer_count`: integer
- `existing_customer_updates`: integer
- `open_followups`: integer
- `overdue_followups`: integer
- `blocked_cases`: string[]
- `next_week_plan`: string[]

## Contract Rules

- Specialists must return structured outputs with a `status` field.
- When required fields are missing, return `needs_input` with explicit missing field notes.
- If work is possible with caveats, return `partial` and list assumptions.
- Orchestrator merges specialist outputs; specialists do not assume orchestration ownership.
- Prefer source-of-truth systems over memory or free-form inference.
- Human-readable summaries may accompany structured outputs, but must not replace machine handoff objects.
- Tool-accessible workspace data should be checked before answering questions that may have changed over time.
- Durable corrections, repeated failures, and stable success patterns should be written to the workspace memory file through the global `self-improving-agent`.
- Every production run must append at least one memory entry (`success`, `correction`, or `failure`) without requiring manual reminders.
- Reply-generation outputs are drafts for manual review/edit/send unless the user explicitly requests auto-send.
