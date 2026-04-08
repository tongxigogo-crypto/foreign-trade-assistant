# Self Improving Agent Memory

This file stores reusable learnings, corrections, and failure patterns for this worktree only.

## Persistent Rule

- This memory is proactive, not passive.
- After substantial runs, record reusable learnings without waiting for the user to ask.
- Capture repeated failures, corrected assumptions, and stable workflow patterns immediately so future runs can reuse them.


## [2026-03-17 00:58:09] trade-ops-run

- status: needs_confirmation
- summary: Preview mode blocked write operations for 2026-03-17.

## [2026-04-09 13:20:00] figma-homepage-capture-workflow

- status: confirmed_working
- summary: For homepage visual exploration, prefer generating a local HTML moodboard in the user asset folder and capture localhost into Figma via `generate_figma_design` instead of trying to import large images with `use_figma`.
- learnings:
  - `use_figma` runtime in this environment does not support `createImageAsync` and has no `fetch`, so direct URL image import is not viable.
  - Windows + Chinese path handling is fragile for Python/Pillow output; use an ASCII directory alias/junction such as `C:\Users\Administrator\Desktop\personal_site_assets` that maps to the real Chinese folder.
  - For image-heavy Figma work, build a simple local HTML page, inject the Figma capture script, serve it with `python -m http.server`, and capture into an existing Figma file with `generate_figma_design`.
  - Keep the capture script in the local HTML until the user explicitly asks to remove it.

## [2026-04-09 13:45:00] proactive-subagent-orchestration

- status: confirmed_rule
- summary: In this worktree, do not wait for the user to remind about sub-agents. The orchestrator should proactively create the minimum useful set of specialist agents whenever the task can be decomposed into independent tracks.
- learnings:
  - Treat proactive sub-agent dispatch as part of the default agent architecture, not an optional optimization.
  - Use sub-agents especially for parallel strategy, content, UI/Figma, SEO, QA, and release preparation work.
  - Keep the orchestrator as the only end-to-end coordinator and merge sub-agent outputs back into one execution path.
