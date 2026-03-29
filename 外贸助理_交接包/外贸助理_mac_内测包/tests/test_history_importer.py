from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from app import history_importer


def test_supported_suffixes_include_pdf_word_excel() -> None:
    assert {".pdf", ".docx", ".doc", ".xlsx", ".xls"}.issubset(history_importer.SUPPORTED_SUFFIXES)


def test_extract_pdf_uses_pdf_reader(monkeypatch, tmp_path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"%PDF-1.4")

    class _FakePdfPage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class _FakePdfReader:
        def __init__(self, path) -> None:
            assert str(path).endswith(".pdf")
            self.pages = [_FakePdfPage("报价单 第一页"), _FakePdfPage("客户要求 第二页")]

    monkeypatch.setattr(history_importer, "PdfReader", _FakePdfReader, raising=False)

    facts = history_importer.extract_facts_from_history_file(source, max_lines=10, max_chars_per_fact=100)
    assert "报价单 第一页" in facts
    assert "客户要求 第二页" in facts


def test_extract_docx_uses_python_docx(monkeypatch, tmp_path) -> None:
    source = tmp_path / "sample.docx"
    source.write_bytes(b"docx")

    class _FakeParagraph:
        def __init__(self, text: str) -> None:
            self.text = text

    class _FakeDocument:
        def __init__(self, path) -> None:
            assert str(path).endswith(".docx")
            self.paragraphs = [_FakeParagraph("产品规格"), _FakeParagraph("交期 15 天")]

    monkeypatch.setattr(history_importer, "Document", _FakeDocument, raising=False)

    facts = history_importer.extract_facts_from_history_file(source, max_lines=10, max_chars_per_fact=100)
    assert facts[:2] == ["产品规格", "交期 15 天"]


def test_extract_xlsx_uses_openpyxl(monkeypatch, tmp_path) -> None:
    source = tmp_path / "sample.xlsx"
    source.write_bytes(b"xlsx")

    class _FakeSheet:
        def iter_rows(self, values_only: bool = False):
            assert values_only is True
            return iter([("客户", "美国"), ("金额", 1200)])

    class _FakeWorkbook:
        worksheets = [_FakeSheet()]

    def fake_load_workbook(path, read_only: bool = False, data_only: bool = False):
        assert str(path).endswith(".xlsx")
        assert read_only is True
        assert data_only is True
        return _FakeWorkbook()

    monkeypatch.setattr(history_importer, "load_workbook", fake_load_workbook, raising=False)

    facts = history_importer.extract_facts_from_history_file(source, max_lines=10, max_chars_per_fact=100)
    assert "客户 美国" in facts
    assert "金额 1200" in facts


def test_extract_xls_uses_xlrd(monkeypatch, tmp_path) -> None:
    source = tmp_path / "sample.xls"
    source.write_bytes(b"xls")

    class _FakeSheet:
        nrows = 2

        def row_values(self, index: int):
            rows = [["SKU", "A-001"], ["数量", 50]]
            return rows[index]

    class _FakeBook:
        nsheets = 1

        def sheet_by_index(self, index: int):
            assert index == 0
            return _FakeSheet()

    def fake_open_workbook(path):
        assert str(path).endswith(".xls")
        return _FakeBook()

    monkeypatch.setattr(history_importer, "xlrd", SimpleNamespace(open_workbook=fake_open_workbook), raising=False)

    facts = history_importer.extract_facts_from_history_file(source, max_lines=10, max_chars_per_fact=100)
    assert "SKU A-001" in facts
    assert "数量 50" in facts


def test_extract_doc_uses_textutil(monkeypatch, tmp_path) -> None:
    source = tmp_path / "legacy.doc"
    source.write_bytes(b"doc")

    def fake_run(args, capture_output: bool = False, text: bool = False, check: bool = False):
        assert args[:3] == ["textutil", "-convert", "txt"]
        assert str(source) in args
        assert capture_output is True
        assert text is True
        assert check is True
        return SimpleNamespace(stdout="旧版 Word 内容\n第二行")

    monkeypatch.setattr(history_importer.sys, "platform", "darwin")
    monkeypatch.setattr(history_importer.subprocess, "run", fake_run)

    facts = history_importer.extract_facts_from_history_file(source, max_lines=10, max_chars_per_fact=100)
    assert facts[:2] == ["旧版 Word 内容", "第二行"]


def test_ingest_history_directory_marks_parser_exception_as_failed(monkeypatch, tmp_path) -> None:
    source = tmp_path / "broken.xlsx"
    source.write_bytes(b"broken")
    knowledge_file = tmp_path / "knowledge_base.json"
    store = history_importer.LocalKnowledgeStore(knowledge_file)
    store.ensure_initialized()

    monkeypatch.setattr(history_importer, "_scan_files", lambda *_args, **_kwargs: [source])

    def fake_extract(path: Path, *, max_lines: int, max_chars_per_fact: int) -> list[str]:  # noqa: ARG001
        raise ValueError("File is not a zip file")

    monkeypatch.setattr(history_importer, "extract_facts_from_history_file", fake_extract)

    stats = history_importer.ingest_history_directory(store, tmp_path, recursive=True, max_files=10)
    assert stats.scanned_files == 1
    assert stats.imported_files == 0
    assert stats.skipped_files == 1
    assert stats.failed_files == [str(source)]


def test_extract_xlsx_returns_empty_on_parser_error(monkeypatch, tmp_path) -> None:
    source = tmp_path / "broken.xlsx"
    source.write_bytes(b"broken")

    def fake_load_workbook(path, read_only: bool = False, data_only: bool = False):  # noqa: ARG001
        raise IndexError("list index out of range")

    monkeypatch.setattr(history_importer, "load_workbook", fake_load_workbook, raising=False)

    facts = history_importer.extract_facts_from_history_file(source, max_lines=10, max_chars_per_fact=100)
    assert facts == []
