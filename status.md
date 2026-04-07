# Status Snapshot
Updated: 2026-04-07  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active delivery target: `v0.1.1-beta2-build38`
- Released artifacts remain:
  - `TA_Beta_v0.1.1-beta2-build38_windows.zip`
  - `TA_Beta_v0.1.1-beta2-build38_mac.zip`
  - `TA_Beta_v0.1.1-beta2-build38_mac.dmg`
- GitHub Release:
  - `https://github.com/tongxigogo-crypto/foreign-trade-assistant/releases/tag/v0.1.1-beta2-build38`

## Current Development Round
- Added Windows local-model support inside the existing API conversation panel.
- Added local providers:
  - `local_ollama`
  - `local_openai`
- Local providers now support:
  - auto-detect common local service URLs
  - refresh installed model list
  - local requests without API key
  - reuse of existing local-context, memory, preference-learning, and web-fallback layers
- UI wiring remains inside the existing Windows desktop API panel; no second chat surface was introduced.

## Verification
- Tests:
  - `python -m pytest 外贸助理_交接包\外贸助理_windows_内测包\tests\test_api_chat.py 外贸助理_交接包\外贸助理_windows_内测包\tests\test_self_improving_preferences.py tests\test_agent_eval_runner.py -q`
  - result: `13 passed`
- Compile check:
  - `python -m py_compile 外贸助理_交接包\外贸助理_windows_内测包\app\api_chat.py 外贸助理_交接包\外贸助理_windows_内测包\app\desktop_app.py 外贸助理_交接包\外贸助理_windows_内测包\app\user_settings.py`
  - result: `pass`

## Docs Added
- `docs/superpowers/specs/2026-04-07-local-model-support-design.md`
- `docs/superpowers/plans/2026-04-07-local-model-support.md`

## Notes
- This round is code-complete for Windows local-model support, but no new build/package has been produced yet.
- mac sync is still pending and should follow only after Windows acceptance.

## Next Top 3
1. Windows real-device smoke with `Ollama` and one OpenAI-compatible local runtime.
2. Package next Windows build after acceptance.
3. Sync the same capability set to mac.
