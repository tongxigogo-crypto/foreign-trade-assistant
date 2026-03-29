from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from .executors import ExecutionContext, run_agent
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


def load_json_optional(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    return load_json(path)


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


def build_preflight_agent_plan(required_agents: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "agent": agent_name,
            "status": "pending",
            "payload": {"planned": True},
            "missing_data": [],
        }
        for agent_name in required_agents
    ]


def execute_required_agents(required_agents: list[str], *, ctx: ExecutionContext) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for agent_name in required_agents:
        result = {"agent": agent_name}
        result.update(run_agent(agent_name, ctx))
        results.append(result)
    return results


def collect_git_status(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        return out.strip() or "(clean)"
    except Exception:
        return "(git status unavailable)"


def collect_git_changed_files(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def resolve_audit_level(requested: str, changed_files: list[str], runtime_policy: dict[str, Any]) -> str:
    level = str(requested or "auto").strip().lower()
    if level in {"quick", "full"}:
        return level

    full_keywords = list(runtime_policy.get("full_audit_keywords", [])) or [
        "agent_system/runtime.py",
        "agent_system/executors",
        "agent_system/harness",
        "agent_system/learning",
        "agent_system/rag",
        "architecture-contract.json",
        "required-agents.json",
    ]
    quick_max = int(runtime_policy.get("quick_audit_max_files", 4))
    if not changed_files:
        return "full"
    if len(changed_files) > quick_max:
        return "full"
    for item in changed_files:
        normalized = item.replace("\\", "/").lower()
        for token in full_keywords:
            if str(token).lower() in normalized:
                return "full"
    return "quick"


def check_required_outputs(required_outputs: list[str], planned_outputs: dict[str, str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for output_name in required_outputs:
        target = planned_outputs.get(output_name, "")
        exists = bool(target) and Path(target).exists()
        checks.append({"name": f"output_exists:{output_name}", "passed": exists})
        if exists and str(target).lower().endswith(".json"):
            parse_ok = True
            try:
                json.loads(Path(target).read_text(encoding="utf-8-sig"))
            except Exception:
                parse_ok = False
            checks.append({"name": f"output_json_parse:{output_name}", "passed": parse_ok})
    return checks


def check_review_mode_enforced(review_mode: dict[str, Any], agent_results: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_paths = list(review_mode.get("code_edit_forbidden_paths", []))
    review_result = next((x for x in agent_results if x.get("agent") == "review_agent"), {})
    payload = dict(review_result.get("payload", {})) if isinstance(review_result.get("payload", {}), dict) else {}
    payload_paths = payload.get("forbidden_paths", [])
    passed = sorted(str(x) for x in payload_paths) == sorted(str(x) for x in forbidden_paths)
    return {"name": "review_mode_forbidden_paths_enforced", "passed": passed}


def run_pipeline(root: Path, run_id: str, query: str, mode: str, audit_level: str = "auto") -> dict[str, Any]:
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
    runtime_policy = load_json_optional(
        root / "agent_system" / "config" / "runtime-policy.json",
        {
            "active_task": "agent runtime",
            "current_goal": "run configured agent pipeline with evidence",
            "next_actions": ["review run report", "decide next implementation step"],
            "summary": "Pipeline executed with checkpointed harness state.",
            "quick_audit_max_files": 4,
            "quick_rag_sources": [
                "AGENTS.md",
                "docs/harness/current_session.md",
                "docs/memory/self_improving_agent.md",
            ],
        },
    )
    required_outputs = list(architecture_contract.get("required_outputs", []))
    rag_sources = list(architecture_contract.get("rag_sources", []))
    review_mode = dict(architecture_contract.get("review_mode", {}))

    changed_files = collect_git_changed_files(root)
    effective_audit_level = resolve_audit_level(audit_level, changed_files, runtime_policy)
    active_rag_sources = rag_sources
    if effective_audit_level == "quick":
        quick_sources = list(runtime_policy.get("quick_rag_sources", []))
        active_rag_sources = quick_sources or rag_sources[:3]

    preflight_agent_plan = build_preflight_agent_plan(required_agents)
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
        agent_results=preflight_agent_plan,
    )
    write_json(paths.guardrail_report, preflight)

    rag_db = root / "agent_system" / "data" / "rag_index.sqlite"
    index = KnowledgeIndex(rag_db)
    doc_count = index.bulk_upsert(gather_rag_documents(root, rag_sources=active_rag_sources))
    hits = index.query(query=query, top_k=8)
    retrieval_trace = {
        "updated_at": utc_now(),
        "query": query,
        "top_k": 8,
        "indexed_documents": doc_count,
        "hits": [item.to_dict() for item in hits],
    }
    write_json(paths.run_reports_dir / f"retrieval-trace-{run_id}.json", retrieval_trace)
    exec_ctx = ExecutionContext(
        root=root,
        run_id=run_id,
        mode=mode,
        query=query,
        preflight=preflight,
        retrieval_trace=retrieval_trace,
        memory_file=root / "docs" / "memory" / "self_improving_agent.md",
        incidents_file=root / "agent_system" / "data" / "learning_incidents.json",
        review_mode=review_mode,
    )
    agent_results = execute_required_agents(required_agents, ctx=exec_ctx)

    checks = [
        {"name": "preflight_ok", "passed": preflight["status"] == "ok"},
        {"name": "required_agents_defined", "passed": len(required_agents) > 0},
    ]
    if effective_audit_level == "full":
        checks.append({"name": "retrieval_non_empty", "passed": len(hits) > 0})
    checks.append(check_review_mode_enforced(review_mode, agent_results))
    run_status = "blocked" if preflight["status"] != "ok" else "done"
    if run_status == "done" and not all(item["passed"] for item in checks):
        run_status = "failed"
    if mode == "preview":
        run_status = "needs_confirmation"
    run_report_file = paths.run_reports_dir / f"run-report-{run_id}.json"

    verdict = build_closed_loop_verdict(
        run_status=run_status,
        checks=checks,
        evidence={
            "guardrail_report": str(paths.guardrail_report),
            "retrieval_trace": str(paths.run_reports_dir / f"retrieval-trace-{run_id}.json"),
            "run_report": str(run_report_file),
            "rag_db": str(rag_db),
        },
    )
    run_report = {
        "run_id": run_id,
        "run_date": utc_now()[:10],
        "status": run_status,
        "mode": mode,
        "required_agents": required_agents,
        "required_outputs": required_outputs,
        "agent_results": agent_results,
        "architecture_guardrails": preflight,
        "closed_loop": verdict,
        "retrieval_trace_file": planned_outputs["retrieval_trace"],
        "timestamp_utc": utc_now(),
    }
    write_json(run_report_file, run_report)
    if not paths.closed_loop_verdict.exists():
        write_json(paths.closed_loop_verdict, {"status": "pending", "updated_at": utc_now()})
    output_checks = check_required_outputs(required_outputs, planned_outputs)
    if effective_audit_level == "quick":
        output_checks = [item for item in output_checks if "run_report" in item["name"] or "guardrail_report" in item["name"]]
    checks.extend(output_checks)
    if run_status == "done" and not all(item["passed"] for item in checks):
        run_status = "failed"
    run_report["status"] = run_status
    verdict = build_closed_loop_verdict(
        run_status=run_status,
        checks=checks,
        evidence={
            "guardrail_report": str(paths.guardrail_report),
            "retrieval_trace": str(paths.run_reports_dir / f"retrieval-trace-{run_id}.json"),
            "run_report": str(run_report_file),
            "rag_db": str(rag_db),
        },
    )
    run_report["closed_loop"] = verdict
    run_report["audit_level"] = effective_audit_level
    run_report["changed_files"] = changed_files
    run_report["incremental_summary"] = [
        f"Changed scope: {len(changed_files)} file(s); audit={effective_audit_level}.",
        f"Core logic preserved: {'yes' if preflight['status'] == 'ok' else 'check required'}.",
        f"Core checks pass: {sum(1 for x in checks if x.get('passed'))}/{len(checks)}.",
    ]
    write_json(run_report_file, run_report)
    write_json(paths.closed_loop_verdict, verdict)

    ledger = SelfImprovingLedger(
        memory_file=root / "docs" / "memory" / "self_improving_agent.md",
        incidents_file=root / "agent_system" / "data" / "learning_incidents.json",
    )
    for candidate in ledger.derive_candidates_from_run(run_report):
        ledger.record(candidate)

    checkpoint_session(
        paths,
        active_task=str(runtime_policy.get("active_task", "agent runtime")),
        current_goal=str(runtime_policy.get("current_goal", "run configured agent pipeline with evidence")),
        progress=[
            f"preflight status={preflight['status']}",
            f"retrieval hits={len(hits)}",
            f"run status={run_status}",
        ],
        next_actions=list(runtime_policy.get("next_actions", [])),
        blockers=[],
        summary=str(runtime_policy.get("summary", "Pipeline executed with checkpointed harness state.")),
        git_status=collect_git_status(root),
    )

    return run_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Playground-pm agent architecture pipeline")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="Workspace root")
    parser.add_argument("--run-id", default="architecture-run", help="Run identifier")
    parser.add_argument("--query", default="agent architecture guardrails and harness recovery", help="RAG query")
    parser.add_argument("--mode", choices=["preview", "confirm_write"], default="preview")
    parser.add_argument("--audit-level", choices=["auto", "quick", "full"], default="auto")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_pipeline(Path(args.root).resolve(), args.run_id, args.query, args.mode, audit_level=args.audit_level)
    if args.pretty:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"done", "needs_confirmation"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
