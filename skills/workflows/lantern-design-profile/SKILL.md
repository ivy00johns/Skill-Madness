---
name: lantern-design-profile
version: 1.1.0
description: >-
  Write the design profile for a site in the lantern family (black water,
  amber light, one generated character carrying the only light, one hero
  moment): palette tokens, type scale, layout, motion and a graphics brief per
  section, as a file a build loads. The site gets its own cast and copy; only
  the styling language is shared. Use when a site should sit in the same
  visual family as tryfathom.dev, or on "black water and amber light", "lantern-lit site",
  "same family as the Fathom site".
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: ["docs/design-profile.md"]
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
composes_with:
  [
    "site-character-art",
    "marketing-site-build",
    "ui-brief",
    "nano-banana",
    "playwright",
  ]
spawned_by: []
---

# Lantern design profile

A **design profile** is the one file a site build loads before it writes any markup: the tokens,
the type scale, the layout rules, the motion rules and the graphics brief for every section. This
skill writes that file for sites in the lantern family, the visual world Dave built for
tryfathom.dev and that the PSci Labs suite (Fathom, Andon, Refactor) shares: a pure black page, an
amber scale for all text, and one generated character whose light source is the only key light on
the page. The character lights the copy; the copy is never lit by anything else.

The family is defined in `references/profile.md` (tokens, scale, rules, with the measured values
from the Fathom site). This skill's job is to **adapt** that family to one product, write the
result to `docs/design-profile.md` in the project, and hand it to `site-character-art` (which
produces the images) and `marketing-site-build` (which builds the page). Read `ui-brief` when the
ask is a general-purpose UI brief for an app; this skill is only for marketing sites in this family.

**Announce at start:** "Using lantern-design-profile to write the design profile for [site]."

## Instructions

1. **Read the family profile.** Read `references/profile.md` in full. Its tokens are the family;
   do not invent a second accent colour or a second font. What changes per site is listed under
   "What a site may change" there: the character, its light source, the character's own colour,
   the hero moment, the section beats and the copy.
2. **Ground it in the product.** Read the product's README or docs for its nouns (Fathom: pages,
   quests, the map; Andon: cards, runs, machines, the board). The hero moment and the four beats
   must be built from those nouns, not from generic SaaS claims. If research on the family already
   exists (screenshots and findings under some `docs/research/`), read it instead of capturing
   again; otherwise screenshot the sibling sites at 1440 and 390 with Playwright. **Borrow only the
   styling language**: black page, amber light, big generated character art, one hero moment, how
   much effect is on screen. Take no text, no image and no character from a sibling or reference
   site; the profile's "Borrowed / changed" list names the styling borrowed and nothing else.
3. **Invent the cast and its light.** One lead character who carries the only light, plus at most
   three supporting characters, all new and drawn from the product's own world, with two sentences
   on why they fit the product's job. Never reuse a character from a sibling or reference site:
   each sibling's mascot belongs to that site (the anglerfish and telescope fish to Dave's Fathom,
   the octopus to Andon, the nautilus to Refactor). Keep an existing mascot only when the person
   says this product already owns it. Supporting characters share the lead's light; they never
   carry a second one.
4. **Pick the one hero moment.** The family allows exactly one sticky, scroll-driven section per
   page. Name it and its four beats (each beat is a six-word heading plus one sentence). Every
   other section is static: heading left, paragraph right, one image.
5. **Write the graphics brief per section.** For each section, one line: scene, aspect ratio,
   what the light does, what the character does, the alt text. Use the scene list in
   `references/graphics-brief.md` as the starting set (hero, moment, suite, closing, mark) and add
   at most three product-specific scenes.
6. **Write `docs/design-profile.md`** using the template at the end of `references/profile.md`.
   Copy the token block verbatim, then fill in the per-site sections. Keep it under 200 lines: a
   build will load it whole.
7. **Check it before handing it on.** Run the checklist in `references/profile.md` ("Profile
   checklist"). A profile that passes names one lead (plus at most three supporting characters),
   one light, one hero moment, four beats, a scene per section with aspect ratios and alt text, the
   copy voice rules, and nothing copied from a reference site.

## What the profile is not

- Not a brand book: no logo rules, no tone-of-voice essay. Six copy rules, that's all.
- Not a component library: the family has a masthead, a pill field, a pill button, lit text and
  images on black. Anything else is a reason to ask whether the site is still in the family.
- Not the build: the profile says what; `marketing-site-build` decides how (static HTML, CSS
  custom properties, a few lines of JS for the light).

## Examples

### Example 1: a sibling site

**User says:** "Build a site for Refactor in the same family as the Fathom site."

**Actions:**

1. Read `references/profile.md`; screenshot tryfathom.dev at 1440 and 390 into `docs/research/`.
2. Read Refactor's README: it is the shared workspace agents and people dive into. Nouns:
   workspace, worktree, dive, Fibo the nautilus (already in the suite scene: keep it).
3. Light source: the nautilus shell glows from inside, so the light is the shell, not a lantern.
4. Hero moment: "the dive": a worktree opens, the agent and a person work in it, the PR surfaces.
5. Write `docs/design-profile.md` with the token block, the cast line, the four beats and six
   scenes with aspect ratios and alt text.

**Result:** `docs/design-profile.md`, ready for `site-character-art` and `marketing-site-build`.

### Example 2: a re-skin of an existing site

**User says:** "tryandon.dev is teal and busy; make it match tryfathom.dev."

**Actions:**

1. Screenshot both sites at 1440 and 390; write what the current site does well (its copy is
   product-specific) and what breaks the family (teal, white panels, fifteen keyframe animations).
2. The person confirms the octopus is Andon's own mascot (this is the same product's site), so it
   stays; it gets a paper lantern. For any other product, invent a new cast (step 3).
3. Reduce eleven sections to the family's shape: hero, one moment with four beats, three static
   sections, suite, closing.
4. Write the profile; list under "Borrowed / changed" what came from each site.

**Result:** a profile that reads as a sibling of the Fathom site, with Andon's own cast and moment.

## Triggering test

- Must trigger: "design profile for a site in the Fathom family", "black water, amber light,
  a character holding the only light", "make tryandon.dev look like tryfathom.dev".
- Must NOT trigger: "write a UI brief for the admin dashboard" (that is `ui-brief`), "generate a
  picture of an octopus" (that is `nano-banana` or `site-character-art`), "deploy the site"
  (`marketing-site-build`).

## Troubleshooting

### The profile keeps growing past 200 lines

**Cause:** section copy or prompt text is being written into the profile.
**Solution:** the profile holds one line per section (scene, ratio, light, action, alt). Prompts
belong in the graphics inventory `site-character-art` writes; copy belongs in the page.

### Two accents crept in

**Cause:** the product's own brand colour was promoted to a UI colour.
**Solution:** the product's colour lives only in the characters' skin, fur or feathers.
Text, fields, buttons and lines stay on the amber scale.

### The new site looks like a copy of the reference

**Cause:** a sibling's character, headline or scene was reused "to keep the family together".
**Solution:** the family is the styling language only. Replace the borrowed piece with one drawn
from this product's docs and this site's own cast; list the styling you borrowed, nothing else.

### The hero moment is a list of features

**Cause:** beats were written as capabilities rather than as one story told in four steps.
**Solution:** rewrite the beats as what happens to one thing (one quest, one card) from start to
end; a reader should be able to retell it.
