# Status Snapshot
Updated: 2026-03-30  
Workspace: `E:\CodexWorkspace\Playground-pm`  
Branch: `codex/product-manager`

## Current Release
- Active version: `v0.1.1-beta1-build29`
- Tag commit: `421aa4fc762f73e135251ad7ade3486277d5825f`
- Build run: `23715376491` (`success`)
- Artifacts synced:
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta1-build29_mac.dmg`
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_mac_内测包\release\TA_Beta_v0.1.1-beta1-build29_mac.zip`
  - `E:\CodexWorkspace\Playground-pm\外贸助理_交接包\外贸助理_windows_内测包\release\TA_Beta_v0.1.1-beta1-build29_windows.zip`

## Scope Closed In This Round
- Fixed history import failure isolation:
  - parser exceptions no longer abort the whole batch import
  - failed files are recorded into `failed_files` and processing continues
- Synced importer behavior for both mac/windows packages.
- Added regression tests for parser-exception paths.

## Minimal Verification (This Round)
- `python -m pytest tests/test_history_importer.py -q` (mac package): `8 passed`
- `python -m pytest tests/test_history_importer.py -q` (windows package): `7 passed`
- GitHub Actions build: [run `23715376491`](https://github.com/tongxigogo-crypto/foreign-trade-assistant/actions/runs/23715376491) = `success`

## Next Top 3
1. mac real-device import smoke on mixed folders (valid + broken office files) and collect one sample log.
2. windows side real-package smoke for the same mixed-folder import scenario.
3. evaluate optional legacy `.doc` support policy (support via controlled converter vs explicit unsupported notice).
