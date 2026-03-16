# Foreign Trade Worktree Policy

## Execution mode

- `self-improving-agent` invocation is enabled.
- Auto-commit is enabled when repository files change.
- Business writes are confirmation-gated.

## Integration policy

- Gmail: read-only
- Google Drive: read-only
- Outbound messages: draft-only, manual send

## Output policy

- Default run mode is preview only.
- Any write to `trade_ops/output/*` or `trade_ops/state.json` must be explicitly confirmed.

