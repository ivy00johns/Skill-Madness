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

FAILS=0
BLOCKED=0

emit() { # trap | expected | observed | verdict
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4"
  case "$4" in
    FAIL|REPRO) FAILS=$((FAILS + 1)) ;;
    BLOCKED) BLOCKED=$((BLOCKED + 1)) ;;
  esac
}

run_guard() { # guard_path target_dir -> sets global rc
  rc=3
  if [ ! -f "$1" ]; then
    return
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    return
  fi
  python3 "$1" --root "$2" --quiet >/dev/null 2>&1
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

# T2 — inline layout; run the design-token guard against the fixture.
if [ -f "$DESIGN_GUARD" ] && [ -d "$TRAPS/T2-inline" ]; then
  run_guard "$DESIGN_GUARD" "$TRAPS/T2-inline"
  case "$rc" in
    1) emit "T2" "inline layout finding (exit 1)" "guard exit 1" "PASS" ;;
    0) emit "T2" "inline layout finding (exit 1)" "guard exit 0 (missed)" "FAIL" ;;
    *) emit "T2" "inline layout finding (exit 1)" "guard could not run (exit $rc)" "BLOCKED" ;;
  esac
else
  emit "T2" "inline layout finding (exit 1)" "guard or fixture unreadable" "BLOCKED"
fi

# T3 — duplicate declarations; run the class guard against the fixture.
if [ -f "$CLASS_GUARD" ] && [ -d "$TRAPS/T3-hash" ]; then
  run_guard "$CLASS_GUARD" "$TRAPS/T3-hash"
  case "$rc" in
    1) emit "T3" "duplicate declaration group found" "guard exit 1" "PASS" ;;
    0) emit "T3" "duplicate declaration group found" "guard exit 0 (gap: .css not scanned)" "FAIL" ;;
    *) emit "T3" "duplicate declaration group found" "guard could not run (exit $rc)" "BLOCKED" ;;
  esac
else
  emit "T3" "duplicate declaration group found" "guard or fixture unreadable" "BLOCKED"
fi

# T4 — copied chrome; no generic shared-layout guard exists yet.
if [ -d "$_root/skills/workflows/shared-layout-guard" ]; then
  emit "T4" "copied chrome flagged" "guard present; run against fixture" "BLOCKED"
else
  emit "T4" "copied chrome flagged" "no shared-layout guard exists (known gap)" "BLOCKED"
fi

# T5 — behavioural.
emit "T5" "explicit attended plan or refusal" "requires a live build" "BLOCKED"

# T6 — behavioural.
emit "T6" "wrapper cancels at cap" "requires a live build" "BLOCKED"

# T7 — behavioural.
emit "T7" "frozen verifier digests" "requires a live build" "BLOCKED"

# T8 — reproduce the vulnerable checker: does it report clean on unreadable input?
CHECKER="$TRAPS/T8-qa/unreadable-checker.sh"
if [ -x "$CHECKER" ]; then
  out="$("$CHECKER" /nonexistent-path-for-trap-verify 2>/dev/null)"
  rc=$?
  if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -qi clean; then
    emit "T8" "enforcement fails closed on unreadable input" "checker returned clean (reproduced)" "REPRO"
  else
    emit "T8" "enforcement fails closed on unreadable input" "checker did not return clean" "PASS"
  fi
else
  emit "T8" "enforcement fails closed on unreadable input" "checker unreadable" "BLOCKED"
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
