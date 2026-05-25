#!/usr/bin/env bash
#
# catalog.sh — Catalog-as-CI-invariant for Skill Madness.
#
# The filesystem is the single source of truth for the advertised skill counts.
# This script computes the true inventory from disk and either checks the
# hard-coded counts in README.md + plugin.json + marketplace.json against it
# (--check), rewrites those counts to match (--sync), or prints the table
# (--text).
#
# Contract: contracts/installer/catalog-invariant.md v1.0.0
#
# Usage:
#   scripts/catalog.sh [--check | --sync | --text] [--help]
#
# Options:
#   --check   (default) compare asserted counts to disk; exit 1 on any mismatch.
#   --sync    rewrite asserted counts in README/plugin.json/marketplace.json.
#   --text    print total + per-category table to stdout.
#   --help    print this and exit.
#
# A skill = a directory under skills/ containing a SKILL.md, EXCLUDING anything
# under skills/archive/ and skills/in-progress/. Category = the immediate
# subdirectory of skills/ the skill lives in (orchestrator/SKILL.md at the
# category root counts as category 'orchestrator').
#
# Exit codes: 0 ok / clean, 1 drift detected (--check), 2 argument failure.
#
# Bash 3.2 portable: no associative arrays, no mapfile.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"

README="$REPO_ROOT/README.md"
PLUGIN_JSON="$REPO_ROOT/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$REPO_ROOT/.claude-plugin/marketplace.json"

# The six known categories, fixed order for stable output.
CATEGORIES="orchestrator roles contracts meta git workflows"

# ---------------------------------------------------------------------------
# Disk inventory
# ---------------------------------------------------------------------------

# category_of <SKILL.md path relative-or-absolute>
# Echoes the category for a SKILL.md file.
category_of() {
  local f="$1" d parent
  d="$(dirname "$f")"
  parent="$(basename "$(dirname "$d")")"
  if [[ "$parent" == "skills" ]]; then
    basename "$d"
  else
    echo "$parent"
  fi
}

# count_total <skills_root>  — total active skills.
count_total() {
  local root="$1"
  find "$root" -name SKILL.md -type f 2>/dev/null \
    | grep -v "$root/archive/" \
    | grep -v "$root/in-progress/" \
    | wc -l \
    | tr -d ' '
}

# count_category <skills_root> <category> — active skills in one category.
count_category() {
  local root="$1" cat="$2" n=0 f c
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    c="$(category_of "$f")"
    [[ "$c" == "$cat" ]] && n=$(( n + 1 ))
  done < <(find "$root" -name SKILL.md -type f 2>/dev/null \
             | grep -v "$root/archive/" \
             | grep -v "$root/in-progress/")
  echo "$n"
}

# ---------------------------------------------------------------------------
# --text
# ---------------------------------------------------------------------------
cmd_text() {
  local total cat n sum=0
  total="$(count_total "$SKILLS_ROOT")"
  ats_header "Skill catalog (disk truth)"
  printf '  %-16s %s\n' "CATEGORY" "COUNT"
  printf '  %-16s %s\n' "----------------" "-----"
  for cat in $CATEGORIES; do
    n="$(count_category "$SKILLS_ROOT" "$cat")"
    sum=$(( sum + n ))
    printf '  %-16s %s\n' "$cat" "$n"
  done
  printf '  %-16s %s\n' "----------------" "-----"
  printf '  %-16s %s\n' "TOTAL" "$total"
  if (( sum != total )); then
    ats_err "category sum ($sum) != total ($total)"
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Mismatch reporting / file rewriting
#
# We use sed for in-place rewrites. To stay portable across BSD (macOS) and GNU
# sed we write to a temp file and move it back (no -i flag differences).
# ---------------------------------------------------------------------------

# sed_replace <file> <sed-expr...> — apply one or more -e exprs portably.
sed_replace() {
  local file="$1"; shift
  local tmp
  tmp="$(mktemp "${TMPDIR:-/tmp}/ats-catalog.XXXXXX")"
  sed "$@" "$file" > "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

# MISMATCHES accumulates human-readable drift lines for --check.
MISMATCHES=()

# check_pattern <file> <label> <grep-ERE> <expected-number> <capture-sed>
# Finds every line matching grep-ERE in file, extracts the embedded number with
# capture-sed, and records a mismatch if it differs from expected. capture-sed
# must turn a matching line into just the number.
check_pattern() {
  local file="$1" label="$2" ere="$3" expected="$4" capture="$5"
  local line got
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    got="$(printf '%s\n' "$line" | sed -E "$capture")"
    [[ -z "$got" ]] && continue
    if [[ "$got" != "$expected" ]]; then
      MISMATCHES+=("$label: found $got, disk says $expected  ($(basename "$file"))")
    fi
  done < <(grep -nE "$ere" "$file" 2>/dev/null || true)
}

# ---------------------------------------------------------------------------
# Per-category README mermaid label config.
# Maps the README label token -> category -> noun (skills|agents).
# Format: "<label-prefix>|<category>|<noun>"
# e.g. "contracts/|contracts|skills"  matches "contracts/ — 2 skills".
# ---------------------------------------------------------------------------
MERMAID_LABELS=(
  "contracts/|contracts|skills"
  "roles/|roles|agents"
  "meta/|meta|skills"
  "git/|git|skills"
  "workflows/|workflows|skills"
)

# ---------------------------------------------------------------------------
# Build the list of (file, label, grep-ERE, expected, capture-sed) tuples that
# describe every asserted count. Emitted via a callback so --check and --sync
# share exactly one definition of "where the counts live".
#
# for_each_assertion <callback>
#   callback <file> <label> <grep-ERE> <expected> <capture-sed> <sync-sed>
# ---------------------------------------------------------------------------
for_each_assertion() {
  local cb="$1"
  local total spec cat noun n

  total="$(count_total "$SKILLS_ROOT")"

  # --- README total-count assertions ---------------------------------------
  # shields badge:  skills-47-success.svg  and alt="47 skills"
  "$cb" "$README" "README badge (skills-N)" \
    'skills-[0-9]+-' "$total" \
    's/.*skills-([0-9]+)-.*/\1/' \
    "s/(skills-)[0-9]+(-)/\1${total}\2/g"

  "$cb" "$README" "README badge alt (N skills)" \
    'alt="[0-9]+ skills"' "$total" \
    's/.*alt="([0-9]+) skills".*/\1/' \
    "s/(alt=\")[0-9]+( skills\")/\1${total}\2/g"

  # Each prose location is targeted by its distinctive surrounding text so we
  # never touch the skill-table row index ("| 47 |") or the per-category
  # mermaid labels ("contracts/ — 2 skills"), which carry different numbers.

  # "N skills, six categories" — feature bullet (~45) and roadmap line (~544).
  "$cb" "$README" "README prose (N skills, six categories)" \
    '[0-9]+ skills, six categories' "$total" \
    's/.*[^0-9]([0-9]+) skills, six categories.*/\1/' \
    "s/[0-9]+( skills, six categories)/${total}\1/g"

  # "all N skills" — install instruction (~80).
  "$cb" "$README" "README prose (installs all N skills)" \
    'all [0-9]+ skills' "$total" \
    's/.*all ([0-9]+) skills.*/\1/' \
    "s/(all )[0-9]+( skills)/\1${total}\2/g"

  # "N skills organized into six categories" — catalog intro (~252).
  "$cb" "$README" "README prose (N skills organized)" \
    '[0-9]+ skills organized' "$total" \
    's/.*[^0-9]([0-9]+) skills organized.*/\1/' \
    "s/[0-9]+( skills organized)/${total}\1/g"

  # "N-skill library" — progressive-disclosure bullet (~43) and status (~49).
  "$cb" "$README" "README prose (N-skill library)" \
    '[0-9]+-skill library' "$total" \
    's/.*[^0-9]([0-9]+)-skill library.*/\1/' \
    "s/[0-9]+(-skill library)/${total}\1/g"

  # --- README per-category mermaid labels ("contracts/ — 2 skills") ---------
  for spec in "${MERMAID_LABELS[@]}"; do
    local prefix
    prefix="${spec%%|*}"
    cat="${spec#*|}"; cat="${cat%%|*}"
    noun="${spec##*|}"
    n="$(count_category "$SKILLS_ROOT" "$cat")"
    # Escape '/' in prefix for use inside the regex/sed (e.g. "contracts/").
    local pesc
    pesc="$(printf '%s' "$prefix" | sed 's/[\/&]/\\&/g')"
    "$cb" "$README" "README mermaid ${prefix} — N ${noun}" \
      "${pesc} — [0-9]+ ${noun}" "$n" \
      "s/.*${pesc} — ([0-9]+) ${noun}.*/\1/" \
      "s/(${pesc} — )[0-9]+( ${noun})/\1${n}\2/g"
  done

  # --- plugin.json description "N skills" -----------------------------------
  "$cb" "$PLUGIN_JSON" "plugin.json description (N skills)" \
    'with [0-9]+ skills' "$total" \
    's/.*with ([0-9]+) skills.*/\1/' \
    "s/(with )[0-9]+( skills)/\1${total}\2/g"

  # --- marketplace.json count phrases ---------------------------------------
  # metadata.description: "the 41-skill library"
  "$cb" "$MARKETPLACE_JSON" "marketplace metadata (N-skill)" \
    'the [0-9]+-skill library' "$total" \
    's/.*the ([0-9]+)-skill library.*/\1/' \
    "s/(the )[0-9]+(-skill library)/\1${total}\2/g"

  # plugins[].description: "Install all 41 Skill-Madness skills"
  "$cb" "$MARKETPLACE_JSON" "marketplace plugin desc (all N)" \
    'Install all [0-9]+ Skill-Madness skills' "$total" \
    's/.*Install all ([0-9]+) Skill-Madness skills.*/\1/' \
    "s/(Install all )[0-9]+( Skill-Madness skills)/\1${total}\2/g"
}

# ---------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------
_check_cb() {
  # args: file label ere expected capture-sed sync-sed
  check_pattern "$1" "$2" "$3" "$4" "$5"
}

cmd_check() {
  MISMATCHES=()
  for_each_assertion _check_cb

  local total
  total="$(count_total "$SKILLS_ROOT")"

  if (( ${#MISMATCHES[@]} > 0 )); then
    ats_err "catalog drift: asserted counts disagree with disk (disk total = $total)"
    local m
    for m in "${MISMATCHES[@]}"; do
      ats_warn "$m"
    done
    ats_info "run 'scripts/catalog.sh --sync' to reconcile"
    return 1
  fi
  ats_ok "catalog clean: all asserted counts match disk (total = $total)"
  return 0
}

# ---------------------------------------------------------------------------
# --sync
# ---------------------------------------------------------------------------
_sync_cb() {
  # args: file label ere expected capture-sed sync-sed
  local file="$1" sync_sed="$6"
  sed_replace "$file" -E -e "$sync_sed"
}

cmd_sync() {
  for_each_assertion _sync_cb
  local total
  total="$(count_total "$SKILLS_ROOT")"
  ats_ok "synced asserted counts to disk (total = $total)"
  return 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
usage() {
  sed -n '3,28p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

main() {
  local mode="check"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check) mode="check"; shift ;;
      --sync)  mode="sync";  shift ;;
      --text)  mode="text";  shift ;;
      --help|-h) usage ;;
      -*) ats_err "Unknown option: $1"; exit 2 ;;
      *)  ats_err "Unexpected argument: $1"; exit 2 ;;
    esac
  done

  case "$mode" in
    text)  cmd_text ;;
    check) cmd_check ;;
    sync)  cmd_sync ;;
  esac
}

main "$@"
