# Multi-Agent Foreign Trade Automation System

## Mission

Build, maintain, and evolve a coordinated multi-agent system for international trade operations.

## Startup Priority

For any new conversation in this worktree, read these sources first in this order:

1. This file: `AGENTS.md`
2. Workspace memory: `docs/memory/self_improving_agent.md`
3. Worktree knowledge: `trade_ops/config/foreign-trade-worktree.md`
4. Pricing rules: `trade_ops/config/pricing-rules.json`
5. Latest operation outputs under `trade_ops/output/`

## Required Agents

- orchestrator
- email_agent
- quotation_agent
- crm_agent
- followup_agent
- research_agent

Agent definitions live under `agents/*.md`.

## Collaboration Rules

- Orchestrator is the only end-to-end workflow coordinator.
- Specialist agents stay in-domain and return structured status when data is missing.
- Shared business objects should be defined once and reused.
- Machine handoff must prefer structured outputs.
- Outbound email recommendations are draft-only for human editing; do not auto-send.

## Source Of Truth

- Gmail is source of truth for inbound email content.
- CRM storage is source of truth for customer status after successful write.
- Pricing and freight assumptions come from configured business data sources.
- Research outputs are advisory unless promoted into governed rules.

## Operational Tree

### 1) New customer

- Analyze customer message and extract demand.
- Use IP or country signal to analyze market demand, usage habits, and price bands.
- If company name is provided, run background profile: founding year, size, industry, products, and credit signals.
- Determine customer role (distributor, engineering contractor, end user, or unknown).
- Determine product direction (specified category vs needs recommendation).
- Generate first-reply strategy and draft.
- If quote is needed, provide advisory quote range and assumptions.

### 2) Existing customer

- Compare latest message against prior thread context.
- Identify whether it is new demand, new issue, or routine progress.
- Recommend best reply strategy based on relationship stage.
- Create personalized follow-up plan with due windows and owner hints.
- Keep follow-up drafts editable for manual sending only.

### 3) Weekly cadence (Friday)

- Produce weekly summary for inquiries, replies, and open actions.
- Track progress by customer stage and urgency.
- Highlight blocked and overdue items.
- Generate next-week action plan.

## Scope Control

- Default scope is foreign-trade operations only.
- Exclude AI video production assets by default.
- Include video-domain knowledge only when explicitly requested by the user.

## Security Rules

- Never commit secrets, tokens, passwords, or raw credentials.
- Load sensitive values from `.env` or secret stores.
- Mask sensitive values in logs.

## Global Auxiliary Skill

- Use `self-improving-agent` as an auxiliary layer when failures, corrections, or reusable success patterns occur.
- Keep learnings isolated to this workspace in `docs/memory/self_improving_agent.md`.
- Auto invoke `scripts/auto_self_improve.ps1` at the end of each substantial workflow run.
- Each run must append one entry with category `success`, `correction`, or `failure`.

## Delivery Order

1. Review relevant agent definitions.
2. Explain intended architecture or impact briefly.
3. Update `agents/*.md` if behavior changes.
4. Update workspace config when routing or coordination changes.
5. Implement code or workflow updates.
6. Add or update tests when applicable.
7. Document migration notes if contracts changed.
8. Append self-improving memory entry for this run.
