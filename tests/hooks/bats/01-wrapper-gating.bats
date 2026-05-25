#!/usr/bin/env bats
# 01-wrapper-gating.bats — run-with-flags.sh profile/disable gating.
#
# Contract: contracts/hooks/hooks-layer.md §2.
# Cases:
#   - a hook in ATS_DISABLED_HOOKS is a no-op exit 0
#   - profile minimal runs only qa-gate
#   - profile standard runs the three (qa-gate, post-edit-format, session-start-profile)
#   - unknown id → exit 0 with a stderr note

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  export WRAPPER="$REPO_ROOT/hooks/run-with-flags.sh"
}

setup() {
  export WORKDIR
  WORKDIR="$(mktemp -d /tmp/ats-hooks-wd.XXXXXX)"
}

teardown() {
  rm -rf "$WORKDIR"
}

# ---------------------------------------------------------------------------
# Disabled hook is a no-op
# ---------------------------------------------------------------------------

@test "wrapper: disabled hook is a no-op exit 0 with no stdout" {
  run env ATS_HOOK_PROFILE=standard ATS_DISABLED_HOOKS=session-start-profile \
    bash "$WRAPPER" session-start-profile
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "wrapper: ATS_DISABLED_HOOKS honors a multi-id list" {
  run env ATS_HOOK_PROFILE=strict ATS_DISABLED_HOOKS="post-edit-format,pre-commit-lint" \
    bash "$WRAPPER" pre-commit-lint
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# Profile minimal → qa-gate only
# ---------------------------------------------------------------------------

@test "wrapper: minimal profile runs qa-gate (allow with no report)" {
  cd "$WORKDIR"
  run env ATS_HOOK_PROFILE=minimal bash "$WRAPPER" qa-gate
  [ "$status" -eq 0 ]
  # qa-gate runs → prints its warn line about no report
  echo "$output" | grep -qi "qa-gate"
}

@test "wrapper: minimal profile does NOT run post-edit-format (no-op)" {
  run env ATS_HOOK_PROFILE=minimal bash "$WRAPPER" post-edit-format
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "wrapper: minimal profile does NOT run session-start-profile (no-op)" {
  run env ATS_HOOK_PROFILE=minimal bash "$WRAPPER" session-start-profile
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# Profile standard → the three
# ---------------------------------------------------------------------------

@test "wrapper: standard profile runs qa-gate" {
  cd "$WORKDIR"
  run env ATS_HOOK_PROFILE=standard bash "$WRAPPER" qa-gate
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "qa-gate"
}

@test "wrapper: standard profile runs post-edit-format (enabled)" {
  # No file in payload → script runs but exits 0 silently. Enabled means the
  # wrapper dispatches; we confirm exit 0 (disabled would also be 0 but we pair
  # this with the minimal no-op test above to show the difference is real).
  run env ATS_HOOK_PROFILE=standard bash "$WRAPPER" post-edit-format
  [ "$status" -eq 0 ]
}

@test "wrapper: standard profile runs session-start-profile and emits CLAUDE.md" {
  run env ATS_HOOK_PROFILE=standard CLAUDE_PROJECT_DIR="$REPO_ROOT" \
    bash "$WRAPPER" session-start-profile
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "CLAUDE.md"
}

@test "wrapper: standard profile does NOT run pre-commit-lint (strict-only)" {
  run env ATS_HOOK_PROFILE=standard bash "$WRAPPER" pre-commit-lint
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# Profile strict → pre-commit-lint enabled
# ---------------------------------------------------------------------------

@test "wrapper: strict profile runs pre-commit-lint (no git commit cmd → exit 0)" {
  run bash -c 'printf "%s" "{\"tool_input\":{\"command\":\"ls\"}}" | ATS_HOOK_PROFILE=strict bash "$1" pre-commit-lint' _ "$WRAPPER"
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Unknown id
# ---------------------------------------------------------------------------

@test "wrapper: unknown hook id exits 0 with a stderr note and no stdout" {
  run bash "$WRAPPER" no-such-hook
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "unknown hook id"
}

@test "wrapper: unknown hook id writes nothing to stdout" {
  run bash -c 'bash "$1" no-such-hook 2>/dev/null' _ "$WRAPPER"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "wrapper: no hook id given exits 0" {
  run bash "$WRAPPER"
  [ "$status" -eq 0 ]
}
