#!/usr/bin/env bash
#
# lint-skills.sh — Validate all skills/**/SKILL.md files.
#
# Checks frontmatter schema, body quality, and cross-skill invariants.
# This is the CI gate — errors block PR merges.
#
# Usage:
#   scripts/lint-skills.sh [OPTIONS] [PATH ...]
#
# Options:
#   --quiet          Suppress WARN output
#   --verbose        Show INFO output
#   --fix-trivial    Auto-fix trivial issues (prompts before each fix)
#   --format FORMAT  Output format: text (default) or junit
#   --standard       Print the PSFS standard + version this linter implements
#                    and the canonical schema path, then exit 0
#   --changed [REF]  Version-drift guard (git-based): ERROR when a skill's
#                    SKILL.md body changed vs REF (default origin/main, then
#                    main) but its frontmatter version: did not. Ignores PATH
#                    args. Not part of the static lint; wired into CI as a PR
#                    gate in .github/workflows/lint-skills.yml (DV-2).
#   --help           Print this and exit
#
# PATH may be a directory (recurse) or an individual SKILL.md.
# If no PATH given, lints all skills/**/SKILL.md.
#
# Exit codes: 0 no errors, 1 at least one error, 2 argument failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"
# shellcheck source=scripts/lib/frontmatter.sh
. "$LIB_DIR/frontmatter.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"

# Named standard this linter implements (see spec/PSFS.md).
PSFS_NAME="Portable Skill Frontmatter Spec (PSFS)"
PSFS_VERSION="1.1.0"
SCHEMA_PATH="$REPO_ROOT/spec/frontmatter.schema.json"

# print_standard — bind this bash impl to the named, versioned standard.
print_standard() {
  printf '%s v%s\n' "$PSFS_NAME" "$PSFS_VERSION"
  printf 'Canonical schema: %s\n' "$SCHEMA_PATH"
  printf 'Reference implementation: scripts/lint-skills.sh (bash)\n'
}

# ---------------------------------------------------------------------------
# CLI state
# ---------------------------------------------------------------------------
QUIET=false
VERBOSE=false
# shellcheck disable=SC2034  # FIX_TRIVIAL: reserved for future auto-fix implementation
FIX_TRIVIAL=false
FORMAT="text"
LINT_PATHS=()
# --changed mode (SR13 version-drift guard): opt-in, git-based. CHANGED_BASE=""
# means "auto-detect base ref" (origin/main, then main).
CHANGED_MODE=false
CHANGED_BASE=""

# ---------------------------------------------------------------------------
# Issue tracking
# ---------------------------------------------------------------------------
ERRORS=()    # "FILE:LINE:MESSAGE"
WARNS=()
INFOS=()

# Emit the "jsonschema absent" advisory at most once across the whole run.
JSONSCHEMA_ADVISED=false

record_error() { ERRORS+=("$1"); }
record_warn()  { WARNS+=("$1"); }
record_info()  { INFOS+=("$1"); }

# emit_issue <severity> <file> [line] <message>
emit_issue() {
  local sev="$1" file="$2" line_or_msg="$3"
  local msg="${4:-}"
  local line=""

  if [[ -n "$msg" ]]; then
    line="$line_or_msg"
  else
    msg="$line_or_msg"
  fi

  local loc="$file"
  [[ -n "$line" ]] && loc="${file}:${line}"

  case "$sev" in
    ERROR) record_error "${loc}:${msg}" ;;
    WARN)  record_warn  "${loc}:${msg}" ;;
    INFO)  record_info  "${loc}:${msg}" ;;
  esac
}

# ---------------------------------------------------------------------------
# YAML-aware python3 parser for lint checks
# ---------------------------------------------------------------------------
_lint_py3() {
  local file="$1"
  local schema="${2:-}"
  python3 - "$file" "$schema" <<'PYEOF'
import sys, json, re

path = sys.argv[1]
schema_path = sys.argv[2] if len(sys.argv) > 2 else ''

with open(path) as f:
    content = f.read()

lines = content.split('\n')
result = {
    "ok": False,
    "error": None,
    "fm_end_line": None,
    "data": {},
    "body_lines": [],
    "body_word_count": 0,
    "schema_errors": [],
    "jsonschema_missing": False,
}

# Check opening ---
if not lines or lines[0].rstrip() != '---':
    result["error"] = "missing opening ---"
    print(json.dumps(result))
    sys.exit(0)

fm_end = None
for i in range(1, min(101, len(lines))):
    if lines[i].rstrip() == '---':
        fm_end = i
        break

if fm_end is None:
    result["error"] = "no closing --- within 100 lines"
    print(json.dumps(result))
    sys.exit(0)

result["fm_end_line"] = fm_end + 1  # 1-based

fm_text = '\n'.join(lines[1:fm_end])

try:
    import yaml
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        result["error"] = f"YAML parse error: {e}"
        print(json.dumps(result))
        sys.exit(0)
except ImportError:
    result["error"] = "install python3 pyyaml for full YAML validation"
    print(json.dumps(result))
    sys.exit(0)

result["ok"] = True
result["data"] = data

# Angle-bracket safety: '<' and '>' are forbidden in ANY frontmatter string
# value or key, at any depth — including inside the free-form `metadata` object.
# Frontmatter is injected verbatim into the model's system prompt, where '<...>'
# can be read as control/tool tags or abused for prompt injection. Checked
# against parsed VALUES (not raw text), so YAML block-scalar indicators such as
# 'description: >' or 'description: |' are never false positives.
def _angle_hits(obj, path=""):
    hits = []
    if isinstance(obj, str):
        if "<" in obj or ">" in obj:
            hits.append(path or "(root)")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            ks = str(k)
            kp = f"{path}.{ks}" if path else ks
            if "<" in ks or ">" in ks:
                hits.append(f"{kp} (key)")
            hits += _angle_hits(v, kp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _angle_hits(v, f"{path}[{i}]")
    return hits

result["angle_hits"] = _angle_hits(data)

# Body analysis
body_lines = lines[fm_end + 1:]
result["body_lines"] = body_lines
result["body_word_count"] = len(' '.join(body_lines).split())
result["body_line_count"] = len([l for l in body_lines if l.strip()])

# Description char count (collapsed)
desc = data.get('description', '')
if isinstance(desc, str):
    result["desc_len"] = len(' '.join(desc.split()))
else:
    result["desc_len"] = 0

# Check if description starts with action verb (first 5 words)
action_verbs = {
    'use', 'apply', 'generate', 'validate', 'coordinate', 'author', 'review',
    'audit', 'create', 'build', 'analyze', 'check', 'extract', 'prepare',
    'design', 'manage', 'track', 'convert', 'install', 'lint', 'fix',
    'refactor', 'test', 'run', 'write', 'read', 'update', 'set', 'add',
    'remove', 'deploy', 'debug', 'implement', 'scaffold', 'plan', 'parse',
    'emit', 'walk', 'scan', 'detect', 'verify', 'enforce', 'produce',
    'output', 'sync', 'migrate', 'query', 'clean', 'prune', 'stage',
    'commit', 'push', 'pull', 'merge', 'rebase', 'branch', 'tag',
    'profile', 'monitor', 'alert', 'log', 'trace', 'instrument', 'bootstrap',
    'configure', 'format', 'render', 'compile', 'bundle', 'optimize',
    'benchmark', 'measure', 'report', 'summarize', 'document', 'draft',
    'lead', 'coordinate', 'orchestrate', 'spawn', 'dispatch', 'gate',
    'consolidate', 'research', 'improve', 'deep', 'guide', 'chart',
}
first_words = ' '.join(desc.split()).split()[:5]
first_words_lower = [w.lower().strip('.,;:!?') for w in first_words]
result["has_action_verb"] = any(w in action_verbs for w in first_words_lower)

# Check trigger context hint (when/for/whenever/if)
result["has_trigger_context"] = bool(re.search(r'\b(when|for|whenever|if)\b', desc, re.IGNORECASE))

# Optional schema cross-check (PSFS frontmatter.schema.json).
# Only attempts when a schema path was passed AND jsonschema is importable.
# Missing jsonschema is an environment advisory (WARN), mirroring pyyaml.
if schema_path:
    try:
        import jsonschema
        try:
            with open(schema_path) as sf:
                schema = json.load(sf)
            validator = jsonschema.Draft202012Validator(schema)
            for err in sorted(validator.iter_errors(data), key=str):
                loc = '/'.join(str(p) for p in err.absolute_path) or '(root)'
                result["schema_errors"].append(f"{loc}: {err.message}")
        except Exception as e:  # noqa: BLE001 — never block lint on schema-read issues
            result["schema_errors"].append(f"schema validation error: {e}")
    except ImportError:
        result["jsonschema_missing"] = True

print(json.dumps(result))
PYEOF
}

# ---------------------------------------------------------------------------
# Collect SKILL.md files to lint
# ---------------------------------------------------------------------------

# _drop_gitignored — filter stdin, dropping paths git ignores. Gitignored
# SKILL.md files (skill-creator / skill-review eval workspaces, `*-workspace/`
# debris) are not part of the tree, but the discovery find used to pick them
# up and fail the lint (+ the bats regression test) after every local
# skill-creator run. Outside a git repo this is a pass-through. Explicitly
# passed files are NOT filtered — asking for a file means lint that file.
_drop_gitignored() {
  local all ignored
  all="$(cat)"
  [[ -z "$all" ]] && return 0
  if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ignored="$(printf '%s\n' "$all" | git -C "$REPO_ROOT" check-ignore --stdin 2>/dev/null || true)"
    if [[ -n "$ignored" ]]; then
      printf '%s\n' "$all" | grep -vxF -f <(printf '%s\n' "$ignored") || true
      return 0
    fi
  fi
  printf '%s\n' "$all"
}

collect_files() {
  if [[ ${#LINT_PATHS[@]} -eq 0 ]]; then
    find "$SKILLS_ROOT" -name "SKILL.md" -type f | sort | _drop_gitignored
    return
  fi
  local p
  for p in "${LINT_PATHS[@]}"; do
    if [[ -f "$p" ]]; then
      printf '%s\n' "$p"
    elif [[ -d "$p" ]]; then
      find "$p" -name "SKILL.md" -type f | sort | _drop_gitignored
    else
      printf '%s: not a file or directory\n' "$p" >&2
    fi
  done | sort -u
}

# ---------------------------------------------------------------------------
# lint_one <file>
# ---------------------------------------------------------------------------
lint_one() {
  local file="$1"

  # Basic file check
  if [[ ! -f "$file" ]]; then
    emit_issue ERROR "$file" "" "file not found"
    return
  fi

  # Run python3 analysis (passing the schema path enables the optional
  # PSFS schema cross-check when the jsonschema package is available)
  local schema_arg=""
  [[ -f "$SCHEMA_PATH" ]] && schema_arg="$SCHEMA_PATH"
  local json_out
  json_out="$(_lint_py3 "$file" "$schema_arg")"
  if [[ -z "$json_out" ]]; then
    emit_issue ERROR "$file" "" "python3 lint helper returned no output"
    return
  fi

  # Extract fields via python3 json parsing (avoids jq dependency)
  local ok fm_error fm_end_line desc_len body_wc body_lc has_verb has_trigger
  ok="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ok'])")"
  fm_error="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['error'] or '')" 2>/dev/null || echo '')"

  if [[ "$ok" != "True" ]]; then
    # Missing pyyaml is an environment advisory, not a content defect — WARN, not ERROR.
    if [[ "$fm_error" == *"install python3 pyyaml"* ]]; then
      emit_issue WARN "$file" "1" "$fm_error"
    else
      emit_issue ERROR "$file" "1" "$fm_error"
    fi
    return
  fi

  fm_end_line="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['fm_end_line'])")"
  desc_len="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('desc_len',0))")"
  body_wc="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['body_word_count'])")"
  body_lc="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('body_line_count',0))")"
  has_verb="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('has_action_verb',False))")"
  has_trigger="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('has_trigger_context',False))")"

  # ---------------------------------------------------------------------------
  # Optional PSFS schema cross-check (mirrors the pyyaml-absent advisory above)
  # ---------------------------------------------------------------------------
  local jsonschema_missing
  jsonschema_missing="$(printf '%s' "$json_out" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('jsonschema_missing',False))")"
  if [[ "$jsonschema_missing" == "True" ]]; then
    if ! $JSONSCHEMA_ADVISED; then
      emit_issue WARN "$file" "1" "install python3 jsonschema for schema validation"
      JSONSCHEMA_ADVISED=true
    fi
  else
    # Emit each schema violation as an ERROR (structural defect).
    while IFS= read -r schema_err; do
      [[ -z "$schema_err" ]] && continue
      emit_issue ERROR "$file" "1" "schema: $schema_err"
    done < <(printf '%s' "$json_out" | python3 -c "import sys,json; [print(e) for e in json.load(sys.stdin).get('schema_errors',[])]")
  fi

  # Angle-bracket safety (always-on, independent of jsonschema). This is the
  # enforcement home for the no-'<'/'>' rule: the JSON Schema can only pattern
  # the named typed fields, not arbitrary string leaves under the free-form
  # `metadata` object, and the schema check is skipped when jsonschema is absent.
  while IFS= read -r angle_path; do
    [[ -z "$angle_path" ]] && continue
    emit_issue ERROR "$file" "$fm_end_line" \
      "frontmatter contains '<' or '>' in '$angle_path' (forbidden — frontmatter is injected into the system prompt)"
  done < <(printf '%s' "$json_out" | python3 -c "import sys,json; [print(e) for e in json.load(sys.stdin).get('angle_hits',[])]")

  # Derive slug and category from path
  local skill_dir slug category
  skill_dir="$(dirname "$file")"
  slug="$(basename "$skill_dir")"
  local parent_dir
  parent_dir="$(basename "$(dirname "$skill_dir")")"
  if [[ "$parent_dir" == "skills" ]]; then
    category="$slug"
  else
    category="$parent_dir"
  fi

  # ---------------------------------------------------------------------------
  # Required field: name
  # ---------------------------------------------------------------------------
  local name
  name="$(get_field "name" "$file")"
  if [[ -z "$name" ]]; then
    emit_issue ERROR "$file" "1" "required field 'name' is missing or empty"
  else
    # kebab-case check
    if ! printf '%s' "$name" | grep -qE '^[a-z][a-z0-9-]*$'; then
      emit_issue ERROR "$file" "1" "name '$name' is not kebab-case (must match ^[a-z][a-z0-9-]*$)"
    fi
    # length check
    if (( ${#name} > 64 )); then
      emit_issue ERROR "$file" "1" "name '$name' exceeds 64 characters"
    fi
    # name must match directory
    if [[ "$name" != "$slug" ]]; then
      emit_issue ERROR "$file" "1" "name '$name' does not match directory '$slug'"
    fi
  fi

  # ---------------------------------------------------------------------------
  # Required field: version
  # ---------------------------------------------------------------------------
  local version
  version="$(get_field "version" "$file")"
  if [[ -z "$version" ]]; then
    emit_issue ERROR "$file" "1" "required field 'version' is missing or empty"
  elif ! printf '%s' "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    emit_issue ERROR "$file" "1" "version '$version' is not valid semver (expected X.Y.Z)"
  fi

  # ---------------------------------------------------------------------------
  # Required field: description
  # ---------------------------------------------------------------------------
  if (( desc_len == 0 )); then
    emit_issue ERROR "$file" "1" "required field 'description' is missing or empty"
  elif (( desc_len > 950 )); then
    # Ceiling-approach band (SR12): the schema hard-fails description >1024 chars.
    # WARN once a description crosses 950 so it gets trimmed BEFORE one more edit
    # pushes it over and turns a clean tree red. WARN-only — never touches exit.
    emit_issue WARN "$file" "" "description is ${desc_len} chars — within $(( 1024 - desc_len )) of the 1024 hard ceiling; trim trigger text (move detail to body/references) before an edit pushes it over and FAILs the schema check"
  elif (( desc_len > 500 )); then
    emit_issue WARN "$file" "" "description is ${desc_len} chars (consider whether some trigger context belongs in body/references)"
  elif (( desc_len > 200 )); then
    emit_issue WARN "$file" "" "description is ${desc_len} chars (soft target ≤200; pushy descriptions are OK per CLAUDE.md)"
  fi

  # ---------------------------------------------------------------------------
  # Body: must exist
  # ---------------------------------------------------------------------------
  if (( body_wc == 0 )); then
    emit_issue ERROR "$file" "$(( fm_end_line + 1 ))" "body is empty (≥1 non-frontmatter line required)"
  elif (( body_wc < 50 )); then
    emit_issue WARN "$file" "" "body is ${body_wc} words (likely a stub; target ≥50)"
  fi

  # Body line count
  if (( body_lc > 500 )); then
    emit_issue WARN "$file" "" "body is ${body_lc} non-blank lines (target ≤500; move detail to references/)"
  fi

  # ---------------------------------------------------------------------------
  # $ARGUMENTS token guard (WC-1). convert.sh ships the body of every skill
  # verbatim to 10 non-Claude-Code hosts (Cursor/Windsurf/Gemini/etc.) — none
  # of those converters translate Claude Code's slash-command `$ARGUMENTS`
  # placeholder, so a skill using it would silently ship a magic token those
  # hosts don't understand. Fail loudly rather than translate silently: with
  # zero skills using the token, there is no real host-specific behavior to
  # translate against yet, and a loud ERROR here is what forces that design
  # conversation the first time a skill actually needs it.
  # ---------------------------------------------------------------------------
  if tail -n "+$(( fm_end_line + 1 ))" "$file" | grep -qF '$ARGUMENTS'; then
    emit_issue ERROR "$file" "" "body contains '\$ARGUMENTS' — this Claude-Code-only slash-command token is shipped verbatim (untranslated) to every other host by convert.sh; rewrite in host-neutral prose or gate the reference behind a Claude-Code-only note"
  fi

  # ---------------------------------------------------------------------------
  # Description quality heuristics (WARN)
  # ---------------------------------------------------------------------------
  if [[ "$has_verb" != "True" ]]; then
    emit_issue WARN "$file" "" "description may not start with an action verb (check first 5 words)"
  fi
  if [[ "$has_trigger" != "True" ]]; then
    emit_issue WARN "$file" "" "description lacks a trigger context (consider adding 'when', 'for', 'if', or 'whenever')"
  fi

  # ---------------------------------------------------------------------------
  # Recommended fields for role skills
  # ---------------------------------------------------------------------------
  if [[ "$category" == "roles" ]]; then
    local owns_dirs
    owns_dirs="$(get_owns_dirs "$file")"
    if [[ -z "$owns_dirs" ]]; then
      emit_issue WARN "$file" "" "role skill missing recommended 'owns.directories' (agent roles need exclusive ownership)"
    fi

    local allowed_tools
    allowed_tools="$(get_field "allowed-tools" "$file")"
    if [[ -z "$allowed_tools" ]]; then
      emit_issue WARN "$file" "" "role skill missing recommended 'allowed-tools' (prevents agents reaching outside their domain)"
    fi
  fi

  # composes_with recommended for all
  local composes_with_val
  composes_with_val="$(get_field "composes_with" "$file")"
  if [[ -z "$composes_with_val" ]]; then
    emit_issue WARN "$file" "" "missing recommended 'composes_with' (helps orchestrator understand skill relationships)"
  fi
}

# ---------------------------------------------------------------------------
# _glob_intersections <patterns_map_file> <allowlist>
# ---------------------------------------------------------------------------
# owns.patterns glob-intersection detector for cross_validate (SR18). Reads a
# TSV of "pattern<TAB>skill-name" lines and prints one line per cross-owner pair
# of patterns that can both match a single filename, EXCLUDING pairs whose two
# owners are in <allowlist> (newline-separated, sorted '::'-joined name pairs
# with a documented tiebreak). Output columns: ownerA<TAB>ownerB<TAB>patA<TAB>patB
# (owners sorted; each owner/pattern pair emitted once).
#
# Heuristic, NOT full glob algebra — it understands exactly two glob shapes:
#   extension  `*.EXT`      (e.g. *.tsx)      -> matches files ending .EXT
#   infix      `*.TOKEN.*`  (e.g. *.test.*)   -> matches files containing .TOKEN.
# and flags a pair as intersecting when: the patterns are identical; an
# extension meets an infix (a file like x.TOKEN.EXT matches both — the
# frontend `*.tsx` vs qe `*.test.*` case); or two infixes meet (x.A.B.y matches
# both). Any pattern that is NOT one of those two shapes (concrete filenames,
# prefix globs like `Dockerfile*`, char classes, `?`, braces, path-scoped
# globs) is conservatively treated as non-intersecting: this can miss real
# overlaps (false negatives) but never invents one (no false positives).
_glob_intersections() {
  local map_file="$1" allow="$2"
  python3 - "$map_file" "$allow" <<'PYEOF'
import sys, re

map_file = sys.argv[1]
allow = set(x for x in sys.argv[2].split('\n') if x.strip())

pairs = []
with open(map_file) as f:
    for line in f:
        line = line.rstrip('\n')
        if '\t' not in line:
            continue
        pat, owner = line.split('\t', 1)
        if pat and owner:
            pairs.append((pat, owner))

def ext(p):
    m = re.match(r'^\*\.([A-Za-z0-9]+)$', p)
    return m.group(1) if m else None

def infix(p):
    m = re.match(r'^\*\.([A-Za-z0-9]+)\.\*$', p)
    return m.group(1) if m else None

def intersect(p1, p2):
    if p1 == p2:
        return True
    e1, e2 = ext(p1), ext(p2)
    f1, f2 = infix(p1), infix(p2)
    if (e1 and f2) or (e2 and f1):   # extension meets infix
        return True
    if f1 and f2:                    # infix meets infix
        return True
    return False

seen = set()
n = len(pairs)
for i in range(n):
    for j in range(i + 1, n):
        p1, o1 = pairs[i]
        p2, o2 = pairs[j]
        if o1 == o2:
            continue
        if not intersect(p1, p2):
            continue
        key = '::'.join(sorted([o1, o2]))
        if key in allow:
            continue
        dedup = (key, tuple(sorted([p1, p2])))
        if dedup in seen:
            continue
        seen.add(dedup)
        a, b = sorted([o1, o2])
        print('\t'.join([a, b, p1, p2]))
PYEOF
}

# ---------------------------------------------------------------------------
# Cross-skill validation (requires all files)
# ---------------------------------------------------------------------------
cross_validate() {
  local files=("$@")

  # Build name→file map and collect owns.directories
  # Use temp files (bash 3.2 has no associative arrays)
  local name_map_file
  name_map_file="$(mktemp "${TMPDIR:-/tmp}/ats-lint-names.XXXXXX")"
  local owns_map_file
  owns_map_file="$(mktemp "${TMPDIR:-/tmp}/ats-lint-owns.XXXXXX")"
  local patterns_map_file
  patterns_map_file="$(mktemp "${TMPDIR:-/tmp}/ats-lint-pats.XXXXXX")"
  # shellcheck disable=SC2064 # capture current values of temp files
  trap "rm -f '$name_map_file' '$owns_map_file' '$patterns_map_file'" RETURN

  local f name owns_dirs dir owns_pats pat

  # First pass: collect names and ownership
  for f in "${files[@]}"; do
    name="$(get_field "name" "$f")"
    [[ -z "$name" ]] && continue
    # Append "name TAB file" to map
    printf '%s\t%s\n' "$name" "$f" >> "$name_map_file"

    owns_dirs="$(get_owns_dirs "$f")"
    if [[ -n "$owns_dirs" ]]; then
      while IFS= read -r dir; do
        [[ -z "$dir" ]] && continue
        printf '%s\t%s\n' "$dir" "$f" >> "$owns_map_file"
      done <<< "$owns_dirs"
    fi

    # Collect owns.patterns keyed by skill NAME (for the glob-intersection check)
    owns_pats="$(get_owns_patterns "$f")"
    if [[ -n "$owns_pats" ]]; then
      while IFS= read -r pat; do
        [[ -z "$pat" ]] && continue
        printf '%s\t%s\n' "$pat" "$name" >> "$patterns_map_file"
      done <<< "$owns_pats"
    fi
  done

  # Check name uniqueness
  while IFS= read -r name; do
    local count
    count="$(grep -c "^${name}	" "$name_map_file" || true)"
    if (( count > 1 )); then
      local files_with_name
      files_with_name="$(grep "^${name}	" "$name_map_file" | awk -F'\t' '{print $2}' | tr '\n' ' ')"
      emit_issue ERROR "(cross-skill)" "" "name '$name' is not unique: $files_with_name"
    fi
  done < <(awk -F'\t' '{print $1}' "$name_map_file" | sort | uniq)

  # Check owns.directories uniqueness (no overlap between role skills)
  while IFS= read -r dir; do
    local count
    count="$(grep -c "^${dir}	" "$owns_map_file" || true)"
    if (( count > 1 )); then
      local owners
      owners="$(grep "^${dir}	" "$owns_map_file" | awk -F'\t' '{print $2}' | tr '\n' ' ')"
      emit_issue ERROR "(cross-skill)" "" "owns.directories '$dir' claimed by multiple skills: $owners"
    fi
  done < <(awk -F'\t' '{print $1}' "$owns_map_file" | sort | uniq)

  # Check owns.patterns glob intersections across DIFFERENT skills (SR18). The
  # directory/uniqueness checks above only compare pattern strings for equality;
  # two DIFFERENT strings can still both match one file (e.g. frontend `*.tsx`
  # and qe `*.test.*` both match Button.test.tsx). WARN, don't fail — an
  # intersection is a design smell, not always a defect, and some are resolved
  # by a documented tiebreak.
  #
  # Documented-tiebreak allowlist: newline-separated, sorted '::'-joined skill
  # name pairs whose overlap is intentional and stated in
  # skills/orchestrator/references/file-ownership.md. Seed = frontend/qe:
  # test/spec files (qe-agent) win over UI-extension patterns (frontend-agent),
  # so Button.test.tsx belongs to qe-agent. Add a pair here only after recording
  # the tiebreak in that ownership map.
  local glob_tiebreak_allow="frontend-agent::qe-agent"
  if [[ -s "$patterns_map_file" ]]; then
    while IFS=$'\t' read -r g_owner_a g_owner_b g_pat_a g_pat_b; do
      [[ -z "$g_owner_a" ]] && continue
      emit_issue WARN "(cross-skill)" "" \
        "owns.patterns overlap — '$g_pat_a' ($g_owner_a) and '$g_pat_b' ($g_owner_b) can both match one file; assign the overlap to exactly one skill or document a tiebreak"
    done < <(_glob_intersections "$patterns_map_file" "$glob_tiebreak_allow")
  fi

  # Check composes_with references exist
  local all_names
  all_names="$(awk -F'\t' '{print $1}' "$name_map_file" | sort)"

  # Known bare external refs: skills that live outside this collection (a global
  # ~/.claude/skills/ skill, or a bare-invoked plugin skill) or Claude Code
  # built-in slash commands. Bare is their invocable form, so they are legitimate
  # and must not flag as "unknown". This is the allowlist mechanism for
  # non-namespaced externals in BOTH composes_with and spawned_by (colon-namespaced
  # refs like `plugin:name` are skipped separately, by design). Only add
  # genuinely-verified externals. See FA6, SR24.
  #   artifact-design, dataviz — host-global design skills that artifact-publish
  #   composes_with; they ship with the Claude Code host, not this collection.
  local known_external=" ux-review ui-ux-pro-max claude-api loop schedule artifact-design dataviz "

  for f in "${files[@]}"; do
    while IFS= read -r ref_name; do
      [[ -z "$ref_name" ]] && continue
      # Plugin-namespaced refs (plugin:name) are external by definition — out of
      # scope for in-collection resolution, so they are never flagged.
      [[ "$ref_name" == *:* ]] && continue
      # Known bare externals (global skills / built-in commands) are also fine.
      [[ "$known_external" == *" $ref_name "* ]] && continue
      if ! printf '%s\n' "$all_names" | grep -qxF "$ref_name"; then
        emit_issue WARN "$f" "" "composes_with references unknown skill '$ref_name'"
      fi
    done < <(get_array "composes_with" "$f")

    while IFS= read -r ref_name; do
      [[ -z "$ref_name" ]] && continue
      [[ "$ref_name" == *:* ]] && continue
      [[ "$known_external" == *" $ref_name "* ]] && continue
      if ! printf '%s\n' "$all_names" | grep -qxF "$ref_name"; then
        emit_issue WARN "$f" "" "spawned_by references unknown skill '$ref_name'"
      fi
    done < <(get_array "spawned_by" "$f")
  done
}

# ---------------------------------------------------------------------------
# lint_changed [base-ref]   (SR13: version-bump-drift guard)
# ---------------------------------------------------------------------------
# Opt-in, git-based check: ERROR when a skill's SKILL.md BODY (everything after
# the closing frontmatter ---) changed versus a base ref but its frontmatter
# `version:` did NOT. Frontmatter-only edits (e.g. a description tweak) do not
# require a bump — only body changes do.
#
# Compares the base ref against the WORKING TREE (staged + unstaged), so it
# catches local edits before they are committed. New files (absent in the base)
# and deletions are skipped: drift needs a prior version to compare against.
# base-ref defaults to origin/main, then main. This is NOT part of the static
# lint (it needs git) and is deliberately NOT wired into CI here.
# bash-3.2-safe. Exits 0 (no drift) / 1 (drift) / 2 (git/base-ref error).
lint_changed() {
  local base_ref="$1"

  if ! git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ats_err "--changed: not inside a git work tree"
    exit 2
  fi

  if [[ -z "$base_ref" ]]; then
    if git -C "$REPO_ROOT" rev-parse --verify -q origin/main >/dev/null 2>&1; then
      base_ref="origin/main"
    elif git -C "$REPO_ROOT" rev-parse --verify -q main >/dev/null 2>&1; then
      base_ref="main"
    else
      ats_err "--changed: no base ref found (tried origin/main, main); pass one explicitly"
      exit 2
    fi
  fi

  if ! git -C "$REPO_ROOT" rev-parse --verify -q "${base_ref}^{commit}" >/dev/null 2>&1; then
    ats_err "--changed: base ref '$base_ref' does not resolve to a commit"
    exit 2
  fi

  # Changed SKILL.md paths (repo-relative). Filter with grep rather than relying
  # on git pathspec magic, so nested paths are always matched.
  local changed
  changed="$(git -C "$REPO_ROOT" diff --name-only "$base_ref" 2>/dev/null | grep -E '(^|/)SKILL\.md$' || true)"

  local n_drift=0 n_checked=0
  local rel nowfile basecontent basetmp vbase vnow bbase bnow
  if [[ -n "$changed" ]]; then
    while IFS= read -r rel; do
      [[ -z "$rel" ]] && continue
      nowfile="$REPO_ROOT/$rel"
      [[ -f "$nowfile" ]] || continue   # deleted in the work tree — skip
      basecontent="$(git -C "$REPO_ROOT" show "${base_ref}:${rel}" 2>/dev/null || true)"
      [[ -z "$basecontent" ]] && continue   # new file (absent in base) — no prior version
      basetmp="$(mktemp "${TMPDIR:-/tmp}/ats-drift.XXXXXX")"
      printf '%s\n' "$basecontent" > "$basetmp"
      vbase="$(get_field version "$basetmp")"
      vnow="$(get_field version "$nowfile")"
      bbase="$(get_body "$basetmp")"
      bnow="$(get_body "$nowfile")"
      rm -f "$basetmp"
      n_checked=$(( n_checked + 1 ))
      if [[ "$bbase" != "$bnow" && "$vbase" == "$vnow" ]]; then
        emit_issue ERROR "$rel" "" \
          "SKILL.md body changed since ${base_ref} but its version stayed ${vnow:-unset} — bump the frontmatter version field"
        n_drift=$(( n_drift + 1 ))
      fi
    done <<< "$changed"
  fi

  printf 'Version-drift check vs %s: %d changed SKILL.md file(s), %d drift(s).\n' \
    "$base_ref" "$n_checked" "$n_drift"
  local issue loc msg
  for issue in "${ERRORS[@]+"${ERRORS[@]}"}"; do
    msg="${issue##*:}"
    loc="${issue%:*}"
    printf '%-6s %s  %s\n' 'ERROR' "$loc" "$msg"
  done

  if (( n_drift > 0 )); then
    printf '\nFAILED: bump the version: of each skill whose body changed.\n'
    exit 1
  fi
  printf 'PASSED: no version-bump drift.\n'
  exit 0
}

# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

# Print issues in text format to stdout
print_text_report() {
  local n_files="$1"
  local n_errors=${#ERRORS[@]}
  local n_warns=${#WARNS[@]}

  printf 'Linting %s skills...\n\n' "$n_files"

  local issue
  for issue in "${ERRORS[@]+"${ERRORS[@]}"}"; do
    local loc msg
    # Split on last colon-prefixed message: "file:line:msg" or "file:msg"
    # We stored as "loc:msg" with loc possibly containing ":"
    # Strategy: last field after ":" is the message if it starts uppercase, else join
    msg="${issue##*:}"
    loc="${issue%:*}"
    printf '%-6s %s  %s\n' 'ERROR' "$loc" "$msg"
  done

  if ! $QUIET; then
    for issue in "${WARNS[@]+"${WARNS[@]}"}"; do
      msg="${issue##*:}"
      loc="${issue%:*}"
      printf '%-6s %s  %s\n' 'WARN' "$loc" "$msg"
    done
  fi

  if $VERBOSE; then
    for issue in "${INFOS[@]+"${INFOS[@]}"}"; do
      msg="${issue##*:}"
      loc="${issue%:*}"
      printf '%-6s %s  %s\n' 'INFO' "$loc" "$msg"
    done
  fi

  printf '\nResults: %d error(s), %d warning(s) across %d skills.\n' \
    "$n_errors" "$n_warns" "$n_files"

  if (( n_errors > 0 )); then
    printf 'FAILED: fix the errors above before merging.\n'
  else
    printf 'PASSED\n'
  fi
}

# Print issues in JUnit XML format to stdout
print_junit_report() {
  local n_files="$1"
  local n_errors=${#ERRORS[@]}

  printf '<?xml version="1.0" encoding="UTF-8"?>\n'
  printf '<testsuites name="skill-lint" tests="%s" failures="%s" errors="0">\n' \
    "$n_files" "$n_errors"

  # Group by file
  local all_issues=()
  local issue
  for issue in "${ERRORS[@]+"${ERRORS[@]}"}"; do
    all_issues+=("ERROR:$issue")
  done
  if ! $QUIET; then
    for issue in "${WARNS[@]+"${WARNS[@]}"}"; do
      all_issues+=("WARN:$issue")
    done
  fi

  # Collect unique files mentioned
  local files_seen=()
  for issue in "${all_issues[@]+"${all_issues[@]}"}"; do
    local raw="${issue#*:}"
    local loc="${raw%:*}"
    # strip line number if present (loc might be "file:lineno")
    local fpart
    fpart="$(printf '%s' "$loc" | sed 's/:[0-9]*$//')"
    local already=false fs
    for fs in "${files_seen[@]+"${files_seen[@]}"}"; do
      [[ "$fs" == "$fpart" ]] && already=true && break
    done
    $already || files_seen+=("$fpart")
  done

  local fpart
  for fpart in "${files_seen[@]+"${files_seen[@]}"}"; do
    local suite_name="${fpart#"$REPO_ROOT"/}"
    local f_errors=0 f_warns=0
    for issue in "${ERRORS[@]+"${ERRORS[@]}"}"; do
      [[ "$issue" == "${fpart}"* ]] && f_errors=$(( f_errors + 1 ))
    done
    for issue in "${WARNS[@]+"${WARNS[@]}"}"; do
      [[ "$issue" == "${fpart}"* ]] && f_warns=$(( f_warns + 1 ))
    done
    local f_tests=$(( f_errors + f_warns ))
    (( f_tests == 0 )) && f_tests=1

    printf '  <testsuite name="%s" tests="%s" failures="%s">\n' \
      "$suite_name" "$f_tests" "$f_errors"

    for issue in "${ERRORS[@]+"${ERRORS[@]}"}"; do
      if [[ "$issue" == "${fpart}"* ]]; then
        local msg="${issue##*:}"
        local loc="${issue%:*}"
        local lineno="${loc##*:}"
        [[ "$lineno" =~ ^[0-9]+$ ]] || lineno=""
        printf '    <testcase classname="frontmatter" name="%s">\n' \
          "$(printf '%s' "$msg" | sed 's/&/\&amp;/g;s/</\&lt;/g;s/>/\&gt;/g;s/"/\&quot;/g')"
        printf '      <failure message="%s"/>\n' \
          "$(printf '%s' "$msg" | sed 's/&/\&amp;/g;s/</\&lt;/g;s/>/\&gt;/g;s/"/\&quot;/g')"
        printf '    </testcase>\n'
      fi
    done

    printf '  </testsuite>\n'
  done

  printf '</testsuites>\n'
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
usage() {
  sed -n '3,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --quiet)        QUIET=true; shift ;;
      --verbose)      VERBOSE=true; shift ;;
      --fix-trivial)  FIX_TRIVIAL=true; shift ;;  # future: implement trivial auto-fixes
      --format)       FORMAT="${2:?'--format requires a value'}"; shift 2 ;;
      --standard)     print_standard; exit 0 ;;
      --changed)
        CHANGED_MODE=true
        # Optional base ref immediately follows if it is not another flag.
        # --changed ignores PATH args, so consuming one non-flag token is safe.
        if [[ $# -ge 2 && "$2" != -* ]]; then
          CHANGED_BASE="$2"; shift 2
        else
          shift
        fi
        ;;
      --help|-h)      usage ;;
      -*)             ats_err "Unknown option: $1"; exit 2 ;;
      *)              LINT_PATHS+=("$1"); shift ;;
    esac
  done

  # --changed is a distinct, git-based mode (SR13): run the version-drift guard
  # and exit. It deliberately does not run the static per-file / cross-skill lint.
  if $CHANGED_MODE; then
    lint_changed "$CHANGED_BASE"
    # lint_changed always exits; this is unreachable but keeps intent explicit.
    exit $?
  fi

  case "$FORMAT" in
    text|junit) ;;
    *) ats_err "Unknown format '$FORMAT'. Use: text or junit"; exit 2 ;;
  esac

  # Collect files
  local files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(collect_files)

  if [[ ${#files[@]} -eq 0 ]]; then
    printf 'No SKILL.md files found.\n' >&2
    exit 1
  fi

  # Per-skill lint (--fix-trivial is reserved for a future interactive pass)
  if $FIX_TRIVIAL; then
    ats_warn "--fix-trivial: auto-fix not yet implemented; running lint-only"
  fi
  local f
  for f in "${files[@]}"; do
    lint_one "$f"
  done

  # Cross-skill checks
  cross_validate "${files[@]}"

  local n_errors=${#ERRORS[@]}
  local n_files=${#files[@]}

  # Print report
  if [[ "$FORMAT" == "junit" ]]; then
    print_junit_report "$n_files"
  else
    print_text_report "$n_files"
  fi

  if (( n_errors > 0 )); then
    exit 1
  fi
  exit 0
}

main "$@"
