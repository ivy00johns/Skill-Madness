# class-extraction-guard configuration

All behavior is controlled by a `.class-guard.json` at the project root (or a path
passed with `--config`). Every field is optional; unset fields fall back to the
defaults below. Pass `--config none` semantics by simply not having the file.

## Fields

| field | default | meaning |
|---|---|---|
| `scanExtensions` | `.tsx .ts .jsx .js .mjs .cjs .vue .svelte .astro .html` | file types scanned |
| `ignoreDirs` | `node_modules .git .next dist build out coverage .turbo .vercel __pycache__ .svelte-kit .cache storybook-static` | directories never walked |
| `minUtilities` | `4` | a class string needs at least this many tokens to be considered at all — short strings (`flex gap-2`) are noise, not soup |
| `minRepeats` | `3` | how many distinct call-sites a combo must appear in before `repeated-class-string` fires |
| `maxUtilities` | `12` | threshold for `long-class-string` (a single over-stuffed element) |
| `allowlist` | `[]` | exact class strings to never flag (order-independent). Escape hatch for a combo you've deliberately chosen not to extract |
| `namedClassPattern` | `""` | regex marking your project's named/`@apply` classes (e.g. `"^(lab|ui)-"`). Required for `abstraction-defeat` |
| `rules` | see below | severity per rule: `"off"`, `"warning"`, or `"error"` |

## Rules and severity

```json
"rules": {
  "repeated-class-string": "warning",
  "long-class-string": "off",
  "abstraction-defeat": "off"
}
```

- **`repeated-class-string`** — the strong signal: the same combo copy-pasted
  around. On by default at `warning`.
- **`long-class-string`** — a single element with `maxUtilities`+ classes. Off by
  default because a genuinely complex one-off element is sometimes fine; turn it on
  when you want pressure toward components.
- **`abstraction-defeat`** — utilities glued onto an element that already has a
  named class (`lab-header flex items-center justify-between gap-2 !py-1`), which
  quietly defeats the abstraction. Needs `namedClassPattern`. Off by default.

Severity drives the exit code: any `error`-severity finding → exit 1 (blocks a
gate); `warning` findings report but exit 0. The summary always reports both
counts so a wave-gate reads `summary.errors`.

## Recipe: non-blocking adoption (default)

Ship the file as-is (or omit it). The gate reports `repeated-class-string` as
warnings, never blocks. Good for an existing codebase you want visibility on.

## Recipe: ratchet on an existing codebase

```json
{ "rules": { "repeated-class-string": "error" } }
```
```bash
python3 check_class_extraction.py --root . --write-baseline   # snapshot existing soup
# commit .class-guard-baseline.json — now only NEW combos are errors and block.
```

## Recipe: greenfield, hard-gated from commit #1

Scaffold at the bootstrap wave (see `scaffolding.md`) with `repeated-class-string:
"error"` and **no** baseline. Violation #1 fails at commit #1 — the soup never
accumulates. This is the placement that actually prevents the problem rather than
cleaning it up later.

## Recipe: stricter project with a named-class system

```json
{
  "rules": { "repeated-class-string": "error", "abstraction-defeat": "warning" },
  "namedClassPattern": "^(lab|ui|app)-",
  "minRepeats": 2
}
```
