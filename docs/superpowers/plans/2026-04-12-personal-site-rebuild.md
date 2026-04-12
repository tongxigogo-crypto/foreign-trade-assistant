# Personal Site Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the personal website around a lighter Apple-minimal plus fairytale-accent visual system while preserving the four fixed entry themes and retaining `pretext` for key headings.

**Architecture:** Restore or confirm the current static-site baseline first, then rebuild the homepage information hierarchy and visual system on top of the existing page set (`index.html`, `download.html`, `docs.html`, `privacy.html`, `styles.css`, `app.js`, assets). Keep the site static and lightweight, restrict motion to small enhancements, and narrow `pretext` usage to high-value headings only.

**Tech Stack:** Static HTML, CSS, JavaScript, existing `pretext` integration/vendor modules, image assets, pytest for orchestrator tests only if repo-side workflow files are touched.

---

### Task 1: Confirm and Restore the Site Baseline

**Files:**
- Confirm existence/state: `website_from_playground/index.html`
- Confirm existence/state: `website_from_playground/download.html`
- Confirm existence/state: `website_from_playground/docs.html`
- Confirm existence/state: `website_from_playground/privacy.html`
- Confirm existence/state: `website_from_playground/styles.css`
- Confirm existence/state: `website_from_playground/app.js`
- Reference: `docs/WEBSITE_HANDOFF_FROM_PLAYGROUND_2026-03-26.md`

- [ ] **Step 1: Inspect git status and record the current deletion set**

Run: `git status --short`
Expected: show the existing deletions under `website_from_playground/` so work does not begin on an uncertain filesystem state.

- [ ] **Step 2: Ask the user whether the current `website_from_playground/` deletions are intentional**

Expected: explicit confirmation to either restore the site baseline or proceed with a different source of truth.

- [ ] **Step 3: If the deletions are not intentional, restore the baseline files**

Run: `git restore website_from_playground`
Expected: the original transferred site files return to the working tree.

- [ ] **Step 4: Verify the restored baseline files exist**

Run: `Get-ChildItem website_from_playground`
Expected: the page files, assets, and support files listed in `docs/WEBSITE_HANDOFF_FROM_PLAYGROUND_2026-03-26.md` are present.

- [ ] **Step 5: Commit the baseline restoration if restoration was required**

```bash
git add website_from_playground
git commit -m "chore: restore site baseline before rebuild"
```

### Task 2: Audit the Existing Site Structure and `pretext` Integration

**Files:**
- Read: `website_from_playground/index.html`
- Read: `website_from_playground/download.html`
- Read: `website_from_playground/docs.html`
- Read: `website_from_playground/privacy.html`
- Read: `website_from_playground/styles.css`
- Read: `website_from_playground/app.js`
- Read: `docs/memory/self_improving_agent.md`

- [ ] **Step 1: Identify current homepage sections, navigation anchors, and four-entry mapping**

Run: `rg -n "href=|section|download|docs|privacy|pretext" website_from_playground`
Expected: exact markup locations for navigation, sections, and `pretext` hooks.

- [ ] **Step 2: Document the current `pretext` loading and initialization path**

Expected: know whether `pretext` is loaded from local vendor files, inline script, or another mechanism before editing.

- [ ] **Step 3: Capture which current assets are still reusable**

Expected: a short decision list for hero/IP imagery, entry images, and any icons that can stay after the redesign.

- [ ] **Step 4: Commit notes only if code comments or inline docs were intentionally added**

If no repo files changed, skip commit.

### Task 3: Define the New Homepage Information Hierarchy in Markup

**Files:**
- Modify: `website_from_playground/index.html`
- Reference: `docs/superpowers/specs/2026-04-12-personal-site-rebuild-design.md`

- [ ] **Step 1: Write the failing structural expectation by creating a manual HTML checklist in the plan execution notes**

Expected checklist:
- hero with left IP visual and right intro block
- four alternating content rows
- preserved four fixed entry targets
- explicit IP/tool/trade relationship statement

- [ ] **Step 2: Restructure homepage markup to match the approved hierarchy**

Required sections:
- lightweight hero
- row 1: Pet IP image + Pet IP introduction
- row 2: business bridge text + Foreign Trade Assistant download card/image/link
- row 3: Pet supplies international trade intro + visual
- row 4: Mini-program development intro + visual

- [ ] **Step 3: Preserve or remap the four entry links so navigation targets remain valid**

Expected: all four destination anchors/pages still exist and are easy to reach.

- [ ] **Step 4: Verify the HTML contains only the new structure and no leftover plaza-specific scaffolding**

Run: `rg -n "plaza|portal|hotspot|scene" website_from_playground/index.html`
Expected: no outdated homepage concept markers remain unless intentionally reused.

- [ ] **Step 5: Commit the homepage structural rewrite**

```bash
git add website_from_playground/index.html
git commit -m "feat: rebuild homepage information hierarchy"
```

### Task 4: Rebuild the Visual System for Speed and Clarity

**Files:**
- Modify: `website_from_playground/styles.css`
- Modify: `website_from_playground/index.html`
- Optional asset references: `website_from_playground/assets/*`

- [ ] **Step 1: Define CSS variables for the new visual system**

Required token groups:
- background colors
- text colors
- accent colors
- border/surface colors
- radius
- shadow
- spacing
- motion timing

- [ ] **Step 2: Implement the Apple-minimal base layout**

Required outcomes:
- strong whitespace
- clean grid behavior
- readable type scale
- restrained cards/surfaces
- desktop and mobile consistency

- [ ] **Step 3: Layer the fairytale tone lightly through image treatment and accents**

Allowed techniques:
- warm gradients
- subtle glow
- rounded surfaces
- soft highlight backgrounds

Not allowed:
- heavy decorative background scenes
- large parallax systems
- dense floating ornaments

- [ ] **Step 4: Replace heavy hero styling with a lightweight dynamic presentation**

Expected: subtle fade/float only, no large layered animation stack.

- [ ] **Step 5: Verify mobile layout stacks cleanly for all alternating rows**

Run: open local site and inspect mobile breakpoint behavior.
Expected: rows collapse into readable single-column sections without losing the alternating narrative.

- [ ] **Step 6: Commit the visual-system rewrite**

```bash
git add website_from_playground/styles.css website_from_playground/index.html
git commit -m "feat: apply lightweight visual system to homepage"
```

### Task 5: Preserve and Narrow `pretext` Usage

**Files:**
- Modify: `website_from_playground/index.html`
- Modify: `website_from_playground/app.js`
- Read or modify if present: any local `pretext` vendor path referenced by the homepage

- [ ] **Step 1: Locate all current `pretext` targets**

Run: `rg -n "pretext" website_from_playground`
Expected: exact initialization and markup targets.

- [ ] **Step 2: Reduce `pretext` application to the homepage title and major section headings only**

Expected: body copy, utility labels, and small captions do not use `pretext`.

- [ ] **Step 3: Verify `pretext` still initializes without console errors**

Run: serve the site locally and inspect browser console.
Expected: no initialization errors, no missing module/path errors.

- [ ] **Step 4: Verify headings remain visually intentional on mobile**

Expected: no broken line composition, overflow, or unreadable letter spacing.

- [ ] **Step 5: Commit the `pretext` cleanup**

```bash
git add website_from_playground/index.html website_from_playground/app.js
git commit -m "feat: focus pretext on key headings"
```

### Task 6: Rewrite Homepage Messaging Around the Business Relationship

**Files:**
- Modify: `website_from_playground/index.html`
- Optional text constants if they exist: `website_from_playground/app.js`

- [ ] **Step 1: Draft concise homepage copy for hero and four alternating rows**

Required copy outcomes:
- clear identity statement
- clear product/tool statement
- explicit explanation that IP + tool support later pet-supplies international trade
- clear framing for mini-program capability

- [ ] **Step 2: Replace old homepage copy with the new concise messaging**

Expected: homepage becomes easier to scan and more business-legible.

- [ ] **Step 3: Verify no row reads like an unrelated portfolio item**

Expected: all four areas feel connected within one strategy.

- [ ] **Step 4: Commit the copy rewrite**

```bash
git add website_from_playground/index.html website_from_playground/app.js
git commit -m "feat: align homepage copy with ip and trade strategy"
```

### Task 7: Rebuild Secondary Pages to Match the New System

**Files:**
- Modify: `website_from_playground/download.html`
- Modify: `website_from_playground/docs.html`
- Modify: `website_from_playground/privacy.html`
- Modify: `website_from_playground/styles.css`
- Modify: `website_from_playground/app.js` if shared navigation/page logic needs updates

- [ ] **Step 1: Audit each secondary page for content blocks that should stay unchanged in meaning**

Expected: preserve page purpose while improving presentation.

- [ ] **Step 2: Apply the new shared layout, spacing, and typography system**

Expected: all pages feel part of one site family.

- [ ] **Step 3: Keep secondary pages lighter than the homepage**

Expected: simpler surfaces, simpler imagery, strong readability.

- [ ] **Step 4: Verify download page keeps primary conversion actions obvious**

Expected: download CTA is immediately visible and trustworthy.

- [ ] **Step 5: Commit the secondary-page restyle**

```bash
git add website_from_playground/download.html website_from_playground/docs.html website_from_playground/privacy.html website_from_playground/styles.css website_from_playground/app.js
git commit -m "feat: restyle secondary pages for rebuilt site"
```

### Task 8: Optimize Assets and Loading Behavior

**Files:**
- Modify or replace: `website_from_playground/assets/*`
- Modify: `website_from_playground/index.html`
- Modify: `website_from_playground/styles.css`

- [ ] **Step 1: Inventory current image assets and identify oversized files**

Run: `Get-ChildItem website_from_playground/assets | Select-Object Name,Length`
Expected: clear candidates for resize/re-export.

- [ ] **Step 2: Resize or replace the homepage hero asset for web delivery**

Expected: one optimized hero asset with appropriate rendered dimensions.

- [ ] **Step 3: Ensure below-the-fold visuals do not dominate initial load**

Expected: lower-priority images use proper sizing/loading behavior.

- [ ] **Step 4: Recheck first-screen visual simplicity**

Expected: no unnecessary decorative assets reintroduced during implementation.

- [ ] **Step 5: Commit the asset optimization**

```bash
git add website_from_playground/assets website_from_playground/index.html website_from_playground/styles.css
git commit -m "perf: optimize site assets for rebuilt homepage"
```

### Task 9: Verify Behavior, Readability, and Constraints

**Files:**
- Verify: `website_from_playground/index.html`
- Verify: `website_from_playground/download.html`
- Verify: `website_from_playground/docs.html`
- Verify: `website_from_playground/privacy.html`
- Verify: `website_from_playground/styles.css`
- Verify: `website_from_playground/app.js`

- [ ] **Step 1: Serve the site locally**

Run: `python -m http.server 8000`
Expected: pages available locally for browser validation.

- [ ] **Step 2: Verify desktop behavior**

Required checks:
- hero reads immediately
- alternating layout feels coherent
- four entries are intact
- `pretext` headings render correctly

- [ ] **Step 3: Verify mobile behavior**

Required checks:
- no overflow
- no broken heading composition
- CTA remains visible
- row stacking remains understandable

- [ ] **Step 4: Verify console cleanliness**

Expected: no JavaScript errors and no broken asset/module paths.

- [ ] **Step 5: Verify the approved strategic relationship is visible in the homepage copy**

Expected: users can infer why Pet IP and Foreign Trade Assistant belong together.

- [ ] **Step 6: Commit final verification adjustments**

```bash
git add website_from_playground
git commit -m "fix: polish rebuilt personal site interactions and layout"
```

### Task 10: Prepare Preview-Only Release Readiness

**Files:**
- Review only unless explicitly confirmed: `site_ops/config/publishing-policy.json`
- Optional docs update after substantial run: `docs/memory/self_improving_agent.md`

- [ ] **Step 1: Confirm all required quality gates are satisfied**

Required gates from policy:
- `content_review_passed`
- `seo_review_passed`
- `ui_review_passed`
- `qa_review_passed`

- [ ] **Step 2: Summarize what changed and what still needs explicit confirmation**

Expected: a concise readiness note for the user.

- [ ] **Step 3: Do not write under `site_ops/output/` and do not deploy without explicit user confirmation**

Expected: policy compliance.

- [ ] **Step 4: After substantial implementation, append durable learnings to memory**

File: `docs/memory/self_improving_agent.md`
Expected: record reusable site-rebuild lessons only after the implementation run actually happens.

