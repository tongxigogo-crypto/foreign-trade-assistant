from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class PreferenceLearningResult:
    updated_profile: dict[str, Any]
    deltas: dict[str, Any]
    summary: str


def default_profile() -> dict[str, Any]:
    return {
        "tone": "neutral",
        "length": "balanced",
        "structure": "paragraph",
        "price_style": "balanced",
        "action_style": "single_next_step",
        "confidence": 0.0,
    }


def _normalize_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    base = default_profile()
    if not isinstance(profile, dict):
        return base
    for key in base:
        if key in profile and profile[key] not in (None, ""):
            base[key] = profile[key]
    try:
        base["confidence"] = max(0.0, min(float(base.get("confidence", 0.0)), 1.0))
    except (TypeError, ValueError):
        base["confidence"] = 0.0
    return base


def _contains_any(text: str, patterns: list[str]) -> bool:
    low = text.lower()
    return any(p in low for p in patterns)


def _infer_deltas(draft: str, revised: str) -> dict[str, str]:
    draft_s = draft.strip()
    revised_s = revised.strip()
    revised_low = revised_s.lower()
    deltas: dict[str, str] = {}

    # tone
    if _contains_any(revised_low, ["please", "kindly", "thanks", "thank you", "您好", "感谢", "请"]):
        deltas["tone"] = "polite"
    elif _contains_any(revised_low, ["must", "strictly", "必须", "立刻", "立即"]):
        deltas["tone"] = "firm"
    else:
        deltas["tone"] = "neutral"

    # length
    draft_len = max(1, len(draft_s))
    ratio = len(revised_s) / draft_len
    if ratio <= 0.75:
        deltas["length"] = "concise"
    elif ratio >= 1.35:
        deltas["length"] = "detailed"
    else:
        deltas["length"] = "balanced"

    # structure
    # Accept both line-based bullets and inline numbered steps like "1) ... 2) ..."
    line_bullets = len(re.findall(r"(^|\n)\s*[-*]\s+", revised_s))
    numbered_steps = len(re.findall(r"(?<!\d)\d+\s*[.)]\s*", revised_s))
    bullet_count = line_bullets + numbered_steps
    if bullet_count >= 2:
        deltas["structure"] = "bullet"
    else:
        deltas["structure"] = "paragraph"

    # price style
    if re.search(r"(usd|rmb|\$|￥|%|折扣|discount|unit price|单价)", revised_low):
        if _contains_any(revised_low, ["底价", "bottom price", "最低", "floor"]):
            deltas["price_style"] = "strict_floor"
        else:
            deltas["price_style"] = "explicit_numbers"
    else:
        deltas["price_style"] = "balanced"

    # action style
    if _contains_any(revised_low, ["next step", "下一步", "请确认", "confirm", "action"]):
        if bullet_count >= 2:
            deltas["action_style"] = "multi_step"
        else:
            deltas["action_style"] = "single_next_step"
    else:
        deltas["action_style"] = "single_next_step"

    return deltas


def learn_from_edit(
    *,
    original_reply: str,
    revised_reply: str,
    existing_profile: dict[str, Any] | None = None,
) -> PreferenceLearningResult:
    profile = _normalize_profile(existing_profile)
    if not revised_reply.strip():
        return PreferenceLearningResult(profile, {}, "No revision content.")
    deltas = _infer_deltas(original_reply, revised_reply)
    for key, value in deltas.items():
        profile[key] = value
    conf = float(profile.get("confidence", 0.0))
    profile["confidence"] = round(min(1.0, conf + 0.1), 2)
    summary = (
        f"tone={profile['tone']}, length={profile['length']}, structure={profile['structure']}, "
        f"price={profile['price_style']}, action={profile['action_style']}, confidence={profile['confidence']}"
    )
    return PreferenceLearningResult(profile, deltas, summary)


def preference_instruction(profile: dict[str, Any] | None, *, lang: str = "zh") -> str:
    p = _normalize_profile(profile)
    if lang == "en":
        return (
            "Preference profile: "
            f"tone={p['tone']}, length={p['length']}, structure={p['structure']}, "
            f"price_style={p['price_style']}, action_style={p['action_style']}. "
            "Apply these preferences when composing the answer."
        )
    return (
        "偏好配置："
        f"语气={p['tone']}，长度={p['length']}，结构={p['structure']}，"
        f"价格表达={p['price_style']}，行动建议={p['action_style']}。"
        "请在回复中遵循这些偏好。"
    )


def preference_basis_line(profile: dict[str, Any] | None, *, lang: str = "zh") -> str:
    p = _normalize_profile(profile)
    if lang == "en":
        return (
            "Applied preferences: "
            f"tone={p['tone']}; length={p['length']}; structure={p['structure']}; "
            f"price={p['price_style']}; action={p['action_style']}."
        )
    return (
        "已应用偏好："
        f"语气={p['tone']}；长度={p['length']}；结构={p['structure']}；"
        f"价格={p['price_style']}；行动={p['action_style']}。"
    )
