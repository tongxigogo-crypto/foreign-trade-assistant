from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VALID_STATUSES = {"pending", "running", "blocked", "needs_confirmation", "done", "failed"}


@dataclass
class OrchestratorConfig:
    root_dir: Path
    run_id: str
    confirm_writes: bool


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def build_agent_result(
    agent: str,
    status: str,
    summary: str,
    artifacts: list[str] | None = None,
    risks: list[str] | None = None,
    missing_data: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    return {
        "agent": agent,
        "status": status,
        "summary": summary,
        "artifacts": artifacts or [],
        "risks": risks or [],
        "missing_data": missing_data or [],
        "next_actions": next_actions or [],
    }


def run_orchestration(config: OrchestratorConfig) -> dict[str, Any]:
    cfg_dir = config.root_dir / "site_ops" / "config"
    registry = load_json(cfg_dir / "agent-registry.json")
    publish_policy = load_json(cfg_dir / "publishing-policy.json")
    stitch = load_json(cfg_dir / "stitch-integration.json")

    required_agents: list[str] = list(registry.get("required_agents", []))
    flow: list[str] = list(registry.get("default_flow", []))
    missing_registry = [name for name in required_agents if name not in (["orchestrator"] + flow)]
    if missing_registry:
        return {
            "run_id": config.run_id,
            "status": "failed",
            "mode": "confirm_write" if config.confirm_writes else "preview",
            "required_agents": required_agents,
            "flow": flow,
            "agent_results": [],
            "missing_data": [f"agent missing in flow: {name}" for name in missing_registry],
            "message": "Agent registry is inconsistent.",
        }

    stitch_enabled = bool(stitch.get("enabled", False))
    agent_results = [
        build_agent_result(
            "orchestrator",
            "done",
            "Site publishing workflow dispatched.",
            next_actions=[f"dispatch {name}" for name in flow],
        )
    ]
    for name in flow:
        if name == "ui_stitch_agent" and stitch_enabled:
            agent_results.append(
                build_agent_result(
                    name,
                    "done",
                    "Stitch UI polishing lane enabled.",
                    artifacts=["stitch_export_reference", "component_map", "style_tokens"],
                    next_actions=["handoff implementation-ready UI specs"],
                )
            )
            continue
        agent_results.append(
            build_agent_result(
                name,
                "done",
                f"{name} accepted current release scope.",
                next_actions=["await task payload"],
            )
        )

    if not config.confirm_writes:
        return {
            "run_id": config.run_id,
            "status": "needs_confirmation",
            "mode": "preview",
            "required_agents": required_agents,
            "flow": flow,
            "agent_results": agent_results,
            "missing_data": [],
            "message": "Preview only. Re-run with --confirm-writes to persist outputs.",
        }

    if bool(publish_policy.get("require_confirmation_for_output_write", True)) and not config.confirm_writes:
        return {
            "run_id": config.run_id,
            "status": "needs_confirmation",
            "mode": "preview",
            "required_agents": required_agents,
            "flow": flow,
            "agent_results": agent_results,
            "missing_data": [],
            "message": "Output write requires explicit confirmation.",
        }

    output_dir = config.root_dir / "site_ops" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"site-flow-{config.run_id}.json"
    output_path.write_text(json.dumps(agent_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "run_id": config.run_id,
        "status": "done",
        "mode": "confirm_write",
        "required_agents": required_agents,
        "flow": flow,
        "agent_results": agent_results,
        "missing_data": [],
        "message": f"Site flow persisted to {output_path}",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Site publishing multi-agent orchestrator")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--run-id", default=f"run-{uuid.uuid4().hex[:10]}")
    parser.add_argument("--confirm-writes", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_orchestration(
        OrchestratorConfig(
            root_dir=Path(args.root).resolve(),
            run_id=args.run_id,
            confirm_writes=args.confirm_writes,
        )
    )
    if args.pretty:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"done", "needs_confirmation"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
