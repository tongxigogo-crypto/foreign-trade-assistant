# Status Snapshot
Updated: 2026-04-02  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active version baseline: `v0.1.1-beta2-build1`
- Windows scope in this round only (mac pending explicit sync command)
- Release assets for `v0.1.1-beta2-build1` are available on GitHub Release, including mac `.dmg/.zip` direct links

## Scope Closed In This Round (Windows)
- Desktop API panel:
  - provider switch now auto-syncs both `api_url` and default `model` (no manual model reset needed)
  - one-click update changed to direct execution path after detecting a new version (no second confirmation dialog)
- Desktop top bar:
  - version label added (zh/en localized)
  - theme mode selector added: `system | light | dark` (zh/en display mapping + persistence)
- Theme persistence:
  - `UserSettings.theme_mode` introduced and validated (`system` fallback on invalid value)
- Business panel linkage:
  - import completion now triggers immediate `refresh_runtime_status()` to sync right-panel/customer detail view without waiting for polling

## Minimal Verification (This Round)
- Command:
  - `python -m pytest -q tests/test_api_chat.py tests/test_update_manager.py tests/test_desktop_import_customer_linking.py tests/test_user_settings_theme.py tests/test_desktop_api_provider_linkage.py`
- Result:
  - `17 passed`

## Next Top 3
1. Windows real-package smoke: verify provider-model auto jump, theme switch persistence, and one-click update full path on installed package.
2. After user confirmation, sync the same feature set to mac package tree and rerun mirrored tests.
3. Build next beta2 windows package and run auto-update end-to-end from older beta install.
