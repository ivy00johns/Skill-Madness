# Wiring into the orchestrator / agent builds

This is the *organization* gate that sits beside `design-token-guard` (the *value*
gate). Both read source for problems the render gates can't see; neither subsumes
the other. Wire this one the same three ways design-token-guard is wired.

| gate | reads | catches | misses |
|---|---|---|---|
| render-sanity / ux-review | the running UI (pixels) | broken pages, dead links, stale data | repeated utility strings (they render fine) |
| design-token-guard | source | token-system bypasses, hardcoded colors, inline styles | how styling is *organized* |
| class-extraction-guard | source | the same utility combo repeated inline instead of extracted | anything wrong only at runtime; value-level token bypasses |

## 1. Frontend-agent self-check (before reporting done)

Add to the frontend-agent's done criteria, parallel to the design-token-guard
self-check:

```bash
python3 ~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py \
  --root . --json src/components/<the-files-it-touched> > /tmp/ceg.json
# If a rule is set to "error" and .summary.errors > 0, the task is NOT done:
# extract the repeated combo into a named class/component and re-run.
```

Phrase it in the prompt as a soft gate (warnings) or a hard gate (errors),
depending on the project's `.class-guard.json`:
> Before reporting done, run class-extraction-guard on your changed files. If a
> combo of 4+ utilities shows up 3+ times, extract it into a named class (`@apply`
> / a `cva` variant / a shared component) per `extraction-convention.md` and re-run.

## 2. Orchestrator wave-gate

At the UI wave-gate — where the orchestrator already runs install + typecheck +
test + `design-token-guard` — add this check for any wave that touched UI. Same
deterministic, parse-once shape, same failure routing:

```bash
python3 ~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py \
  --root . --json > /tmp/ceg.json
ERRORS=$(python3 -c "import json;print(json.load(open('/tmp/ceg.json'))['summary']['errors'])")
# ERRORS > 0  →  block the wave (only when a rule is "error"), route findings back
#               to the owning frontend-agent by file (each finding has file/line).
```

With the default config (`repeated-class-string: warning`) this never blocks — it
surfaces the soup in the wave report so the orchestrator and the human see it. Set
the rule to `error` (greenfield, scaffolded at bootstrap) to make it a hard gate.

## 3. Definition of Done line

Add alongside design-token-guard's source-convention item:

> **Source-organization gate passed for UI builds** — `class-extraction-guard`
> reports no error-severity findings (and its warnings are reviewed): the same
> utility combo isn't copy-pasted across the codebase instead of being a named
> class. This is the *organization* complement to design-token-guard's *value*
> check and render-sanity's *pixel* check — repeated utilities render identically
> to an extracted class, so only a source read catches them.

## Why this isn't redundant with design-token-guard

They check orthogonal axes. design-token-guard asks "is this color a token or a
hardcoded literal?" class-extraction-guard asks "is this 6-utility combo a named
class or pasted inline for the ninth time?" A string can pass the first and fail
the second (valid tokens, copy-pasted everywhere) — which is exactly the case that
shipped through a "passing" build and triggered this skill's existence.

## The placement that actually prevents the problem

Run it on every UI wave, yes — but the decisive move is **scaffolding it in the
bootstrap wave** (`scaffolding.md`), before the first frontend-agent writes a line.
A gate added after a fleet of agents has authored the UI inherits a backlog and can
only ratchet; one installed at commit #1 catches violation #1 and the soup never
accumulates.
