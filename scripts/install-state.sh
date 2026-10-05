#!/usr/bin/env bash
# install-state.sh — list/drift/uninstall/repair reviewed schema-v2 installations.
# Usage: scripts/install-state.sh COMMAND [--root DIR] [--dry-run] [--plan FILE]
# Refuse old/escaped state and changed-file uninstall; never remove unowned files.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/lib/term.sh"
main() {
  local command="${1:-}" root="${HOME:-/tmp}" dry_run=0 plan=""
  case "$command" in
    list|drift|uninstall|repair) shift ;;
    --help|-h|'') sed -n '2,4p' "$0"; return 0 ;;
    *) ats_err "Unknown command: $command"; return 2 ;;
  esac
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --root) root="${2:?'--root requires a value'}"; shift 2 ;;
      --plan) plan="${2:?'--plan requires a value'}"; shift 2 ;;
      --dry-run) dry_run=1; shift ;;
      *) ats_err "Unknown option: $1"; return 2 ;;
    esac
  done
  ATS_DELIVERY_LIB="$SCRIPT_DIR/lib" python3 - "$command" "$root" "$dry_run" "$plan" <<'PY'
import os, sys
sys.path.insert(0, os.environ['ATS_DELIVERY_LIB'])
from resource_delivery import manage_state
try:
    sys.exit(manage_state(sys.argv[1], sys.argv[2], sys.argv[3] == '1', sys.argv[4] or None))
except (OSError, ValueError, TypeError, KeyError) as exc:
    print('[state] blocked: %s' % exc, file=sys.stderr)
    sys.exit(2)
PY
}
main "$@"
