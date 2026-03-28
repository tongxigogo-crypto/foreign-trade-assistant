from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .harness.workflow_engine import (
    HarnessPaths,
    build_closed_loop_verdict,
    build_preflight_report,
    checkpoint_session,
    ensure_dirs,
    utc_now,
    write_json,
)
from .learning.self_improving import SelfImprovingLedger
from .rag.knowledge_index import KnowledgeIndex


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def gather_rag_documents(root: Path, rag_sources: list[str]) -> list[dict[str, Any]]:
    candidates = [root / item for item in rag_sources]
    docs: list[dict[str, Any]] = []
    for path in candidates:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        docs.append(
            {
                "namespace": "workspace",
                "source_id": str(path.relative_to(root)).replace("\\", "/"),
                "content": content,
                "metadata": {"path": str(path)},
            }
        )
    return docs


def run_pipeline(root: Path, run_id: str, query: str, mode: str) -> dict[str, Any]:
    harness_dir = root / "docs" / "harness"
    run_reports_dir = root / "agent_system" / "output"
    paths = HarnessPaths(
        session_state=harness_dir / "session_state.json",
        current_session=harness_dir / "current_session.md",
        guardrail_report=harness_dir / "architecture_guardrails.json",
        closed_loop_verdict=harness_dir / "closed_loop_verdict.json",
        run_reports_dir=run_reports_dir,
    )
    ensure_dirs(paths)

    required_agents_cfg = load_json(root / "agent_system" / "config" / "required-agents.json")
    required_agents = list(required_agents_cfg.get("required_agents", []))
    architecture_contract = load_json(root / "agent_system" / "config" / "architecture-contract.json")
    required_outputs = list(architecture_contract.get("required_outputs", []))
    rag_sources = list(architecture_contract.get("rag_sources", []))

    sample_agent_results = load_json(root / "agent_system" / "input" / "agent-results.sample.json").get("agent_results", [])
    planned_outputs = {
        "run_report": str(paths.run_reports_dir / f"run-report-{run_id}.json"),
        "retrieval_trace": str(paths.run_reports_dir / f"retrieval-trace-{run_id}.json"),
        "guardrail_report": str(paths.guardrail_report),
        "closed_loop_verdict": str(paths.closed_loop_verdict),
    }

    preflight = build_preflight_report(
        required_agents=required_agents,
        required_outputs=required_outputs,
        planned_outputs=planned_outputs,
        agent_results=sample_agent_results,
    )
    write_json(paths.guardrail_report, preflight)

    rag_db = root / "agent_system" / "data" / "rag_index.sqlite"
    index = KnowledgeIndex(rag_db)
    doc_count = index.bulk_upsert(gather_rag_documents(root, rag_sources=rag_sources))
    hits = index.query(query=query, top_k=8)
    retrieval_trace = {
        "updated_at": utc_now(),
        "query": query,
        "top_k": 8,
        "indexed_documents": doc_count,
        "hits": [item.to_dict() for item in hits],
    }
    write_json(paths.run_reports_dir / f"retrieval-trace-{run_id}.json", retrieval_trace)

    checks = [
        {"name": "preflight_ok", "passed": preflight["status"] == "ok"},
        {"name": "retrieval_non_empty", "passed": len(hits) > 0},
        {"name": "required_agents_defined", "passed": len(required_agents) > 0},
    ]
    run_status = "blocked" if preflight["status"] != "ok" else "done"
    if run_status == "done" and not all(item["passed"] for item in checks):
        run_status = "failed"
    if mode == "preview":
        run_status = "needs_confirmation"
    verdict = build_closed_loop_verdict(
        run_status=run_status,
        checks=checks,
        evidence={
            "guardrail_report": str(paths.guardrail_report),
            "retrieval_trace": str(paths.run_reports_dir / f"retrieval-trace-{run_id}.json"),
            "rag_db": str(rag_db),
        },
    )
    write_json(paths.closed_loop_verdict, verdict)

    run_report = {
        "run_id": run_id,
        "run_date": utc_now()[:10],
        "status": run_status,
        "mode": mode,
        "required_agents": required_agents,
        "required_outputs": required_outputs,
        "agent_results": sample_agent_results,
        "architecture_guardrails": preflight,
        "closed_loop": verdict,
        "retrieval_trace_file": planned_outputs["retrieval_trace"],
        "timestamp_utc": utc_now(),
    }
    write_json(paths.run_reports_dir / f"run-report-{run_id}.json", run_report)

    ledger = SelfImprovingLedger(
        memory_file=root / "docs" / "memory" / "self_improving_agent.md",
        incidents_file=root / "agent_system" / "data" / "learning_incidents.json",
    )
    for candidate in ledger.derive_candidates_from_run(run_report):
        ledger.record(candidate)

    checkpoint_session(
        paths,
        active_task="agent architecture refactor runtime",
        current_goal="stabilize RAG + Harness + self-improving pipeline",
        progress=[
            f"preflight status={preflight['status']}",
            f"retrieval hits={len(hits)}",
            f"run status={run_status}",
        ],
        next_actions=[
            "Replace sample agent results with live orchestration outputs",
            "Hook run pipeline into CI gate",
        ],
        blockers=[],
        summary="Architecture pipeline executed with persistent evidence and learning records.",
        git_status="",
    )

    return run_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Playground-pm agent architecture pipeline")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="Workspace root")
    parser.add_argument("--run-id", default="architecture-run", help="Run identifier")
    parser.add_argument("--query", default="agent architecture guardrails and harness recovery", help="RAG query")
    parser.add_argument("--mode", choices=["preview", "confirm_write"], default="preview")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_pipeline(Path(args.root).resolve(), args.run_id, args.query, args.mode)
    if args.pretty:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"done", "needs_confirmation"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
