#!/usr/bin/env bash
# install-plan.sh — Pure resolution from converted resource manifests; no writes
# except an explicitly requested --out plan receipt.
# Usage: scripts/install-plan.sh --tool NAME[,NAME...] [--profile NAME]
#        [--root DIR] [--integrations DIR] [--include-hooks] [--out FILE]
# --root overrides HOME/project destinations (default HOME).
# --include-hooks includes native hook files, never activates settings hooks.
# Schema v2 binds root, source bytes/modes and destination preconditions.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/lib/term.sh"
. "$SCRIPT_DIR/lib/install-state.sh"
main() {
  local tools_csv="" profile="full" root="${HOME:-/tmp}"
  local integrations="$REPO_ROOT/integrations" out="" include_hooks=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool) tools_csv="${tools_csv:+$tools_csv,}${2:?'--tool requires a value'}"; shift 2 ;;
      --profile) profile="${2:?'--profile requires a value'}"; shift 2 ;;
      --root) root="${2:?'--root requires a value'}"; shift 2 ;;
      --integrations) integrations="${2:?'--integrations requires a value'}"; shift 2 ;;
      --out) out="${2:?'--out requires a value'}"; shift 2 ;;
      --include-hooks) include_hooks=1; shift ;;
      --help|-h) sed -n '2,8p' "$0"; return 0 ;;
      *) ats_err "Unknown option: $1"; return 2 ;;
    esac
  done
  [[ -n "$tools_csv" ]] || { ats_err '--tool is required'; return 2; }
  [[ -d "$integrations" ]] || { ats_err 'integrations dir not found (run scripts/convert.sh first)'; return 2; }
  local cats
  cats="$(profile_categories "$profile" "$REPO_ROOT/manifests/profiles.json")" || { ats_err "Unknown profile: $profile"; return 2; }
  local plan_json
  plan_json="$(ATS_DELIVERY_LIB="$SCRIPT_DIR/lib" python3 - "$integrations" "$tools_csv" "$root" "$cats" "$profile" "$include_hooks" <<'PY'
import datetime, json, os, sys
sys.path.insert(0, os.environ['ATS_DELIVERY_LIB'])
from resource_delivery import TOOLS, make_plan
try:
    integ, csv, root, cats, profile, hooks = sys.argv[1:]
    tools = list(dict.fromkeys(csv.split(',')))
    if not tools or any(t not in TOOLS for t in tools):
        raise ValueError('Unknown tool: ' + csv)
    result = make_plan(integ, tools, root, set(cats.split()), profile,
                       datetime.datetime.now(datetime.timezone.utc).isoformat(), hooks == '1')
    print(json.dumps(result, indent=2))
except (OSError, ValueError, TypeError, KeyError) as exc:
    print('[plan] blocked: %s' % exc, file=sys.stderr)
    sys.exit(2)
PY
  )" || return 2
  if [[ -n "$out" ]]; then
    mkdir -p "$(dirname "$out")"
    printf '%s\n' "$plan_json" > "$out"
    ats_ok "Wrote plan: $out"
  else
    printf '%s\n' "$plan_json"
  fi
}
main "$@"
