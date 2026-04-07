# Windows Local Model Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Windows 对话中枢中增加本地模型 provider，支持 Ollama 与 OpenAI-compatible 本地服务。

**Architecture:** 复用现有 API 面板和聊天主链，把本地模型能力集中收敛到 `api_chat.py`，UI 只做 provider/model 切换、模型列表刷新和本地 provider 的输入限制。远程 provider 保持原逻辑。

**Tech Stack:** Python, tkinter/ttk, urllib, pytest

---

### Task 1: Define Provider Metadata And Discovery

**Files:**
- Modify: `外贸助理_交接包/外贸助理_windows_内测包/app/api_chat.py`
- Test: `外贸助理_交接包/外贸助理_windows_内测包/tests/test_api_chat.py`

- [ ] Add local provider defaults and metadata helpers.
- [ ] Add failing tests for local provider defaults and key requirement behavior.
- [ ] Add local model discovery functions for Ollama and local OpenAI-compatible services.
- [ ] Run targeted tests.

### Task 2: Wire Local Model Requests Into Chat Runtime

**Files:**
- Modify: `外贸助理_交接包/外贸助理_windows_内测包/app/api_chat.py`
- Test: `外贸助理_交接包/外贸助理_windows_内测包/tests/test_api_chat.py`

- [ ] Add failing tests for local requests without authorization header.
- [ ] Keep remote request behavior unchanged.
- [ ] Ensure `send_chat_request` works for local providers with empty API key.
- [ ] Run targeted tests.

### Task 3: Connect Windows UI

**Files:**
- Modify: `外贸助理_交接包/外贸助理_windows_内测包/app/desktop_app.py`
- Modify: `外贸助理_交接包/外贸助理_windows_内测包/app/user_settings.py`

- [ ] Expand provider choices in the API settings panel.
- [ ] Replace model entry with editable combobox and add refresh button.
- [ ] Disable API key input for local providers and allow local connection test without key.
- [ ] Auto-refresh model list when switching to local providers.

### Task 4: Verify And Close

**Files:**
- Modify: `status.md`
- Modify: `docs/harness/current_session.md`
- Modify: `docs/harness/session_state.json`
- Modify: `docs/memory/self_improving_agent.md`

- [ ] Run targeted Windows tests.
- [ ] Run local runtime gate if impacted.
- [ ] Run `scripts/harness-finish.ps1`.
- [ ] Summarize artifact and repo status.
