from __future__ import annotations

from app.api_chat import default_api_url, default_model
from app.desktop_app import DesktopWindow


class _Var:
    def __init__(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value


def test_provider_change_updates_model_and_url() -> None:
    window = DesktopWindow.__new__(DesktopWindow)
    window.api_provider_var = _Var("openai")
    window.api_url_var = _Var("")
    window.api_model_var = _Var("custom-before")

    window._on_api_provider_changed()

    assert window.api_url_var.get() == default_api_url("openai")
    assert window.api_model_var.get() == default_model("openai")
