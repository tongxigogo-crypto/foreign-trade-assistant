---
name: trade-ops-agent
description: Automate export sales operations for B2B teams. Use when users need to process customer inquiries (email drafts, quotations, customer type segmentation, follow-up plans, customer analysis), build a daily MIC product link plan (40 items/day), and generate independent-site page update tasks (content rewrite plus image supplementation).
---

# Trade Ops Agent

Use this skill to run a repeatable daily workflow for foreign-trade operations.

## 0) Load workspace knowledge first

Before any run or analysis, read:

- `AGENTS.md`
- `trade_ops/config/foreign-trade-worktree.md`
- `trade_ops/config/pricing-rules.json`

Apply only foreign-trade knowledge by default. Exclude AI video production content unless user explicitly asks.

## 1) Initialize workspace

Run:

```powershell
./skills/trade-ops-agent/scripts/init-workspace.ps1
```

This creates `trade_ops/input`, `trade_ops/config`, `trade_ops/output`, and `trade_ops/state.json` with starter data.

## 2) Maintain input files

Update these files before each run:

- `trade_ops/input/inquiries.csv`
- `trade_ops/input/mic-products.csv`
- `trade_ops/input/site-pages.csv`
- `trade_ops/config/pricing-rules.json`

Input format details: see [references/input-files.md](references/input-files.md).

## 3) Run full automation (auto self-improving enabled)

Run:

```powershell
./skills/trade-ops-agent/scripts/run-trade-ops-agent-auto.ps1
```

Optional run date:

```powershell
./skills/trade-ops-agent/scripts/run-trade-ops-agent-auto.ps1 -RunDate 2026-03-09
```

The auto runner appends a self-improving entry to:

- `docs/memory/self_improving_agent.md`

It writes one entry per run with category `success` or `failure`.

## 4) Collect outputs

Read generated files under `trade_ops/output`:

- `inquiry-quote-pack-YYYY-MM-DD.csv`
- `customer-analysis-YYYY-MM-DD.md`
- `mic-daily-40-YYYY-MM-DD.csv`
- `site-update-tasks-YYYY-MM-DD.csv`
- `run-summary-YYYY-MM-DD.md`

## 5) Execution rules

- Prioritize `A-KeyAccount` customers first.
- Keep MIC daily publishing fixed at 40 entries; rotation is controlled by `state.json`.
- Update site tasks only when `needs_content=1` or `needs_image=1`.
- Adjust price logic only through `pricing-rules.json` or script function thresholds.
