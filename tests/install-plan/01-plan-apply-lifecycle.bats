#!/usr/bin/env bats
# 01-plan-apply-lifecycle.bats — Plan/apply install + install-state + profiles.
#
# Covers contract P1-B Tests section:
#   - plan resolution (action create into empty root; sources orchestrator-only
#     for minimal; every op has sha256)
#   - plan idempotent action: identical dest -> skip; differing dest -> overwrite
#   - apply creates files + writes parseable state whose hashes match; re-apply no-op
#   - state list reflects applied files
#   - drift: pristine exit 0; mutated file -> drift + exit 1
#   - uninstall removes recorded files + clears state
#   - repair restores a mutated file to source hash
#   - profile resolution: git -> git-only; full -> all categories; counts match disk
#
# All operations run under a temp --root; the real ~/.claude is never touched.

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  export SCRIPTS="$REPO_ROOT/scripts"

  # Build a fresh integrations/ source tree ONCE into a temp dir (never in-repo).
  export INTEG
  INTEG="$(mktemp -d "${TMPDIR:-/tmp}/ats-pa-integ.XXXXXX")"
  bash "$SCRIPTS/convert.sh" --out "$INTEG" >/dev/null 2>&1
}

teardown_file() {
  rm -rf "$INTEG"
}

setup() {
  export ROOT
  ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ats-pa-root.XXXXXX")"
}

teardown() {
  rm -rf "$ROOT"
}

plan() {
  bash "$SCRIPTS/install-plan.sh" --integrations "$INTEG" --root "$ROOT" "$@"
}

# ---------------------------------------------------------------------------
# Plan resolution
# ---------------------------------------------------------------------------

@test "plan: minimal/claude-code emits parseable JSON" {
  run plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  [ "$status" -eq 0 ]
  run python3 -c "import json,sys; json.load(open('$ROOT/plan.json'))"
  [ "$status" -eq 0 ]
}

@test "plan: minimal references only orchestrator-category sources" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan.json'))['operations']
cats={o['source'].split('/claude-code/')[1].split('/')[0] for o in ops}
assert cats=={'orchestrator'}, cats
assert len(ops)>0
"
  [ "$status" -eq 0 ]
}

@test "plan: every operation has a non-empty sha256" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan.json'))['operations']
assert all(len(o['sha256'])==64 for o in ops)
"
  [ "$status" -eq 0 ]
}

@test "plan: action=create into an empty root" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan.json'))['operations']
assert all(o['action']=='create' for o in ops)
"
  [ "$status" -eq 0 ]
}

@test "plan: pre-placed identical dest -> action=skip" {
  # First plan to learn a dest+source, then pre-place identical content.
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  local dest src
  dest="$(python3 -c "import json;print(json.load(open('$ROOT/plan.json'))['operations'][0]['dest'])")"
  src="$(python3 -c "import json;print(json.load(open('$ROOT/plan.json'))['operations'][0]['source'])")"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  plan --profile minimal --tool claude-code --out "$ROOT/plan2.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan2.json'))['operations']
m=[o for o in ops if o['dest']=='$dest'][0]
assert m['action']=='skip', m['action']
"
  [ "$status" -eq 0 ]
}

@test "plan: pre-placed differing dest -> action=overwrite" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  local dest
  dest="$(python3 -c "import json;print(json.load(open('$ROOT/plan.json'))['operations'][0]['dest'])")"
  mkdir -p "$(dirname "$dest")"
  printf 'DIFFERENT CONTENT\n' > "$dest"
  plan --profile minimal --tool claude-code --out "$ROOT/plan2.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan2.json'))['operations']
m=[o for o in ops if o['dest']=='$dest'][0]
assert m['action']=='overwrite', m['action']
"
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Apply + state
# ---------------------------------------------------------------------------

@test "apply: creates files and writes a parseable state with matching hashes" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  run bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT"
  [ "$status" -eq 0 ]
  [ -f "$ROOT/.claude/.ats-install-state.json" ]
  run python3 -c "
import json,hashlib,os
st=json.load(open('$ROOT/.claude/.ats-install-state.json'))
assert st['files']
for fr in st['files']:
    h=hashlib.sha256(open(fr['dest'],'rb').read()).hexdigest()
    assert h==fr['sha256'], fr['dest']
"
  [ "$status" -eq 0 ]
}

@test "apply: re-applying an unchanged plan is a no-op (all skip)" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  run bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "created=0"
  echo "$output" | grep -qE "skipped=[1-9]"
}

@test "apply --dry-run: writes no files and no state" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  run bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" --dry-run
  [ "$status" -eq 0 ]
  [ ! -d "$ROOT/.claude/skills" ]
  [ ! -f "$ROOT/.claude/.ats-install-state.json" ]
}

# ---------------------------------------------------------------------------
# list / drift / uninstall / repair
# ---------------------------------------------------------------------------

@test "state list: reflects applied files" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  run bash "$SCRIPTS/install-state.sh" list --root "$ROOT"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "profile:    minimal"
  echo "$output" | grep -q "orchestrator"
}

@test "drift: pristine install reports no drift, exit 0" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  run bash "$SCRIPTS/install-state.sh" drift --root "$ROOT"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "pristine"
}

@test "drift: mutated file is reported and exits 1" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  local f
  f="$(python3 -c "import json;print(json.load(open('$ROOT/.claude/.ats-install-state.json'))['files'][0]['dest'])")"
  printf 'TAMPER\n' >> "$f"
  run bash "$SCRIPTS/install-state.sh" drift --root "$ROOT"
  [ "$status" -eq 1 ]
  echo "$output" | grep -q "changed:"
}

@test "repair: restores a mutated file to the source hash; drift clean after" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  local f
  f="$(python3 -c "import json;print(json.load(open('$ROOT/.claude/.ats-install-state.json'))['files'][0]['dest'])")"
  printf 'TAMPER\n' >> "$f"
  run bash "$SCRIPTS/install-state.sh" repair --root "$ROOT"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "repaired:"
  run bash "$SCRIPTS/install-state.sh" drift --root "$ROOT"
  [ "$status" -eq 0 ]
}

@test "uninstall: removes recorded files and clears state" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  run bash "$SCRIPTS/install-state.sh" uninstall --root "$ROOT"
  [ "$status" -eq 0 ]
  [ ! -f "$ROOT/.claude/.ats-install-state.json" ]
  run bash -c "find '$ROOT/.claude/skills' -type f 2>/dev/null | wc -l | tr -d ' '"
  [ "$output" = "0" ]
}

@test "uninstall --dry-run: leaves files and state intact" {
  plan --profile minimal --tool claude-code --out "$ROOT/plan.json"
  bash "$SCRIPTS/install-apply.sh" --plan "$ROOT/plan.json" --root "$ROOT" >/dev/null 2>&1
  run bash "$SCRIPTS/install-state.sh" uninstall --root "$ROOT" --dry-run
  [ "$status" -eq 0 ]
  [ -f "$ROOT/.claude/.ats-install-state.json" ]
}

# ---------------------------------------------------------------------------
# Profile resolution
# ---------------------------------------------------------------------------

@test "profile git: selects only git-category skills" {
  plan --profile git --tool claude-code --out "$ROOT/plan.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan.json'))['operations']
cats={o['source'].split('/claude-code/')[1].split('/')[0] for o in ops}
assert cats=={'git'}, cats
"
  [ "$status" -eq 0 ]
}

@test "profile full: selects all six categories" {
  plan --profile full --tool claude-code --out "$ROOT/plan.json"
  run python3 -c "
import json
ops=json.load(open('$ROOT/plan.json'))['operations']
cats={o['source'].split('/claude-code/')[1].split('/')[0] for o in ops}
assert cats=={'orchestrator','roles','contracts','meta','git','workflows'}, cats
assert 'archive' not in cats
"
  [ "$status" -eq 0 ]
}

@test "profile resolution: per-category skill counts match disk (catalog rule)" {
  plan --profile full --tool claude-code --out "$ROOT/plan.json"
  # Disk truth: count skill dirs per category, excluding archive/in-progress.
  local disk
  disk="$(find "$REPO_ROOT/skills" -name SKILL.md -type f \
            | grep -v '/archive/' | grep -v '/in-progress/' \
            | while IFS= read -r f; do
                d="$(dirname "$f")"; slug="$(basename "$d")"
                parent="$(basename "$(dirname "$d")")"
                if [ "$parent" = "skills" ]; then echo "$slug"; else echo "$parent"; fi
              done | sort | uniq -c | awk '{print $2"="$1}' | sort)"
  run python3 -c "
import json
from collections import Counter
ops=json.load(open('$ROOT/plan.json'))['operations']
skills={(o['source'].split('/claude-code/')[1].split('/')[0],
         o['source'].split('/claude-code/')[1].split('/')[1]) for o in ops}
c=Counter(cat for cat,_ in skills)
print('\n'.join('%s=%d'%(k,v) for k,v in sorted(c.items())))
"
  [ "$status" -eq 0 ]
  # Compare the two sorted "cat=N" lists.
  [ "$(printf '%s\n' "$disk")" = "$(printf '%s\n' "$output")" ]
}

@test "unknown profile exits 2" {
  run plan --profile no-such-profile --tool claude-code
  [ "$status" -eq 2 ]
}

@test "unknown tool exits 2" {
  run plan --profile minimal --tool no-such-tool
  [ "$status" -eq 2 ]
}

@test "missing --tool exits 2" {
  run plan --profile minimal
  [ "$status" -eq 2 ]
}
