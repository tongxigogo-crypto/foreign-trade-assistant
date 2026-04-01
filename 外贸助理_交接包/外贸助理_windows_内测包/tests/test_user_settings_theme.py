from __future__ import annotations

from app.user_settings import UserSettings


def test_theme_mode_roundtrip_in_to_dict() -> None:
    settings = UserSettings(theme_mode="dark")
    payload = settings.to_dict()
    assert payload["theme_mode"] == "dark"


def test_theme_mode_defaults_to_system_when_invalid() -> None:
    settings = UserSettings.from_dict({"theme_mode": "unknown-mode"})
    assert settings.theme_mode == "system"
