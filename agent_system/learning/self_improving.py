from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class LearningRecord:
    timestamp: str
    category: str
    status: str
    context: str
    signal: str
    rule: str
    action: str
    scope: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "category": self.category,
            "status": self.status,
            "context": self.context,
            "signal": self.signal,
            "rule": self.rule,
            "action": self.action,
            "scope": self.scope,
        }


class SelfImprovingLedger:
    def __init__(self, memory_file: Path, incidents_file: Path) -> None:
        self.memory_file = memory_file
        self.incidents_file = incidents_file
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.incidents_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_file.exists():
            self.memory_file.write_text("# Self Improving Agent Memory\n\n", encoding="utf-8")
        if not self.incidents_file.exists():
            self.incidents_file.write_text("[]\n", encoding="utf-8")

    def record(self, record: LearningRecord) -> None:
        incidents = self.load_incidents()
        incidents.append(record.to_dict())
        self.incidents_file.write_text(json.dumps(incidents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        entry = "\n".join(
            [
                f"## [{record.timestamp}] {record.category}",
                "",
                f"- status: {record.status}",
                f"- context: {record.context}",
                f"- signal: {record.signal}",
                f"- rule: {record.rule}",
                f"- scope: {record.scope}",
                f"- action: {record.action}",
                "",
            ]
        )
        with self.memory_file.open("a", encoding="utf-8") as fh:
            fh.write(entry)

    def load_incidents(self) -> list[dict[str, Any]]:
        try:
            payload = json.loads(self.incidents_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]

    def derive_candidates_from_run(self, run_report: dict[str, Any]) -> list[LearningRecord]:
        status = str(run_report.get("status", ""))
        if status in {"done", "needs_confirmation"}:
            return []
        missing = run_report.get("missing_data", [])
        missing_line = "; ".join(str(item) for item in missing[:5]) if isinstance(missing, list) else str(missing)
        signal = missing_line or "run failed without explicit missing_data"
        return [
            LearningRecord(
                timestamp=utc_now(),
                category="run-failure-pattern",
                status="candidate",
                context=f"run_id={run_report.get('run_id', '')}",
                signal=signal,
                rule="For blocked/failed runs, enforce explicit missing_data and mapped owner in next step.",
                action="Update orchestrator mapping and add regression test for this failure signature.",
                scope="E:\\CodexWorkspace\\Playground-pm",
            )
        ]

