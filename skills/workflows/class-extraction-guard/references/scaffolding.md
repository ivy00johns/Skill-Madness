# Scaffolding the gate (so debt never accrues)

The whole point: a source-convention gate retrofitted *after* the UI exists can
only ratchet down a backlog — the painful manual burndown a human eventually
notices. Installed at the **bootstrap wave**, before the first frontend-agent
writes a line, it catches violation #1 at commit #1 and the soup never piles up.

## Consented portable bootstrap (native or solo)

Use the sibling design-token-guard's `scripts/bootstrap_frontend_guards.py` preview/apply path, providing this installed skill's root via `--class-guard-dir`. After scoped approval it bundles all helper scripts, selects repeated-utility/CSS ERROR policy, adds shared literal source-layout checks and a full-source runner plus CI. Hook snippet is inactive unless explicitly integrated; existing hooks/config are never overwritten. Full-tree source checks catch cross-file renamed CSS and copied chrome, unlike a staged-only subset. Missing resources/inspection failures block rather than pass. Generated output must be excluded and visible render proof still runs separately.

## Greenfield (recommended — hard gate from the start)

During the orchestrator's workspace-bootstrap step, drop in:

1. **Config** — copy `assets/class-guard.config.json` to `.class-guard.json` and
   set the strong rule to blocking:

   ```json
   { "rules": { "repeated-class-string": "error" } }
   ```

2. **Pre-commit** — install `assets/pre-commit` (or wire it via husky/lefthook) so
   a developer or agent gets the finding before the commit lands.
3. **CI** — add `assets/ci-step.yml` to the pipeline.
4. **No baseline.** On a fresh repo there's nothing to grandfather, so every combo
   is held to the standard from the first component.

Now the first time an agent pastes the same 6-utility combo a third time, the gate
fails and routes the finding back — the agent extracts it into a named class then,
when it's cheap, instead of a human refactoring 40 sites later.

## Existing codebase (ratchet — stop the bleeding, burn down over time)

```bash
python3 ~/.claude/skills/class-extraction-guard/scripts/check_class_extraction.py \
  --root . --write-baseline
git add .class-guard-baseline.json
```

Set `repeated-class-string: "error"` *with* the baseline committed: pre-existing
soup is grandfathered (reported, not blocking), but any **new** repeated combo
fails. Burn the baseline down opportunistically — each time you extract a combo,
re-run `--write-baseline` to shrink it.

## Where this plugs into the build

- **orchestrator** — `references/workspace-bootstrap.md` is where bootstrap
  deliverables (README, one-command dev, now the source-convention gates) are
  produced. Add `.class-guard.json` + hook + CI there, beside the design-token
  scaffolding.
- **frontend-agent** — invokes consented bootstrap before authoring, then runs the full project source runner before done; native independent QE remains required, solo self-check is not certification.
- **sync-skills** — the global `~/.claude/skills/class-extraction-guard` symlink is
  what the hook and agents invoke; run `/sync-skills` after installing the skill.
