"""Research agent implementation."""

from __future__ import annotations

import json
from pathlib import Path

from app.contracts import ResearchAgentOutput, ResearchFinding


class ResearchAgent:
    def __init__(self, compliance_rules_path: Path) -> None:
        self.compliance_rules_path = compliance_rules_path

    def _load_rules(self) -> dict:
        with self.compliance_rules_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def analyze(self, *, destination: str, body: str) -> ResearchAgentOutput:
        if not destination:
            return ResearchAgentOutput(
                status="needs_input",
                risk_level="unknown",
                advisory_only=True,
                findings=[],
                notes=["Missing destination for risk analysis."],
            )
        rules = self._load_rules()
        findings: list[ResearchFinding] = []
        risk = "low"

        if destination.lower() in [x.lower() for x in rules.get("high_risk_destinations", [])]:
            findings.append(
                ResearchFinding(
                    topic="destination_risk",
                    detail=f"Destination {destination} is in configured high-risk list.",
                    severity="high",
                )
            )
            risk = "high"

        for kw in rules.get("watch_keywords", []):
            if kw.lower() in body.lower():
                findings.append(
                    ResearchFinding(
                        topic="keyword_watch",
                        detail=f"Message includes watch keyword: {kw}.",
                        severity="medium",
                    )
                )
                if risk != "high":
                    risk = "medium"

        if not findings:
            findings.append(
                ResearchFinding(
                    topic="baseline",
                    detail="No elevated compliance risk found in configured rules.",
                    severity="low",
                )
            )

        return ResearchAgentOutput(
            status="success",
            risk_level=("high" if risk == "high" else "medium" if risk == "medium" else "low"),
            advisory_only=True,
            findings=findings,
            notes=[],
        )
