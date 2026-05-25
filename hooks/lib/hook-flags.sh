#!/usr/bin/env bash
# hooks/lib/hook-flags.sh — Gating logic for Skill Madness hooks.
#
# Source this file; it reads ATS_HOOK_PROFILE + ATS_DISABLED_HOOKS and exposes
# is_enabled <hook-id> (returns 0 if the hook should run, 1 otherwise).
#
# Gating model (see contracts/hooks/hooks-layer.md §2):
#   ATS_HOOK_PROFILE ∈ {minimal, standard, strict}, default standard.
#     A hook runs only when the active profile is listed in the manifest
#     entry's "profiles" array.
#   ATS_DISABLED_HOOKS — comma-separated hook ids force-disabled regardless
#     of profile.
#
# Usage (from a wrapper that already sourced term.sh):
#   . "$HOOKS_DIR/lib/hook-flags.sh"
#   is_enabled qa-gate && exec ...

# HOOKS_ROOT — the hooks/ tree this lib lives under. Resolved relative to this
# file so the lib works whether sourced from the wrapper or a test harness.
HOOK_FLAGS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_ROOT="$(cd "$HOOK_FLAGS_LIB_DIR/.." && pwd)"
HOOKS_MANIFEST="${HOOKS_MANIFEST:-$HOOKS_ROOT/hooks.manifest.json}"

# ---------------------------------------------------------------------------
# hook_active_profile — normalized profile, defaulting to "standard".
# Unknown values fall back to standard (never wedge the harness).
# ---------------------------------------------------------------------------
hook_active_profile() {
  local p="${ATS_HOOK_PROFILE:-standard}"
  case "$p" in
    minimal|standard|strict) printf '%s' "$p" ;;
    *) printf 'standard' ;;
  esac
}

# ---------------------------------------------------------------------------
# _hook_in_disabled_list <id> — return 0 if <id> is in ATS_DISABLED_HOOKS.
# Bash 3.2 portable: comma-split via IFS, exact match.
# ---------------------------------------------------------------------------
_hook_in_disabled_list() {
  local id="$1"
  local raw="${ATS_DISABLED_HOOKS:-}"
  [[ -z "$raw" ]] && return 1
  local item old_ifs="$IFS"
  IFS=','
  # shellcheck disable=SC2086 # intentional word-splitting on comma
  set -- $raw
  IFS="$old_ifs"
  for item in "$@"; do
    # trim surrounding whitespace
    item="${item#"${item%%[![:space:]]*}"}"
    item="${item%"${item##*[![:space:]]}"}"
    [[ "$item" == "$id" ]] && return 0
  done
  return 1
}

# ---------------------------------------------------------------------------
# _hook_profile_matches <id> — return 0 if the active profile is in the
# manifest entry's profiles array for <id>. python3 stdlib only.
# ---------------------------------------------------------------------------
_hook_profile_matches() {
  local id="$1"
  local profile
  profile="$(hook_active_profile)"
  python3 - "$HOOKS_MANIFEST" "$id" "$profile" <<'PYEOF'
import json, sys
manifest, hid, profile = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(manifest) as f:
        data = json.load(f)
except Exception:
    sys.exit(1)
for h in data.get("hooks", []):
    if h.get("id") == hid:
        sys.exit(0 if profile in (h.get("profiles") or []) else 1)
# Unknown hook id → not enabled
sys.exit(1)
PYEOF
}

# ---------------------------------------------------------------------------
# is_enabled <hook-id> — 0 = run, 1 = skip.
# Disabled list wins over profile membership.
# ---------------------------------------------------------------------------
is_enabled() {
  local id="$1"
  [[ -z "$id" ]] && return 1
  if _hook_in_disabled_list "$id"; then
    return 1
  fi
  if _hook_profile_matches "$id"; then
    return 0
  fi
  return 1
}
