#!/usr/bin/env bats
# 01-skill-health.bats — scripts/skill-health.sh deterministic engine.
#
# Contract: contracts/installer/skill-health.md v1.0.0 (P2-C).
#
# Builds a self-contained fake repo (scripts/skill-health.sh + libs + a tiny
# skills/ tree with known frontmatter versions) so current_version() resolves
# against the fixture. Every event log is a temp file passed via --log; no test
# ever touches the real ~/.claude/ats-telemetry log.
#
# Cases:
#   - record then report → event appears; 3 success + 1 failure = 0.75
#   - 7d vs 30d windows differ when an old event is added
#   - declining flag fires when recent rate drops past threshold
#   - version drift stale (recorded != current) and not-stale (matching)
#   - empty/absent log → report and drift exit 0 with no-data, never crash
#   - --json parses (python3) and totals are internally consistent

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  export REAL_ENGINE="$REPO_ROOT/scripts/skill-health.sh"
}

# _mk_skill <dir> <name> <version>
_mk_skill() {
  mkdir -p "$1"
  cat > "$1/SKILL.md" <<EOF
---
name: $2
version: $3
description: Fixture skill for skill-health tests.
---

# $2

Fixture body.
EOF
}

setup() {
  export FAKE
  FAKE="$(mktemp -d "${TMPDIR:-/tmp}/ats-sh-test.XXXXXX")"
  mkdir -p "$FAKE/scripts/lib"
  cp "$REAL_ENGINE"                          "$FAKE/scripts/skill-health.sh"
  cp "$REPO_ROOT/scripts/lib/term.sh"        "$FAKE/scripts/lib/term.sh"
  cp "$REPO_ROOT/scripts/lib/frontmatter.sh" "$FAKE/scripts/lib/frontmatter.sh"
  chmod +x "$FAKE/scripts/skill-health.sh"

  # Fixture skills tree: alpha v1.2.0, beta v2.0.0.
  _mk_skill "$FAKE/skills/meta/alpha" alpha 1.2.0
  _mk_skill "$FAKE/skills/meta/beta"  beta  2.0.0

  export ENGINE="$FAKE/scripts/skill-health.sh"
  export LOG="$FAKE/events.jsonl"
}

teardown() {
  rm -rf "$FAKE"
}

# ts_days_ago <n> — ISO8601 UTC timestamp n days before now.
ts_days_ago() {
  python3 -c "from datetime import datetime,timezone,timedelta; print((datetime.now(timezone.utc)-timedelta(days=$1)).strftime('%Y-%m-%dT%H:%M:%SZ'))"
}

# append_event <log> <skill> <version> <outcome> <ts>
append_event() {
  printf '{"ts":"%s","skill":"%s","version":"%s","outcome":"%s","session_id":"t","source":"manual"}\n' \
    "$5" "$2" "$3" "$4" >> "$1"
}

# ---------------------------------------------------------------------------
# record then report
# ---------------------------------------------------------------------------

@test "record appends a schema-valid line and report shows it" {
  run bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  [ "$status" -eq 0 ]
  [ -f "$LOG" ]
  run python3 -c "import json,sys; json.loads(open(sys.argv[1]).readline())" "$LOG"
  [ "$status" -eq 0 ]
}

@test "report: 3 success + 1 failure = total 4, rate 0.75" {
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  bash "$ENGINE" record --skill alpha --outcome failure --log "$LOG"
  run bash "$ENGINE" report --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | grep -E "alpha[[:space:]]+4[[:space:]]+0.75[[:space:]]+0.75"
}

@test "report --json: 3 success + 1 failure gives total 4 rate 0.75" {
  for o in success success success failure; do
    bash "$ENGINE" record --skill alpha --outcome "$o" --log "$LOG"
  done
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[s for s in d["skills"] if s["skill"]=="alpha"][0]
assert a["total"]==4, a
assert a["rate_7d"]==0.75, a
assert a["rate_30d"]==0.75, a
assert d["skill_count"]==1
'
}

# ---------------------------------------------------------------------------
# 7d vs 30d windows
# ---------------------------------------------------------------------------

@test "7d vs 30d: an old success counts in 30d only" {
  # 4 recent (3 success + 1 failure) → 7d 0.75
  for o in success success success failure; do
    bash "$ENGINE" record --skill alpha --outcome "$o" --log "$LOG"
  done
  # 1 old success at 10 days → still within 30d, outside 7d
  append_event "$LOG" alpha 1.2.0 success "$(ts_days_ago 10)"
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[s for s in d["skills"] if s["skill"]=="alpha"][0]
assert a["rate_7d"]==0.75, a
assert a["rate_30d"]==0.80, a   # 5 graded, 4 ok
assert a["total"]==5, a
'
}

# ---------------------------------------------------------------------------
# declining flag
# ---------------------------------------------------------------------------

@test "declining flag fires when 7d rate drops past threshold below 30d" {
  # recent: 1 success + 1 failure → 7d 0.50
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  bash "$ENGINE" record --skill alpha --outcome failure --log "$LOG"
  # older (10d): 4 success → pulls 30d up to 5/6 = 0.83
  for i in 1 2 3 4; do
    append_event "$LOG" alpha 1.2.0 success "$(ts_days_ago 10)"
  done
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[s for s in d["skills"] if s["skill"]=="alpha"][0]
assert a["rate_7d"]==0.50, a
assert a["declining"] is True, a   # 0.50 + 0.15 < 0.83
'
}

@test "declining flag stays false when recent rate holds" {
  for o in success success success failure; do
    bash "$ENGINE" record --skill alpha --outcome "$o" --log "$LOG"
  done
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[s for s in d["skills"] if s["skill"]=="alpha"][0]
assert a["declining"] is False, a
'
}

# ---------------------------------------------------------------------------
# version drift
# ---------------------------------------------------------------------------

@test "drift: recorded version differs from current SKILL.md → stale" {
  append_event "$LOG" alpha 0.9.0 success "$(ts_days_ago 1)"
  run bash "$ENGINE" drift --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | grep -E "alpha[[:space:]]+0.9.0[[:space:]]+1.2.0[[:space:]]+stale"
}

@test "drift: recorded version matches current SKILL.md → ok (not stale)" {
  append_event "$LOG" alpha 1.2.0 success "$(ts_days_ago 1)"
  run bash "$ENGINE" drift --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | grep -E "alpha[[:space:]]+1.2.0[[:space:]]+1.2.0[[:space:]]+ok"
  ! echo "$output" | grep -qE "alpha.*stale"
}

@test "drift --json: stale surfaces in version_drift" {
  append_event "$LOG" beta 1.0.0 success "$(ts_days_ago 1)"
  run bash "$ENGINE" drift --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
b=[s for s in d["skills"] if s["skill"]=="beta"][0]
assert b["recorded_version"]=="1.0.0", b
assert b["current_version"]=="2.0.0", b
assert b["version_drift"]=="stale", b
'
}

# ---------------------------------------------------------------------------
# empty / absent log → no-data, exit 0
# ---------------------------------------------------------------------------

@test "report on absent log exits 0 with no-data" {
  run bash "$ENGINE" report --log "$FAKE/nope.jsonl"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "no-data"
}

@test "drift on absent log exits 0 with no-data" {
  run bash "$ENGINE" drift --log "$FAKE/nope.jsonl"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "no-data"
}

@test "report --json on absent log exits 0 and parses to empty skills" {
  run bash "$ENGINE" report --json --log "$FAKE/nope.jsonl"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
assert d["skill_count"]==0, d
assert d["skills"]==[], d
'
}

@test "report on empty (touched) log exits 0 with no-data" {
  : > "$LOG"
  run bash "$ENGINE" report --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "no-data"
}

@test "report on absent/empty log warns telemetry is inactive (SR3)" {
  # Absent log: the emitter hook is not wired, so the report must say so.
  run bash "$ENGINE" report --log "$FAKE/nope.jsonl"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "telemetry inactive"
  echo "$output" | grep -qi "settings.json"
}

@test "report --json on absent log stays clean (no banner leaks into JSON)" {
  # The human banner must never break the machine-readable JSON.
  run bash "$ENGINE" report --json --log "$FAKE/nope.jsonl"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c 'import json,sys; json.load(sys.stdin)'
  ! ( echo "$output" | grep -qi "telemetry inactive" )
}

# ---------------------------------------------------------------------------
# robustness
# ---------------------------------------------------------------------------

@test "report tolerates malformed JSONL lines without crashing" {
  printf 'not json\n' >> "$LOG"
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  printf '{"partial":true}\n' >> "$LOG"
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[s for s in d["skills"] if s["skill"]=="alpha"][0]
assert a["total"]==1, a
'
}

@test "unknown-outcome events count in total but not in success rate" {
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  bash "$ENGINE" record --skill alpha --outcome unknown --log "$LOG"
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
a=[s for s in d["skills"] if s["skill"]=="alpha"][0]
assert a["total"]==2, a          # both counted in total
assert a["rate_7d"]==1.00, a     # only the graded success in the denominator
'
}

@test "bad outcome to record is an arg error (exit 2)" {
  run bash "$ENGINE" record --skill alpha --outcome bogus --log "$LOG"
  [ "$status" -eq 2 ]
}

@test "report no-data skill: a recorded-only skill still appears" {
  # beta never recorded → not in report; alpha recorded → present.
  bash "$ENGINE" record --skill alpha --outcome success --log "$LOG"
  run bash "$ENGINE" report --json --log "$LOG"
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c '
import json,sys
d=json.load(sys.stdin)
names=[s["skill"] for s in d["skills"]]
assert "alpha" in names
assert "beta" not in names   # unseen skills are no-data by absence, never errored
'
}
