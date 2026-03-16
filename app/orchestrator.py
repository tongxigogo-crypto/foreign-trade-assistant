from app.contracts import Inquiry
from app.agents.email_agent import EmailAgent
from app.agents.research_agent import ResearchAgent
from app.agents.quotation_agent import QuotationAgent
from app.agents.crm_agent import CrmAgent
from app.agents.followup_agent import FollowupAgent


class Orchestrator:
    def __init__(self, pricing: dict):
        self.email_agent = EmailAgent()
        self.research_agent = ResearchAgent()
        self.quotation_agent = QuotationAgent()
        self.crm_agent = CrmAgent()
        self.followup_agent = FollowupAgent()
        self.pricing = pricing

    def run_new_customer(self, inquiry: Inquiry) -> dict:
        email = self.email_agent.parse(inquiry)
        research = self.research_agent.analyze(email.data)
        quote = self.quotation_agent.draft(email.data, research.data, self.pricing)
        crm = self.crm_agent.upsert(email.data)
        followup = self.followup_agent.plan(email.data)
        return {
            "status": "success",
            "workflow_type": "new_customer",
            "email": email.data,
            "research": research.data,
            "quote": quote.data,
            "crm": crm.data,
            "followup": followup.data,
        }
