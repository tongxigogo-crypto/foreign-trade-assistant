from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.desktop_app import DesktopWindow


def test_build_customer_source_map_infers_customer_when_kb_has_no_customers(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "history.txt"
    source.write_text("placeholder", encoding="utf-8")

    window = DesktopWindow.__new__(DesktopWindow)
    window.store = SimpleNamespace(load=lambda: SimpleNamespace(customers={}, doc_facts=[]))

    monkeypatch.setattr(
        "app.desktop_app.extract_facts_from_history_file",
        lambda *_args, **_kwargs: [
            "Customer: ACME Trading",
            "Contact: sales@acme.com",
            "Need quote for SKU A100",
        ],
    )

    mapping = window._build_customer_source_map([source])

    assert "ACME Trading" in mapping
    assert mapping["ACME Trading"] == [str(source)]


def test_merge_customer_names_for_picker_includes_import_linked_names() -> None:
    window = DesktopWindow.__new__(DesktopWindow)
    window._filtered_customer_rows = [{"customer_name": "Vitor Maia"}]
    window._last_import_customer_sources = {
        "ACME Trading": ["a.txt"],
        "Vitor Maia": ["b.txt"],
    }

    names = window._merge_customer_names_for_picker()

    assert names == ["Vitor Maia", "ACME Trading"]
