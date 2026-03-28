from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExecutionContext:
    root: Path
    run_id: str
    mode: str
    query: str
    preflight: dict[str, Any]
    retrieval_trace: dict[str, Any]
    memory_file: Path
    incidents_file: Path
    review_mode: dict[str, Any]


def _orchestrator_agent(ctx: ExecutionContext) -> dict[str, Any]:
    preflight_ok = ctx.preflight.get("status") == "ok"
    checks_ready = bool(ctx.retrieval_trace.get("hits", []))
    status = "done" if preflight_ok else "blocked"
    if status == "done" and not checks_ready:
        status = "failed"
    return {
        "status": status,
        "payload": {
            "phase": "checkpoint" if preflight_ok else "preflight",
            "summary": "pipeline reached checkpoint" if preflight_ok else "pipeline blocked in preflight",
            "mode": ctx.mode,
            "run_id": ctx.run_id,
        },
        "missing_data": [] if preflight_ok else ["architecture_guardrails"],
    }


def _rag_agent(ctx: ExecutionContext) -> dict[str, Any]:
    hits = list(ctx.retrieval_trace.get("hits", []))
    return {
        "status": "done",
        "payload": {
            "indexed_documents": int(ctx.retrieval_trace.get("indexed_documents", 0)),
            "hit_count": len(hits),
            "query": ctx.retrieval_trace.get("query", ctx.query),
            "top_hit_source": (hits[0].get("source_id") if hits else ""),
        },
        "missing_data": [] if hits else ["rag_hits"],
    }


def _guardrails_agent(ctx: ExecutionContext) -> dict[str, Any]:
    violations = list(ctx.preflight.get("violations", []))
    return {
        "status": "done" if not violations else "blocked",
        "payload": {
            "preflight_status": ctx.preflight.get("status", "unknown"),
            "violation_count": len(violations),
            "violations": violations,
        },
        "missing_data": [],
    }


def _self_improving_agent(ctx: ExecutionContext) -> dict[str, Any]:
    missing: list[str] = []
    if not ctx.memory_file.exists():
        missing.append("memory_file")
    if not ctx.incidents_file.exists():
        missing.append("incidents_file")
    return {
        "status": "done" if not missing else "blocked",
        "payload": {
            "memory_write": "ready" if not missing else "blocked",
            "memory_file": str(ctx.memory_file),
            "incidents_file": str(ctx.incidents_file),
        },
        "missing_data": missing,
    }


def _review_agent(ctx: ExecutionContext) -> dict[str, Any]:
    forbidden_paths = list(ctx.review_mode.get("code_edit_forbidden_paths", []))
    software_edit_default = bool(ctx.review_mode.get("software_edit_default", False))
    if ctx.mode == "preview":
        status = "needs_confirmation"
    else:
        status = "done"
    return {
        "status": status,
        "payload": {
            "mode": "review_only",
            "software_edit_default": software_edit_default,
            "forbidden_paths": forbidden_paths,
        },
        "missing_data": [],
    }


_EXECUTORS = {
    "orchestrator_agent": _orchestrator_agent,
    "rag_agent": _rag_agent,
    "guardrails_agent": _guardrails_agent,
    "self_improving_agent": _self_improving_agent,
    "review_agent": _review_agent,
}


def run_agent(agent_name: str, ctx: ExecutionContext) -> dict[str, Any]:
    handler = _EXECUTORS.get(agent_name)
    if not handler:
        return {
            "status": "failed",
            "payload": {"error": "unsupported required agent"},
            "missing_data": ["agent_executor_mapping"],
        }
    return handler(ctx)

