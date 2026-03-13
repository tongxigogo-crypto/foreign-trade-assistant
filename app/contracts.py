"""Shared typed contracts for multi-agent handoff."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AgentStatus = Literal["success", "partial", "needs_input", "failed"]
MessageClass = Literal[
    "inquiry",
    "follow_up_from_customer",
    "logistics_notice",
    "supplier_message",
    "advertising_or_spam",
    "internal_or_irrelevant",
    "unknown",
]


@dataclass(slots=True)
class PlanStep:
    step: int
    agent: Literal["email", "quotation", "crm", "followup", "research"]
    objective: str
    depends_on: list[int] = field(default_factory=list)


@dataclass(slots=True)
class InquiryExtracted:
    message_id: str = ""
    thread_id: str = ""
    date: str = ""
    sender_name: str = ""
    sender_email: str = ""
    company_name: str = ""
    subject: str = ""
    cleaned_body: str = ""
    country: str = ""
    product: str = ""
    product_specs: str = ""
    quantity: str = ""
    unit: str = ""
    incoterm_if_any: str = ""
    destination_port_if_any: str = ""
    contact_details: str = ""
    detected_intent: str = ""


@dataclass(slots=True)
class EmailHandoffRecommendations:
    send_to_crm: bool = False
    send_to_quotation: bool = False
    send_to_followup: bool = False
    send_to_research: bool = False


@dataclass(slots=True)
class EmailAgentOutput:
    status: AgentStatus
    message_class: MessageClass
    is_valid_inquiry: bool
    confidence_score: float
    extracted: InquiryExtracted
    handoff_recommendations: EmailHandoffRecommendations
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class QuotationDrafts:
    reply_email_subject: str = ""
    reply_email_body: str = ""
    quotation_summary: str = ""


@dataclass(slots=True)
class QuotationAgentOutput:
    status: AgentStatus
    quotation_readiness: Literal["ready", "missing_data", "blocked"]
    missing_fields: list[str] = field(default_factory=list)
    pricing_assumptions: list[str] = field(default_factory=list)
    drafts: QuotationDrafts = field(default_factory=QuotationDrafts)
    commercial_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CRMAgentOutput:
    status: AgentStatus
    operation: Literal["create", "update", "upsert", "skip"]
    crm_record_id: str
    lead_status: str
    deduplication_result: str
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FollowupAction:
    action: str
    owner: str
    due_at: str


@dataclass(slots=True)
class FollowupAgentOutput:
    status: AgentStatus
    priority_level: Literal["high", "medium", "low"]
    recommended_actions: list[FollowupAction] = field(default_factory=list)
    sla_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ResearchFinding:
    topic: str
    detail: str
    severity: Literal["low", "medium", "high"]


@dataclass(slots=True)
class ResearchAgentOutput:
    status: AgentStatus
    risk_level: Literal["low", "medium", "high", "unknown"]
    advisory_only: bool
    findings: list[ResearchFinding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PipelineRecord:
    message_id: str
    email: EmailAgentOutput
    quotation: QuotationAgentOutput | None = None
    crm: CRMAgentOutput | None = None
    followup: FollowupAgentOutput | None = None
    research: ResearchAgentOutput | None = None


@dataclass(slots=True)
class OrchestratorOutput:
    task: str
    plan: list[PlanStep]
    status: AgentStatus
    notes: list[str]
    pipelines: list[PipelineRecord] = field(default_factory=list)
    human_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
