#!/usr/bin/env bash
# lib/frontmatter.sh — SKILL.md frontmatter parser for Skill Madness.
#
# get_body() is adapted from msitarzewski/agency-agents (MIT). See
# ACKNOWLEDGMENTS.md at the repo root.
#
# Uses Python 3 + PyYAML for correctness on multiline descriptions.
# Each SKILL.md is parsed ONCE per process: the first field read spawns a
# single python3 that writes every frontmatter field to a per-file cache
# directory; all subsequent reads (including from command-substitution
# subshells) are served from that cache with plain bash — no interpreter
# spawn. This is what keeps a full convert.sh run (71 skills x 11 tools,
# thousands of field reads) at seconds instead of minutes.
#
# Cache invariants:
#   - The cache is keyed to this process ($$ + $RANDOM at source time), so
#     files edited BETWEEN script runs are always re-parsed. Files must not
#     be mutated and re-read within one process (no current caller does).
#   - Under bats, the cache lives in $BATS_TEST_TMPDIR (cleaned by bats).
#     Otherwise it lives under $TMPDIR and is removed by an EXIT trap,
#     registered only when the sourcing script has no EXIT trap of its own;
#     scripts that set their own EXIT trap should also call fm_cache_clear.
#
# Public API (all print to stdout):
#   get_field <field> <file>        — scalar field value (whitespace-collapsed)
#   get_field_raw <field> <file>    — scalar field value (newlines preserved)
#   get_array <field> <file>        — one array element per line
#   get_owns_dirs <file>            — owns.directories, one per line
#   get_owns_patterns <file>        — owns.patterns, one per line
#   get_owns_shared <file>          — owns.shared_read, one per line
#   get_body <file>                 — everything after the closing ---
#   fm_raw <file>                   — raw YAML between the two --- markers
#   fm_check <file>                 — exit 1 if frontmatter malformed
#   fm_has_field <field> <file>     — exit 0 if field present, 1 if absent
#   fm_cache_clear                  — delete this process's parse cache
#
# Usage:
#   . "$(dirname "$0")/lib/frontmatter.sh"

# ---------------------------------------------------------------------------
# Cache location. Fixed at source time so every command-substitution subshell
# sees the same path. $RANDOM guards against PID reuse picking up a stale
# cache from an earlier, uncleaned run.
# ---------------------------------------------------------------------------
if [[ -z "${_FM_CACHE_DIR:-}" ]]; then
  _FM_CACHE_DIR="${BATS_TEST_TMPDIR:-${TMPDIR:-/tmp}}/ats-fm-cache.$$.$RANDOM"
fi

fm_cache_clear() {
  [[ -n "${_FM_CACHE_DIR:-}" && -d "$_FM_CACHE_DIR" ]] && rm -rf "$_FM_CACHE_DIR"
  return 0
}

# Register cleanup only when the caller has no EXIT trap (bash 3.2 reports
# the parent's traps for `trap -p` inside a command substitution). Callers
# that install their own EXIT trap later (e.g. convert.sh) take over cleanup
# by calling fm_cache_clear from it. Never touch bats' EXIT trap machinery.
if [[ -z "${BATS_TEST_FILENAME:-}" && -z "$(trap -p EXIT 2>/dev/null)" ]]; then
  trap fm_cache_clear EXIT
fi

# ---------------------------------------------------------------------------
# _fm_entry <file>
# Set _FM_ENTRY to the per-file cache directory. The key is the sanitized
# path plus its length; a stored .path file catches the residual collision
# case (two same-length paths differing only in non-portable characters),
# which falls back to a re-parse.
# ---------------------------------------------------------------------------
_fm_entry() {
  local file="$1"
  local key="${file//[^A-Za-z0-9._-]/_}"
  if [[ ${#key} -gt 180 ]]; then
    key="${key:$(( ${#key} - 180 ))}"
  fi
  _FM_ENTRY="$_FM_CACHE_DIR/${#file}.$key"
}

# ---------------------------------------------------------------------------
# _fm_load <file>
# Ensure the parse cache for <file> exists; sets _FM_ENTRY. Returns non-zero
# (propagating python's stderr/exit) when the file is unreadable or its YAML
# is invalid — mirroring the old per-call parser's failure mode.
# ---------------------------------------------------------------------------
_fm_load() {
  local file="$1" cached=""
  _fm_entry "$file"
  if [[ -f "$_FM_ENTRY/.done" ]]; then
    IFS= read -r cached < "$_FM_ENTRY/.path" || true
    [[ "$cached" == "$file" ]] && return 0
    rm -rf "$_FM_ENTRY"   # key collision: drop and re-parse
  fi
  _fm_parse "$file"
}

# ---------------------------------------------------------------------------
# _fm_parse <file>
# One python3 run that mirrors the print logic of every accessor and writes
# each result to its own cache file:
#   scalar.<field>  — get_field output   (collapsed value + newline)
#   raw.<field>     — get_field_raw output (verbatim bytes, no added newline)
#   array.<field>   — get_array output   (one element per line)
#   owns.<subfield> — get_owns_* output
# A file is written only when the old accessor would have printed something;
# an absent cache file means "print nothing". Without PyYAML the emitter
# degrades exactly like the old code: regex-parsed top-level scalars only.
# Failures are not cached, so every call on a broken file retries (and
# tracebacks) just as the per-call parsers did.
# ---------------------------------------------------------------------------
_fm_parse() {
  local file="$1"
  rm -rf "$_FM_ENTRY"
  mkdir -p "$_FM_ENTRY"
  printf '%s\n' "$file" > "$_FM_ENTRY/.path"
  if ! python3 - "$file" "$_FM_ENTRY" <<'PYEOF'
import sys, os, re

path = sys.argv[1]
outdir = sys.argv[2]

with open(path) as f:
    content = f.read()

def emit(kind, key, data):
    if data == '':
        return
    fname = kind + '.' + key.replace('/', '_')
    with open(os.path.join(outdir, fname), 'w') as fh:
        fh.write(data)

lines = content.split('\n')
if not lines or lines[0].rstrip() != '---':
    sys.exit(0)

fm_end = None
for i in range(1, len(lines)):
    if lines[i].rstrip() == '---':
        fm_end = i
        break
if fm_end is None:
    sys.exit(0)

fm_text = '\n'.join(lines[1:fm_end])

try:
    import yaml
except ImportError:
    yaml = None

if yaml is None:
    # Hand-rolled fallback for simple scalars only (mirrors the old
    # get_field fallback; raw/array/owns stay empty, as before).
    seen = set()
    for line in fm_text.split('\n'):
        if line.startswith((' ', '\t')):
            continue
        m = re.match(r'^([^:]+):\s*(.*)$', line)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        val = m.group(2).strip()
        if val in ('|', '>', '>-', '|-'):
            continue  # multiline -- can't parse without yaml
        if val.startswith(('"', "'")):
            out = val.strip('"\'')
        elif val.lower() in ('true', 'false'):
            out = val.lower()
        else:
            out = val
        emit('scalar', m.group(1), out + '\n')
    sys.exit(0)

data = yaml.safe_load(fm_text) or {}

for key, val in data.items():
    if not isinstance(key, str):
        continue  # shell callers can only ask for string keys
    if val is None:
        continue  # every accessor printed nothing for null values
    # scalar.<key> — get_field
    if isinstance(val, bool):
        emit('scalar', key, ('true' if val else 'false') + '\n')
    elif isinstance(val, list):
        emit('scalar', key, ','.join(str(v) for v in val) + '\n')
    elif isinstance(val, dict):
        pass  # dicts not useful as scalar
    else:
        emit('scalar', key, ' '.join(str(val).split()) + '\n')
    # raw.<key> — get_field_raw
    if isinstance(val, bool):
        emit('raw', key, 'true' if val else 'false')
    elif isinstance(val, str):
        emit('raw', key, val)
    else:
        emit('raw', key, str(val))
    # array.<key> — get_array
    if isinstance(val, list):
        emit('array', key, ''.join(str(item) + '\n' for item in val))
    else:
        emit('array', key, str(val) + '\n')

owns = data.get('owns') or {}
if isinstance(owns, dict):
    for sub in ('directories', 'patterns', 'shared_read'):
        items = owns.get(sub) or []
        emit('owns', sub, ''.join(str(item) + '\n' for item in items))
PYEOF
  then
    rm -rf "$_FM_ENTRY"   # never cache a failed parse
    return 1
  fi
  : > "$_FM_ENTRY/.done"
  return 0
}

# ---------------------------------------------------------------------------
# get_field <field> <file>
# Print a single scalar field value with whitespace collapsed to one line.
# ---------------------------------------------------------------------------
get_field() {
  local field="$1" file="$2" f v=""
  _fm_load "$file" || return $?
  f="$_FM_ENTRY/scalar.${field//\//_}"
  if [[ -f "$f" ]]; then
    IFS= read -r v < "$f" || true
    printf '%s\n' "$v"
  fi
  return 0
}

# ---------------------------------------------------------------------------
# get_field_raw <field> <file>
# Print a scalar field value preserving internal newlines (for description).
# ---------------------------------------------------------------------------
get_field_raw() {
  local field="$1" file="$2" f
  _fm_load "$file" || return $?
  f="$_FM_ENTRY/raw.${field//\//_}"
  [[ -f "$f" ]] && cat "$f"
  return 0
}

# ---------------------------------------------------------------------------
# get_array <field> <file>
# Print each element of a YAML array field, one per line.
# ---------------------------------------------------------------------------
get_array() {
  local field="$1" file="$2" f
  _fm_load "$file" || return $?
  f="$_FM_ENTRY/array.${field//\//_}"
  [[ -f "$f" ]] && cat "$f"
  return 0
}

# ---------------------------------------------------------------------------
# get_owns_dirs / get_owns_patterns / get_owns_shared <file>
# Print owns sub-field elements, one per line.
# ---------------------------------------------------------------------------
_fm_owns() {
  local file="$1" sub="$2" f
  _fm_load "$file" || return $?
  f="$_FM_ENTRY/owns.$sub"
  [[ -f "$f" ]] && cat "$f"
  return 0
}

get_owns_dirs()     { _fm_owns "$1" directories; }
get_owns_patterns() { _fm_owns "$1" patterns; }
get_owns_shared()   { _fm_owns "$1" shared_read; }

# ---------------------------------------------------------------------------
# get_body <file>
# Print everything after the closing --- of the frontmatter block.
# ---------------------------------------------------------------------------
get_body() {
  local file="$1"
  awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$file"
}

# ---------------------------------------------------------------------------
# fm_raw <file>
# Print the raw YAML text between the two --- markers (no delimiters).
# ---------------------------------------------------------------------------
fm_raw() {
  local file="$1"
  awk 'NR==1{next} /^---$/{exit} {print}' "$file"
}

# ---------------------------------------------------------------------------
# fm_check <file>
# Return 0 if frontmatter is well-formed; print error and return 1 if not.
# ---------------------------------------------------------------------------
fm_check() {
  local file="$1"
  local first_line found line_num
  first_line=$(head -1 "$file")
  if [[ "$first_line" != "---" ]]; then
    printf '[frontmatter] ERROR: %s: missing opening ---\n' "$file" >&2
    return 1
  fi
  found=0
  line_num=0
  while IFS= read -r line; do
    (( line_num++ )) || true
    if (( line_num == 1 )); then continue; fi
    if [[ "$line" == "---" ]]; then found=1; break; fi
    if (( line_num > 100 )); then break; fi
  done < "$file"
  if (( found == 0 )); then
    printf '[frontmatter] ERROR: %s: no closing --- within 100 lines\n' "$file" >&2
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# fm_has_field <field> <file>
# Return 0 if the field is present and non-empty in frontmatter, 1 otherwise.
# ---------------------------------------------------------------------------
fm_has_field() {
  local field="$1" file="$2" f v=""
  _fm_load "$file" || return 1
  f="$_FM_ENTRY/scalar.${field//\//_}"
  [[ -f "$f" ]] || return 1
  IFS= read -r v < "$f" || true
  [[ -n "$v" ]]
}
