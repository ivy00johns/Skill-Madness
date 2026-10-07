#!/usr/bin/env bats
# 01-trigger-probe.bats — offline checks for scripts/gauntlet/trigger-probe.py and
# the explicit-invocation reconciliation in docs/gauntlet/coverage-matrix.md.
#
# No host, no model, no network: everything here reads the matrix and drives the
# probe's pure helpers with synthetic stream-json, so it runs in the same
# environment as the rest of tests/run-all.sh.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  PROBE="$REPO_ROOT/scripts/gauntlet/trigger-probe.py"
  MATRIX="$REPO_ROOT/docs/gauntlet/coverage-matrix.md"
  TMP="$(mktemp -d "${TMPDIR:-/tmp}/ats-probe.XXXXXX")"
  cd "$REPO_ROOT"
}

teardown() {
  rm -rf "$TMP"
}

# Write the python test body on stdin to a temp file, with the probe preloaded.
probe_test() {
  cat > "$TMP/probe_test.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("tp", sys.argv[1])
tp = importlib.util.module_from_spec(spec)
sys.modules["tp"] = tp
spec.loader.exec_module(tp)
PY
  cat >> "$TMP/probe_test.py"
}

@test "matrix marks exactly the five disable-model-invocation skills explicit" {
  probe_test <<'PY'
from pathlib import Path
mode = {r.skill: r.mode for r in tp.parse_matrix(Path("docs/gauntlet/coverage-matrix.md"))}
explicit = sorted(s for s, m in mode.items() if m == "explicit")
assert explicit == ["code-review-agent", "frontend-agent", "loop-controller", "perf-loop", "zoom-out"], explicit
assert mode["backend-agent"] == "must_fire"
assert mode["payload-cms"] == "optional"
assert sum(1 for m in mode.values() if m == "must_fire") == 70
assert len(mode) == 76
PY
  run python3 "$TMP/probe_test.py" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "work signal accepts an index-served answer but not a request for input" {
  probe_test <<'PY'
import json
line = lambda **e: json.dumps(e)
routing = "\n".join([
    line(type="tool_use", name="skills_list", input={}),
    line(type="result", text="**dependency-health-loop** audits for known vulnerabilities and over-stale pins, applies one safe update per pass, runs the full gate, and opens a PR."),
])
assert tp.assess_work(tp.parse_trace(routing))[0] is True
punt = line(type="result", text="You haven't included a diff. Please paste the diff or point me to the file/branch so I can review it.")
assert tp.assess_work(tp.parse_trace(punt))[0] is False
# A terse but correct routing answer still counts as work.
terse = line(type="result", text="dependency-health-loop audits for stale pins and opens one gated update PR.")
assert tp.assess_work(tp.parse_trace(terse))[0] is True
refusal = line(type="result", text="I can't help with that request.")
assert tp.assess_work(tp.parse_trace(refusal))[0] is False
# A question can be the work itself: an interview skill asks one at a time.
interview = line(type="result", text="First question: what is the core trust gap this escrow design must close?")
assert tp.assess_work(tp.parse_trace(interview))[0] is True
acted = line(type="tool_use", name="bash", input={"command": "pytest"})
assert tp.assess_work(tp.parse_trace(acted))[0] is True
view = "\n".join([
    line(type="tool_use", name="skill_view", input={"name": "zoom-out"}),
    line(type="tool_result", name="skill_view", output=json.dumps({"success": True})),
])
assert tp.parse_loads(view) == {"zoom-out"}
# A bare skill_view with no confirming result is not a load.
assert tp.parse_loads(line(type="tool_use", name="skill_view", input={"name": "zoom-out"})) == set()
PY
  run python3 "$TMP/probe_test.py" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "verdict collapsing keeps WORKED distinct from PASS and MISS" {
  probe_test <<'PY'
g = tp._group_verdict
assert g("positive", ["PASS", "PASS"]) == "PASS"
assert g("positive", ["PASS", "MISS"]) == "FLAKY"
assert g("positive", ["WORKED", "WORKED"]) == "WORKED"
assert g("positive", ["WORKED", "MISS"]) == "WORKED"
assert g("positive", ["MISS", "MISS"]) == "MISS"
assert g("negative", ["PASS", "PASS"]) == "PASS"
assert g("negative", ["FALSE_POSITIVE", "PASS"]) == "FLAKY"
assert g("negative", ["FALSE_POSITIVE"]) == "FALSE_POSITIVE"
PY
  run python3 "$TMP/probe_test.py" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "launcher snapshot covers sibling launchers like hermes-acp" {
  BIN="$TMP/fakehome/.hermes/hermes-agent/.hermes/bin"
  mkdir -p "$BIN"
  for name in hermes hermes-acp; do
    cat > "$BIN/$name" <<'SH'
#!/bin/sh
exec /usr/bin/env python3 -I -c '' "$@"
SH
  done
  printf 'not a launcher\n' > "$BIN/README"
  probe_test <<'PY'
import os, pathlib
os.environ["HOME"] = os.environ["FAKE_HOME"]
bindir = pathlib.Path(os.environ["FAKE_HOME"]) / ".hermes/hermes-agent/.hermes/bin"
got = tp.host_launchers("hermes")
# Both launchers the host rewrites are captured, whatever name is on PATH.
siblings = sorted(p.name for p in got if p.parent == bindir)
assert siblings == ["hermes", "hermes-acp"], siblings
# The non-launcher file in the same directory is not snapshotted.
assert all(p.name != "README" for p in got)
assert tp.host_launcher_dir("hermes") == bindir
PY
  FAKE_HOME="$TMP/fakehome" run python3 "$TMP/probe_test.py" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "trace-merge treats an explicit skill as reachable, not a false positive" {
  echo '{"skill": "frontend-agent"}' > "$TMP/telemetry.jsonl"
  run python3 "$REPO_ROOT/scripts/gauntlet/trace-merge.py" "$TMP/telemetry.jsonl" --matrix "$MATRIX"
  [ "$status" -eq 0 ]
  [[ "$output" != *"unexpected firing"* ]]
}

@test "score does not report an explicit skill as a missed must-fire" {
  echo '{"skill": "frontend-agent"}' > "$TMP/trace.jsonl"
  run python3 "$REPO_ROOT/scripts/gauntlet/score.py" "$TMP/trace.jsonl" --matrix "$MATRIX"
  [ "$status" -eq 0 ]
  [[ "$output" != *"Missed must-fire skills"* ]]
  [[ "$output" != *"frontend-agent"* ]]
}
