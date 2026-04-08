# Status Snapshot
Updated: 2026-04-08  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Latest published release remains: `v0.1.1-beta2-build38`
- Published artifacts:
  - `TA_Beta_v0.1.1-beta2-build38_windows.zip`
  - `TA_Beta_v0.1.1-beta2-build38_mac.zip`
  - `TA_Beta_v0.1.1-beta2-build38_mac.dmg`
- GitHub Release:
  - `https://github.com/tongxigogo-crypto/foreign-trade-assistant/releases/tag/v0.1.1-beta2-build38`

## Current Development Round
- Windows local-model support is implemented, packaged, and accepted for the next Windows build.
- Added local providers inside the existing API conversation panel:
  - `local_ollama`
  - `local_openai`
- Local providers now support:
  - auto-detect common local service URLs
  - refresh installed model list
  - local requests without API key
  - reuse of existing local-context, memory, preference-learning, and web-fallback layers
- UI wiring remains inside the existing Windows desktop API panel; no second chat surface was introduced.

## Accepted Local Artifact
- Windows package prepared for acceptance:
  - `TA_Beta_v0.1.1-beta2-build39_windows.zip`
- Windows app version:
  - `v0.1.1-beta2-build39`
- Release state:
  - packaged locally only
  - not yet published
  - mac sync still pending

## Verification
- Tests:
  - `python -m pytest "外贸助理_交接包/外贸助理_windows_内测包/tests/test_api_chat.py" "外贸助理_交接包/外贸助理_windows_内测包/tests/test_self_improving_preferences.py" tests/test_agent_eval_runner.py -q`
  - result: `13 passed`
- Compile check:
  - `python -m py_compile "外贸助理_交接包/外贸助理_windows_内测包/app/version.py" "外贸助理_交接包/外贸助理_windows_内测包/app/api_chat.py" "外贸助理_交接包/外贸助理_windows_内测包/app/desktop_app.py"`
  - result: `pass`
- Packaging:
  - `powershell -ExecutionPolicy Bypass -File "外贸助理_交接包/外贸助理_windows_内测包/scripts/build_windows_release.ps1" -Version "v0.1.1-beta2-build39" -SkipTests`
  - result: `pass`

## Docs Added
- `docs/superpowers/specs/2026-04-07-local-model-support-design.md`
- `docs/superpowers/plans/2026-04-07-local-model-support.md`

## Notes
- A parallel project directory `vylora-com-site` was intentionally moved out of this repo to `E:\CodexWorkspace\vylora-com-site` and is not part of this delivery.
- This round is closed as a Windows-first change set; mac work should start only after explicit instruction.

## Next Top 3
1. Publish `build39` for Windows when release timing is confirmed.
2. Sync the same local-model capability set to mac.
3. Do real-device local-runtime smoke with `Ollama` or another OpenAI-compatible local runtime when available.
