#!/usr/bin/env python3
"""Resolve and validate the shared scroll-world capability across sibling worktrees."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_path(root: Path) -> Path:
    site_path = root / "site_ops" / "config" / "scroll-world-link.json"
    if site_path.exists():
        return site_path
    return root / "config" / "scroll-world-link.json"


def load_config(root: Path) -> dict[str, Any]:
    with config_path(root).open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def peer_root(root: Path, config: dict[str, Any]) -> Path:
    return root.parent / config["peer_workspace"]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(root: Path) -> str | None:
    if not root.is_dir():
        return None
    digest = hashlib.sha256()
    for path in sorted(
        item
        for item in root.rglob("*")
        if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"
    ):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_status(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    peer = peer_root(root, config)
    local_skill = root / config["skill_path"]
    remote_skill = peer / config["peer_skill_path"]
    local_hash = tree_sha256(local_skill.parent)
    peer_hash = tree_sha256(remote_skill.parent)
    expected_local_hash = config["local_skill_tree_sha256"]
    expected_peer_hash = config["peer_skill_tree_sha256"]
    return {
        "workspace": config["workspace"],
        "peer_workspace": config["peer_workspace"],
        "local_skill": str(local_skill),
        "peer_skill": str(remote_skill),
        "local_available": local_hash is not None,
        "peer_available": peer_hash is not None,
        "source_commit": config["source_commit"],
        "expected_local_skill_tree_sha256": expected_local_hash,
        "expected_peer_skill_tree_sha256": expected_peer_hash,
        "local_skill_tree_sha256": local_hash,
        "peer_skill_tree_sha256": peer_hash,
        "skill_versions_match": bool(local_hash == expected_local_hash and peer_hash == expected_peer_hash),
        "capability_owners": config["capability_owners"],
    }


def build_handoff(
    root: Path,
    config: dict[str, Any],
    capability: str,
    project_id: str,
    brief: str,
) -> dict[str, Any]:
    owners = config["capability_owners"]
    if capability not in owners:
        raise ValueError(f"unknown capability: {capability}")
    owner = owners[capability]
    target = config["workspace"] if owner in {"shared", config["workspace"]} else config["peer_workspace"]
    target_root = root if target == config["workspace"] else peer_root(root, config)
    status = build_status(root, config)
    return {
        "schema_version": config["schema_version"],
        "source_workspace": config["workspace"],
        "target_workspace": target,
        "target_root": str(target_root),
        "target_skill": str(target_root / config["peer_skill_path"]),
        "project_id": project_id,
        "capability": capability,
        "brief": brief,
        "status": "requested",
        "hop_count": 1,
        "visited_workspaces": [config["workspace"]],
        "contract": config["handoff_contract"],
        "link_ready": status["local_available"] and status["peer_available"] and status["skill_versions_match"],
        "next_action": "Open the target worktree and invoke its project-local scroll-world skill with this payload.",
    }


def accept_handoff(root: Path, config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if payload.get("target_workspace") != config["workspace"]:
        reasons.append("target_workspace_mismatch")
    if int(payload.get("hop_count", 0)) > int(config["max_hops"]):
        reasons.append("max_hops_exceeded")
    if config["workspace"] in payload.get("visited_workspaces", []):
        reasons.append("handoff_loop_detected")
    status = build_status(root, config)
    if not status["skill_versions_match"]:
        reasons.append("skill_version_mismatch")
    return {
        "schema_version": config["schema_version"],
        "workspace": config["workspace"],
        "request_source": payload.get("source_workspace"),
        "capability": payload.get("capability"),
        "status": "blocked" if reasons else "accepted",
        "reasons": reasons,
        "skill": str(root / config["skill_path"]),
        "source_commit": config["source_commit"],
        "next_action": "Apply the project-local scroll-world skill; obtain confirmation before paid generation or release." if not reasons else "Resolve linkage validation errors before invoking the skill.",
    }


def dispatch_handoff(root: Path, config: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    peer_script = peer_root(root, config) / "scripts" / "scroll-world-link.py"
    completed = subprocess.run(
        [sys.executable, str(peer_script), "accept", "--payload-json", json.dumps(payload, ensure_ascii=False)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {"status": "blocked", "reasons": ["peer_invocation_failed"], "stderr": completed.stderr.strip()}
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    handoff = subparsers.add_parser("handoff")
    handoff.add_argument("--capability", required=True)
    handoff.add_argument("--project-id", required=True)
    handoff.add_argument("--brief", required=True)
    dispatch = subparsers.add_parser("dispatch")
    dispatch.add_argument("--capability", required=True)
    dispatch.add_argument("--project-id", required=True)
    dispatch.add_argument("--brief", required=True)
    accept = subparsers.add_parser("accept")
    accept.add_argument("--payload-json", required=True)
    args = parser.parse_args()

    root = workspace_root()
    config = load_config(root)
    try:
        if args.command == "status":
            result = build_status(root, config)
        elif args.command == "accept":
            result = accept_handoff(root, config, json.loads(args.payload_json))
        else:
            payload = build_handoff(root, config, args.capability, args.project_id, args.brief)
            result = dispatch_handoff(root, config, payload) if args.command == "dispatch" else payload
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
