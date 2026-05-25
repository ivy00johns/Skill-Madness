#!/usr/bin/env bats
# 03-convert-hooks.bats — convert.sh emits the Claude Code hooks artifacts.
#
# Contract: contracts/hooks/hooks-layer.md §4 + §6.
# Cases:
#   - convert --tool claude-code produces hooks/run-with-flags.sh (executable)
#   - produces hooks.json that parses and references run-with-flags.sh
#   - other tools log "hooks: unsupported for <tool>" and do not error
#
# Uses setup_file so convert runs once into a shared temp out dir.

setup_file() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  export CONVERT="$REPO_ROOT/scripts/convert.sh"

  export OUT_CC
  OUT_CC="$(mktemp -d /tmp/ats-conv-cc.XXXXXX)"
  bash "$CONVERT" --tool claude-code --out "$OUT_CC" >/dev/null 2>"$OUT_CC/.stderr" || true

  export OUT_CURSOR
  OUT_CURSOR="$(mktemp -d /tmp/ats-conv-cursor.XXXXXX)"
  bash "$CONVERT" --tool cursor --out "$OUT_CURSOR" >"$OUT_CURSOR/.stdout" 2>&1 || true
}

teardown_file() {
  rm -rf "$OUT_CC" "$OUT_CURSOR"
}

@test "convert: emits hooks/run-with-flags.sh" {
  [ -f "$OUT_CC/claude-code/hooks/run-with-flags.sh" ]
}

@test "convert: run-with-flags.sh is executable" {
  [ -x "$OUT_CC/claude-code/hooks/run-with-flags.sh" ]
}

@test "convert: emits the four hook scripts + validator + manifest" {
  [ -f "$OUT_CC/claude-code/hooks/scripts/qa-gate.sh" ]
  [ -f "$OUT_CC/claude-code/hooks/scripts/qa-gate-validate.py" ]
  [ -f "$OUT_CC/claude-code/hooks/scripts/post-edit-format.sh" ]
  [ -f "$OUT_CC/claude-code/hooks/scripts/session-start-profile.sh" ]
  [ -f "$OUT_CC/claude-code/hooks/scripts/pre-commit-lint.sh" ]
  [ -f "$OUT_CC/claude-code/hooks/hooks.manifest.json" ]
}

@test "convert: hooks.json exists and parses as JSON" {
  [ -f "$OUT_CC/claude-code/hooks.json" ]
  run python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$OUT_CC/claude-code/hooks.json"
  [ "$status" -eq 0 ]
}

@test "convert: hooks.json references run-with-flags.sh" {
  run grep -q "run-with-flags.sh" "$OUT_CC/claude-code/hooks.json"
  [ "$status" -eq 0 ]
}

@test "convert: hooks.json references the namespaced ats-hooks path" {
  run grep -q "ats-hooks" "$OUT_CC/claude-code/hooks.json"
  [ "$status" -eq 0 ]
}

@test "convert: hooks.json maps all four lifecycle events" {
  run python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))["hooks"]
for ev in ("Stop", "PostToolUse", "SessionStart", "PreToolUse"):
    assert ev in d, "missing event " + ev
' "$OUT_CC/claude-code/hooks.json"
  [ "$status" -eq 0 ]
}

@test "convert: non-claude-code tool logs hooks unsupported and exits 0" {
  run cat "$OUT_CURSOR/.stdout"
  echo "$output" | grep -qi "hooks: unsupported for cursor"
}

@test "convert: cursor run does not emit a hooks tree" {
  [ ! -d "$OUT_CURSOR/cursor/hooks" ]
  [ ! -f "$OUT_CURSOR/cursor/hooks.json" ]
}
