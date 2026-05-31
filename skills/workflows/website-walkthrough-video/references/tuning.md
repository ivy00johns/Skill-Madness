# Tuning & internals

Read this when the default walkthrough needs adjusting, when you want non-standard
device modes, or when something rendered wrong and you need to understand the pipeline.

## Table of contents
- [Config schema (full)](#config-schema-full)
- [Render modes](#render-modes)
- [The manifest](#the-manifest)
- [How the pan works (ffmpeg)](#how-the-pan-works-ffmpeg)
- [Timing model](#timing-model)
- [Smoothness levers](#smoothness-levers)
- [Troubleshooting](#troubleshooting)

## Config schema (full)

Only `baseUrl`, `outDir`, and `routes` are required. Everything else has a default.

```json
{
  "title": "My Site",
  "baseUrl": "http://localhost:8080",
  "outDir": "./walkthrough",
  "fps": 60,
  "timeout": 60000,
  "fontFile": "/System/Library/Fonts/Supplemental/Arial.ttf",
  "bg": "0x0B0B0C",
  "routes": [
    { "path": "/", "slug": "home", "label": "HOME" }
  ],
  "modes": [ /* see below; omit to use desktop + mobile defaults */ ]
}
```

- `fps` — output frame rate. 60 is smooth; 30 halves file size with visibly choppier pans.
- `timeout` — per-page navigation timeout (ms). Raise for slow/heavy pages.
- `fontFile` — path to a `.ttf`/`.otf` for the on-screen label. If the file doesn't
  exist at render time the label is simply omitted (video still renders). The default is
  a macOS system font; on Linux try `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`.
- `bg` — letterbox color shown only when a page is *shorter* than the window (no scroll).
  `0xRRGGBB`. Capture auto-detects the page's `<body>` background and writes it into the
  manifest per mode; set `bg` here only to force one.
- `routes[].slug` — optional; defaults to a slug derived from the path (`/` → `home`).
- `routes[].label` — optional; defaults to the slug uppercased. This is what's stamped
  on screen, so keep it short.

## Render modes

A "mode" is one device rendering (desktop, mobile, or anything you define). Omit `modes`
to get the two defaults below. Override by supplying a `modes` array — you can override
just a couple of fields of a default by reusing its `name`.

```json
"modes": [
  { "name": "desktop", "width": 1440, "winHeight": 810,  "outWidth": 1440,
    "deviceScaleFactor": 1, "isMobile": false, "fontSize": 24, "speed": 200, "maxPan": 11, "label": "DESKTOP" },
  { "name": "mobile",  "width": 390,  "winHeight": 844,  "outWidth": 780,
    "deviceScaleFactor": 1, "isMobile": true,  "fontSize": 30, "speed": 620, "maxPan": 16, "label": "MOBILE" }
]
```

Field meanings:

| Field | Meaning |
|---|---|
| `name` | Mode id; also the screenshot filename prefix (first letter) and `walkthrough-<name>.mp4` |
| `width` × `winHeight` | The **capture** viewport. `winHeight` becomes the height of the scrolling "window" in the video |
| `outWidth` | Video pixel width. Mobile is captured at 390 and rendered at 780 so phone-sized text stays crisp; the image is scaled to `outWidth` with lanczos |
| `deviceScaleFactor`, `isMobile` | Passed to the Playwright context. `isMobile: true` enables touch + mobile layout |
| `fontSize` | Label size for this mode (mobile is rendered larger, so it wants a bigger font) |
| `speed` | Pan rate in **output** px/sec. Higher = faster scroll. This is the main "feel" dial |
| `maxPan` | Hard cap (seconds) on a single page's scroll, so a very long page doesn't drag |
| `label` | Text after the `|` in the on-screen stamp |

The video's window height is computed as `winHeight × (outWidth / width)` — e.g. mobile
844 × (780/390) = 1688. So with the defaults, the desktop window is 1440×810 and the
mobile window is 780×1688, exactly a 2× phone viewport.

### Adding a tablet (example)
```json
{ "name": "tablet", "width": 834, "winHeight": 1112, "outWidth": 834,
  "deviceScaleFactor": 1, "isMobile": true, "fontSize": 26, "speed": 380, "maxPan": 14, "label": "TABLET" }
```

## The manifest

Capture writes `manifest.json` into `outDir`; build reads it. You can hand-edit it and
re-run with `--skip-capture` to re-render without re-screenshotting. Shape:

```json
{
  "title": "...", "baseUrl": "...", "fps": 60,
  "renders": [
    {
      "name": "desktop", "label": "DESKTOP",
      "outWidth": 1440, "outWinHeight": 810,
      "fontSize": 24, "speed": 200, "maxPan": 11,
      "bg": "0x0B0B0C", "fontFile": "/System/Library/Fonts/Supplemental/Arial.ttf",
      "clips": [ { "file": "d-01-home.png", "label": "HOME" }, ... ]
    }
  ]
}
```

Reorder, drop, or relabel `clips` freely; build renders them in array order.

## How the pan works (ffmpeg)

Per clip, two inputs are composited:

1. `color=<bg>:s=<outWidth>x<outWinHeight>` — a solid canvas the size of the window.
2. The full-page screenshot, scaled to `outWidth` with lanczos.

The screenshot is overlaid on the canvas with an animated y offset:

```
overlay=x=0:y='-floor((h-H)*clip((t-1.0)/<pd>,0,1))'
```

- `h` = scaled image height, `H` = window height, so `h-H` is the total scroll distance.
- `clip((t-1.0)/pd, 0, 1)` ramps 0→1 over the pan window `[1.0, 1.0+pd]` seconds, and is
  flat (0 before, 1 after) outside it — giving the hold/scroll/hold shape.
- `floor(...)` snaps the offset to whole pixels every frame. **This is what kills the
  shimmer** on text during the scroll; without it the image lands on sub-pixel positions
  and small text crawls.

A `drawtext` filter stamps the `// LABEL | MODE` chip, then `format=yuv420p` and `fps`
normalize the stream. Clips are concatenated with the concat demuxer (re-encoded so
per-clip timestamps can't conflict) and written with `+faststart` for web playback.

## Timing model

Constants live at the top of `build.mjs`:

- `HOLD_TOP = 1.0`, `HOLD_BOTTOM = 1.0` — still beats at each end of a scroll.
- `MIN_PAN = 2.5` — a page only slightly taller than the viewport still gets a gentle pan.
- `STATIC_HOLD = 3.0` — a page that fits the viewport (no scroll) just holds this long.
- `CRF = 18`, `PRESET = 'medium'` — quality/size tradeoff. CRF 18 is near-visually-lossless;
  raise toward 23 for smaller files, lower toward 16 for higher quality.

Per page: `pan_seconds = clamp(scroll_distance / speed, MIN_PAN, maxPan)` and the clip
length is `HOLD_TOP + pan_seconds + HOLD_BOTTOM`. So `speed` and `maxPan` together govern
both pace and total runtime.

## Smoothness levers

In rough order of impact:

1. **`fps`** — keep at 60.
2. **`speed`** — slower pans read as smoother and more deliberate. If motion feels jittery
   or rushed, lower `speed` before touching anything else.
3. **`CRF`** — lower = cleaner gradients/text (try 16–18).
4. The **floored pan** and **lanczos scale** are already on; don't remove them.

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| `Could not load 'playwright'` | `cd scripts && npm install`. If browser missing: `npx playwright install chromium` |
| `ffmpeg: command not found` | Install ffmpeg (`brew install ffmpeg`) and ensure it's on PATH |
| Page blank or half-rendered | Raise `timeout`; the page may need data/auth, or `networkidle` never settles (heavy polling/websockets) — capture still proceeds after a 15s fallback |
| Header repeats down the page | Full-page screenshots can duplicate `position: fixed`/`sticky` elements. Add a pre-screenshot CSS injection in `capture.mjs` (in the route loop, before `page.screenshot`): `await page.addStyleTag({ content: '*{position:static !important}' })` — test it; it can shift layouts. A gentler version targets only the known header selector |
| Black bars at the bottom of a short page | The page is shorter than the window; set `bg` to the page color (e.g. `0xFFFFFF`) |
| Auth-gated pages 401/redirect | Default capture has no session. Extend `capture.mjs` to `context.addCookies(...)` or load `storageState` before navigating |
| Text too small on mobile | Raise that mode's `fontSize` |
| Want a single combined video | Render per-mode as usual, then concatenate the mp4s with a separate ffmpeg concat, or add a mode that captures both — simplest is to keep them separate for side-by-side review |
