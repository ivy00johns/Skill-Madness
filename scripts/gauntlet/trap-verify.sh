#!/usr/bin/env bash
# trap-verify.sh — check the Gauntlet II trap fixtures against their guards.
#
# Deterministic and offline. For each trap it reports one verdict:
#   PASS     the expected behaviour was observed
#   FAIL     the guard did not behave as expected (a real finding)
#   REPRO    the vulnerable fixture reproduces the failure shape (a finding)
#   BLOCKED  the check could not read its inputs, or needs a live run
#
# A checker that cannot inspect its input reports BLOCKED, never PASS.
#
# This script is authored for the Gauntlet II run. It does not run a model.
#
# Usage: trap-verify.sh [TARGET]
set -uo pipefail

TARGET="${1:-}"
_here="$(cd "$(dirname "$0")" && pwd)"
_root="$_here"
while [ "$_root" != "/" ] && [ ! -f "$_root/.env.example" ]; do
  _root="$(dirname "$_root")"
done
if [ ! -f "$_root/.env.example" ]; then
  echo "error: could not locate repo root from $_here" >&2
  exit 2
fi

if [ -z "$TARGET" ]; then
  TARGET="$_root/.workspaces/gauntlet-ii"
fi
TRAPS="$TARGET/traps"

DESIGN_GUARD="$_root/skills/workflows/design-token-guard/scripts/check_design_tokens.py"
CLASS_GUARD="$_root/skills/workflows/class-extraction-guard/scripts/check_class_extraction.py"
SHARED_GUARD="$_root/skills/workflows/class-extraction-guard/scripts/check_shared_layout.py"

# Scratch area for verifier-side config. Fixtures stay pristine.
VERIFY_SCRATCH="$TARGET/.verify"
mkdir -p "$VERIFY_SCRATCH"

FAILS=0
BLOCKED=0

emit() { # trap | expected | observed | verdict
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4"
  case "$4" in
    FAIL|REPRO) FAILS=$((FAILS + 1)) ;;
    BLOCKED) BLOCKED=$((BLOCKED + 1)) ;;
  esac
}

run_guard() { # guard_path target_dir [extra args...] -> sets global rc
  local guard="$1"
  local target="$2"
  shift 2
  rc=3
  if [ ! -f "$guard" ]; then
    return
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    return
  fi
  # Do not force --quiet: not every guard defines it, and stdout is discarded.
  python3 "$guard" --root "$target" "$@" >/dev/null 2>&1
  rc=$?
}

if [ ! -f "$TRAPS/.seeded" ]; then
  echo "traps not seeded at $TRAPS — run trap-inject.sh first" >&2
  exit 2
fi

printf 'trap\texpected\tobserved\tverdict\n'
printf '%s\n' "-------------------------------------------------------------"

# T1 — behavioural; needs a live build.
emit "T1" "frontend solo mode applies" "requires a live build" "BLOCKED"

# T2 — inline layout. The catalog requires BOTH halves: the default profile
# reports a finding, and the strict layout profile exits non-zero.
T2_EXPECT="default reports finding; strict profile exits non-zero"
if [ -f "$DESIGN_GUARD" ] && [ -d "$TRAPS/T2-inline" ]; then
  t2_total="$(python3 "$DESIGN_GUARD" --root "$TRAPS/T2-inline" --json 2>/dev/null | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin)["summary"]["total"])
except Exception:
    print(-1)
')"
  run_guard "$DESIGN_GUARD" "$TRAPS/T2-inline" --profile layout
  t2_strict="$rc"
  if [ "$t2_total" = "-1" ]; then
    emit "T2" "$T2_EXPECT" "default profile output unreadable" "BLOCKED"
  elif [ "$t2_total" -eq 0 ]; then
    emit "T2" "$T2_EXPECT" "default profile found nothing (strict exit=$t2_strict)" "FAIL"
  elif [ "$t2_strict" -eq 1 ]; then
    emit "T2" "$T2_EXPECT" "default findings=$t2_total, strict exit=$t2_strict" "PASS"
  elif [ "$t2_strict" -eq 3 ]; then
    emit "T2" "$T2_EXPECT" "strict guard could not run" "BLOCKED"
  else
    emit "T2" "$T2_EXPECT" "default findings=$t2_total, strict exit=$t2_strict (no strict enforcement)" "FAIL"
  fi
else
  emit "T2" "$T2_EXPECT" "guard or fixture unreadable" "BLOCKED"
fi

# T3 — duplicate declarations. `duplicate-css-block` ships "off" (opt-in), so the
# verifier must enable it; running with defaults tests nothing.
T3_CFG="$VERIFY_SCRATCH/class-guard.json"
printf '%s\n' '{"rules": {"duplicate-css-block": "error"}}' > "$T3_CFG"
if [ -f "$CLASS_GUARD" ] && [ -d "$TRAPS/T3-hash" ]; then
  run_guard "$CLASS_GUARD" "$TRAPS/T3-hash" --config "$T3_CFG"
  case "$rc" in
    1) emit "T3" "duplicate declaration group found (rule enabled)" "guard exit 1" "PASS" ;;
    0) emit "T3" "duplicate declaration group found (rule enabled)" "guard exit 0 (missed)" "FAIL" ;;
    *) emit "T3" "duplicate declaration group found (rule enabled)" "guard could not run (exit $rc)" "BLOCKED" ;;
  esac
else
  emit "T3" "duplicate declaration group found (rule enabled)" "guard or fixture unreadable" "BLOCKED"
fi

# T4 — copied chrome. UA-07 landed this guard at class-extraction-guard/scripts/;
# the original audit-baseline note said no such guard existed.
if [ -f "$SHARED_GUARD" ] && [ -d "$TRAPS/T4-chrome" ]; then
  run_guard "$SHARED_GUARD" "$TRAPS/T4-chrome"
  case "$rc" in
    1) emit "T4" "copied chrome flagged (exit 1)" "guard exit 1" "PASS" ;;
    0) emit "T4" "copied chrome flagged (exit 1)" "guard exit 0 (missed)" "FAIL" ;;
    *) emit "T4" "copied chrome flagged (exit 1)" "guard could not run (exit $rc)" "BLOCKED" ;;
  esac
else
  emit "T4" "copied chrome flagged (exit 1)" "guard or fixture unreadable" "BLOCKED"
fi

# T5 — behavioural.
emit "T5" "explicit attended plan or refusal" "requires a live build" "BLOCKED"

# T6 — behavioural.
emit "T6" "wrapper cancels at cap" "requires a live build" "BLOCKED"

# T7 — behavioural.
emit "T7" "frozen verifier digests" "requires a live build" "BLOCKED"

# T8 — stale, unbound QA report. The guard under test is hooks/scripts/qa-gate.sh,
# which is deterministic and offline-checkable; the seeded "bad checker" only
# illustrates the shape and proves nothing about the real gate. qa-gate signals
# through the Stop-hook decision JSON and always exits 0, so assert on the JSON.
QA_GATE="$_root/hooks/scripts/qa-gate.sh"
T8_EXPECT="strict fails closed; standard preserved"
if [ -f "$QA_GATE" ] && [ -d "$TRAPS/T8-qa" ]; then
  t8_strict="$(printf '' | ATS_HOOK_PROFILE=strict ATS_QA_REPORT="$TRAPS/T8-qa/absent.json" bash "$QA_GATE" 2>/dev/null || true)"
  t8_standard="$(printf '' | ATS_HOOK_PROFILE=standard ATS_QA_REPORT="$TRAPS/T8-qa/absent.json" bash "$QA_GATE" 2>/dev/null || true)"
  t8_stale="$(printf '' | ATS_HOOK_PROFILE=strict ATS_QA_REPORT="$TRAPS/T8-qa/qa-report.json" bash "$QA_GATE" 2>/dev/null || true)"
  t8_ok=1
  printf '%s' "$t8_strict" | grep -q '"decision"[[:space:]]*:[[:space:]]*"block"' || t8_ok=0
  [ -z "$t8_standard" ] || t8_ok=0
  printf '%s' "$t8_stale" | grep -q '"decision"[[:space:]]*:[[:space:]]*"block"' || t8_ok=0
  if [ "$t8_ok" -eq 1 ]; then
    emit "T8" "$T8_EXPECT" "strict blocks missing+stale; standard allows" "PASS"
  else
    emit "T8" "$T8_EXPECT" "strict='$t8_strict' standard='$t8_standard' stale='$t8_stale'" "FAIL"
  fi
else
  emit "T8" "$T8_EXPECT" "qa-gate or fixture unreadable" "BLOCKED"
fi

# T9 — fixture integrity for delivery (nested resource + exec bit).
if [ -f "$TRAPS/T9-delivery/nested/assets/logo.txt" ] && [ -x "$TRAPS/T9-delivery/nested/run.sh" ]; then
  emit "T9" "nested resource and exec bit preserved" "fixtures present; installer check needs a live run" "BLOCKED"
else
  emit "T9" "nested resource and exec bit preserved" "fixtures unreadable" "BLOCKED"
fi

# T10 — fixture integrity for the creator eval.
if [ -f "$TRAPS/T10-creator/candidate-a.md" ] && [ -f "$TRAPS/T10-creator/candidate-b.md" ]; then
  emit "T10" "train/dev selection, held-out once" "fixtures present; eval check needs a live run" "BLOCKED"
else
  emit "T10" "train/dev selection, held-out once" "fixtures unreadable" "BLOCKED"
fi

# T11 — behavioural.
emit "T11" "unknown provider stays unknown" "requires a live build" "BLOCKED"

printf '%s\n' "-------------------------------------------------------------"
echo "trap-verify: $FAILS finding(s), $BLOCKED blocked"

if [ "$FAILS" -gt 0 ]; then
  exit 1
fi
if [ "$BLOCKED" -gt 0 ]; then
  exit 2
fi
exit 0
