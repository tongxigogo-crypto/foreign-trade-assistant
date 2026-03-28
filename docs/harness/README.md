# Harness (v2)

Harness provides the persistent execution state for the rebuilt agent control plane.

## Core Files

- `session_state.json`: machine-readable restore anchor.
- `current_session.md`: human-readable checkpoint.
- `architecture_guardrails.json`: preflight validation result.
- `closed_loop_verdict.json`: post-run evidence and check summary.

## Contract

- Always restore from harness before substantial work.
- Always checkpoint harness after substantial work.
- `agent_system/output/run-report-*.json` is the canonical run artifact linked from harness.
