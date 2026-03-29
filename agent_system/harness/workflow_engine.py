from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VALID_STATUSES = {"pending", "running", "blocked", "needs_confirmation", "done", "failed"}


@dataclass
class HarnessPaths:
    session_state: Path
    current_session: Path
    guardrail_report: Path
    closed_loop_verdict: Path
    run_reports_dir: Path


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def ensure_dirs(paths: HarnessPaths) -> None:
    for path in [
        paths.session_state.parent,
        paths.current_session.parent,
        paths.guardrail_report.parent,
        paths.closed_loop_verdict.parent,
        paths.run_reports_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def validate_agent_results(agent_results: list[dict[str, Any]], required_agents: list[str]) -> list[str]:
    violations: list[str] = []
    names = {str(item.get("agent", "")) for item in agent_results}
    missing = [name for name in required_agents if name not in names]
    if missing:
        violations.append(f"missing required agents: {', '.join(missing)}")
    for item in agent_results:
        status = str(item.get("status", ""))
        if status not in VALID_STATUSES:
            violations.append(f"invalid status for {item.get('agent', 'unknown')}: {status}")
        if not isinstance(item.get("payload", {}), dict):
            violations.append(f"payload must be object for {item.get('agent', 'unknown')}")
        if not isinstance(item.get("missing_data", []), list):
            violations.append(f"missing_data must be array for {item.get('agent', 'unknown')}")
    return violations


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_preflight_report(
    required_agents: list[str],
    required_outputs: list[str],
    planned_outputs: dict[str, str],
    agent_results: list[dict[str, Any]],
) -> dict[str, Any]:
    violations = validate_agent_results(agent_results, required_agents)
    missing_outputs = [name for name in required_outputs if name not in planned_outputs]
    if missing_outputs:
        violations.append(f"missing planned outputs: {', '.join(missing_outputs)}")
    return {
        "status": "ok" if not violations else "blocked",
        "updated_at": utc_now(),
        "required_agents": required_agents,
        "required_outputs": required_outputs,
        "violations": violations,
    }


def build_closed_loop_verdict(
    run_status: str,
    checks: list[dict[str, Any]],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    passed = all(bool(item.get("passed")) for item in checks)
    if run_status == "needs_confirmation":
        status = "preview"
    elif run_status in {"blocked", "failed"}:
        status = "failed"
    else:
        status = "pass" if passed else "failed"
    return {
        "status": status,
        "updated_at": utc_now(),
        "summary": f"{sum(1 for x in checks if x.get('passed'))}/{len(checks)} checks passed",
        "checks": checks,
        "evidence": evidence,
    }


def checkpoint_session(
    paths: HarnessPaths,
    *,
    active_task: str,
    current_goal: str,
    progress: list[str],
    next_actions: list[str],
    blockers: list[str],
    summary: str,
    git_status: str,
) -> None:
    def section_lines(items: list[str]) -> list[str]:
        if not items:
            return ["- None"]
        return [f"- {item}" for item in items]

    ensure_dirs(paths)
    session_payload = {
        "updated_at": utc_now(),
        "active_task": active_task,
        "current_goal": current_goal,
        "progress": progress,
        "open_questions": [],
        "blockers": blockers,
        "next_actions": next_actions,
        "last_git_status": git_status,
    }
    write_json(paths.session_state, session_payload)
    current_md = "\n".join(
        [
            "# Current Session",
            "",
            "## Active Task",
            f"- {active_task or 'None'}",
            "",
            "## Current Goal",
            f"- {current_goal or 'None'}",
            "",
            "## Progress",
            *section_lines(progress),
            "",
            "## Blockers",
            *section_lines(blockers),
            "",
            "## Next Actions",
            *section_lines(next_actions),
            "",
            "## Summary",
            f"- {summary or 'None'}",
        ]
    )
    paths.current_session.write_text(current_md + "\n", encoding="utf-8")
