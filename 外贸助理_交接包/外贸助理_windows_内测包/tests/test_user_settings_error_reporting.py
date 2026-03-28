from __future__ import annotations

from app.user_settings import UserSettings


def test_error_reporting_enabled_default_true() -> None:
    settings = UserSettings.from_dict({})
    assert settings.error_reporting_enabled is True


def test_error_reporting_enabled_roundtrip() -> None:
    settings = UserSettings.from_dict({"error_reporting_enabled": False})
    assert settings.error_reporting_enabled is False
    payload = settings.to_dict()
    assert payload["error_reporting_enabled"] is False

