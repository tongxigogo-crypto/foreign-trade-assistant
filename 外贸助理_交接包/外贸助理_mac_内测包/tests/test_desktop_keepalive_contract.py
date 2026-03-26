from __future__ import annotations

from pathlib import Path


def test_desktop_has_keepalive_watchdog() -> None:
    src = Path("app/desktop_app.py").read_text(encoding="utf-8", errors="ignore")
    assert "def _service_watchdog_tick(self)" in src
    assert "self.root.after(2500, self._service_watchdog_tick)" in src


def test_desktop_has_close_confirmation() -> None:
    src = Path("app/desktop_app.py").read_text(encoding="utf-8", errors="ignore")
    assert 'self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)' in src
    assert "def _on_close_request(self)" in src
