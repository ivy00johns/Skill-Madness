# Site template (lantern family)

Plain files under `public/`. Copy these shapes; fill copy and art from the profile and inventory.

## `index.html` skeleton

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#000000">
  <title><Name>: <promise></title>
  <meta name="description" content="<pitch sentence>">
  <meta property="og:title" content="…"><meta property="og:description" content="…">
  <meta property="og:image" content="/og.jpg">
  <link rel="icon" href="/art/mark.webp">
  <link rel="preload" href="/fonts/bricolage-grotesque-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="masthead">
    <a class="wordmark" href="/"><img class="brand-mark" src="/art/mark.webp" alt="" width="40" height="40">
      <span class="brand lit"><Name></span><span class="byline lit">by PSci Labs</span></a>
    <nav class="rail-links"><a class="nav-link lit" href="#how">How it works</a> … <a class="rail-cta" href="#waitlist">Join the waitlist</a></nav>
  </header>
  <main id="main">
    <section class="hero">
      <h1 class="headline lit">…</h1>
      <div class="stage"><div class="glow" data-light></div>
        <img class="art hero-art" src="/art/hero.webp" width="1200" height="896" alt="…" fetchpriority="high"></div>
      <div class="pitch"><p class="body lit">…</p>
        <form class="waitlist field" …><input type="email" placeholder="you@company.com" required><button>Join the waitlist</button></form>
        <p class="note">In private testing.</p></div>
    </section>
    <section class="moment" id="how" data-moment>
      <div class="moment-stage"><img class="art moment-art" data-mover src="/art/board.webp" …></div>
      <div class="moment-copy">
        <div class="beat" data-beat="0,0.25"><h2 class="section-heading lit">…</h2><p class="lede lit">…</p></div>
        … four beats …
        <p class="caption lit">Illustrative. <Name> is still being built.</p>
      </div>
    </section>
    <section class="static"><div class="copy"><h2 class="section-heading lit">…</h2><p class="lede lit">…</p></div>
      <img class="art" src="/art/machines.webp" loading="lazy" …></section>
    <section class="suite" id="suite">…<div class="suite-scene"><img class="art" src="/art/suite.webp" …>
      <div class="scene-names"><span>Fathom</span><span>Andon</span><span>Refactor</span></div></div></section>
    <section class="closing" id="waitlist">…</section>
  </main>
  <footer class="colophon lit">Fathom, Andon and Refactor are from PSci Labs.</footer>
  <script src="/main.js" defer></script>
</body>
</html>
```

## `styles.css` essentials

```css
@font-face {
  font-family: "Bricolage Grotesque";
  src: url(/fonts/bricolage-grotesque-latin-wght-normal.woff2) format("woff2");
  font-weight: 200 800;
  font-display: swap;
}
:root {
  /* paste the profile token block here, unchanged */
}
html {
  background: var(--ink);
  scrollbar-color: var(--scrollbar) var(--ink);
}
body {
  margin: 0;
  background: var(--ink);
  color: var(--amber-mid);
  font-family: "Bricolage Grotesque", sans-serif;
  font-weight: 400;
  font-optical-sizing: auto;
  -webkit-font-smoothing: antialiased;
  overflow-x: clip;
}
h1,
h2,
p {
  margin: 0;
  font-weight: 400;
}
::selection {
  background: var(--button);
  color: var(--on-button);
  -webkit-text-fill-color: var(--on-button);
}
:focus-visible {
  outline: 2px solid var(--ember);
  outline-offset: 3px;
  border-radius: 4px;
}

/* lit text: the gradient centre is the light, written by main.js as --lx/--ly per element */
.lit {
  --reach: calc(2050 * var(--u));
  color: var(--amber-mid);
  background-image: radial-gradient(
    circle var(--reach) at var(--lx, 50%) var(--ly, 50%),
    var(--lit-stops)
  );
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* art on black: near-black JPEG becomes invisible, edges fade */
.art {
  display: block;
  max-width: 100%;
  height: auto;
  mix-blend-mode: screen;
  -webkit-mask-image: radial-gradient(
    ellipse 70% 70% at 50% 50%,
    #000 55%,
    transparent 100%
  );
  mask-image: radial-gradient(
    ellipse 70% 70% at 50% 50%,
    #000 55%,
    transparent 100%
  );
}
.glow {
  position: absolute;
  inset: -40% -30%;
  background: radial-gradient(closest-side, var(--glow-stops));
  pointer-events: none;
}

/* the moment: one sticky stage, beats on the right */
.moment {
  position: relative;
  height: 640svh;
}
.moment-stage {
  position: sticky;
  top: 0;
  height: 100svh;
  overflow: clip;
}
.moment-copy {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.beat {
  position: absolute;
  left: 58%;
  right: calc(155 * var(--u));
  top: 50%;
  transform: translateY(-50%);
  opacity: var(--on, 0);
  transition: opacity 0.18s ease-out;
}
.beat::before {
  content: "";
  position: absolute;
  inset: -9svh -7% -9svh -9%;
  z-index: -1;
  background: rgba(0, 0, 0, 0.96);
  -webkit-mask-image:
    linear-gradient(90deg, transparent, #000 16% 90%, transparent),
    linear-gradient(transparent, #000 22% 78%, transparent);
  -webkit-mask-composite: source-in;
  mask-composite: intersect;
}

/* field + buttons */
.field {
  display: flex;
  align-items: center;
  height: calc(88 * var(--u));
  padding: calc(6 * var(--u)) calc(6 * var(--u)) calc(6 * var(--u))
    calc(30 * var(--u));
  border: 1px solid var(--hairline);
  background: var(--field);
  border-radius: 999px;
  transition: border-color 0.2s ease-out;
}
.field:hover,
.field:focus-within {
  border-color: var(--hairline-hot);
}
.field input {
  flex: 1;
  min-width: 0;
  height: 100%;
  background: none;
  border: 0;
  outline: 0;
  color: var(--ember);
  font: inherit;
  font-size: max(14px, calc(30 * var(--u)));
  caret-color: var(--button);
}
.field input::placeholder {
  color: var(--placeholder);
}
.field button,
.rail-cta {
  background: var(--button);
  color: var(--on-button);
  border: 0;
  border-radius: 999px;
  font: inherit;
  font-weight: 450;
  cursor: pointer;
  transition:
    background-color 0.16s ease-out,
    transform 0.16s var(--ease-press);
}
.field button:hover,
.rail-cta:hover {
  background: var(--ember);
}
.field button:active {
  transform: scale(0.98);
}

@media (prefers-reduced-motion: no-preference) {
  html {
    scroll-behavior: smooth;
  }
}
@media (width <= 860px), (aspect-ratio <= 1) {
  /* collapse the stage: H1 → art → pitch; beats at top; clamp() sizes from the profile */
}
@media (width <= 640px) {
  .nav-link {
    display: none;
  }
}
```

## `main.js` essentials

The shape below is the minimum. It reads layout on every scroll frame (`getBoundingClientRect` per
lit element), which drops frames on long pages. Prefer the cached-geometry version: measure on
load/resize, light static text once from its own section's `[data-light]`, and per frame write only
transforms, opacity and the moving beats' `--lx/--ly` (see SKILL.md step 5;
`~/Work/fathom-site/public/main.js` is a worked example).

```js
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const light = document.querySelector("[data-light]");
const lit = [...document.querySelectorAll(".lit")];
function relight() {
  const r = light.getBoundingClientRect();
  const lx = r.left + r.width / 2,
    ly = r.top + r.height / 2;
  for (const el of lit) {
    const b = el.getBoundingClientRect();
    el.style.setProperty("--lx", lx - b.left + "px");
    el.style.setProperty("--ly", ly - b.top + "px");
  }
}
const moment = document.querySelector("[data-moment]");
const mover = moment?.querySelector("[data-mover]");
const beats = [...document.querySelectorAll("[data-beat]")].map((el) => ({
  el,
  range: el.dataset.beat.split(",").map(Number),
}));
function progress() {
  // 0..1 across the sticky section
  const r = moment.getBoundingClientRect();
  return Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
}
function tick() {
  if (moment) {
    const p = progress();
    for (const {
      el,
      range: [a, b],
    } of beats) {
      const t = (p - a) / (b - a);
      el.style.setProperty(
        "--on",
        Math.max(0, Math.min(1, Math.min(t * 4, (1 - t) * 4))).toFixed(3),
      );
    }
    if (mover)
      mover.style.transform = `translate(${(p * 30 - 10).toFixed(2)}vw, ${(Math.sin(p * Math.PI) * -6).toFixed(2)}vh) scale(${(1 + p * 0.35).toFixed(3)})`;
  }
  relight();
}
if (reduce) {
  beats.forEach((b) => b.el.style.setProperty("--on", 1));
  relight();
} else {
  addEventListener("scroll", () => requestAnimationFrame(tick), {
    passive: true,
  });
  addEventListener("resize", tick);
  tick();
}
```

## `vercel.json`

```json
{
  "cleanUrls": true,
  "trailingSlash": false,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [{ "key": "X-Content-Type-Options", "value": "nosniff" }]
    },
    {
      "source": "/art/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

Deploy the `public/` directory as the project root (CLI: `vercel deploy public --yes`; MCP
`create_deployment`: `files` from `public/` with paths relative to it, `projectSettings.framework: null`).
A preview is the default target; production and domains only on an explicit ask.

## Checks (Playwright)

| Check (also at 1024×768, and again with reduced motion)                                | 1440×900 | 390×844                                  |
| -------------------------------------------------------------------------------------- | -------- | ---------------------------------------- |
| full-page screenshot into `docs/review/`                                               | yes      | yes                                      |
| console errors                                                                         | 0        | 0                                        |
| `img` with `naturalWidth === 0`                                                        | none     | none                                     |
| `document.documentElement.scrollWidth <= innerWidth`                                   | yes      | yes                                      |
| H1 visible above the fold, field visible in the hero                                   | yes      | yes (field within the first 1.5 screens) |
| the four beats reach `--on: 1` at some scroll position                                 | yes      | yes                                      |
| the field submits to the configured endpoint, or shows the honest "not wired yet" note | yes      | yes                                      |
| axe wcag2aa / wcag21aa violations                                                      | 0        | 0                                        |
| frame timing while wheel-scrolling the moment, p95                                     | ≤ 17ms   | ≤ 17ms                                   |
