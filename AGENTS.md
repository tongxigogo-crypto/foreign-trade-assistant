# Multi-Agent Foreign Trade Automation System

## Mission

Build, maintain, and evolve a coordinated multi-agent system for international trade operations.

## Startup Priority

For any new conversation in this worktree, read these sources first in this order:

1. `AGENTS.md`
2. `docs/memory/self_improving_agent.md`
3. `trade_ops/config/foreign-trade-worktree.md`
4. `trade_ops/config/pricing-rules.json`
5. Latest outputs under `trade_ops/output/`

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

