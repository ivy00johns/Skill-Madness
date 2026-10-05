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

# Read the Stop payload without reviving DV-1's open-TTY hang.
payload=""
if [[ ! -t 0 ]]; then
  payload="$(cat)"
fi

active_profile="${ATS_HOOK_PROFILE:-standard}"
case "$active_profile" in
  minimal|standard|strict) : ;;
  *) active_profile="strict" ;; # A typo must not downgrade enforcement.
esac

# emit_block <reason> — print the Stop-hook block decision and a stderr note.
emit_block() {
  local reason="$1"
  # JSON-encode the reason safely via python3 (stdlib).
  if ! python3 -c '
import json, sys
print(json.dumps({"decision": "block", "reason": sys.argv[1]}))
' "$reason"; then
    # Even a missing Python runtime must produce valid blocking JSON.
    printf '%s\n' '{"decision":"block","reason":"qa-gate runtime unavailable; restore python3 or explicitly disable the hook"}'
  fi
  ats_err "qa-gate: BLOCK — $reason"
  exit 0
}

# Check host reentry before blocking: allow the host to stop on the second
# invocation, but explicitly report UNVERIFIED rather than claiming QA passed.
if [[ -n "$payload" ]]; then
  payload_state=""
  if payload_state="$(python3 -c '
import json, sys
p = json.loads(sys.argv[1])
if not isinstance(p, dict) or not isinstance(p.get("stop_hook_active", False), bool):
    raise ValueError("invalid Stop payload")
print("reentry" if p.get("stop_hook_active", False) else "initial")
' "$payload" 2>/dev/null)"; then
    if [[ "$payload_state" == "reentry" ]]; then
      ats_err "qa-gate: UNVERIFIED — Stop-hook reentry; returning control without QA certification"
      exit 0
    fi
    if [[ -z "${ATS_QA_RUN_ID:-}" ]]; then
      ATS_QA_RUN_ID="$(python3 -c '
import json, sys
value = json.loads(sys.argv[1]).get("session_id", "")
print(value if isinstance(value, str) else "")
' "$payload")"
      export ATS_QA_RUN_ID
    fi
  elif [[ "$active_profile" == "strict" ]]; then
    emit_block "invalid Stop-hook payload or Python runtime unavailable"
  fi
fi

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
  ats_warn "qa-gate: no qa-report.json found — allowing (profile=$active_profile)" >&2
  exit 0
fi

if [[ ! -f "$VALIDATOR" ]]; then
  if [[ "$active_profile" == "strict" ]]; then
    emit_block "validator not found at $VALIDATOR (strict enforcement unavailable)"
  fi
  ats_warn "qa-gate: UNVERIFIED — validator not found at $VALIDATOR — allowing" >&2
  exit 0
fi

# --- Validate + evaluate gate rules ---
set +e
validator_args=("$report")
if [[ "$active_profile" == "strict" ]]; then
  validator_args+=(--strict)
fi
gate_reason="$(python3 "$VALIDATOR" "${validator_args[@]}" 2>/dev/null)"
rc=$?
set -e

case "$rc" in
  0)
    ats_ok "qa-gate: report passed the gate — allowing" >&2
    exit 0
    ;;
  1)
    emit_block "${gate_reason:-gate rule failed}"
    ;;
  2)
    emit_block "${gate_reason:-report malformed: not conformant}"
    ;;
  *)
    if [[ "$active_profile" == "strict" ]]; then
      emit_block "validator exited $rc unexpectedly (strict enforcement unavailable)"
    fi
    ats_warn "qa-gate: UNVERIFIED — validator exited $rc unexpectedly — allowing" >&2
    exit 0
    ;;
esac
