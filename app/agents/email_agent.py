from app.contracts import AgentResult, Inquiry


class EmailAgent:
    def parse(self, inquiry: Inquiry) -> AgentResult:
        role = "unknown"
        body = inquiry.body.lower()
        if any(k in body for k in ["distributor", "reseller", "wholesale"]):
            role = "trader"
        if any(k in body for k in ["project", "epc", "tender"]):
            role = "engineering_contractor"
        return AgentResult(status="success", data={
            "sender_email": inquiry.sender_email,
            "subject": inquiry.subject,
            "role_hint": role,
            "product_direction": "specified" if "model" in body else "needs_recommendation",
        })
