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

## [2026-04-21 05:05:00] v6-content-polish-and-core-identity

- status: confirmed_working
- summary: After the V6 laptop workspace is productized, the next useful refinement is not more modules but sharper Chinese-first utility copy, tighter hero spacing, and a more intentional mascot-core crop/glow treatment.
- learnings:
  - On these external personal-site prototypes, the best copy tone is product-operator language rather than explanatory prototype language; reduce "concept demo" phrasing and describe workflow outcomes directly.
  - The hero support cards read better as a fixed three-column strip on desktop than as loose pills once the laptop interior becomes denser.
  - The mascot core becomes more brand-like when the image is cropped tighter with glow and a cleaner chip label, while keeping the existing elliptical collision model unchanged.
  - For stable desktop verification of scroll-activated states in single-file HTML prototypes, generate a temporary preview variant that forces the active panel visible instead of relying on automated scrolling in headless capture.

## [2026-04-22 00:10:00] static-site-admin-v1-with-stdlib-backend

- status: confirmed_working
- summary: For this worktree, the smallest reliable backend v1 is a Python-stdlib admin layer that serves a JSON content document, image uploads, and a simple authenticated editor while leaving the existing static frontend intact.
- learnings:
  - When the frontend already exists as static HTML/CSS/JS, prefer adding a narrow content API plus admin editor over rebuilding the site into a framework just to get content management.
  - In this environment, do not assume FastAPI or other web dependencies are installed; verify first, and fall back to WSGI/stdlib when the dependency cost is not justified.
  - Keep homepage text and homepage image overrides in one shared `website_from_playground/content/site-content.json` document, and make the frontend merge that data into its existing i18n object at boot.
  - Backend v1 should be useful on first open: provide a default content skeleton with keys like `hero_intro` and the managed image slots so the editor is not an empty JSON shell.
  - A minimal `site_backend/server.py` wrapper that serves both static files and `/admin` routes is enough for local operation and easier to verify than introducing a heavier deployment shape too early.

## [2026-04-22 09:05:00] real-publish-source-vs-repo-demo-site

- status: confirmed_rule
- summary: Before wiring any admin preview or publish flow, verify the user's real release target. In this project, the real homepage source can live outside the repo and must not be silently substituted with an in-repo demo site.
- learnings:
  - If the user names a specific local publish artifact such as `C:\\Users\\Administrator\\Desktop\\preson\\indexV6.6_refined.html`, treat that file as the homepage source of truth for preview and save flows until told otherwise.
  - Do not assume the repo's static demo site is the publish target just because it already has a backend scaffold.
  - When the real publish source is a standalone HTML file, prefer serving that file directly through the local backend and syncing admin saves back into the same file, instead of maintaining a disconnected parallel preview target.

## [2026-04-22 13:58:00] v66-preview-chinese-asset-paths

- status: confirmed_working
- summary: When the admin preview targets the external V6.6 HTML, Chinese image paths need two protections: normalize previously corrupted JSON image values, and normalize WSGI `PATH_INFO` before resolving static files.
- learnings:
  - `wsgiref.simple_server` on Windows can surface percent-encoded or mojibake `PATH_INFO`; recover by attempting `latin-1 -> utf-8` decoding and then `unquote` before mapping to disk.
  - If earlier saves produced corrupted values in `site-content.json`, keep a small fixup map in the V6.6 adapter so preview and sync do not strand existing content entries.
  - When local preview behavior appears unchanged after a fix, first check for multiple `site_backend.server` processes; stale instances can mask a correct code change and make debugging look inconsistent.

## [2026-04-22 14:20:00] admin-preview-diagnostics-panel

- status: confirmed_working
- summary: The admin preview flow is safer when the sidebar shows draft-vs-published state and image asset reachability before opening the homepage preview.
- learnings:
  - For this local CMS flow, the most actionable preview hints are: whether preview will use draft content, how many text/image changes differ from the saved version, and whether each managed image path responds successfully from the local server.
  - When preview can open an unsaved draft safely, use a lightweight confirmation modal only when there are draft changes or asset risks; otherwise open preview directly.
  - Image-path checks can stay entirely client-side in the admin page by fetching the same-origin asset URL that the preview page will use.

## [2026-04-22 15:05:00] external-v66-seo-first-pass

- status: confirmed_working
- summary: For the external `indexV6.6_refined.html`, the highest-value first SEO pass is not a framework migration but a machine-readable layer added directly to the existing single-file homepage.
- learnings:
  - Prioritize `head` metadata, `JSON-LD`, precise `alt` text, and `aria-label` on the real `h1` before touching broader architecture.
  - In this project phase, keep the scrollytelling DOM and GSAP logic intact; add semantics around the existing structure instead of refactoring the page into a new stack.
  - A useful "framework optimization" inside the current static architecture is resource prioritization: keep above-the-fold mascot/product imagery high-priority and move below-the-fold IP imagery to `loading="lazy"` with async decoding.

## [2026-04-24 00:00:00] external-v66-bilingual-two-file-pattern

- status: confirmed_working
- summary: For the external V6.6 homepage, the safer bilingual pattern is a Chinese default file plus a separate English sibling file, not forcing one file to behave as both language experiences.
- learnings:
  - Keep `C:\Users\Administrator\Desktop\preson\indexV6.6_refined.html` as the Chinese default source of truth and create `indexV6.6_refined_en.html` for the English independent-site version.
  - Use `html[data-site-lang]` and a small shared `bilingual.js` helper for copy hydration and EN/CN button routing, but route buttons between files instead of relying on `?lang=` state.
  - Add a cache-busting query to the shared bilingual script during active local preview so browser cache does not hide recent text changes.
  - For image-led pet gallery cards, keep English titles and summaries short to avoid narrow-viewport word breaks; the homepage should remain visual-first.

## [2026-04-22 16:35:00] external-v66-preview-to-real-integration

- status: confirmed_working
- summary: When the user approves a visual preview for the external homepage, integrate that design into the real `indexV6.6_refined.html` and lock it with an external-file regression test instead of leaving it as a disconnected preview artifact.
- learnings:
  - Approved preview HTML files under `C:\\Users\\Administrator\\Desktop\\preson\\` are only review artifacts; the real completion step is copying the chosen visual language into the source-of-truth V6.6 file.
  - For external homepage regressions, use stable English markers or structural selectors in repo tests when possible; they are less fragile than repeatedly asserting long Chinese strings.
  - For content-led homepage additions in this project, prefer image-first editorial modules with a small DOM footprint so the section can extend brand narrative without disturbing the existing scrollytelling flow.

## [2026-04-22 16:52:00] early-homepage-placeholder-content

- status: confirmed_working
- summary: During the site's early phase, new homepage content modules should explicitly present themselves as placeholders when there are no real detail pages yet, while still matching the visual language of the finished site.
- learnings:
  - For unfinished content systems, replace fake detail links with clear `敬请期待` states so the homepage does not imply missing pages already exist.
  - A new image-led module needs the same `use-pretext` hooks as the rest of V6.6, otherwise it reads as bolted-on even if the layout is visually consistent.
  - Using real local mascot/pet imagery as temporary covers is preferable to abstract gradients when the business already has recognizable brand assets and the backend content system will come later.

## [2026-04-22 17:06:00] editorial-module-heading-alignment

- status: confirmed_working
- summary: In V6.6 mid-page editorial modules, the section heading block should read as a centered stage title rather than a left rail, especially when the card grid spans the full width.
- learnings:
  - For wide showcase sections like `pet-products-gallery`, center the kicker, title, summary, and chip as one heading cluster before the grid starts.
  - A left-aligned heading block can make the top of the section feel visually jammed even when the cards below are balanced.

## [2026-04-22 17:12:00] short-chinese-editorial-headlines

- status: confirmed_working
- summary: Short Chinese section headlines in V6.6 should stay on one centered line on desktop instead of wrapping prematurely under generic responsive heading rules.
- learnings:
  - For headings like `宠物用品内容精选`, widen the heading cluster and locally override `.use-pretext` width behavior so the desktop version reads as one complete line.
  - Allow wrapping again only at narrower breakpoints where the grid has already stepped down.

## [2026-04-22 17:20:00] pretext-heading-fit

- status: corrected_assumption
- summary: Do not force `use-pretext` onto every mid-page editorial headline. For short Chinese display titles, the pretext layout can fight centered single-line typography and produce visibly worse results.
- learnings:
  - If the design goal is a clean centered stage title, prefer a normal `h2` over a pretext heading when the text is short and the surrounding block is already visually rich.
  - Keep pretext on supporting copy or smaller subheads where motion adds texture without destabilizing the headline's shape.

## [2026-04-22 18:05:00] external-v66-gallery-management-and-template-seo

- status: confirmed_working
- summary: For the external V6.6 flow, pet product content should be managed as a dedicated gallery-card object in the backend, with one reusable template page and lightweight SEO files added directly to the external publish directory.
- learnings:
  - `pet_products_gallery.cards[4]` is the right shape for this phase: image, cover label, cover title, title, summary, tag, and status are enough to make the homepage editable without prematurely building full detail-page CMS complexity.
  - When the real homepage source lives outside the repo, complete the loop by syncing both the external `site-content.json` and the external HTML/template files, not just the repo code.
  - A single `pet-product-template.html` plus `robots.txt` and `sitemap.xml` in the external directory is a pragmatic first SEO scaffold before real per-product pages exist.

## [2026-04-22 18:28:00] one-template-before-many-detail-pages

- status: confirmed_working
- summary: Before building many real product detail pages, use one polished shared template page that reads backend-managed gallery data and route homepage cards into it by status plus hash.
- learnings:
  - This phase benefits more from a stable reusable template structure than from generating multiple half-filled pages.
  - The admin must manage both homepage card fields and the shared detail-template copy, otherwise the homepage and template drift immediately.
  - For local smoke checks in this Windows setup, prefer checking stable ASCII markers like `data-template-field`, `pet-product-template`, and `entry-list` instead of relying on Chinese string matching in console output.

## [2026-04-23 01:55:00] v66-editorial-rail-baseline

- status: confirmed_working
- summary: In the external V6.6 homepage, the pet-products editorial area works better as a horizontal content rail inside the same outer width shell used by the other major sections, with one explicit template-preview CTA instead of making every placeholder card clickable.
- learnings:
  - Use one shared outer shell token for scene 1 support elements, features, pet IP, gallery, and closing sections; keep the hero laptop itself intentionally narrower inside that shell.
  - For early-stage gallery cards that are still `coming_soon`, keep their per-card state inert and provide a separate `查看模板预览` entry at the section-note level so the homepage has a clear jump target without implying full detail pages already exist.
  - When a horizontal rail is introduced, lock it in with regression checks for `grid-auto-flow: column`, `overflow-x: auto`, the shared shell token, and the preview-template link.

## [2026-04-23 02:12:00] v66-natural-gallery-motion

- status: confirmed_working
- summary: For the V6.6 pet-products rail, a visible scrollbar reads as unfinished; the better desktop behavior is a hidden-scrollbar editorial rail that auto-drifts gently, pauses on hover, and supports pointer dragging.
- learnings:
  - Keep the rail implementation lightweight: hide the scrollbar, use a simple requestAnimationFrame drift with edge reversal, and pause during hover or pointer drag instead of introducing a heavy marquee dependency.
  - When the shared section shell is tightened too far, the first hero screen is the first place users feel it; widening the outer shell while slightly enlarging the laptop stage restores the intended desktop-first presence without undoing the aligned mid-page widths.

## [2026-04-24 11:42:00] external-v66-template-fields-and-discovery-sync

- status: confirmed_working
- summary: The external V6.6 publishing flow now needs the homepage gallery, shared product template, and SEO discovery files to evolve together; extending only the backend schema is not enough unless the external content JSON, adapter, and generated `robots.txt` / `sitemap.xml` are synchronized in the same run.
- learnings:
  - For the current phase, each `pet_products_gallery` card should carry both `status` and `entry_mode`; `status=live` does not automatically mean the card should navigate, because early live cards may still be display-only.
  - The shared `pet_product_template` object is materially more useful once it includes `eyebrow`, CTA fields, a care section, hero spec cards, and `seo.canonical_path`; otherwise the detail template becomes visually richer than the CMS can actually drive.
  - After schema expansion, always re-save the external content through `ContentStore` so the external homepage HTML, `site-content.json`, `robots.txt`, and `sitemap.xml` stay aligned with the backend’s latest shape.

## [2026-04-24 12:08:00] cms-gallery-needs-visual-rail-preview

- status: confirmed_working
- summary: For the homepage pet-products gallery, a field-only CMS editor is too abstract; backend users make better decisions when the section begins with a compact rail-style visual preview that approximates the homepage reading order.
- learnings:
  - Put the gallery preview ahead of the per-card forms so image dominance, title rhythm, and publish-state semantics are readable before operators dive into individual fields.
  - The backend preview should echo the homepage card grammar, not just show thumbnails; keep the kicker, cover title, title, summary, tag, and state chip in the mini-card so “display only” versus “template page” is obvious.
  - A horizontal preview rail inside the CMS is enough for this phase; there is no need to embed the full homepage iframe just to validate gallery composition.

## [2026-04-24 12:26:00] split-english-site-and-chinese-wechat-page

- status: confirmed_direction
- summary: The personal site should ship as two coordinated experiences instead of one bilingual page: an English desktop-first independent site for SEO and overseas positioning, and a separate Chinese WeChat-friendly page for domestic trust-building and conversion.
- learnings:
  - Do not try to make one homepage simultaneously satisfy Google-facing English SEO and China-facing WeChat conversion; keep the two experiences separated at the page/template level even if they share one backend.
  - Finish the English independent-site version first until it is launch-ready, then build the Chinese mobile-first WeChat page as the next phase.
  - The future CMS should manage both `en` and `zh` variants from one system, but the Chinese page should be a purpose-built conversion page, not a direct visual copy of the English site.

## [2026-04-24 13:18:00] english-launch-polish-needs-dom-targeted-replacements

- status: confirmed_working
- summary: For the external English launch shell, broad search-and-replace against historical mojibake is unreliable; the safe path is to patch real visible DOM nodes and the sync adapter together, then verify with a Unicode scan.
- learnings:
  - When polishing `C:\Users\Administrator\Desktop\preson\indexV6.6_refined.html` and `pet-product-template.html`, check the live DOM text for remaining Han characters instead of assuming the content JSON already covers every visible label.
  - Update `site_backend/v66_adapter.py` in the same run whenever a user-facing gallery alt, status chip, or preview label changes, otherwise the next CMS save can regress the homepage back to mixed-language output.
  - Comments and local asset paths can stay Chinese for now; prioritize only visible launch copy, SEO text, CTA labels, and preview-state semantics.

## [2026-04-24 13:35:00] english-launch-cta-and-resource-gates

- status: confirmed_working
- summary: English launch readiness should treat navigation anchors, real contact links, and first-screen resource priority hints as regression-gated behavior, not one-off manual polish.
- learnings:
  - The external V6.6 homepage needs a real `#contact` section plus navigation entries for `#pet-products-gallery` and `#contact`; CTA-looking controls should be anchors with concrete `mailto:` targets until a form route exists.
  - Keep lightweight resource hints in the HTML head for the current CDN dependencies and first-screen images; this is a low-risk performance improvement before any future bundling or framework migration.
  - Add tests for these launch-facing behaviors because they live in the external page source and are easy to lose during later content syncs.
