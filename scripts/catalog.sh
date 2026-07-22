#!/usr/bin/env bash
#
# catalog.sh — Catalog-as-CI-invariant for Skill Madness.
#
# The filesystem is the single source of truth for the skill catalog. This
# script computes the true inventory from disk and either checks every derived
# assertion against it (--check), rewrites them to match (--sync), or prints the
# table (--text). It covers:
#   - the count phrases in README.md, plugin.json, marketplace.json,
#     CLAUDE.md, PLAN.md, and START-HERE.md (live phrasings only — historical
#     "47 skills" notes are left alone), including per-category phrases
#     ("N role agents", "N meta-skills", the marketplace category breakdown,
#     CLAUDE.md's "skills/<cat>/ (N)" lines);
#   - the README one-row-per-skill catalog table: row count + skill names must
#     equal disk (--check only; the table's descriptions are hand-maintained so
#     --sync deliberately does not rewrite it — fix reported rows by hand);
#   - the README architecture-diagram boxes: named nodes + the "+ N more"
#     overflow must equal disk per category, node ids unique per graph
#     (--sync repairs only the overflow number);
#   - the plugin.json `skills` array itself (every on-disk skill registered,
#     no stale entries) — delegated to scripts/sync-catalog-skills.py.
#
# Contract: contracts/installer/catalog-invariant.md v1.2.0
#
# Usage:
#   scripts/catalog.sh [--check | --sync | --text] [--help]
#
# Options:
#   --check   (default) compare every asserted count + the plugin listing to
#             disk; exit 1 on any mismatch.
#   --sync    rewrite all counts + reconcile the plugin.json skills array.
#   --text    print total + per-category table to stdout.
#   --help    print this and exit.
#
# A skill = a directory directly under a category (skills/<cat>/<skill>/SKILL.md)
# or the top-level orchestrator (skills/orchestrator/SKILL.md). Anything under
# skills/archive/, skills/in-progress/, or node_modules/ — or nested deeper than
# a skill root (a bundled node_modules SKILL.md) — is NOT a skill; the -maxdepth
# scan and the python reconciler both enforce that.
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
CLAUDE_MD="$REPO_ROOT/CLAUDE.md"
PLAN_MD="$REPO_ROOT/PLAN.md"
START_HERE="$REPO_ROOT/START-HERE.md"

# Companion that reconciles the plugin.json `skills` array with disk (registers
# new skills, drops stale entries). Delegated to from --check / --sync.
SKILLS_SYNC="$SCRIPT_DIR/sync-catalog-skills.py"

# The seven known categories, fixed order for stable output (matches plugin.json).
CATEGORIES="orchestrator roles contracts git meta workflows loops"

# ---------------------------------------------------------------------------
# Disk inventory
# ---------------------------------------------------------------------------

# _inventory <skills_root> — one find+awk pass over the tree, emitting
# "category|skill-name" per active skill ("orchestrator|orchestrator" for the
# top-level skill). Cached per process: every count/list below derives from
# this single pass instead of re-walking the tree with per-file subshells
# (the old per-file dirname/basename loop cost ~3 forks per skill per call,
# which multiplied badly once per-category assertions landed).
_INVENTORY_CACHE=""
_inventory() {
  local root="$1"
  if [[ -z "$_INVENTORY_CACHE" ]]; then
    _INVENTORY_CACHE="$(find "$root" -maxdepth 3 -name SKILL.md -type f 2>/dev/null \
      | grep -v "$root/archive/" \
      | grep -v "$root/in-progress/" \
      | awk -F/ '{
          if ($(NF-2) == "skills") print $(NF-1) "|" $(NF-1)
          else                     print $(NF-2) "|" $(NF-1)
        }')"
  fi
  [[ -n "$_INVENTORY_CACHE" ]] && printf '%s\n' "$_INVENTORY_CACHE"
  return 0
}

# count_total <skills_root>  — total active skills.
count_total() {
  _inventory "$1" | grep -c . || true
}

# count_category <skills_root> <category> — active skills in one category.
count_category() {
  _inventory "$1" | grep -c "^$2|" || true
}

# count_convertible <skills_root> — active skills that convert to non-Claude-
# Code hosts: requires_claude_code absent or false (the criterion convert.sh
# implements). Guards the README's hand-drifting "N of the M skills" phrases.
count_convertible() {
  local root="$1" n=0 f
  while IFS= read -r f; do
    grep -qE '^requires_claude_code:[[:space:]]*true' "$f" || n=$(( n + 1 ))
  done < <(find "$root" -maxdepth 3 -name SKILL.md -type f 2>/dev/null \
    | grep -v "$root/archive/" \
    | grep -v "$root/in-progress/")
  printf '%s\n' "$n"
}

# list_skills <skills_root> — print each active skill's name (the directory
# basename, or "orchestrator" for the top-level skill), one per line, sorted.
# Derives from the SAME inventory pass as count_total so the README-table
# check sees exactly the inventory the counts are derived from.
list_skills() {
  _inventory "$1" | cut -d'|' -f2 | LC_ALL=C sort
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
# A missing target is a no-op: not every repo (or test fixture) carries every
# asserted-count file, and a count that isn't present simply can't drift.
sed_replace() {
  local file="$1"; shift
  [[ -f "$file" ]] || return 0
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
# README skill-catalog TABLE check.
#
# The README carries a one-row-per-skill catalog table:
#     | # | Skill | Category | What it does |
#     |---|-------|----------|--------------|
#     | 1 | `orchestrator` | coordinator | ... |
#     ...
# This is hand-maintained and has drifted silently before (a new skill ships
# but no row is added), which the count-phrase checks above cannot catch — the
# total badge can be bumped without the table gaining a row.
#
# check_readme_table asserts the set of backticked skill names in that table
# equals the on-disk skill set: same cardinality, and (where parseable) the
# exact names. It is keyed on the table HEADER, so any README without that
# header (e.g. the bats fixture) is a clean no-op — never a false failure.
#
# Records drift in MISMATCHES (so the existing --check exit-1 path fires) AND
# prints an explicit [!!] line per missing/extra skill for an actionable diff.
check_readme_table() {
  local file="$1"
  [[ -f "$file" ]] || return 0

  # Locate the catalog-table header. No header -> no table to check (no-op).
  # `|| true` keeps a no-match grep from tripping `set -o pipefail`.
  local hdr
  hdr="$( { grep -nE '^\| *# *\| *Skill *\| *Category' "$file" 2>/dev/null || true; } \
           | head -n1 | cut -d: -f1)"
  [[ -z "$hdr" ]] && return 0

  # Collect backticked skill names from contiguous numbered rows after the
  # header (skip the `|---|` separator). Stop at the first non-row line.
  local tmp_t tmp_d
  tmp_t="$(mktemp "${TMPDIR:-/tmp}/ats-table.XXXXXX")"
  awk -v start="$hdr" '
    NR <= start { next }
    /^\|[[:space:]]*-+/ { next }                 # separator row
    /^\|[[:space:]]*[0-9]+[[:space:]]*\|/ {       # | N | `name` | ... |
      if (match($0, /`[^`]+`/)) {
        s = substr($0, RSTART + 1, RLENGTH - 2)
        print s
      }
      next
    }
    { exit }                                      # first non-row line ends table
  ' "$file" | LC_ALL=C sort > "$tmp_t"

  tmp_d="$(mktemp "${TMPDIR:-/tmp}/ats-disk.XXXXXX")"
  list_skills "$SKILLS_ROOT" > "$tmp_d"

  local disk_n table_n
  disk_n="$(wc -l < "$tmp_d" | tr -d ' ')"
  table_n="$(wc -l < "$tmp_t" | tr -d ' ')"

  # Cardinality assertion (always meaningful even if name parsing is imperfect).
  if [[ "$table_n" != "$disk_n" ]]; then
    MISMATCHES+=("README catalog table rows: found $table_n, disk says $disk_n  ($(basename "$file"))")
  fi

  # Name-level diff: skills on disk but missing a table row, and vice versa.
  local missing extra line
  missing="$(LC_ALL=C comm -23 "$tmp_d" "$tmp_t")"
  extra="$(LC_ALL=C comm -13 "$tmp_d" "$tmp_t")"

  if [[ -n "$missing" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      MISMATCHES+=("README catalog table: missing row for on-disk skill '$line'")
    done <<EOF
$missing
EOF
  fi
  if [[ -n "$extra" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      MISMATCHES+=("README catalog table: stale row '$line' (no such skill on disk)")
    done <<EOF
$extra
EOF
  fi

  rm -f "$tmp_t" "$tmp_d"
}

# ---------------------------------------------------------------------------
# README architecture-diagram BOX check.
#
# The category subgraph labels ("⚙️ workflows/ — 32 skills") are kept fresh by
# the MERMAID_LABELS assertions below, but the box CONTENTS are hand-drawn:
# named nodes plus an optional overflow node (`more["+ N more"]`). Both have
# drifted silently — 13 named + "+ 18 more" = 31 under a "32 skills" label,
# and a node id reused across two boxes made one box render a node short
# (mermaid node ids are global per graph). Per category box this asserts:
# named nodes + overflow == disk count, and no node id is defined twice inside
# one mermaid block. Boxes with no nodes at all are skipped (fixture READMEs
# carry bare subgraph headers), so a README without drawn boxes is a no-op.
#
# --sync repairs only the overflow number; named nodes are hand-maintained,
# like the catalog table — add/remove those by hand.

# _mermaid_boxes <file> — emit "BOX|<subgraph-id>|<category>|<named>|<overflow-or-->"
# per category box and "DUP|<node-id>" per duplicated node id.
_mermaid_boxes() {
  awk '
    function flushbox() {
      if (box != "") print "BOX|" box "|" cat "|" named "|" over
      box = ""
    }
    /^```mermaid[[:space:]]*$/ { inm = 1; box = ""; delete seen; next }
    inm && /^```/ {
      flushbox()
      for (id in seen) if (seen[id] > 1) print "DUP|" id
      inm = 0
      next
    }
    !inm { next }
    /^[[:space:]]*subgraph[[:space:]]/ {
      flushbox()
      cat = ""
      line = $0
      sub(/^[[:space:]]*subgraph[[:space:]]+/, "", line)
      id = line; sub(/\[.*$/, "", id)
      # Category boxes carry a "<dir>/ — N skills|agents" label.
      if (match(line, /[A-Za-z0-9_-]+\/ — [0-9]+ (skills|agents)/)) {
        cat = substr(line, RSTART, RLENGTH)
        sub(/\/.*$/, "", cat)
        box = id; named = 0; over = "-"
      }
      next
    }
    /^[[:space:]]*end[[:space:]]*$/ { flushbox(); next }
    match($0, /^[[:space:]]*[A-Za-z][A-Za-z0-9_]*\[/) {
      id = $0
      sub(/^[[:space:]]*/, "", id); sub(/\[.*$/, "", id)
      seen[id]++
      if (box != "") {
        if ($0 ~ /\[" *\+ *[0-9]+ more *"\]/) {
          over = $0
          sub(/^.*\[" *\+ */, "", over); sub(/ more.*$/, "", over)
        } else {
          named++
        }
      }
      next
    }
  ' "$1"
}

check_readme_mermaid_boxes() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  local kind id cat named over disk
  while IFS='|' read -r kind id cat named over; do
    case "$kind" in
      DUP)
        MISMATCHES+=("README mermaid: node id '$id' defined more than once (one box renders short — rename one id)")
        ;;
      BOX)
        [[ "$named" == "0" && "$over" == "-" ]] && continue
        disk="$(count_category "$SKILLS_ROOT" "$cat")"
        if [[ "$over" == "-" ]]; then
          if (( named != disk )); then
            MISMATCHES+=("README mermaid ${cat}/ box: $named named nodes, disk says $disk (add/remove nodes by hand)")
          fi
        else
          if (( named + over != disk )); then
            MISMATCHES+=("README mermaid ${cat}/ box: $named named + $over more = $(( named + over )), disk says $disk")
          fi
        fi
        ;;
    esac
  done < <(_mermaid_boxes "$file")
}

# sync_readme_mermaid_overflow <file> — rewrite each box's "+ N more" node so
# named + N == disk. Boxes without an overflow node are left for --check.
sync_readme_mermaid_overflow() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  local kind id cat named over disk expect tmp
  while IFS='|' read -r kind id cat named over; do
    [[ "$kind" == "BOX" ]] || continue
    [[ "$over" == "-" ]] && continue
    disk="$(count_category "$SKILLS_ROOT" "$cat")"
    expect=$(( disk - named ))
    (( expect < 1 )) && continue
    if (( named + over != disk )); then
      tmp="$(mktemp "${TMPDIR:-/tmp}/ats-mermaid.XXXXXX")"
      awk -v sg="$id" -v n="$expect" '
        /^[[:space:]]*subgraph[[:space:]]/ {
          line = $0
          sub(/^[[:space:]]*subgraph[[:space:]]+/, "", line)
          cur = line; sub(/\[.*$/, "", cur)
          inbox = (cur == sg)
        }
        /^[[:space:]]*end[[:space:]]*$/ { inbox = 0 }
        inbox && /\[" *\+ *[0-9]+ more *"\]/ {
          sub(/\[" *\+ *[0-9]+ more *"\]/, "[\"+ " n " more\"]")
        }
        { print }
      ' "$file" > "$tmp"
      cat "$tmp" > "$file"
      rm -f "$tmp"
    fi
  done < <(_mermaid_boxes "$file")
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
  "loops/|loops|skills"
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

  # "N skills, seven categories" — feature bullet (~45) and roadmap line (~544).
  "$cb" "$README" "README prose (N skills, seven categories)" \
    '[0-9]+ skills, seven categories' "$total" \
    's/.*[^0-9]([0-9]+) skills, seven categories.*/\1/' \
    "s/[0-9]+( skills, seven categories)/${total}\1/g"

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

  # "N portable skills" — the hero tagline (~9). Drifted 67-vs-68 unguarded.
  "$cb" "$README" "README hero (N portable skills)" \
    '[0-9]+ portable skills' "$total" \
    's/.*[^0-9]([0-9]+) portable skills.*/\1/' \
    "s/[0-9]+( portable skills)/${total}\1/g"

  # "out of all N" — the madness-router blurb (~63) and front-door bullet (~80).
  "$cb" "$README" "README prose (out of all N)" \
    'out of all [0-9]+' "$total" \
    's/.*out of all ([0-9]+).*/\1/' \
    "s/(out of all )[0-9]+/\1${total}/g"

  # "skill library (N)" — the project-structure tree comment (~453).
  "$cb" "$README" "README tree (skill library (N))" \
    'skill library \([0-9]+\)' "$total" \
    's/.*skill library \(([0-9]+)\).*/\1/' \
    "s/(skill library \()[0-9]+(\))/\1${total}\2/g"

  # --- Convertible-subset assertions (PF3) ----------------------------------
  # "N of the M skills" — the other-hosts section (~501) and troubleshooting
  # (~675). N = skills without requires_claude_code:true (what convert.sh
  # ships); M = the disk total. Two assertions per phrase so a flag flip or a
  # new skill can't silently strand either number.
  local convertible
  convertible="$(count_convertible "$SKILLS_ROOT")"
  "$cb" "$README" "README prose (N of the M skills — convertible)" \
    '[0-9]+ of the [0-9]+ skills' "$convertible" \
    's/.*[^0-9]([0-9]+) of the [0-9]+ skills.*/\1/' \
    "s/[0-9]+( of the [0-9]+ skills)/${convertible}\1/g"
  "$cb" "$README" "README prose (N of the M skills — total)" \
    '[0-9]+ of the [0-9]+ skills' "$total" \
    's/.*[0-9]+ of the ([0-9]+) skills.*/\1/' \
    "s/( of the )[0-9]+( skills)/\1${total}\2/g"

  # --- Per-category prose/badge phrases (README + plugin/marketplace) --------
  # These carry per-category numbers that the total-only sync used to strand
  # (the marketplace breakdown shipped 41-era counts at a 68-skill HEAD).
  local n_roles n_contracts n_git n_meta n_workflows n_loops f
  n_roles="$(count_category "$SKILLS_ROOT" roles)"
  n_contracts="$(count_category "$SKILLS_ROOT" contracts)"
  n_git="$(count_category "$SKILLS_ROOT" git)"
  n_meta="$(count_category "$SKILLS_ROOT" meta)"
  n_workflows="$(count_category "$SKILLS_ROOT" workflows)"
  n_loops="$(count_category "$SKILLS_ROOT" loops)"

  for f in "$README" "$PLUGIN_JSON" "$MARKETPLACE_JSON"; do
    "$cb" "$f" "per-category (N role agents)" \
      '[0-9]+ role agents' "$n_roles" \
      's/.*[^0-9]([0-9]+) role agents.*/\1/' \
      "s/[0-9]+( role agents)/${n_roles}\1/g"
    "$cb" "$f" "per-category (N contract skills)" \
      '[0-9]+ contract skills' "$n_contracts" \
      's/.*[^0-9]([0-9]+) contract skills.*/\1/' \
      "s/[0-9]+( contract skills)/${n_contracts}\1/g"
    "$cb" "$f" "per-category (N git workflow skills)" \
      '[0-9]+ git[- ]workflow skills' "$n_git" \
      's/.*[^0-9]([0-9]+) git[- ]workflow skills.*/\1/' \
      "s/[0-9]+( git[- ]workflow skills)/${n_git}\1/g"
    "$cb" "$f" "per-category (N meta skills)" \
      '[0-9]+ meta[-/]s' "$n_meta" \
      's@.*[^0-9]([0-9]+) meta[-/]s.*@\1@' \
      "s@[0-9]+( meta[-/]s)@${n_meta}\1@g"
    "$cb" "$f" "per-category (N cross-cutting workflow)" \
      '[0-9]+ cross-cutting workflow' "$n_workflows" \
      's/.*[^0-9]([0-9]+) cross-cutting workflow.*/\1/' \
      "s/[0-9]+( cross-cutting workflow)/${n_workflows}\1/g"
    "$cb" "$f" "per-category (N autonomous-loop skills)" \
      '[0-9]+ autonomous-loop skills' "$n_loops" \
      's/.*[^0-9]([0-9]+) autonomous-loop skills.*/\1/' \
      "s/[0-9]+( autonomous-loop skills)/${n_loops}\1/g"
  done

  # README-only per-category phrasings: badges + loop prose.
  "$cb" "$README" "README badge (role%20agents-N)" \
    'role%20agents-[0-9]+-' "$n_roles" \
    's/.*role%20agents-([0-9]+)-.*/\1/' \
    "s/(role%20agents-)[0-9]+(-)/\1${n_roles}\2/g"
  "$cb" "$README" "README badge (autonomous%20loops-N)" \
    'autonomous%20loops-[0-9]+-' "$n_loops" \
    's/.*autonomous%20loops-([0-9]+)-.*/\1/' \
    "s/(autonomous%20loops-)[0-9]+(-)/\1${n_loops}\2/g"
  "$cb" "$README" "README prose (N autonomous loops)" \
    '[0-9]+ autonomous loops' "$n_loops" \
    's/.*[^0-9]([0-9]+) autonomous loops.*/\1/' \
    "s/[0-9]+( autonomous loops)/${n_loops}\1/g"
  "$cb" "$README" "README prose (N loop skills)" \
    '[0-9]+ loop skills' "$n_loops" \
    's/.*[^0-9]([0-9]+) loop skills.*/\1/' \
    "s/[0-9]+( loop skills)/${n_loops}\1/g"

  # PLAN.md "a **13-skill autonomous-loop library**".
  "$cb" "$PLAN_MD" "PLAN.md (N-skill autonomous-loop library)" \
    '[0-9]+-skill autonomous-loop library' "$n_loops" \
    's/.*[^0-9]([0-9]+)-skill autonomous-loop library.*/\1/' \
    "s/[0-9]+(-skill autonomous-loop library)/${n_loops}\1/g"

  # --- CLAUDE.md per-category "(N)" breakdown --------------------------------
  # "- **`skills/<cat>/`** (N) — ..." — the always-loaded instruction file's
  # category counts drifted silently after #33 (workflows said 31 at a 32 disk).
  for cat in $CATEGORIES; do
    n="$(count_category "$SKILLS_ROOT" "$cat")"
    "$cb" "$CLAUDE_MD" "CLAUDE.md category skills/${cat}/ (N)" \
      "\\*\\*\`skills/${cat}/\`\\*\\* \\([0-9]+\\)" "$n" \
      "s@.*\`skills/${cat}/\`\\*\\* \\(([0-9]+)\\).*@\\1@" \
      "s@(\`skills/${cat}/\`\\*\\* \\()[0-9]+(\\))@\\1${n}\\2@"
  done

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

  # --- CLAUDE.md / PLAN.md / START-HERE.md live total counts -----------------
  # Only the LIVE current-count phrasings are targeted. Historical mentions
  # ("47 skills across 6 categories", "validating all 47 skills clean",
  # "across 49 skills") use different wording and are deliberately left alone.

  # CLAUDE.md "What This Is": "— N OSS-publishable skills in `skills/`".
  "$cb" "$CLAUDE_MD" "CLAUDE.md (N OSS-publishable skills)" \
    '[0-9]+ OSS-publishable skills' "$total" \
    's/.*[^0-9]([0-9]+) OSS-publishable skills.*/\1/' \
    "s/[0-9]+( OSS-publishable skills)/${total}\1/g"

  # PLAN.md "Where we are": "a mature **N-skill** library".
  "$cb" "$PLAN_MD" "PLAN.md (N-skill library)" \
    '\*\*[0-9]+-skill\*\* library' "$total" \
    's/.*\*\*([0-9]+)-skill\*\* library.*/\1/' \
    "s/(\*\*)[0-9]+(-skill\*\* library)/\1${total}\2/g"

  # START-HERE.md "Status at a glance": "A mature library of **N skills**".
  "$cb" "$START_HERE" "START-HERE.md (library of N skills)" \
    'library of \*\*[0-9]+ skills\*\*' "$total" \
    's/.*library of \*\*([0-9]+) skills\*\*.*/\1/' \
    "s/(library of \*\*)[0-9]+( skills\*\*)/\1${total}\2/g"
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
  # Additionally assert the README's one-row-per-skill catalog table matches
  # disk (row count + skill names). No-op on READMEs without the table header.
  check_readme_table "$README"
  # And the architecture-diagram boxes: named nodes + "+ N more" == disk per
  # category, no duplicate node ids. No-op on READMEs without drawn boxes.
  check_readme_mermaid_boxes "$README"

  local total rc=0
  total="$(count_total "$SKILLS_ROOT")"

  if (( ${#MISMATCHES[@]} > 0 )); then
    ats_err "catalog drift: asserted counts disagree with disk (disk total = $total)"
    local m
    for m in "${MISMATCHES[@]}"; do
      ats_warn "$m"
    done
    rc=1
  fi

  # plugin.json `skills` array registration — delegated to the reconciler, which
  # prints its own drift lines. Missing python3 degrades to count-only checking.
  if [[ -f "$SKILLS_SYNC" ]] && command -v python3 >/dev/null 2>&1; then
    python3 "$SKILLS_SYNC" --check || rc=1
  fi

  if (( rc != 0 )); then
    ats_info "run 'scripts/catalog.sh --sync' to reconcile"
    return 1
  fi
  ats_ok "catalog clean: counts + plugin.json listing all match disk (total = $total)"
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
  # Repair the architecture-diagram overflow nodes ("+ N more") from disk.
  sync_readme_mermaid_overflow "$README"
  # Reconcile the plugin.json `skills` array (register new, drop stale).
  if [[ -f "$SKILLS_SYNC" ]] && command -v python3 >/dev/null 2>&1; then
    python3 "$SKILLS_SYNC" --sync
  fi
  local total
  total="$(count_total "$SKILLS_ROOT")"
  ats_ok "synced counts + plugin.json listing to disk (total = $total)"
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
