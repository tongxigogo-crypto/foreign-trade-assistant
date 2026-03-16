import json
from app.contracts import Inquiry
from app.config import PRICING_RULES
from app.data_access.pricing_source import load_pricing
from app.orchestrator import Orchestrator


def main() -> None:
    pricing = load_pricing(PRICING_RULES)
    orch = Orchestrator(pricing)
    inquiry = Inquiry(
        sender_email="demo@example.com",
        subject="Need wall panels",
        body="We are a distributor. Please quote your model options.",
    )
    result = orch.run_new_customer(inquiry)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
