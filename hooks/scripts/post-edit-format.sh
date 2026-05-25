#!/usr/bin/env bash
#
# post-edit-format.sh — PostToolUse(Edit|Write) hook.
#
# Reads the Claude Code PostToolUse JSON payload on stdin, extracts the edited
# file path, and runs a matching formatter if one is on PATH. Best-effort and
# non-blocking: any problem exits 0 so the harness is never wedged.
#
# Recognized formatters (first available wins per extension):
#   .js .ts .jsx .tsx .json .md .css .html → prettier
#   .py                                    → black, else ruff format
#   .sh                                    → shfmt
#   .go                                    → gofmt
#   .rs                                    → rustfmt
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
# Fallbacks if term.sh was not found (installed tree may omit it).
type ats_info >/dev/null 2>&1 || ats_info() { printf '[--]  %s\n' "$*"; }
type ats_ok   >/dev/null 2>&1 || ats_ok()   { printf '[OK]  %s\n' "$*"; }
type ats_warn >/dev/null 2>&1 || ats_warn() { printf '[!!]  %s\n' "$*"; }

# Read the payload (may be empty when invoked outside a harness).
PAYLOAD="$(cat 2>/dev/null || true)"

# Extract a file path. Claude Code PostToolUse puts it under
# tool_input.file_path (Edit/Write). python3 stdlib, tolerant of junk.
target_file=""
if [[ -n "$PAYLOAD" ]]; then
  target_file="$(printf '%s' "$PAYLOAD" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
fp = ti.get("file_path") or d.get("file_path") or ""
print(fp)
' 2>/dev/null || true)"
fi

if [[ -z "$target_file" || ! -f "$target_file" ]]; then
  # Nothing to format — quietly succeed.
  exit 0
fi

ext="${target_file##*.}"
run_fmt() {
  # run_fmt <tool> [args...] — run only if tool exists; swallow failure.
  command -v "$1" >/dev/null 2>&1 || return 1
  "$@" >/dev/null 2>&1 || true
  return 0
}

formatted=0
case "$ext" in
  js|ts|jsx|tsx|json|md|css|html|yaml|yml)
    run_fmt prettier --write "$target_file" && formatted=1 ;;
  py)
    run_fmt black "$target_file" && formatted=1 || \
      { run_fmt ruff format "$target_file" && formatted=1; } ;;
  sh|bash)
    run_fmt shfmt -w "$target_file" && formatted=1 ;;
  go)
    run_fmt gofmt -w "$target_file" && formatted=1 ;;
  rs)
    run_fmt rustfmt "$target_file" && formatted=1 ;;
  *)
    : ;;
esac

if [[ "$formatted" -eq 1 ]]; then
  ats_info "post-edit-format: formatted $target_file"
fi

exit 0
