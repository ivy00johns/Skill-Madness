#!/usr/bin/env bash
# run-tests.sh — Run the hooks-layer test suite.
#
# Requires bats-core:
#   macOS:  brew install bats-core
#   Ubuntu: apt install bats
#
# Usage:
#   bash tests/hooks/run-tests.sh              # run all .bats files
#   bash tests/hooks/run-tests.sh --filter 01  # run only matching files
#
# Exit codes:
#   0  all tests passed
#   1  at least one test failed
#   2  bats not found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BATS_DIR="$SCRIPT_DIR/bats"
FILTER="${1:-}"
[[ "$FILTER" == "--filter" ]] && FILTER="${2:-}"

if ! command -v bats >/dev/null 2>&1; then
  printf '[run-tests] ERROR: bats-core is not installed.\n' >&2
  printf '[run-tests]   macOS:  brew install bats-core\n' >&2
  printf '[run-tests]   Ubuntu: apt install bats\n' >&2
  exit 2
fi

printf '[run-tests] bats version: %s\n' "$(bats --version)"
printf '[run-tests] test directory: %s\n\n' "$BATS_DIR"

TEST_FILES=()
while IFS= read -r f; do
  if [[ -z "$FILTER" ]] || [[ "$(basename "$f")" == *"$FILTER"* ]]; then
    TEST_FILES+=("$f")
  fi
done < <(find "$BATS_DIR" -name "*.bats" -type f | sort)

if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
  printf '[run-tests] No .bats files found matching filter: %s\n' "${FILTER:-*}" >&2
  exit 1
fi

printf '[run-tests] Running %d test file(s):\n' "${#TEST_FILES[@]}"
for f in "${TEST_FILES[@]}"; do printf '  %s\n' "$(basename "$f")"; done
printf '\n'

if [[ -t 1 ]]; then
  bats --timing "${TEST_FILES[@]}"
else
  bats --tap "${TEST_FILES[@]}"
fi
