# Multi-Agent Foreign Trade Automation System

## Mission
Build, maintain, and evolve a coordinated multi-agent system for international trade operations.

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

## Source Of Truth

- Gmail is source of truth for inbound email content.
- CRM storage is source of truth for customer status after successful write.
- Pricing and freight assumptions come from configured business data sources.
- Research outputs are advisory unless promoted into governed rules.

## Security Rules

- Never commit secrets, tokens, passwords, or raw credentials.
- Load sensitive values from `.env` or secret stores.
- Mask sensitive values in logs.

## Global Auxiliary Skill

- Use the global `self-improving-agent` skill as an auxiliary layer when durable learnings should be preserved after failures, user corrections, or repeated success patterns.
- Keep learnings isolated to this workspace in `docs/memory/self_improving_agent.md`.
- Do not mix short-video learnings into the foreign trade assistant memory file.

## Delivery Order

1. Review relevant agent definitions.
2. Explain intended architecture or impact briefly.
3. Update `agents/*.md` if behavior changes.
4. Update `.codex/config.toml` if routing/coordination changes.
5. Implement code.
6. Add or update tests.
7. Document migration notes if contracts changed.
