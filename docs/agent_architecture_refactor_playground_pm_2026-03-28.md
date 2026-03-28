# Playground-pm Agent Architecture Refactor (2026-03-28)

## Goal

Rebuild the worktree agent architecture into a single, durable control plane with:
- RAG retrieval trace
- Harness recovery state
- Closed-loop evidence
- Self-improving memory

This refactor does not modify developed software under application source directories.

## What Was Changed

1. Replaced root `AGENTS.md` with a concise v2 contract.
2. Added config-driven core under `agent_system/config/`.
3. Added sample agent-output input under `agent_system/input/`.
4. Kept runtime entry at `agent_system/runtime.py` and switched it to config-driven required outputs + RAG sources.
5. Simplified harness scripts:
   - `scripts/harness-start.ps1`
   - `scripts/harness-finish.ps1`
   - added `scripts/run-agent-system.ps1`
6. Reset self-improving memory to clean v2 baseline:
   - active file: `docs/memory/self_improving_agent.md`
   - archived legacy stack: `docs/memory/archive/self_improving_agent.legacy.2026-03-28.md`

## New Single Entry Workflow

1. `scripts/harness-start.ps1`
2. `scripts/run-agent-system.ps1 -Mode preview`
3. Review `docs/harness/architecture_guardrails.json`
4. Review `docs/harness/closed_loop_verdict.json`
5. `scripts/harness-finish.ps1` to checkpoint

## Role Model (v2)

- `orchestrator_agent`: phase gate owner
- `rag_agent`: workspace retrieval/indexing
- `guardrails_agent`: architecture contract checker
- `self_improving_agent`: rule memory maintenance
- `review_agent`: review-only findings, no software edits by default

## Guardrails

- Architecture edits allowed in: `agent_system/*`, `docs/*`, `scripts/*`, `tests/*`.
- Software edits forbidden by default under: `外贸助理_交接包/*/app`.

## Verification Plan

- Run unit tests for `agent_system` modules only.
- Run runtime in preview mode and verify harness outputs are regenerated.
- Confirm no app-source file was edited by this refactor.
