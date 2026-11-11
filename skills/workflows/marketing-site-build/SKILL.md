---
name: marketing-site-build
version: 1.1.0
description: >-
  Build a one-page static marketing site from a design profile plus a graphics
  inventory: lit text, masthead, one scroll-driven moment, static sections,
  suite and closing, as plain HTML/CSS/JS ready for Vercel; checks it at
  1440, 1024 and 390 with Playwright (axe AA, frame timing) and deploys a preview. Use for "build the site
  from the profile", "ship the landing page to Vercel".
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: ["public/index.html", "public/styles.css", "public/main.js", "public/vercel.json"]
  shared_read: ["docs/design-profile.md", "graphics/inventory.json"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
composes_with:
  [
    "lantern-design-profile",
    "site-character-art",
    "frontend-design:frontend-design",
    "playwright",
    "ux-review",
    "deployment-checklist",
  ]
spawned_by: []
---

# Marketing site build

Turn `docs/design-profile.md` (from `lantern-design-profile`) and `graphics/inventory.json` (from
`site-character-art`) into a deployed one-page site. The output is deliberately plain: one
`index.html`, one stylesheet, one small script, self-hosted font, webp art, no framework and no
build step, so the page deploys as static files anywhere and stays readable in a year. The design
decisions are already made in the profile; this skill's job is fidelity to them, then proof in a
real browser at two widths, then a preview URL.

**Announce at start:** "Using marketing-site-build to build [site] from its design profile."

## Instructions

1. **Load the inputs.** Read the profile whole and the inventory's promoted entries (file paths
   under `public/art/`, widths, alt text). Missing either: stop and run the owning skill first; a
   site built without them drifts back to a generic dark landing page within an hour.
2. **Scaffold** from `references/site-template.md`: `public/index.html`, `public/styles.css`,
   `public/main.js`, `public/fonts/` (Bricolage Grotesque variable woff2, pinned from
   `@fontsource-variable/bricolage-grotesque`, a release at least seven days old), `public/art/`.
   Paste the profile's token block into `:root` unchanged.
3. **Write the sections in the profile's order**: masthead, hero, the moment (one sticky section
   with four beats), the static sections, the suite, the closing, a one-line colophon. Every
   heading and lede carries class `lit`. Copy comes from the profile verbatim; the build does not
   rewrite copy, and never fills a gap with a sentence from a sibling or reference site. If the
   product has no waitlist endpoint, use a CTA link to the product shots instead of a dead field.
4. **Place the art the family's way.** Each image: `<img>` with `width`/`height` attributes,
   `loading="lazy"` below the fold, alt from the inventory, class `art`, and the CSS from the
   template (`mix-blend-mode: screen` + radial `mask-image`) so the near-black JPEG background
   vanishes on the black page. The hero image is eager and `fetchpriority="high"`.
5. **Light the page, smoothly.** Give each section's art its own `[data-light]` over the light in
   that image, and tag each `.lit` element with the light it belongs to (`data-near`). Text lit by
   a light that does not move gets `--lx/--ly` once, on load and resize, never on scroll. Only the
   moment's copy is relit per frame. The scroll path does **no layout reads**: measure positions on
   load/resize, then each frame computes from `scrollY` and writes only `transform`, `opacity` and
   the few moving `--lx/--ly`. Ease the character toward the scroll target with a
   frame-rate-independent lerp (`k = 1 - (1 - 0.16) ** (dt / 16.67)`) so wheel steps glide.
   Change discrete states (a place turning lit) by class at thresholds and let CSS transitions run.
   Clip horizontal overflow on `main`, not on `body` (body's `overflow-x` propagates to the
   viewport and stops nothing). Reduced motion: no intro, no pinning, everything shown static.
   `references/site-template.md` has the shape; the fathom-site build (2026-11-08) is a worked
   example.
6. **Run it locally** on a free port (check first: `lsof -iTCP:<port> -sTCP:LISTEN`; another
   site's server may already hold 4173, and a check against it passes for the wrong page). Check
   with Playwright at 1440×900, 1024×768 and 390×844: screenshots into `docs/review/` (scroll
   frames rather than one full-page shot, since a full-page capture stretches `svh` on the sticky
   section), zero console errors, every image loaded after scrolling (`naturalWidth > 0`), no
   horizontal overflow at any width, axe with `wcag2aa`/`wcag21aa` tags and zero violations
   (contrast on gradient-clipped text comes back "incomplete"; the amber floor `#a8875c` is about
   6:1 on black, so it passes by construction), frame timing while wheel-scrolling the moment
   (p95 ≤ 17ms at 60Hz), and a second pass with `reducedMotion: "reduce"`. Look at every
   screenshot; compare the *effect level* with the sibling site, never its content. Fix, re-shoot,
   repeat.
7. **Deploy a preview** to Vercel: `vercel.json` with `{"cleanUrls": true}` and the headers in the
   template, then `vercel deploy` (CLI, from `public/`, `--scope` the team) or the Vercel MCP
   `create_deployment`, `target` omitted so it is a preview. Check `vercel whoami` first: without
   a CLI login, the MCP has to take every binary as base64 in the call, which is slow and costly for
   more than a few hundred KB, so ask the person for a one-time `vercel login` instead. If the MCP
   answers with a team-access link (`authorize_team_access`), give the person the link and wait.
   Team-scoped hostnames may sit behind Deployment Protection; verify the URL from outside
   (plain `curl`, no cookies) and report which hostname is public. Report the preview URL and the screenshots. Never deploy to
   production or attach a domain unless the person asks in that message.

## Rules the family does not bend

- **No panels, no cards, no borders** except the one masthead hairline and the field's border.
  The page is black; text and art sit on it directly.
- **One accent.** Amber scale for all text and controls; the character's colour appears only in
  the art.
- **One sticky section**, four beats; everything else static. Fifteen keyframe animations is the
  failure mode this family exists to avoid.
- **One font**, variable, self-hosted, `font-display: swap`, `font-optical-sizing: auto`.
- **Scroll-driven motion only**, with `prefers-reduced-motion` honoured.
- **Honest status line** under every field: "In development." / "In private testing."

## Examples

### Example 1: profile to preview

**User says:** "Build the Andon site from docs/design-profile.md and deploy a preview."

**Actions:**

1. Read the profile and `graphics/inventory.json` (seven promoted scenes).
2. Scaffold from the template; paste tokens; write hero → moment ("a card's run", four beats) →
   three static sections (board, machines, cord) → suite → closing.
3. Serve locally; Playwright at 1440, 1024 and 390 plus reduced motion; fix the 390 hero order.
4. `vercel deploy`; report the URL and `docs/review/*.png`.

**Result:** a preview URL, screenshots at both widths, zero console errors.

### Example 2: a section added later

**User says:** "Add a self-host section with the install command to the site."

**Actions:**

1. Confirm the profile lists the section (add it there first if not: heading, one sentence, scene).
2. Add a static section in the template's 2-col shape; the command in a pill, the amber scale.
3. Re-shoot both widths; redeploy a preview.

**Result:** the section in the family's shape, not a new component style.

## Triggering test

- Must trigger: "build the marketing site from the design profile", "turn the profile and the
  inventory into a static site for Vercel", "deploy the landing page preview".
- Must NOT trigger: "write the design profile" (`lantern-design-profile`), "render the mascot"
  (`site-character-art`), "build the dashboard UI" (`frontend-agent` / `frontend-design`).

## Troubleshooting

### A dark rectangle shows around an image

**Cause:** the image is a JPEG on near-black and the `art` CSS was dropped, or the page behind it
is not `#000`.
**Solution:** restore `mix-blend-mode: screen` and the mask; keep the section background black.
If the rectangle is at the image edge, the glow reaches the edge: re-roll with `site-character-art`.

### Lit text renders flat amber

**Cause:** `background-clip: text` needs the `-webkit-` prefix and `-webkit-text-fill-color:
transparent`; or `--lx/--ly` were never set so the gradient centre is `0 0`.
**Solution:** copy the `.lit` rule from the template; check `main.js` ran (no console errors).

### Horizontal scroll at 390

**Cause:** the hero's nowrap H1 or a fixed-width stage.
**Solution:** the mobile media query sets `white-space: normal` on headings and `width: min(90vw, 620px)`
on the stage; `body { overflow-x: clip }` is the backstop, not the fix.

### The preview is a 404

**Cause:** files were uploaded without `index.html` at the root, or `outputDirectory` points elsewhere.
**Solution:** deploy the `public/` folder as the root (or set `outputDirectory: "public"`).
