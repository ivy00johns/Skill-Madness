#!/usr/bin/env bash
#
# run-with-flags.sh — The single entrypoint every harness calls for a hook.
#
# Usage (from a Claude Code settings.json hook command):
#   "$CLAUDE_PROJECT_DIR"/.claude/ats-hooks/run-with-flags.sh <hook-id>
#
# Resolves <hook-id> against hooks.manifest.json, applies the profile/disable
# gating in lib/hook-flags.sh, and — if enabled — execs scripts/<hook-id>.sh
# with stdin passed through unchanged. Disabled or unknown id → silent exit 0
# (never wedge the host harness).
#
# Env:
#   ATS_HOOK_PROFILE   minimal | standard | strict (default standard)
#   ATS_DISABLED_HOOKS comma-separated hook ids to force-off
#
# Exit codes: always 0 for the wrapper itself except when the dispatched hook
# deliberately propagates a non-zero (only the qa-gate may, and per its
# contract it uses exit 0 + a block-decision JSON, so even that is 0).

set -euo pipefail

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Locate term.sh: when installed under ~/.claude/ats-hooks/ the scripts/lib/
# tree may not be present, so fall back to a no-op shim for the loggers.
_term_loaded=0
for cand in \
  "$HOOKS_DIR/../scripts/lib/term.sh" \
  "$HOOKS_DIR/lib/term.sh"; do
  if [[ -f "$cand" ]]; then
    # shellcheck source=/dev/null
    . "$cand"
    _term_loaded=1
    break
  fi
done
if [[ "$_term_loaded" -eq 0 ]]; then
  # Minimal shims so hook scripts can call ats_* even when term.sh is absent.
  ats_ok()   { printf '[OK]  %s\n' "$*"; }
  ats_warn() { printf '[!!]  %s\n' "$*"; }
  ats_err()  { printf '[ERR] %s\n' "$*" >&2; }
  ats_info() { printf '[--]  %s\n' "$*"; }
fi

# shellcheck source=hooks/lib/hook-flags.sh
. "$HOOKS_DIR/lib/hook-flags.sh"

HOOK_ID="${1:-}"
if [[ -z "$HOOK_ID" ]]; then
  ats_err "run-with-flags: no hook id given"
  exit 0
fi

HOOK_SCRIPT="$HOOKS_DIR/scripts/${HOOK_ID}.sh"
if [[ ! -f "$HOOK_SCRIPT" ]]; then
  printf '[run-with-flags] unknown hook id: %s\n' "$HOOK_ID" >&2
  exit 0
fi

if ! is_enabled "$HOOK_ID"; then
  # Disabled by profile or ATS_DISABLED_HOOKS — silent no-op.
  exit 0
fi

# Hand the stdin payload straight through to the hook script.
exec bash "$HOOK_SCRIPT" "${@:2}"
