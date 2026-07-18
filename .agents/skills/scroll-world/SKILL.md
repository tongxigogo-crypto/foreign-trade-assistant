---
name: scroll-world
description: Build or adapt immersive website experiences where scrolling scrubs a pre-rendered continuous camera journey through connected scenes. Use for 3D or diorama worlds, scroll cinematics, fly-through brand stories, product journeys, seamless camera chains, native mobile variants, scrub-engine integration, and boundary-frame visual QA.
---

# Scroll World for Codex

Build a website where scroll position drives a pre-rendered camera journey. Preserve the existing site stack, generate or receive a frame-locked video chain, integrate the portable scrub engine, and verify the result in a browser.

The non-negotiable rule is pixel continuity: every chained clip must start from the actual rendered last frame of the previous clip. Never substitute the original scene still at a seam.

## Operating contract

- Use the current Codex session and available tools. Never launch nested `codex exec` processes.
- Treat image/video generation, authentication, paid API use, publishing, and writes to `site_ops/output/` as explicit confirmation gates.
- Keep generated media in a dedicated project directory. Separate source prompts, raw renders, boundary frames, encoded clips, and site deliverables.
- Preserve the current framework and published behavior. Adapt the portable engine instead of replacing the application stack.
- Use the cross-worktree link for video-specialist work:
  - `camera_chain` and `native_mobile_chain` route to `video_workflow`.
  - `web_scroll_runtime` remains in `site-publishing`.
  - `seam_qa` may run in either workspace.
- Do not directly import code from the peer worktree or share mutable output directories. Exchange structured handoff data through `scripts/scroll-world-link.py`.

## Load references progressively

The upstream resources remain under `../../../skills/scroll-world/` relative to this adapter:

- Read `references/prompts.md` for intake fields and prompt templates.
- Read `references/pipeline.md` completely before executing Higgsfield commands, extracting boundary frames, or encoding clips.
- Read `references/scrub-engine.js` completely before copying or modifying the engine.
- Use `references/index-template.html` for a standalone implementation.
- Use `references/knockout.py` only when transparent floating scenes are requested.

Do not load every reference during intake or planning.

## Workflow

### 1. Preflight

Check `ffmpeg`, `ffprobe`, and the intended still/video generation route. Check Higgsfield CLI, authentication, model schema, workspace, and credits only when Higgsfield generation is actually requested.

If Higgsfield is missing, prepare the brief, prompts, manifests, site integration, and placeholders without generation. Do not invent an installation command or silently choose another paid provider.

### 2. Confirm the brief

Capture:

- Subject, one-line journey, and brand name.
- Brand palette and tone.
- One shared art-direction preamble.
- Ordered scenes, normally 5–7.
- Desktop-only or desktop plus native 9:16 mobile chain.
- Camera architecture:
  - Continuous forward chain for grounded walkthroughs.
  - Dive plus aerial connectors only for miniature/diorama worlds.
- Render model and budget tier.

Before any paid generation, state the estimated scene/video count, include re-roll headroom, calibrate cost with one still and one video when possible, and obtain explicit approval.

### 3. Route specialist work

Check linkage:

```bash
python3 scripts/scroll-world-link.py status
```

Delegate continuous camera planning or native mobile chains:

```bash
python3 scripts/scroll-world-link.py dispatch \
  --capability camera_chain \
  --project-id <project-id> \
  --brief <brief>
```

Use `native_mobile_chain` for true portrait renders. Never present a center crop as the native mobile version.

### 4. Build the visual chain

- Use one still-image source for all scenes.
- Reuse the exact style preamble in every scene prompt.
- Use one frame-lock-capable video model for the whole chain.
- For a continuous forward chain, start each new leg from the previous leg's actual last frame and preserve camera velocity across the seam.
- For diorama connectors, use the previous rendered clip's last frame and the next rendered clip's first frame as connector endpoints.
- Review every boundary frame before spending credits on the next dependent render.

Use the current session's image-generation tool for Codex-generated stills. Do not follow upstream examples that start a second Codex process.

### 5. Encode and integrate

- Encode at native resolution with uniform codec settings, small GOP, stripped audio, and faststart.
- Use native portrait renders for the optional mobile chain.
- Integrate the portable engine through configuration rather than rewriting it per page.
- Preserve reduced-motion behavior, still posters, iOS priming, seek coalescing, safe-area handling, and blob-based seekability.

### 6. Verify

Before claiming completion:

- Compare screenshots immediately before and after every seam.
- Confirm actual rendered boundary frames were used.
- Confirm `video.seekable.end(0) > 0` and scroll changes `currentTime`.
- Check console errors, desktop layout, one phone viewport, and reduced motion.
- For a native mobile build, verify portrait media is served and `videoWidth < videoHeight`.
- Verify no publishing action or `site_ops/output/` write occurred without confirmation.

Return structured blockers when authentication, credits, source assets, peer linkage, or confirmation is missing. Do not silently degrade a seamless or native-mobile requirement.
