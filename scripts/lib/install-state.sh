#!/usr/bin/env bash
# lib/install-state.sh — Shared helpers for the plan/apply install discipline.
#
# Sourced by install-plan.sh, install-apply.sh, install-state.sh. Provides:
#   - sha256_file        portable content hashing (shasum -a 256 / sha256sum)
#   - category_for_slug  canonical slug -> category map (from skills/ on disk)
#   - profile_categories read a profile's category list from manifests/profiles.json
#   - resolve_dest       (tool, category, slug, relpath, root) -> absolute dest path
#
# Bash 3.2 portable. No assoc arrays, no mapfile. python3 stdlib for JSON.
#
# Usage:
#   . "$(dirname "$0")/lib/install-state.sh"

# ---------------------------------------------------------------------------
# Hashing — detect once which tool is available.
# ---------------------------------------------------------------------------
_ATS_HASH_CMD=""
_ats_detect_hash() {
  if [[ -n "$_ATS_HASH_CMD" ]]; then return 0; fi
  if command -v shasum >/dev/null 2>&1; then
    _ATS_HASH_CMD="shasum"
  elif command -v sha256sum >/dev/null 2>&1; then
    _ATS_HASH_CMD="sha256sum"
  else
    _ATS_HASH_CMD="none"
  fi
}

# sha256_file <path> — print the hex sha256 of a file (no filename).
sha256_file() {
  local path="$1"
  _ats_detect_hash
  case "$_ATS_HASH_CMD" in
    shasum)    shasum -a 256 "$path" | awk '{print $1}' ;;
    sha256sum) sha256sum "$path"     | awk '{print $1}' ;;
    *) printf 'ERROR: no sha256 tool (shasum/sha256sum)\n' >&2; return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# Canonical slug -> category map, built from skills/ on disk.
# Mirrors catalog.sh / convert.sh derive_category_slug: a skill is a dir under
# skills/ containing SKILL.md; category is the parent dir name, except a skill
# living directly under skills/ (orchestrator) whose category == its slug.
# Excludes archive/ and in-progress/.
# ---------------------------------------------------------------------------
# _ATS_SLUG_CAT holds "slug<TAB>category" lines; populated once.
_ATS_SLUG_CAT=""
_ats_build_slug_cat() {
  local skills_root="$1"
  if [[ -n "$_ATS_SLUG_CAT" ]]; then return 0; fi
  local file dir slug parent cat
  _ATS_SLUG_CAT="$(
    find "$skills_root" -name SKILL.md -type f \
      | grep -v '/archive/' \
      | grep -v '/in-progress/' \
      | sort \
      | while IFS= read -r file; do
          dir="$(dirname "$file")"
          slug="$(basename "$dir")"
          parent="$(basename "$(dirname "$dir")")"
          if [[ "$parent" == "$(basename "$skills_root")" ]]; then
            cat="$slug"
          else
            cat="$parent"
          fi
          printf '%s\t%s\n' "$slug" "$cat"
        done
  )"
}

# category_for_slug <slug> <skills_root> — print the category, or "" if unknown.
category_for_slug() {
  local slug="$1" skills_root="$2"
  _ats_build_slug_cat "$skills_root"
  printf '%s\n' "$_ATS_SLUG_CAT" | awk -F'\t' -v s="$slug" '$1==s {print $2; exit}'
}

# ---------------------------------------------------------------------------
# profile_categories <profile> <profiles_json> — print one category per line.
# Empty output (and exit 1) if the profile is unknown.
# ---------------------------------------------------------------------------
profile_categories() {
  local profile="$1" json="$2"
  python3 - "$json" "$profile" <<'PYEOF'
import json, sys
path, profile = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
profiles = data.get("profiles", data)
p = profiles.get(profile)
if p is None:
    sys.exit(1)
for c in p.get("categories", []):
    print(c)
PYEOF
}

# ---------------------------------------------------------------------------
# resolve_dest <tool> <category> <slug> <relpath> <root>
# Map an integration source (relative to integrations/<tool>/) to its install
# destination under <root>. <root> overrides BOTH ~ (HOME) and $PWD bases from
# the install-locations matrix so tests never touch real locations.
#
#   user-scope  (~/...)   -> <root>/<tail-after-HOME>
#   project-scope ($PWD)  -> <root>/<tail-after-PWD>
#
# relpath is the path of the source file relative to integrations/<tool>/.
# ---------------------------------------------------------------------------
resolve_dest() {
  local tool="$1" category="$2" slug="$3" relpath="$4" root="$5"
  case "$tool" in
    claude-code)
      # ~/.claude/skills/<category>/<slug>/<...>  ; relpath already = <category>/<slug>/<file>
      printf '%s/.claude/skills/%s\n' "$root" "$relpath"
      ;;
    copilot)
      # ~/.github/agents/ AND ~/.copilot/agents/ — emit github path; apply mirrors.
      printf '%s/.github/agents/%s\n' "$root" "$relpath"
      ;;
    antigravity)
      printf '%s/.gemini/antigravity/skills/%s\n' "$root" "$relpath"
      ;;
    gemini-cli)
      printf '%s/.gemini/extensions/alltheskills/%s\n' "$root" "$relpath"
      ;;
    opencode)
      # source root is integrations/opencode/agents/ ; dest $PWD/.opencode/agents/
      printf '%s/.opencode/agents/%s\n' "$root" "$relpath"
      ;;
    cursor)
      printf '%s/.cursor/rules/%s\n' "$root" "$relpath"
      ;;
    openclaw)
      printf '%s/.openclaw/alltheskills/%s\n' "$root" "$relpath"
      ;;
    qwen)
      printf '%s/.qwen/agents/%s\n' "$root" "$relpath"
      ;;
    kimi)
      printf '%s/.config/kimi/agents/%s\n' "$root" "$relpath"
      ;;
    aider)
      printf '%s/CONVENTIONS.md\n' "$root"
      ;;
    windsurf)
      printf '%s/.windsurfrules\n' "$root"
      ;;
    *)
      return 1
      ;;
  esac
}

# ---------------------------------------------------------------------------
# integ_source_subdir <tool> — the subdir within integrations/<tool>/ that the
# matrix treats as the source root (so relpaths line up with resolve_dest).
# Prints "" when the tool root itself is the source root.
# ---------------------------------------------------------------------------
integ_source_subdir() {
  local tool="$1"
  case "$tool" in
    opencode) printf 'agents' ;;
    qwen)     printf 'agents' ;;
    gemini-cli) printf 'skills' ;;
    cursor)   printf 'rules' ;;
    *)        printf '' ;;
  esac
}
