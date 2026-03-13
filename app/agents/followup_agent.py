"""Followup agent implementation."""

from __future__ import annotations

from datetime import date, timedelta

from app.contracts import FollowupAction, FollowupAgentOutput, QuotationAgentOutput, ResearchAgentOutput


class FollowupAgent:
    def plan(
        self,
        *,
        message_id: str,
        quotation: QuotationAgentOutput | None,
        research: ResearchAgentOutput | None,
        needs_input: bool,
    ) -> FollowupAgentOutput:
        today = date.today()
        actions: list[FollowupAction] = []
        priority = "low"
        sla_flags: list[str] = []

        if needs_input:
            priority = "high"
            actions.append(
                FollowupAction(
                    action="Request missing commercial data from customer",
                    owner="sales_ops",
                    due_at=(today + timedelta(days=1)).isoformat(),
                )
            )
            sla_flags.append("awaiting_customer_input")

        if quotation and quotation.status == "success":
            actions.append(
                FollowupAction(
                    action=f"Send quote package for thread {message_id}",
                    owner="sales_rep",
                    due_at=(today + timedelta(days=1)).isoformat(),
                )
            )
            if priority != "high":
                priority = "medium"

        if research and research.risk_level == "high":
            priority = "high"
            actions.append(
                FollowupAction(
                    action="Escalate to compliance before quote commitment",
                    owner="compliance",
                    due_at=today.isoformat(),
                )
            )
            sla_flags.append("compliance_escalation")

        if not actions:
            actions.append(
                FollowupAction(
                    action=f"Monitor message {message_id} for updates",
                    owner="sales_ops",
                    due_at=(today + timedelta(days=2)).isoformat(),
                )
            )

        return FollowupAgentOutput(
            status="success",
            priority_level=priority,  # type: ignore[arg-type]
            recommended_actions=actions,
            sla_flags=sla_flags,
            notes=[],
        )
