---
name: site-character-art
version: 1.1.0
description: >-
  Plan a site's cast of generated characters and scenes, render them through
  nano-banana (Gemini) with style references, and keep a graphics inventory:
  scene names, sizes, prompts, versions, matched-black or knocked-out
  backgrounds, web-ready webp. Use for mascot art for a marketing site,
  "render the hero scene", or when a generated image shows a dark rectangle on
  a black page.
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: ["graphics/"]
  patterns: ["graphics/inventory.json", "graphics/scenes.json"]
  shared_read: ["docs/design-profile.md", "public/art/"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
composes_with:
  [
    "nano-banana",
    "lantern-design-profile",
    "marketing-site-build",
    "look-first",
  ]
spawned_by: []
---

# Site character art

Marketing sites in the lantern family are carried by their generated characters: one mascot,
one light, a handful of scenes that tell the product's story. This skill turns a design profile's
graphics brief into rendered, web-ready images and keeps the record of how each was made, so the
set can be regenerated, extended or re-rolled months later by someone who wasn't there.

The pipeline is three scripts under `scripts/` (python3; `prepare.py` needs Pillow) that sit on
top of `nano-banana`'s `generate_image.py`:

| Step    | Script                           | What it does                                                                                                                                                          |
| ------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| plan    | you write `graphics/scenes.json` | one entry per scene: name, aspect, prompt, reference images, alt text                                                                                                 |
| render  | `generate_scenes.py`             | calls nano-banana per scene, sequentially, into `graphics/candidates/<site>-<scene>-vN.png`, never overwriting, and records every prompt in `graphics/inventory.json` |
| record  | `inventory.py`                   | sniffs each candidate's real format and size, measures corner and edge darkness, warns on lit edges                                                                   |
| prepare | `prepare.py`                     | turns promoted candidates into `public/art/<scene>.webp` (+ `-800`), matched-black or knocked out to alpha                                                            |

Generation is paid (about $0.04 per standard image, more for the Pro and newer tiers): confirm the
scene list and an image cap (including retries) with the person before the first render, render the
hero alone, then the rest in one go, and keep a running count against the cap.

**Model.** Run `python3 scripts/generate_scenes.py --list-models` first and use the newest image
model the key reaches (on 2026-11-08 that was `gemini-nano-banana-2.1`, Nano Banana 2.1, above
`gemini-3-pro-image`); pass its raw id to `--model`. Fall back to `pro` only if the newer one fails.
Record the id in the inventory's `generator`.

**Announce at start:** "Using site-character-art to plan and render the cast for [site]."

## Instructions

1. **Read the brief.** Open `docs/design-profile.md` (from `lantern-design-profile`) and its
   graphics brief table. Each row becomes a scene. If there is no profile, write the table first
   with that skill; rendering without a brief produces a pile of unrelated pictures.
2. **References are this site's own.** Never pass a sibling or reference site's image as a
   reference: the model copies its character, and the site becomes a clone. Render the lead's hero
   first from words alone (cast line + style block); every later scene then references that
   promoted hero, and a supporting character's first scene becomes its reference for group scenes.
   The only outside reference allowed is a mascot the person says this product already owns (put it
   in `graphics/refs/`; convert webp to PNG, since nano-banana sniffs mime by content).
3. **Write `graphics/scenes.json`.** Use `references/prompt-recipes.md`: every prompt is the
   **cast line** (who the character is, in words the model can draw) + the **scene line** (what
   it does, where the light is) + the **style block** (render language, black background, glow
   fading to black, no text). The hero renders first; every later scene lists the hero candidate
   as a reference so the lantern, eyes and surface match.
4. **Render.** `python3 scripts/generate_scenes.py graphics/scenes.json --site <slug> --model <newest id>`
   renders every scene (Pro and newer honour reference images; `standard` ignores them). Pass
   `--only hero` first, look at it, then run the rest. Each scene may carry a `section` naming where
   the page uses it; it is copied into the inventory. Each run writes a new `vN` file; nothing
   is overwritten, nothing deleted. Re-roll one scene with `--only <scene>`.
5. **Look at every candidate** before choosing (open the image files; never pick from filenames).
   Check: one light source, the glow fades to black before the edge, no text, eyes and surface
   match the hero, the alt text is still true. Mark the chosen file `"status": "promoted"` in
   `graphics/inventory.json`; leave the others as `candidate` (or `rejected` with a reason).
6. **Record and prepare.** `python3 scripts/inventory.py graphics/candidates graphics/inventory.json`
   fills in real format, size and darkness numbers (the model returns JPEG even when the file is
   named `.png`; corners should read ≤ 3/255, and an edge above 24/255 means a lit edge that will
   show as a rectangle). Then `python3 scripts/prepare.py graphics/inventory.json --out public/art`
   writes the webp files the build uses and records their paths and sizes back into the inventory.
7. **Hand off.** `marketing-site-build` reads `graphics/inventory.json` for file paths, sizes
   and alt text. The site repo keeps `graphics/` (refs, scenes, inventory, candidates) so the set
   is reproducible; candidates can be left out of git if they are large, the inventory cannot.

## Backgrounds: matched black or knocked out

The model cannot return transparency, and its "black" is not page black: corners measured 7-13/255
on Nano Banana 2.1, which shows as a faint box on a `#000` page. `prepare.py` applies a levels
black point (`--black-point`, default 16) before export, then one of three modes chosen per scene
in `scenes.json` (`"background": "black" | "alpha" | "cutout"`):

- **`black`** (default): after the black point, pixels with every channel ≤ 6 are forced to pure 0,
  and the build places the image with `mix-blend-mode: screen` plus a radial `mask-image`, so any
  residual noise and the JPEG edge disappear against the page. Right for scenes with a large glow.
- **`cutout`**: near-black pixels connected to the image border become transparent (flood fill,
  1px feather); dark shadows inside the character stay opaque. Right for a character that moves
  over drawn lines, where screen blend would let the lines show through its body.
- **`alpha`**: a luminance ramp (0 → 24) becomes the alpha channel and the result is an RGBA
  webp. Right for the mark and for images that will sit over something other than pure black.

Either way, a scene whose glow reaches the image edge cannot be fixed here: re-roll it with "the
glow fades to pure black well inside the frame".

## Examples

### Example 1: a cast from a profile

**User says:** "Make the characters and scenes for the Andon site from the design profile."

**Actions:**

1. Read `docs/design-profile.md`; the brief lists hero, board, machines, cord, suite, closing, mark.
2. No outside references: the profile's cast is new, so the hero is rendered from words first.
3. Write `graphics/scenes.json` with seven entries from the recipes; confirm count and cap.
4. Render `--only hero`, look at it, then render the rest with the hero as a reference.
5. Look at all seven, promote one per scene, run `inventory.py` then `prepare.py`.

**Result:** `public/art/*.webp` for the build; `graphics/inventory.json` with every prompt, size
and status; candidates kept under `graphics/candidates/`.

### Example 2: the dark rectangle

**User says:** "The octopus image shows a dark box around it on the black page."

**Actions:**

1. `inventory.py` on the candidates: the file is JPEG, corners read 1–3, right edge reads 31.
2. The edge is lit: re-roll that scene with the glow fading inside the frame; or, if the edge is
   only noise, set `"background": "black"` and confirm the build uses screen blend + mask.

**Result:** a re-rendered or re-prepared image that sits on the page with no visible boundary.

## Triggering test

- Must trigger: "render the mascot scenes for the site", "make the characters for the marketing
  page with Gemini", "the generated image has a black box around it on the dark page".
- Must NOT trigger: "generate a product photo of a leather bag" (plain `nano-banana`), "write the
  design profile" (`lantern-design-profile`), "build the site" (`marketing-site-build`).

## Troubleshooting

### `GEMINI_API_KEY ... is not set`

**Cause:** only nano-banana's own script can tell; it searched the listed `.env` files.
**Solution:** follow nano-banana's Setup section (export the key or select a root `.env`). Do not
grep for the key yourself.

### The character drifts between scenes

**Cause:** later scenes were rendered without the hero as a reference, or with `--model standard`.
**Solution:** add the promoted hero file to every scene's `refs` and render with the newest model
(Pro or later). For a group scene, also reference each supporting character's own first scene.

### A scene came back with text or a watermark

**Cause:** the prompt described a label, a card title or a screen.
**Solution:** describe shapes ("a small translucent card, blank"); all words are HTML over the image.

### Pillow is missing

**Cause:** `prepare.py` needs it for webp and alpha.
**Solution:** `python3 -m pip install Pillow` in a venv, or use `cwebp` for black-mode scenes only.
