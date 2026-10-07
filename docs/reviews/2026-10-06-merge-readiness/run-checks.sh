#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CANDIDATE="$ROOT/.workspaces/today-audit/candidate"
EVIDENCE="$ROOT/.workspaces/today-audit/evidence"
export PATH="$ROOT/.workspaces/today-audit/venv/bin:$PATH"
mkdir -p "$EVIDENCE"
cd "$CANDIDATE" || exit 2
run_check() {
  local name="$1"
  shift
  local start=$SECONDS
  "$@" > "$EVIDENCE/$name.log" 2>&1
  local status=$?
  printf '%s\t%s\t%s\n' "$name" "$status" "$((SECONDS-start))" >> "$EVIDENCE/check-status.tsv"
  printf '%s: exit %s (%ss)\n' "$name" "$status" "$((SECONDS-start))"
}
printf 'check\texit_code\tseconds\n' > "$EVIDENCE/check-status.tsv"
run_check skill-lint bash scripts/lint-skills.sh skills/
run_check version-drift bash scripts/lint-skills.sh --changed origin/main
run_check catalog bash scripts/catalog.sh --check
run_check hooks-lint bash scripts/lint-hooks.sh
run_check supply-chain bash scripts/scan-skills.sh --check skills/
run_check python-tests python -m pytest -q tests/class-extraction-guard/test_frontend_wave.py tests/installer/test_resource_delivery.py tests/model-eval tests/orchestrator
run_check bats bash tests/run-all.sh
run_check convert-all bash scripts/convert.sh --tool all
printf 'Checks completed; inspect check-status.tsv (this script does not substitute for gate status).\n'
