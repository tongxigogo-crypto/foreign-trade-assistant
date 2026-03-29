# Mac History Importers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the mac desktop package actually import PDF, Word, and Excel files that the UI already advertises to users.

**Architecture:** Extend the mac-only history importer with format-specific text extractors, using packaged Python libraries for PDF/Excel/new Word and a macOS-native `textutil` fallback for old `.doc`. Keep the importer API stable so the desktop UI does not need structural changes, then align the UI strings and build dependencies with the real supported formats.

**Tech Stack:** Python, pytest, PyInstaller, pypdf, python-docx, openpyxl, xlrd, macOS `textutil`

---

### Task 1: Add failing importer tests

**Files:**
- Create: `docs/superpowers/plans/2026-03-30-mac-history-importers.md`
- Create: `外贸助理_交接包/外贸助理_mac_内测包/tests/test_history_importer.py`
- Modify: `外贸助理_交接包/外贸助理_mac_内测包/app/history_importer.py`

- [ ] **Step 1: Write the failing tests**

Cover:
- `.pdf` extraction via `PdfReader`
- `.docx` extraction via `Document`
- `.xlsx` extraction via `load_workbook`
- `.xls` extraction via `xlrd.open_workbook`
- `.doc` extraction via `textutil`
- scan list includes these suffixes

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest 外贸助理_交接包/外贸助理_mac_内测包/tests/test_history_importer.py -q`

- [ ] **Step 3: Implement minimal extractor support**

Add suffix routing and per-format extraction helpers in `app/history_importer.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest 外贸助理_交接包/外贸助理_mac_内测包/tests/test_history_importer.py -q`

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-03-30-mac-history-importers.md 外贸助理_交接包/外贸助理_mac_内测包/tests/test_history_importer.py 外贸助理_交接包/外贸助理_mac_内测包/app/history_importer.py
git commit -m "feat: add mac office history import support"
```

### Task 2: Align build/runtime packaging

**Files:**
- Modify: `外贸助理_交接包/外贸助理_mac_内测包/requirements.txt`
- Modify: `外贸助理_交接包/外贸助理_mac_内测包/scripts/build_mac_release.sh`

- [ ] **Step 1: Write the failing packaging expectation**

Document required runtime deps: `pypdf`, `python-docx`, `openpyxl`, `xlrd`.

- [ ] **Step 2: Implement minimal dependency changes**

Add only the needed dependencies to `requirements.txt`. Keep build script using that file.

- [ ] **Step 3: Verify environment install path**

Run: `python -m pip install -r 外贸助理_交接包/外贸助理_mac_内测包/requirements.txt`

- [ ] **Step 4: Commit**

```bash
git add 外贸助理_交接包/外贸助理_mac_内测包/requirements.txt 外贸助理_交接包/外贸助理_mac_内测包/scripts/build_mac_release.sh
git commit -m "build: package mac history import dependencies"
```

### Task 3: Fix mac UI claims

**Files:**
- Modify: `外贸助理_交接包/外贸助理_mac_内测包/app/desktop_app.py`

- [ ] **Step 1: Write the failing expectation**

UI file picker and import-complete text must match actual supported formats.

- [ ] **Step 2: Implement minimal text/filter changes**

Remove unsupported `pptx/ppt` claims from mac-only UI strings and file dialog filters.

- [ ] **Step 3: Verify strings**

Run: `rg -n "pptx|ppt|xlsx|xls|docx|doc|pdf" 外贸助理_交接包/外贸助理_mac_内测包/app/desktop_app.py`

- [ ] **Step 4: Commit**

```bash
git add 外贸助理_交接包/外贸助理_mac_内测包/app/desktop_app.py
git commit -m "fix: align mac import UI with supported formats"
```
