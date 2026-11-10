# `graphics/inventory.json`

One file per site. `generate_scenes.py` appends an entry per render; `inventory.py` fills in the
measured fields; `prepare.py` fills in `outputs`. People edit `status`, `alt` and `notes`.

```json
{
  "site": "andon",
  "generator": "nano-banana generate_image.py, model gemini-nano-banana-2.1",
  "refs": [],
  "entries": [
    {
      "scene": "hero",
      "file": "graphics/candidates/andon-hero-v1.png",
      "version": 1,
      "rendered_at": "2026-11-07T20:30:56Z",
      "aspect": "4:3",
      "model": "pro",
      "refs": [],
      "prompt": "…the full prompt…",
      "background": "black",
      "section": "hero",
      "alt": "Andon's mascot, a lilac octopus holding up a glowing amber paper lantern.",
      "status": "promoted",
      "notes": "",
      "measured": {
        "format": "jpeg",
        "width": 1200,
        "height": 896,
        "corners_max": 2,
        "edge_max": 9,
        "sha1": "…"
      },
      "outputs": {
        "webp": "public/art/hero.webp",
        "webp_800": "public/art/hero-800.webp",
        "width": 1200,
        "height": 896
      }
    }
  ]
}
```

Field rules:

- `scene` matches the design profile's graphics brief; `version` increments per render of that scene.
- `status` is `candidate` (default), `promoted` (exactly one per scene) or `rejected`.
- `background`: `black` (matched black, used with screen blend + mask), `alpha` (luminance knock-out)
  or `cutout` (border-connected black removed; for a character that moves over drawn art).
- `section`: where the page uses the image; copied from `scenes.json`.
- `measured.corners_max` is the brightest channel in the four 8×8 corner patches; `edge_max` the
  brightest channel along the four edges. `edge_max > 24` is a warning: the glow reaches the edge.
- `outputs` exists only for promoted entries after `prepare.py`.

# `graphics/scenes.json`

The plan the renderer reads:

```json
{
  "site": "andon",
  "style": "…the style block…",
  "cast": { "andon": "…cast line…" },
  "scenes": [
    {
      "scene": "hero",
      "aspect": "4:3",
      "refs": [],
      "background": "black",
      "alt": "…",
      "prompt": "{cast.andon} <scene line> {style}"
    }
  ]
}
```

`{cast.<name>}` and `{style}` are substituted. The hero has no refs (words only); later scenes
name `"hero"`. `refs` are relative to `graphics/`; a ref that
names a scene (`"hero"`) resolves to that scene's promoted candidate, or its latest version if
none is promoted yet.
