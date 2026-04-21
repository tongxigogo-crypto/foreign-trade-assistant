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

## [2026-04-09 22:20:00] plaza-entry-baked-signs-and-real-pretext

- status: confirmed_rule
- summary: When the homepage must feel like one game plaza, entrance labels should be baked into the scene image (or visually integrated as facade signage), and clickable regions should map to door zones instead of floating chips.
- learnings:
  - Replace floating hotspot pills with facade-level or baked signage; keep DOM entrance elements mostly invisible and use them as hit areas over doors only.
  - Integrate `@chenglou/pretext` as real ESM vendor modules (`vendor/pretext/*.js`) and use it for title layout computation, not DOM jitter tricks.
  - If Chinese text is painted into generated images via Python/Pillow in Windows shell flows, avoid terminal encoding corruption by using Unicode escapes (`\uXXXX`) for deterministic rendering.
  - To make a character appear independently cursor-followed in a static scene, split out a transparent cast layer from the same base scene and move that layer, while keeping background parallax subtle.
  - For immersive homepage mode, hide the regular footer on home and compress mobile header nav to avoid breaking first-screen atmosphere.

## [2026-04-09 16:40:00] user-intent-door-sign-vs-overlay

- status: confirmed_rule
- summary: For this homepage, user intent is not generic hotspot labels. They want building-integrated signage and door-as-entry behavior; overlays should be minimized and only used when visually indistinguishable from original signboards.
- learnings:
  - When user says “把门头改成入口”, interpret as “preserve scene realism”: edit facade sign text (or localized scene variant) and keep click target mapped to the actual door/building zone.
  - For bilingual signage on generated scene art, prefer per-language scene assets (`*-zh.png` / `*-en.png`) and switch by language state, instead of persistent floating chips.
  - Avoid Chinese path encoding issues in Windows shell flows by using ASCII alias paths (e.g., `C:\\Users\\Administrator\\Desktop\\personal_site_assets`) for all image pipelines.

## [2026-04-12 20:30:00] lightweight-rebuild-with-local-pretext

- status: confirmed_working
- summary: For the personal-site rebuild direction, a lighter Apple-led layout with small fairytale accents works better than a heavy scene homepage, and `@chenglou/pretext` should be vendored locally into `website_from_playground/vendor/pretext/`.
- learnings:
  - Use lightweight local SVG illustrations for Pet IP, Trade Assistant, pet trade, and mini-program sections instead of large raster hero scenes when the user prioritizes fast loading.
  - Keep the homepage as alternating media/text rows (`左右交叉`) and make the IP + tool -> pet trade relationship explicit in copy; do not rely on users to infer the business link.
  - Apply `pretext` only to the hero title and major section headings, and use it to compute balanced widths rather than decorative jitter.
  - In this Windows desktop environment, local browser verification is more reliable through HTML structure tests plus module import checks than through long-lived ad-hoc background HTTP servers.

## [2026-04-12 21:35:00] utf8-source-vs-console-mojibake

- status: confirmed_working
- summary: In this Windows worktree, browser screenshots and PowerShell output can hide a real source-encoding problem; verify UTF-8 page content from file bytes or decoded HTTP responses before assuming the Chinese copy is healthy.
- learnings:
  - If page text contains markers like `瀹`, `鍥`, `棣`, `鑱`, or stray `€`, treat it as a real mojibake regression and fix the source files, not just the terminal rendering.
  - For local preview verification, use Python to fetch the served page and decode as UTF-8 with Unicode escapes in the script when the shell path or console encoding is unreliable.
  - Keep homepage HTML, secondary page HTML, and `app.js` i18n content aligned so SEO metadata, no-JS fallback text, and runtime language switching stay consistent.
- When the site broadens from a single product page to a personal-site profile, update `llms.txt`, `/.well-known/agent.json`, and `/api/openapi.json` together so discovery metadata does not lag behind the visible site.

## [2026-04-18 00:00:00] scrollytelling-homepage-and-admin-v1

- status: confirmed_working
- summary: For this rebuild, the homepage should use a desktop-first scrollytelling structure with five scenes, while the backend should start as a practical admin console focused on submissions and basic traffic data.
- learnings:
  - Use the Mochi-style storytelling reference as the visual and pacing anchor, but replace the content with the user's own pet-trade narrative.
  - Keep `Q` and `Douzi` as recurring characters across all scenes; do not treat them as isolated mascots.
  - The opening scene should combine a sharp pain-point headline with dispersed pain visuals that physically overwhelm the characters.
  - Backend v1 should prioritize submission handling and analytics visibility over decorative admin features.
  - Plan the admin area in the same project first, but leave a clean boundary for later separation into an independent management system.

## [2026-04-20 00:00:00] karpathy-style-engineering-global-constraint

- status: confirmed_rule
- summary: This worktree now treats `karpathy-style-engineering` as a global engineering constraint for implementation, debugging, and code review.
- learnings:
  - Restate the requested outcome before editing, then identify the smallest change that can achieve it.
  - Prefer simple, local fixes over broad cleanup or speculative abstraction.
  - Keep changes precise and avoid refactoring adjacent code unless it directly blocks the requested result.
  - Verify against a concrete success condition before claiming completion; if verification is partial, state the risk clearly.

## [2026-04-21 01:40:00] v5-laptop-first-screen-reset

- status: confirmed_rule
- summary: The V5 rebuild should keep the existing multi-scene architecture, but the first screen is no longer mascot-centered; it is now a real-feeling laptop that absorbs trade pain points and converts into the Trade Assistant UI.
- learnings:
  - Keep the V5 page structure, but replace the opening narrative from “Q and Douzi getting overwhelmed” to “laptop screen under pressure -> system response -> UI conversion”.
  - The main headline belongs inside the laptop screen, not outside it.
  - The visual direction should be bright, soft-gradient, product-polished, and technological without using dark oppressive cyberpunk styling.
  - Use scrollytelling for page progression and pain-point trajectories, and reserve HyperFrames for screen-contained product motion assets.
  - Pet IP remains later in the story as brand identity, while the final conversion still centers on the Trade Assistant APP.

## [2026-04-21 02:20:00] v5-scene-boundaries-and-ip-layout

- status: confirmed_working
- summary: For the rewritten external `indexV5.html`, scene boundaries need explicit non-overlapping `autoAlpha` timing, and the Pet IP scene must use dedicated layout columns instead of overlaying an absolute copy block on top of character cards.
- learnings:
  - In this scrollytelling build, starting Scene N+1 before Scene N is fully hidden reads as a bug, not as cinematic overlap; keep the transitions sequential unless the user explicitly asks for blending.
  - The modules scene becomes too airy when copy and console columns are spaced like a marketing hero; tighten the grid, reduce gaps, and give the feature explanation a denser system-dashboard feel.
  - If the user asks to add a line like “换模型不用重头学习”, place it in the system-process or feature-logic layer, not as decorative marketing copy.
  - For IP scenes with large portraits, never combine an absolutely positioned headline block with the same visual region as the image cards; split text and image into separate columns first, then style within those boundaries.

## [2026-04-21 03:10:00] external-v6-refined-variant-pattern

- status: confirmed_working
- summary: When the user iterates local homepage files such as `indexV6.html` or `indexV6.1.html`, preserve the source draft and write changes into a sibling refined variant instead of editing the original directly.
- learnings:
  - For user-owned desktop HTML prototypes, default to `indexVx.y_refined.html` so the original Gemini/other-AI draft remains available for comparison.
  - In these V6-style concept pages, the highest-value changes are usually brand/product truth corrections and interaction-safe mascot integration, not large structural rewrites.
  - If a floating global core changes from a circle to a mascot-shaped badge, update the obstacle physics from circular to elliptical instead of keeping a stale radius approximation.

## [2026-04-21 03:35:00] v6-refined-mascot-core-and-truth-pass

- status: confirmed_working
- summary: For external V6 concept pages, the best upgrade path is to preserve the interaction scaffold, replace generic AI-brand language with real product/brand facts, and swap abstract mascot placeholders for actual local IP assets.
- learnings:
  - When a floating obstacle becomes a mascot-driven core, prefer using the real local character asset instead of drawing a synthetic mascot face in CSS.
  - Once the obstacle silhouette changes away from a circle, keep the text-flow physics aligned with an ellipse or shape approximation so the Pretext demo still feels intentional.
  - On these concept pages, hero support strips carrying version, privacy model, and compatibility are more valuable than extra slogan copy because they anchor the concept to a believable product.
  - Pet IP sections become materially stronger when they show the real local XiaoQ/Douzi images and runway art instead of initial-letter placeholders.

## [2026-04-21 04:20:00] v6-laptop-workspace-productization

- status: confirmed_working
- summary: For the external V6 homepage direction, the next high-value iteration after brand-truth correction is to turn the laptop interior from a concept input/output demo into a denser desktop-first Trade Assistant workspace with real operational panels.
- learnings:
  - Keep the existing scrollytelling shell, mascot-core interaction, and hero meta anchors; upgrade the laptop internals locally instead of rewriting the whole first scene.
  - A three-column workspace works well here: left for customer context recovery, center for inquiry console plus real product anchor, right for quote/task/action outputs.
  - Using the real local `APP.png` screenshot as one panel inside the laptop materially increases product credibility without needing to replace the whole scene with a raw screenshot.
  - The brighter glass-tech direction survives higher information density if panels stay soft, rounded, and operational rather than turning into dark dashboard-card clutter.
