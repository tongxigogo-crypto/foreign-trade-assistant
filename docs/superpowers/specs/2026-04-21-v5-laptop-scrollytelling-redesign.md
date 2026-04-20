# V5 Laptop Scrollytelling Redesign

Date: 2026-04-21
Status: Draft for review
Scope: Visual reset and scene-content rewrite for the existing `indexV5.html` architecture

## Goal

Keep the overall V5 page structure intact while changing:

- first-screen narrative center
- color system
- motion logic
- per-scene content emphasis
- technology/product feel

The homepage should remain a desktop-first scrollytelling site, but the first screen should no longer be "Q and Douzi getting hit." The new center is a real-feeling laptop. Pain points hit the laptop screen, then convert into the Trade Assistant UI.

## Non-Goals

- Do not rebuild the page into a completely new site structure.
- Do not move Pet IP into the first-screen core narrative.
- Do not use dark, oppressive cyberpunk styling.
- Do not convert the whole page into one full-screen video player.

## Constraints

- Preserve the existing V5 multi-screen architecture.
- Keep the site bright, clean, and design-led.
- Use scrollytelling for page progression.
- Use HyperFrames only for the most valuable screen-in-screen system animations, not for the entire page.
- Keep later scenes for Pet IP showcase and contact closing.
- Final conversion focus remains the Trade Assistant APP.

## Visual Direction

### Core Look

The visual style should shift from warm editorial storytelling to bright product-tech presentation:

- soft light gradient backgrounds
- airy glassmorphism surfaces
- high-fidelity product rendering feel
- clean whitespace
- restrained, precise motion

The mood reference is not dark cyber-tech. It is premium, bright, slightly futuristic, and product-polished.

### Color System

Recommended palette:

- base background: warm white / fog white
- gradient wash: pale violet, soft sky blue, muted mint, faint blush
- product accent: clean electric blue
- support accent: very controlled lavender and coral
- text: dark graphite, not pure black

Avoid:

- deep black page backgrounds
- high-saturation neon overload
- heavy glitch effects
- dense particle noise

### Material Language

- laptop hardware should feel real, not conceptual sci-fi
- screen should feel like a product surface, not a floating card
- interface layers can use glass, blur, inner glow, subtle reflections
- shadows should be soft and wide, not harsh

## Narrative Structure

## Scene 1: Pressure Into System

This is the major redesign.

Composition:

- a real-looking laptop sits front-facing
- the screen occupies about two-thirds of the first screen
- the lower part reveals roughly half of the keyboard
- the composition should feel like the user is facing a real computer

Content:

- the main headline appears directly inside the laptop screen
- external pain-point cards orbit or align from outside the screen area
- on scroll, the pain points accelerate and hit the screen
- the screen reacts like a system under pressure
- the screen then converts into the Trade Assistant UI

Motion logic:

- pain cards must follow believable trajectories
- impacts must visually register on the laptop, not on mascots
- system response should feel mechanical:
  - flash
  - scan
  - jitter
  - panel activation
  - UI lock-in

The first screen should be simple, high-design, and tech-forward.

## Scene 2: Solution Appears

After the first-screen conversion, the Trade Assistant interface becomes the main subject.

Purpose:

- show that the system turns chaos into order
- move from emotional problem framing into product understanding

Visual treatment:

- screen UI becomes stable and readable
- supporting labels and module callouts may appear around the laptop
- HyperFrames is suitable here for screen-internal UI transitions

## Scene 3: Functional Expansion

This screen explains product capability.

Content focus:

- customer management
- quotes
- emails
- tasks
- scattered records becoming structured

Motion:

- modules should expand like system panels
- cards should dock, assemble, or snap into place
- motion should feel like a product system, not decorative floating blocks

## Scene 4: Pet IP Showcase

Pet IP stays in the site, but no longer drives the first-screen crisis narrative.

Purpose:

- brand memory
- warmth and distinctiveness
- visual identity beyond a pure SaaS/product page

Visual treatment:

- Q and Douzi should be presented in a style consistent with the upgraded site
- the screen can be lighter and more expressive, but should still match the same color/material system

## Scene 5: Contact And Product Closing

The ending stays as contact + conversion, but the center of gravity returns to the Trade Assistant APP.

Purpose:

- summarize value
- present contact action
- connect brand trust back to product use

This should not end as a generic portfolio close. It should end as a product-oriented invitation.

## Motion Architecture

### Scrollytelling Layer

The page itself should continue handling:

- scene progression
- typography
- pain-point cards
- scroll rhythm
- layout transitions

Recommended tools:

- GSAP
- ScrollTrigger

### HyperFrames Layer

HyperFrames should be used selectively for:

- laptop screen boot-up transitions
- UI state transformation
- product panel animation
- screen-contained explanatory sequences

HyperFrames should not carry the entire page. It should produce precise, reusable motion assets for the laptop screen and other contained product moments.

### Mechanistic Motion Principle

All key motions should feel intentional and system-driven.

Good examples:

- snap
- lock
- route
- impact
- initialize
- scan
- assemble

Bad examples:

- random drifting
- over-decorative floating
- meaningless wobble
- cinematic motion with no interface logic

## First-Screen Interaction Spec

### Layout

- screen headline lives inside laptop screen
- supporting microcopy may stay outside the laptop if needed, but should remain minimal
- keyboard remains partially visible to anchor realism

### Impact Sequence

Suggested beat order:

1. calm product stage
2. screen headline visible
3. first pain cards appear
4. cards lock trajectory
5. impacts hit the laptop screen
6. impact feedback occurs
7. screen transitions into Trade Assistant UI

### Success Criteria

The user should understand in under 10 seconds:

- this product is for solving messy trade workflows
- the problem is real and concrete
- the laptop/system is the object that processes the chaos
- the result is a working software interface

## Design Risks

### Risk 1: Too Much Tech Styling

If the page leans too hard into cyber visuals, it will lose clarity and become visually noisy.

Mitigation:

- keep the background bright
- use glow sparingly
- let composition carry the premium feel

### Risk 2: Pain Cards Feel Unrelated To Laptop

If trajectories are vague, the first-screen logic breaks.

Mitigation:

- define explicit impact vectors
- align card movement with laptop screen boundaries
- time card collisions against screen response states

### Risk 3: HyperFrames Overuse

If too much is turned into video, maintainability and iteration speed will collapse.

Mitigation:

- keep HyperFrames scoped to screen-contained motion assets
- keep the webpage responsible for structure and copy

## Implementation Boundary

The implementation should start with:

1. redesign Scene 1 around the laptop
2. update the global color/material system
3. align Scene 2 and Scene 3 to the new product-tech language
4. restyle Scene 4 and Scene 5 to match the same visual system

Do not begin by polishing every minor detail. The first pass should establish the new narrative and system style.

## Acceptance Check

This redesign is correct if:

- V5 structure is still recognizable
- Scene 1 is laptop-centered
- the title is inside the laptop screen
- pain cards hit the laptop, not mascots
- the laptop screen converts into Trade Assistant UI
- the page feels bright, premium, and technological without becoming oppressive
- Pet IP remains present later in the story
- the closing screen still serves Trade Assistant APP conversion
