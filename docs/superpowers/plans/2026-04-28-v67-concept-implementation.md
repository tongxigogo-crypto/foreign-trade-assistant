# V6.7 Concept Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first independent `indexV6.7_concept.html` prototype for reviewing the scroll-driven AI product launch direction.

**Architecture:** Create one standalone external HTML file under `C:\Users\Administrator\Desktop\preson\` so current V6.6 production files remain untouched. The page uses a pinned GSAP/ScrollTrigger timeline with five absolute-positioned scenes, plus lightweight interaction feedback.

**Tech Stack:** HTML, CSS, vanilla JavaScript, GSAP, ScrollTrigger.

---

### Task 1: Standalone Concept Page

**Files:**
- Create: `C:\Users\Administrator\Desktop\preson\indexV6.7_concept.html`

- [ ] **Step 1: Create the standalone page shell**
  - Add semantic HTML, light v0/AI launch visual tokens, fixed nav, boot overlay, cursor, toast, and story stage.

- [ ] **Step 2: Add five concept scenes**
  - Hero / Trade Assistant workspace.
  - Core capabilities.
  - Xiao Q and Douzi IP scene.
  - Pet product story picks.
  - Contact / conversion.

- [ ] **Step 3: Add scroll-driven motion**
  - Register GSAP ScrollTrigger.
  - Pin the story stage.
  - Crossfade scenes.
  - Animate camera scale, heading movement, UI cards, and navigation progress.

- [ ] **Step 4: Add interaction feedback**
  - Custom cursor.
  - Click ripple.
  - Toast feedback.
  - Card hover/active state.
  - Navigation scene jump.

- [ ] **Step 5: Verify locally**
  - Confirm file exists.
  - Run basic HTML/JS string checks.
  - Open through a local server or browser preview for visual review.

### Task 2: Keep Git Scope Clean

**Files:**
- Modify: `docs/superpowers/plans/2026-04-28-v67-concept-implementation.md`

- [ ] **Step 1: Stage only the plan doc if committing**
  - Do not stage existing V6.6 adapter/test dirty files.
  - Do not stage `website_from_playground/styles.css`.

- [ ] **Step 2: Leave external concept HTML untracked**
  - The concept page is outside this git repo and is reviewed manually.
