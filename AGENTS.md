# Multi-Agent Foreign Trade Automation System

## Mission

Build, maintain, and evolve a coordinated multi-agent system for international trade operations.

## Startup Priority

For any new conversation in this worktree, read these sources first in this order:

1. `AGENTS.md`
2. `docs/harness/session_state.json`
3. `docs/harness/current_session.md`
4. `docs/harness/architecture_guardrails.json` if it exists
5. `docs/harness/closed_loop_verdict.json` if it exists
6. `docs/memory/self_improving_agent.md`
7. `trade_ops/config/foreign-trade-worktree.md`
8. `trade_ops/config/pricing-rules.json`
9. Latest outputs under `trade_ops/output/`

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
- After every substantial run, check `git status --short` before reporting back.
- If the changes are a coherent same-theme set that looks functionally complete, prompt for a收口提交 instead of leaving it hanging.
- If the changes are caches, build outputs, or other noise, prompt for cleanup and do not treat them as commit candidates.
- If the tree contains mixed-purpose changes, classify them first and keep unrelated leftovers untouched unless the user explicitly includes them.
- Packaging execution boundary: complete Windows package first and get user validation before touching Mac package changes, unless user explicitly requests parallel Win+Mac work.
- Keep user-facing delivery simple: default release target is downloadable, double-click runnable package with no Python/pip steps.

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

## Harness Rule

- Treat `docs/harness/session_state.json` as the recovery anchor after background compression.
- Treat `docs/harness/architecture_guardrails.json` as the preflight contract check.
- Treat `docs/harness/closed_loop_verdict.json` as the post-run evidence bundle.
- Before substantial work, restore state from the harness files instead of re-deriving context from scratch.
- After substantial work, checkpoint the current state into the harness files before reporting back.

