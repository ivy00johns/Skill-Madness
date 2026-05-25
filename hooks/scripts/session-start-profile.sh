#!/usr/bin/env bash
#
# session-start-profile.sh — SessionStart hook.
#
# Injects a short orientation summary into the session: the project's CLAUDE.md
# and/or .claude/profile.yaml, truncated to <=8 KB total. Printed to stdout so
# the harness folds it into context. Non-blocking; always exits 0.
#
# Project root resolution:
#   $CLAUDE_PROJECT_DIR if set, else $PWD.
#
# Exit: always 0.

set -euo pipefail

HOOK_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
for cand in \
  "$HOOK_SCRIPTS_DIR/../../scripts/lib/term.sh" \
  "$HOOK_SCRIPTS_DIR/../lib/term.sh"; do
  [[ -f "$cand" ]] && { . "$cand"; break; }
done
type ats_info >/dev/null 2>&1 || ats_info() { printf '[--]  %s\n' "$*"; }

# Drain any stdin payload (SessionStart may send JSON); we don't need it.
cat >/dev/null 2>&1 || true

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"

MAX_BYTES=8192
emitted=0
budget="$MAX_BYTES"

emit_file() {
  # emit_file <label> <path> — print a header + up-to-budget bytes of the file.
  local label="$1" path="$2"
  [[ -f "$path" ]] || return 0
  (( budget > 0 )) || return 0
  printf '\n===== %s =====\n' "$label"
  # head -c is portable on macOS + Linux; cap to remaining budget.
  head -c "$budget" "$path"
  local n
  n="$(wc -c < "$path" | tr -d '[:space:]')"
  if (( n > budget )); then
    printf '\n[... truncated at %d bytes ...]\n' "$budget"
    budget=0
  else
    budget=$(( budget - n ))
  fi
  emitted=1
}

emit_file "CLAUDE.md" "$PROJECT_DIR/CLAUDE.md"
emit_file ".claude/profile.yaml" "$PROJECT_DIR/.claude/profile.yaml"

if [[ "$emitted" -eq 0 ]]; then
  ats_info "session-start-profile: no CLAUDE.md or .claude/profile.yaml found"
fi

exit 0
