# Project

Personal site publishing workspace. Fixed rules and workflow authority are defined in `AGENTS.md`; this handoff only captures the current recovery state and what to do next.

# Current Branch

`codex/site-publishing`

# Current Status

- Workspace is in a partial/inconsistent state: `website_from_playground/` files are currently deleted in the working tree and not restored.
- `site_ops/output/` is currently missing, so there are no recent generated outputs to resume from there.
- `docs/memory/self_improving_agent.md` is present and active; proactive self-improving is enabled by workspace rule.
- Stitch integration is enabled via `site_ops/config/stitch-integration.json`; UI polishing remains owned by `ui_stitch_agent`.
- No explicit `RAG` or `harness` constraints were found in the checked startup/config files.

# Last Known Good State

- Latest commit on current branch: `055ad5f` `docs(memory): capture doorway-sign intent and i18n scene asset rule`
- That commit only updated memory, so it is the latest known recorded state, not a verified release snapshot.
- Strategy/policy baseline at last check:
  - Site remains a personal professional website with clear value communication, trust-building, and low-friction conversion.
  - Publishing policy is preview-first and confirmation-gated.
  - Required quality gates before release are content, SEO, UI, and QA review passes.

# Startup Read Order

1. `AGENTS.md`
2. `docs/memory/self_improving_agent.md`
3. `site_ops/config/site-strategy.md`
4. `site_ops/config/publishing-policy.json`
5. Latest files under `site_ops/output/` if that directory exists
6. If UI work is involved, also read `site_ops/config/stitch-integration.json`
7. If agent sequencing matters, read `site_ops/config/agent-registry.json`

# Next Actions

1. Confirm whether the current deletions under `website_from_playground/` are intentional before changing or restoring anything.
2. Re-establish the actual runnable site state from repository files, since there is no current `site_ops/output/` snapshot to rely on.
3. If resuming UI work, follow the Stitch handoff requirements: export reference, component map, style tokens, responsive notes.
4. Before any release-impacting action, obtain explicit user confirmation and satisfy content/SEO/UI/QA review gates.
5. After any substantial run, append durable learnings to `docs/memory/self_improving_agent.md`.

# Constraints

- Fixed rules are governed by `AGENTS.md`.
- Do not write under `site_ops/output/` without explicit user confirmation.
- Do not perform release/deploy actions without explicit user confirmation.
- Do not move outside personal-site publishing scope unless the user explicitly redirects scope.
- Do not commit secrets or expose raw credentials; use `.env`/secret stores and mask logs.
- Treat current repo files as source of truth for shipped behavior; performance/content outcomes are advisory until confirmed.

# Notes

- Checked startup memory entries emphasize:
  - proactive sub-agent orchestration is expected in this worktree;
  - self-improving updates are mandatory after substantial work;
  - homepage/secondary-page visual rules currently lean toward a bright, cinematic plaza-style system;
  - Windows Chinese-path handling is fragile for image/Pillow flows, so ASCII alias paths are preferred when image pipelines are resumed.
- Existing recovery context files in `docs/`:
  - `docs/WEBSITE_HANDOFF_FROM_PLAYGROUND_2026-03-26.md`
  - `docs/site-agent-architecture-report-2026-03-26.md`
- No recent output artifacts were available at handoff time because `site_ops/output/` does not exist in the current worktree.
