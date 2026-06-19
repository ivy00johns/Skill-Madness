# `.design-guard.json` configuration reference

The checker runs with zero config (it auto-discovers the token source and uses
sensible defaults). A `.design-guard.json` at the repo root makes behavior
deterministic and turns on project-specific rules. User config is shallow-merged
over the defaults; the `rules` object is merged key-by-key.

## Full schema

```jsonc
{
  // Token source files. Empty/omitted => auto-discover (css/scss/less/json with
  // token-ish names or many custom properties). Set this explicitly in CI so
  // discovery never drifts. Paths are relative to the repo root.
  "tokenSources": ["src/styles/tokens.css"],

  // File extensions scanned for violations.
  "scanExtensions": [".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte", ".astro", ".html"],

  // Directory names never walked.
  "ignoreDirs": ["node_modules", ".git", ".next", "dist", "build", "out", "coverage"],

  // Skip any file whose path contains one of these substrings.
  "ignorePathContains": [".config.", ".d.ts"],

  // Per-rule severity: "error" | "warn" | "off". Errors set exit code 1.
  "rules": {
    "no-hardcoded-color": "error",
    "no-inline-style": "warn",
    "no-class-in-svg": "off",
    "restricted-radius": "off",
    "forbidden-colors": "off",
    "no-arbitrary-tailwind": "off"
  },

  // "literal" (default): no-inline-style fires only on inline styles carrying a
  //   hardcoded literal; dynamic/token inline styles are allowed.
  // "strict": fires on every inline style attribute, period.
  "inlineStyleMode": "literal",

  // restricted-radius threshold (px) and rounded-* class gate.
  "maxRadiusPx": 2,

  // forbidden-colors: regexes matched against each source line.
  "forbiddenColors": [],

  // Also scan .css/.scss/.less files for hardcoded colors? Usually false — that's
  // where colors legitimately live. Turn on if component-level stylesheets
  // (CSS modules, *.module.scss) should be token-only too.
  "scanStyleSheets": false
}
```

## Per-rule notes

### `no-hardcoded-color` (universal)
Flags `#hex` (3/4/6/8-digit), `rgb()/rgba()`, `hsl()/hsla()` literals across the
scanned files. When the normalized value matches a declared token, the message
names the exact token and suggests `var(--token)`. When it doesn't, it flags the
color as **undeclared** — the higher-value signal, because it means the palette
has an untracked value. Color literals inside comments and the token sources
themselves are ignored.

### `no-inline-style` (universal)
Catches `style={{…}}` (JSX), `style="…"`, `:style`, and `[style]` (Vue/Svelte/
Angular/HTML) attributes. Default `"literal"` mode fires only when the attribute
carries a hardcoded literal — color literals are owned by `no-hardcoded-color`
(more specific, has the token suggestion), so this rule's distinct contribution
in literal mode is hardcoded **dimensions** and mixed literals. Switch to
`"strict"` to forbid inline styles outright.

### `no-class-in-svg` (opt-in)
For projects whose convention is "SVG is styled with token attributes, never
utility/Tailwind classes." Flags `className`/`class` carrying utility-looking
tokens on `<rect>`, `<path>`, `<g>`, `<circle>`, etc.

### `restricted-radius` (opt-in)
Flags `rounded-{md,lg,xl,2xl,3xl,full}` classes and `border-radius: Npx` where
`N > maxRadiusPx`. For editorial/sharp design systems with a hard radius cap.

### `forbidden-colors` (opt-in)
Each entry is a regex tested against every line. Use for a banned second accent,
partisan red/blue, or any class/value the project forbids. Example:
```json
"forbiddenColors": ["\\b(?:text|bg|border)-(?:red|blue)-\\d{3}\\b", "#ff0000"]
```

### `no-arbitrary-tailwind` (opt-in)
Flags Tailwind **arbitrary-value** utilities — `text-[10px]`, `max-w-[1100px]`,
`leading-[1.75]`, `pb-[1px]` — that hardcode a value off the spacing/type scale.
For projects that want strict scale discipline. Deliberately **off by default**:
many design systems (and design-handoff ports) use specific px values on purpose,
so blanket-flagging them is noise unless the project opts in. It skips two cases
that are not violations: arbitrary *colors* (`border-[rgba(…)]`, owned by
`no-hardcoded-color` which has the token suggestion) and token refs
(`text-[var(--token)]`). Semantic utilities that map to tokens via the Tailwind
config (`text-fg-2`, `border-ink-3`) have no brackets and are never flagged.

## Adapting to non-CSS-variable token systems

The checker derives its `value → token` map from whatever token sources it parses:

- **CSS custom properties** (`--name: value;`) → suggestion is `var(--name)`.
- **SCSS / Less** (`$name`, `@name`) → suggestion names the variable; reference it
  the way your build expects (`$name`).
- **JS/TS theme object** (`{ name: '#hex' }`) → the key is surfaced as the token
  name; reference it through your theme accessor.
- **Design-token JSON** (Style Dictionary `{ "color": { "bg": { "value": "#…" } } }`)
  → the dotted path becomes the token name.

If a project has multiple sources (e.g. a CSS file *and* a JSON), list them all
in `tokenSources`; the first source to define a given color value wins the
suggestion.
