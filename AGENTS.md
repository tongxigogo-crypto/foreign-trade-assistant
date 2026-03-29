# Multi-Agent Foreign Trade Automation System

## Mission

Build, maintain, and evolve a coordinated multi-agent system for international trade operations.

## Startup Priority

For any new conversation in this worktree, read these sources first in this order:

1. `AGENTS.md`
2. `status.md`
3. `docs/harness/session_state.json`
4. `docs/harness/current_session.md`
5. `docs/memory/self_improving_agent.md`
6. `trade_ops/config/foreign-trade-worktree.md`
7. `trade_ops/config/pricing-rules.json`
8. Latest outputs under `trade_ops/output/`

## Required Agents

- orchestrator
- email_agent
- quotation_agent
- crm_agent
- followup_agent
- research_agent

## Collaboration Rules

- Orchestrator is the only end-to-end workflow coordinator.
- Specialist agents stay in-domain and return structured status when data is missing.
- Shared business objects should be defined once and reused.
- Machine handoff must prefer structured outputs.
- Outbound email recommendations are draft-only for human editing; do not auto-send.
- When a user instruction references specific files, prioritize RAG retrieval of latest local files over chat history snippets.
- If local files and conversation snippets conflict, local files are source of truth.

## Workspace Hygiene (Hard Rules)

- `status.md` and `docs/harness/*` are protected baseline files; cleanup routines must never delete them.
- Treat `status.md` and harness files as context anchors, not temporary artifacts.
- At end of each substantial run:
  - Check existence of `status.md`, `docs/harness/session_state.json`, `docs/harness/current_session.md`.
  - If any missing, recreate immediately before reporting completion.
  - Run `scripts/harness-finish.ps1` to force a quick harness checkpoint + self-improving writeback.
  - Then run `git status --short` and classify changes into:
    - commit candidates (same-theme functional work),
    - cleanup-only noise (`__pycache__`, temp downloads, local caches).

## Source Of Truth

- Gmail is source of truth for inbound email content.
- CRM storage is source of truth for customer status after successful write.
- Pricing and freight assumptions come from configured business data sources.
- Research outputs are advisory unless promoted into governed rules.

## Scope Control

- Default scope is foreign-trade operations only.
- Exclude AI video production assets by default.
- Include video-domain knowledge only when explicitly requested.

## Security Rules

- Never commit secrets, tokens, passwords, or raw credentials.
- Load sensitive values from `.env` or secret stores.
- Mask sensitive values in logs.

## User Confirmation Gate

- Keep self-improving invocation enabled.
- Keep automatic git commit enabled when repository files are modified.
- Any business-impacting action requires explicit user confirmation first.
- Gmail and Google Drive access is read-only by default.
- Writing files under `trade_ops/output/` or changing runtime state requires explicit confirmation first.

