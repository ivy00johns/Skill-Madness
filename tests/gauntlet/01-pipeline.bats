#!/usr/bin/env bats
@test "gauntlet: offline evidence pipeline refuses false coverage and proves CLI round trips" {
  local root
  root="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  run python3 -B "$root/tests/gauntlet/test_pipeline.py"
  if [[ "$status" -ne 0 ]]; then printf '%s\n' "$output" >&2; fi
  [ "$status" -eq 0 ]
}
