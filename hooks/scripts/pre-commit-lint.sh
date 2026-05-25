#!/usr/bin/env bash
#
# pre-commit-lint.sh — PreToolUse(Bash) hook, scoped to `git commit`.
#
# When the Bash command being run is a git commit and skills/ files are staged,
# run scripts/lint-skills.sh on them and WARN if it finds problems. This is a
# warn-only hook: it never blocks the commit (only qa-gate blocks).
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
type ats_warn >/dev/null 2>&1 || ats_warn() { printf '[!!]  %s\n' "$*"; }
type ats_ok   >/dev/null 2>&1 || ats_ok()   { printf '[OK]  %s\n' "$*"; }
type ats_info >/dev/null 2>&1 || ats_info() { printf '[--]  %s\n' "$*"; }

PAYLOAD="$(cat 2>/dev/null || true)"

# Pull the command string out of the PreToolUse payload (tool_input.command).
cmd=""
if [[ -n "$PAYLOAD" ]]; then
  cmd="$(printf '%s' "$PAYLOAD" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input") or {}
print(ti.get("command") or d.get("command") or "")
' 2>/dev/null || true)"
fi

# Only act on a git commit invocation.
case "$cmd" in
  *"git commit"*) : ;;
  *) exit 0 ;;
esac

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LINT="$PROJECT_DIR/scripts/lint-skills.sh"
if [[ ! -x "$LINT" && ! -f "$LINT" ]]; then
  exit 0
fi

# Find staged skills/**/SKILL.md (best-effort; no git → bail quietly).
command -v git >/dev/null 2>&1 || exit 0
staged="$(cd "$PROJECT_DIR" 2>/dev/null && git diff --cached --name-only 2>/dev/null | grep -E '^skills/.*SKILL\.md$' || true)"

if [[ -z "$staged" ]]; then
  exit 0
fi

# Run lint on the staged skill files. Warn-only — capture status, never block.
lint_rc=0
( cd "$PROJECT_DIR" && bash "$LINT" $staged ) >/dev/null 2>&1 || lint_rc=$?
if (( lint_rc != 0 )); then
  ats_warn "pre-commit-lint: lint-skills.sh reported issues in staged skills (commit NOT blocked)"
else
  ats_ok "pre-commit-lint: staged skills pass lint"
fi

exit 0
