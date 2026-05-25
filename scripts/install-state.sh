#!/usr/bin/env bash
#
# install-state.sh — Inspect and manage recorded install-state.
#
# Reads <root>/.claude/.ats-install-state.json (written by install-apply.sh).
#
# Usage:
#   scripts/install-state.sh list      [--root DIR]
#   scripts/install-state.sh drift     [--root DIR]
#   scripts/install-state.sh uninstall [--root DIR] [--dry-run]
#   scripts/install-state.sh repair    [--root DIR] [--dry-run]
#
# Commands:
#   list       Show the recorded install-state (files + hashes).
#   drift      Compare recorded sha256 vs on-disk; report added/changed/removed.
#              Exit 1 if any drift, 0 if pristine.
#   uninstall  Remove recorded files and clear the state file.
#   repair     Re-copy files whose on-disk hash != recorded hash. Needs the
#              source still available — repair re-resolves source via a plan, so
#              pass --plan to point at the plan that produced the state, or rely
#              on the source path recorded in a sibling plan.
#
# Options:
#   --root DIR    Destination base (default: $HOME). Must match the apply root.
#   --plan FILE   (repair only) plan JSON to source files from. If omitted,
#                 repair uses the source paths embedded in the plan when state
#                 was written alongside one (see --plan on apply). Optional.
#   --dry-run     For uninstall/repair: print actions, write nothing.
#   --help        Show this help and exit.
#
# Exit codes: 0 success / no drift; 1 drift detected; 2 argument/state error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"
# shellcheck source=scripts/lib/install-state.sh
. "$LIB_DIR/install-state.sh"

usage() {
  sed -n '3,38p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

# ---------------------------------------------------------------------------
cmd_list() {
  local state="$1"
  if [[ ! -f "$state" ]]; then
    ats_warn "no install-state at $state"
    return 0
  fi
  ATS_STATE="$state" python3 - <<'PYEOF'
import json, os
state_path = os.environ["ATS_STATE"]
with open(state_path) as f:
    state = json.load(f)
print("profile:    %s" % state.get("profile"))
print("tools:      %s" % ", ".join(state.get("tools", [])))
print("applied_at: %s" % state.get("applied_at"))
files = state.get("files", [])
print("files:      %d" % len(files))
for fr in files:
    print("  [%s] %s  %s" % (fr.get("tool"), fr.get("sha256", "")[:12], fr.get("dest")))
PYEOF
}

# ---------------------------------------------------------------------------
cmd_drift() {
  local state="$1"
  if [[ ! -f "$state" ]]; then
    ats_warn "no install-state at $state (nothing to drift-check)"
    return 0
  fi
  local rc=0
  ATS_STATE="$state" python3 - <<'PYEOF' || rc=$?
import hashlib, json, os, sys
state_path = os.environ["ATS_STATE"]
with open(state_path) as f:
    state = json.load(f)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

changed = []
removed = []
for fr in state.get("files", []):
    dest = fr["dest"]
    want = fr["sha256"]
    if not os.path.isfile(dest):
        removed.append(dest)
    elif sha256(dest) != want:
        changed.append(dest)

for d in removed:
    print("removed: %s" % d)
for d in changed:
    print("changed: %s" % d)

if removed or changed:
    print("DRIFT: %d changed, %d removed" % (len(changed), len(removed)))
    sys.exit(1)
print("pristine: no drift")
PYEOF
  return "$rc"
}

# ---------------------------------------------------------------------------
cmd_uninstall() {
  local state="$1" dry_run="$2"
  if [[ ! -f "$state" ]]; then
    ats_warn "no install-state at $state (nothing to uninstall)"
    return 0
  fi
  ATS_STATE="$state" ATS_DRY_RUN="$dry_run" python3 - <<'PYEOF'
import json, os, sys
state_path = os.environ["ATS_STATE"]
dry_run = os.environ["ATS_DRY_RUN"] == "1"
with open(state_path) as f:
    state = json.load(f)

removed = 0
for fr in state.get("files", []):
    dest = fr["dest"]
    if os.path.isfile(dest) or os.path.islink(dest):
        if dry_run:
            print("would remove: %s" % dest)
        else:
            os.remove(dest)
            print("removed: %s" % dest)
        removed += 1
    else:
        print("absent: %s" % dest)

if not dry_run:
    os.remove(state_path)
    print("cleared state: %s" % state_path)
else:
    print("would clear state: %s" % state_path)
sys.stderr.write("[uninstall] removed=%d dry_run=%s\n" % (removed, dry_run))
PYEOF
}

# ---------------------------------------------------------------------------
# repair: re-copy files whose on-disk hash != recorded hash. The recorded state
# carries dest+sha256 but not source; we re-resolve sources from --plan if given,
# else from a plan written next to the state (.ats-install-plan.json) if present.
cmd_repair() {
  local state="$1" dry_run="$2" plan="$3"
  if [[ ! -f "$state" ]]; then
    ats_warn "no install-state at $state (nothing to repair)"
    return 0
  fi
  # Auto-discover a sibling plan if none provided.
  if [[ -z "$plan" ]]; then
    local sibling
    sibling="$(dirname "$state")/.ats-install-plan.json"
    [[ -f "$sibling" ]] && plan="$sibling"
  fi
  if [[ -z "$plan" || ! -f "$plan" ]]; then
    ats_err "repair needs a plan to source files from (--plan FILE); none found"
    return 2
  fi
  ATS_STATE="$state" ATS_PLAN="$plan" ATS_DRY_RUN="$dry_run" python3 - <<'PYEOF'
import hashlib, json, os, shutil, sys
state_path = os.environ["ATS_STATE"]
plan_path = os.environ["ATS_PLAN"]
dry_run = os.environ["ATS_DRY_RUN"] == "1"

with open(state_path) as f:
    state = json.load(f)
with open(plan_path) as f:
    plan = json.load(f)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# dest -> source map from the plan.
src_by_dest = {op["dest"]: op["source"] for op in plan.get("operations", [])}

repaired = 0
for fr in state.get("files", []):
    dest = fr["dest"]
    want = fr["sha256"]
    on_disk = sha256(dest) if os.path.isfile(dest) else None
    if on_disk == want:
        continue
    src = src_by_dest.get(dest)
    if not src or not os.path.isfile(src):
        sys.stderr.write("[repair] WARN no source for %s\n" % dest)
        continue
    if dry_run:
        print("would repair: %s" % dest)
    else:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.islink(dest):
            os.unlink(dest)
        shutil.copyfile(src, dest)
        print("repaired: %s" % dest)
    repaired += 1

if repaired == 0:
    print("nothing to repair")
sys.stderr.write("[repair] repaired=%d dry_run=%s\n" % (repaired, dry_run))
PYEOF
}

# ---------------------------------------------------------------------------
main() {
  local subcmd="${1:-}"
  case "$subcmd" in
    list|drift|uninstall|repair) shift ;;
    --help|-h|"") usage ;;
    *) ats_err "Unknown command: $subcmd"; exit 2 ;;
  esac

  local root="${HOME:-/tmp}"
  local dry_run=0
  local plan=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --root)    root="${2:?'--root requires a value'}"; shift 2 ;;
      --plan)    plan="${2:?'--plan requires a value'}"; shift 2 ;;
      --dry-run) dry_run=1; shift ;;
      --help|-h) usage ;;
      *)         ats_err "Unknown option: $1"; exit 2 ;;
    esac
  done

  local state="$root/.claude/.ats-install-state.json"

  case "$subcmd" in
    list)      cmd_list "$state" ;;
    drift)     cmd_drift "$state" ;;
    uninstall) cmd_uninstall "$state" "$dry_run" ;;
    repair)    cmd_repair "$state" "$dry_run" "$plan" ;;
  esac
}

main "$@"
