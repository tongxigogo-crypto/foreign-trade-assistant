"""Email agent implementation."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from app.contracts import (
    EmailAgentOutput,
    EmailHandoffRecommendations,
    InquiryExtracted,
    MessageClass,
)


class EmailAgent:
    def process_message(self, message: dict) -> EmailAgentOutput:
        subject = str(message.get("subject", ""))
        body = str(message.get("body", ""))
        lowered = f"{subject} {body}".lower()
        message_class = self._classify(lowered, str(message.get("sender", "")))

        extracted = InquiryExtracted(
            message_id=str(message.get("message_id", "")),
            thread_id=str(message.get("thread_id", "")),
            date=str(message.get("received_at", datetime.now(timezone.utc).isoformat())),
            sender_name=str(message.get("sender_name", message.get("customer_name", ""))),
            sender_email=str(message.get("sender", "")),
            company_name=str(message.get("company_name", "")),
            subject=subject,
            cleaned_body=re.sub(r"\s+", " ", body).strip()[:2000],
            country=self._extract_country(lowered),
            product=self._extract_product(lowered),
            product_specs=self._extract_specs(body),
            quantity=self._extract_quantity(lowered),
            unit=self._extract_unit(lowered),
            incoterm_if_any=self._extract_incoterm(lowered),
            destination_port_if_any=self._extract_destination(lowered),
            contact_details=str(message.get("contact_details", "")),
            detected_intent="request_quotation" if message_class == "inquiry" else "",
        )
        is_valid_inquiry = message_class in {"inquiry", "follow_up_from_customer"}
        missing = [k for k, v in {"product": extracted.product, "quantity": extracted.quantity}.items() if not v]

        if not is_valid_inquiry:
            return EmailAgentOutput(
                status="partial",
                message_class=message_class,
                is_valid_inquiry=False,
                confidence_score=0.6,
                extracted=extracted,
                handoff_recommendations=EmailHandoffRecommendations(),
                notes=["Message is not a valid foreign trade inquiry."],
            )
        if missing:
            return EmailAgentOutput(
                status="needs_input",
                message_class=message_class,
                is_valid_inquiry=True,
                confidence_score=0.72,
                extracted=extracted,
                handoff_recommendations=EmailHandoffRecommendations(
                    send_to_crm=True,
                    send_to_followup=True,
                ),
                notes=[f"Missing required fields: {', '.join(missing)}."],
            )
        return EmailAgentOutput(
            status="success",
            message_class=message_class,
            is_valid_inquiry=True,
            confidence_score=0.9,
            extracted=extracted,
            handoff_recommendations=EmailHandoffRecommendations(
                send_to_crm=True,
                send_to_quotation=True,
                send_to_research=bool(extracted.destination_port_if_any),
            ),
            notes=[],
        )

    def _classify(self, lowered: str, sender: str) -> MessageClass:
        if any(k in lowered for k in ("quote", "quotation", "rfq", "inquiry", "price")):
            return "inquiry"
        if any(k in lowered for k in ("shipment", "tracking", "bill of lading")):
            return "logistics_notice"
        if any(k in lowered for k in ("vendor", "supplier", "factory")):
            return "supplier_message"
        if "unsubscribe" in lowered:
            return "advertising_or_spam"
        if sender.endswith("@mycompany.com"):
            return "internal_or_irrelevant"
        return "unknown"

    def _extract_country(self, text: str) -> str:
        m = re.search(r"\bto\s+([a-z ]{2,40})\b", text)
        return m.group(1).strip().title() if m else ""

    def _extract_product(self, text: str) -> str:
        m = re.search(r"\b([a-z]{2,8}-\d{2,5})\b", text)
        return m.group(1).upper() if m else ""

    def _extract_specs(self, body: str) -> str:
        m = re.search(r"specs?:\s*(.+)", body, flags=re.IGNORECASE)
        return m.group(1).strip()[:200] if m else ""

    def _extract_quantity(self, text: str) -> str:
        m = re.search(r"\b(\d{1,7})\s*(pcs|pieces|units)\b", text)
        if m:
            return m.group(1)
        m = re.search(r"\bquantity[:\s]+(\d{1,7})\b", text)
        return m.group(1) if m else ""

    def _extract_unit(self, text: str) -> str:
        m = re.search(r"\b\d{1,7}\s*(pcs|pieces|units)\b", text)
        return m.group(1) if m else ""

    def _extract_incoterm(self, text: str) -> str:
        m = re.search(r"\b(exw|fob|cif|ddp|dap)\b", text)
        return m.group(1).upper() if m else ""

    def _extract_destination(self, text: str) -> str:
        m = re.search(r"(?:to|destination)\s+([a-z ]{2,40})", text)
        return m.group(1).strip().title() if m else ""
