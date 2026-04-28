# V6.7 Concept Design

## Purpose

Create an independent desktop-first concept page for Tong Studio named `indexV6.7_concept.html`.

This is not a replacement for the current V6.6 production files yet. The page is a structure-and-motion prototype for a video-like HTML product introduction: users scroll through five scenes as if moving through a product launch video, while still interacting with a real webpage.

## Confirmed Direction

- Use HyperFrames as a design method, not as the first implementation target.
- Implement the webpage prototype with HTML, CSS, GSAP, and ScrollTrigger.
- Build the first version as an independent external HTML file under `C:\Users\Administrator\Desktop\preson\`.
- Do not modify `indexV6.6_refined.html` in the first concept pass.
- After the concept is approved, migrate the stable interaction model back into V6.6.
- After the website version is stable, create a real HyperFrames project for product demo video use.

## Visual Direction

The approved visual direction is v0 / AI product launch style:

- Light canvas.
- Soft glass UI.
- Blue and violet glow.
- Product workspace cards.
- Large, clear launch-style headings.
- UI panels that group, expand, and reorganize across scenes.
- No dark cyber terminal theme for this concept pass.

The design should preserve Tong Studio V6.6's current soft-tech product narrative rather than reverting to the earlier black neon game draft.

## Scene Structure

Keep the V6.6 five-scene structure as the narrative backbone:

1. Hero / Trade Assistant workspace.
2. Core capabilities / product modules.
3. Xiao Q and Douzi IP scene.
4. Pet product story picks.
5. Contact / conversion.

The first concept pass may use abstract UI placeholders instead of real production assets. The goal is to validate motion, rhythm, and scene transitions before final asset integration.

## Motion Model

The page should feel like a scroll-driven product launch:

- Scrolling advances a timeline.
- Key scenes can pin to the viewport.
- Scene transitions use full-page fading, camera push/pull, UI card regrouping, and heading re-composition.
- Each scene has a clear entrance, hold, and transition moment.
- The transition should feel closer to an AI product launch than to a standard webpage section reveal.

HyperFrames principles to apply:

- Treat each scene as a composition.
- Build the most visible scene state first.
- Animate into that state.
- Avoid random or non-deterministic animation.
- Keep transitions intentional and readable.

## Interaction Layer

Borrow selected interaction feedback from the Claude Code game-style draft, but tune it for a light product launch page:

- Extremely short brand boot screen, about 0.8 to 1.2 seconds.
- Custom cursor.
- Click ripple.
- Toast feedback.
- Card hover and active states.
- Navigation highlight that follows scene progress.

These effects are supporting feedback, not the primary story. They should not make the page feel like a black cyber game UI.

## Content Strategy

The first concept version is a structure and motion prototype:

- Reuse the existing V6.6 content skeleton.
- Do not perform a full copy rewrite in the first pass.
- Use ordinary-user language for technical ideas such as local-first operation.
- Keep the concept Chinese-first for now.
- Real assets can be connected after the motion direction is approved.

## Device Strategy

Desktop comes first.

The first pass should prioritize 1440px and 1920px wide screens. Mobile should not be broken, but detailed mobile motion and layout polish can follow after the desktop experience is validated.

## Non-Goals For First Pass

- Do not replace the production V6.6 files.
- Do not build a HyperFrames export project yet.
- Do not wire the concept to the backend CMS in the first pass.
- Do not rewrite all copy.
- Do not integrate all real assets in the first pass.
- Do not touch unrelated dirty files.

## Migration Path

1. Build `indexV6.7_concept.html` as an isolated prototype.
2. Review the scroll rhythm, scene transitions, and interaction feedback.
3. Add real assets and copy refinements after the interaction model is approved.
4. Migrate the approved approach into V6.6 production files.
5. Synchronize bilingual runtime and backend adapter as needed.
6. Build a separate HyperFrames project for product demo video use.

## Open Implementation Notes

- Use GSAP and ScrollTrigger for the webpage prototype.
- Keep code isolated from current V6.6 files.
- Prefer deterministic animation values.
- Preserve the existing Douzi AI Core / pretext idea when migrating later, but the concept pass can use placeholders if needed.
- Keep the pet product gallery direction aligned with the current V6.6 fifth-screen work.
