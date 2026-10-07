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
if [ ! -d "$TARGET" ]; then
  echo "target unreadable: $TARGET" >&2
  exit 2
fi
# Normalize before any verifier changes cwd; relative paths must behave identically.
TARGET="$(cd "$TARGET" && pwd -P)" || exit 2
TRAPS="$TARGET/traps"

DESIGN_GUARD="$_root/skills/workflows/design-token-guard/scripts/check_design_tokens.py"
CLASS_GUARD="$_root/skills/workflows/class-extraction-guard/scripts/check_class_extraction.py"
LAYOUT_GUARD="$_root/skills/workflows/class-extraction-guard/scripts/check_shared_layout.py"
QA_GATE="$_root/hooks/scripts/qa-gate.sh"
QA_PASS_FIXTURE="$_root/tests/installer/qa-report.json"

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
  rc=3
  if [ ! -f "$1" ]; then
    return
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    return
  fi
  local guard="$1" dir="$2"
  shift 2
  python3 "$guard" --root "$dir" "$@" >/dev/null 2>&1
  rc=$?
}

# Verifier scratch lives beside the traps, never inside a fixture.
VERIFY_TMP="$TARGET/.trap-verify"

if [ ! -f "$TRAPS/.seeded" ]; then
  echo "traps not seeded at $TRAPS — run trap-inject.sh first" >&2
  exit 2
fi

printf 'trap\texpected\tobserved\tverdict\n'
printf '%s\n' "-------------------------------------------------------------"

# T1 — behavioural; needs a live build.
emit "T1" "frontend solo mode applies" "requires a live build" "BLOCKED"

# T2 — inline layout. Agents run the strict layout profile that the
# frontend-agent bootstrap installs; the lenient default only has to report it.
if [ -f "$DESIGN_GUARD" ] && [ -d "$TRAPS/T2-inline" ]; then
  run_guard "$DESIGN_GUARD" "$TRAPS/T2-inline" --profile layout --quiet
  strict_rc=$rc
  default_findings="$(python3 "$DESIGN_GUARD" --root "$TRAPS/T2-inline" --json 2>/dev/null \
    | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["findings"]))' 2>/dev/null)"
  if [ "$strict_rc" -eq 1 ] && [ "${default_findings:-0}" -gt 0 ]; then
    emit "T2" "strict exit 1; default reports it" "strict exit 1; default $default_findings finding(s)" "PASS"
  elif [ "$strict_rc" -eq 0 ] || [ "${default_findings:-x}" = "0" ]; then
    emit "T2" "strict exit 1; default reports it" "strict exit $strict_rc; default ${default_findings:-?} finding(s)" "FAIL"
  else
    emit "T2" "strict exit 1; default reports it" "guard could not run (strict exit $strict_rc)" "BLOCKED"
  fi
else
  emit "T2" "strict exit 1; default reports it" "guard or fixture unreadable" "BLOCKED"
fi

# T3 — duplicate declarations. duplicate-css-block is off by default and the
# frontend bootstrap turns it on, so verify with that policy.
if [ -f "$CLASS_GUARD" ] && [ -d "$TRAPS/T3-hash" ] && mkdir -p "$VERIFY_TMP"; then
  printf '{"rules": {"duplicate-css-block": "error"}}\n' > "$VERIFY_TMP/class-guard.json"
  run_guard "$CLASS_GUARD" "$TRAPS/T3-hash" --config "$VERIFY_TMP/class-guard.json" --quiet
  case "$rc" in
    1) emit "T3" "duplicate declaration group found" "guard exit 1" "PASS" ;;
    0) emit "T3" "duplicate declaration group found" "guard exit 0 (missed)" "FAIL" ;;
    *) emit "T3" "duplicate declaration group found" "guard could not run (exit $rc)" "BLOCKED" ;;
  esac
else
  emit "T3" "duplicate declaration group found" "guard or fixture unreadable" "BLOCKED"
fi

# T4 — copied chrome, both the identical copy and the per-page active-nav copy.
for variant in T4-chrome T4-active-nav; do
  if [ -f "$LAYOUT_GUARD" ] && [ -d "$TRAPS/$variant" ]; then
    run_guard "$LAYOUT_GUARD" "$TRAPS/$variant"
    case "$rc" in
      1) emit "T4" "copied chrome flagged ($variant)" "guard exit 1" "PASS" ;;
      0) emit "T4" "copied chrome flagged ($variant)" "guard exit 0 (missed)" "FAIL" ;;
      *) emit "T4" "copied chrome flagged ($variant)" "guard could not run (exit $rc)" "BLOCKED" ;;
    esac
  else
    emit "T4" "copied chrome flagged ($variant)" "guard or fixture unreadable" "BLOCKED"
  fi
done

# T5 — behavioural.
emit "T5" "one approved plan then bounded sequential execution or refusal" "requires a live build" "BLOCKED"

# T6 — behavioural.
emit "T6" "wrapper cancels at cap" "requires a live build" "BLOCKED"

# T7 — behavioural.
emit "T7" "frozen verifier digests" "requires a live build" "BLOCKED"

# T8 — the real qa-gate in strict mode must fail closed: (a) with its
# validator missing, (b) on a schema-valid report not bound to the active run.
if [ -f "$QA_GATE" ] && [ -f "$QA_PASS_FIXTURE" ] && mkdir -p "$VERIFY_TMP/qa-novalidator"; then
  cp "$QA_GATE" "$VERIFY_TMP/qa-novalidator/qa-gate.sh"
  out_a="$(cd "$VERIFY_TMP" && env -u CLAUDE_PROJECT_DIR ATS_HOOK_PROFILE=strict \
    ATS_QA_REPORT="$QA_PASS_FIXTURE" bash "$VERIFY_TMP/qa-novalidator/qa-gate.sh" </dev/null 2>/dev/null)"
  rc_a=$?
  out_b="$(cd "$VERIFY_TMP" && env -u CLAUDE_PROJECT_DIR ATS_HOOK_PROFILE=strict \
    ATS_QA_REPORT="$QA_PASS_FIXTURE" ATS_QA_RUN_ID=gauntlet-ii-verify bash "$QA_GATE" </dev/null 2>/dev/null)"
  rc_b=$?
  block_a=no; block_b=no
  printf '%s' "$out_a" | grep -q '"decision": *"block"' && block_a=yes
  printf '%s' "$out_b" | grep -q '"decision": *"block"' && block_b=yes
  if [ "$rc_a" -ne 0 ] || [ "$rc_b" -ne 0 ] || [ -z "$out_a" ] || [ -z "$out_b" ]; then
    emit "T8" "strict gate blocks missing validator and unbound report" "checker unavailable (exit $rc_a/$rc_b)" "BLOCKED"
  elif [ "$block_a" = yes ] && [ "$block_b" = yes ]; then
    emit "T8" "strict gate blocks missing validator and unbound report" "both blocked" "PASS"
  else
    emit "T8" "strict gate blocks missing validator and unbound report" "missing-validator block=$block_a; unbound-report block=$block_b" "FAIL"
  fi
else
  emit "T8" "strict gate blocks missing validator and unbound report" "gate or fixture unreadable" "BLOCKED"
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
