# Playground-pm Agent Architecture (v2)

## Mission

Refactor and run a stable agent system for software-worktree governance.
This worktree focuses on agent architecture, workflow reliability, and review quality.
Do not modify shipped application code unless the user explicitly asks.

## Single Entry

All agent workflow entry goes through:
- `agent_system/runtime.py`

Legacy `trade_ops/*` orchestration is compatibility only, not the default control plane.

## Startup Priority

For every new session, restore in this order:

1. `AGENTS.md`
2. `docs/harness/session_state.json`
3. `docs/harness/current_session.md`
4. `docs/harness/architecture_guardrails.json` (if exists)
5. `docs/harness/closed_loop_verdict.json` (if exists)
6. `docs/memory/self_improving_agent.md`
7. latest run report under `agent_system/output/`

## Required Agents (Core)

- `orchestrator_agent`: controls phase gates and final status.
- `rag_agent`: indexes and retrieves workspace knowledge.
- `guardrails_agent`: enforces architecture contract before run.
- `self_improving_agent`: records durable lessons from failures and corrections.
- `review_agent`: produces software review findings only; no code edits in review mode.

## Phase Contract

- `preflight`: validate required agents/status schema/planned outputs.
- `retrieval`: run RAG query and persist retrieval trace.
- `execution`: run or simulate agent outputs.
- `closed_loop`: produce objective checks and evidence bundle.
- `checkpoint`: write harness state and memory updates.

## Scope Boundary

- Allowed: `agent_system/*`, `docs/harness/*`, `docs/memory/*`, `scripts/*`, `tests/*` (architecture tests only).
- Forbidden by default: application runtime/package code under `外贸助理_交接包/*/app`.

## Confirmation Gate

- Business-impacting actions require explicit user confirmation.
- Architecture and process changes can be applied directly.
- Review-only requests must not write into software source directories.

## Security

- Never commit secrets or credentials.
- Load sensitive values from `.env` or secret stores.
- Mask sensitive values in outputs.
