from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


class DiagnosticsStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.diagnostics_dir = data_dir / "diagnostics"
        self.log_file = self.diagnostics_dir / "runtime.log.jsonl"
        self.feedback_file = self.diagnostics_dir / "feedback.jsonl"
        self.feedback_webhook_url = os.getenv("TA_FEEDBACK_WEBHOOK_URL", "").strip()
        self.feedback_webhook_token = os.getenv("TA_FEEDBACK_WEBHOOK_TOKEN", "").strip()
        self.instance_id = os.getenv("TA_FEEDBACK_INSTANCE_ID", "").strip() or data_dir.name

    def ensure_initialized(self) -> None:
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.write_text("", encoding="utf-8")
        if not self.feedback_file.exists():
            self.feedback_file.write_text("", encoding="utf-8")

    def write_log(self, level: str, message: str, context: dict | None = None) -> None:
        self.ensure_initialized()
        payload = {
            "at_utc": datetime.now(UTC).isoformat(),
            "level": level,
            "message": message,
            "context": context or {},
        }
        self._append_jsonl(self.log_file, payload)

    def append_feedback(self, source: str, text: str, extra: dict | None = None) -> dict:
        self.ensure_initialized()
        payload = {
            "at_utc": datetime.now(UTC).isoformat(),
            "instance_id": self.instance_id,
            "source": source.strip() or "desktop",
            "text": text.strip(),
            "extra": extra or {},
        }
        payload["relay"] = self._relay_feedback(payload)
        self._append_jsonl(self.feedback_file, payload)
        return payload

    def tail_feedback(self, limit: int = 100, sources: set[str] | None = None) -> list[dict]:
        rows = _read_tail_jsonl(self.feedback_file, max_items=max(1, limit * 5))
        if not sources:
            return rows[-max(1, limit) :]
        wanted = {item.strip().lower() for item in sources if item and item.strip()}
        filtered: list[dict] = []
        for row in rows:
            source = str(row.get("source", "")).strip().lower()
            if source in wanted:
                filtered.append(row)
        return filtered[-max(1, limit) :]

    def feedback_summary(self, limit: int = 500) -> dict:
        rows = self.tail_feedback(limit=max(1, limit))
        by_source: dict[str, int] = {}
        by_relay: dict[str, int] = {}
        latest_item = rows[-1] if rows else None
        for row in rows:
            source = str(row.get("source", "")).strip() or "unknown"
            by_source[source] = by_source.get(source, 0) + 1
            relay = str(row.get("relay", "unknown")).strip() or "unknown"
            by_relay[relay] = by_relay.get(relay, 0) + 1
        return {
            "instance_id": self.instance_id,
            "total": len(rows),
            "by_source": by_source,
            "by_relay": by_relay,
            "latest_at_utc": str(latest_item.get("at_utc", "")) if isinstance(latest_item, dict) else "",
        }

    def export_snapshot(self, target: Path, include_tail: int = 200) -> Path:
        self.ensure_initialized()
        logs = _read_tail_jsonl(self.log_file, include_tail)
        feedback = _read_tail_jsonl(self.feedback_file, include_tail)
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "diagnostics_dir": str(self.diagnostics_dir),
            "log_file": str(self.log_file),
            "feedback_file": str(self.feedback_file),
            "log_tail": logs,
            "feedback_tail": feedback,
        }
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target

    def health_check(self, *, knowledge_file: Path, state_board_file: Path, output_dir: Path) -> dict:
        checks = []
        checks.append(_check_path(knowledge_file, "knowledge_file", should_be_file=True, create_if_missing=True))
        checks.append(_check_path(state_board_file, "state_board_file", should_be_file=True, create_if_missing=True))
        checks.append(_check_path(output_dir, "output_dir", should_be_file=False, create_if_missing=True))
        checks.append(_check_path(self.log_file, "runtime_log_file", should_be_file=True, create_if_missing=True))
        checks.append(_check_path(self.feedback_file, "feedback_file", should_be_file=True, create_if_missing=True))
        ok = all(item.get("status") == "ok" for item in checks)
        return {
            "status": "ok" if ok else "degraded",
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "checks": checks,
        }

    def tail_logs(self, limit: int = 80, levels: set[str] | None = None) -> list[dict]:
        rows = _read_tail_jsonl(self.log_file, max_items=max(1, limit * 3))
        if not levels:
            return rows[-max(1, limit) :]
        wanted = {item.strip().lower() for item in levels if item and item.strip()}
        filtered: list[dict] = []
        for row in rows:
            level = str(row.get("level", "")).strip().lower()
            if level in wanted:
                filtered.append(row)
        return filtered[-max(1, limit) :]

    def _append_jsonl(self, path: Path, payload: dict) -> None:
        line = json.dumps(payload, ensure_ascii=False)
        for attempt in range(5):
            try:
                with path.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")
                return
            except PermissionError:
                time.sleep(0.08 * (attempt + 1))

    def _relay_feedback(self, payload: dict) -> str:
        if not self.feedback_webhook_url:
            return "not_configured"
        body = dict(payload)
        token = self.feedback_webhook_token
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = Request(
            url=self.feedback_webhook_url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with urlopen(req, timeout=3) as resp:  # noqa: S310
                if 200 <= int(getattr(resp, "status", 0)) < 300:
                    return "sent"
                return "failed"
        except (URLError, OSError, TimeoutError):
            return "failed"


def _check_path(path: Path, label: str, *, should_be_file: bool, create_if_missing: bool) -> dict:
    result = {"label": label, "path": str(path), "status": "ok", "detail": ""}
    try:
        if should_be_file:
            if not path.exists() and create_if_missing:
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".json":
                    path.write_text("{}\n", encoding="utf-8")
                else:
                    path.write_text("", encoding="utf-8")
            elif path.exists() and not path.is_file():
                result["status"] = "failed"
                result["detail"] = "expected file but found non-file"
                return result
            if not path.exists():
                result["status"] = "failed"
                result["detail"] = "file missing"
        else:
            if not path.exists() and create_if_missing:
                path.mkdir(parents=True, exist_ok=True)
            elif path.exists() and not path.is_dir():
                result["status"] = "failed"
                result["detail"] = "expected directory but found non-directory"
                return result
            if not path.exists():
                result["status"] = "failed"
                result["detail"] = "directory missing"
    except OSError as exc:
        result["status"] = "failed"
        result["detail"] = str(exc)
    return result


def _read_tail_jsonl(path: Path, max_items: int) -> list[dict]:
    if not path.exists() or not path.is_file():
        return []
    rows: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return rows[-max(1, max_items) :]
