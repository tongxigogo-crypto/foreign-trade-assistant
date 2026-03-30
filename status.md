# Status Snapshot
Updated: 2026-03-30  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active version baseline: `v0.1.1-beta2-build1`
- Release baseline commit: `4a91dd3`
- Packaging result:
  - Windows package rebuilt: `TA_Beta_v0.1.1-beta2-build1_windows.zip`
  - mac package: pending (requires mac build environment with python3-venv + hdiutil)
- Update manifest baseline:
  - windows/mac `website/api/release-manifest.json` unified to `v0.1.1-beta2-build1`
  - asset URLs changed to absolute downloadable URLs under `https://tongxigogo-crypto.github.io/foreign-trade-assistant-site/assets/downloads/`

## Scope Closed In This Round
- API chat capability for desktop mode:
  - local-context mode now supports automatic web fallback when local facts are missing/insufficient
  - non-local-context mode now keeps multi-turn memory via conversation history
  - web retrieval path supports DuckDuckGo-first + Bing fallback
- Version baseline switched from beta1 to beta2 in both mac/windows app trees
- Update manifests synchronized for beta2 baseline and auto-update URL compatibility
- Windows beta2 package rebuilt successfully

## Minimal Verification (This Round)
- `python -m pytest tests/test_api_chat.py -q` (windows package): `6 passed`
- `python -m pytest tests/test_update_manager.py -q` (windows package): `6 passed`
- `python -m pytest tests/test_desktop_import_customer_linking.py -q` (windows package): `2 passed`
- `powershell -ExecutionPolicy Bypass -File scripts/build_windows_release.ps1 -Version v0.1.1-beta2-build1`: `success`

## Next Top 3
1. Rebuild mac `v0.1.1-beta2-build1` package in native mac environment and sync `.dmg/.zip` to downloads path.
2. Run desktop auto-update E2E check from beta1/beta2 old install to beta2 build1 (check manifest fetch + download + apply).
3. Do windows real-package smoke for: local-miss web fallback + no-local-context multi-turn memory, then record one user-facing validation note.
