from __future__ import annotations

from app.self_improving_preferences import (
    default_profile,
    learn_from_edit,
    preference_basis_line,
    preference_instruction,
)


def test_learn_from_edit_updates_profile() -> None:
    original = "We can offer a quote soon."
    revised = "请确认数量和交期。下一步：1) 今日确认规格 2) 明日确认付款条款。"
    result = learn_from_edit(original_reply=original, revised_reply=revised, existing_profile=default_profile())
    assert result.updated_profile["structure"] == "bullet"
    assert result.updated_profile["action_style"] == "multi_step"
    assert result.updated_profile["confidence"] > 0.0


def test_preference_instruction_and_basis_are_non_empty() -> None:
    profile = default_profile()
    zh = preference_instruction(profile, lang="zh")
    en = preference_instruction(profile, lang="en")
    basis = preference_basis_line(profile, lang="zh")
    assert zh.strip()
    assert en.strip()
    assert basis.strip()

