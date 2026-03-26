from __future__ import annotations

from pathlib import Path


def test_windows_start_script_is_headless() -> None:
    script = Path("启动外贸助理桌面版_windows.bat").read_text(encoding="utf-8", errors="ignore").lower()
    assert "pythonw.exe" in script or "windowstyle hidden" in script
    assert "python -m app.main desktop" not in script
    assert "pause" not in script


def test_windows_start_script_is_ascii_safe() -> None:
    # cmd.exe is sensitive to batch encoding and quoting; keep launcher ASCII-only.
    raw = Path("启动外贸助理桌面版_windows.bat").read_bytes()
    raw.decode("ascii")
