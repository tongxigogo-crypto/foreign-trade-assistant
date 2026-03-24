from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from .contracts import KnowledgeBase
from .local_store import LocalKnowledgeStore

ADAPTIVE_PREFIX = "[adaptive]"
ADAPTIVE_RULE_LIMIT = 300
PRICE_RE = re.compile(r"(?<!\d)(?:USD|EUR|GBP|CNY|RMB|\$|¥)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
MARKED_PRICE_RE = re.compile(r"(?:USD|EUR|GBP|CNY|RMB|\$|¥)\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
PRICE_CONTEXT_TERMS = (
    "price",
    "offer",
    "quote",
    "quoted",
    "unit",
    "total",
    "amount",
    "报价",
    "价格",
    "总价",
    "单价",
)
NON_PRICE_CONTEXT_TERMS = (
    "freight",
    "shipping",
    "delivery",
    "lead time",
    "day",
    "days",
    "container",
    "sample",
    "qty",
    "quantity",
    "pcs",
)
LOGISTICS_TONE_TOKENS = (
    "container",
    "lead time",
    "fob",
    "cif",
    "etd",
    "eta",
    "shipping",
    "freight",
)
QUALITY_TONE_TOKENS = (
    "sample",
    "quality certificate",
    "certificate",
    "coa",
    "qc",
    "spec",
    "test report",
)


def learn_from_quote_decision(
    *,
    store: LocalKnowledgeStore,
    customer_id: str,
    customer_name: str,
    product: str,
    price: float,
    currency: str,
) -> dict[str, Any]:
    kb = store.load()
    profile = dict(kb.preference.adaptive_profile or {})
    key = _profile_key(customer_id=customer_id, product=product)
    now = datetime.now(UTC).isoformat()
    prev = profile.get(key, {}) if isinstance(profile.get(key), dict) else {}
    prev_count = int(prev.get("count", 0))
    prev_avg = _to_float(prev.get("avg_price"), 0.0)
    new_avg = ((prev_avg * prev_count) + price) / max(1, prev_count + 1)
    profile[key] = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "product": product,
        "currency": currency,
        "avg_price": round(new_avg, 4),
        "last_price": round(price, 4),
        "count": prev_count + 1,
        "last_updated_at_utc": now,
    }
    kb.preference.adaptive_profile = profile
    _upsert_adaptive_rule(
        kb=kb,
        customer_id=customer_id,
        customer_name=customer_name,
        product=product,
        payload={
            "mode": "quote_observation",
            "currency": currency,
            "avg_price": round(new_avg, 4),
            "last_price": round(price, 4),
            "samples": prev_count + 1,
            "updated_at_utc": now,
        },
    )
    store.save(kb)
    return profile[key]


def learn_from_edit_feedback(
    *,
    store: LocalKnowledgeStore,
    before_text: str,
    after_text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    before_price = _extract_last_price(before_text)
    after_price = _extract_last_price(after_text)
    delta_pct = 0.0
    direction = "stable"
    if before_price > 0 and after_price > 0:
        delta_pct = ((after_price - before_price) / before_price) * 100.0
        if delta_pct > 0.2:
            direction = "increase"
        elif delta_pct < -0.2:
            direction = "decrease"
    tone = _infer_tone(after_text)
    customer_id = str(context.get("customer_id", "")).strip()
    customer_name = str(context.get("customer_name", "")).strip() or customer_id or "unknown_customer"
    product = str(context.get("product", "")).strip() or "unknown_product"
    scenario = str(context.get("scenario", "")).strip() or _infer_scenario(context=context)
    kb = store.load()
    _upsert_adaptive_rule(
        kb=kb,
        customer_id=customer_id or customer_name.lower().replace(" ", "-"),
        customer_name=customer_name,
        product=product,
        payload={
            "mode": "edit_feedback",
            "scenario": scenario,
            "before_price": round(before_price, 4),
            "after_price": round(after_price, 4),
            "delta_pct": round(delta_pct, 4),
            "direction": direction,
            "tone": tone,
            "updated_at_utc": datetime.now(UTC).isoformat(),
        },
    )
    if tone and tone not in kb.preference.must_include:
        kb.preference.must_include = (kb.preference.must_include + [tone])[-8:]
    store.save(kb)
    return {
        "customer_name": customer_name,
        "product": product,
        "scenario": scenario,
        "before_price": round(before_price, 4),
        "after_price": round(after_price, 4),
        "delta_pct": round(delta_pct, 4),
        "direction": direction,
        "tone": tone,
    }


def adaptive_hints_for_request(
    *,
    kb: KnowledgeBase,
    user_input: str,
    customer_hint: str,
    product_hint: str,
    limit: int = 2,
) -> list[str]:
    query = " ".join([user_input, customer_hint, product_hint]).lower()
    hints: list[str] = []
    for rule in kb.preference.pricing_rules:
        parsed = parse_adaptive_rule(rule)
        if not parsed:
            continue
        customer = str(parsed.get("customer_name", "")).lower()
        product = str(parsed.get("product", "")).lower()
        cid = str(parsed.get("customer_id", "")).lower()
        if query and not any(token and token in query for token in (customer, product, cid)):
            continue
        payload = parsed.get("payload", {})
        if isinstance(payload, dict) and payload.get("mode") == "quote_observation":
            hints.append(
                f"Adaptive pricing memory: {parsed.get('customer_name')} / {parsed.get('product')} "
                f"recent avg {payload.get('avg_price')} {payload.get('currency')}."
            )
        elif isinstance(payload, dict):
            hints.append(
                f"Adaptive edit memory: {parsed.get('customer_name')} / {parsed.get('product')} "
                f"{payload.get('direction')} {payload.get('delta_pct')}% in scenario {payload.get('scenario')}."
            )
        if len(hints) >= max(1, limit):
            break
    return hints


def parse_adaptive_rule(rule: str) -> dict[str, Any] | None:
    text = str(rule or "").strip()
    if not text.startswith(ADAPTIVE_PREFIX):
        return None
    body = text[len(ADAPTIVE_PREFIX) :].strip()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _upsert_adaptive_rule(
    *,
    kb: KnowledgeBase,
    customer_id: str,
    customer_name: str,
    product: str,
    payload: dict[str, Any],
) -> None:
    rules = list(kb.preference.pricing_rules or [])
    key = f"{customer_id}|{product}"
    target = {
        "key": key,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "product": product,
        "payload": payload,
    }
    encoded = ADAPTIVE_PREFIX + " " + json.dumps(target, ensure_ascii=False, sort_keys=True)
    replaced = False
    for idx, rule in enumerate(rules):
        parsed = parse_adaptive_rule(rule)
        if not parsed:
            continue
        if str(parsed.get("key", "")).strip() != key:
            continue
        rules[idx] = encoded
        replaced = True
        break
    if not replaced:
        rules.append(encoded)
    kb.preference.pricing_rules = _trim_adaptive_rules_lru(rules, limit=ADAPTIVE_RULE_LIMIT)


def _extract_last_price(text: str) -> float:
    source = str(text or "")
    if not source.strip():
        return 0.0
    candidates = _collect_price_candidates(source)
    if not candidates:
        return 0.0
    best = max(candidates, key=lambda item: (item["score"], item["start"]))
    return float(best["value"])


def _infer_tone(text: str) -> str:
    low = str(text or "").lower()
    if any(token in low for token in LOGISTICS_TONE_TOKENS):
        return "logistics_focused"
    if any(token in low for token in QUALITY_TONE_TOKENS):
        return "quality_driven"
    if any(token in low for token in ("final offer", "non-negotiable", "strict")):
        return "firm_pricing"
    if any(token in low for token in ("best regards", "kindly", "thank you")):
        return "polite_close"
    return "professional"


def _infer_scenario(*, context: dict[str, Any]) -> str:
    weekday = _context_int(context, "weekday", "local_weekday", "reply_weekday")
    if weekday is not None and weekday >= 5:
        return "weekend_urgent"
    hour = _context_int(context, "hour", "local_hour", "reply_hour")
    if hour is not None and (hour >= 22 or hour < 7):
        return "night_urgent"
    dt = _context_datetime(context, "reply_at", "sent_at", "timestamp", "event_at", "datetime")
    if dt is not None:
        offset = _context_int(context, "timezone_offset", "timezone_offset_min")
        if offset is not None:
            dt = _apply_timezone_offset(dt, offset)
        if dt.weekday() >= 5:
            return "weekend_urgent"
        if dt.hour >= 22 or dt.hour < 7:
            return "night_urgent"
        month = dt.month
    else:
        month = _context_int(context, "month")
        if month is None:
            month = datetime.now(UTC).month
    if month in {3, 6, 9, 12}:
        return "quarter_end"
    return "normal"


def _profile_key(*, customer_id: str, product: str) -> str:
    return f"{customer_id or 'unknown_customer'}|{product or 'unknown_product'}"


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _collect_price_candidates(text: str) -> list[dict[str, float]]:
    scored: list[dict[str, float]] = []
    seen_spans: set[tuple[int, int]] = set()
    for match in MARKED_PRICE_RE.finditer(text):
        value = _to_float(match.group(1), 0.0)
        if value <= 0:
            continue
        span = (match.start(1), match.end(1))
        seen_spans.add(span)
        scored.append(
            {
                "value": value,
                "start": float(span[0]),
                "score": _score_price_candidate(text=text, start=span[0], end=span[1], value=value, marked=True),
            }
        )
    for match in PRICE_RE.finditer(text):
        value = _to_float(match.group(1), 0.0)
        if value <= 0:
            continue
        span = (match.start(1), match.end(1))
        if span in seen_spans:
            continue
        scored.append(
            {
                "value": value,
                "start": float(span[0]),
                "score": _score_price_candidate(text=text, start=span[0], end=span[1], value=value, marked=False),
            }
        )
    return scored


def _score_price_candidate(*, text: str, start: int, end: int, value: float, marked: bool) -> float:
    if value <= 0:
        return float("-inf")
    low = text.lower()
    radius = 36
    left = max(0, start - radius)
    right = min(len(low), end + radius)
    window = low[left:right]
    positive_hits = sum(1 for token in PRICE_CONTEXT_TERMS if token in window)
    negative_hits = sum(1 for token in NON_PRICE_CONTEXT_TERMS if token in window)
    sentence = _sentence_window(text=low, start=start, end=end)
    sentence_positive = sum(1 for token in PRICE_CONTEXT_TERMS if token in sentence)
    sentence_negative = sum(1 for token in NON_PRICE_CONTEXT_TERMS if token in sentence)
    score = float(start) / max(1, len(text))
    if marked:
        score += 25.0
    score += 40.0 * positive_hits
    score += 65.0 * sentence_positive
    if negative_hits:
        score -= (10.0 if positive_hits else 35.0) * negative_hits
    if sentence_negative:
        score -= (30.0 if sentence_positive else 80.0) * sentence_negative
    if "%" in window:
        score -= 20.0
    if value < 1:
        score -= 10.0
    return score


def _trim_adaptive_rules_lru(rules: list[str], *, limit: int) -> list[str]:
    if limit <= 0:
        return [rule for rule in rules if not parse_adaptive_rule(rule)]
    adaptive_rows: list[tuple[int, str, datetime]] = []
    for idx, rule in enumerate(rules):
        parsed = parse_adaptive_rule(rule)
        if not parsed:
            continue
        adaptive_rows.append((idx, rule, _adaptive_rule_timestamp(parsed)))
    if len(adaptive_rows) <= limit:
        return rules
    adaptive_rows.sort(key=lambda item: (item[2], item[0]))
    remove_n = len(adaptive_rows) - limit
    remove_idx = {row[0] for row in adaptive_rows[:remove_n]}
    return [rule for idx, rule in enumerate(rules) if idx not in remove_idx]


def _adaptive_rule_timestamp(parsed: dict[str, Any]) -> datetime:
    payload = parsed.get("payload", {})
    if isinstance(payload, dict):
        raw = str(payload.get("updated_at_utc", "") or payload.get("created_at_utc", "")).strip()
        if raw:
            parsed_dt = _parse_datetime(raw)
            if parsed_dt is not None:
                return parsed_dt
    return datetime.fromtimestamp(0, tz=UTC)


def _context_int(context: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        if key not in context:
            continue
        raw = context.get(key)
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return None


def _context_datetime(context: dict[str, Any], *keys: str) -> datetime | None:
    for key in keys:
        if key not in context:
            continue
        raw = context.get(key)
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(float(raw), tz=UTC)
        if isinstance(raw, str):
            parsed = _parse_datetime(raw)
            if parsed is not None:
                return parsed
    return None


def _parse_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _apply_timezone_offset(value: datetime, offset_minutes: int) -> datetime:
    # JS Date.getTimezoneOffset semantics: local_time = utc_time - offset.
    return value.astimezone(UTC) - timedelta(minutes=offset_minutes)


def _sentence_window(*, text: str, start: int, end: int) -> str:
    separators = ".!?;\n"
    left = start
    while left > 0 and text[left - 1] not in separators:
        left -= 1
    right = end
    while right < len(text) and text[right] not in separators:
        right += 1
    return text[left:right]
