"""JSON CRM store with idempotent writes and audit trail."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CRMStore:
    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self._save({"customers": {}, "processed_events": [], "audit": []})

    def _load(self) -> dict[str, Any]:
        with self.store_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, payload: dict[str, Any]) -> None:
        with self.store_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def apply_update(
        self,
        *,
        event_id: str,
        customer_email: str,
        customer_status: str,
        note: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self._load()
        if event_id in payload["processed_events"]:
            return {
                "write_applied": False,
                "customer_status": payload["customers"].get(customer_email, {}).get(
                    "status", customer_status
                ),
                "audit_record_id": f"idempotent-{event_id}",
            }

        timestamp = datetime.now(timezone.utc).isoformat()
        audit_record_id = str(uuid.uuid4())
        payload["customers"][customer_email] = {
            "status": customer_status,
            "updated_at": timestamp,
            "note": note,
            "metadata": metadata or {},
        }
        payload["processed_events"].append(event_id)
        payload["audit"].append(
            {
                "audit_record_id": audit_record_id,
                "event_id": event_id,
                "customer_email": customer_email,
                "customer_status": customer_status,
                "note": note,
                "metadata": metadata or {},
                "created_at": timestamp,
            }
        )
        self._save(payload)
        return {
            "write_applied": True,
            "customer_status": customer_status,
            "audit_record_id": audit_record_id,
        }
