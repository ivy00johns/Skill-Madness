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

@test "post-load refusal is graded apart from doing the work" {
  probe_test <<'PY'
g = tp._group_verdict
# Selected in every rep, but declining the work in one is not a clean pass.
assert g("positive", ["PASS", "LOADED_REFUSED"]) == "LOADED_REFUSED"
assert g("positive", ["LOADED_REFUSED", "LOADED_REFUSED"]) == "LOADED_REFUSED"
assert g("positive", ["PASS", "PASS"]) == "PASS"
# A refusal in some reps and a load miss in others is still a load flake.
assert g("positive", ["LOADED_REFUSED", "MISS"]) == "FLAKY"
pv = tp.positive_verdict
assert pv("render-sanity", {"render-sanity"}, False,
          "I can't run this without a browser.") == "LOADED_REFUSED"
# Declining but still handing back a BLOCKED report means the fallback ran.
assert pv("render-sanity", {"render-sanity"}, False,
          "I can't click through here, so every check is BLOCKED.") == "PASS"
assert pv("render-sanity", {"render-sanity"}, True, "Applied all four checks.") == "PASS"
assert pv("render-sanity", set(), True, "did the work anyway") == "WORKED"
assert pv("render-sanity", set(), False, "no output") == "MISS"
PY
  run python3 "$TMP/probe_test.py" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "host toolsets are selectable so a file-read host can be exercised" {
  probe_test <<'PY'
import pathlib, tempfile, types
from unittest import mock

captured = {}
def fake_run(cmd, **kwargs):
    captured["cmd"] = cmd
    return types.SimpleNamespace(returncode=0, stdout="", stderr="")

work = pathlib.Path(tempfile.mkdtemp())
with mock.patch.object(tp.subprocess, "run", fake_run):
    trace, code, note = tp.run_probe(
        "verify no inline styles bypass the design tokens",
        "deepseek-flash", work / "home", work, 30, {},
        toolsets="skills,file", max_turns=8,
    )
cmd = captured["cmd"]
assert cmd[cmd.index("-t") + 1] == "skills,file"
assert cmd[cmd.index("--max-turns") + 1] == "8"
assert code == 0
# The defaults still describe the original tool-less host: only `skills`, 4 turns.
with mock.patch.object(tp.subprocess, "run", fake_run):
    tp.run_probe("q", "m", work / "home", work, 30, {})
cmd = captured["cmd"]
assert cmd[cmd.index("-t") + 1] == "skills"
assert cmd[cmd.index("--max-turns") + 1] == "4"
PY
  run python3 "$TMP/probe_test.py" "$PROBE"
  [ "$status" -eq 0 ]
}

@test "hand-scan fixture keeps its planted violations and ground truth" {
  FIX="$REPO_ROOT/tests/gauntlet/fixtures/handscan-source"
  [ -f "$FIX/ground-truth.json" ]
  for f in theme.ts Button.tsx Card.tsx Row.tsx; do
    [ -f "$FIX/src/ui/$f" ]
  done
  # The inline-style files carry the hardcoded colours the guard must cite.
  grep -q '#1d4ed8' "$FIX/src/ui/Button.tsx"
  grep -q 'rgb(229, 231, 235)' "$FIX/src/ui/Card.tsx"
  grep -q 'hsl(0, 0%, 0%)' "$FIX/src/ui/Card.tsx"
  # The repeated class string appears at exactly three call-sites.
  count="$(grep -o 'flex items-center justify-between gap-4 rounded-md' "$FIX/src/ui/"*.tsx | wc -l | tr -d ' ')"
  [ "$count" -eq 3 ]
  # Ground truth names both source-level guards.
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert set(d)=={'design-token-guard','class-extraction-guard'}, d; assert d['class-extraction-guard']['files']" "$FIX/ground-truth.json"
}

@test "ground truth grades a loaded answer by whether it cites a finding" {
  probe_test <<'PY'
ce = tp.cites_expected
assert ce("Found src/ui/Button.tsx:5 — hardcoded #1d4ed8", ["src/ui/Button.tsx"]) is True
# Suffix-tolerant: a cited basename still counts.
assert ce("Button.tsx:5 bypasses the token", ["src/ui/Button.tsx"]) is True
# A bare path, or a line in a non-expected file, is not a finding.
assert ce("I scanned src/ui/Button.tsx thoroughly", ["src/ui/Button.tsx"]) is False
assert ce("The guard was BLOCKED; check src/ui/theme.ts:3", ["src/ui/Button.tsx"]) is False
# A host with no file read is not graded: its BLOCKED report is the correct answer.
assert tp.has_file_read([], "skills") is False
assert tp.has_file_read([], "skills,file") is True
assert tp.has_file_read(["read_file"], "skills") is True
pv = tp.positive_verdict
assert pv("design-token-guard", {"design-token-guard"}, True,
          "I hand-scanned the tree but found nothing to report.", grounded=False) == "LOADED_UNGROUNDED"
assert pv("design-token-guard", {"design-token-guard"}, True,
          "src/ui/Button.tsx:5 hardcodes #1d4ed8.", grounded=True) == "PASS"
# No expectation supplied -> the load is still a PASS.
assert pv("design-token-guard", {"design-token-guard"}, True, "scanned", grounded=None) == "PASS"
g = tp._group_verdict
assert g("positive", ["LOADED_UNGROUNDED", "LOADED_UNGROUNDED"]) == "LOADED_UNGROUNDED"
assert g("positive", ["PASS", "LOADED_UNGROUNDED"]) == "LOADED_UNGROUNDED"
assert g("positive", ["PASS", "PASS"]) == "PASS"
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
  # A one-record trace legitimately misses every OTHER must-fire skill, so the
  # report always carries a "Missed must-fire skills" section here; asserting
  # the section is absent would fail. The real invariant is narrower: an
  # explicit (disable-model-invocation) skill must never appear IN that list.
  missed_section="$(printf '%s\n' "$output" | sed -n '/## Missed must-fire skills/,/^## /p')"
  [[ "$missed_section" != *"frontend-agent"* ]]
}
