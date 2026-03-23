# Trade Assistant MVP

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main init
```

End-user desktop mode (no command line operations after startup):

```powershell
python -m app.main desktop
```

Check runtime version:

```powershell
python -m app.main --version
```

## Build Local Knowledge

```powershell
python -m app.main add-customer --id ali-001 --name "Ali Trading" --region "Dubai" --currency USD --price-floor 12.5
python -m app.main add-product --sku A100 --name "A series valve" --base-price 15 --min-price 12.5
python -m app.main set-preference --tone professional --must-include "Delivery term" "MOQ" --forbidden-terms "guaranteed"
```

Ingest an email thread:

```powershell
python -m app.main ingest-email-thread --path "E:\工作测试\邮件.txt" --confirm-write
```

Ingest multi-model history directory (Gemini / DeepSeek / Doubao / Qwen / ChatGPT / Claude / Kimi):

```powershell
python -m app.main ingest-history-dir --dir "E:\HistoryExports" --recursive --max-files 800 --max-lines-per-file 60 --confirm-write
```

## Local Capsule and Actions

Build capsule:

```powershell
python -m app.main build-capsule --input "Give Ali a quote for A100" --model doubao --format prompt
```

Parse and execute actions:

```powershell
python -m app.main parse-actions --text '<action>generate_quote_draft:{"client":"Ali","product":"A100","price":13.2,"currency":"USD"}</action>'
python -m app.main execute-actions --text '<action>generate_quote_draft:{"client":"Ali","product":"A100","price":13.2,"currency":"USD"}</action>' --confirm-write
```

Notes:
- Duplicate identical action tags are deduplicated before execution.
- Action results now include structured `customer_id/customer_name` context.

## Run Bridge and Dashboard

Start bridge:

```powershell
python -m app.main serve-bridge --host 127.0.0.1 --port 8765 --allow-action-execute
```

Start dashboard:

```powershell
python -m app.main serve-dashboard --host 127.0.0.1 --port 8787
```

Open:
- `http://127.0.0.1:8787`

One-command startup (restart and run both services):

```powershell
powershell -File scripts/start_mvp.ps1
```

## Browser Extension (Chrome + Edge)

This extension is Manifest V3 and works on both Chromium browsers:
- Google Chrome
- Microsoft Edge

Manual install steps:
1. Open extension page:
   - Chrome: `chrome://extensions`
   - Edge: `edge://extensions`
2. Turn on `Developer mode`.
3. Click `Load unpacked`.
4. Select folder: `E:\CodexWorkspace\外贸助理\extension`

After install, open Doubao/DeepSeek/Gemini web page and test by typing `@`.

Dashboard includes:
- KPI summary cards (`Open Tasks`, `Overdue`, `High Priority Open`, `Alerts`)
- `Today Focus` queue (highest-risk actionable tasks)
- `Critical Alerts` (overdue + due-soon risks with snooze)
- Customer lines
- Kanban columns
- Recent events and artifact preview

## Task Commands

List tasks:

```powershell
python -m app.main task-list --limit 50
```

List alerts:

```powershell
python -m app.main alert-list --limit 10
```

Acknowledge/snooze alert:

```powershell
python -m app.main alert-ack --task-id "<task-id>" --snooze-hours 24 --confirm-write
```

Read summary metrics:

```powershell
python -m app.main state-summary
```

Export summary file:

```powershell
python -m app.main export-summary --confirm-write
python -m app.main export-summary --path "E:\CodexWorkspace\外贸助理\local_data\artifacts\summary.json" --confirm-write
```

## Release Utilities

Package extension:

```powershell
python scripts/package_extension.py
```

Smoke checks:

```powershell
python scripts/release_check.py
```

Release checklist:
- `docs/RELEASE_MVP1.md`

Update status:

```powershell
python -m app.main task-update --task-id "<task-id>" --status in_progress --note "Waiting buyer confirmation" --confirm-write
python -m app.main task-update --task-id "<task-id>" --status completed --confirm-write
```

Confirm quote and auto-create reminder:

```powershell
python -m app.main confirm-quote --customer vitor-maia --artifact "E:\CodexWorkspace\外贸助理\local_data\artifacts\quote_Vitor_Maia_xxx.md" --confirm-write
```

## Data Files

- Knowledge base: `local_data/knowledge_base.json`
- Artifacts: `local_data/artifacts/`
- State board: `local_data/state_board.json`

All mutating operations require `--confirm-write`.
