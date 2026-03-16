from app.contracts import AgentResult


class QuotationAgent:
    def draft(self, email_data: dict, research_data: dict, pricing: dict) -> AgentResult:
        fallback = pricing.get("fallbackUnitPrice", 100)
        currency = pricing.get("defaultCurrency", "USD")
        return AgentResult(status="success", data={
            "quote_suggestion": f"{fallback}-{round(fallback*1.2,2)} {currency}",
            "reply_draft": "Thanks for your inquiry. Please confirm quantity/spec and destination port.",
        })
