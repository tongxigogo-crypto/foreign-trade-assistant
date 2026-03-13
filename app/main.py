"""Project entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

from app.orchestrator import TradeOpsOrchestrator


def load_messages() -> list[dict]:
    sample = Path("data/inbox_sample.json")
    if sample.exists():
        with sample.open("r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {
            "message_id": "sample-1",
            "thread_id": "thread-1",
            "sender": "buyer@example.com",
            "sender_name": "Buyer",
            "subject": "RFQ for MIC-100",
            "body": "Please quote MIC-100 120 pcs to Rotterdam. Specs: black finish.",
            "received_at": "2026-03-12T00:00:00Z",
        }
    ]


def main() -> None:
    result = TradeOpsOrchestrator().run(load_messages())
    print(result.human_summary)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
