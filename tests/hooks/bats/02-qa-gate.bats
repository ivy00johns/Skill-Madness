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
  unset ATS_QA_REPORT ATS_QA_RUN_ID ATS_QA_CONTRACTS ATS_HOOK_PROFILE CLAUDE_PROJECT_DIR
}

teardown() {
  rm -rf "$WORKDIR"
}

# Build a tiny committed worktree and bind a fresh report to its current bytes.
bound_fixture() {
  mkdir -p "$WORKDIR/project/contracts"
  export CLAUDE_PROJECT_DIR="$WORKDIR/project" ATS_QA_RUN_ID="test-run"
  git -C "$CLAUDE_PROJECT_DIR" init -q
  git -C "$CLAUDE_PROJECT_DIR" config user.email "test@example.com"
  git -C "$CLAUDE_PROJECT_DIR" config user.name "QA Test"
  git -C "$CLAUDE_PROJECT_DIR" config commit.gpgsign false
  printf 'source\n' > "$CLAUDE_PROJECT_DIR/app.txt"
  printf 'contract\n' > "$CLAUDE_PROJECT_DIR/contracts/api.txt"
  git -C "$CLAUDE_PROJECT_DIR" add .
  git -C "$CLAUDE_PROJECT_DIR" commit -qm fixture
  export ATS_QA_REPORT="$CLAUDE_PROJECT_DIR/qa-report.json"
  python3 - "$VALIDATOR" "$PASS_FIXTURE" "$ATS_QA_REPORT" <<'PY'
import json, os, subprocess, sys
binding = json.loads(subprocess.check_output([sys.executable, sys.argv[1], sys.argv[3], "--snapshot"]))
data = json.load(open(sys.argv[2]))
data["build_session_id"] = os.environ["ATS_QA_RUN_ID"]
data["proof_binding"] = binding
with open(sys.argv[3], "w") as f:
    json.dump(data, f)
PY
}

assert_block_json() {
  [ "$status" -eq 0 ]
  echo "$output" | grep -q '"decision": "block"'
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

@test "qa-gate.sh: strict missing validator blocks; standard remains explicitly unverified" {
  cp "$GATE" "$WORKDIR/qa-gate.sh"
  run env ATS_HOOK_PROFILE=strict ATS_QA_REPORT="$PASS_FIXTURE" bash "$WORKDIR/qa-gate.sh"
  assert_block_json
  echo "$output" | grep -q 'validator not found'
  run env ATS_HOOK_PROFILE=standard ATS_QA_REPORT="$PASS_FIXTURE" bash "$WORKDIR/qa-gate.sh"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'UNVERIFIED'
  ! echo "$output" | grep -q '"decision"'
}

@test "qa-gate.sh: strict crashed validator blocks" {
  cp "$GATE" "$WORKDIR/qa-gate.sh"
  printf 'raise RuntimeError("crashed")\n' > "$WORKDIR/qa-gate-validate.py"
  run env ATS_HOOK_PROFILE=strict ATS_QA_REPORT="$PASS_FIXTURE" bash "$WORKDIR/qa-gate.sh"
  assert_block_json
  echo "$output" | grep -q 'exited 1\|gate rule failed'
}

@test "qa-gate.sh: strict unexpected validator status blocks" {
  cp "$GATE" "$WORKDIR/qa-gate.sh"
  printf 'import sys; sys.exit(7)\n' > "$WORKDIR/qa-gate-validate.py"
  run env ATS_HOOK_PROFILE=strict ATS_QA_REPORT="$PASS_FIXTURE" bash "$WORKDIR/qa-gate.sh"
  assert_block_json
  echo "$output" | grep -q 'exited 7'
}

@test "qa-gate.sh: strict current run and source/contract binding allows" {
  bound_fixture
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -q '"decision"'
  echo "$output" | grep -q 'passed the gate'
}

@test "qa-gate.sh: strict legacy unbound PASS cannot certify" {
  bound_fixture
  cp "$PASS_FIXTURE" "$ATS_QA_REPORT"
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'proof_binding'
}

@test "qa-gate.sh: strict wrong run ID blocks" {
  bound_fixture
  run env ATS_HOOK_PROFILE=strict ATS_QA_RUN_ID=another-run bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'active run'
}

@test "qa-gate.sh: strict missing active run ID blocks" {
  bound_fixture
  run env ATS_HOOK_PROFILE=strict ATS_QA_RUN_ID= bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'active run ID'
}

@test "qa-gate.sh: strict changed source bytes block at the same HEAD" {
  bound_fixture
  printf 'changed\n' >> "$CLAUDE_PROJECT_DIR/app.txt"
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'source_sha256'
}

@test "qa-gate.sh: strict new untracked source blocks" {
  bound_fixture
  printf 'new\n' > "$CLAUDE_PROJECT_DIR/new.txt"
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  assert_block_json
}

@test "qa-gate.sh: strict changed contracts block" {
  bound_fixture
  printf 'changed\n' >> "$CLAUDE_PROJECT_DIR/contracts/api.txt"
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'proof stale'
}

@test "qa-gate.sh: strict wrong contract digest blocks" {
  bound_fixture
  python3 - "$ATS_QA_REPORT" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["proof_binding"]["contract_sha256"] = "0" * 64
with open(p, "w") as f:
    json.dump(d, f)
PY
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'contract_sha256'
}

@test "qa-gate.sh: strict deleted source and new revision block" {
  bound_fixture
  rm "$CLAUDE_PROJECT_DIR/app.txt"
  git -C "$CLAUDE_PROJECT_DIR" add -u
  git -C "$CLAUDE_PROJECT_DIR" commit -qm deletion
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  assert_block_json
  echo "$output" | grep -q 'revision'
}

@test "qa-gate.sh: Stop reentry returns control without certifying or looping" {
  run bash -c 'printf "%s" "{\"stop_hook_active\":true}" | ATS_HOOK_PROFILE=strict bash "$1"' _ "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'UNVERIFIED.*reentry'
  ! echo "$output" | grep -q '"decision"\|passed the gate'
}

@test "qa-gate.sh: malformed strict Stop payload blocks" {
  run bash -c 'printf "%s" "not JSON" | ATS_HOOK_PROFILE=strict bash "$1"' _ "$GATE"
  assert_block_json
  echo "$output" | grep -q 'invalid Stop-hook payload'
}

@test "qa-gate.sh: string reentry flag cannot bypass strict enforcement" {
  run bash -c 'printf "%s" "{\"stop_hook_active\":\"true\"}" | ATS_HOOK_PROFILE=strict bash "$1"' _ "$GATE"
  assert_block_json
}

@test "qa-gate.sh: host session ID supplies strict run context" {
  bound_fixture
  unset ATS_QA_RUN_ID
  run bash -c 'printf "%s" "{\"session_id\":\"test-run\",\"stop_hook_active\":false}" | ATS_HOOK_PROFILE=strict bash "$1"' _ "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'passed the gate'
}

@test "qa-gate.sh: unknown profile cannot downgrade enforcement" {
  cd "$WORKDIR"
  run env ATS_HOOK_PROFILE=strcit bash "$GATE"
  assert_block_json
}

@test "qa-gate.sh: strict missing Python still emits valid block JSON" {
  mkdir -p "$WORKDIR/bin"
  printf '#!/usr/bin/env bash\nexit 127\n' > "$WORKDIR/bin/python3"
  chmod +x "$WORKDIR/bin/python3"
  run bash -c 'PATH="$1:$PATH" ATS_HOOK_PROFILE=strict ATS_QA_REPORT="$2" bash "$3" 2>/dev/null' _ "$WORKDIR/bin" "$PASS_FIXTURE" "$GATE"
  [ "$status" -eq 0 ]
  run python3 -c 'import json, sys; assert json.loads(sys.argv[1])["decision"] == "block"' "$output"
  [ "$status" -eq 0 ]
}

@test "qa-gate.sh: allow path writes no stdout diagnostics" {
  run bash -c 'ATS_QA_REPORT="$1" bash "$2" 2>/dev/null' _ "$PASS_FIXTURE" "$GATE"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "qa-gate.sh: changed report narrative does not invalidate source proof" {
  bound_fixture
  printf 'QA narrative\n' > "$CLAUDE_PROJECT_DIR/qa-report.md"
  run env ATS_HOOK_PROFILE=strict bash "$GATE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q 'passed the gate'
}

@test "validate: strict non-Git project cannot certify" {
  run env ATS_QA_RUN_ID=test-run python3 "$VALIDATOR" "$PASS_FIXTURE" --strict --root "$WORKDIR"
  [ "$status" -eq 2 ]
  echo "$output" | grep -q 'proof unavailable'
}

@test "validate: strict contracts outside project cannot certify" {
  bound_fixture
  run env ATS_QA_CONTRACTS="$WORKDIR" python3 "$VALIDATOR" "$ATS_QA_REPORT" --strict
  [ "$status" -eq 2 ]
  echo "$output" | grep -q 'within the project root'
}

@test "validate: symlinked source requires an explicit separate evidence boundary" {
  bound_fixture
  ln -s app.txt "$CLAUDE_PROJECT_DIR/linked.txt"
  run python3 "$VALIDATOR" "$ATS_QA_REPORT" --snapshot
  [ "$status" -eq 2 ]
  echo "$output" | grep -q 'symlink requires a separate evidence boundary'
}

@test "validate: FAIL status cannot be overridden by proceed=true" {
  python3 - "$PASS_FIXTURE" "$WORKDIR/report.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["status"] = "FAIL"
with open(sys.argv[2], "w") as f:
    json.dump(d, f)
PY
  run python3 "$VALIDATOR" "$WORKDIR/report.json"
  [ "$status" -eq 1 ]
  echo "$output" | grep -q 'status is FAIL'
}
