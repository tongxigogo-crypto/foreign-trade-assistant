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

## [2026-04-09 14:20:00] bright-secondary-pages-rule

- status: confirmed_rule
- summary: After a strong homepage visual reset, secondary pages should inherit the same bright brand system and motion language, but remain task-oriented and lighter than the homepage.
- learnings:
  - For this personal site, `download`, `docs`, and `privacy` should reuse the light palette, rounded glass panels, and restrained pretext-style heading motion from the homepage.
  - Secondary pages should not become miniature hero scenes; keep them operational, readable, and conversion-oriented.
  - When the homepage is image-led and cinematic, the follow-up pages should use simpler cards and clean grids so the homepage remains the emotional peak.
  - Treat build downloads as site-hosted first, with GitHub Release only as fallback behavior.

## [2026-04-09 20:35:00] homepage-plaza-over-cards

- status: confirmed_rule
- summary: For the Xiao Q personal site, the homepage should read as one integrated playable plaza. Do not break the first screen into attachment-like feature cards or repeated section blocks.
- learnings:
  - The four core functions should be represented as buildings or environmental entrances inside the plaza scene, not as foreground cards stacked under the hero.
  - Keep homepage copy minimal: brand, short world statement, language switch, and subtle entry affordances. Let the scene carry the structure.
  - Mouse-responsive character behavior should be implemented as a restrained local motion layer inside the plaza scene, not as a second disconnected mascot composition.
  - Mobile can use lighter fallback entry buttons if needed for tappability, but desktop should prioritize the cinematic plaza illusion.
