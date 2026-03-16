from app.contracts import AgentResult


class ResearchAgent:
    def analyze(self, email_data: dict) -> AgentResult:
        return AgentResult(status="success", data={
            "market_snapshot": "advisory",
            "risk_level": "medium",
            "region": "unknown",
        })
