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
- The Windows local-model support feature set has now been synced to mac.
- Both package trees now support local providers inside the existing API conversation panel:
  - `local_ollama`
  - `local_openai`
- Local providers now support:
  - auto-detect common local service URLs
  - refresh installed model list
  - local requests without API key
  - reuse of existing local-context, memory, preference-learning, and web-fallback layers

## Cloud Build Result
- Cloud build workflow: `Build InVault Releases`
- Run id: `24133793510`
- Source ref: `codex/product-manager`
- Requested version: `v0.1.1-beta2-build39`
- Result:
  - Windows job passed
  - macOS job passed

## Local Cloud Artifacts
- Windows cloud-built artifact stored at:
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包\release\TA_Beta_v0.1.1-beta2-build39_windows.zip`
- mac cloud-built artifacts stored at:
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta2-build39_mac.zip`
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta2-build39_mac.dmg`

## Verification
- mac tests:
  - `python -m pytest "外贸助理_交接包/外贸助理_mac_内测包/tests/test_api_chat.py" "外贸助理_交接包/外贸助理_mac_内测包/tests/test_update_manager.py" -q`
  - result: `10 passed`
- mac compile check:
  - `python -m py_compile "外贸助理_交接包/外贸助理_mac_内测包/app/api_chat.py" "外贸助理_交接包/外贸助理_mac_内测包/app/desktop_app.py" "外贸助理_交接包/外贸助理_mac_内测包/app/version.py"`
  - result: `pass`

## Notes
- This round completed the mac sync and cloud build for `build39`, but did not yet change the published update manifest from `build38` to `build39`.
- A parallel project directory `vylora-com-site` remains outside this repo at `E:\CodexWorkspace\vylora-com-site`.

## Next Top 3
1. Publish `build39` assets and update both release manifests when release timing is confirmed.
2. Run real-device local-runtime smoke once `Ollama` or another OpenAI-compatible local runtime is available.
3. Decide whether to keep the mac regression tests separate from Windows or consolidate shared API chat tests.
