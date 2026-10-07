#!/usr/bin/env bats
@test "delivery wave: portable resources, parallel parity, reviewed apply and owned sync" {
  local root
  root="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  run python3 -B "$root/tests/installer/test_resource_delivery.py"
  if [[ "$status" -ne 0 ]]; then printf '%s\n' "$output" >&2; fi
  [ "$status" -eq 0 ]
}
