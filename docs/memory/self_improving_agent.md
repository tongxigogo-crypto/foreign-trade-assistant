# Self Improving Agent Memory

This file stores durable learnings for this worktree only. It is intentionally compressed: keep rules that should affect future work, not a full run log.

## Persistent Rules

- Record reusable lessons after substantial runs without waiting for the user to ask.
- Prefer stable project rules, corrected assumptions, and repeated failure patterns over chronological detail.
- Keep the orchestrator responsible for end-to-end decisions; use specialist sub-agents only when work naturally splits into independent strategy, content, SEO, UI, implementation, QA, release, or analytics tracks.
- Apply `karpathy-style-engineering` globally: restate the target, choose the smallest valid change, avoid speculative refactors, and verify before claiming completion.
- Do not release, deploy, or write under `site_ops/output/` without explicit user confirmation.
- For local Remotion projects on this Windows machine, `render`/`still` may hang unless the CLI is passed `--browser-executable="C:\Program Files\Google\Chrome\Application\chrome.exe"`; `@remotion/zod-types@4.0.456` should be paired with `zod@4.3.6` to avoid npm peer-resolution loops.
- For isolated static previews served through `python -m http.server`, cache-bust linked CSS and JS when iterating (`?v=...`) and verify the loaded `href/src` in the browser before diagnosing stale visual behavior as a code regression.
- For pointer-drag UI such as Douzi/AI Core, synthetic `dispatchEvent()` may not exercise pointer capture correctly; use real Playwright mouse movement to verify draggable behavior.
- When turning V6.6 experiments into left-nav single-viewport previews, verify at the user's apparent browser width as well as standard desktop; fixed-size center compositions can leave large white areas on wide Chrome windows unless the root shell is fixed to the viewport and the stage owns the full remaining canvas.
- For V6.6 left-navigation rebuilds, preserve the original `#hero-section` contract instead of approximating it: `min-h-[350vh]`, inner `sticky top-0 h-screen w-full`, `#impact-1..4`, and the GSAP ScrollTrigger timeline must remain on window scroll. Do not move scrolling into an internal container unless ScrollTrigger is reconfigured with that scroller.
- For user-requested V6.6 visual experiments based on `C:\Users\Administrator\Desktop\preson`, prefer an isolated output folder under `E:\网页测试\...` first. Preserve the source V6.6 files, copy only needed assets, and implement first-screen cockpit/app prototypes with static HTML/CSS/JS unless video rendering or true timeline export is explicitly required.

## Current Source Of Truth

- The active external homepage source is `C:\Users\Administrator\Desktop\preson\indexV6.6_refined.html`.
- The English independent-site sibling is `C:\Users\Administrator\Desktop\preson\indexV6.6_refined_en.html`.
- The shared runtime is `C:\Users\Administrator\Desktop\preson\bilingual.js`.
- The local backend/admin source lives in `site_backend/`.
- Do not silently substitute `website_from_playground/` as the publish target when the user is reviewing the external V6.6 files.
- Preserve original Gemini/prototype drafts; write major iterations into refined siblings unless the user explicitly asks to overwrite.

## Product And Brand Direction

- The site is Tong Studio / Tong工作室, centered on real work: Trade Assistant, pet product trade, pet IP, and future mini-program/website development services.
- Avoid reverting to generic AI SaaS marketing. The page should stay bright, soft-tech, glassy, product-narrative, and desktop-first.
- Xiao Q and Douzi are brand memory assets, not decorative mascots. Use real local images when available; do not replace them with letter placeholders.
- Douzi Core is a floating mascot-shaped AI core. Keep the elliptical obstacle model aligned with the real mascot silhouette.
- The Chinese and English experiences should be coordinated but not identical: English is for independent-site/Google SEO; the future Chinese version should be WeChat-friendly and conversion-oriented.

## External V6.6 Homepage Rules

- Keep the existing GSAP/scrollytelling shell and pretext interaction unless the user explicitly asks for a structural rewrite.
- The first screen should feel like a real Trade Assistant workspace, not a generic concept dashboard.
- The first-screen laptop intro now uses a fullscreen macOS-style software window. Preserve the pain cards and scrollytelling transition; edit the inner window copy through `hero_summary_title`, `hero_intro`, and `hero_subtitle`.
- Keep the first-screen hero title on one line and attached to `use-pretext` so Douzi Core movement continues to affect the text layout.
- The laptop/workspace panel should show credible operational details: customer context, inquiry input, quote/task suggestions, local-first and multi-model compatibility.
- The user explicitly authorized proactive use of sub-agents and design plugins/skills when useful; do not wait for a reminder on future design, copy, SEO, backend, or QA splits.
- Use one shared outer shell width for major mid-page sections; keep the hero laptop intentionally staged inside it.
- Pet-products gallery belongs after the Pet IP section and should feel like an editorial/brand content rail, not a normal product grid.
- Gallery behavior: hidden-scrollbar horizontal rail, gentle auto-drift, pause on hover/drag, pointer dragging supported.
- Early-stage pet product cards can be placeholders, but they must be honest: use `coming_soon` or template-preview states instead of fake finished detail links.
- Short Chinese display headings may work better without pretext when pretext harms centered single-line typography.

## V6.7 Concept Direction

- The V6.7 concept is an isolated external prototype at `C:\Users\Administrator\Desktop\preson\indexV6.7_concept.html`, not a direct V6.6 replacement.
- First concept pass uses HyperFrames as a design method only: composition-like scenes, timeline thinking, and video-style transitions implemented with normal HTML/CSS/GSAP/ScrollTrigger.
- Do not build the actual HyperFrames project until after the website concept is reviewed, approved, and migrated back into V6.6.
- The approved first-pass style is v0 / AI product launch: light canvas, soft glass UI, blue/violet glow, product workspace cards, camera push/pull, and UI regrouping.
- First pass is desktop-first and uses abstract UI placeholders; real app screenshots, Xiao Q/Douzi assets, and pet product poster assets are connected later after motion direction approval.
- Boot should be a very short brand flash, about 0.8 to 1.2 seconds, not a long system loading sequence.
- V6.7-to-V6.6 migration should enhance the existing V6.6 files with a launch layer instead of replacing them: preserve `#global-obstacle`, `data-ai-assistant-mount="douzi-core"`, `.use-pretext`, and `GlobalPretextEngine`.
- Keep Chinese and English V6.6 pages synchronized for the launch layer (`data-v67-launch`, boot, progress, cursor, scene dots, and `initV67LaunchExperience`) so bilingual navigation does not switch into an older interaction model.
- If `bilingual.js` has mojibake or syntax damage, fix it before visual migration because a broken runtime can prevent language copy, gallery link handling, contact form binding, and `window.TongAICore` from initializing.

## Backend And CMS Rules

- The smallest reliable backend shape is Python stdlib WSGI: serve static external files, `/admin`, `/api/content`, asset upload, preview, and placeholder public APIs without adding unnecessary framework dependencies.
- Preview/publish must target the real external V6.6 files and their `content/site-content.json`, not a disconnected repo demo.
- Admin preview should show draft-vs-saved state, image reachability, and open preview only after warning on draft changes or asset risks.
- When local preview seems unchanged, check for stale `site_backend.server` processes before assuming the code failed.
- Normalize Windows/Chinese-path static serving: recover `PATH_INFO` with `latin-1 -> utf-8` where needed and unquote before resolving files.
- Keep `site_backend/v66_adapter.py` aligned with user-facing homepage/card/template changes, or the next CMS save can regress visible copy and links.

## Bilingual CMS Contract

- Store homepage gallery cards as `pet_products_gallery.zh.cards` and `pet_products_gallery.en.cards`.
- Mirror legacy `pet_products_gallery.cards` from Chinese only for backward compatibility.
- Frontend runtime should prefer localized gallery cards; only Chinese may fall back to legacy `cards`, otherwise English can inherit Chinese placeholder copy.
- Admin preview targets must be concrete:
  - Chinese homepage: `/?preview=1`
  - English homepage: `/indexV6.6_refined_en.html?preview=1`
  - Template page: `/pet-product-template.html?preview=1`
- Use `localStorage.site_content_preview` for draft-only preview; it must not overwrite saved content.

## SEO And Launch Readiness

- For the current static architecture, prioritize direct semantic improvements over framework migration: title, description, canonical, JSON-LD, precise alt text, aria labels, resource hints, and sitemap/robots.
- Keep above-the-fold Douzi and app images high priority; lazy-load below-the-fold IP/gallery assets.
- English launch polish should target real visible DOM nodes and adapter code; do not rely on broad string replacement against historical mojibake.
- Verify UTF-8 and mojibake from actual source bytes or decoded HTTP responses. PowerShell display can be misleading.
- External-file regressions should use stable structural markers or English strings where possible.

## Pet Product Content Model

- `pet_products_gallery` cards currently need: `id`, `image`, `cover_label`, `cover_title`, `title`, `summary`, `tag`, `status`, and `entry_mode`.
- Pet product homepage assets should live under the external site asset directory, currently `C:\Users\Administrator\Desktop\preson\pet-product-assets\`, with stable relative URLs such as `./pet-product-assets/mother-keepsake-necklace.png`.
- When changing homepage gallery cards, update all three layers together: static V6.6 HTML fallback, `bilingual.js`, and `content/site-content.json` plus `site_backend/v66_adapter.py` defaults, otherwise CMS preview/save can regress the visible homepage.
- `status=live` does not automatically mean the card should navigate; `entry_mode` controls whether it opens the shared template.
- A single `pet-product-template.html` is the correct first detail-page scaffold before generating many product pages.
- The template should remain CMS-driven: hero image/card, eyebrow, title, intro, CTA, specs, sections, care notes, and SEO metadata.
- V6.7 pet poster detail pages should work as static hash routes first: `#mother-keepsake` and `#pet-keepsake` must render complete Chinese fallback content even when `/api/content` is unavailable.
- Homepage pet poster navigation belongs on each live card's image and "View poster" link. Do not use the lower "Open template preview" note as the primary poster route.
- If the pet gallery removes visible CTA buttons, keep `data-poster-href` on the image cover and a rail click handler that routes through `window.location.href`; the auto-scrolling rail can otherwise make plain anchors unreliable.
- For the V6.6 pet gallery card body, "only keep the main title" means remove the per-card summary paragraph and bottom CTA/tag row; the card should show image plus `h3` only.
- Keep `site_backend/v66_adapter.py` and preview runtime aligned with that title-only gallery shape; backend `apply_content()` must not regenerate footer links, status pills, tags, or card summaries after a CMS save.
- Keep a stable `data-poster-template="v67"` marker and `initPosterExperience()` in the shared poster page so tests can distinguish the approved V6.7 poster experience from the earlier generic scaffold.
- The homepage top-right CTA is now a download entry, not a demo booking mailto. Keep `data-i18n="navCta"` text as `Download` / `下载` and route it to `./download.html`; the download page introduces InVault / 外贸助理 as a local-first private AI business advisor until installer details are ready.
- Keep `robots.txt` and `sitemap.xml` synchronized when content/template publishing behavior changes.

## Contact And AI Core APIs

- Douzi AI Core is currently a reserved assistant mount, not a live chat product.
- Frontend contract: `data-ai-assistant-mount="douzi-core"` and `window.TongAICore.context()` / `window.TongAICore.send()`.
- Public AI placeholders:
  - `GET /api/ai-context`
  - `POST /api/ai-core/message`
- The AI message endpoint must not call external models until a model adapter is explicitly added.
- Contact intent slugs are stable:
  - `website-development`
  - `mini-program`
  - `product-information`
  - `ip-collaboration`
- Current contact endpoint is placeholder-only:
  - `POST /api/contact`
  - validates name/contact/intent/message
  - uses a honeypot field for simple spam filtering
  - persists accepted homepage project feeds into `content/contact-submissions.jsonl`
  - returns `feed_saved`
  - does not send email until deployment credentials are configured
- Admin can review homepage project feeds through authenticated `GET /admin/api/contact-submissions` and the right-side inspector module.
- Email target is `tongxigogo@gmail.com`.
- WeChat QR should use a stable asset path: `小Q和豆子/wechat-qr-tong1390.jpg`.

## Deployment Direction

- Recommended free/low-cost shape for this project: Cloudflare Pages + Cloudflare Workers + Resend.
- GitHub Pages is not enough for real form submission because it cannot run `/api/contact`.
- Deployment email sending should use environment variables, not committed secrets:
  - `RESEND_API_KEY`
  - `CONTACT_TO_EMAIL=tongxigogo@gmail.com`
  - `CONTACT_FROM_EMAIL=<verified sender>`
- Add stronger spam protection later with Cloudflare Turnstile if submissions become public-facing and noisy.

## Retired Or Deprioritized Directions

- Do not revive the heavy game-plaza homepage direction unless the user explicitly asks; current approved direction is V6.6 scrollytelling/product narrative.
- Do not migrate to Next.js just for SEO before content volume and deployment needs justify it.
- Do not build many pet product detail pages before the shared template and content workflow are stable.
- Do not overbuild the admin UI into a full CMS platform before final homepage copy, deployment, and email delivery are settled.

## V6.6/V6.7 Release Review Learnings

- For external static pages under `C:\Users\Administrator\Desktop\preson`, production checks must include browser-rendered mobile review, not only file scans, because runtime language updates can override static HTML.
- Keep fifth-screen pet gallery card titles as normal `h3` text, not `use-pretext`, so the global Pretext character engine stays focused on large narrative headings and cannot corrupt compact card titles.
- Public homepage assets should use ASCII deploy paths such as `characters/douzi-thanks.png`; keep original Chinese asset folders untouched as source material, but do not regenerate publish HTML with Chinese paths.
- Treat `InVault Trade Assistant` / `外贸助理` and `v0.1.1 Beta` as the current public naming/version pattern unless the user changes the release name.
- When adopting an externally repaired single-file prototype such as `geminiV7.1.html`, copy it into a fresh output folder and migrate its asset directories first, then replace placeholder cards with real assets before QA. Fullscreen checks must measure both `main` and the pinned ScrollTrigger container: fixed left-navigation layouts should use `calc(100vw - var(--left-nav-width))`, not `calc(100% - ...)`, because ScrollTrigger pin wrappers can otherwise produce horizontal overflow.
- Configurable prototype parameters should be connected to runtime behavior, not only declared. For the Gemini V7.1 rebuild, `window.V66_CONFIG.animation` drives boot delay, hero impact scale, scroll length, APP demo delay, and gallery drag speed.
- For pinned single-viewport GSAP prototypes, left-nav clicks should drive the GSAP timeline to a settled scene time rather than relying only on programmatic `window.scrollTo()`. Some browser/ScrollTrigger states can update active navigation without actually scrolling, leaving a half-transition scene. Verify by checking the target section `getBoundingClientRect().y === 0` after each nav click in the shortest supported desktop viewport.
- When a repaired prototype simplifies original copy, compare against both `indexV6.6_refined.html` and `indexV6.6_refined_en.html` before accepting it. Preserve the original V6.6 content contracts: feature explanation copy, IP character descriptions, 4-card pet product rail, product note, and full contact form fields.
- The practical lesson from `forrestchang/andrej-karpathy-skills` is to make implementation changes assumption-light, minimal, and verification-driven. Apply that here by fixing only the failing behavior and proving it with concrete browser measurements/screenshots before summarizing.
