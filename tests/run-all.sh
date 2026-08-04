#!/usr/bin/env bash
# run-all.sh — Run the ENTIRE bats suite: every .bats file under tests/.
#
# Why this exists: `bats tests/` is NOT recursive. Every .bats file in this
# repo lives in a subdirectory (tests/installer/bats/, tests/catalog/, ...),
# so the non-recursive form runs zero tests and prints a green-looking
# `1..0`. Always use this script (or `bats -r tests/`) instead.
#
# Requires bats-core:
#   macOS:  brew install bats-core
#   Ubuntu: apt install bats
#
# Usage:
#   bash tests/run-all.sh                     # whole suite
#   bash tests/run-all.sh --tap               # extra args forwarded to bats
#   bash tests/run-all.sh --filter 'convert'  # bats' test-name regex filter
#
# With no arguments: --timing when stdout is a TTY, --tap otherwise (CI),
# matching the per-suite run-tests.sh scripts.
#
# Exit codes:
#   0  all tests passed
#   1  at least one test failed
#   2  bats not found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v bats >/dev/null 2>&1; then
  printf '[run-all] ERROR: bats-core is not installed.\n' >&2
  printf '[run-all]   macOS:  brew install bats-core\n' >&2
  printf '[run-all]   Ubuntu: apt install bats\n' >&2
  exit 2
fi

printf '[run-all] bats version: %s\n' "$(bats --version)" >&2
printf '[run-all] running all .bats files under: %s\n' "$SCRIPT_DIR" >&2

BATS_ARGS=("$@")
if [[ ${#BATS_ARGS[@]} -eq 0 ]]; then
  if [[ -t 1 ]]; then
    BATS_ARGS=(--timing)
  else
    BATS_ARGS=(--tap)
  fi
fi

# Close stdin for the whole run (DV-1): hook scripts under tests/hooks/
# drain stdin, and with inherited open stdin the suite hangs forever in a
# terminal. The scripts' own `[[ ! -t 0 ]]` guards cover TTY stdin; this
# redirect covers every other open-stdin shape (pipes that never EOF). No
# test in this repo reads stdin, so /dev/null is safe — don't remove it.
exec bats -r "${BATS_ARGS[@]}" "$SCRIPT_DIR" < /dev/null
