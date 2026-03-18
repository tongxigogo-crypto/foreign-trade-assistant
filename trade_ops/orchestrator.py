#!/usr/bin/env python3
"""Foreign trade assistant orchestrator.

Default mode is preview-only. Use --confirm-writes to allow writing outputs
and state updates.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_AGENTS = [
    "orchestrator",
    "email_agent",
    "quotation_agent",
    "crm_agent",
    "followup_agent",
    "research_agent",
]

VALID_STATUSES = {"pending", "running", "blocked", "needs_confirmation", "done", "failed"}


@dataclass
class OrchestratorConfig:
    root_dir: Path
    run_date: str
    confirm_writes: bool
    run_id: str


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv_rows(path: Path, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def ensure_state_shape(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("version", "1.0")
    state.setdefault("mic_last_index", 0)
    state.setdefault("workflow", {"status": "pending", "last_run_id": None, "last_run_date": None})
    state.setdefault("runs", [])
    return state


def set_workflow_status(state: Dict[str, Any], status: str, run_id: str, run_date: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid workflow status: {status}")
    state["workflow"] = {
        "status": status,
        "last_run_id": run_id,
        "last_run_date": run_date,
    }


def build_agent_result(
    agent: str,
    status: str,
    payload: Dict[str, Any] | None = None,
    missing_data: List[str] | None = None,
) -> Dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid agent status: {status}")
    return {
        "agent": agent,
        "status": status,
        "payload": payload or {},
        "missing_data": missing_data or [],
    }


def email_agent(inquiries: List[Dict[str, str]]) -> Dict[str, Any]:
    required_fields = ["inquiry_id", "company_name", "contact_name", "product_name", "request_qty"]
    missing = []
    for row in inquiries:
        for field in required_fields:
            if not row.get(field):
                missing.append(f"{row.get('inquiry_id', 'unknown')} missing {field}")
    status = "blocked" if missing else "done"
    return build_agent_result("email_agent", status, payload={"inquiries": inquiries}, missing_data=missing)


def quotation_agent(
    inquiries: List[Dict[str, str]],
    pricing_rules: Dict[str, Any],
) -> Dict[str, Any]:
    fallback_price = float(pricing_rules["fallbackUnitPrice"])
    shipping_per_order = float(pricing_rules["shippingPerOrder"])
    currency = pricing_rules.get("defaultCurrency", "USD")

    quotes: List[Dict[str, Any]] = []
    for row in inquiries:
        qty = int(float(row.get("request_qty") or 0))
        base_price = row.get("base_unit_price")
        unit_price = float(base_price) if base_price not in (None, "", "null") else fallback_price
        total = round(qty * unit_price + shipping_per_order, 2)
        quotes.append(
            {
                "inquiry_id": row["inquiry_id"],
                "company_name": row["company_name"],
                "product_name": row["product_name"],
                "request_qty": qty,
                "unit_price": round(unit_price, 2),
                "shipping_per_order": round(shipping_per_order, 2),
                "currency": currency,
                "total_price": total,
            }
        )

    return build_agent_result("quotation_agent", "done", payload={"quotes": quotes})


def crm_agent(inquiries: List[Dict[str, str]]) -> Dict[str, Any]:
    customer_rows: List[Dict[str, Any]] = []
    counts = {"A-KeyAccount": 0, "B-Growth": 0, "C-LongTail": 0}
    for row in inquiries:
        qty = int(float(row.get("request_qty") or 0))
        if qty >= 1000:
            tier = "A-KeyAccount"
        elif qty >= 300:
            tier = "B-Growth"
        else:
            tier = "C-LongTail"
        counts[tier] += 1
        customer_rows.append(
            {
                "inquiry_id": row["inquiry_id"],
                "company_name": row["company_name"],
                "tier": tier,
            }
        )
    payload = {"customers": customer_rows, "tier_counts": counts, "total_inquiries": len(inquiries)}
    return build_agent_result("crm_agent", "done", payload=payload)


def followup_agent(quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
    followups = []
    for quote in quotes:
        if quote["request_qty"] >= 1000:
            channel = "email+call"
            sla = "24h"
        elif quote["request_qty"] >= 300:
            channel = "email"
            sla = "48h"
        else:
            channel = "batch_email"
            sla = "72h"
        followups.append(
            {
                "inquiry_id": quote["inquiry_id"],
                "recommended_channel": channel,
                "response_sla": sla,
                "draft_only": True,
            }
        )
    return build_agent_result("followup_agent", "done", payload={"followups": followups})


def research_agent(
    mic_products: List[Dict[str, str]],
    site_pages: List[Dict[str, str]],
    mic_last_index: int,
) -> Dict[str, Any]:
    batch_size = 40
    if not mic_products:
        mic_daily = []
        next_index = 0
    else:
        selected: List[Dict[str, str]] = []
        idx = mic_last_index % len(mic_products)
        for _ in range(min(batch_size, len(mic_products))):
            selected.append(mic_products[idx])
            idx = (idx + 1) % len(mic_products)
        mic_daily = selected
        next_index = idx

    site_updates = [
        {
            "page_slug": row["page_slug"],
            "page_url": row["page_url"],
            "seo_keyword": row["seo_keyword"],
            "priority": row["priority"],
            "content_task": "write" if row.get("needs_content") == "1" else "skip",
            "image_task": "create" if row.get("needs_image") == "1" else "skip",
        }
        for row in site_pages
    ]

    payload = {"mic_daily": mic_daily, "site_updates": site_updates, "next_mic_index": next_index}
    return build_agent_result("research_agent", "done", payload=payload)


def build_customer_analysis_markdown(run_date: str, crm_payload: Dict[str, Any]) -> str:
    counts = crm_payload["tier_counts"]
    lines = [
        f"# Customer Analysis - {run_date}",
        "",
        f"- Total inquiries: {crm_payload['total_inquiries']}",
        f"- A-KeyAccount: {counts['A-KeyAccount']}",
        f"- B-Growth: {counts['B-Growth']}",
        f"- C-LongTail: {counts['C-LongTail']}",
        "",
        "## Priority Actions",
        "- Focus first on A-KeyAccount with call + technical response in 24h.",
        "- Convert B-Growth with sample offer and lead-time commitment.",
        "- Use batch follow-up for C-LongTail to control time cost.",
        "",
    ]
    return "\n".join(lines)


def build_run_summary_markdown(run_date: str, output_paths: Dict[str, Path], next_mic_index: int) -> str:
    lines = [
        f"# Trade Ops Agent Run Summary ({run_date})",
        "",
        f"- Inquiry pack: {output_paths['inquiry_quote_pack']}",
        f"- Customer analysis: {output_paths['customer_analysis']}",
        f"- MIC daily list (40): {output_paths['mic_daily_40']}",
        f"- Site update tasks: {output_paths['site_update_tasks']}",
        f"- Next MIC start index: {next_mic_index}",
        "",
    ]
    return "\n".join(lines)


def run_orchestration(config: OrchestratorConfig) -> Dict[str, Any]:
    root = config.root_dir
    input_dir = root / "trade_ops" / "input"
    output_dir = root / "trade_ops" / "output"
    config_dir = root / "trade_ops" / "config"
    state_path = root / "trade_ops" / "state.json"

    state = ensure_state_shape(load_json(state_path))
    set_workflow_status(state, "running", config.run_id, config.run_date)

    inquiries = read_csv_rows(input_dir / "inquiries.csv")
    mic_products = read_csv_rows(input_dir / "mic-products.csv")
    site_pages = read_csv_rows(input_dir / "site-pages.csv")
    pricing_rules = load_json(config_dir / "pricing-rules.json")

    agent_results = []
    agent_results.append(email_agent(inquiries))
    agent_results.append(quotation_agent(inquiries, pricing_rules))
    agent_results.append(crm_agent(inquiries))
    agent_results.append(followup_agent(agent_results[1]["payload"]["quotes"]))
    agent_results.append(research_agent(mic_products, site_pages, int(state.get("mic_last_index", 0))))

    blocked_agents = [x for x in agent_results if x["status"] in {"blocked", "failed"}]

    run_report: Dict[str, Any] = {
        "run_id": config.run_id,
        "run_date": config.run_date,
        "required_agents": REQUIRED_AGENTS,
        "agent_results": agent_results,
        "needs_confirmation": not config.confirm_writes,
        "mode": "confirm_write" if config.confirm_writes else "preview",
        "timestamp_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    if blocked_agents:
        set_workflow_status(state, "blocked", config.run_id, config.run_date)
        run_report["status"] = "blocked"
        run_report["blocked_agents"] = [x["agent"] for x in blocked_agents]
        run_report["missing_data"] = [item for x in blocked_agents for item in x.get("missing_data", [])]
        if config.confirm_writes:
            state["runs"].append(
                {
                    "run_id": config.run_id,
                    "run_date": config.run_date,
                    "status": "blocked",
                    "mode": "confirm_write",
                }
            )
            save_json(state_path, state)
        return run_report

    quote_rows = agent_results[1]["payload"]["quotes"]
    crm_payload = agent_results[2]["payload"]
    research_payload = agent_results[4]["payload"]

    output_paths = {
        "inquiry_quote_pack": output_dir / f"inquiry-quote-pack-{config.run_date}.csv",
        "customer_analysis": output_dir / f"customer-analysis-{config.run_date}.md",
        "mic_daily_40": output_dir / f"mic-daily-40-{config.run_date}.csv",
        "site_update_tasks": output_dir / f"site-update-tasks-{config.run_date}.csv",
        "run_summary": output_dir / f"run-summary-{config.run_date}.md",
    }
    run_report["planned_outputs"] = {k: str(v) for k, v in output_paths.items()}
    run_report["next_mic_index"] = research_payload["next_mic_index"]

    if not config.confirm_writes:
        set_workflow_status(state, "needs_confirmation", config.run_id, config.run_date)
        run_report["status"] = "needs_confirmation"
        run_report["message"] = "Preview mode only. Re-run with --confirm-writes to persist outputs."
        return run_report

    write_csv_rows(
        output_paths["inquiry_quote_pack"],
        [
            "inquiry_id",
            "company_name",
            "product_name",
            "request_qty",
            "unit_price",
            "shipping_per_order",
            "currency",
            "total_price",
        ],
        quote_rows,
    )
    write_markdown(
        output_paths["customer_analysis"],
        build_customer_analysis_markdown(config.run_date, crm_payload),
    )
    write_csv_rows(
        output_paths["mic_daily_40"],
        ["product_id", "product_name", "mic_url", "target_market", "owner"],
        research_payload["mic_daily"],
    )
    write_csv_rows(
        output_paths["site_update_tasks"],
        ["page_slug", "page_url", "seo_keyword", "priority", "content_task", "image_task"],
        research_payload["site_updates"],
    )
    write_markdown(
        output_paths["run_summary"],
        build_run_summary_markdown(config.run_date, output_paths, research_payload["next_mic_index"]),
    )

    state["mic_last_index"] = research_payload["next_mic_index"]
    set_workflow_status(state, "done", config.run_id, config.run_date)
    state["runs"].append(
        {
            "run_id": config.run_id,
            "run_date": config.run_date,
            "status": "done",
            "mode": "confirm_write",
            "outputs": run_report["planned_outputs"],
        }
    )
    state["runs"] = state["runs"][-20:]
    save_json(state_path, state)

    run_report["status"] = "done"
    run_report["message"] = "Outputs and state were persisted."
    return run_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Foreign trade assistant orchestrator")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="Workspace root")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Run date: YYYY-MM-DD")
    parser.add_argument("--confirm-writes", action="store_true", help="Allow output and state writes")
    parser.add_argument("--run-id", default=f"run-{uuid.uuid4().hex[:10]}", help="Run identifier")
    parser.add_argument("--pretty", action="store_true", help="Pretty JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = OrchestratorConfig(
        root_dir=Path(args.root).resolve(),
        run_date=args.date,
        confirm_writes=args.confirm_writes,
        run_id=args.run_id,
    )
    report = run_orchestration(config)
    if args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get("status") in {"done", "needs_confirmation"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
