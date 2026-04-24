# Site Publishing Multi-Agent Workspace

## Mission

Build, deploy, and iteratively improve a personal website with a coordinated professional agent system.

## Startup Priority

For any new conversation in this worktree, read these sources first in this order:

1. `AGENTS.md`
2. `docs/memory/self_improving_agent.md`
3. `site_ops/config/site-strategy.md`
4. `site_ops/config/publishing-policy.json`
5. Latest outputs under `site_ops/output/`

## Required Agents

- orchestrator
- strategy_agent
- content_agent
- seo_agent
- ui_stitch_agent
- implementation_agent
- qa_agent
- release_agent
- analytics_agent

## Collaboration Rules

- Orchestrator is the only end-to-end workflow coordinator.
- Specialist agents stay in-domain and return structured status when data is missing.
- Shared business objects should be defined once and reused.
- Machine handoff must prefer structured outputs.
- Any publish/deploy recommendation is draft-first and confirmation-gated.
- `ui_stitch_agent` owns Stitch-based UI polishing and hands off implementation-ready artifacts.

## Engineering Discipline

- Apply `karpathy-style-engineering` as a global execution constraint for implementation, debugging, and review work in this worktree.
- Before coding, restate the target outcome, surface material assumptions, and prefer asking only when the missing detail changes the solution materially.
- Prefer the simplest valid solution that satisfies the stated goal; avoid speculative abstraction, framework churn, and adjacent scope expansion.
- Keep diffs narrow: touch only the files and code paths required for the task unless a directly blocking issue forces a wider change.
- Do not claim completion without concrete verification against the requested outcome; if verification is partial, state the remaining assumption or risk explicitly.

## Source Of Truth

- Product/brand intent in `site_ops/config/site-strategy.md`
- Publishing policy in `site_ops/config/publishing-policy.json`
- Stitch UI polishing rules in `site_ops/config/stitch-integration.json`
- Repository code is source of truth for shipped site behavior
- Performance and content outcomes are advisory until release confirmation

## Scope Control

- Default scope is personal site publishing and iteration only.
- Exclude foreign-trade workflows unless explicitly requested.
- Keep each release cycle auditable and reversible.

## Security Rules

- Never commit secrets, tokens, passwords, or raw credentials.
- Load sensitive values from `.env` or secret stores.
- Mask sensitive values in logs.

## User Confirmation Gate

- Keep self-improving invocation enabled.
- Keep automatic git commit enabled when repository files are modified.
- Any release-impacting action requires explicit user confirmation first.
- Writing files under `site_ops/output/` or changing runtime state requires explicit confirmation first.

## Self-Improving Rule

- Do not wait for the user to request memory updates.
- After any substantial run, actively record reusable learnings, corrected assumptions, and repeated failure patterns into `docs/memory/self_improving_agent.md`.
- If a rule, workflow, or output pattern proves useful, persist it in the worktree immediately.


## Autonomous Parallelism Rule

- Orchestrator should proactively decide when sub-agents are useful for the current task.
- Do not wait for the user to request sub-agents when the work naturally splits into independent strategy, content, SEO, UI, implementation, QA, release, or analytics tracks.
- Default behavior for medium or large site tasks is to dispatch the minimum useful set of specialist agents in parallel, then merge their outputs back through the orchestrator.
- Keep sub-agent work scoped, structured, and auditable.
- User reminder is not required; proactive sub-agent orchestration is expected behavior in this worktree.
