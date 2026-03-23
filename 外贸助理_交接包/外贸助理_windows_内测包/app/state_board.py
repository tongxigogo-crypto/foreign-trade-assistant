from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
import time
from uuid import uuid4

from .contracts import ActionExecutionResult


class StateBoard:
    def __init__(self, board_file: Path) -> None:
        self.board_file = board_file

    def ensure_initialized(self) -> None:
        self.board_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.board_file.exists():
            self._write({"events": [], "tasks": [], "alert_acks": {}, "idempotency_cache": {}})
            return
        board = self._read()
        mutated = False
        if "events" not in board:
            board["events"] = []
            mutated = True
        if "tasks" not in board:
            board["tasks"] = []
            mutated = True
        if "alert_acks" not in board:
            board["alert_acks"] = {}
            mutated = True
        if "idempotency_cache" not in board:
            board["idempotency_cache"] = {}
            mutated = True
        if mutated:
            self._write(board)

    def append_execution(self, action_name: str, results: list[ActionExecutionResult]) -> dict:
        self.ensure_initialized()
        board = self._read()
        event = {
            "event_id": str(uuid4()),
            "created_at_utc": datetime.now(UTC).isoformat(),
            "action_name": action_name,
            "results": [item.to_dict() for item in results],
        }
        board.setdefault("events", []).append(event)
        board["events"] = board["events"][-200:]
        self._write(board)
        return event

    def get_idempotent_result(self, key: str) -> dict | None:
        self.ensure_initialized()
        token = key.strip()
        if not token:
            return None
        board = self._read()
        cache = board.get("idempotency_cache", {})
        if not isinstance(cache, dict):
            return None
        entry = cache.get(token)
        if not isinstance(entry, dict):
            return None
        at_text = str(entry.get("at_utc", "")).strip()
        if at_text:
            try:
                at = datetime.fromisoformat(at_text)
                if at.tzinfo is None:
                    at = at.replace(tzinfo=UTC)
                ttl_seconds = 15 if token.startswith("auto:") else 300
                if datetime.now(UTC) - at > timedelta(seconds=ttl_seconds):
                    return None
            except ValueError:
                return None
        return entry

    def set_idempotent_result(self, key: str, event: dict, results: list[dict]) -> None:
        self.ensure_initialized()
        token = key.strip()
        if not token:
            return
        board = self._read()
        cache = board.setdefault("idempotency_cache", {})
        if not isinstance(cache, dict):
            cache = {}
            board["idempotency_cache"] = cache
        cache[token] = {
            "at_utc": datetime.now(UTC).isoformat(),
            "event": event,
            "results": results,
        }
        if len(cache) > 500:
            keys = sorted(cache.keys(), key=lambda x: str(cache[x].get("at_utc", "")))
            for old in keys[: len(cache) - 500]:
                cache.pop(old, None)
        self._write(board)

    def latest(self, limit: int = 20) -> list[dict]:
        self.ensure_initialized()
        events = self._read().get("events", [])
        return list(events[-limit:])

    def create_followup_task(
        self,
        customer_id: str,
        customer_name: str,
        title: str,
        due_in_days: int = 3,
        priority: str = "normal",
        source_event_id: str = "",
        dedupe_open_task: bool = True,
        initial_status: str = "waiting_reply",
    ) -> dict:
        self.ensure_initialized()
        board = self._read()
        if initial_status not in {"waiting_reply", "in_progress", "completed"}:
            initial_status = "waiting_reply"
        if dedupe_open_task:
            for task in reversed(board.get("tasks", [])):
                if task.get("customer_id") != customer_id:
                    continue
                if task.get("title") != title:
                    continue
                if task.get("status") == "completed":
                    continue
                task["updated_at_utc"] = datetime.now(UTC).isoformat()
                if source_event_id:
                    task["source_event_id"] = source_event_id
                self._write(board)
                return task
        task = {
            "task_id": str(uuid4()),
            "created_at_utc": datetime.now(UTC).isoformat(),
            "customer_id": customer_id,
            "customer_name": customer_name,
            "title": title,
            "status": initial_status,
            "priority": priority,
            "due_at_utc": (datetime.now(UTC) + timedelta(days=max(1, due_in_days))).isoformat(),
            "source_event_id": source_event_id,
            "notes": [],
            "updated_at_utc": datetime.now(UTC).isoformat(),
        }
        board.setdefault("tasks", []).append(task)
        board["tasks"] = board["tasks"][-500:]
        self._write(board)
        return task

    def update_task_status(self, task_id: str, status: str, note: str = "") -> dict | None:
        self.ensure_initialized()
        board = self._read()
        allowed = {"waiting_reply", "in_progress", "completed"}
        if status not in allowed:
            return None
        for task in board.get("tasks", []):
            if task.get("task_id") != task_id:
                continue
            task["status"] = status
            task["updated_at_utc"] = datetime.now(UTC).isoformat()
            if note.strip():
                task.setdefault("notes", []).append(note.strip())
            self._write(board)
            return task
        return None

    def transition_customer_tasks(
        self,
        customer_id: str,
        to_status: str,
        note: str = "",
        from_statuses: tuple[str, ...] = ("waiting_reply", "overdue"),
        max_items: int = 1,
    ) -> list[dict]:
        self.ensure_initialized()
        if to_status not in {"waiting_reply", "in_progress", "completed"}:
            return []
        board = self._read()
        changed: list[dict] = []
        count = 0
        for task in reversed(board.get("tasks", [])):
            if count >= max_items:
                break
            if task.get("customer_id") != customer_id:
                continue
            computed = self._with_computed_status(task).get("computed_status", "waiting_reply")
            if computed not in from_statuses and task.get("status") not in from_statuses:
                continue
            task["status"] = to_status
            task["updated_at_utc"] = datetime.now(UTC).isoformat()
            if note.strip():
                task.setdefault("notes", []).append(note.strip())
            changed.append(dict(task))
            count += 1
        if changed:
            self._write(board)
        return changed

    def list_tasks(self, limit: int = 100) -> list[dict]:
        self.ensure_initialized()
        tasks = self._read().get("tasks", [])
        enriched = [self._with_computed_status(task) for task in tasks]
        return list(enriched[-limit:])

    def kanban(self, limit: int = 200) -> dict[str, list[dict]]:
        tasks = self.list_tasks(limit=limit)
        columns = {
            "waiting_reply": [],
            "in_progress": [],
            "overdue": [],
            "completed": [],
        }
        for task in tasks:
            columns[task["computed_status"]].append(task)
        for key in columns:
            columns[key] = sorted(
                columns[key],
                key=lambda x: (
                    int(x.get("priority_score", 0)),
                    -self._due_timestamp_for_sort(x.get("due_at_utc", "")),
                ),
                reverse=True,
            )
        return columns

    def customer_lines(self, limit: int = 100) -> list[dict]:
        self.ensure_initialized()
        board = self._read()
        tasks = [self._with_computed_status(item) for item in board.get("tasks", [])]
        events = list(board.get("events", []))
        rows: dict[str, dict] = {}

        for task in tasks:
            customer_id = task.get("customer_id", "").strip() or "unknown_customer"
            customer_name = task.get("customer_name", "").strip() or customer_id
            row = rows.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "open_tasks": 0,
                    "overdue_tasks": 0,
                    "in_progress_tasks": 0,
                    "max_priority_score": 0,
                    "latest_task_due_at_utc": "",
                    "latest_event_at_utc": "",
                    "latest_event_action": "",
                    "latest_artifact": "",
                },
            )
            if task.get("computed_status") != "completed":
                row["open_tasks"] += 1
            if task.get("computed_status") == "overdue":
                row["overdue_tasks"] += 1
            if task.get("computed_status") == "in_progress":
                row["in_progress_tasks"] += 1
            score = int(task.get("priority_score", 0))
            if score > row["max_priority_score"]:
                row["max_priority_score"] = score
            due_at = str(task.get("due_at_utc", ""))
            if due_at and due_at > row["latest_task_due_at_utc"]:
                row["latest_task_due_at_utc"] = due_at

        for event in events:
            action = str(event.get("action_name", ""))
            created = str(event.get("created_at_utc", ""))
            results = event.get("results", []) if isinstance(event.get("results", []), list) else []
            candidate_artifact = ""
            for item in results:
                artifacts = item.get("artifacts", []) if isinstance(item, dict) else []
                if artifacts:
                    candidate_artifact = str(artifacts[0])
                    break
            customer_info = self._extract_event_customer(event)
            customer_id = customer_info.get("customer_id", "")
            if not customer_id:
                continue
            row = rows.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "customer_name": customer_info.get("customer_name", customer_id),
                    "open_tasks": 0,
                    "overdue_tasks": 0,
                    "in_progress_tasks": 0,
                    "max_priority_score": 0,
                    "latest_task_due_at_utc": "",
                    "latest_event_at_utc": "",
                    "latest_event_action": "",
                    "latest_artifact": "",
                },
            )
            if created > row["latest_event_at_utc"]:
                row["latest_event_at_utc"] = created
                row["latest_event_action"] = action
                row["latest_artifact"] = candidate_artifact
            if not row.get("customer_name") or row.get("customer_name") == row.get("customer_id"):
                row["customer_name"] = customer_info.get("customer_name", row.get("customer_name", customer_id))

        ordered = sorted(
            rows.values(),
            key=lambda x: (x["overdue_tasks"], x["max_priority_score"], x["open_tasks"], x["latest_event_at_utc"]),
            reverse=True,
        )
        return ordered[:limit]

    def customer_detail(self, customer_id: str, limit_events: int = 50) -> dict:
        self.ensure_initialized()
        cid = customer_id.strip()
        board = self._read()
        tasks = [self._with_computed_status(t) for t in board.get("tasks", []) if t.get("customer_id") == cid]
        events = []
        for event in board.get("events", []):
            guess = self._extract_event_customer(event).get("customer_id", "")
            if guess == cid:
                events.append(event)
        latest_artifacts: list[str] = []
        for event in reversed(events):
            for result in event.get("results", []) if isinstance(event.get("results", []), list) else []:
                if not isinstance(result, dict):
                    continue
                for art in result.get("artifacts", []) if isinstance(result.get("artifacts", []), list) else []:
                    art_text = str(art)
                    if art_text and art_text not in latest_artifacts:
                        latest_artifacts.append(art_text)
                if len(latest_artifacts) >= 10:
                    break
            if len(latest_artifacts) >= 10:
                break
        customer_name = tasks[-1]["customer_name"] if tasks else cid
        return {
            "customer_id": cid,
            "customer_name": customer_name,
            "tasks": tasks[-100:],
            "events": events[-limit_events:],
            "artifacts": latest_artifacts[:10],
        }

    def focus(self, limit: int = 5) -> list[dict]:
        tasks = self.list_tasks(limit=500)
        actionable = [t for t in tasks if t.get("computed_status") in {"overdue", "waiting_reply", "in_progress"}]
        for item in actionable:
            item["focus_reason"] = self._focus_reason(item)
        ordered = sorted(
            actionable,
            key=lambda x: (
                x.get("computed_status") == "overdue",
                int(x.get("priority_score", 0)),
                -self._due_timestamp_for_sort(x.get("due_at_utc", "")),
            ),
            reverse=True,
        )
        return ordered[: max(1, limit)]

    def summary(self) -> dict:
        tasks = self.list_tasks(limit=500)
        alerts = self.alerts(limit=500)
        status_counts = {
            "waiting_reply": 0,
            "in_progress": 0,
            "overdue": 0,
            "completed": 0,
        }
        high_priority_open = 0
        for item in tasks:
            status = str(item.get("computed_status", "waiting_reply"))
            if status not in status_counts:
                continue
            status_counts[status] += 1
            if status != "completed" and int(item.get("priority_score", 0)) >= 80:
                high_priority_open += 1
        alert_counts = {
            "overdue": 0,
            "due_soon": 0,
        }
        for item in alerts:
            kind = str(item.get("alert_type", ""))
            if kind in alert_counts:
                alert_counts[kind] += 1
        return {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "tasks_total": len(tasks),
            "status_counts": status_counts,
            "high_priority_open": high_priority_open,
            "alerts_total": len(alerts),
            "alert_counts": alert_counts,
        }

    def alerts(self, limit: int = 5) -> list[dict]:
        self.ensure_initialized()
        board = self._read()
        ack_map = board.get("alert_acks", {}) if isinstance(board.get("alert_acks", {}), dict) else {}
        candidates = self.focus(limit=500)
        now = datetime.now(UTC)
        rows: list[dict] = []
        for item in candidates:
            task_id = str(item.get("task_id", "")).strip()
            if not task_id:
                continue
            alert_type = self._alert_type(item, now=now)
            if not alert_type:
                continue
            ack_until_text = str(ack_map.get(task_id, "")).strip()
            if ack_until_text:
                try:
                    ack_until = datetime.fromisoformat(ack_until_text)
                    if ack_until.tzinfo is None:
                        ack_until = ack_until.replace(tzinfo=UTC)
                    if now < ack_until:
                        continue
                except ValueError:
                    pass
            enriched = dict(item)
            enriched["alert_type"] = alert_type
            enriched["alert_message"] = self._alert_message(item, alert_type=alert_type)
            rows.append(enriched)
        rows = sorted(
            rows,
            key=lambda x: (
                x.get("alert_type") == "overdue",
                int(x.get("priority_score", 0)),
                -self._due_timestamp_for_sort(x.get("due_at_utc", "")),
            ),
            reverse=True,
        )
        return rows[: max(1, limit)]

    def ack_alert(self, task_id: str, snooze_hours: int = 24) -> dict | None:
        self.ensure_initialized()
        tid = task_id.strip()
        if not tid:
            return None
        board = self._read()
        exists = any(str(item.get("task_id", "")) == tid for item in board.get("tasks", []))
        if not exists:
            return None
        until = (datetime.now(UTC) + timedelta(hours=max(1, snooze_hours))).isoformat()
        board.setdefault("alert_acks", {})[tid] = until
        self._write(board)
        return {"task_id": tid, "ack_until_utc": until}

    def _read(self) -> dict:
        text = self.board_file.read_text(encoding="utf-8")
        return json.loads(text)

    def _write(self, payload: dict) -> None:
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        for attempt in range(5):
            temp = self.board_file.with_suffix(self.board_file.suffix + f".tmp{attempt}")
            try:
                temp.write_text(content, encoding="utf-8")
                temp.replace(self.board_file)
                return
            except PermissionError:
                time.sleep(0.08 * (attempt + 1))
            finally:
                if temp.exists():
                    try:
                        temp.unlink()
                    except OSError:
                        pass
        self.board_file.write_text(content, encoding="utf-8")

    def _with_computed_status(self, task: dict) -> dict:
        item = dict(task)
        status = item.get("status", "waiting_reply")
        base_priority = self._priority_value(str(item.get("priority", "normal")))
        item["priority_score"] = base_priority
        if status == "completed":
            item["computed_status"] = "completed"
            item["suggested_action"] = ""
            return item
        due_text = item.get("due_at_utc", "")
        try:
            due_at = datetime.fromisoformat(due_text)
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=UTC)
        except ValueError:
            due_at = datetime.now(UTC) + timedelta(days=1)
        if datetime.now(UTC) > due_at:
            item["computed_status"] = "overdue"
            item["priority_score"] = max(item["priority_score"], 95)
            customer = item.get("customer_name", "Customer")
            item["suggested_action"] = (
                f"<action>generate_followup_draft:{{customer:'{customer}',reason:'overdue follow-up',tone:'firm_professional'}}</action>"
            )
            return item
        item["computed_status"] = status if status in {"waiting_reply", "in_progress"} else "waiting_reply"
        if item["computed_status"] == "in_progress":
            item["priority_score"] = max(item["priority_score"], 70)
        item["suggested_action"] = ""
        return item

    def _guess_customer_id_from_event(self, event: dict) -> str:
        info = self._extract_event_customer(event)
        return info.get("customer_id", "")

    def _extract_event_customer(self, event: dict) -> dict:
        results = event.get("results", [])
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                context = item.get("context", {}) if isinstance(item.get("context", {}), dict) else {}
                context_cid = str(context.get("customer_id", "")).strip()
                context_name = str(context.get("customer_name", "")).strip()
                if context_cid:
                    return {"customer_id": context_cid, "customer_name": context_name or context_cid}

        action = str(event.get("action_name", ""))
        if action == "ingest_email_thread":
            results = event.get("results", [])
            if isinstance(results, list) and results:
                message = str(results[0].get("message", "")) if isinstance(results[0], dict) else ""
                # "Ingested email thread for Vitor Maia; ..."
                if " for " in message:
                    name = message.split(" for ", 1)[1].split(";", 1)[0].strip()
                    return {"customer_id": name.lower().replace(" ", "-"), "customer_name": name}
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                message = str(item.get("message", ""))
                if " for " in message:
                    name = message.split(" for ", 1)[1].split(".", 1)[0].strip()
                    if name:
                        return {"customer_id": name.lower().replace(" ", "-"), "customer_name": name}
        return {"customer_id": "", "customer_name": ""}

    def _priority_value(self, text: str) -> int:
        value = text.strip().lower()
        if value == "high":
            return 85
        if value == "low":
            return 40
        return 60

    def _due_timestamp_for_sort(self, due_text: str) -> float:
        try:
            due = datetime.fromisoformat(str(due_text))
            if due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            return due.timestamp()
        except ValueError:
            return datetime.now(UTC).timestamp() + 86400 * 365

    def _focus_reason(self, task: dict) -> str:
        status = str(task.get("computed_status", "waiting_reply"))
        customer = str(task.get("customer_name", "Customer"))
        if status == "overdue":
            return f"{customer}: overdue and at risk of losing response window."
        if status == "in_progress":
            return f"{customer}: active execution task, finish to close loop."
        return f"{customer}: waiting reply, should be nudged before it turns overdue."

    def _alert_type(self, task: dict, now: datetime) -> str:
        status = str(task.get("computed_status", "waiting_reply"))
        if status == "overdue":
            return "overdue"
        if status == "in_progress":
            return ""
        score = int(task.get("priority_score", 0))
        due_at = self._due_datetime(task.get("due_at_utc", ""))
        if due_at is None:
            return ""
        if due_at - now <= timedelta(hours=12) and score >= 80:
            return "due_soon"
        return ""

    def _alert_message(self, task: dict, alert_type: str) -> str:
        customer = str(task.get("customer_name", "Customer"))
        title = str(task.get("title", "Task"))
        if alert_type == "overdue":
            return f"{customer}: '{title}' is overdue and needs immediate follow-up."
        return f"{customer}: '{title}' is due soon and may slip without action."

    def _due_datetime(self, due_text: str) -> datetime | None:
        try:
            due = datetime.fromisoformat(str(due_text))
            if due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            return due
        except ValueError:
            return None
