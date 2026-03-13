from pathlib import Path

from app.data_access.crm_store import CRMStore


def test_crm_idempotent_write(tmp_path: Path) -> None:
    store = CRMStore(tmp_path / "crm.json")
    first = store.apply_update(
        event_id="evt-1",
        customer_email="buyer@example.com",
        customer_status="quote_ready",
        note="first",
    )
    second = store.apply_update(
        event_id="evt-1",
        customer_email="buyer@example.com",
        customer_status="quote_ready",
        note="second",
    )
    assert first["write_applied"] is True
    assert second["write_applied"] is False
