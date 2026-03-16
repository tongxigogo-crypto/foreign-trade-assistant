# Foreign Trade Assistant Worktree Knowledge Base

Last updated: 2026-03-16
Source scope: Google Drive and local workspace assets, excluding AI video production content.

## 1) What This Worktree Knows

This worktree has durable knowledge in these domains:

1. Export sales operations and inquiry handling
2. Quote and pricing workflow management
3. Customer analysis and follow-up planning
4. Product catalog and independent-site content operations
5. SEO/content production engineering for trade websites
6. Scripted automation workflow (CSV plus Markdown outputs)

## 2) Core Data Assets To Use In Answers

### Local operational files

- `trade_ops/config/pricing-rules.json`
- `trade_ops/input/inquiries.csv`
- `trade_ops/input/mic-products.csv`
- `trade_ops/input/site-pages.csv`
- `trade_ops/output/customer-analysis-*.md`
- `trade_ops/output/inquiry-quote-pack-*.csv`
- `trade_ops/output/mic-daily-40-*.csv`
- `trade_ops/output/site-update-tasks-*.csv`
- `trade_ops/output/run-summary-*.md`

### Learned Drive-side business assets (non-video)

- Site and navigation documents (for home page and structure planning)
- Product and catalogue sheets (for example `vylora-catalogue` and related xlsx files)
- Customer analysis and form sheets (customer profiling and case tracking)
- Technical proposal and export documents (including English rewrite/export docs)
- Quote and pricing draft documents (including wall panel quote draft data)
- SEO strategy and matrix documents (mother-link archetypes, title/content generators)
- Colab notebooks used for operational content and workflow automation

## 3) Operational Decision Tree

### A. New customer workflow

1. Extract buyer demand from inquiry text.
2. Determine customer role:
   - distributor or reseller
   - engineering contractor or project buyer
   - unknown (request clarification)
3. Build market context:
   - country or region demand pattern
   - likely product use habits
   - pricing band and export feasibility
4. If company name exists, run background profile:
   - company age and size
   - focus industry
   - credit signals
5. Output:
   - customer analysis summary
   - quote suggestion range
   - first-reply draft for manual review

### B. Existing customer workflow

1. Compare latest message with prior thread context.
2. Identify whether it is:
   - new requirement
   - issue or escalation
   - quote or terms negotiation
3. Recommend best reply strategy and risk controls.
4. Create follow-up plan:
   - next action
   - due date
   - personalized tone and objective

### C. Weekly workflow (Friday)

1. Summarize weekly inquiries, replies, and pending actions.
2. Track progress by customer and stage.
3. Identify blockers and risk items.
4. Generate next-week execution plan.

## 4) Output Policy

When answering business questions, default output should include:

1. Key findings
2. Recommended action
3. Draft text (email, reply, follow-up) when relevant
4. Data gaps and assumptions

## 5) Exclusion Rule

Do not use AI video production assets in business reasoning unless the user explicitly requests video domain support.
