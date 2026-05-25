#!/usr/bin/env bash
#
# qa-gate.sh — Stop / TaskCompleted hook [MARQUEE].
#
# Locates a QA report, validates it with qa-gate-validate.py, applies the
# orchestrator gate rules, and BLOCKS the Stop on a gate failure using Claude
# Code's documented Stop-hook contract: print {"decision":"block","reason":...}
# to stdout and exit 0 (the human reason also goes to stderr). Allowing prints
# no decision and exits 0.
#
# Report location (contract §3 step 1):
#   $ATS_QA_REPORT if set, else first existing of
#   ./qa-report.json, coordination/qa-report.json, .claude/qa-report.json
#
# Missing report (step 2): standard/minimal → warn + allow; strict → block.
#
# Exit: always 0 (block is signalled via the decision JSON, not the exit code).

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
type ats_err  >/dev/null 2>&1 || ats_err()  { printf '[ERR] %s\n' "$*" >&2; }

VALIDATOR="$HOOK_SCRIPTS_DIR/qa-gate-validate.py"

# Drain stdin (Stop hook payload not needed for the gate decision).
cat >/dev/null 2>&1 || true

active_profile="${ATS_HOOK_PROFILE:-standard}"
case "$active_profile" in
  minimal|standard|strict) : ;;
  *) active_profile="standard" ;;
esac

# emit_block <reason> — print the Stop-hook block decision and a stderr note.
emit_block() {
  local reason="$1"
  # JSON-encode the reason safely via python3 (stdlib).
  python3 -c '
import json, sys
print(json.dumps({"decision": "block", "reason": sys.argv[1]}))
' "$reason"
  ats_err "qa-gate: BLOCK — $reason"
  exit 0
}

# --- Locate the report ---
report=""
if [[ -n "${ATS_QA_REPORT:-}" ]]; then
  report="$ATS_QA_REPORT"
else
  for cand in "./qa-report.json" "coordination/qa-report.json" ".claude/qa-report.json"; do
    if [[ -f "$cand" ]]; then
      report="$cand"
      break
    fi
  done
fi

# --- Missing report handling ---
if [[ -z "$report" || ! -f "$report" ]]; then
  if [[ "$active_profile" == "strict" ]]; then
    emit_block "no qa-report.json found (strict profile requires one)"
  fi
  ats_warn "qa-gate: no qa-report.json found — allowing (profile=$active_profile)"
  exit 0
fi

if [[ ! -f "$VALIDATOR" ]]; then
  # Cannot validate — non-critical: allow rather than wedge the harness.
  ats_warn "qa-gate: validator not found at $VALIDATOR — allowing"
  exit 0
fi

# --- Validate + evaluate gate rules ---
set +e
gate_reason="$(python3 "$VALIDATOR" "$report" 2>/dev/null)"
rc=$?
set -e

case "$rc" in
  0)
    ats_ok "qa-gate: report passed the gate — allowing"
    exit 0
    ;;
  1)
    emit_block "${gate_reason:-gate rule failed}"
    ;;
  2)
    emit_block "${gate_reason:-report malformed: not conformant}"
    ;;
  *)
    # Unexpected validator failure — allow (non-critical) but note it.
    ats_warn "qa-gate: validator exited $rc unexpectedly — allowing"
    exit 0
    ;;
esac
