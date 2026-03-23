from __future__ import annotations

import json
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .action_protocol import ActionExecutor, dedupe_actions, parse_actions
from .contracts import ActionExecutionResult
from .diagnostics import DiagnosticsStore
from .state_board import StateBoard
from .user_settings import UserSettingsStore


def run_dashboard_server(
    state_board: StateBoard,
    action_executor: ActionExecutor,
    settings_store: UserSettingsStore,
    host: str = "127.0.0.1",
    port: int = 8787,
    open_browser: bool = False,
) -> None:
    handler = _build_handler(state_board, action_executor, settings_store)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}"
    print(json.dumps({"status": "dashboard_started", "url": url}, ensure_ascii=False))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(state_board: StateBoard, action_executor: ActionExecutor, settings_store: UserSettingsStore):
    diagnostics = DiagnosticsStore(state_board.board_file.parent)
    diagnostics.ensure_initialized()

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                self._send_html(_dashboard_html())
                return
            if parsed.path == "/api/state/latest":
                events = state_board.latest(limit=50)
                self._send_json({"count": len(events), "events": events})
                return
            if parsed.path == "/api/state/summary":
                self._send_json({"summary": state_board.summary()})
                return
            if parsed.path == "/api/state/kanban":
                self._send_json({"columns": state_board.kanban(limit=200)})
                return
            if parsed.path == "/api/state/customers":
                rows = state_board.customer_lines(limit=100)
                self._send_json({"count": len(rows), "rows": rows})
                return
            if parsed.path == "/api/state/focus":
                q = parse_qs(parsed.query)
                limit = int(q.get("limit", ["8"])[0]) if q.get("limit") else 8
                rows = state_board.focus(limit=max(1, min(limit, 30)))
                self._send_json({"count": len(rows), "rows": rows})
                return
            if parsed.path == "/api/state/alerts":
                q = parse_qs(parsed.query)
                limit = int(q.get("limit", ["6"])[0]) if q.get("limit") else 6
                rows = state_board.alerts(limit=max(1, min(limit, 30)))
                self._send_json({"count": len(rows), "rows": rows})
                return
            if parsed.path == "/api/state/customer":
                q = parse_qs(parsed.query)
                cid = q.get("customer_id", [""])[0].strip()
                if not cid:
                    self._send_json({"error": "missing_customer_id"}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._send_json({"detail": state_board.customer_detail(customer_id=cid, limit_events=80)})
                return
            if parsed.path == "/api/settings":
                settings = settings_store.load()
                self._send_json({"settings": settings.to_dict(), "effective_output_dir": str(action_executor.output_dir)})
                return
            if parsed.path == "/api/diagnostics/status":
                report = diagnostics.health_check(
                    knowledge_file=action_executor.store.knowledge_file,
                    state_board_file=state_board.board_file,
                    output_dir=action_executor.output_dir,
                )
                issues = diagnostics.tail_logs(limit=80, levels={"warn", "error"})
                report["issue_logs"] = issues
                self._send_json(report)
                return
            if parsed.path == "/api/artifact/read":
                q = parse_qs(parsed.query)
                target = q.get("path", [""])[0].strip()
                if not target:
                    self._send_json({"error": "missing_path"}, status=HTTPStatus.BAD_REQUEST)
                    return
                p = Path(target)
                if not p.exists() or not p.is_file():
                    self._send_json({"error": "file_not_found", "path": str(p)}, status=HTTPStatus.NOT_FOUND)
                    return
                self._send_json({"path": str(p), "content": p.read_text(encoding="utf-8", errors="ignore")[:20000]})
                return
            self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/task/update":
                payload = self._read_json()
                task = state_board.update_task_status(
                    task_id=str(payload.get("task_id", "")).strip(),
                    status=str(payload.get("status", "")).strip(),
                    note=str(payload.get("note", "")).strip(),
                )
                if task is None:
                    self._send_json(
                        {"status": "failed", "message": "task not found or invalid status"},
                        status=HTTPStatus.BAD_REQUEST,
                    )
                    return
                self._send_json({"status": "ok", "task": task})
                return
            if parsed.path == "/api/action/execute":
                payload = self._read_json()
                action_text = str(payload.get("action_text", "")).strip()
                if not action_text:
                    self._send_json({"status": "failed", "message": "missing action_text"}, status=HTTPStatus.BAD_REQUEST)
                    return
                commands = dedupe_actions(parse_actions(action_text))
                if not commands:
                    self._send_json({"status": "failed", "message": "no action found"}, status=HTTPStatus.BAD_REQUEST)
                    return
                idem_key = str(payload.get("idempotency_key", "")).strip()
                if idem_key:
                    cached = state_board.get_idempotent_result(idem_key)
                    if cached:
                        self._send_json(
                            {
                                "status": "ok",
                                "results": cached.get("results", []),
                                "state_event": cached.get("event", {}),
                                "idempotent": True,
                            }
                        )
                        return
                results: list[ActionExecutionResult] = [action_executor.run_with_retry(cmd, max_attempts=3) for cmd in commands]
                event = state_board.append_execution(action_name=commands[0].name, results=results)
                result_data = [item.to_dict() for item in results]
                if idem_key:
                    state_board.set_idempotent_result(idem_key, event=event, results=result_data)
                diagnostics.write_log(
                    "info",
                    "dashboard_action_execute",
                    {"actions": [c.name for c in commands], "idempotency_key": idem_key, "statuses": [r.status for r in results]},
                )
                self._send_json({"status": "ok", "results": result_data, "state_event": event})
                return
            if parsed.path == "/api/alert/ack":
                payload = self._read_json()
                task_id = str(payload.get("task_id", "")).strip()
                snooze = int(payload.get("snooze_hours", 24)) if str(payload.get("snooze_hours", "")).strip() else 24
                ack = state_board.ack_alert(task_id=task_id, snooze_hours=max(1, min(snooze, 168)))
                if ack is None:
                    self._send_json({"status": "failed", "message": "task not found"}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._send_json({"status": "ok", "ack": ack})
                return
            if parsed.path == "/api/settings/output-dir":
                payload = self._read_json()
                raw = str(payload.get("output_dir", "")).strip()
                if not raw:
                    self._send_json({"status": "failed", "message": "output_dir is required"}, status=HTTPStatus.BAD_REQUEST)
                    return
                target = Path(raw).expanduser().resolve()
                try:
                    target.mkdir(parents=True, exist_ok=True)
                except OSError as exc:
                    self._send_json({"status": "failed", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                action_executor.output_dir = target
                settings = settings_store.load()
                settings.output_dir = str(target)
                settings_store.save(settings)
                self._send_json({"status": "ok", "output_dir": str(target)})
                return
            if parsed.path == "/api/diagnostics/export":
                target = diagnostics.diagnostics_dir / "dashboard_diagnostics_export.json"
                written = diagnostics.export_snapshot(target=target, include_tail=300)
                self._send_json({"status": "ok", "path": str(written)})
                return
            self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {}

        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(int(HTTPStatus.OK))
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return DashboardHandler


def _dashboard_html() -> str:
    ui_file = Path(__file__).with_name("dashboard_ui.html")
    try:
        return ui_file.read_text(encoding="utf-8")
    except OSError:
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Trade Assistant</title></head>"
            "<body><h1>Trade Assistant Dashboard</h1><p>Missing dashboard_ui.html</p></body></html>"
        )
