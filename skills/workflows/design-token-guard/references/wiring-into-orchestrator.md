# Wiring into the orchestrator / agent builds

This is the missing **source-level** gate in a contract-first multi-agent build.
The orchestrator's existing gates are all **render-level** — `render-sanity`
(click-through, smell scan), `ux-review` (visual hierarchy), QA (contract +
security). None of them can see a hardcoded color, because it renders identically
to the token it should have used. That's how inline CSS shipped through a "passing"
build. This gate closes that hole by reading source, not pixels.

## Frontend-agent self-check (before reporting done)

Add to the frontend-agent's done criteria: run the checker against the files it
changed and treat error-severity findings as "not done."

```bash
python3 ~/.claude/skills/design-token-guard/scripts/check_design_tokens.py \
  --root . --json src/components/<the-files-it-touched> > /tmp/dtg.json
# Parse: if .summary.errors > 0, the task is NOT done — fix and re-run.
```

In a frontend-agent prompt, phrase it as a hard gate, parallel to typecheck:
> Before reporting done, run design-token-guard on your changed files. Any
> `no-hardcoded-color` error means you bypassed the token system — fix it using
> the suggested `var(--token)` (or add a new token if the color is genuinely new)
> and re-run until clean.

## Orchestrator wave-gate

At the wave gate — where the orchestrator already runs install + typecheck +
test between waves — add the token check for any wave that touched UI. It's a
deterministic, parse-once gate:

```bash
python3 scripts/check_design_tokens.py --root . --json > /tmp/dtg.json
ERRORS=$(python3 -c "import json;print(json.load(open('/tmp/dtg.json'))['summary']['errors'])")
# ERRORS > 0  →  block the wave, route findings back to the owning frontend-agent.
```

Route by file: each finding has `file`/`line`, so the orchestrator hands each
back to whichever agent owns that path (per `references/file-ownership.md`). This
is the same failure-routing protocol as a failed typecheck.

## Definition of Done line this closes

The orchestrator's Definition of Done has render-level gates (#10 render-sanity)
but no source-convention gate. Add one:

> **Source-convention gate passed** — `design-token-guard` returns zero
> error-severity findings for UI code (no inline styles or hardcoded colors
> bypassing the token system). This is the source-level complement to
> render-sanity's pixel-level checks; a UI build needs both. A green render and a
> clean console do not certify token discipline — only this does.

## Why both gates, not one

Keep the framing explicit for the orchestrator so it doesn't treat this as
redundant with render-sanity:

| gate | reads | catches | misses |
|---|---|---|---|
| render-sanity / ux-review | the running UI (pixels) | broken pages, dead links, stale data, visual regressions | hardcoded colors, inline styles (they render fine) |
| design-token-guard | the source | token-system bypasses, hardcoded CSS, inline styles | anything that's wrong only at runtime |

Neither subsumes the other. The inline-CSS class of bug lives exactly in
render-sanity's blind spot, which is why it accumulated unseen until a manual
refactor — and why this gate has to run on every UI wave, not as an afterthought.
