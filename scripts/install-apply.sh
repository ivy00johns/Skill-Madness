#!/usr/bin/env bash
#
# install-apply.sh — Execute a plan produced by install-plan.sh + record state.
#
# Consumes a serializable plan, performs the file operations (respecting
# --dry-run), then writes install-state to <root>/.claude/.ats-install-state.json
# with the content hash of every installed file. Idempotent: re-applying an
# unchanged plan is a no-op.
#
# Usage:
#   scripts/install-apply.sh --plan FILE [--root DIR] [--dry-run]
#
# Options:
#   --plan FILE   Plan JSON from install-plan.sh. Required.
#   --root DIR    Destination base (default: $HOME). The plan's dests already
#                 encode the root; --root is used to locate the state file and
#                 must match the root the plan was resolved against.
#   --dry-run     Print actions; write nothing.
#   --help        Show this help and exit.
#
# install-state shape:
#   { schema_version, applied_at, profile, tools,
#     files:[ {dest, sha256, tool} ] }
#
# Exit codes: 0 success, 2 argument/plan error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"
# shellcheck source=scripts/lib/install-state.sh
. "$LIB_DIR/install-state.sh"

usage() {
  sed -n '3,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

main() {
  local plan=""
  local root="${HOME:-/tmp}"
  local dry_run=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan)    plan="${2:?'--plan requires a value'}"; shift 2 ;;
      --root)    root="${2:?'--root requires a value'}"; shift 2 ;;
      --dry-run) dry_run=1; shift ;;
      --help|-h) usage ;;
      *)         ats_err "Unknown option: $1"; exit 2 ;;
    esac
  done

  if [[ -z "$plan" ]]; then ats_err "--plan is required"; exit 2; fi
  if [[ ! -f "$plan" ]]; then ats_err "plan not found: $plan"; exit 2; fi

  local state_file="$root/.claude/.ats-install-state.json"
  local applied_at
  applied_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  local rc=0
  ATS_PLAN="$plan" \
  ATS_ROOT="$root" \
  ATS_STATE="$state_file" \
  ATS_APPLIED_AT="$applied_at" \
  ATS_DRY_RUN="$dry_run" \
  python3 - <<'PYEOF' || rc=$?
import hashlib, json, os, shutil, sys

plan_path  = os.environ["ATS_PLAN"]
state_path = os.environ["ATS_STATE"]
applied_at = os.environ["ATS_APPLIED_AT"]
dry_run    = os.environ["ATS_DRY_RUN"] == "1"

with open(plan_path) as f:
    plan = json.load(f)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

ops = plan.get("operations", [])
created = updated = skipped = 0
files = []

for op in ops:
    src = op["source"]
    dest = op["dest"]
    tool = op["tool"]
    want = op["sha256"]

    if not os.path.isfile(src):
        sys.stderr.write("[apply] WARN missing source: %s\n" % src)
        continue

    # Recompute the on-disk action at apply time (the plan may be stale).
    if os.path.isfile(dest):
        action = "skip" if sha256(dest) == want else "overwrite"
    else:
        action = "create"

    if action == "skip":
        skipped += 1
    else:
        if not dry_run:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            # Replace symlinks with regular files (do not follow).
            if os.path.islink(dest):
                os.unlink(dest)
            shutil.copyfile(src, dest)
        if action == "create":
            created += 1
        else:
            updated += 1

    files.append({"dest": dest, "sha256": want, "tool": tool})

state = {
    "schema_version": plan.get("schema_version", 1),
    "applied_at": applied_at,
    "profile": plan.get("profile"),
    "tools": plan.get("tools", []),
    "files": sorted(files, key=lambda x: x["dest"]),
}

if not dry_run:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")

sys.stderr.write("[apply] created=%d updated=%d skipped=%d dry_run=%s\n"
                 % (created, updated, skipped, dry_run))
print("created=%d updated=%d skipped=%d" % (created, updated, skipped))
PYEOF

  if [[ "$rc" -ne 0 ]]; then ats_err "apply failed"; exit 2; fi
  if [[ "$dry_run" -eq 1 ]]; then
    ats_info "dry-run: no files written, no state recorded"
  else
    # Stash a copy of the plan beside the state so `install-state.sh repair`
    # can re-resolve source paths without re-running install-plan.
    mkdir -p "$(dirname "$state_file")"
    cp "$plan" "$(dirname "$state_file")/.ats-install-plan.json"
    ats_ok "Applied plan; state: $state_file"
  fi
}

main "$@"
