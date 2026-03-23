from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from .action_protocol import ActionExecutor, dedupe_actions, parse_actions
from .bridge_server import run_bridge_server
from .capsule_builder import CapsuleBuilder
from .config import AppConfig
from .contracts import ActionExecutionResult, CapsuleRequest, CustomerProfile, ProductRecord, UserPreference
from .dashboard_server import run_dashboard_server
from .desktop_app import run_desktop_window
from .email_thread_parser import parse_email_thread_file
from .history_importer import ingest_history_directory
from .local_store import LocalKnowledgeStore, extract_facts_from_text_file, slugify_id
from .orchestrator import TradeAssistantOrchestrator
from .state_board import StateBoard
from .user_settings import UserSettingsStore
from .version import APP_VERSION


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trade assistant local runtime CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize local knowledge base")

    add_customer = subparsers.add_parser("add-customer", help="Add or update customer profile")
    add_customer.add_argument("--id", required=True, help="Customer id")
    add_customer.add_argument("--name", required=True, help="Customer name")
    add_customer.add_argument("--region", default="", help="Customer region")
    add_customer.add_argument("--currency", default="USD", help="Customer currency")
    add_customer.add_argument("--price-floor", type=float, default=None, help="Optional price floor")

    add_product = subparsers.add_parser("add-product", help="Add or update product info")
    add_product.add_argument("--sku", required=True, help="Product sku")
    add_product.add_argument("--name", required=True, help="Product name")
    add_product.add_argument("--currency", default="USD", help="Price currency")
    add_product.add_argument("--base-price", type=float, default=None, help="Reference price")
    add_product.add_argument("--min-price", type=float, default=None, help="Minimum allowed price")

    set_pref = subparsers.add_parser("set-preference", help="Update user communication preference")
    set_pref.add_argument("--tone", default="professional")
    set_pref.add_argument("--must-include", nargs="*", default=[])
    set_pref.add_argument("--forbidden-terms", nargs="*", default=[])
    set_pref.add_argument("--pricing-rules", nargs="*", default=[])

    ingest_file = subparsers.add_parser("ingest-file", help="Ingest local text file facts into knowledge base")
    ingest_file.add_argument("--path", required=True, help="Path to text or markdown file")
    ingest_file.add_argument("--max-lines", type=int, default=50)
    ingest_file.add_argument("--confirm-write", action="store_true")

    ingest_mail = subparsers.add_parser("ingest-email-thread", help="Parse and ingest an email thread file")
    ingest_mail.add_argument("--path", required=True, help="Path to exported email thread text file")
    ingest_mail.add_argument("--customer-id", default="", help="Optional customer id override")
    ingest_mail.add_argument("--confirm-write", action="store_true")

    ingest_history = subparsers.add_parser("ingest-history-dir", help="Ingest multi-model history directory")
    ingest_history.add_argument("--dir", required=True, help="Root folder that contains model history files")
    ingest_history.add_argument("--recursive", action="store_true", help="Scan subfolders recursively")
    ingest_history.add_argument("--max-files", type=int, default=500, help="Max files scanned in one run")
    ingest_history.add_argument("--max-lines-per-file", type=int, default=80, help="Max extracted lines per file")
    ingest_history.add_argument("--confirm-write", action="store_true")

    capsule = subparsers.add_parser("build-capsule", help="Build prompt capsule for web model input")
    capsule.add_argument("--input", required=True, help="User message")
    capsule.add_argument("--customer", default="", help="Optional customer hint")
    capsule.add_argument("--product", default="", help="Optional product hint")
    capsule.add_argument("--model", default="", help="Optional target model name")
    capsule.add_argument("--format", choices=["json", "prompt"], default="json")

    parse = subparsers.add_parser("parse-actions", help="Parse action tags from model output")
    parse.add_argument("--text", default="", help="Raw model output text")
    parse.add_argument("--from-file", default="", help="Read model output from file")

    execute = subparsers.add_parser("execute-actions", help="Execute parsed actions against local runtime")
    execute.add_argument("--text", default="", help="Raw model output text")
    execute.add_argument("--from-file", default="", help="Read model output from file")
    execute.add_argument("--confirm-write", action="store_true")

    confirm_quote = subparsers.add_parser("confirm-quote", help="Confirm quote sent and schedule reminder follow-up")
    confirm_quote.add_argument("--customer", required=True, help="Customer name or id")
    confirm_quote.add_argument("--artifact", default="", help="Optional quote artifact path")
    confirm_quote.add_argument("--confirm-write", action="store_true")

    serve = subparsers.add_parser("serve-bridge", help="Run localhost bridge for browser extension")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--allow-action-execute", action="store_true")

    state = subparsers.add_parser("state-latest", help="Read latest execution events from local state board")
    state.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("state-summary", help="Read summary metrics from local state board")

    export_summary = subparsers.add_parser("export-summary", help="Export summary metrics to a local JSON file")
    export_summary.add_argument("--path", default="", help="Optional output path (.json). Defaults to artifacts directory.")
    export_summary.add_argument("--confirm-write", action="store_true")

    tasks = subparsers.add_parser("task-list", help="List local follow-up tasks")
    tasks.add_argument("--limit", type=int, default=100)

    alerts = subparsers.add_parser("alert-list", help="List critical alerts (overdue or due-soon high priority)")
    alerts.add_argument("--limit", type=int, default=10)

    alert_ack = subparsers.add_parser("alert-ack", help="Snooze a critical alert for a task")
    alert_ack.add_argument("--task-id", required=True)
    alert_ack.add_argument("--snooze-hours", type=int, default=24)
    alert_ack.add_argument("--confirm-write", action="store_true")

    task_update = subparsers.add_parser("task-update", help="Update task status")
    task_update.add_argument("--task-id", required=True)
    task_update.add_argument("--status", choices=["waiting_reply", "in_progress", "completed"], required=True)
    task_update.add_argument("--note", default="")
    task_update.add_argument("--confirm-write", action="store_true")

    dashboard = subparsers.add_parser("serve-dashboard", help="Run local dashboard UI for state board")
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8787)
    dashboard.add_argument("--open-browser", action="store_true")

    subparsers.add_parser("desktop", help="Run desktop client window (no command line needed for end users)")

    return parser


def run_cli(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    root = Path(os.getenv("TRADE_ASSISTANT_ROOT", Path(__file__).resolve().parents[1]))
    config = AppConfig.load(root)
    settings_store = UserSettingsStore(config.user_settings_file)
    runtime_settings = settings_store.load()
    effective_output_dir = Path(runtime_settings.output_dir).expanduser().resolve() if runtime_settings.output_dir else config.output_dir
    store = LocalKnowledgeStore(config.knowledge_file)
    capsule_builder = CapsuleBuilder(store=store)
    action_executor = ActionExecutor(store=store, output_dir=effective_output_dir)
    orchestrator = TradeAssistantOrchestrator(capsule_builder=capsule_builder, action_executor=action_executor)
    state_board = StateBoard(config.state_board_file)

    if args.command == "init":
        store.ensure_initialized()
        print(json.dumps({"status": "initialized", "knowledge_file": str(config.knowledge_file)}, ensure_ascii=False))
        return 0

    if args.command == "add-customer":
        customer = CustomerProfile(
            customer_id=args.id,
            name=args.name,
            region=args.region,
            currency=args.currency,
            price_floor=args.price_floor,
        )
        kb = store.upsert_customer(customer)
        print(json.dumps({"status": "ok", "customers": len(kb.customers)}, ensure_ascii=False))
        return 0

    if args.command == "add-product":
        product = ProductRecord(
            sku=args.sku,
            name=args.name,
            currency=args.currency,
            base_price=args.base_price,
            min_price=args.min_price,
        )
        kb = store.upsert_product(product)
        print(json.dumps({"status": "ok", "products": len(kb.products)}, ensure_ascii=False))
        return 0

    if args.command == "set-preference":
        preference = UserPreference(
            tone=args.tone,
            must_include=list(args.must_include),
            forbidden_terms=list(args.forbidden_terms),
            pricing_rules=list(args.pricing_rules),
        )
        store.update_preference(preference)
        print(json.dumps({"status": "ok", "tone": preference.tone}, ensure_ascii=False))
        return 0

    if args.command == "ingest-file":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Ingestion modifies local knowledge base. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        facts = extract_facts_from_text_file(Path(args.path), max_lines=args.max_lines)
        kb = store.append_doc_facts(facts)
        print(json.dumps({"status": "ok", "ingested_facts": len(facts), "total_doc_facts": len(kb.doc_facts)}, ensure_ascii=False))
        return 0

    if args.command == "ingest-email-thread":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Email thread ingestion modifies local knowledge base and state board. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        parsed = parse_email_thread_file(Path(args.path))
        customer_name = parsed.customer_name or "Unknown Customer"
        customer_id = args.customer_id.strip() or slugify_id(customer_name)
        existing = store.find_customer(customer_id)
        customer = existing or CustomerProfile(customer_id=customer_id, name=customer_name)
        customer.name = customer_name or customer.name
        customer.region = parsed.country_or_region or customer.region
        if parsed.customer_email and parsed.customer_email not in customer.notes:
            customer.notes.append(f"Email: {parsed.customer_email}")
        if parsed.customer_phone and parsed.customer_phone not in customer.notes:
            customer.notes.append(f"Phone: {parsed.customer_phone}")
        for issue in parsed.issues:
            if issue not in customer.last_issues:
                customer.last_issues.append(issue)
        for tag in ["email_thread_ingested"] + parsed.trade_terms:
            if tag and tag not in customer.tags:
                customer.tags.append(tag)
        store.upsert_customer(customer)

        for sku in parsed.products:
            if not store.find_product(sku):
                store.upsert_product(ProductRecord(sku=sku, name=sku))

        kb = store.append_doc_facts(parsed.summary_facts)
        ingest_result = ActionExecutionResult(
            status="success",
            message=f"Ingested email thread for {customer.name}; detected {len(parsed.products)} products.",
            artifacts=[str(config.knowledge_file)],
        )
        event = state_board.append_execution(
            action_name="ingest_email_thread",
            results=[ingest_result],
        )
        transitioned = state_board.transition_customer_tasks(
            customer_id=customer_id,
            to_status="in_progress",
            note="Auto-progressed by new inbound email reply detection.",
            from_statuses=("waiting_reply", "overdue"),
            max_items=2,
        )
        task = state_board.create_followup_task(
            customer_id=customer_id,
            customer_name=customer.name,
            title=f"Follow up inquiry thread for {customer.name}",
            due_in_days=3,
            priority="high" if parsed.issues else "normal",
            source_event_id=event["event_id"],
            initial_status="in_progress",
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "customer_id": customer_id,
                    "customer_name": customer.name,
                    "products_detected": parsed.products,
                    "facts_added": len(parsed.summary_facts),
                    "total_doc_facts": len(kb.doc_facts),
                    "state_event_id": event["event_id"],
                    "task_id": task["task_id"],
                    "auto_transitioned_task_ids": [item["task_id"] for item in transitioned],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "ingest-history-dir":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "History directory ingestion modifies local knowledge base. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        root_dir = Path(args.dir).expanduser().resolve()
        if not root_dir.exists() or not root_dir.is_dir():
            print(json.dumps({"status": "failed", "message": f"Directory not found: {root_dir}"}, ensure_ascii=False))
            return 1
        stats = ingest_history_directory(
            store=store,
            directory=root_dir,
            recursive=bool(args.recursive),
            max_files=max(1, int(args.max_files)),
            max_lines_per_file=max(5, int(args.max_lines_per_file)),
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "directory": str(root_dir),
                    "stats": stats.to_dict(),
                    "knowledge_file": str(config.knowledge_file),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "build-capsule":
        capsule = orchestrator.build_capsule(
            CapsuleRequest(
                user_input=args.input,
                customer_hint=args.customer,
                product_hint=args.product,
                model_name=args.model,
            )
        )
        if args.format == "prompt":
            _safe_print(capsule.injected_prompt)
        else:
            print(json.dumps(capsule.to_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "parse-actions":
        raw_text = _load_text(args.text, args.from_file)
        commands = [item.to_dict() for item in dedupe_actions(parse_actions(raw_text))]
        print(json.dumps({"count": len(commands), "actions": commands}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "execute-actions":
        raw_text = _load_text(args.text, args.from_file)
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Action execution may write files. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        parsed = dedupe_actions(orchestrator.parse_actions(raw_text))
        executed = orchestrator.execute_actions(raw_text)
        event = state_board.append_execution(
            action_name=parsed[0].name if parsed else "unknown",
            results=executed,
        )
        if parsed and parsed[0].name == "generate_quote_draft":
            first_result = executed[0].to_dict() if executed else {}
            context = first_result.get("context", {}) if isinstance(first_result.get("context", {}), dict) else {}
            customer_id = str(context.get("customer_id", "")).strip()
            customer_name = str(context.get("customer_name", "")).strip()
            if not customer_id:
                client = str(parsed[0].payload.get("client", "")).strip() or str(parsed[0].payload.get("customer", "")).strip()
                customer = store.find_customer(client) if client else None
                customer_id = customer.customer_id if customer else slugify_id(client or "unknown_customer")
                customer_name = customer.name if customer else (client or "Unknown Customer")
            state_board.create_followup_task(
                customer_id=customer_id,
                customer_name=customer_name,
                title=f"Follow up quote response for {customer_name}",
                due_in_days=2,
                priority="high",
                source_event_id=event["event_id"],
            )
        results = [result.to_dict() for result in executed]
        print(json.dumps({"count": len(results), "results": results, "state_event": event}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "confirm-quote":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Quote confirmation modifies local state board. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        hint = args.customer.strip()
        customer = store.find_customer(hint)
        customer_id = customer.customer_id if customer else slugify_id(hint or "unknown_customer")
        customer_name = customer.name if customer else (hint or "Unknown Customer")
        moved = state_board.transition_customer_tasks(
            customer_id=customer_id,
            to_status="completed",
            note=f"Quote confirmed by user. Artifact: {args.artifact}".strip(),
            from_statuses=("in_progress", "waiting_reply", "overdue"),
            max_items=2,
        )
        reminder = state_board.create_followup_task(
            customer_id=customer_id,
            customer_name=customer_name,
            title=f"Reminder follow-up after quote confirmation for {customer_name}",
            due_in_days=2,
            priority="high",
            source_event_id="manual_confirm_quote",
            initial_status="waiting_reply",
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "customer_id": customer_id,
                    "completed_task_ids": [item["task_id"] for item in moved],
                    "reminder_task_id": reminder["task_id"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "serve-bridge":
        run_bridge_server(
            orchestrator=orchestrator,
            state_board=state_board,
            host=args.host,
            port=args.port,
            allow_action_execute=bool(args.allow_action_execute),
        )
        return 0

    if args.command == "state-latest":
        events = state_board.latest(limit=max(1, min(int(args.limit), 100)))
        print(json.dumps({"count": len(events), "events": events}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "state-summary":
        print(json.dumps({"summary": state_board.summary()}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "export-summary":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Export writes local files. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        summary = state_board.summary()
        if args.path.strip():
            output_path = Path(args.path.strip())
        else:
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            output_path = config.output_dir / f"state_summary_{ts}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"summary": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "ok", "path": str(output_path)}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "task-list":
        items = state_board.list_tasks(limit=max(1, min(int(args.limit), 500)))
        print(json.dumps({"count": len(items), "tasks": items}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "alert-list":
        rows = state_board.alerts(limit=max(1, min(int(args.limit), 100)))
        print(json.dumps({"count": len(rows), "alerts": rows}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "alert-ack":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Alert acknowledge modifies local state board. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        ack = state_board.ack_alert(
            task_id=args.task_id,
            snooze_hours=max(1, min(int(args.snooze_hours), 168)),
        )
        if ack is None:
            print(json.dumps({"status": "failed", "message": "task not found"}, ensure_ascii=False))
            return 1
        print(json.dumps({"status": "ok", "ack": ack}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "task-update":
        if not args.confirm_write:
            print(
                json.dumps(
                    {
                        "status": "needs_confirmation",
                        "message": "Task update modifies local state board. Re-run with --confirm-write.",
                    },
                    ensure_ascii=False,
                )
            )
            return 2
        updated = state_board.update_task_status(
            task_id=args.task_id,
            status=args.status,
            note=args.note,
        )
        if updated is None:
            print(json.dumps({"status": "failed", "message": "task not found or invalid status"}, ensure_ascii=False))
            return 1
        print(json.dumps({"status": "ok", "task": updated}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "serve-dashboard":
        run_dashboard_server(
            state_board=state_board,
            action_executor=action_executor,
            settings_store=settings_store,
            host=args.host,
            port=args.port,
            open_browser=bool(args.open_browser),
        )
        return 0

    if args.command == "desktop":
        return run_desktop_window(config=config)

    return 0


def _load_text(text: str, from_file: str) -> str:
    if text:
        return text
    if from_file:
        return Path(from_file).read_text(encoding="utf-8")
    return ""


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv[1:]))
