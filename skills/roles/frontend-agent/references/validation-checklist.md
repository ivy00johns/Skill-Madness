# Frontend Agent Validation Checklist

Run ALL before reporting done. Fix failures. Adapt commands for your package manager (npm/pnpm/yarn).

> **The single most important gate is below: actually run the typecheck and any tests the package defines.** Grep-based validation (e.g., "all 9 routes are wired" by counting matches) cannot catch missing dependency declarations, broken type narrowing, or runtime errors. If `tsc --noEmit` reports errors, you are not done.

## Build Verification

Run the project's own scripts for your package — whatever the stack provides:

| Stack | Typecheck | Build | Lint | Test |
|---|---|---|---|---|
| Node (pnpm workspace) | `pnpm --filter <pkg> run typecheck` | `pnpm --filter <pkg> run build` | `pnpm --filter <pkg> run lint` | `pnpm --filter <pkg> run test` |
| Node (npm / yarn) | `npm run typecheck` (in package dir) | `npm run build` | `npm run lint` | `npm test` |
| Elixir (Phoenix LiveView) | `mix compile --warnings-as-errors` | `mix assets.deploy` | `mix credo` | `mix test` |
| Ruby (Rails views) | — | `bundle exec rake assets:precompile` | `bundle exec rubocop` | `bundle exec rspec` |
| Python (Streamlit / Reflex / templates) | `mypy .` | `python -m build` (if applicable) | `ruff check .` | `pytest` |

Common failure (Node workspaces): `Cannot find module '@<scope>/<sibling>'`. The sibling is referenced in an `import` statement but NOT declared in your `package.json` `dependencies`. Add it as `"@<scope>/<sibling>": "workspace:*"` — that's what tells pnpm/npm/yarn to symlink the sibling into `node_modules`. Same principle in Python: `pip install -e ./packages/sibling` won't happen unless the manifest pins it.

## Imports must resolve to declared deps

This applies wherever the language has an explicit dependency manifest (Node `package.json`, Python `pyproject.toml`, Ruby `Gemfile`, Go `go.mod`, Rust `Cargo.toml`). Every non-relative import in your source must correspond to a declared dependency.

```bash
# Node example — list every non-relative import in src/.
grep -rhE '^import .* from "([^.][^"]+)"' src/ \
  | sed -E 's/.*from "([^"]+)".*/\1/' \
  | grep -v '^\.' \
  | sort -u

# Python example — every `import foo` and `from foo import …`.
grep -rhE '^(import |from )([a-zA-Z_][a-zA-Z0-9_]*)' src/ \
  | sed -E 's/^(import|from) ([a-zA-Z_][a-zA-Z0-9_]*).*/\2/' \
  | grep -v '^_' \
  | sort -u
```

For each entry, confirm it appears in the project manifest. **Workspace siblings — declare them explicitly.** Tooling will not auto-symlink a sibling unless your manifest lists it; the resulting "module not found" error looks mysterious until you remember to check.

## Cross-package CSS imports — JS-side, not `@import`

In a workspace where your frontend imports CSS from a sibling package (a design-system package, a shared tokens file, etc.), the `@import` directive inside a `.css` file does NOT reliably resolve through:

- the sibling package's `exports` map
- TypeScript path aliases (`@scope/sibling/*`)
- pnpm/npm/yarn workspace symlinks

PostCSS-import follows the package's `main` field and naively concatenates subpaths; Vite respects the exports map but its CSS plugin doesn't fall back gracefully when your `.css`-extensioned subpath isn't an explicit key. Combinations break in non-obvious ways: `@import '@scope/ui/tokens'` resolves to `<scope/ui/main>/tokens` instead of looking up the export, then errors with `ENOTDIR` or `ENOENT` against a fake path.

**The reliable pattern: import the CSS from your TypeScript/JS entry point, not from a CSS file.** Vite handles JS-side CSS imports natively and the cross-package resolution Just Works.

```ts
// ✅ apps/web/src/main.tsx — JS-side CSS import via relative workspace path
import '../../../packages/ui/src/tokens.css';
import './styles/global.css';
```

```css
/* ❌ apps/web/src/styles/global.css — don't try to @import a workspace sibling */
@import '@scope/ui/tokens';            /* breaks: postcss-import + main field */
@import '@scope/ui/src/tokens.css';    /* breaks: exports map filters by key */
@import '../../../packages/ui/src/tokens.css';  /* breaks: postcss-import cwd */
```

The relative path inside a JS import is stable because Vite resolves it against the importing file's directory. CSS imports in CSS files are not the same — they go through a different resolver with different cwd semantics.

If you genuinely need the CSS imported from another CSS file (e.g., a Tailwind layer), use Vite's plugin layer (`vite-plugin-postcss-import` with a custom resolver) — but for 95% of cases, importing from `main.tsx` is the right answer.

## Dev Server

```bash
npm run dev             # Starts without errors, no console errors in browser
```

## API Contract Compliance

```bash
# Find all API calls — verify each matches the contract
grep -rn "fetch\|axios\|\.get\|\.post\|\.put\|\.delete" src/ \
  --include="*.ts" --include="*.tsx" --include="*.jsx" \
  --include="*.vue" --include="*.svelte"
```

For each call found: URL matches contract exactly, HTTP method matches, request body shape matches, response destructuring matches contracted shape, errors handled per error envelope.

## Environment Variable Audit

```bash
# Zero hardcoded API URLs in source
grep -rn "localhost\|127\.0\.0\.1" src/ \
  --include="*.ts" --include="*.tsx" --include="*.jsx" \
  --include="*.vue" --include="*.svelte" \
  | grep -v "node_modules" | grep -v ".env"
# Each match should reference an env variable, not a literal URL
```

## CORS Verification

If the backend is running: open dev tools, Network tab, trigger an API call, verify zero CORS errors.

If the backend is not yet available: flag CORS verification as **BLOCKED** in your completion report. Do NOT skip it silently.

## Route Verification

- Every defined route renders without errors
- 404/not-found route displays for undefined paths
- Protected routes redirect unauthenticated users (if auth is in contract)
- Browser back/forward navigation works correctly

## Visual Verification

- Primary user flow works end-to-end
- Empty states display correctly
- Loading states appear during API calls
- Error states appear when backend is down
- Zero console errors or warnings during primary user flow

## Responsive Verification

The full responsive playbook is in `references/mobile-responsive.md`. The bar below is the minimum gate before reporting done — meet all of it, or do not report done.

### 1. Actually render at both widths

A `@media` rule in CSS proves nothing if an inline style is overriding it. Open the page at both widths and look. Capture a screenshot at each (Playwright is cheap if available; browser devtools otherwise) and include the path in your completion report so reviewers can verify.

- **375 × 667** (mobile, e.g. iPhone SE) — no horizontal scrollbar; tap targets look ≥ 44 × 44; text wraps without clipping; navigation is reachable (hamburger works if collapsed); hero / primary CTA visible at the top.
- **1440 × 900** (desktop laptop) — layout uses the extra width; no awkward giant gaps; nothing clipped.

### 2. Viewport meta tag is present

```bash
grep -rE '<meta[^>]+name="viewport"[^>]+width=device-width' \
  --include='*.html' --include='*.php' --include='*.erb' --include='*.tsx' --include='*.jsx' .
```

Every served page needs `<meta name="viewport" content="width=device-width, initial-scale=1">` in `<head>`. Without it the page renders at fake-desktop zoom on phones and none of your responsive rules matter.

### 3. No hardcoded `width: <px>` on layout containers

Hardcoded pixel widths on wrappers, sections, cards, columns, or any container that holds other content lock the layout off mobile. Tokens (icons, button heights, hairlines) are fine.

```bash
# Surface every fixed-pixel width declaration in CSS for human review.
# Expect to see most matches in token files (icon-size, button-height, etc.)
# and very few in layout files. Investigate any match in a layout-shaped file.
grep -rnE 'width:\s*[0-9]+(px|rem)\s*;?' \
  --include='*.css' --include='*.scss' --include='*.module.css' . \
  | grep -viE '(icon|btn|button|avatar|chip|badge|border|hairline|--w-)'
```

For each remaining match, replace with the size primitive that matches the container's intent — `max-width`, `clamp()`, `minmax()`, or `flex-basis`. See the primitives table in `references/mobile-responsive.md`.

### 4. Inline `style=` is near-zero for layout

Layout CSS belongs in stylesheets; inline `style=` beats media queries on specificity and silently breaks the responsive layer. A handful of inline styles feeding CSS custom properties (e.g. `style="--progress: 72%"`) is fine; inline `display: grid` / `width: …` / `flex: …` is not.

```bash
grep -rno 'style=' \
  --include='*.php' --include='*.erb' --include='*.html' \
  --include='*.html.heex' --include='*.jsx' --include='*.tsx' . \
  | wc -l
```

Read each match if the count is non-trivial. Move every layout/sizing/grid/flex inline style into a class.

### 5. `!important` count is near-zero

`!important` is an escape hatch, not a layout tool. A responsive stylesheet larger than its base stylesheet, or one that leans on `!important`, almost always means inline styles upstream are being clawed back.

```bash
grep -rn '!important' --include='*.css' --include='*.scss' . | wc -l
```

If the count is non-trivial, fix the source (remove the inline styles or fixed widths that prompted it) rather than adding more `!important`.

## Design-Token Discipline (source-level gate)

The grep in §4 above catches inline *layout* styles, but it can't see a hardcoded
**color** — `style={{ background: "#07090c" }}` renders identically to the token
it should have used, so it sails through every visual check. That class of bug
only exists in source, and it's how inline CSS accumulates until a painful manual
token refactor. Close it deterministically with the `design-token-guard` skill:

```bash
# Run against the files you changed. --json for a parseable verdict.
python3 ~/.claude/skills/design-token-guard/scripts/check_design_tokens.py \
  --root . --json <your changed files or dirs> > /tmp/dtg.json
python3 -c "import json;d=json.load(open('/tmp/dtg.json'));print('errors:',d['summary']['errors'])"
```

**Error-severity findings mean you are not done.** Each finding names the exact
fix — when the literal matches a declared token it suggests `var(--token)`; when
it doesn't, the color was never tokenized (add it to the token source or use the
nearest existing token — don't leave the literal). This is the source-level
complement to the render checks: a clean render does not certify token discipline.

## Class-Extraction Discipline (source-level gate)

design-token-guard catches the *wrong value* (a hardcoded color); it passes a
*correctly-tokenized* utility string even when that same 6-utility combo is pasted
inline for the ninth time. That copy-paste soup renders identically to an extracted
class, so no visual check sees it either — it only exists in source. Close it with
`class-extraction-guard`:

```bash
python3 ~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py \
  --root . --json <your changed files or dirs> > /tmp/ceg.json
python3 -c "import json;d=json.load(open('/tmp/ceg.json'));print('warnings:',d['summary']['warnings'],'errors:',d['summary']['errors'])"
```

When the same combo of 4+ utilities shows up 3+ times, extract it into a named
class (`@apply` / a `cva` variant / a shared component) per the skill's
`extraction-convention.md` — the markup should read as intent, not soup. Warnings
are informational by default; an error-severity finding (a project that set the
rule to block) means you are not done.

## Accessibility Verification

- Tab through every interactive element — focus indicator visible on each
- Every `<input>` has an associated `<label>` or `aria-label`
- Every `<button>` has descriptive text (not just an icon)
- Every `<img>` has meaningful `alt` text
- Loading and error states use `aria-live="polite"` or `role="status"`
- No keyboard traps — Tab/Shift+Tab can reach and leave every control
