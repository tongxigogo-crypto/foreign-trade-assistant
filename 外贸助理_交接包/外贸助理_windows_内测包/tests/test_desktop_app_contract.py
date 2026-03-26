from __future__ import annotations

from pathlib import Path
import sys

from app.config import AppConfig
from app.desktop_app import DesktopWindow

def test_desktop_has_three_pane_layout_and_global_scroll() -> None:
    src = Path("app/desktop_app.py").read_text(encoding="utf-8", errors="ignore")
    assert "ttk.Panedwindow(" in src
    assert "_configure_canvas_scrollregion" in src
    assert "self.api_input_text.bind(\"<Return>\"" in src
    assert "self.api_result_pane = ttk.Panedwindow" in src
    assert "self.root.after_idle(lambda: self._set_api_result_split(0.72))" in src
    assert "self._build_radar_section(self.left_panel)" in src
    assert "self._build_guide_section(self.left_panel)" in src


def test_desktop_keeps_mail_import_and_pull_controls() -> None:
    src = Path("app/desktop_app.py").read_text(encoding="utf-8", errors="ignore")
    assert "批量导入邮件线程" in src
    assert "邮箱一键拉取" in src


def test_desktop_has_language_toggle_controls() -> None:
    src = Path("app/desktop_app.py").read_text(encoding="utf-8", errors="ignore")
    assert "self.ui_lang" in src
    assert "中文" in src
    assert "EN" in src


def test_desktop_switching_language_updates_core_labels(tmp_path: Path) -> None:
    root_dir = tmp_path / "trade-assistant"
    app_dir = root_dir / "app"
    app_dir.mkdir(parents=True)
    config = AppConfig.load(root_dir)
    window = DesktopWindow(config)
    try:
        window._switch_language("en")
        assert window.root.title() == "Trade Assistant Desktop"
        assert window.service_section_box.cget("text") == "1) Work Entry (Recommended)"
        assert window.api_box.cget("text") == "Conversation Core (API)"
        assert window.open_workbench_button.cget("text") == "Open Web Workbench"
    finally:
        window.root.destroy()
