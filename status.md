# Status Snapshot
Updated: 2026-04-08  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Latest published release: `v0.1.1-beta2-build39`
- Published artifacts:
  - `TA_Beta_v0.1.1-beta2-build39_windows.zip`
  - `TA_Beta_v0.1.1-beta2-build39_mac.zip`
  - `TA_Beta_v0.1.1-beta2-build39_mac.dmg`
- GitHub Release:
  - `https://github.com/tongxigogo-crypto/foreign-trade-assistant/releases/tag/v0.1.1-beta2-build39`
- Online manifest:
  - `https://tongxigogo-crypto.github.io/foreign-trade-assistant-site/api/release-manifest.json`

## Current Development Round
- Windows and mac local-model support have both been synced and cloud-built for `build39`.
- Release assets are now published and the online update manifest has been switched to `build39`.
- Local providers remain available inside the existing API conversation panel:
  - `local_ollama`
  - `local_openai`

## Published Artifacts
- Windows artifact:
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包\release\TA_Beta_v0.1.1-beta2-build39_windows.zip`
- mac artifacts:
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta2-build39_mac.zip`
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta2-build39_mac.dmg`

## Verification
- Cloud build workflow:
  - `Build InVault Releases`
  - run id: `24133793510`
  - result: `windows + macOS passed`
- Online manifest check:
  - result: `build39 returned`
- GitHub Release assets:
  - result: `uploaded`

## Next Top 3
1. Run real-device local-runtime smoke once `Ollama` or another OpenAI-compatible local runtime is available.
2. Track whether users can update successfully from `build38` to `build39` in-app.
3. Consolidate or separate cross-platform API chat regression tests deliberately instead of ad-hoc copying.
