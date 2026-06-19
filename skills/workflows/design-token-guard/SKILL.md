---
name: design-token-guard
version: 1.0.1
composes_with: ["orchestrator", "frontend-agent", "render-sanity", "ux-review", "code-review-agent", "sync-skills"]
description: >-
  Source-level gate that prevents inline styles and hardcoded CSS from
  bypassing a project's design-token system. Use whenever frontend work touches
  colors, styling, or themes — before committing or declaring a UI task done,
  when auditing for hardcoded hex/rgb/inline styles, when setting up enforcement
  so inline CSS can't slip in again, or as an orchestrator/agent wave-gate.
  Trigger on: "inline CSS", "inline styles", "hardcoded colors", "hardcoded
  hex", "style={{}}", "theme/token drift", "design tokens", "we keep shipping
  inline styles", "lint for tokens", "why did this get through review".
  Framework- and stack-agnostic (React/JSX, Vue, Svelte, Angular, Astro, HTML;
  CSS variables, SCSS/Less, JS theme objects, design-token JSON) — it
  auto-discovers the project's tokens, so it is NOT specific to any one repo or
  to Tailwind. Don't skip it because a visual/render review passed: render gates
  can't see a hardcoded color — it renders identically to the token.
---

# design-token-guard

## The problem this solves

A hardcoded color renders *identically* to the token it should have used.
`style={{ background: "#07090c" }}` and `style={{ background: "var(--tl-tooltip)" }}`
produce the same pixels. So every **render-level** gate — visual review, e2e,
screenshots, "console is clean" — passes a component that has silently bypassed
the design system. The violation only exists in **source**.

That is why inline styles and hardcoded CSS accumulate invisibly until someone
eyeballs the code weeks later and burns hours on a token refactor. The fix is a
**source-level gate**: a deterministic check that reads the diff for styling
that bypasses the token system, run *before* the code is declared done, and
wired into the repo so it can't regress.

This skill is that gate. It does two things:

1. **Audit** — run the bundled checker (`scripts/check_design_tokens.py`) to find
   every inline style and hardcoded color, each mapped to the exact token to use.
2. **Enforce** — scaffold the check into the repo (config + ESLint rule +
   pre-commit hook + `lint:tokens` script) so the gate runs on every commit/CI,
   not just when an agent remembers to look.

It is **dynamic**: it auto-discovers whatever token system the project already
uses and derives the rules from it. TruthLens and a vanilla Vue app are two
*configs* of one skill, not two skills.

## Step 1 — Audit

Run the checker from the project root. It needs no flags for a first pass:

```bash
python3 <skill-dir>/scripts/check_design_tokens.py --root .
```

What it does automatically:
- **Discovers the token source** — scans for CSS custom properties
  (`--name: …`), SCSS/Less vars (`$name`, `@name`), JS/TS theme objects, or
  design-token JSON. From those it builds a `color-value → token` map.
- **Scans the source tree** (`.tsx/.ts/.jsx/.js/.vue/.svelte/.astro/.html`),
  skipping `node_modules`, build dirs, config files, and the token files
  themselves.
- **Reports** each finding as `file:line:col`, the offending snippet, and — when
  the literal matches a declared token — the exact fix:

  ```
  no-hardcoded-color (error) — 2
    src/components/schedule/EventBar.tsx:69:17
      fill="#0E1116"
      → hardcoded color #0E1116 is var(--tl-bg-0)  ·  use var(--tl-bg-0)
  ```

Useful flags:
- `--staged` — only git-staged files (this is what the pre-commit hook uses).
- `--json` — machine-readable output for a gate/CI to parse (`{ ok, summary, findings }`).
- `PATHS…` — limit to specific files/dirs (e.g. just the component you changed).
- `--config <path>` — explicit config location.

Exit code is `1` when there are **error**-severity findings, `0` when clean — so
it drops straight into a gate or CI step.

## Step 2 — Interpret and fix

Two outcomes per color finding, and they need different fixes — don't blur them:

- **"… is `var(--token)`"** — the literal duplicates an existing token. Replace
  it with the token reference. Mechanical and safe.
- **"… is not a declared token"** — the color was never tokenized. This is the
  more important signal: either it's a genuinely new design value (add it to the
  token source with a real name, then reference it) or it's an off-palette
  mistake (use the nearest existing token). Don't paper over it by leaving the
  literal — that's how palettes rot.

For `no-inline-style` findings, move the value into a token or a utility class.
Inline styles whose values are all dynamic (`var(--…)`, JS expressions) are
**allowed** by default — the rule fires on hardcoded literals, not on the
mechanism. Use `"inlineStyleMode": "strict"` only if the project bans inline
style attributes outright.

## Step 3 — Enforce (scaffold into the repo)

A one-time audit doesn't stop regression. Wire the gate into the repo so it runs
without anyone remembering. Read `references/scaffolding.md` for the full
procedure; the short version:

1. **Write `.design-guard.json`** at the repo root (template:
   `assets/design-guard.config.json`). Set `tokenSources` explicitly so
   discovery is deterministic in CI, and turn on any project-specific rules.
2. **Add the checker to the repo** — copy `scripts/check_design_tokens.py` into
   the project's `scripts/`, or reference the skill path. Add a script:
   `"lint:tokens": "python3 scripts/check_design_tokens.py --root ."`.
3. **Pre-commit hook** — install `assets/pre-commit` (runs `--staged`, blocks the
   commit on error-severity findings). Wire via Husky/lefthook if present, else a
   plain `.git/hooks/pre-commit`.
4. **ESLint editor-time subset** — merge `assets/eslint-tokens.snippet.mjs` into
   the repo's flat config (create `eslint.config.mjs` if absent). ESLint gives
   in-editor squiggles for the patterns it expresses well (inline-style literals,
   forbidden radius/partisan-color classes). The Python checker stays the
   authority — it's the only layer that can do the `value → token` mapping, so
   pre-commit/CI run *that*, and ESLint is fast feedback, not the source of truth.
5. **CI** — add a `lint:tokens` step to the pipeline (`assets/ci-step.yml` shows a
   GitHub Actions example).

Tell the user which layers you installed and which you skipped (e.g. "no Husky
here, used a raw git hook").

## The rule set

Two **universal** rules, on by default (these are the "no inline CSS" core):

| rule | catches | default |
|---|---|---|
| `no-hardcoded-color` | `#hex`, `rgb()/rgba()`, `hsl()/hsla()` literals anywhere a token belongs — inline styles, SVG `fill`/`stroke`, JS color strings, Tailwind arbitrary `[#…]` | error |
| `no-inline-style` | `style={{…}}` / `style="…"` / `:style` / `[style]` carrying hardcoded literals (React/Vue/Svelte/Angular/HTML) | warn |

A **project-specific library**, off by default — opt in via config when a repo
has these conventions:

| rule | catches |
|---|---|
| `no-class-in-svg` | utility/Tailwind classes on `<svg>` primitives (`rect`, `path`, `g`, …) where styling should be token attributes |
| `restricted-radius` | border-radius above `maxRadiusPx`, or `rounded-{md,lg,xl,…}` classes |
| `forbidden-colors` | configured regexes — banned second accent, partisan red/blue, etc. |
| `no-arbitrary-tailwind` | Tailwind arbitrary *values* — `text-[10px]`, `max-w-[1100px]`, `leading-[1.75]` — that bypass the spacing/type scale. Arbitrary *colors* (`border-[rgba(…)]`) are already caught by `no-hardcoded-color`, so this rule skips them. `*-[var(--token)]` is allowed. |

Each rule's severity is `"error" | "warn" | "off"`. Errors fail the gate
(exit 1); warnings report but pass. Full config reference and per-rule notes:
`references/config.md`.

## Using it as an agent / orchestrator gate

When a frontend build runs under an orchestrator or agent team, this is a **hard
source-level wave-gate**, complementary to the render-level gates (render-sanity,
ux-review) — those check pixels, this checks source, and a build needs both:

- A **frontend-agent** runs `--json` against the files it changed *before*
  reporting done; error-severity findings mean the task isn't done.
- The **orchestrator** runs it at the wave gate alongside typecheck/test. Parse
  `summary.errors`; non-zero blocks the wave and routes back to the owning agent.

See `references/wiring-into-orchestrator.md` for the exact gate snippet and how
this plugs into the orchestrator's Definition of Done.

## Reference files

- `references/config.md` — full `.design-guard.json` schema, every field, per-rule notes, and adapting to non-CSS-variable token systems (SCSS, JS theme, Style Dictionary).
- `references/scaffolding.md` — step-by-step repo enforcement: config, hook, ESLint, CI, with the Husky/lefthook/raw-hook decision.
- `references/wiring-into-orchestrator.md` — the agent self-check + orchestrator wave-gate snippets, and the Definition-of-Done line this closes.
