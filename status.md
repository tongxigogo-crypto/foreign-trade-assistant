# Status Snapshot
Updated: 2026-04-02  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active delivery target: `v0.1.1-beta2-build37` (Windows + mac sync)
- Windows package: `TA_Beta_v0.1.1-beta2-build37_windows.zip`
- mac package: `TA_Beta_v0.1.1-beta2-build37_mac.zip`

## This Round (mac Sync)
- Synced mac API panel behavior with Windows:
  - provider switch now auto-syncs model default
  - added `Use Conversation Memory` toggle
  - added `Memory Turns` selector (2-24)
  - persisted via `user_settings.json`
- Bumped mac app version to `v0.1.1-beta2-build37`.
- Unified Win/Mac release manifest to build37 zip assets for one-click update.
- Built and packaged mac zip in release folder.
- Published Win/Mac build37 zip files into local download directories under both package websites.

## Verification
- mac compile check:
  - `app/desktop_app.py`
  - `app/user_settings.py`
  - `app/version.py`
- mac tests:
  - `tests/test_update_manager.py`
  - `tests/test_history_importer.py`
  - Result: `11 passed`

## Artifacts
- `外贸助理_交接包/外贸助理_windows_内测包/release/TA_Beta_v0.1.1-beta2-build37_windows.zip`
- `外贸助理_交接包/外贸助理_mac_内测包/release/TA_Beta_v0.1.1-beta2-build37_mac.zip`
- Download dir (local):
  - `外贸助理_交接包/外贸助理_windows_内测包/website/assets/downloads/`
  - `外贸助理_交接包/外贸助理_mac_内测包/website/assets/downloads/`

## Note
- `dmg` creation requires macOS toolchain (`hdiutil`); current Windows environment delivered zip channel required by in-app one-click update.

## Next Top 3
1. On mac host, generate signed/unsigned `build37.dmg` from same staged content.
2. Execute mac real-device smoke for one-click update path.
3. Freeze beta2 build37 and open next build focus list.
