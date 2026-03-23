from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import ActionCommand, ActionExecutionResult
from .local_store import LocalKnowledgeStore, slugify_id

ACTION_PATTERN = re.compile(r"<action>(?P<body>.*?)</action>", re.DOTALL)


def parse_actions(text: str) -> list[ActionCommand]:
    commands: list[ActionCommand] = []
    for match in ACTION_PATTERN.finditer(text):
        raw = match.group("body").strip()
        name, payload = _parse_action_body(raw)
        commands.append(ActionCommand(name=name, payload=payload, raw=raw))
    return commands


def dedupe_actions(commands: list[ActionCommand]) -> list[ActionCommand]:
    unique: list[ActionCommand] = []
    seen: set[str] = set()
    for command in commands:
        signature = _action_signature(command)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(command)
    return unique


def _parse_action_body(raw: str) -> tuple[str, dict]:
    if ":" not in raw:
        return raw.strip(), {}
    name, payload_text = raw.split(":", 1)
    payload_text = payload_text.strip()
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        payload = _parse_relaxed_payload(payload_text)
        if not payload:
            payload = {"raw_payload": payload_text}
    return name.strip(), payload


def _action_signature(command: ActionCommand) -> str:
    try:
        payload = json.dumps(command.payload, ensure_ascii=False, sort_keys=True)
    except TypeError:
        payload = str(command.payload)
    return f"{command.name}|{payload}"


class ActionExecutor:
    def __init__(self, store: LocalKnowledgeStore, output_dir: Path) -> None:
        self.store = store
        self.output_dir = output_dir

    def run(self, command: ActionCommand) -> ActionExecutionResult:
        try:
            if command.name == "generate_quote_draft":
                return self._generate_quote_draft(command.payload)
            if command.name == "generate_followup_draft":
                return self._generate_followup_draft(command.payload)
            if command.name == "update_customer_note":
                return self._update_customer_note(command.payload)
            return ActionExecutionResult(
                status="ignored",
                message=f"Unsupported action: {command.name}",
                artifacts=[],
                context={"non_retryable": True},
            )
        except OSError as exc:
            return ActionExecutionResult(
                status="failed",
                message=f"File write failed: {exc}",
                artifacts=[],
                context={"retryable": True},
            )
        except Exception as exc:  # pragma: no cover
            return ActionExecutionResult(
                status="failed",
                message=f"Action execution error: {exc}",
                artifacts=[],
                context={"retryable": False},
            )

    def run_with_retry(self, command: ActionCommand, max_attempts: int = 3, backoff_sec: float = 0.15) -> ActionExecutionResult:
        attempts = max(1, max_attempts)
        result = self.run(command)
        for idx in range(1, attempts):
            if result.status != "failed":
                return result
            context = result.context if isinstance(result.context, dict) else {}
            if not bool(context.get("retryable", False)):
                return result
            time.sleep(backoff_sec * idx)
            result = self.run(command)
        return result

    def _generate_quote_draft(self, payload: dict) -> ActionExecutionResult:
        normalized = _normalize_payload(payload)
        client = str(normalized.get("client", "")).strip()
        product = str(normalized.get("product", "")).strip() or "unknown_product"
        if not client:
            client = self._infer_default_client()
        customer_id, customer_name = self._resolve_customer(client)
        if customer_name:
            client = customer_name
        price = normalized.get("price", "N/A")
        currency = str(normalized.get("currency", "USD"))
        quantity = normalized.get("quantity", "N/A")
        total = normalized.get("total", "")
        terms = str(normalized.get("terms", "")).strip()
        notes = str(normalized.get("notes", "")).strip()

        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"quote_{_safe_name(client)}_{ts}.md"
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_content = "\n".join(
            [
                "# Quote Draft",
                "",
                f"- Client: {client}",
                f"- Product: {product}",
                f"- Price: {price} {currency}",
                f"- Quantity: {quantity}",
                f"- Terms: {terms or 'N/A'}",
                f"- Total: {total if total != '' else 'N/A'}",
                f"- Generated At (UTC): {ts}",
                "",
                "## Notes",
                notes or "No additional notes.",
                "",
            ]
        )
        _write_text_retry(output_path, markdown_content)
        txt_path = output_path.with_suffix(".txt")
        _write_text_retry(txt_path, _render_plain_text(markdown_content))
        html_path = output_path.with_suffix(".html")
        _write_text_retry(html_path, _render_simple_html("Quote Draft", markdown_content))
        return ActionExecutionResult(
            status="success",
            message=f"Quote draft generated for {client}.",
            artifacts=[str(output_path), str(txt_path), str(html_path)],
            context={
                "customer_id": customer_id,
                "customer_name": client,
                "product": product,
                "action": "generate_quote_draft",
            },
        )

    def _generate_followup_draft(self, payload: dict) -> ActionExecutionResult:
        normalized = _normalize_payload(payload)
        customer = str(normalized.get("customer", "")).strip() or self._infer_default_client()
        customer_id, customer_name = self._resolve_customer(customer)
        if customer_name:
            customer = customer_name
        reason = str(normalized.get("reason", "pending response")).strip()
        tone = str(normalized.get("tone", "professional")).strip()
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"followup_{_safe_name(customer)}_{ts}.md"
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subject = f"Follow-up on previous quote - {customer}"
        body = (
            f"Dear {customer},\n\n"
            f"I hope you are doing well. I am writing to follow up regarding our previous quotation.\n"
            f"Reason: {reason}.\n\n"
            "Please let me know if you need any revisions on price, quantity, or delivery terms.\n\n"
            "Best regards,\nTrade Assistant\n"
        )
        markdown_content = "\n".join(
            [
                "# Follow-up Draft",
                "",
                f"- Customer: {customer}",
                f"- Tone: {tone}",
                f"- Reason: {reason}",
                f"- Generated At (UTC): {ts}",
                "",
                "## Suggested Subject",
                subject,
                "",
                "## Suggested Body",
                body,
                "",
            ]
        )
        _write_text_retry(output_path, markdown_content)
        txt_path = output_path.with_suffix(".txt")
        _write_text_retry(txt_path, _render_plain_text(markdown_content))
        html_path = output_path.with_suffix(".html")
        _write_text_retry(html_path, _render_simple_html("Follow-up Draft", markdown_content))
        return ActionExecutionResult(
            status="success",
            message=f"Follow-up draft generated for {customer}.",
            artifacts=[str(output_path), str(txt_path), str(html_path)],
            context={
                "customer_id": customer_id,
                "customer_name": customer,
                "product": str(normalized.get("product", "")).strip(),
                "action": "generate_followup_draft",
            },
        )

    def _infer_default_client(self) -> str:
        kb = self.store.load()
        customers = list(kb.customers.values())
        if len(customers) == 1:
            return customers[0].name
        return "unknown_client"

    def _update_customer_note(self, payload: dict) -> ActionExecutionResult:
        customer_hint = str(payload.get("customer", "")).strip()
        note = str(payload.get("note", "")).strip()
        if not customer_hint or not note:
            return ActionExecutionResult(
                status="failed",
                message="update_customer_note requires customer and note.",
                artifacts=[],
                context={"non_retryable": True},
            )
        kb = self.store.load()
        customer = self.store.find_customer(customer_hint, kb=kb)
        if customer is None:
            return ActionExecutionResult(
                status="failed",
                message=f"Customer not found: {customer_hint}",
                artifacts=[],
                context={"non_retryable": True},
            )
        customer.notes.append(note)
        kb.customers[customer.customer_id] = customer
        self.store.save(kb)
        return ActionExecutionResult(
            status="success",
            message=f"Customer note updated: {customer.name}",
            artifacts=[str(self.store.knowledge_file)],
            context={
                "customer_id": customer.customer_id,
                "customer_name": customer.name,
                "action": "update_customer_note",
            },
        )

    def _resolve_customer(self, hint: str) -> tuple[str, str]:
        if not hint.strip():
            return ("unknown_customer", "Unknown Customer")
        customer = self.store.find_customer(hint)
        if customer is not None:
            return (customer.customer_id, customer.name)
        return (slugify_id(hint), hint)


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "unknown"


def _parse_relaxed_payload(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1]
    pattern = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(\"[^\"]*\"|'[^']*'|[^,]+)")
    payload: dict[str, Any] = {}
    for key, value_raw in pattern.findall(text):
        payload[key] = _coerce_value(value_raw.strip())
    return payload


def _coerce_value(value: str) -> Any:
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    low = value.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in {"null", "none"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if not normalized.get("client") and normalized.get("customer"):
        normalized["client"] = normalized.get("customer")
    return normalized


def _write_text_retry(path: Path, content: str, attempts: int = 5) -> None:
    for idx in range(attempts):
        tmp = path.with_suffix(path.suffix + f".tmp{idx}")
        try:
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(path)
            return
        except PermissionError:
            time.sleep(0.08 * (idx + 1))
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
    path.write_text(content, encoding="utf-8")


def _render_plain_text(markdown_like: str) -> str:
    lines = []
    for line in markdown_like.splitlines():
        lines.append(line.replace("#", "").strip())
    return "\n".join(lines).strip() + "\n"


def _render_simple_html(title: str, markdown_like: str) -> str:
    escaped = (
        markdown_like.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>\n")
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>body{font-family:Segoe UI,Arial,sans-serif;padding:18px;line-height:1.6;}</style>"
        "</head><body>"
        f"<h2>{title}</h2><div>{escaped}</div>"
        "</body></html>\n"
    )
