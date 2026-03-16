from app.contracts import AgentResult


class FollowupAgent:
    def plan(self, email_data: dict) -> AgentResult:
        return AgentResult(status="success", data={
            "priority": "high" if email_data.get("role_hint") != "unknown" else "medium",
            "next_action": "send draft after review",
        })
