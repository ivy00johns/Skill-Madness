---
name: website-walkthrough-video
version: 1.1.0
description: |
  Generate a smooth scrolling walkthrough video of an entire website — capture
  every page full-length at desktop and mobile widths, then render an mp4 that
  pans down each page like a real person scrolling, stitched into one continuous
  tour. Use this whenever the user wants a video tour, demo reel, screen-recording,
  walkthrough, "show me the site as a video", a marketing/launch clip of their
  pages, a before/after of a redesign, or a desktop + mobile walkthrough mp4 — even
  if they don't say the word "video" but describe wanting to show the whole site
  scrolling. Triggers on "walkthrough video", "video tour of the site", "record the
  site", "demo video of all the pages", "scrolling screen recording", "make a reel
  of the site", "capture the whole site as a video", "smooth scroll-through". Also
  reach for it after a build or redesign wraps. Prefer this over hand-driving
  the Playwright MCP
  screenshot-by-screenshot — the bundled scripts do the capture and the smooth pan
  deterministically.
compatibility: Claude Code; requires ffmpeg + Node.js + Playwright (Chromium)
requires_claude_code: true
requires_agent_teams: false
min_plan: starter
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
owns:
  directories: []
  patterns: []
---

# Website Walkthrough Video

Turn a running website into a polished, smooth scrolling walkthrough video — one
continuous mp4 per device (desktop + mobile) that pans down each page in turn, the
way a person would scroll through it, with a small `// PAGE | MODE` label in the
corner.

## What it produces

For a site with N routes you get `walkthrough-desktop.mp4` and
`walkthrough-mobile.mp4` in your output dir. Each is N clips concatenated: per page,
a 1-second hold at the top, a smooth linear scroll to the bottom, a 1-second hold,
then on to the next page. Pages that fit in one viewport just hold for a few seconds.

## How it works (two stages)

1. **Capture** (`scripts/capture.mjs`, Playwright): for each device width and each
   route, set the viewport, navigate, scroll the whole page once so lazy images and
   on-scroll animations fire, return to top, and take a **full-page** screenshot
   (tall — the entire page, not just the fold). It also samples the page background
   color so the video never flashes black. Writes the PNGs plus a `manifest.json`.

2. **Render** (`scripts/build.mjs`, ffmpeg): for each screenshot, build a clip that
   overlays the tall image on a viewport-sized window and animates its vertical
   position from top to bottom — that pan *is* the simulated scroll. Then concatenate
   the clips into one video per device. The smoothness comes from 60fps + CRF 18 +
   lanczos scaling + a pixel-floored pan offset (no sub-pixel shimmer on text).

`scripts/walkthrough.mjs` runs both stages from one config file.

## Prerequisites

- **ffmpeg / ffprobe** on PATH (`ffmpeg -version`). On macOS: `brew install ffmpeg`.
- **Node.js** (any recent version).
- **Playwright + Chromium**. Install the npm package once inside the skill:
  ```bash
  cd <this-skill>/scripts && npm install
  ```
  Chromium is often already cached from other Playwright use; if capture complains
  about a missing browser, run `npx playwright install chromium`.

## Workflow

Follow these steps. The only real thinking is step 2 — getting the route list right.

### 1. Make sure the site is running and reachable

You need a live URL (local dev server, Docker container, or a public URL). Confirm
it responds, e.g. `curl -sI http://localhost:8080 | head -1`. Note the base URL.

### 2. Discover the routes and write a config

The config is the whole interface. Minimal version — just the base URL, where to put
output, and the ordered list of pages:

```json
{
  "title": "Sovereign Sampson",
  "baseUrl": "http://localhost:8080",
  "outDir": "./walkthrough",
  "routes": [
    { "path": "/", "label": "Home" },
    { "path": "/about/", "label": "About" },
    { "path": "/dispatches/", "label": "Dispatches" },
    { "path": "/contact/", "label": "Contact" }
  ]
}
```

To find the routes, in order of preference: ask the user if they have a page list;
read the site's nav/menu (fetch the homepage and pull the primary nav links); check a
`sitemap.xml`; or look at the route definitions in the codebase. Put them in the order
you want them to appear in the tour (usually nav order, home first). `label` is what
shows on screen — keep it short. `slug` is optional (derived from the path).

`outDir` is resolved relative to the config file. A path the project already
gitignores is a good choice (videos are large and regenerable).

See `assets/example-site.json` for a starting point. The full set of overridable
fields (device widths, pan speed, fps, fonts, custom modes) is documented in
`references/tuning.md` — you rarely need them for a first pass.

### 3. Run it

```bash
cd <this-skill>/scripts
node walkthrough.mjs --config /abs/path/to/site.json
```

Capture takes a few seconds per page per device; rendering is fast. Output lands in
`outDir` as `walkthrough-desktop.mp4` and `walkthrough-mobile.mp4`, alongside the
screenshots and `manifest.json`.

`--base-url <url>` and `--out-dir <dir>` override the config at the command line — handy
for pointing the same route list at local/staging/prod, or for a project wrapper script
that reads the base URL from its own env (e.g. a repo's `.env`) and supplies an absolute
output path. With `--base-url` set, the config file can omit `baseUrl`.

### 4. Review the result

**Actually watch the videos** (or open them for the user) before declaring success —
smoothness and framing are visual judgments a file size can't confirm. Check: does
each page scroll smoothly end to end, is text legible, are the holds long enough to
read, is anything cut off, do any pages 404 or render half-loaded?

### 5. Iterate fast with `--skip-capture`

Tuning the motion doesn't require re-screenshotting. Edit `speed` / `maxPan` /
`fontSize` in the generated `manifest.json` (or in the config and re-capture), then:

```bash
node walkthrough.mjs --config /abs/path/to/site.json --skip-capture
```

This re-renders from the existing PNGs in seconds. Common adjustments:

| Symptom | Fix |
|---|---|
| Scroll feels too fast | Lower `speed` (e.g. desktop 200 → 130) |
| Long pages drag on | Lower `maxPan` (caps the longest clip) |
| Label too small/large | Adjust `fontSize` per mode |
| Black bars on short pages | Set `bg` to the page color, e.g. `"0xFFFFFF"` |
| A page came out blank/half-loaded | Bump `timeout`, or that route needs auth/data |

Everything tunable, plus the device-mode schema and ffmpeg internals, is in
`references/tuning.md`.

## Notes

- **Full-page screenshots with sticky/fixed headers** can repeat the header down the
  page in some sites. If you see that, see `references/tuning.md` for the CSS-injection
  knob to neutralize sticky positioning before capture.
- **Auth-gated pages**: capture runs a fresh browser context with no login. For pages
  behind auth you'll need to extend `capture.mjs` to set cookies/storage state — out of
  scope for the default flow; capture the public pages and note the gap to the user.
- **Output is large.** mp4s and full-page PNGs are big and regenerable — keep `outDir`
  gitignored.
