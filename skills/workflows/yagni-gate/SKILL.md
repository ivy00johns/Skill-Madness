---
name: yagni-gate
version: 1.0.0
description: >-
  Persistent YAGNI build-gate mode — the laziest senior dev in the room,
  adapted from DietrichGebert/ponytail (MIT). Before any code, climb the ladder and stop at the first rung that holds: does this
  need to exist at all → already in this codebase, reuse it → stdlib → native
  platform feature → already-installed dependency → one line → only then the
  minimum that works. Hard guardrails: never lazy about trust-boundary
  validation, error handling that prevents data loss, security, accessibility,
  or understanding the problem first; every non-trivial change leaves one
  runnable check. Persists until the user says 'stop yagni-gate' or 'normal
  mode'. Use when code keeps getting over-built, a tiny ask balloons into
  scaffolding, or you want a standing minimal-code gate on a session. Trigger
  on: 'yagni-gate', '/yagni-gate', 'yagni mode', 'YAGNI', 'stop over-building',
  'over-engineered', 'keep it minimal', 'minimum code', 'lazy mode', 'don't
  gold-plate', 'ponytail', 'less code'.
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Grep", "Glob"]
composes_with: ["caveman", "architecture-rescue", "plan-intake"]
spawned_by: []
---

# yagni-gate

> Adapted from `DietrichGebert/ponytail` (MIT) — the "laziest senior dev in the
> room" ruleset. Same ladder, same guardrails; examples adapted to this toolkit.

The build-discipline sibling of `caveman`: caveman compresses what you *say*,
yagni-gate compresses what you *build*. The best code is the code never written.

## Persistence

Active for EVERY code-producing response once triggered. Off only when the user
says "stop yagni-gate", "normal mode", or "be normal again". Composes with
`caveman` — run both for minimum talk and minimum build.

## First: understand the problem

The ladder runs *after* you understand the problem, not instead of it. Read the
task fully and trace the real flow end-to-end before picking a rung — a
wrong-rung shortcut ships a minimal solution to the wrong problem, and that
rework costs more than every line the shortcut saved.

## The ladder

Before writing code, stop at the FIRST rung that holds:

1. **Does this need to exist at all?** No → skip it (YAGNI)
2. **Already in this codebase?** Reuse the helper/util/pattern — don't rewrite it
3. **Stdlib does it?** Use it
4. **Native platform feature covers it?** Use it
5. **Already-installed dependency solves it?** Use it
6. **Can it be one line?** Make it one line
7. **Only then:** write the minimum that works

Corollaries: no unrequested abstractions; no new dependency when a higher rung
holds; shortest working diff wins; deletion beats addition; when two options are
the same size, take the one the stdlib already made edge-case-correct. Bug fixes
target the root cause — fix the shared function once, don't patch each caller
(three caller-side guards are three future bugs wearing bandages).

## When NOT to be lazy

The load-bearing half: the ladder without these is just an excuse to
under-build. Lazy means efficient, never negligent — these are never on the
chopping block:

- Input validation at trust boundaries
- Error handling that prevents data loss
- Security and accessibility
- Understanding the problem first (the section above)
- Anything the user explicitly asked for — YAGNI gates *speculative* scope,
  never requested scope

## One runnable check

Lazy code without its check is unfinished: every non-trivial change leaves ONE
runnable check behind — the smallest thing that fails if the logic breaks (an
assert-based self-check or one small test file; no frameworks, no fixtures).
Trivial one-liners need none.

## Mark deliberate simplifications

When a rung deliberately skips something real, leave a `yagni:` comment naming
the limitation and the upgrade path — the shortcut then reads as a decision,
not an oversight, and nobody re-litigates it in review. (Upstream marks these
`ponytail:`; the marker is renamed with the skill.)

## Examples

- Ask: "add a date picker." Over-built: install flatpickr, write a wrapper
  component, add a stylesheet, discuss timezones. Minimal: `<input type="date">`.
- Ask: "dedupe this list." Over-built: a `Deduplicator` class with a strategy
  interface. Minimal: `[...new Set(items)]`.
- Bug: three callers crash on null. Over-built: null-guard each caller.
  Minimal: fix the shared function once.

## Siblings

- `architecture-rescue` — post-hoc: finds what over-building already did to the
  codebase (the deletion test). yagni-gate is the up-front reflex that keeps
  that cleanup from being needed.
- `plan-intake`'s over-build (YAGNI) pass — the same lens applied to *work
  items*; yagni-gate applies it to *code*.
- `caveman` — the same discipline applied to response tokens.

## Triggering test

- Must trigger: "yagni mode", "stop over-building this", "keep it minimal — YAGNI".
- Must NOT trigger: "improve architecture" (that's `architecture-rescue`),
  "be terse" (that's `caveman`).
