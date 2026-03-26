from __future__ import annotations

from pathlib import Path

from app.config import AppConfig
from app.desktop_app import DesktopWindow


def test_desktop_switching_language_updates_extended_labels(tmp_path: Path) -> None:
    root_dir = tmp_path / "trade-assistant-mac"
    (root_dir / "app").mkdir(parents=True)
    config = AppConfig.load(root_dir)
    window = DesktopWindow(config)
    try:
        window._switch_language("en")
        assert window.root.title() == "Trade Assistant Desktop"
        assert window.import_section_box.cget("text") == "History Import"
        assert window.guide_section_box.cget("text") == "Extension Setup Guide"
        assert window.email_import_button.cget("text") == "Batch Import Mail Threads"
        assert window.pull_mail_button.cget("text") == "Mail Pull and Import"
        assert window.feedback_section_box.cget("text") == "7) Feedback"
        assert window.runtime_refresh_button.cget("text") == "Refresh"
        assert window.runtime_open_workbench_button.cget("text") == "Open Web Workbench"
        assert window.action_execute_button.cget("text") == "Execute Action Tag"
        assert window.radar_search_button.cget("text") == "Search"
        assert window.radar_capsule_button.cget("text") == "Build Capsule"
    finally:
        window.root.destroy()
