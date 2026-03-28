from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agent_system.runtime import run_pipeline


def evaluate_report(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if report.get("status") != "done":
        failures.append(f"run status expected 'done', got {report.get('status')!r}")

    closed_loop = report.get("closed_loop", {})
    if closed_loop.get("status") != "pass":
        failures.append(f"closed loop expected 'pass', got {closed_loop.get('status')!r}")

    checks = closed_loop.get("checks", [])
    if not checks:
        failures.append("closed loop checks missing")
    elif not all(bool(item.get("passed")) for item in checks):
        failures.append("one or more closed loop checks failed")

    required_agents = list(report.get("required_agents", []))
    agent_results = list(report.get("agent_results", []))
    seen_agents = {str(item.get("agent", "")) for item in agent_results}
    missing = [name for name in required_agents if name not in seen_agents]
    if missing:
        failures.append(f"missing agent results: {', '.join(missing)}")

    return failures


def run_gate(root: Path, run_id: str, query: str) -> dict[str, Any]:
    report = run_pipeline(root=root.resolve(), run_id=run_id, query=query, mode="confirm_write")
    failures = evaluate_report(report)
    return {
        "ok": not failures,
        "run_id": run_id,
        "failures": failures,
        "report": report,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent system CI gate")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--run-id", default="ci-gate", help="Runtime run identifier")
    parser.add_argument(
        "--query",
        default="agent architecture guardrails and harness recovery",
        help="RAG query used for runtime execution",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_gate(root=Path(args.root), run_id=args.run_id, query=args.query)
    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
