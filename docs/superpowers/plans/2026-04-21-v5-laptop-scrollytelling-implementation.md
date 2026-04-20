# V5 Laptop Scrollytelling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refit `indexV5.html` to keep its five-scene scrollytelling structure while changing the first-screen narrative to a laptop-under-pressure story and aligning the whole page to a bright, product-tech visual system.

**Architecture:** Preserve the single-file V5 page structure and GSAP/ScrollTrigger-driven scene progression. Replace the mascot-centered opening with a laptop-centered screen transformation, then rewrite later scenes to match the new visual language while still retaining Pet IP and APP-focused closing.

**Tech Stack:** HTML, CSS, GSAP, ScrollTrigger, TextPlugin, local media/assets

---

### Task 1: Lock The New Scene Model Into The Existing File

**Files:**
- Modify: `C:\Users\Administrator\Desktop\preson\indexV5.html`

- [ ] **Step 1: Back up the current file**

Run: `Copy-Item 'C:\Users\Administrator\Desktop\preson\indexV5.html' 'C:\Users\Administrator\Desktop\preson\indexV5.before-laptop-redesign.html' -Force`
Expected: backup file exists

- [ ] **Step 2: Replace the visual thesis in CSS**

Update:
- root colors
- background system
- typography accents
- section materials

Expected result:
- bright gradient page
- glass/product-tech surfaces
- removal of dark cartoon warmth from the current version

- [ ] **Step 3: Keep the five-scene shell but swap scene responsibilities**

Expected mapping:
- Scene 1: laptop + pain impact + UI conversion
- Scene 2: product solution
- Scene 3: functional system expansion
- Scene 4: Pet IP showcase
- Scene 5: APP-centered contact close

### Task 2: Rebuild Scene 1 Around The Laptop

**Files:**
- Modify: `C:\Users\Administrator\Desktop\preson\indexV5.html`

- [ ] **Step 1: Remove mascot-centered first-screen composition**

Delete or repurpose:
- split mascot intro layout
- mascot-hit-first logic
- old warm pain setup

- [ ] **Step 2: Build a laptop hero**

Create:
- laptop shell
- screen area
- half-visible keyboard area
- screen-contained hero title

Expected result:
- first viewport reads as a premium product poster

- [ ] **Step 3: Build pain-card trajectories toward the laptop**

Implement:
- explicit card paths
- impact timing
- screen response timing

Expected result:
- pain cards visibly hit the laptop screen, not random coordinates

- [ ] **Step 4: Transform the screen into Trade Assistant UI**

Implement:
- scan / boot / flash / system-lock sequence
- UI reveal inside the screen

Expected result:
- the narrative moves from trade pain to software solution in one screen

### Task 3: Rewrite Scenes 2-5 Without Breaking Flow

**Files:**
- Modify: `C:\Users\Administrator\Desktop\preson\indexV5.html`

- [ ] **Step 1: Replace Scene 2 content**

Focus:
- explain product payoff after first-screen conversion

- [ ] **Step 2: Replace Scene 3 content**

Focus:
- system modules: customer, quote, email, tasks, records

- [ ] **Step 3: Retain Scene 4 as Pet IP**

Focus:
- unify Pet IP visual treatment with the new bright tech language

- [ ] **Step 4: Retain Scene 5 as APP-centered contact close**

Focus:
- conversion remains tied to the Trade Assistant APP

### Task 4: Verification

**Files:**
- Modify: `C:\Users\Administrator\Desktop\preson\indexV5.html` if fixes are needed

- [ ] **Step 1: Load the page and inspect for broken text or encoding**

Run:
- open file locally or inspect generated preview

Expected:
- no mojibake

- [ ] **Step 2: Validate GSAP timeline basics**

Expected:
- scenes still progress in order
- first-screen impact sequence reads correctly

- [ ] **Step 3: Check visual hierarchy**

Expected:
- first screen is simpler than the old version
- laptop is dominant
- title is inside screen
- background stays bright and premium

- [ ] **Step 4: Capture remaining gaps**

Expected:
- short list of any remaining polish items rather than architectural issues
