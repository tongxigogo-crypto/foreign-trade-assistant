from __future__ import annotations

from pathlib import Path
import sys

from app.config import AppConfig
from app.desktop_app import DesktopWindow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_APP_FILE = PROJECT_ROOT / "app" / "desktop_app.py"


def test_desktop_has_three_pane_layout_and_global_scroll() -> None:
    src = DESKTOP_APP_FILE.read_text(encoding="utf-8", errors="ignore")
    assert "ttk.Panedwindow(" in src
    assert "_configure_canvas_scrollregion" in src
    assert "self.api_input_text.bind(\"<Return>\"" in src
    assert "self.api_result_pane = ttk.Panedwindow" in src
    assert "self.root.after_idle(lambda: self._set_api_result_split(0.72))" in src
    assert "self._build_radar_section(self.left_panel)" in src
    assert "self._build_guide_section(self.left_panel)" in src


def test_desktop_keeps_mail_import_and_pull_controls() -> None:
    src = DESKTOP_APP_FILE.read_text(encoding="utf-8", errors="ignore")
    assert "批量导入邮件线程" in src
    assert "邮箱一键拉取" in src


def test_desktop_has_language_toggle_controls() -> None:
    src = DESKTOP_APP_FILE.read_text(encoding="utf-8", errors="ignore")
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
        assert window.import_section_box.cget("text") == "History Import"
        assert window.guide_section_box.cget("text") == "Extension Setup Guide"
        assert window.email_import_button.cget("text") == "Batch Import Mail Threads"
        assert window.pull_mail_button.cget("text") == "Mail Pull and Import"
        assert window.feedback_section_box.cget("text") == "7) Feedback"
        assert window.runtime_refresh_button.cget("text") == "Refresh"
        assert not hasattr(window, "runtime_open_workbench_button")
        assert window.action_execute_button.cget("text") == "Execute Action Tag"
        assert window.radar_search_button.cget("text") == "Search"
        assert window.radar_capsule_button.cget("text") == "Build Capsule"
        assert window.beginner_mode_check.cget("text") == "Beginner Mode"
        assert window.show_advanced_check.cget("text") == "Show Advanced"
        assert window.radar_section_box.cget("text") == "Radar Search"
        assert window.radar_hint_label.cget("text").startswith("Supports fuzzy and exact terms")
        assert window.import_hint_label.cget("text").startswith("Repeatable import + auto-dedup")
        assert window.email_thread_label.cget("text") == "Mail Threads:"
        assert window.choose_import_source_button.cget("text") == "Choose History Files/Folder"
        assert window.api_status_var.get() == "Waiting for connection"
        assert window.import_status.get() == "Waiting for import"
        assert window.api_basis_text.get("1.0", "end").strip() == "No local context used yet."
        assert window.result_text.get("1.0", "end").strip() == "Import results will appear here."
        assert window.radar_result.get("1.0", "end").strip() == "Enter keywords then click Search."
    finally:
        window.root.destroy()
