from app.contracts import Inquiry
from app.orchestrator import Orchestrator


def test_orchestrator_new_customer_success():
    orch = Orchestrator({"fallbackUnitPrice": 100, "defaultCurrency": "USD"})
    inquiry = Inquiry("x@example.com", "Need quote", "We are distributor and need model")
    result = orch.run_new_customer(inquiry)
    assert result["status"] == "success"
    assert result["workflow_type"] == "new_customer"
    assert "quote_suggestion" in result["quote"]
