# Status Snapshot
Updated: 2026-04-05  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active delivery target: `v0.1.1-beta2-build38`
- Windows package: `TA_Beta_v0.1.1-beta2-build38_windows.zip`
- mac packages:
  - `TA_Beta_v0.1.1-beta2-build38_mac.zip`
  - `TA_Beta_v0.1.1-beta2-build38_mac.dmg`
- GitHub Release:
  - `https://github.com/tongxigogo-crypto/foreign-trade-assistant/releases/tag/v0.1.1-beta2-build38`

## This Round (build38 Closure)
- Pushed `build38` app-version and manifest bump on `codex/product-manager`.
- Ran local gate: `python -m agent_system.runtime --root . --run-id local-build38-gate --mode preview --audit-level auto`
- Triggered cloud workflow `Build InVault Releases`:
  - run id: `23998170126`
  - result: `windows-latest` success, `macos-latest` success
- Downloaded cloud-built artifacts and refreshed local release folders:
  - `澶栬锤鍔╃悊_浜ゆ帴鍖?澶栬锤鍔╃悊_windows_鍐呮祴鍖?release/TA_Beta_v0.1.1-beta2-build38_windows.zip`
  - `澶栬锤鍔╃悊_浜ゆ帴鍖?澶栬锤鍔╃悊_mac_鍐呮祴鍖?release/TA_Beta_v0.1.1-beta2-build38_mac.zip`
  - `澶栬锤鍔╃悊_浜ゆ帴鍖?澶栬锤鍔╃悊_mac_鍐呮祴鍖?release/TA_Beta_v0.1.1-beta2-build38_mac.dmg`
- Uploaded the same three artifacts to GitHub Release `v0.1.1-beta2-build38`.
- Switched both update manifests to GitHub Release asset URLs so one-click update no longer depends on separately published site download files.
- Confirmed this repo does not have GitHub Pages enabled; removed local `deploy-website.yml` to avoid false CI failures.
- Confirmed live site publishing remains owned by `tongxigogo-crypto/foreign-trade-assistant-site`.

## Verification
- mac updater regression:
  - `python -m pytest 澶栬锤鍔╃悊_浜ゆ帴鍖匼澶栬锤鍔╃悊_mac_鍐呮祴鍖匼tests\test_update_manager.py -q`
  - result: `3 passed`
- windows + agent regression:
  - `python -m pytest 澶栬锤鍔╃悊_浜ゆ帴鍖匼澶栬锤鍔╃悊_windows_鍐呮祴鍖匼tests\test_api_chat.py 澶栬锤鍔╃悊_浜ゆ帴鍖匼澶栬锤鍔╃悊_windows_鍐呮祴鍖匼tests\test_self_improving_preferences.py tests\test_agent_eval_runner.py -q`
  - result: `10 passed`
- runtime gate:
  - `python -m agent_system.runtime --root . --run-id local-build38-gate --mode preview --audit-level auto`
  - result: `needs_confirmation`, summary `7/7 checks passed`

## Release Artifacts
- local release:
  - `澶栬锤鍔╃悊_浜ゆ帴鍖?澶栬锤鍔╃悊_windows_鍐呮祴鍖?release/TA_Beta_v0.1.1-beta2-build38_windows.zip`
  - `澶栬锤鍔╃悊_浜ゆ帴鍖?澶栬锤鍔╃悊_mac_鍐呮祴鍖?release/TA_Beta_v0.1.1-beta2-build38_mac.zip`
  - `澶栬锤鍔╃悊_浜ゆ帴鍖?澶栬锤鍔╃悊_mac_鍐呮祴鍖?release/TA_Beta_v0.1.1-beta2-build38_mac.dmg`
- cloud artifact cache:
  - `agent_system/output/ci_artifacts_23998170126/`

## Next Top 3
1. On real devices, verify old-build -> `build38` one-click update on Windows and mac.
2. Upgrade conversation memory from raw turn window to summary + recent-turn hybrid memory.
3. Add涓撻」璇勬祴 for `鏈湴璧勬枡缂哄け鑷姩鑱旂綉鍏滃簳` and `鍏抽棴鏈湴涓婁笅鏂囦絾淇濈暀浼氳瘽璁板繂`.
