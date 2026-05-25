#!/usr/bin/env bats
# 02-qa-gate.bats — qa-gate validator + Stop-hook behavior.
#
# Contract: contracts/hooks/hooks-layer.md §3.
# Cases:
#   - PASS fixture (tests/installer/qa-report.json) → allow (validator exit 0;
#     qa-gate.sh prints no block JSON)
#   - FAIL fixtures block for each rule: proceed=false, CRITICAL blocker,
#     contract_conformance<3, security<3 (validator exit 1, qa-gate.sh emits
#     {"decision":"block",...})
#   - malformed JSON → validator exit 2; qa-gate.sh blocks
#   - missing report → allow under standard, block under strict

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  export VALIDATOR="$REPO_ROOT/hooks/scripts/qa-gate-validate.py"
  export GATE="$REPO_ROOT/hooks/scripts/qa-gate.sh"
  export PASS_FIXTURE="$REPO_ROOT/tests/installer/qa-report.json"
  export FIX="$REPO_ROOT/tests/hooks/fixtures"
}

setup() {
  export WORKDIR
  WORKDIR="$(mktemp -d /tmp/ats-qagate-wd.XXXXXX)"
}

teardown() {
  rm -rf "$WORKDIR"
}

# ---------------------------------------------------------------------------
# Validator: PASS
# ---------------------------------------------------------------------------

@test "validate: PASS fixture allows (exit 0, no output)" {
  run python3 "$VALIDATOR" "$PASS_FIXTURE"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# Validator: each gate rule → exit 1 with reason
# ---------------------------------------------------------------------------

@test "validate: proceed=false blocks (exit 1)" {
  run python3 "$VALIDATOR" "$FIX/fail-proceed-false.json"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "proceed is false"
}

@test "validate: CRITICAL blocker blocks (exit 1)" {
  run python3 "$VALIDATOR" "$FIX/fail-critical-blocker.json"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "CRITICAL blocker"
}

@test "validate: contract_conformance<3 blocks (exit 1)" {
  run python3 "$VALIDATOR" "$FIX/fail-contract-conformance.json"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "contract_conformance"
}

@test "validate: security<3 blocks (exit 1)" {
  run python3 "$VALIDATOR" "$FIX/fail-security.json"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "security score"
}

# ---------------------------------------------------------------------------
# Validator: malformed / not found → exit 2
# ---------------------------------------------------------------------------

@test "validate: invalid JSON → exit 2" {
  run python3 "$VALIDATOR" "$FIX/malformed-bad-json.json"
  [ "$status" -eq 2 ]
  echo "$output" | grep -qi "malformed"
}

@test "validate: missing required key → exit 2" {
  run python3 "$VALIDATOR" "$FIX/malformed-missing-key.json"
  [ "$status" -eq 2 ]
  echo "$output" | grep -qi "malformed"
}

@test "validate: file not found → exit 2" {
  run python3 "$VALIDATOR" "$WORKDIR/nope.json"
  [ "$status" -eq 2 ]
  echo "$output" | grep -qi "not found"
}

# ---------------------------------------------------------------------------
# qa-gate.sh Stop-hook: allow path emits NO block JSON
# ---------------------------------------------------------------------------

@test "qa-gate.sh: PASS via ATS_QA_REPORT → exit 0, no block JSON" {
  run env ATS_QA_REPORT="$PASS_FIXTURE" bash "$GATE"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -q '"decision"'
}

# ---------------------------------------------------------------------------
# qa-gate.sh Stop-hook: block path emits decision JSON, exit 0
# ---------------------------------------------------------------------------

@test "qa-gate.sh: proceed=false → block JSON on stdout, exit 0" {
  run bash -c 'ATS_QA_REPORT="$1" bash "$2" 2>/dev/null' _ "$FIX/fail-proceed-false.json" "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q '"decision": "block"'
  echo "$output" | grep -qi "proceed is false"
}

@test "qa-gate.sh: CRITICAL blocker → block JSON, exit 0" {
  run bash -c 'ATS_QA_REPORT="$1" bash "$2" 2>/dev/null' _ "$FIX/fail-critical-blocker.json" "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q '"decision": "block"'
}

@test "qa-gate.sh: malformed report → block JSON, exit 0" {
  run bash -c 'ATS_QA_REPORT="$1" bash "$2" 2>/dev/null' _ "$FIX/malformed-bad-json.json" "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q '"decision": "block"'
  echo "$output" | grep -qi "malformed"
}

# ---------------------------------------------------------------------------
# qa-gate.sh: missing report by profile
# ---------------------------------------------------------------------------

@test "qa-gate.sh: missing report under standard → allow (exit 0, no block JSON)" {
  cd "$WORKDIR"
  run env ATS_HOOK_PROFILE=standard bash "$GATE"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -q '"decision"'
}

@test "qa-gate.sh: missing report under minimal → allow (no block JSON)" {
  cd "$WORKDIR"
  run env ATS_HOOK_PROFILE=minimal bash "$GATE"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -q '"decision"'
}

@test "qa-gate.sh: missing report under strict → block JSON, exit 0" {
  cd "$WORKDIR"
  run bash -c 'cd "$1" && ATS_HOOK_PROFILE=strict bash "$2" 2>/dev/null' _ "$WORKDIR" "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q '"decision": "block"'
}

# ---------------------------------------------------------------------------
# qa-gate.sh: report discovery via ./qa-report.json in CWD
# ---------------------------------------------------------------------------

@test "qa-gate.sh: discovers ./qa-report.json in CWD" {
  cp "$PASS_FIXTURE" "$WORKDIR/qa-report.json"
  run bash -c 'cd "$1" && ATS_HOOK_PROFILE=standard bash "$2"' _ "$WORKDIR" "$GATE"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -q '"decision"'
}
