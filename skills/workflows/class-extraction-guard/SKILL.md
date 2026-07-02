---
name: class-extraction-guard
version: 1.0.1
composes_with: ["orchestrator", "frontend-agent", "design-token-guard", "render-sanity", "code-review-agent", "sync-skills"]
description: >-
  Source-level gate that catches utility-class soup — the same long run of
  utility classes (e.g. `flex items-center gap-1.5 text-fg-muted hover:text-accent`)
  copy-pasted inline across many files instead of extracted into a named class or
  component. Use whenever frontend work touches className/class markup: before
  committing or declaring a UI task done, when auditing why a codebase looks like
  utility soup, when a Tailwind combo is repeated everywhere, or as an
  orchestrator/agent wave-gate. Trigger on: "utility soup", "repeated tailwind
  classes", "extract into named classes", "className duplication", "class string
  copy-pasted", "DRY up the styles", "class-extraction". Framework-agnostic
  (React/JSX, Vue, Svelte, Astro, HTML; clsx/cn/cva). Sibling to design-token-guard:
  it checks WHICH values styling uses (tokens vs hex), this checks HOW styling is
  organized (extracted vs repeated) — invisible to render review since repeated
  utilities render identically to an extracted class.
compatibility: Claude Code; requires Python 3.8+ (stdlib only) to run scripts/check_class_extraction.py
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

## Quick start

```bash
# Human-readable report
python3 ~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py --root .

# JSON for a gate (same gate contract as design-token-guard: exit codes +
# .summary.errors / .summary.warnings — the JSON key shapes differ)
python3 ~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py --root . --json
#   -> { "summary": { "errors": 0, "warnings": 12, "files_scanned": 98 },
#        "findings": [ { "rule": "...", "file": "...", "line": 93, "count": 9,
#                        "string": "...", "occurrences": [...], "suggestion": "..." } ] }
```

Exit codes: **0** = no error-severity findings, **1** = error-severity findings,
**2** = usage/config error. `--staged` scans only git-staged files (for a
pre-commit hook). `--quiet` suppresses the human output.

## What it flags

| rule | default | fires when |
|---|---|---|
| `repeated-class-string` | **warning** | the same (order-normalized) class string of ≥ `minUtilities` (4) tokens appears in ≥ `minRepeats` (3) distinct call-sites |
| `long-class-string` | off (opt-in) | a single class string carries ≥ `maxUtilities` (12) tokens — a one-off mega-string worth splitting even unrepeated |
| `abstraction-defeat` | off (opt-in) | extra utilities are glued onto an element that already has a named/`@apply` class (needs `namedClassPattern` set) |

The default is intentionally just **one rule, at warning severity** — utility-soup
is a preference-y standard, so the gate informs by default and never blocks a
build on adoption day. Flip a rule to `error` (and scaffold it at the bootstrap
wave) when you want it to hard-gate a greenfield project from commit #1. See
`references/config.md` for every option.

## Adopting on an existing codebase (ratchet mode)

A gate added *after* a fleet of agents has written the UI inherits a backlog —
which is why the default is non-blocking. To adopt without drowning in
pre-existing debt, record a baseline and only flag **new** duplication:

```bash
CEG=~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py
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

- `scripts/check_class_extraction.py` — the detector (Python 3.8+ stdlib only).
- `assets/class-guard.config.json` — a starter `.class-guard.json`.
- `assets/pre-commit` — a git pre-commit hook running `--staged`.
- `assets/ci-step.yml` — a CI step.
- `references/config.md` — every config field, with examples.
- `references/wiring-into-orchestrator.md` — the wave-gate + DoD snippets.
- `references/scaffolding.md` — installing the gate at bootstrap so debt never accrues.
- `references/extraction-convention.md` — the citable "when to extract" standard.
