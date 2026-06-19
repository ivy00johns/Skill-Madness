# Scaffolding repo enforcement

A one-time audit doesn't prevent regression. These steps wire the gate into the
repo so it runs on every commit and in CI — the difference between "we cleaned it
up once" and "it can't come back." Install the layers that fit the repo; tell the
user which you installed and which you skipped and why.

## 1. Write `.design-guard.json`

Copy `assets/design-guard.config.json` to the repo root and tailor it:
- Set `tokenSources` to the project's real token file(s) — explicit, not
  auto-discovered, so CI is deterministic.
- Turn on any project-specific rules (`no-class-in-svg`, `restricted-radius`,
  `forbidden-colors`) the repo's conventions call for. Leave them `off` otherwise.
- Decide `inlineStyleMode`: `"literal"` (allow dynamic inline styles, forbid
  hardcoded ones) for most repos; `"strict"` if the design system bans inline
  styles entirely.

## 2. Vendor the checker + add an npm script

Copy `scripts/check_design_tokens.py` into the repo's `scripts/` (so CI/hook
don't depend on the skill being installed on the runner). Add to `package.json`:

```json
{
  "scripts": {
    "lint:tokens": "python3 scripts/check_design_tokens.py --root ."
  }
}
```

Confirm it runs: `npm run lint:tokens` (or `pnpm lint:tokens`). For a non-Node
repo, just document the `python3 scripts/check_design_tokens.py` invocation.

## 3. Pre-commit hook

The hook scans staged files only, so it's fast and scoped. Choose the wiring that
matches the repo:

- **Husky present** (`.husky/`): add to `.husky/pre-commit`:
  ```sh
  python3 scripts/check_design_tokens.py --root . --staged --quiet || exit 1
  ```
- **lefthook present** (`lefthook.yml`): add a command:
  ```yaml
  pre-commit:
    commands:
      design-token-guard:
        run: python3 scripts/check_design_tokens.py --root . --staged --quiet
  ```
- **Neither** (raw git hook): `cp assets/pre-commit .git/hooks/pre-commit &&
  chmod +x .git/hooks/pre-commit`. Note this isn't version-controlled — prefer
  Husky/lefthook for team repos; the raw hook is fine for a solo repo.

The hook blocks on error-severity findings; `--no-verify` is the documented
escape hatch for an intentional exception.

## 4. ESLint editor-time subset

Merge `assets/eslint-tokens.snippet.mjs` into the repo's `eslint.config.mjs`
(create one if absent). This gives in-editor squiggles for inline-style color
literals — fast feedback while typing. It's intentionally a subset: ESLint can't
map a hex back to its token, so it can't produce the "use `var(--tl-bg-0)`"
suggestion. The Python checker remains the authority; ESLint is a convenience
layer. Don't let the two definitions drift — when you change a rule, change the
Python checker first and treat ESLint as best-effort mirroring.

For Vue/Svelte/Angular template styles, skip ESLint and rely on the pre-commit
checker, which is template-aware via regex.

## 5. CI step

Add `assets/ci-step.yml`'s step to the pipeline so a bypassed local hook
(`--no-verify`, or a contributor without the hook installed) still gets caught on
the server. The checker needs only a Python runtime.

## 6. Seed cleanup vs. ratchet

If the repo already has many violations (a legacy codebase), a hard gate will
block every commit. Two options — pick with the user:
- **Clean then gate** — fix the existing findings in one pass (the checker's
  `value → token` suggestions make most of them mechanical), then turn the gate
  to `error`. Best when the backlog is small.
- **Ratchet** — set `no-hardcoded-color` to `error` only on changed files (the
  pre-commit `--staged` path already does this) while the full-tree CI run stays
  a `warn`-level report until the backlog is burned down. Stops new debt
  immediately without blocking on old debt.

State which you chose in the handoff so the user isn't surprised by the gate's
strictness.
