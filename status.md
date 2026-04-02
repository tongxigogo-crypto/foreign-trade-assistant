# Status Snapshot
Updated: 2026-04-02  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active delivery target: `v0.1.1-beta2-build37` (Windows)
- Generated package: `TA_Beta_v0.1.1-beta2-build37_windows.zip`
- Package path: `外贸助理_交接包/外贸助理_windows_内测包/release/`
- mac sync remains pending explicit user start command

## Scope Closed In This Round
- Fixed runtime dual-index evidence field bug (`rag_db` -> `rag_db_facts` + `rag_db_memory`) so build gate no longer blocks.
- Added API conversation memory controls in Windows desktop:
  1. `Use Conversation Memory` switch
  2. `Memory Turns` selector (2-24)
  3. Persisted in `user_settings.json` and injected into API call history window.
- Bumped Windows app version constant to `v0.1.1-beta2-build37`.
- Updated Windows release manifest entry to `build37` package name/url.
- Produced eval comparison artifact for 20-case set:
  - `agent_system/output/eval-compare-build36-build37.json`

## Minimal Verification (This Round)
- `python -m py_compile`:
  - `app/desktop_app.py`
  - `app/user_settings.py`
  - `agent_system/runtime.py`
- `pytest`:
  - `外贸助理_交接包/外贸助理_windows_内测包/tests/test_api_chat.py`
  - `外贸助理_交接包/外贸助理_windows_内测包/tests/test_self_improving_preferences.py`
  - `tests/test_agent_eval_runner.py`
  - Result: `10 passed`
- Build gate + packaging:
  - `scripts/build_windows_release.ps1 -Version v0.1.1-beta2-build37 -SkipTests`
  - Result: success, zip generated in release folder

## Next Top 3
1. Windows真机验收：重点验证“关闭本地上下文 + 开启会话记忆”链路与回复连续性。
2. 将会话记忆策略升级为“摘要记忆 + 最近轮次混合”，降低长对话 token 成本。
3. 用户确认后同步 mac 到同能力集并产出对应 `beta2-build37` 包。
