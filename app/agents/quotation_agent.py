"""Quotation agent implementation."""

from __future__ import annotations

from app.contracts import InquiryExtracted, QuotationAgentOutput, QuotationDrafts
from app.data_access.pricing_source import PricingSource


class QuotationAgent:
    def __init__(self, pricing_source: PricingSource) -> None:
        self.pricing_source = pricing_source

    def prepare(self, inquiry: InquiryExtracted) -> QuotationAgentOutput:
        missing = [k for k, v in {"product": inquiry.product, "quantity": inquiry.quantity}.items() if not v]
        if missing:
            return QuotationAgentOutput(
                status="needs_input",
                quotation_readiness="missing_data",
                missing_fields=missing,
                notes=["Cannot prepare quotation without required fields."],
            )
        product = self.pricing_source.get_product(inquiry.product)
        if not product:
            return QuotationAgentOutput(
                status="partial",
                quotation_readiness="blocked",
                commercial_flags=["missing_governed_pricing"],
                notes=[f"No governed price for {inquiry.product}."],
            )

        quantity = int(inquiry.quantity)
        unit_price = float(product["unit_price"])
        freight = self.pricing_source.get_freight_per_unit(inquiry.destination_port_if_any or None)
        total = (unit_price + freight) * quantity

        return QuotationAgentOutput(
            status="success",
            quotation_readiness="ready",
            pricing_assumptions=[
                "Product unit pricing from configured pricing source.",
                "Freight estimate from configured freight source.",
            ],
            drafts=QuotationDrafts(
                reply_email_subject=f"Quotation Draft - {inquiry.product} - {quantity} units",
                reply_email_body=(
                    f"Dear Customer,\n\nThank you for your inquiry for {inquiry.product}.\n"
                    f"Quantity: {quantity} {inquiry.unit or 'units'}\n"
                    f"Estimated unit price: USD {unit_price:.2f}\n"
                    f"Estimated freight per unit: USD {freight:.2f}\n"
                    f"Estimated total: USD {total:.2f}\n\n"
                    "Please confirm destination and requested terms for final quote.\n"
                ),
                quotation_summary=(
                    f"{inquiry.product} x {quantity}: unit {unit_price:.2f}, "
                    f"freight {freight:.2f}, total {total:.2f} USD."
                ),
            ),
            notes=[],
        )
