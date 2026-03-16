from app.contracts import AgentResult


class CrmAgent:
    def upsert(self, email_data: dict) -> AgentResult:
        return AgentResult(status="success", data={"operation": "upsert"})
