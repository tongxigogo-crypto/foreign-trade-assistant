import json
from pathlib import Path

from app.config import Settings
from app.orchestrator import TradeOpsOrchestrator


def test_orchestrator_runs_with_structured_output(tmp_path: Path) -> None:
    (tmp_path / "pricing.json").write_text(
        json.dumps({"products": {"MIC-100": {"unit_price": 50.0, "currency": "USD"}}}),
        encoding="utf-8",
    )
    (tmp_path / "freight.json").write_text(
        json.dumps({"default_freight_per_unit": 3.0, "ports": {"rotterdam": 4.0}}),
        encoding="utf-8",
    )
    (tmp_path / "compliance.json").write_text(
        json.dumps({"high_risk_destinations": [], "watch_keywords": []}),
        encoding="utf-8",
    )

    settings = Settings(
        app_env="test",
        log_level="INFO",
        log_path=tmp_path / "system.log",
        crm_store_path=tmp_path / "crm.json",
        pricing_rules_path=tmp_path / "pricing.json",
        freight_rules_path=tmp_path / "freight.json",
        compliance_rules_path=tmp_path / "compliance.json",
        retry_max_attempts=1,
        retry_base_delay_seconds=0.01,
    )
    orchestrator = TradeOpsOrchestrator(settings=settings)
    result = orchestrator.run(
        [
            {
                "message_id": "m-1",
                "thread_id": "t-1",
                "sender": "buyer@example.com",
                "sender_name": "Buyer",
                "subject": "RFQ for MIC-100",
                "body": "Please quote MIC-100 100 pcs to Rotterdam.",
                "received_at": "2026-03-12T01:00:00Z",
            }
        ]
    )
    assert result.task == "daily_foreign_trade_email_pipeline"
    assert result.status in {"success", "partial", "needs_input", "failed"}
    assert len(result.pipelines) == 1
    assert len(result.plan) == 5
