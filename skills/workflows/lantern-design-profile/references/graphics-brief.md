# Graphics brief per section

The family's base set is five scenes. A site adds at most three product-specific ones. Every
scene is rendered on black with the character's light as the only key light; see `profile.md`
("Graphics") for the render style and `site-character-art` for prompts and the inventory.

| Scene     | Ratio       | Light                                                      | Character                                                                     | Alt text pattern                                                            |
| --------- | ----------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `hero`    | 4:3         | the light held up, front-right, glow fills the right third | three-quarter view, facing the reader, one arm/fin raised with the light      | "<Name>'s mascot, a <colour> <creature> holding a glowing amber <light>."   |
| `moment`  | 16:9 or 4:3 | the light moves with the character across the stage        | the character doing the product's job (swims the map, holds the cards)        | "<Name> <does the job>."                                                    |
| `suite`   | 21:9        | the lead's one light, centred                              | the site's own cast together, sharing the lead's light                         | "<Lead>, <supporting> and <supporting> gathered around the <light>."       |
| `closing` | 4:3         | the light turned low                                       | at rest, or looking up at the light                                           | "<Name> resting beside the <light>."                                        |
| `mark`    | 1:1         | a dot of amber                                             | head and eyes only, simplified for 36–40px                                    | decorative, empty alt                                                       |

Product-specific scenes (examples of the *shape* of a scene from two sibling sites; never reuse
their characters or scenes):

| Site   | Scene      | Ratio | What it shows                                                                  |
| ------ | ---------- | ----- | ------------------------------------------------------------------------------ |
| Fathom | `map`      | stage | contour map drawn in code; the fish swims it; labels fade by zoom level        |
| Andon  | `board`    | 4:3   | six arms holding translucent cards, one amber ("needs you")                    |
| Andon  | `machines` | 16:9  | arms reaching to three small machines on the seabed, each with one amber light |
| Andon  | `cord`     | 3:4   | an arm pulling the cord that lights the lantern                                |

Rules that keep the set coherent:

1. **One light per site.** The lead carries it; supporting characters share it. Never add a second lamp, a window, caustics or sun rays.
2. **The glow fades to black inside the image.** No image reaches its edge lit; the build masks
   the edges anyway, but a lit edge shows the rectangle.
3. **Same render language across scenes.** Pass the hero image as a reference to every later
   scene so the surface, eyes and lantern match.
4. **No text in images.** Labels, card titles and names are HTML over the image.
5. **Alt text names the character and the action**, in the product's nouns, one sentence.
