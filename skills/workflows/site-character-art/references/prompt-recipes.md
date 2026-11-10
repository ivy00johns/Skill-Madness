# Prompt recipes for lantern-family scenes

Every prompt is three parts, in this order: **cast line** → **scene line** → **style block**.
The cast line and style block are fixed per site and pasted into every scene; only the scene line
changes. Write prompts as full sentences; the Gemini image models follow prose better than tags.

## Style block (paste verbatim, then adjust only the light's name)

> Soft 3D rendered character art in the exact style of the reference images: smooth clay-like
> vinyl toy surfaces, large glossy dark eyes with two white highlights, a small gentle smile, no
> hard outlines. The scene is lit by ONE warm amber <paper lantern / lure / glowing shell> only;
> everything far from it falls into deep shadow. Pure black (#000000) background everywhere
> outside the characters and the glow, no floor unless stated, no bubbles, no text, no watermark,
> no border. The glow fades to pure black well inside the frame so the image can sit on a black
> web page.

## Cast line (one per character, invented for this site)

Write the cast line from the profile's cast, never from a sibling site's mascot. Shape: name,
species and build, two colours (skin and one accent), eyes, one prop that tells its job. Only the
lead carries the light. An example from the fathom-site build (2026-11-08), to show the shape only:

> Vela is a small, round owl cartographer: soft moon-grey plumage with faint silver-blue speckles,
> a pale cream heart-shaped face disc, huge glossy near-black eyes, a tiny peach beak. Vela
> carries an old brass ship's lantern with amber glass panes; the lantern is the only light.

> Digby is a chubby, velvety mole surveyor: dusky rose-brown fur, a round soft pink nose, big glossy
> dark eyes behind small round brass spectacles, broad pink spade-shaped front paws.

When a supporting character's scene has no lead in it, say "Use the reference image only for the
render style and for the <light>" so the model takes the lantern, not the lead's body.

## Scene lines (the family's base set)

| Scene   | Ratio | Scene line                                                                                                                                                                                                                                                                   |
| ------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| hero    | 4:3   | "<Name> floats in black water at three-quarter view facing the viewer, one arm raised holding the glowing amber <light>; the light falls across the face and nearest arms, the far side sinks into shadow."                                                                  |
| suite   | 21:9  | "The same characters as the reference images, each exactly as they look there. <cast lines>. They stand side by side around the <light>, which sits in the centre; <one action each, tied to the product>. The <light> lights all faces; black space between and around them." |
| closing | 4:3   | "<Name> resting on the seabed at night, arms folded under, eyes half closed, content. The <light> sits on the sand beside it, turned down low, a small warm pool of light; everything else is pure black."                                                                   |
| mark    | 1:1   | "A tiny app-icon style mark: just <Name>'s head and eyes with one small arm holding up the glowing amber <light> at the top right, simplified for display at 40 pixels, centred, filling most of the square."                                                                |

Product scenes are written the same way; name objects by shape and material, never by what is
written on them. "A small rectangular translucent card, like a thin frosted glass tile" renders;
"a card titled Migrate to passkeys" renders a card with garbage text.

## What to pass as references

- First render (the hero): no references. Words only, so nothing from another site leaks in.
- Every later scene: the promoted hero candidate, so lantern, eyes and surfaces match.
- Group scene: the hero plus each supporting character's own first scene.
- Never a sibling or reference site's image. A mascot the person says this product already owns is
  the one exception.

Pro and newer tiers read reference images; `standard` silently ignores them.

## Re-roll guide

| Symptom                   | Add to the scene line                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| glow touches the edge     | "The glow fades to pure black well inside the frame; the image edges are pure black."                             |
| two light sources         | "There is no other light: no window, no sun rays, no caustics, no second lamp."                                   |
| a floor appeared          | "No floor, no sand, no horizon: the character floats in black water."                                             |
| text appeared             | "No letters, no numbers, no symbols anywhere in the image."                                                       |
| character looks different | pass the promoted hero as the first reference and say "the same character as the reference, same eyes, same skin" |
| too dark to read          | "The lantern is brighter and closer to the face; the face is fully lit."                                          |

## Sizes that come back

The `pro` endpoint returns about 1200 px on the long side regardless of `--resolution` (4:3 →
1200×896, 16:9 → 1200×675, 21:9 → 1200×514, 1:1 → 1024×1024, 3:4 → 896×1200), as JPEG. Nano
Banana 2.1 (`gemini-nano-banana-2.1`) measured the same for 4:3 and 1:1 and 1584×672 for 21:9. That is
enough for a 600 px display slot at 2×; for a full-bleed 1440 stage, render 16:9 and let the build
scale with the glow masked.
