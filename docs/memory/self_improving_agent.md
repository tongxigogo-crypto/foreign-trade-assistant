# Self Improving Agent Memory

This file stores durable learnings for this worktree only. It is intentionally compressed: keep rules that should affect future work, not a full run log.

## Persistent Rules

- Record reusable lessons after substantial runs without waiting for the user to ask.
- Prefer stable project rules, corrected assumptions, and repeated failure patterns over chronological detail.
- Keep the orchestrator responsible for end-to-end decisions; use specialist sub-agents only when work naturally splits into independent strategy, content, SEO, UI, implementation, QA, release, or analytics tracks.
- Apply `karpathy-style-engineering` globally: restate the target, choose the smallest valid change, avoid speculative refactors, and verify before claiming completion.
- Do not release, deploy, or write under `site_ops/output/` without explicit user confirmation.

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
- Use one shared outer shell width for major mid-page sections; keep the hero laptop intentionally staged inside it.
- Pet-products gallery belongs after the Pet IP section and should feel like an editorial/brand content rail, not a normal product grid.
- Gallery behavior: hidden-scrollbar horizontal rail, gentle auto-drift, pause on hover/drag, pointer dragging supported.
- Early-stage pet product cards can be placeholders, but they must be honest: use `coming_soon` or template-preview states instead of fake finished detail links.
- Short Chinese display headings may work better without pretext when pretext harms centered single-line typography.

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
- `status=live` does not automatically mean the card should navigate; `entry_mode` controls whether it opens the shared template.
- A single `pet-product-template.html` is the correct first detail-page scaffold before generating many product pages.
- The template should remain CMS-driven: hero image/card, eyebrow, title, intro, CTA, specs, sections, care notes, and SEO metadata.
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
  - returns `email_placeholder`
  - does not send email until deployment credentials are configured
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
