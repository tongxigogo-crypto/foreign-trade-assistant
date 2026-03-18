# Trade Ops Orchestrator

## Purpose

This worktree runs a multi-agent foreign-trade assistant with confirmation-gated writes.

## Entry Point

- PowerShell: `scripts/trade-ops-run.ps1`
- Python: `trade_ops/orchestrator.py`

## Modes

- Preview (default): no output/state writes.
- Confirm write: persist outputs and update `trade_ops/state.json`.

## Example

```powershell
python trade_ops/orchestrator.py --root D:\Backup\Documents\Playground --date 2026-03-18 --pretty
python trade_ops/orchestrator.py --root D:\Backup\Documents\Playground --date 2026-03-18 --confirm-writes --pretty
```
