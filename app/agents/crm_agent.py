"""CRM agent implementation."""

from __future__ import annotations

from app.contracts import CRMAgentOutput, InquiryExtracted
from app.data_access.crm_store import CRMStore


class CRMAgent:
    def __init__(self, store: CRMStore) -> None:
        self.store = store

    def upsert_lead(self, *, inquiry: InquiryExtracted, lead_status: str, source: str) -> CRMAgentOutput:
        if not inquiry.sender_email:
            return CRMAgentOutput(
                status="needs_input",
                operation="skip",
                crm_record_id="",
                lead_status=lead_status,
                deduplication_result="missing_customer_email",
                notes=["Cannot write CRM record without customer_email."],
            )
        event_id = f"{inquiry.message_id}:{lead_status}"
        metadata = {
            "lead_id": inquiry.message_id,
            "date_created": inquiry.date,
            "last_updated": inquiry.date,
            "customer_name": inquiry.sender_name,
            "customer_email": inquiry.sender_email,
            "company_name": inquiry.company_name,
            "country": inquiry.country,
            "product": inquiry.product,
            "product_specs": inquiry.product_specs,
            "quantity": inquiry.quantity,
            "inquiry_source": source,
            "lead_status": lead_status,
            "owner_if_any": "",
            "notes": "",
        }
        result = self.store.apply_update(
            event_id=event_id,
            customer_email=inquiry.sender_email,
            customer_status=lead_status,
            note=f"Lead {lead_status} via orchestrator",
            metadata=metadata,
        )
        applied = bool(result["write_applied"])
        return CRMAgentOutput(
            status="success",
            operation="upsert" if applied else "skip",
            crm_record_id=str(result["audit_record_id"]),
            lead_status=str(result["customer_status"]),
            deduplication_result="write_applied" if applied else "duplicate_event",
            notes=[],
        )
