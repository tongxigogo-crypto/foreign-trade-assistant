"""Orchestrator main flow."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.agents.crm_agent import CRMAgent
from app.agents.email_agent import EmailAgent
from app.agents.followup_agent import FollowupAgent
from app.agents.quotation_agent import QuotationAgent
from app.agents.research_agent import ResearchAgent
from app.config import Settings, load_settings
from app.contracts import AgentStatus, OrchestratorOutput, PipelineRecord, PlanStep
from app.data_access.crm_store import CRMStore
from app.data_access.pricing_source import PricingSource
from app.logging_utils import setup_logging


class TradeOpsOrchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.logger = setup_logging(self.settings.log_path, self.settings.log_level)

        self.email_agent = EmailAgent()
        self.quotation_agent = QuotationAgent(
            PricingSource(self.settings.pricing_rules_path, self.settings.freight_rules_path)
        )
        self.crm_agent = CRMAgent(CRMStore(self.settings.crm_store_path))
        self.followup_agent = FollowupAgent()
        self.research_agent = ResearchAgent(self.settings.compliance_rules_path)

    def run(self, messages: list[dict]) -> OrchestratorOutput:
        plan = [
            PlanStep(step=1, agent="email", objective="Normalize and classify inbound messages"),
            PlanStep(step=2, agent="research", objective="Generate advisory findings", depends_on=[1]),
            PlanStep(step=3, agent="quotation", objective="Draft quotation package", depends_on=[1]),
            PlanStep(step=4, agent="crm", objective="Persist lead updates", depends_on=[1, 3]),
            PlanStep(step=5, agent="followup", objective="Plan follow-up actions", depends_on=[2, 3, 4]),
        ]
        pipelines: list[PipelineRecord] = []
        notes: list[str] = []
        overall_status: AgentStatus = "success"

        for message in messages:
            email_output = self.email_agent.process_message(message)
            quotation_output = None
            research_output = None
            crm_output = None
            message_id = email_output.extracted.message_id or "unknown"

            if email_output.handoff_recommendations.send_to_research:
                research_output = self.research_agent.analyze(
                    destination=email_output.extracted.destination_port_if_any,
                    body=email_output.extracted.cleaned_body,
                )
            if email_output.handoff_recommendations.send_to_quotation:
                quotation_output = self.quotation_agent.prepare(email_output.extracted)
            if email_output.handoff_recommendations.send_to_crm:
                lead_status = (
                    "quote_ready"
                    if quotation_output and quotation_output.quotation_readiness == "ready"
                    else "awaiting_details"
                )
                crm_output = self.crm_agent.upsert_lead(
                    inquiry=email_output.extracted, lead_status=lead_status, source="gmail"
                )

            followup_output = self.followup_agent.plan(
                message_id=message_id,
                quotation=quotation_output,
                research=research_output,
                needs_input=email_output.status == "needs_input"
                or (quotation_output is not None and quotation_output.status == "needs_input"),
            )

            pipelines.append(
                PipelineRecord(
                    message_id=message_id,
                    email=email_output,
                    quotation=quotation_output,
                    crm=crm_output,
                    followup=followup_output,
                    research=research_output,
                )
            )
            notes.extend(email_output.notes)
            if quotation_output:
                notes.extend(quotation_output.notes)
            if research_output:
                notes.extend(research_output.notes)

            statuses = [
                email_output.status,
                quotation_output.status if quotation_output else "success",
                research_output.status if research_output else "success",
                crm_output.status if crm_output else "success",
                followup_output.status,
            ]
            for status in statuses:
                if status == "failed":
                    overall_status = "failed"
                elif status == "needs_input" and overall_status != "failed":
                    overall_status = "needs_input"
                elif status == "partial" and overall_status == "success":
                    overall_status = "partial"

        output = OrchestratorOutput(
            task="daily_foreign_trade_email_pipeline",
            plan=plan,
            status=overall_status,
            notes=notes,
            pipelines=pipelines,
            human_summary=self._summary(pipelines, overall_status),
        )
        self._write_summary(output)
        return output

    def _summary(self, pipelines: list[PipelineRecord], status: AgentStatus) -> str:
        total = len(pipelines)
        valid = sum(1 for p in pipelines if p.email.is_valid_inquiry)
        quote_ready = sum(
            1 for p in pipelines if p.quotation is not None and p.quotation.quotation_readiness == "ready"
        )
        return (
            f"{date.today().isoformat()} status={status}: processed {total} messages, "
            f"detected {valid} valid inquiries, prepared {quote_ready} quote-ready packages."
        )

    def _write_summary(self, output: OrchestratorOutput) -> None:
        path = Path("data") / f"orchestrator-summary-{date.today().isoformat()}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(output.to_dict(), f, ensure_ascii=False, indent=2)
        self.logger.info("Orchestrator summary written to %s", path.as_posix())
