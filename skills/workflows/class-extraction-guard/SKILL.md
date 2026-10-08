---
name: class-extraction-guard
version: 1.1.1
composes_with: ["orchestrator", "frontend-agent", "design-token-guard", "render-sanity", "code-review-agent", "sync-skills"]
description: >-
  Source-level gate that catches utility-class soup — the same long run of
  utility classes (e.g. `flex items-center gap-1.5 text-fg-muted hover:text-accent`)
  copy-pasted inline across many files instead of extracted into a named class or
  component. Use whenever frontend work touches className/class markup: before
  committing or declaring a UI task done, when auditing for utility soup, when a
  Tailwind combo is repeated everywhere, or as an orchestrator/agent wave-gate.
  Trigger on: "utility soup", "repeated tailwind classes", "extract into named
  classes", "className duplication", "class string copy-pasted", "DRY up the
  styles", "class-extraction". Framework-agnostic (React/JSX, Vue, Svelte, Astro,
  HTML; clsx/cn/cva). Sibling to design-token-guard: it checks WHICH values
  styling uses (tokens vs hex), this checks HOW it's organized (extracted vs
  repeated) — invisible to render review since repeated utilities render
  identically.
compatibility: Read/edit/shell host; requires Python 3.9+ (stdlib only) to run scripts/check_class_extraction.py
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
---

# class-extraction-guard

## What this is

A deterministic, parse-once gate that flags **utility-class soup**: the same long
run of utility classes pasted inline across many call-sites instead of extracted
into a named class (`@apply` / a CSS component) or a shared UI component.

It exists because of a real gap. `design-token-guard` checks *which values*
styling uses — it catches a hardcoded `#07090c` that should be `var(--token)`. But
a string like `flex items-center gap-1.5 text-bone-faint hover:text-rune` uses
perfectly valid tokens, so design-token-guard passes it by construction. Repeat
that string 9× across the codebase and you have a maintenance problem the value
gate was never built to see. And because the repeated version *renders
identically* to an extracted one, the pixel gates (`render-sanity`, `ux-review`)
can't see it either. The duplication lives only in source — exactly in the seam
between the value gate and the pixel gates. This is the missing **organization**
gate that closes that seam.

| gate | reads | catches |
|---|---|---|
| render-sanity / ux-review | pixels | broken pages, dead links, stale data, visual regressions |
| design-token-guard | source | hardcoded colors / inline styles bypassing the token system |
| **class-extraction-guard** | source | **the same utility combo repeated inline instead of extracted** |

None subsumes the others. A UI build wants all three.

## When the checker can't run (no shell, or no file read)

The detector is the authority, but the gate is the **source scan**, not the
script binary. Degrade instead of declining — never report a clean pass you did
not observe:

- **Shell + file read (full host):** run `scripts/check_class_extraction.py` as
  below. A crash or a blocked inspection (exit 2) is never a clean pass.
- **File read, no shell:** apply the default rule by hand. Grep the changed
  source for class attributes (`class=`, `className=`, `:class`, `class:list`,
  and the class-string args to `clsx` / `cn` / `classNames` / `cva` / `tv` /
  `twMerge`), order-normalize the utility tokens in each string, and flag any
  normalized combo of ≥ 4 utilities that appears at ≥ 3 distinct call-sites —
  exactly the `repeated-class-string` rule the detector applies. Report each combo
  with its occurrences as `file:line`, the same shape the checker emits. Mark
  coverage partial where a file was unreadable.
- **No shell and no file read:** load the skill and report **every check
  BLOCKED** — you cannot name the repeated combos, so say so. Hand the next host
  the command and the thresholds (`minUtilities` 4, `minRepeats` 3). Do not
  invent findings, and do not decline the skill.

**BLOCKED is not a pass.** Whether the detector ran or you hand-scanned, any check
you could not perform is reported `BLOCKED` with its reason, and an unrun gate is
an uncleared gate — not a clean build.

## Quick start

Resolve `<class-guard-root>` from this host's actual installed skill resources, not a hardcoded Claude home.

```bash
# Human-readable report
python3 <class-guard-root>/scripts/check_class_extraction.py --root .

# JSON for a gate (same gate contract as design-token-guard: exit codes +
# .summary.errors / .summary.warnings — the JSON key shapes differ)
python3 <class-guard-root>/scripts/check_class_extraction.py --root . --json
#   -> { "summary": { "errors": 0, "warnings": 12, "files_scanned": 98 },
#        "findings": [ { "rule": "...", "file": "...", "line": 93, "count": 9,
#                        "string": "...", "occurrences": [...], "suggestion": "..." } ] }
```

Exit codes: **0** = no error-severity findings, **1** = error-severity findings,
**2** = usage/configuration or blocked-inspection error. `--staged` scans only git-staged files (for a
pre-commit hook). `--quiet` suppresses the human output.

## What it flags

| rule | default | fires when |
|---|---|---|
| `repeated-class-string` | **warning** | the same (order-normalized) class string of ≥ `minUtilities` (4) tokens appears in ≥ `minRepeats` (3) distinct call-sites |
| `duplicate-css-block` | off (opt-in; bootstrap sets error) | at least `minCssRepeats` simple class rules share `minDeclarations` identical ordered declarations in the same media/layer/supports scope |
| `long-class-string` | off (opt-in) | a single class string carries ≥ `maxUtilities` (12) tokens — a one-off mega-string worth splitting even unrepeated |
| `abstraction-defeat` | off (opt-in) | extra utilities are glued onto an element that already has a named/`@apply` class (needs `namedClassPattern` set) |

The default is intentionally just **one rule, at warning severity** — utility-soup
is a preference-y standard, so the gate informs by default and never blocks a
build on adoption day. Flip a rule to `error` (and scaffold it at the bootstrap
wave) when you want it to hard-gate a greenfield project from commit #1. See
`references/config.md` for every option.

## CSS declaration equivalence and shared source layout

The project-local frontend bootstrap sets `duplicate-css-block` to error. It scans plain CSS and inline `<style>` sources; renaming repeated blocks to unique/hash classes no longer hides identical declarations. Only equivalent **simple class selectors** in identical at-rule ancestry are grouped. Declaration order, fallback values and `!important` are retained; complex selectors, nested/preprocessor syntax and CSS-in-JS require manual review, not automatic equivalence claims. Rule fingerprints can be exempted only with a reasoned owner-approved `cssAllowlist` entry; utility baselines never suppress CSS duplicates.

`scripts/check_shared_layout.py --root . --json` uses the same class config/discovery and flags copied literal header/nav/footer markup across at least two authored source files. Extract one owning component/partial/include. It excludes generated build directories and script/style bodies; do not scan a static generator's published HTML as authored source. It is not a runtime component-ownership verifier or semantic near-duplicate detector. Intentional independent copies need a reasoned `sharedLayout.allowlist` fingerprint entry. Dynamic/framework composition still needs manual shell inspection.

Frontend-agent invokes the consented project bootstrap from design-token-guard **before** authoring, then runs all guards together on the full source tree. Resource absence, invalid config/baseline, git/read failure or missing explicit paths blocks inspection (exit 2), never clean success. Native teams/dispatch and independent QE remain unchanged; solo self-check is not independent review.

## Adopting on an existing codebase (ratchet mode)

A gate added *after* a fleet of agents has written the UI inherits a backlog —
which is why the default is non-blocking. To adopt without drowning in
pre-existing debt, record a baseline and only flag **new** duplication:

```bash
CEG=<class-guard-root>/scripts/check_class_extraction.py
python3 "$CEG" --root . --write-baseline   # snapshot today's soup
python3 "$CEG" --root . --json             # now reports only NEW combos
```

The baseline (`.class-guard-baseline.json`) is a set of normalized combo keys.
Burn it down over time; the gate stops the pile from growing in the meantime.

## Wiring into orchestrator / agent builds

This is the *organization* complement to design-token-guard's *value* gate, and it
wires in the same way (UI wave-gate + a Definition-of-Done line + a frontend-agent
self-check). The single most important placement detail: **scaffold it in the
bootstrap wave, before the first frontend-agent writes a line** — a gate retrofitted
after the UI exists can only ratchet, but one installed at commit #1 means the
soup never accumulates. See `references/wiring-into-orchestrator.md` and
`references/scaffolding.md`.

## The standard it enforces

A gate is only fair if it points at a written rule. `references/extraction-convention.md`
is the short, citable convention every finding references: *when the same utility
combo of 4+ classes shows up 3+ times, it has earned a name.* Ship it (or a project
copy) so "use well-named classes" is an actual standard, not an after-the-fact
complaint.

## Bundled resources

- `scripts/check_shared_layout.py` + `scripts/frontend_source.py` — small shared-source-chrome and conservative CSS extraction helpers.
- `scripts/check_class_extraction.py` — the detector (Python 3.8+ stdlib only).
- `assets/class-guard.config.json` — a starter `.class-guard.json`.
- `assets/pre-commit` — a git pre-commit hook running `--staged`.
- `assets/ci-step.yml` — a CI step.
- `references/config.md` — every config field, with examples.
- `references/wiring-into-orchestrator.md` — the wave-gate + DoD snippets.
- `references/scaffolding.md` — installing the gate at bootstrap so debt never accrues.
- `references/extraction-convention.md` — the citable "when to extract" standard.
