#!/usr/bin/env bash
#
# catalog-sync.sh — PreToolUse(Bash) hook, scoped to `git commit`.
#
# The filesystem is the single source of truth for the skill catalog. When a
# commit is about to run, this checks whether the derived artifacts (skill
# counts across README/CLAUDE/PLAN/START-HERE/plugin.json/marketplace.json, and
# the plugin.json `skills` array) still agree with disk. If they've drifted —
# typically because a skill directory was just added or removed — it runs
# `scripts/catalog.sh --sync` and re-stages the corrected files so the commit
# carries them. You never have to remember to update counts again.
#
# It only acts when there is REAL drift (a no-op otherwise), so ordinary commits
# are untouched. Never blocks — worst case it does nothing.
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
CATALOG="$PROJECT_DIR/scripts/catalog.sh"
[[ -f "$CATALOG" ]] || exit 0
command -v git >/dev/null 2>&1 || exit 0
( cd "$PROJECT_DIR" 2>/dev/null && git rev-parse --is-inside-work-tree ) >/dev/null 2>&1 || exit 0

# Cheap check first — if the catalog already matches disk, do nothing.
if ( cd "$PROJECT_DIR" && bash "$CATALOG" --check ) >/dev/null 2>&1; then
  exit 0
fi

# Drift detected: reconcile and re-stage the derived files so the commit is
# self-consistent.
( cd "$PROJECT_DIR" && bash "$CATALOG" --sync ) >/dev/null 2>&1 || {
  ats_warn "catalog-sync: catalog drift detected but --sync failed (commit NOT blocked); run scripts/catalog.sh --sync"
  exit 0
}

CATALOG_FILES=(
  "README.md"
  "CLAUDE.md"
  "PLAN.md"
  "START-HERE.md"
  ".claude-plugin/plugin.json"
  ".claude-plugin/marketplace.json"
)
restaged=""
for f in "${CATALOG_FILES[@]}"; do
  if ( cd "$PROJECT_DIR" && ! git diff --quiet -- "$f" 2>/dev/null ); then
    ( cd "$PROJECT_DIR" && git add -- "$f" ) 2>/dev/null && restaged="$restaged $f"
  fi
done

if [[ -n "$restaged" ]]; then
  ats_ok "catalog-sync: reconciled skill counts + plugin listing to disk and re-staged:$restaged"
else
  ats_info "catalog-sync: catalog reconciled (no tracked files needed restaging)"
fi
exit 0
