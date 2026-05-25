#!/usr/bin/env bash
#
# scan-skills.sh — Deterministic supply-chain / injection scanner for skills/.
#
# Scans every SKILL.md (and its references/) under the given paths for secrets,
# prompt-injection payloads, invisible-unicode tricks, and untrusted compose
# references. LLM-free and reproducible, so it can be a blocking CI gate.
#
# Usage:
#   scripts/scan-skills.sh [--check | --text | --json] [PATH ...] [--help]
#
#   --check  (default) scan; exit 1 if any HIGH-severity finding; else 0
#   --text   human-readable findings grouped by severity
#   --json   machine-readable findings array
#
# PATH may be a directory (recurse) or an individual file.
# If no PATH given, scans skills/ (excluding archive/ + in-progress/).
#
# Rule set (severity):
#   secret-aws          HIGH   AKIA... access-key ids, AWS secret-key shapes
#   secret-generic      HIGH   api_key/token/password/secret = long literal;
#                              Authorization: Bearer <token>
#   private-key         HIGH   -----BEGIN ... PRIVATE KEY-----
#   zero-width-unicode  HIGH   zero-width / invisible / bidi-control codepoints
#   prompt-injection    MEDIUM "ignore previous instructions" override phrasing
#   untrusted-composes  MEDIUM composes_with entry naming a skill not present
#   mcp-ref             LOW    references to MCP servers (informational)
#   long-base64         LOW    base64-looking blobs >= 200 chars
#
# Ignore mechanisms (both supported):
#   - inline annotation on the same line:  # scan-skills:ignore[ rule]
#   - a .scan-skills-ignore file of "path:rule" entries (path relative to repo
#     root or absolute; rule omitted means all rules for that path)
#
# Findings carry path, line, rule, severity, excerpt (truncated; never the full
# secret). Pure bash + python3 stdlib. No network, no eval.
#
# Exit codes: 0 no HIGH findings, 1 HIGH finding present (in --check), 2 arg error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"
IGNORE_FILE="$REPO_ROOT/.scan-skills-ignore"

# ---------------------------------------------------------------------------
# CLI state
# ---------------------------------------------------------------------------
MODE="check"
SCAN_PATHS=()

usage() {
  sed -n '3,40p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

# ---------------------------------------------------------------------------
# Collect files to scan: SKILL.md + everything under references/.
# Excludes archive/ and in-progress/ anywhere in the path.
# ---------------------------------------------------------------------------
collect_files() {
  local roots=()
  if [[ ${#SCAN_PATHS[@]} -eq 0 ]]; then
    roots=("$SKILLS_ROOT")
  else
    roots=("${SCAN_PATHS[@]}")
  fi

  local p
  for p in "${roots[@]}"; do
    if [[ -f "$p" ]]; then
      printf '%s\n' "$p"
    elif [[ -d "$p" ]]; then
      # SKILL.md files and any file under a references/ directory.
      find "$p" \( -path '*/archive/*' -o -path '*/in-progress/*' \) -prune -o \
        -type f \( -name 'SKILL.md' -o -path '*/references/*' \) -print
    else
      ats_err "scan-skills: not a file or directory: $p"
    fi
  done | sort -u
}

# ---------------------------------------------------------------------------
# Known skill names — for untrusted-composes resolution.
# Printed one per line. Always derived from the full repo skills/ tree (not the
# scan paths) so a narrow scan still resolves real cross-skill references.
# ---------------------------------------------------------------------------
known_skill_names() {
  python3 - "$SKILLS_ROOT" <<'PYEOF'
import os, sys, re
root = sys.argv[1]
names = set()
for dirpath, dirnames, filenames in os.walk(root):
    if '/archive' in dirpath or '/in-progress' in dirpath:
        continue
    if 'SKILL.md' in filenames:
        # name = directory basename (lint enforces name == dir)
        names.add(os.path.basename(dirpath))
        # also trust an explicit name: field if present
        try:
            with open(os.path.join(dirpath, 'SKILL.md'), encoding='utf-8', errors='replace') as f:
                content = f.read()
        except OSError:
            continue
        lines = content.split('\n')
        if lines and lines[0].rstrip() == '---':
            for i in range(1, len(lines)):
                if lines[i].rstrip() == '---':
                    break
                m = re.match(r'^name:\s*(\S+)', lines[i])
                if m:
                    names.add(m.group(1).strip('"\''))
for n in sorted(names):
    print(n)
PYEOF
}

# ---------------------------------------------------------------------------
# Core scan — delegated to python3 for unicode + regex correctness.
# Emits one JSON object per finding to stdout, one per line (JSONL), plus a
# final summary line is NOT emitted here (the bash layer aggregates).
#
# Args: <ignore_file> <known_names_file> <file>...
# ---------------------------------------------------------------------------
run_scan() {
  local ignore_file="$1"; shift
  local names_file="$1"; shift
  python3 - "$REPO_ROOT" "$ignore_file" "$names_file" "$@" <<'PYEOF'
import os, re, sys, json

repo_root = sys.argv[1]
ignore_file = sys.argv[2]
names_file = sys.argv[3]
files = sys.argv[4:]

# ---- known skill names ----------------------------------------------------
known = set()
try:
    with open(names_file, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                known.add(line)
except OSError:
    pass

# ---- file-level ignore entries (path:rule) --------------------------------
# stored as dict: relpath -> set(rules) ; '*' rule means all
file_ignores = {}
try:
    with open(ignore_file, encoding='utf-8') as f:
        for raw in f:
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue
            if ':' in line:
                # split on the LAST colon so paths with colons survive (rare)
                path_part, rule_part = line.rsplit(':', 1)
                rule_part = rule_part.strip()
            else:
                path_part, rule_part = line, '*'
            path_part = path_part.strip()
            if not path_part:
                continue
            file_ignores.setdefault(path_part, set()).add(rule_part or '*')
except OSError:
    pass

# Pre-resolve ignore-file path keys (relative -> repo-rooted abs, plus realpath)
# so symlinked temp dirs (e.g. macOS /var -> /private/var) still match.
_ignore_keys = {}
for _k, _rules in file_ignores.items():
    cands = {_k}
    if not os.path.isabs(_k):
        cands.add(os.path.normpath(os.path.join(repo_root, _k)))
    for c in list(cands):
        try:
            cands.add(os.path.realpath(c))
        except OSError:
            pass
    for c in cands:
        _ignore_keys.setdefault(c, set()).update(_rules)

def file_ignored(relpath, abspath, rule):
    keys = {relpath, abspath}
    try:
        keys.add(os.path.realpath(abspath))
    except OSError:
        pass
    for key in keys:
        rules = _ignore_keys.get(key)
        if rules and (rule in rules or '*' in rules):
            return True
    return False

# ---- inline ignore annotation ---------------------------------------------
# "# scan-skills:ignore" -> all rules on this line
# "# scan-skills:ignore secret-generic" -> just that rule
INLINE_RE = re.compile(r'#\s*scan-skills:ignore(?:\s+([a-z0-9-]+))?', re.IGNORECASE)

def inline_ignored(line, rule):
    matched = False
    for m in INLINE_RE.finditer(line):
        matched = True
        which = m.group(1)
        if which is None or which == rule:
            return True
    return False

# ---- excerpt helper: truncate + redact secret-looking middles -------------
def make_excerpt(line, rule):
    s = line.strip()
    # Generic hard cap.
    cap = 80
    if len(s) > cap:
        s = s[:cap] + '...'
    # For secret rules, redact the captured secret so the full value never
    # appears, regardless of length.
    if rule in ('secret-aws', 'secret-generic', 'private-key', 'long-base64'):
        s = redact_secrets(s)
    return s

def redact_secrets(s):
    # Replace any run of >=8 secret-ish chars, keeping a short prefix only.
    def repl(m):
        tok = m.group(0)
        keep = min(4, len(tok))
        return tok[:keep] + '*' * (len(tok) - keep)
    return re.sub(r'[A-Za-z0-9/+_=.-]{8,}', repl, s)

# ---- rule definitions ------------------------------------------------------
# Each rule: (name, severity, scanner-callable(line)->bool)
# Some rules need extra context, handled separately below.

RE_AWS_ID = re.compile(r'\bAKIA[0-9A-Z]{16}\b')
# AWS secret key: 40 chars base64-ish assigned to an aws_secret_access_key-like
# field. Keep it specific to avoid hashing/docs false positives.
RE_AWS_SECRET = re.compile(
    r'(?i)aws[_-]?secret[_-]?access[_-]?key["\' ]*[:=]["\' ]*[A-Za-z0-9/+]{40}\b')

# Generic secret assignment: key = long literal value.
RE_GENERIC = re.compile(
    r'(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|'
    r'password|passwd|client[_-]?secret|api[_-]?secret|token|secret)\b'
    r'\s*[:=]\s*["\']?([A-Za-z0-9/+_.=-]{16,})["\']?')
RE_BEARER = re.compile(r'(?i)authorization\s*:\s*bearer\s+([A-Za-z0-9._-]{12,})')

RE_PRIVKEY = re.compile(
    r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----')

RE_INJECTION = re.compile(
    r'(?i)(ignore\s+(?:all\s+)?previous\s+instructions'
    r'|disregard\s+(?:the\s+)?above'
    r'|you\s+are\s+now\s+(?:a\b|an\b|the\b|in\b)'
    r'|system\s+prompt\s*:\s*\S)')

RE_MCP = re.compile(r'(?i)(mcp__[a-z0-9_]+|mcp\s+server|mcpServers|mcp-config)')
RE_BASE64 = re.compile(r'[A-Za-z0-9+/]{200,}={0,2}')

# Zero-width / invisible / bidi-control codepoints.
ZW_CODEPOINTS = {
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2060, 0xFEFF,
}

# Placeholder/example heuristics — values that are obviously not real secrets.
# These are commonly used in docs; treating them as findings would create
# noise but they are NOT silenced for the HIGH secret rules unless clearly a
# template token (e.g. <...>, ${...}, ALL_CAPS_PLACEHOLDER, xxx/your-...).
# Case-insensitive literal placeholder words (intentionally NOT including the
# ALL-CAPS env-var pattern — that one must stay case-sensitive so real lowercase
# tokens are not mistaken for env-var names).
PLACEHOLDER_RE = re.compile(
    r'^(?:<.*>|\$\{.*\}|x{6,}|your[-_].*|<?your_?.*>?'
    r'|example[-_].*|changeme|placeholder|redacted|\.\.\.)$', re.IGNORECASE)

def is_placeholder(value):
    v = value.strip().strip('"\'')
    if not v:
        return True
    if PLACEHOLDER_RE.match(v):
        return True
    # All-caps env-var / template token e.g. AWS_SECRET_ACCESS_KEY, $TOKEN.
    # Case-SENSITIVE: a lowercase literal is a real value, not a name.
    if re.fullmatch(r'\$?[A-Z][A-Z0-9_]{4,}', v):
        return True
    # contains template markers anywhere
    if '<' in v or '>' in v or '${' in v or v.startswith('$'):
        return True
    return False

findings = []

def add(path, relpath, abspath, lineno, line, rule, severity):
    if inline_ignored(line, rule):
        return
    if file_ignored(relpath, abspath, rule):
        return
    findings.append({
        'path': relpath,
        'line': lineno,
        'rule': rule,
        'severity': severity,
        'excerpt': make_excerpt(line, rule),
    })

def scan_text(relpath, abspath, content):
    lines = content.split('\n')
    for idx, line in enumerate(lines, 1):
        # --- zero-width / bidi (HIGH) ---
        for ch in line:
            if ord(ch) in ZW_CODEPOINTS:
                add(abspath if False else relpath, relpath, abspath, idx,
                    '<line contains invisible/bidi codepoint(s)>',
                    'zero-width-unicode', 'HIGH')
                break

        # --- private key (HIGH) ---
        if RE_PRIVKEY.search(line):
            add(relpath, relpath, abspath, idx, line, 'private-key', 'HIGH')

        # --- aws (HIGH) ---
        if RE_AWS_ID.search(line) or RE_AWS_SECRET.search(line):
            add(relpath, relpath, abspath, idx, line, 'secret-aws', 'HIGH')

        # --- generic secret (HIGH) ---
        m = RE_GENERIC.search(line)
        if m and not is_placeholder(m.group(1)):
            add(relpath, relpath, abspath, idx, line, 'secret-generic', 'HIGH')
        else:
            mb = RE_BEARER.search(line)
            if mb and not is_placeholder(mb.group(1)):
                add(relpath, relpath, abspath, idx, line, 'secret-generic', 'HIGH')

        # --- prompt injection (MEDIUM) ---
        if RE_INJECTION.search(line):
            add(relpath, relpath, abspath, idx, line, 'prompt-injection', 'MEDIUM')

        # --- mcp ref (LOW) ---
        if RE_MCP.search(line):
            add(relpath, relpath, abspath, idx, line, 'mcp-ref', 'LOW')

        # --- long base64 (LOW) ---
        if RE_BASE64.search(line):
            add(relpath, relpath, abspath, idx, line, 'long-base64', 'LOW')

# ---- frontmatter composes_with extraction ---------------------------------
def composes_with_entries(content):
    """Return list of (lineno, name) for composes_with array entries."""
    lines = content.split('\n')
    if not lines or lines[0].rstrip() != '---':
        return []
    fm_end = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() == '---':
            fm_end = i
            break
    if fm_end is None:
        return []
    def split_inline(text, lineno, out):
        for part in text.split(','):
            name = part.strip().strip('"\'')
            if name:
                out.append((lineno, name))

    entries = []
    in_dash_block = False   # YAML "- item" block form
    in_bracket = False      # multi-line [ ... ] inline-array form
    for i in range(1, fm_end):
        raw = lines[i]
        line = raw.rstrip()

        if in_bracket:
            # accumulate until the closing ]
            content = line
            closed = ']' in content
            content = content.split(']', 1)[0]
            split_inline(content, i + 1, entries)
            if closed:
                in_bracket = False
            continue

        # single-line inline: composes_with: [a, b, c]
        m = re.match(r'^composes_with:\s*\[(.*)\]\s*$', line)
        if m:
            split_inline(m.group(1), i + 1, entries)
            in_dash_block = False
            continue
        # multi-line inline starts: composes_with: [
        mo = re.match(r'^composes_with:\s*\[(.*)$', line)
        if mo:
            split_inline(mo.group(1), i + 1, entries)
            in_bracket = True
            in_dash_block = False
            continue
        if re.match(r'^composes_with:\s*$', line):
            in_dash_block = True
            continue
        if in_dash_block:
            mb = re.match(r'^\s*-\s*(.+?)\s*$', raw)
            if mb:
                name = mb.group(1).strip().strip('"\'')
                if name:
                    entries.append((i + 1, name))
            elif re.match(r'^\S', raw):
                # next top-level key ends the block
                in_dash_block = False
    return entries

def scan_composes(relpath, abspath, content):
    for lineno, name in composes_with_entries(content):
        # Namespaced references (plugin:skill) are explicit cross-plugin
        # pointers, not in-repo skills — by design they live elsewhere.
        if ':' in name:
            continue
        if name in known:
            continue
        # Build an excerpt for the offending entry line.
        excerpt = '- ' + name
        finding_line = excerpt
        if inline_ignored(finding_line, 'untrusted-composes') or \
           file_ignored(relpath, abspath, 'untrusted-composes'):
            continue
        findings.append({
            'path': relpath,
            'line': lineno,
            'rule': 'untrusted-composes',
            'severity': 'MEDIUM',
            'excerpt': "composes_with -> %s (not present under skills/)" % name,
        })

# ---- run -------------------------------------------------------------------
for fpath in files:
    abspath = os.path.abspath(fpath)
    try:
        relpath = os.path.relpath(abspath, repo_root)
    except ValueError:
        relpath = fpath
    try:
        with open(fpath, encoding='utf-8', errors='replace') as fh:
            content = fh.read()
    except OSError as e:
        sys.stderr.write("[scan-skills] cannot read %s: %s\n" % (fpath, e))
        continue
    scan_text(relpath, abspath, content)
    if os.path.basename(fpath) == 'SKILL.md':
        scan_composes(relpath, abspath, content)

for fnd in findings:
    sys.stdout.write(json.dumps(fnd) + '\n')
PYEOF
}

# ---------------------------------------------------------------------------
# Output formatters operate on a JSONL findings file.
# ---------------------------------------------------------------------------
emit_json() {
  local jsonl="$1"
  python3 - "$jsonl" <<'PYEOF'
import sys, json
out = []
with open(sys.argv[1], encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            out.append(json.loads(line))
print(json.dumps(out, indent=2))
PYEOF
}

emit_text() {
  local jsonl="$1"
  local n_high n_med n_low
  n_high="$(grep -c '"severity": "HIGH"' "$jsonl" 2>/dev/null || true)"
  n_med="$(grep -c '"severity": "MEDIUM"' "$jsonl" 2>/dev/null || true)"
  n_low="$(grep -c '"severity": "LOW"' "$jsonl" 2>/dev/null || true)"
  : "${n_high:=0}" "${n_med:=0}" "${n_low:=0}"

  local sev
  for sev in HIGH MEDIUM LOW; do
    local any=false line
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      if [[ "$any" == false ]]; then
        case "$sev" in
          HIGH)   ats_header "HIGH (blocking)";;
          MEDIUM) ats_header "MEDIUM";;
          LOW)    ats_header "LOW (informational)";;
        esac
        any=true
      fi
      printf '%s\n' "$line"
    done < <(python3 - "$jsonl" "$sev" <<'PYEOF'
import sys, json
target = sys.argv[2]
with open(sys.argv[1], encoding='utf-8') as f:
    for raw in f:
        raw = raw.strip()
        if not raw:
            continue
        d = json.loads(raw)
        if d['severity'] != target:
            continue
        print("  %s:%s  [%s]  %s" % (d['path'], d['line'], d['rule'], d['excerpt']))
PYEOF
)
  done

  ats_header "Summary"
  printf '  HIGH: %s   MEDIUM: %s   LOW: %s\n' "$n_high" "$n_med" "$n_low"
  if (( n_high > 0 )); then
    ats_err "scan-skills: $n_high HIGH finding(s) — blocking."
  else
    ats_ok "scan-skills: no HIGH findings."
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --check) MODE="check"; shift ;;
      --text)  MODE="text";  shift ;;
      --json)  MODE="json";  shift ;;
      --help|-h) usage ;;
      -*) ats_err "Unknown option: $1"; exit 2 ;;
      *)  SCAN_PATHS+=("$1"); shift ;;
    esac
  done

  # Collect files
  local files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] && files+=("$f")
  done < <(collect_files)

  if [[ ${#files[@]} -eq 0 ]]; then
    ats_err "scan-skills: no files to scan."
    exit 2
  fi

  # known skill names -> temp file
  local names_file jsonl
  names_file="$(mktemp "${TMPDIR:-/tmp}/ats-scan-names.XXXXXX")"
  jsonl="$(mktemp "${TMPDIR:-/tmp}/ats-scan-findings.XXXXXX")"
  # shellcheck disable=SC2064
  trap "rm -f '$names_file' '$jsonl'" EXIT
  known_skill_names > "$names_file"

  local ignore_arg="$IGNORE_FILE"
  [[ -f "$ignore_arg" ]] || ignore_arg="/dev/null"

  run_scan "$ignore_arg" "$names_file" "${files[@]}" > "$jsonl"

  local n_high
  n_high="$(grep -c '"severity": "HIGH"' "$jsonl" 2>/dev/null || true)"
  : "${n_high:=0}"

  case "$MODE" in
    json)  emit_json "$jsonl" ;;
    text)  emit_text "$jsonl" ;;
    check)
      emit_text "$jsonl"
      if (( n_high > 0 )); then exit 1; fi
      exit 0
      ;;
  esac
  exit 0
}

main "$@"
