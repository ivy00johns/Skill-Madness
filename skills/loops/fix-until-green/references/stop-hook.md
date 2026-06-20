# The fix-until-green Stop-hook gate

When you want "don't stop until the gate is green" to ship *with* the build —
deterministically, so a role agent or an orchestrated wave can't declare done
while the gate is red — wire it as a **Stop hook**. This is the alternative to
the `/goal` driver: instead of an evaluator judging the transcript, the hook runs
the *real* gate and blocks the Stop on a non-zero result.

The hook follows this repo's Stop-hook contract (same as `hooks/scripts/qa-gate.sh`):
**signal a block by printing `{"decision":"block","reason":…}` to stdout and
exiting 0** — never by a non-zero exit code. Allowing the stop prints no decision
and exits 0.

## The two rules that keep it from becoming an infinite loop

1. **Guard `stop_hook_active`.** The Stop-hook payload (on stdin) carries
   `stop_hook_active: true` when the stop was *already* triggered by a prior Stop
   hook continuation. If you block unconditionally you create an infinite loop;
   when the flag is set and the gate is green, **let the stop through**.
2. **The gate is the only authority.** Block iff the gate is red. A green gate
   must always allow — otherwise the loop can never terminate even when the work
   is done.

## Reference gate hook

```bash
#!/usr/bin/env bash
# fix-until-green-gate.sh — Stop / SubagentStop hook.
# Blocks the stop while the project's test+lint+typecheck gate is red.
set -euo pipefail

# 1. Read the payload; respect stop_hook_active to avoid infinite loops.
payload="$(cat || true)"
active="$(printf '%s' "$payload" \
  | python3 -c 'import json,sys;
try: print(json.load(sys.stdin).get("stop_hook_active", False))
except Exception: print(False)' 2>/dev/null || echo False)"

# 2. Resolve + run the gate (see gate-commands.md for TEST/LINT/TYPECHECK_CMD).
#    run_gate exits 0 when all three legs pass, non-zero otherwise.
if run_gate; then
  exit 0                         # green → always allow the stop
fi

# 3. Red gate. If we're already inside a continuation AND the human may need to
#    break in (cap reached, no progress), prefer allowing over wedging — the
#    loop's own no-progress/iteration guards decide escalation, not the hook.
if [[ "$active" == "True" ]]; then
  # Optional: consult a fix_plan.md round counter here; allow once exhausted.
  : # fall through to block by default; flip to `exit 0` when escalating.
fi

# 4. Block: tell Claude to keep fixing, with the failing legs as the reason.
python3 -c '
import json, sys
print(json.dumps({"decision": "block",
                  "reason": "Gate is red: " + sys.argv[1] +
                            ". Fix one root cause and re-run the whole gate. "
                            "Do not skip/delete tests or add ignore directives."}))
' "$(failing_legs_summary)"
exit 0
```

`run_gate` and `failing_legs_summary` come from the composition snippet in
`gate-commands.md` (capture each leg's exit code; summarize which failed). Keep
the gate identical to the one the loop runs interactively — a hook that runs a
*different* command than CI is how a "blocked until green" build still produces a
red PR.

## Wiring

- **Per-skill (inherited by subagents):** declare the hook in the skill/agent
  frontmatter. A Stop hook declared there is **auto-converted to SubagentStop**
  when the agent runs as a subagent, so the gate travels into orchestrated builds
  without extra wiring.
- **Orchestrated wave gate:** register it where this repo registers the
  `qa-gate` hook (`hooks/hooks.manifest.json`); scope it to the wave that should
  not stop while red. Failures still route back to the owning agent **by file**
  (a red `src/api/` typecheck → the backend agent).
- **Profiles:** mirror `qa-gate.sh`'s `minimal | standard | strict` handling if
  you want the gate advisory in some profiles and blocking in others.

## When to prefer this over `/goal`

- **Stop-hook** — the proof needs a real script/file/tool check, you want the
  gate to ship with the build, or you want deterministic blocking in an
  orchestrated wave. Same-session continuation.
- **`/goal`** — interactive "work until green," the proof is fully provable from
  command output you surface, and you don't need the gate to persist with the
  skill. See `loop-controller/references/primitives.md`.
