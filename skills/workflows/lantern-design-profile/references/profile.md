# The lantern family: design profile

Measured from tryfathom.dev on 2026-11-07 (shipped CSS, computed styles at 1440×900 and 390×844).
These values are the family. A site in the family copies the token block verbatim and changes
only what "What a site may change" allows.

## Tokens

```css
:root {
  /* ink and light */
  --ink: #000000; /* the page. There is no other surface colour. */
  --ember: #f7d596; /* hottest text, at the light source */
  --amber: #f5d08e;
  --amber-mid: #eebf7b; /* default text colour */
  --amber-low: #dfaa66;
  --amber-floor: #a8875c; /* text furthest from the light */
  --button: #f8c881; /* CTA fill */
  --on-button: #231312; /* CTA text */
  --field: rgba(30, 20, 12, 0.72); /* input background */
  --hairline: rgba(
    232,
    190,
    130,
    0.14
  ); /* masthead rule, field border at rest */
  --hairline-hot: rgba(248, 200, 129, 0.62); /* field border on hover/focus */
  --placeholder: #9a8a76;
  --scrollbar: #4a3a26;
  /* the glow behind the light source (radial, closest-side) */
  --glow-stops:
    rgba(255, 198, 108, 0.8) 0, rgba(246, 174, 82, 0.58) 10%,
    rgba(212, 150, 74, 0.41) 24%, rgba(152, 108, 52, 0.25) 42%,
    rgba(92, 66, 30, 0.11) 62%, rgba(44, 31, 14, 0.03) 80%, transparent 94%;
  /* the lit-text gradient: centre at the light source, radius = reach */
  --lit-stops:
    var(--ember) 0, var(--amber) 42%, var(--amber-mid) 60%,
    var(--amber-low) 82%, var(--amber-floor) 100%;
  /* the design unit: the hero is a 2752×1536 frame scaled to the viewport */
  --u: min(calc(100vw / 2752), calc(100svh / 1536));
  --ease-press: cubic-bezier(0.16, 1, 0.3, 1);
  color-scheme: dark;
}
```

```json
{
  "ink": "#000000",
  "amber": {
    "ember": "#f7d596",
    "amber": "#f5d08e",
    "mid": "#eebf7b",
    "low": "#dfaa66",
    "floor": "#a8875c"
  },
  "button": { "fill": "#f8c881", "text": "#231312" },
  "field": {
    "bg": "rgba(30,20,12,0.72)",
    "border": "rgba(232,190,130,0.14)",
    "placeholder": "#9a8a76"
  },
  "font": "Bricolage Grotesque (variable, 200-800, self-hosted woff2, font-optical-sizing auto)"
}
```

## The light rule

All copy is **lit text**: its colour is a radial gradient clipped to the glyphs, centred on the
light source's position on the page. Text near the light reads `--ember`; text far away reads
`--amber-floor`. The light source belongs to the character (a lure, a lantern, a shell). When the
character moves (scroll-driven), the gradient centre moves with it. Behind the light sits one
radial glow (`--glow-stops`), roughly 1.7× the character's width.

Implementation shape (the build copies this):

```css
.lit {
  color: var(--amber-mid);
  background-image: radial-gradient(
    circle var(--reach) at var(--lx) var(--ly),
    var(--lit-stops)
  );
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

`--lx/--ly` are the light's position relative to the element; `--reach` is about 2050 units
(`calc(2050 * var(--u))`). Sections far from the character (the suite, the closing) may set the
text colour flat (`--amber` headings, `--amber-mid` ledes).

## Type

One family: **Bricolage Grotesque**, variable. Weights: 450 display H1, 400 everything else,
500 nav and labels, 600 CTA, 650 wordmark. Tracking −0.012em on display sizes, −0.008em on H2.

| Role           | 1440 (units → px)       | 390                              | Measure                    |
| -------------- | ----------------------- | -------------------------------- | -------------------------- |
| H1             | 125u → 65px / 129u line | clamp(36px, 11.2vw, 84px) / 1.04 | 3 lines, nowrap on desktop |
| H2             | 104u → 54px / 120u      | clamp(32px, 9.4vw, 64px) / 1.08  | ≤ 6 words                  |
| Lede           | 58u → 30px / 80u        | clamp(19px, 5vw, 26px) / 1.36    | 34ch (26ch in the closing) |
| Pitch body     | 43.5u → 23px / 54.5u    | clamp(19px, 5vw, 24px) / 1.32    | one sentence               |
| Nav            | 15px                    | hidden ≤ 640px                   |                            |
| Caption / note | max(13px, 26u) / 1.4    | 13–14px                          |                            |
| Field input    | max(14px, 30u)          | 16px                             |                            |

## Layout

- **Masthead**: mark + wordmark ("Name" / "by PSci Labs") left; up to three text links and one
  pill CTA right; one hairline below. Height 116u (min 56px); 60px on mobile.
- **Hero**: a fixed-ratio stage (2752×1536 units). H1 top-left; the character centre-right,
  overlapping the H1's right edge; pitch + field + one-line note bottom-right (width 695u). On
  mobile the order becomes H1, character, pitch, field.
- **The moment**: one sticky section, 640svh tall, the stage pinned at `top: 0`. Four beats of copy
  on the right (width ≤ 44vw), each fading in with a soft black vignette behind it; the character
  moves across the stage on scroll. On mobile the beats sit at the top under a black-to-transparent
  gradient and the stage fills the rest.
- **Static sections**: 2-col grid (heading left `1fr`, paragraph right `1.05fr`, gap 120u), one
  image below or beside, masked at the edges (`mask-image: linear-gradient(90deg, transparent, #000 5% 95%, transparent)`).
- **Suite**: heading "X plans. Y decides. Z is the workspace." left, paragraph right, a 1920×660
  scene of the three mascots, names under each in a 3-col grid.
- **Closing**: character left, H2 + lede + field right, colophon line bottom-right.
- **Gutters**: 155u (≈81px at 1440); mobile `clamp(20px, 6vw, 48px)`. Page `overflow-x: clip`.
- **Fields and buttons**: pill (`border-radius: 999px`), field 88u tall (56px mobile), button
  inside the field; the masthead CTA is a 36px pill with 7px radius.

## Motion

- Scroll-driven only: the character's position, the stage's zoom, label and beat opacity.
- Transitions: 0.16s `background-color` on buttons; 0.32s `opacity` crossfades (still ↔ loop
  video); 0.18s label fades; `transform: scale(.98)` on press with `--ease-press`.
- One keyframe animation at most (the intro's "skip" fade). `prefers-reduced-motion: reduce`
  turns smooth scroll off and shows the static page.
- Optional intro: the page starts dark (light reach 1px, character at `brightness(0)`), the light
  switches on, a "Skip intro" button sits bottom-right.

## Copy voice

1. H1 is a promise in one sentence, second person, full stop.
2. H2s are claims of six words or fewer, full stop. ("A map, not a list.")
3. One idea per beat; the four beats tell one story about one thing.
4. Say what is not ready: "In development.", "Illustrative map. X is still being built."
5. No exclamation marks, no superlatives, no feature lists.
6. The suite triad comes from the product's own docs, in their words (Fathom's spec says "Fathom
   plans, Andon orchestrates, Refactor executes"). Do not copy a sibling site's phrasing of it.

## Graphics

Rendered on black, lit by the character's light only. Soft 3D, vinyl-toy surfaces, big glossy
eyes with two highlights, small smile, no outlines (styling shared with the family; the characters
themselves are always this site's own). Scene sizes: hero 4:3 (≈1200×900), moment
stage 16:9 or 4:3, suite 21:9 (1920×660 to 1920×800), closing 4:3, mark 1:1. Render with the
newest image model the key can reach (`site-character-art` lists them). The model returns JPEG
even when saved as `.png`, so backgrounds are near-black (7-13/255 measured), not transparent:
either crush them to page black (`prepare.py` black point) and place with `mix-blend-mode: screen`
plus a radial mask, or cut the character out to an RGBA webp when it moves over drawn lines. See `graphics-brief.md` for the per-section brief and `site-character-art` for the
pipeline.

## What a site may change

- The cast (always the site's own), its light source, and the characters' own colours (skin only).
- The hero moment and its four beats; the two or three static sections; all copy.
- The product nouns in alt text and labels.
- Nothing in the token block, the type scale, the field/button shapes, or the motion rules.

## Profile checklist

- [ ] Token block copied verbatim; no second accent, no second font.
- [ ] One lead character (plus at most three supporting), one light source, two sentences on why.
- [ ] One hero moment with exactly four beats, each ≤ 6-word heading + one sentence.
- [ ] A scene line per section: scene, aspect ratio, light, character action, alt text.
- [ ] Copy voice rules present; the suite triad taken from the product's docs.
- [ ] Original: no copy, image or character taken from a sibling or reference site.
- [ ] "Borrowed / changed" list when a sibling site exists.
- [ ] Under 200 lines.

## Template for `docs/design-profile.md`

```markdown
# <Site> design profile (lantern family)

## Tokens

<the CSS token block, verbatim>

## Cast

Lead: <character>, carrying <light>. Supporting: <0-3 characters, one line each>.
Why: <two sentences tying the cast to the product's job>. Skin colours: <hex each>, used nowhere else.

## Hero

H1: "<promise>." Pitch: "<one sentence>." Note: "<status line>."

## The moment: <name>

1. "<beat heading>." <one sentence>
2. …
3. …
4. …

## Static sections

- <heading> — <one sentence> — scene: <name>

## Suite

<the triad in the product docs' words> + <one paragraph>

## Closing

H2 "<claim>." Lede "<two sentences>." Field + note.

## Graphics brief

| scene | ratio | light | character | alt |
| ----- | ----- | ----- | --------- | --- |

## Borrowed / changed

- Borrowed (styling language only): …
- New (cast, copy, every image): …
```
