#!/usr/bin/env bats
# 01-scanner.bats — class-extraction-guard scanner regressions.
#
# Covers the three bugs fixed after the 2026-07 offline-window review:
#   - --staged joined git's TOPLEVEL-relative paths onto --root, so a
#     subdirectory --root silently scanned nothing (false green);
#   - --staged never applied ignoreDirs (dist/, vendor/ were scanned);
#   - line numbers, after the O(matches × file-size) line lookup was replaced
#     with a precomputed newline index.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  GUARD="$REPO_ROOT/skills/workflows/class-extraction-guard/scripts/check_class_extraction.py"
  command -v git >/dev/null 2>&1 || skip "git not available"
  command -v python3 >/dev/null 2>&1 || skip "python3 not available"
  FIX="$(mktemp -d "${TMPDIR:-/tmp}/ats-ceg-test.XXXXXX")"
  git -C "$FIX" init -q
  git -C "$FIX" config user.email test@test.invalid
  git -C "$FIX" config user.name test
}

teardown() {
  rm -rf "$FIX"
}

# _combo_file <path> — a file carrying the same 4-utility combo at 3 call-sites
# (>= minUtilities 4, >= minRepeats 3, so repeated-class-string fires).
_combo_file() {
  mkdir -p "$(dirname "$1")"
  cat > "$1" <<'EOF'
export const A = () => <div className="flex items-center gap-2 text-sm">a</div>;
export const B = () => <div className="flex items-center gap-2 text-sm">b</div>;
export const C = () => <div className="flex items-center gap-2 text-sm">c</div>;
EOF
}

@test "scanner: walk mode reports the repeated combo with correct line numbers" {
  _combo_file "$FIX/web/src/E.tsx"
  run python3 "$GUARD" --root "$FIX" --json
  [ "$status" -eq 0 ]   # default severity is warning -> exit 0
  echo "$output" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['summary']['warnings'] == 1, d
f = d['findings'][0]
assert f['line'] == 1, f
assert f['count'] == 3, f
"
}

@test "scanner: --staged with a subdirectory --root scans the staged file (toplevel path-join regression)" {
  _combo_file "$FIX/web/src/E.tsx"
  git -C "$FIX" add web/src/E.tsx
  run python3 "$GUARD" --root "$FIX/web" --staged --json
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['summary']['files_scanned'] == 1, d
assert d['summary']['warnings'] == 1, d
"
}

@test "scanner: --staged with a subdirectory --root excludes staged files outside it" {
  _combo_file "$FIX/web/src/E.tsx"
  _combo_file "$FIX/api/ui/F.tsx"
  git -C "$FIX" add .
  run python3 "$GUARD" --root "$FIX/web" --staged --json
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['summary']['files_scanned'] == 1, d
"
}

@test "scanner: --staged applies ignoreDirs (dist/ staged is not scanned)" {
  _combo_file "$FIX/dist/bundle.tsx"
  git -C "$FIX" add -f dist/bundle.tsx
  run python3 "$GUARD" --root "$FIX" --staged --json
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['summary']['files_scanned'] == 0, d
assert d['summary']['warnings'] == 0, d
"
}
