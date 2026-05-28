# Mobile-First & Responsive Discipline

The patterns, tokens, and verification that keep a "responsive" build from rotting into inline styles, hardcoded widths, and an `!important` pile. SKILL.md points here before any CSS is written. Read top-to-bottom the first time; come back to the patterns section to copy.

## Why this file exists

Agents that read only SKILL.md repeatedly ship the same three failures: inline grid layouts on elements, fixed pixel widths on layout containers, and desktop-first patched with `@media (max-width: …)` queries that fight the base rules. Each one is recoverable individually; together they compound into a layout that needs `!important` to do anything, and at that point the responsive layer is unmaintainable.

This file is the playbook that prevents that. It is opinionated on purpose — when there is one right answer, it gives one.

## The three failure modes to avoid

1. **Inline `style=` for layout.** An inline `style` attribute beats any non-`!important` selector in a stylesheet. The moment you inline `style="display:grid;grid-template-columns:60% 40%"`, every media query targeting that element silently loses. The only way back is `!important`, which then needs to propagate to neighboring rules, and the cascade is dead.

2. **Hardcoded `width: <px>` on layout containers.** `width: 1200px` on a wrapper locks the layout off mobile entirely. `width: 600px` on a card means it ignores its grid cell. Fixed widths belong on *tokens* (icon sizes, button heights, hairline borders) — not on anything that holds other content.

3. **Desktop-first with `max-width` patches.** Writing `.thing { grid-template-columns: 1fr 1fr; }` and then `@media (max-width: 768px) { .thing { grid-template-columns: 1fr; } }` is the workflow that produces the other two failures. The base rule is more complex than it needs to be, and every device width below the threshold is a "patch" fighting it. Inverting the order — simple base for mobile, layered enhancements above — makes the base naturally responsive and the rest additive.

## Breakpoint tokens (canonical)

Use these. Match Tailwind's defaults so cross-stack equivalents are obvious, and so devs new to the project don't have to learn a private vocabulary.

```css
:root {
  --bp-sm:   640px;  /* large phone / small tablet portrait */
  --bp-md:   768px;  /* tablet portrait */
  --bp-lg:  1024px;  /* tablet landscape / small laptop */
  --bp-xl:  1280px;  /* desktop */
  --bp-2xl: 1536px;  /* wide desktop */
}
```

Then always layer up with `min-width`:

```css
.thing { /* base — mobile */ }
@media (min-width: 768px)  { .thing { /* tablet+ */ } }
@media (min-width: 1024px) { .thing { /* laptop+ */ } }
```

Invent project-private breakpoints only when the content genuinely demands one — e.g. a chart whose legend wraps at 880px regardless of overall layout. Even then, name it for the content (`--bp-chart-legend: 880px`), not a new tier.

## Size primitives — pick by intent, not by reflex

The reason hardcoded `width: 600px` keeps appearing is that "container should be 600px" is what the design mock says. It's almost never what the design actually *needs*. Pick the primitive that matches intent:

| Intent | Primitive | Example |
|---|---|---|
| Container should grow up to a ceiling | `max-width` | `max-width: 80ch;` |
| Container should shrink to its content | `width: fit-content` | `width: fit-content;` |
| Fluid between a floor and a ceiling | `clamp()` | `width: clamp(20rem, 60vw, 60rem);` |
| Side-by-side that wraps when cramped | `flex-basis` + `flex-wrap` | `flex: 1 1 20rem;` |
| Auto-fitting card grid | `repeat(auto-fit, minmax())` | `grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));` |
| Reading-comfortable text width | `max-width` in `ch` | `max-width: 65ch;` |

If you find yourself typing `width: <number>px` on anything that contains other elements, stop and pick from this table. Tokens (icons, button heights, hairlines) are the exception.

## Fluid type and spacing

Fixed `font-size: 48px` headings look comical on phones and tiny on 4K. Use `clamp()` so headings scale with viewport between a floor and a ceiling:

```css
h1 { font-size: clamp(1.75rem, 4vw + 1rem, 3.5rem); }
h2 { font-size: clamp(1.5rem, 2.5vw + 0.75rem, 2.5rem); }
```

The middle term — `<px or rem> + <vw>` — is the magic. Pure `vw` over-scales; `clamp(min, vw, max)` is what gives the "fluid but not crazy" feel.

Body text stays static at **16px floor minimum**. iOS Safari auto-zooms inputs under 16px, which is jarring; the same floor on body type keeps things consistent.

For spacing, prefer `rem` (scales with user's font preference) for layout gaps. Use `px` only for hairlines (1–2px borders) and tokens that must hold a physical-pixel shape.

## Layout patterns to copy

These are the patterns that come up in nearly every build. Copy them; don't reinvent.

### Page shell with content max-width

```css
.shell { width: 100%; padding-inline: clamp(1rem, 4vw, 2rem); }
.shell > * { max-width: 80ch; margin-inline: auto; }
```

The shell handles the gutter; children get a reading width and auto-center. No media queries needed for the basic case.

### Two-column that collapses on mobile

```css
.two-col {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;        /* base: stacked */
}
@media (min-width: 768px) {
  .two-col { grid-template-columns: 60% 40%; }
}
```

### Auto-fit card grid (no breakpoints needed)

```css
.cards {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}
```

This is one of the most underused patterns. Cards reflow from 1-up on mobile to 4-up on desktop without a single media query. The `16rem` is the floor — adjust per card content.

### Responsive nav (horizontal → hamburger)

```css
.nav { display: flex; gap: 1rem; flex-wrap: wrap; }
.nav-toggle { display: none; }

@media (max-width: 767px) {
  .nav         { display: none; }
  .nav.is-open { display: flex; flex-direction: column; }
  .nav-toggle  { display: inline-flex; }
}
```

The toggle button gets `display: none` by default and shows on small screens. The base nav is `flex-wrap: wrap` so it degrades gracefully even before the breakpoint kicks in.

### Hero that doesn't collapse to nothing

```css
.hero {
  display: grid;
  gap: 2rem;
  align-items: center;
  grid-template-columns: 1fr;           /* base: stacked */
}
@media (min-width: 1024px) {
  .hero { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
}
```

The `minmax(0, 1fr)` (instead of just `1fr`) is the fix for "my image inside a grid column blows the column wider than 50%" — grid items default to `min-width: auto`, which is "their content's intrinsic min", which for a big image is the image's natural width.

### Image that doesn't break layout

```css
img, video { max-width: 100%; height: auto; display: block; }
```

Put this in your base reset. Forgetting it is the #1 source of "the page has a horizontal scrollbar on mobile and I can't find why."

## Touch targets

Minimum **44 × 44 CSS pixels** for any tap target on mobile (Apple HIG; WCAG 2.5.5 sets 24 × 24 as AA minimum, but 44 is the safer floor). On dense desktop UIs you can shrink, but the same control on a phone needs the larger hit area.

```css
.btn { min-height: 44px; padding: 0.625rem 1rem; }
```

A hover-only interaction (tooltip, dropdown trigger) is broken on touch. Every hover state needs a tap-or-focus equivalent — usually `:focus-visible` plus a click handler that toggles the same state.

## Mobile gotchas that will bite you

| Gotcha | Fix |
|---|---|
| `<meta viewport>` missing → page renders at "fake desktop" zoom | `<meta name="viewport" content="width=device-width, initial-scale=1">` in every `<head>`, no exceptions |
| `100vh` on iOS Safari includes the URL bar and jumps when scrolled | Use `100dvh` (dynamic) or `min-height: 100svh` (smallest). Fall back: `min-height: 100vh; min-height: 100dvh;` (second wins where supported) |
| Inputs under 16px font cause auto-zoom on iOS focus | Body inputs stay ≥ 16px. If you need a visually smaller input, set `font-size: 16px` and use `transform: scale()` for the visual shrink |
| Mysterious horizontal scrollbar on mobile | A child element or image is wider than viewport. Don't band-aid with `overflow-x: hidden` on body — find the offender with `* { outline: 1px solid red; }` in devtools |
| Notched devices clip content under the notch | Use `env(safe-area-inset-*)`: `padding-inline: max(1rem, env(safe-area-inset-left)) max(1rem, env(safe-area-inset-right));` |
| `position: fixed` bars get pushed above the fold by iOS keyboard | Prefer `position: sticky` for headers; for chat-style inputs, listen for `visualViewport` resize events |
| Image with intrinsic width breaks grid column | `minmax(0, 1fr)` in `grid-template-columns`, and `max-width: 100%; height: auto;` on the image |

## Stack adapters

The rules above are stack-neutral. Apply them through your stack's mechanism:

### Tailwind / shadcn

Tailwind's default breakpoints (`sm: 640`, `md: 768`, `lg: 1024`, `xl: 1280`, `2xl: 1536`) match the tokens above. Use `md:`, `lg:`, `xl:` prefixes mobile-first. Helpful utilities:

- `max-w-prose`, `max-w-screen-md`, `container` — content widths
- `min-h-dvh` (Tailwind 3.4+) instead of `min-h-screen` — mobile-safe full-height
- `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3` — explicit responsive grid
- `grid grid-cols-[repeat(auto-fit,minmax(16rem,1fr))]` — auto-fit grid
- `aspect-video`, `aspect-square` — instead of fixed widths/heights on media

Don't redefine the default breakpoints unless the design system requires it. Don't use `style={}` props for layout — same cascade trap as inline `style=` attributes.

### Vanilla CSS

Tokens in `:root`, classes in stylesheets, mobile-first, `min-width` queries. No framework needed; the patterns above work as-is.

### CSS-in-JS (styled-components, emotion, Linaria, vanilla-extract)

Same rules apply. Base styles in the component's styled definition, media queries in the same scope. Avoid `style={}` JSX props for layout — they generate inline `style=` and inherit its specificity problem.

### Server-rendered themes (WordPress / Rails / Phoenix / Django / PHP)

Same rules, plus one platform constraint: there's no bundler injecting your CSS, so you must register the stylesheet through the platform's mechanism and reference classes from templates. Hand-writing `<style>` blocks or `style=` attributes in templates to "just get it working" is the failure mode.

- **WordPress:** enqueue every stylesheet via `wp_enqueue_style()` in `functions.php`. Order matters — set up a dependency chain (`tokens → base → responsive`) so cascade is predictable. Version each file with `filemtime( get_stylesheet_directory() . '/path/to.css' )` so edits actually reach the browser instead of being served stale. Templates (`front-page.php`, `page-*.php`, etc.) contain markup with `class=` attributes only.
- **Rails / ERB:** put CSS in `app/assets/stylesheets/`, register via `stylesheet_link_tag` in the layout. Same class-only discipline in templates.
- **Phoenix LiveView:** put CSS in `assets/css/app.css`, let esbuild handle it. Live components carry `class=` attributes.

A base stylesheet that ends up *smaller* than the responsive stylesheet is a strong signal that layout leaked into the templates. Investigate.

## The two-width render proof (required before reporting done)

A `@media` rule in CSS proves nothing if an inline style overrides it, and a `grep` for `@media` proves even less. Before reporting done, actually render the page at both widths and verify with your eyes (or a screenshot):

- **375 × 667** (iPhone SE / small mobile). Browser devtools → device toolbar → 375 × 667. Or Playwright: `await page.setViewportSize({ width: 375, height: 667 })`.
- **1440 × 900** (laptop). Same drill.

At each width, check:

- [ ] No horizontal scrollbar
- [ ] Text wraps; nothing clipped
- [ ] Images scale (no overflow)
- [ ] Tap targets look ≥ 44 × 44 at 375px
- [ ] Navigation is reachable (hamburger works on mobile if collapsed)
- [ ] Hero / primary CTA visible without scrolling at the top of each width

If the `playwright` skill is composable in your environment, take screenshots — they're cheap and provide receipts. Otherwise capture manually via browser devtools. The validation-checklist depends on this proof; do not skip it.

## Bugs and where they actually come from

| Symptom | Root cause |
|---|---|
| "Works in dev but breaks on phone" | Missing `<meta viewport>`, or inline `style=` overriding media query |
| "Added a media query and nothing happened" | Inline style upstream is winning specificity. Move to a class |
| "Layout jumps when browser resizes" | Mixed `vw` / `px` without `clamp()`, or `position: absolute` on a layout container |
| "Cards don't wrap" | `flex-wrap: wrap` missing, or fixed `width` on cards instead of `flex-basis` |
| "Page is wider than viewport on mobile" | A child has fixed `width: <px>` larger than viewport, or an unconstrained image. Find with `* { outline: 1px solid red; }` |
| "Hero looks tiny on 4K, huge on phone" | Fixed `font-size: 48px`. Use `clamp()` |
| "Everything is `!important` and I can't tell which rule wins" | Inline styles upstream. Remove them and rebuild the cascade from scratch |
| "Image blows out grid column to its natural width" | `minmax(0, 1fr)` in `grid-template-columns` + `max-width: 100%; height: auto;` on the image |

## The rules in one screen

1. **Mobile-first.** Base rules unprefixed; enhancements in `min-width` queries.
2. **Layout CSS lives in stylesheets, keyed by class.** Never inline `style=` for grid/flex/sizing. The only legitimate inline `style=` is a per-instance CSS custom property the JS/server computes (e.g. `style="--progress: 72%"`).
3. **No hardcoded `width: <px>` on layout containers.** Use `max-width`, `clamp()`, `minmax()`, or `flex-basis` — pick by intent from the primitives table. Tokens (icons, button heights, hairlines) are the exception.
4. **Use the canonical breakpoint tokens** (sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536). Project-private breakpoints only when content genuinely demands it.
5. **Fluid type with `clamp()`** for headings; static **≥ 16px** for body and inputs.
6. **Tap targets ≥ 44 × 44** on mobile. Every hover state has a tap/focus equivalent.
7. **`<meta viewport>` always.** Use `100dvh` / `100svh` instead of `100vh`.
8. **Two-width render proof** at 375px and 1440px before reporting done.
9. **If you reach for `!important`, stop** — the bug is an inline style upstream.
