from __future__ import annotations

import json
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .action_protocol import dedupe_actions
from .contracts import ActionExecutionResult, CapsuleRequest
from .diagnostics import DiagnosticsStore
from .local_store import slugify_id
from .orchestrator import TradeAssistantOrchestrator
from .state_board import StateBoard


def run_bridge_server(
    orchestrator: TradeAssistantOrchestrator,
    state_board: StateBoard,
    host: str = "127.0.0.1",
    port: int = 8765,
    allow_action_execute: bool = False,
) -> None:
    handler = _build_handler(
        orchestrator=orchestrator,
        state_board=state_board,
        allow_action_execute=allow_action_execute,
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(
        json.dumps(
            {
                "status": "bridge_started",
                "host": host,
                "port": port,
                "allow_action_execute": allow_action_execute,
            },
            ensure_ascii=False,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(orchestrator: TradeAssistantOrchestrator, state_board: StateBoard, allow_action_execute: bool):
    diagnostics = DiagnosticsStore(state_board.board_file.parent)
    diagnostics.ensure_initialized()

    class BridgeHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            if parsed.path == "/feedback/inbox":
                query = parse_qs(parsed.query)
                try:
                    limit = int(query.get("limit", ["120"])[0])
                except (TypeError, ValueError):
                    limit = 120
                source_text = str(query.get("source", [""])[0] or "").strip().lower()
                source_set = {source_text} if source_text else None
                rows = diagnostics.tail_feedback(limit=max(1, min(limit, 500)), sources=source_set)
                summary = diagnostics.feedback_summary(limit=1000)
                self._send_html(HTTPStatus.OK, _feedback_inbox_html(rows=rows, summary=summary))
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/capsule/build":
                self._handle_build_capsule()
                return
            if self.path == "/actions/parse":
                self._handle_parse_actions()
                return
            if self.path == "/actions/execute":
                self._handle_execute_actions()
                return
            if self.path == "/conversation/sync":
                self._handle_conversation_sync()
                return
            if self.path == "/state/latest":
                self._handle_state_latest()
                return
            if self.path == "/state/focus":
                self._handle_state_focus()
                return
            if self.path == "/state/kanban":
                self._handle_state_kanban()
                return
            if self.path == "/state/alerts":
                self._handle_state_alerts()
                return
            if self.path == "/health/check":
                self._handle_health_check()
                return
            if self.path == "/diagnostics/export":
                self._handle_diagnostics_export()
                return
            if self.path == "/feedback/add":
                self._handle_feedback_add()
                return
            if self.path == "/feedback/list":
                self._handle_feedback_list()
                return
            if self.path == "/alert/ack":
                self._handle_alert_ack()
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _handle_build_capsule(self) -> None:
            payload = self._read_json()
            capsule = orchestrator.build_capsule(
                CapsuleRequest(
                    user_input=str(payload.get("user_input", "")),
                    customer_hint=str(payload.get("customer_hint", "")),
                    product_hint=str(payload.get("product_hint", "")),
                    model_name=str(payload.get("model_name", "")),
                    template_lang=str(payload.get("template_lang", "zh")),
                    template_mode=str(payload.get("template_mode", "standard")),
                    custom_instruction=str(payload.get("custom_instruction", "")),
                )
            )
            self._send_json(HTTPStatus.OK, {"capsule": capsule.to_dict()})

        def _handle_parse_actions(self) -> None:
            payload = self._read_json()
            model_output = str(payload.get("model_output", ""))
            actions = [item.to_dict() for item in dedupe_actions(orchestrator.parse_actions(model_output))]
            self._send_json(HTTPStatus.OK, {"count": len(actions), "actions": actions})

        def _handle_execute_actions(self) -> None:
            if not allow_action_execute:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": "action_execution_disabled", "message": "Start bridge with execution enabled."},
                )
                return
            if not self._is_allowed_execute_origin():
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"error": "forbidden_origin", "message": "Origin not allowed for action execution."},
                )
                return
            payload = self._read_json()
            model_output = str(payload.get("model_output", ""))
            parsed = dedupe_actions(orchestrator.parse_actions(model_output))
            idem_key = self._idempotency_key(payload=payload, actions=parsed)
            cached = state_board.get_idempotent_result(idem_key) if idem_key else None
            if cached:
                diagnostics.write_log("info", "idempotent_hit", {"key": idem_key})
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "count": len(cached.get("results", [])),
                        "results": cached.get("results", []),
                        "state_event": cached.get("event", {}),
                        "idempotent": True,
                    },
                )
                return
            executed = [orchestrator.action_executor.run_with_retry(item, max_attempts=3) for item in parsed]
            event = state_board.append_execution(
                action_name=parsed[0].name if parsed else "unknown",
                results=executed,
            )
            for command, result in zip(parsed, executed, strict=False):
                self._sync_task_state(command.name, command.payload, result.to_dict(), event.get("event_id", ""))
            results = [item.to_dict() for item in executed]
            if idem_key:
                state_board.set_idempotent_result(idem_key, event=event, results=results)
            diagnostics.write_log(
                "info",
                "actions_executed",
                {
                    "idempotency_key": idem_key,
                    "actions": [item.name for item in parsed],
                    "result_statuses": [item.status for item in executed],
                },
            )
            self._send_json(HTTPStatus.OK, {"count": len(results), "results": results, "state_event": event})

        def _handle_conversation_sync(self) -> None:
            payload = self._read_json()
            reply_text = str(payload.get("assistant_reply", "")).strip()
            model_name = str(payload.get("model_name", "")).strip() or "web-llm"
            if not reply_text:
                self._send_json(HTTPStatus.BAD_REQUEST, {"status": "failed", "message": "assistant_reply is required"})
                return
            kb = orchestrator.capsule_builder.store.append_conversation_snapshot(model_name=model_name, reply_text=reply_text)
            result = ActionExecutionResult(
                status="success",
                message=f"Conversation synced from {model_name}.",
                artifacts=[str(orchestrator.capsule_builder.store.knowledge_file)],
                context={"action": "conversation_sync", "model_name": model_name},
            )
            event = state_board.append_execution(action_name="conversation_sync", results=[result])
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "doc_facts_total": len(kb.doc_facts),
                    "state_event": event,
                },
            )
            diagnostics.write_log("info", "conversation_synced", {"model_name": model_name, "doc_facts_total": len(kb.doc_facts)})

        def _handle_state_latest(self) -> None:
            payload = self._read_json()
            try:
                limit = int(payload.get("limit", 20))
            except (TypeError, ValueError):
                limit = 20
            self._send_json(HTTPStatus.OK, {"events": state_board.latest(limit=max(1, min(limit, 100)))})

        def _handle_state_focus(self) -> None:
            payload = self._read_json()
            try:
                limit = int(payload.get("limit", 8))
            except (TypeError, ValueError):
                limit = 8
            self._send_json(HTTPStatus.OK, {"rows": state_board.focus(limit=max(1, min(limit, 30)))})

        def _handle_state_kanban(self) -> None:
            payload = self._read_json()
            try:
                limit = int(payload.get("limit", 200))
            except (TypeError, ValueError):
                limit = 200
            self._send_json(HTTPStatus.OK, {"columns": state_board.kanban(limit=max(1, min(limit, 500)))})

        def _handle_state_alerts(self) -> None:
            payload = self._read_json()
            try:
                limit = int(payload.get("limit", 6))
            except (TypeError, ValueError):
                limit = 6
            self._send_json(HTTPStatus.OK, {"rows": state_board.alerts(limit=max(1, min(limit, 30)))})

        def _handle_alert_ack(self) -> None:
            payload = self._read_json()
            task_id = str(payload.get("task_id", "")).strip()
            try:
                snooze_hours = int(payload.get("snooze_hours", 24))
            except (TypeError, ValueError):
                snooze_hours = 24
            ack = state_board.ack_alert(task_id=task_id, snooze_hours=max(1, min(snooze_hours, 168)))
            if ack is None:
                self._send_json(HTTPStatus.BAD_REQUEST, {"status": "failed", "message": "task not found"})
                return
            self._send_json(HTTPStatus.OK, {"status": "ok", "ack": ack})
            diagnostics.write_log("info", "alert_ack", {"task_id": task_id, "snooze_hours": snooze_hours})

        def _handle_health_check(self) -> None:
            report = diagnostics.health_check(
                knowledge_file=orchestrator.capsule_builder.store.knowledge_file,
                state_board_file=state_board.board_file,
                output_dir=orchestrator.action_executor.output_dir,
            )
            self._send_json(HTTPStatus.OK, report)

        def _handle_diagnostics_export(self) -> None:
            ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            target = diagnostics.diagnostics_dir / f"diagnostics_export_{ts}.json"
            written = diagnostics.export_snapshot(target=target, include_tail=300)
            self._send_json(HTTPStatus.OK, {"status": "ok", "path": str(written)})

        def _handle_feedback_add(self) -> None:
            payload = self._read_json()
            text = str(payload.get("text", "")).strip()
            if not text:
                self._send_json(HTTPStatus.BAD_REQUEST, {"status": "failed", "message": "text is required"})
                return
            source = str(payload.get("source", "")).strip() or "desktop"
            saved = diagnostics.append_feedback(source=source, text=text, extra={"tags": payload.get("tags", [])})
            self._send_json(HTTPStatus.OK, {"status": "ok", "feedback": saved})

        def _handle_feedback_list(self) -> None:
            payload = self._read_json()
            try:
                limit = int(payload.get("limit", 100))
            except (TypeError, ValueError):
                limit = 100
            source_text = str(payload.get("source", "")).strip().lower()
            source_set = {source_text} if source_text else None
            rows = diagnostics.tail_feedback(limit=max(1, min(limit, 500)), sources=source_set)
            summary = diagnostics.feedback_summary(limit=1000)
            self._send_json(HTTPStatus.OK, {"status": "ok", "count": len(rows), "rows": rows, "summary": summary})

        def _read_json(self) -> dict:
            raw_len = self.headers.get("Content-Length", "0")
            try:
                content_length = int(raw_len)
            except ValueError:
                content_length = 0
            if content_length <= 0:
                return {}
            raw = self.rfile.read(content_length).decode("utf-8")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                diagnostics.write_log("warn", "json_decode_failed", {"path": self.path})
                return {}

        def _send_json(self, status: HTTPStatus, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            allow_origin = self._cors_allow_origin()
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if allow_origin:
                self.send_header("Access-Control-Allow-Origin", allow_origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, status: HTTPStatus, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802
            allow_origin = self._cors_allow_origin()
            if not allow_origin:
                self.send_response(HTTPStatus.FORBIDDEN)
                self.end_headers()
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", allow_origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()

        def _sync_task_state(self, action_name: str, payload: dict, result: dict, event_id: str) -> None:
            context = result.get("context", {}) if isinstance(result.get("context", {}), dict) else {}
            customer_name = str(
                context.get("customer_name")
                or payload.get("client")
                or payload.get("customer")
                or "Unknown Customer"
            ).strip()
            customer_id = str(context.get("customer_id", "")).strip() or slugify_id(customer_name)
            if action_name == "generate_quote_draft":
                state_board.create_followup_task(
                    customer_id=customer_id,
                    customer_name=customer_name,
                    title=f"Follow up quote response for {customer_name}",
                    due_in_days=2,
                    priority="high",
                    source_event_id=event_id,
                )
                return
            if action_name == "generate_followup_draft":
                state_board.transition_customer_tasks(
                    customer_id=customer_id,
                    to_status="in_progress",
                    note="Auto-progressed by follow-up draft generation.",
                    from_statuses=("waiting_reply", "overdue"),
                    max_items=2,
                )

        def _cors_allow_origin(self) -> str:
            origin = self.headers.get("Origin", "").strip()
            if not origin:
                return "null"
            if self._is_allowed_origin(origin):
                return origin
            return ""

        def _is_allowed_execute_origin(self) -> bool:
            origin = self.headers.get("Origin", "").strip()
            if not origin:
                # Extension background fetch may omit Origin in some environments.
                # Bridge is localhost-only, so allow empty origin for local execution flow.
                return True
            return self._is_allowed_origin(origin)

        def _is_allowed_origin(self, origin: str) -> bool:
            if origin.startswith("chrome-extension://"):
                return True
            parsed = urlparse(origin)
            if parsed.scheme != "http":
                return False
            return parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == 8787

        def _idempotency_key(self, payload: dict, actions: list) -> str:
            raw = str(payload.get("idempotency_key", "")).strip()
            if raw:
                return raw
            if not actions:
                return ""
            sig = []
            for item in actions:
                try:
                    data = json.dumps(item.payload, ensure_ascii=False, sort_keys=True)
                except TypeError:
                    data = str(item.payload)
                sig.append(f"{item.name}|{data}")
            return "auto:" + "|".join(sig)

    return BridgeHandler


def _feedback_inbox_html(rows: list[dict], summary: dict) -> str:
    def esc(value: object) -> str:
        text = str(value or "")
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    lines = []
    for row in reversed(rows):
        extra = row.get("extra", {})
        relay = row.get("relay", "")
        lines.append(
            "<tr>"
            f"<td>{esc(row.get('at_utc', ''))}</td>"
            f"<td>{esc(row.get('source', ''))}</td>"
            f"<td>{esc(row.get('text', ''))}</td>"
            f"<td>{esc(json.dumps(extra, ensure_ascii=False))}</td>"
            f"<td>{esc(relay)}</td>"
            "</tr>"
        )
    table_rows = "".join(lines) or "<tr><td colspan='5'>No feedback yet.</td></tr>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Trade Assistant Feedback Inbox</title>
  <style>
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      background: #f8fafc;
      color: #0f172a;
      padding: 16px;
    }}
    .card {{
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 12px;
    }}
    .meta {{
      color: #475569;
      font-size: 13px;
      margin: 4px 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid #e2e8f0;
      padding: 8px;
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }}
    th {{
      background: #f1f5f9;
      font-weight: 700;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h2 style="margin:0 0 8px;">Feedback Inbox</h2>
    <div class="meta">Instance: {esc(summary.get("instance_id", ""))}</div>
    <div class="meta">Total: {esc(summary.get("total", 0))} | Latest: {esc(summary.get("latest_at_utc", ""))}</div>
    <div class="meta">By source: {esc(json.dumps(summary.get("by_source", {}), ensure_ascii=False))}</div>
    <div class="meta">Relay status: {esc(json.dumps(summary.get("by_relay", {}), ensure_ascii=False))}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Time (UTC)</th>
        <th>Source</th>
        <th>Feedback</th>
        <th>Extra</th>
        <th>Relay</th>
      </tr>
    </thead>
    <tbody>{table_rows}</tbody>
  </table>
</body>
</html>"""
