# The extraction convention

A gate is only fair if it points at a written rule. This is that rule — short and
citable, so "use well-named classes" is a standard, not an after-the-fact gripe.

## The rule

> When the same combo of **4+ utility classes** appears **3+ times**, it has earned
> a name. Extract it into a named class or a component; don't paste it a fourth
> time.

Thresholds are the gate's defaults (`minUtilities` 4, `minRepeats` 3) and are
tunable per project. The *reasoning* matters more than the numbers: a one-off
utility string is fine; a combo you keep retyping is an unnamed concept. Naming it
makes the markup read as intent (`<label class="field-label">`) instead of soup
(`<label class="block font-mono text-[10px] text-muted uppercase tracking-wider">`),
and means the next visual tweak happens in one place, not nine.

## How to extract (pick what fits the stack)

| stack | extraction |
|---|---|
| Tailwind + CSS | `@layer components { .field-label { @apply block font-mono text-[10px] text-muted uppercase tracking-wider; } }` |
| React + variants | a `cva`/`tv` recipe, or a small `<FieldLabel>` component wrapping the classes |
| Vue / Svelte | a component with the classes in its template, or a scoped class |
| plain CSS / SCSS | a semantic class in the stylesheet; reference it by name in markup |

Prefer a **component** when the element has behavior or structure, a **named class**
when it's pure styling. Either way the combo lives in one place.

## What NOT to over-extract

The goal is fewer repeated *concepts*, not zero utilities. Don't extract:

- **One-offs.** A unique layout used once reads fine inline. The gate already
  ignores anything under `minRepeats`.
- **Trivial pairs.** `flex gap-2` is not a concept worth a name (below
  `minUtilities`).
- **Genuinely divergent strings.** If three elements share four classes but each
  adds different ones, extract the shared base and compose — don't force one rigid
  class that needs overrides everywhere (that's how `abstraction-defeat` starts).

Extraction is about naming the thing you keep repeating, then composing variations
on top — not about banning utilities.
