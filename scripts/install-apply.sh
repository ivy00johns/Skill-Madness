#!/usr/bin/env bash
# install-apply.sh — Apply a reviewed schema-v2 plan, fail closed on stale bytes.
# Usage: scripts/install-apply.sh --plan FILE [--root DIR] [--dry-run]
# --root must match the plan's approved root; default HOME. Old plans must be
# regenerated/reviewed. No hook settings activation, credentials or network use.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/term.sh"
main() {
  local plan="" root="${HOME:-/tmp}" dry_run=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan) plan="${2:?'--plan requires a value'}"; shift 2 ;;
      --root) root="${2:?'--root requires a value'}"; shift 2 ;;
      --dry-run) dry_run=1; shift ;;
      --help|-h) sed -n '2,5p' "$0"; return 0 ;;
      *) ats_err "Unknown option: $1"; return 2 ;;
    esac
  done
  [[ -f "$plan" ]] || { ats_err "plan not found: $plan"; return 2; }
  ATS_DELIVERY_LIB="$SCRIPT_DIR/lib" python3 - "$plan" "$root" "$dry_run" <<'PY'
import os, sys
sys.path.insert(0, os.environ['ATS_DELIVERY_LIB'])
from resource_delivery import apply_plan, read_json
try:
    print(apply_plan(read_json(sys.argv[1]), sys.argv[2], sys.argv[3] == '1'))
except (OSError, ValueError, TypeError, KeyError) as exc:
    print('[apply] blocked: %s' % exc, file=sys.stderr)
    sys.exit(2)
PY
}
main "$@"
