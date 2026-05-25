#!/usr/bin/env bash
#
# skill-usage.sh — PostToolUse coarse skill-usage emitter (best-effort).
#
# Contract: contracts/installer/skill-health.md §2 (P2-C).
#
# Honest scope note: Claude Code does NOT emit a clean "skill X invoked →
# outcome Y" event. This hook is therefore deliberately coarse. It inspects the
# PostToolUse payload for the only signal the host reliably provides — a Skill
# tool invocation (tool_input.skill / tool_name "Skill") — and, when it can name
# a skill, appends ONE coarse event via skill-health.sh record. It cannot know
# the true outcome from a single tool call, so it records outcome:unknown
# (source:hook). If it cannot attribute a skill, it silently skips.
#
# Non-blocking and best-effort: ANY problem exits 0 so the harness is never
# wedged. No network. Writes only to $ATS_TELEMETRY_LOG (or the engine default);
# tests override that via ATS_TELEMETRY_LOG to avoid touching ~/.claude/.
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

# Locate the engine. Prefer the repo tree; fall back to a sibling layout when
# installed under ~/.claude/. If we can't find it, silently no-op.
ENGINE=""
for cand in \
  "$HOOK_SCRIPTS_DIR/../../scripts/skill-health.sh" \
  "$HOOK_SCRIPTS_DIR/../scripts/skill-health.sh"; do
  [[ -f "$cand" ]] && { ENGINE="$cand"; break; }
done
if [[ -z "$ENGINE" ]]; then
  exit 0
fi

# Read the payload (may be empty when invoked outside a harness).
PAYLOAD="$(cat 2>/dev/null || true)"
[[ -z "$PAYLOAD" ]] && exit 0

# Extract a skill name from the PostToolUse payload. The only reliable signal is
# a Skill-tool invocation. python3 stdlib, tolerant of junk → empty on anything
# we can't attribute.
SKILL_NAME="$(printf '%s' "$PAYLOAD" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tool = (d.get("tool_name") or "").lower()
ti = d.get("tool_input") or {}
# Only attribute when the tool is the Skill tool and names a skill.
name = ""
if tool == "skill":
    name = ti.get("skill") or ti.get("name") or ""
print(str(name).strip())
' 2>/dev/null || true)"

# Cannot attribute a skill → silently skip (degrade, never fabricate).
[[ -z "$SKILL_NAME" ]] && exit 0

SESSION_ID="$(printf '%s' "$PAYLOAD" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(str(d.get("session_id") or "").strip())
' 2>/dev/null || true)"

# Append one coarse, outcome:unknown event. Swallow any failure → exit 0.
bash "$ENGINE" record \
  --skill "$SKILL_NAME" \
  --outcome unknown \
  --session "$SESSION_ID" \
  --source hook >/dev/null 2>&1 || true

exit 0
