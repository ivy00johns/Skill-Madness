#!/usr/bin/env bash
#
# lint-hooks.sh — Validate the hooks/ layer against the hooks-layer contract.
#
# Checks (contract §5):
#   - hooks.manifest.json parses; every hook id is unique
#   - every manifest entry's `script` exists and is executable
#   - each hook script starts with #!/usr/bin/env bash + set -euo pipefail
#     and sources term.sh
#   - every profile in each entry's `profiles` ⊆ {minimal,standard,strict}
#
# Usage:
#   scripts/lint-hooks.sh [OPTIONS] [HOOKS_DIR]
#
# Options:
#   --quiet    Suppress WARN output
#   --help     Print this and exit
#
# HOOKS_DIR defaults to the repo's hooks/ tree. Passing an alternate dir lets
# tests lint a temp tree.
#
# Exit codes: 0 no errors, 1 at least one error, 2 argument failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------------------
# CLI state
# ---------------------------------------------------------------------------
QUIET=false
HOOKS_DIR=""

# ---------------------------------------------------------------------------
# Issue tracking (mirrors lint-skills.sh)
# ---------------------------------------------------------------------------
ERRORS=()
WARNS=()

record_error() { ERRORS+=("$1"); }
record_warn()  { WARNS+=("$1"); }

# emit_issue <severity> <file> <message>
emit_issue() {
  local sev="$1" file="$2" msg="$3"
  case "$sev" in
    ERROR) record_error "${file}: ${msg}" ;;
    WARN)  record_warn  "${file}: ${msg}" ;;
  esac
}

# ---------------------------------------------------------------------------
# Manifest parsing helpers (python3 stdlib only)
# ---------------------------------------------------------------------------

# manifest_ids <manifest> — print one hook id per line.
manifest_ids() {
  python3 - "$1" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for h in data.get("hooks", []):
    print(h.get("id", ""))
PYEOF
}

# manifest_field <manifest> <id> <field> — print a scalar field for a hook id.
manifest_field() {
  python3 - "$1" "$2" "$3" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for h in data.get("hooks", []):
    if h.get("id") == sys.argv[2]:
        print(h.get(sys.argv[3], ""))
        break
PYEOF
}

# manifest_profiles <manifest> <id> — print one profile per line.
manifest_profiles() {
  python3 - "$1" "$2" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for h in data.get("hooks", []):
    if h.get("id") == sys.argv[2]:
        for p in (h.get("profiles") or []):
            print(p)
        break
PYEOF
}

# ---------------------------------------------------------------------------
# lint_hooks <hooks_dir>
# ---------------------------------------------------------------------------
lint_hooks() {
  local hooks_dir="$1"
  local manifest="$hooks_dir/hooks.manifest.json"

  if [[ ! -d "$hooks_dir" ]]; then
    emit_issue ERROR "$hooks_dir" "hooks directory not found"
    return
  fi

  if [[ ! -f "$manifest" ]]; then
    emit_issue ERROR "$manifest" "hooks.manifest.json not found"
    return
  fi

  # Manifest must parse.
  if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$manifest" 2>/dev/null; then
    emit_issue ERROR "$manifest" "hooks.manifest.json does not parse as JSON"
    return
  fi

  # Wrapper must exist and be executable.
  local wrapper="$hooks_dir/run-with-flags.sh"
  if [[ ! -f "$wrapper" ]]; then
    emit_issue ERROR "$wrapper" "run-with-flags.sh wrapper missing"
  elif [[ ! -x "$wrapper" ]]; then
    emit_issue ERROR "$wrapper" "run-with-flags.sh is not executable"
  fi

  # Collect ids; check uniqueness.
  local ids_file
  ids_file="$(mktemp "${TMPDIR:-/tmp}/ats-hooks-ids.XXXXXX")"
  # shellcheck disable=SC2064
  trap "rm -f '$ids_file'" RETURN
  manifest_ids "$manifest" > "$ids_file"

  local dup
  dup="$(sort "$ids_file" | uniq -d | grep -v '^$' || true)"
  if [[ -n "$dup" ]]; then
    while IFS= read -r d; do
      [[ -z "$d" ]] && continue
      emit_issue ERROR "$manifest" "duplicate hook id '$d'"
    done <<< "$dup"
  fi

  # Per-hook checks.
  local id
  while IFS= read -r id; do
    [[ -z "$id" ]] && continue

    local script_rel script_path
    script_rel="$(manifest_field "$manifest" "$id" "script")"
    if [[ -z "$script_rel" ]]; then
      emit_issue ERROR "$manifest" "hook '$id' has no 'script' field"
      continue
    fi
    script_path="$hooks_dir/$script_rel"

    if [[ ! -f "$script_path" ]]; then
      emit_issue ERROR "$script_path" "hook '$id' script does not exist"
      continue
    fi
    if [[ ! -x "$script_path" ]]; then
      emit_issue ERROR "$script_path" "hook '$id' script is not executable"
    fi

    # Header checks apply to shell scripts only (.sh).
    if [[ "$script_path" == *.sh ]]; then
      local first_line
      first_line="$(head -n1 "$script_path")"
      if [[ "$first_line" != "#!/usr/bin/env bash" ]]; then
        emit_issue ERROR "$script_path" "hook '$id' must start with '#!/usr/bin/env bash'"
      fi
      if ! grep -q 'set -euo pipefail' "$script_path"; then
        emit_issue ERROR "$script_path" "hook '$id' must contain 'set -euo pipefail'"
      fi
      if ! grep -q 'term\.sh' "$script_path"; then
        emit_issue ERROR "$script_path" "hook '$id' must source term.sh"
      fi
    fi

    # Profiles ⊆ {minimal,standard,strict}.
    local p
    while IFS= read -r p; do
      [[ -z "$p" ]] && continue
      case "$p" in
        minimal|standard|strict) : ;;
        *) emit_issue ERROR "$manifest" "hook '$id' has invalid profile '$p' (allowed: minimal,standard,strict)" ;;
      esac
    done < <(manifest_profiles "$manifest" "$id")
  done < "$ids_file"
}

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print_report() {
  local n_errors=${#ERRORS[@]}
  local n_warns=${#WARNS[@]}

  printf 'Linting hooks layer...\n\n'

  local issue
  for issue in "${ERRORS[@]+"${ERRORS[@]}"}"; do
    printf '%-6s %s\n' 'ERROR' "$issue"
  done
  if ! $QUIET; then
    for issue in "${WARNS[@]+"${WARNS[@]}"}"; do
      printf '%-6s %s\n' 'WARN' "$issue"
    done
  fi

  printf '\nResults: %d error(s), %d warning(s).\n' "$n_errors" "$n_warns"
  if (( n_errors > 0 )); then
    printf 'FAILED: fix the errors above.\n'
  else
    printf 'PASSED\n'
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
usage() {
  sed -n '3,28p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --quiet)   QUIET=true; shift ;;
      --help|-h) usage ;;
      -*)        ats_err "Unknown option: $1"; exit 2 ;;
      *)         HOOKS_DIR="$1"; shift ;;
    esac
  done

  [[ -z "$HOOKS_DIR" ]] && HOOKS_DIR="$REPO_ROOT/hooks"

  lint_hooks "$HOOKS_DIR"
  print_report

  (( ${#ERRORS[@]} > 0 )) && exit 1
  exit 0
}

main "$@"
