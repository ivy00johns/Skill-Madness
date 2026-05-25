#!/usr/bin/env bats
# 04-lint-hooks.bats — scripts/lint-hooks.sh against the shipped tree + a
# deliberately-broken temp tree.
#
# Contract: contracts/hooks/hooks-layer.md §5 + §6.
# Cases:
#   - passes on the shipped hooks/ tree (exit 0)
#   - fails when a manifest script is missing (temp tree, exit 1)
#   - fails when a profile is invalid (temp tree, exit 1)

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  export LINT="$REPO_ROOT/scripts/lint-hooks.sh"
  export HOOKS="$REPO_ROOT/hooks"
}

setup() {
  export TMPTREE
  TMPTREE="$(mktemp -d /tmp/ats-lint-hooks.XXXXXX)"
}

teardown() {
  rm -rf "$TMPTREE"
}

@test "lint-hooks: passes on the shipped tree (exit 0)" {
  run bash "$LINT"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "PASSED"
}

@test "lint-hooks: explicit hooks dir arg also passes" {
  run bash "$LINT" "$HOOKS"
  [ "$status" -eq 0 ]
}

@test "lint-hooks: fails when a manifest script is missing (exit 1)" {
  # Copy the real tree, then delete one referenced script.
  cp -r "$HOOKS"/. "$TMPTREE"/
  rm -f "$TMPTREE/scripts/qa-gate.sh"
  run bash "$LINT" "$TMPTREE"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "does not exist"
}

@test "lint-hooks: fails when a hook script is not executable (exit 1)" {
  cp -r "$HOOKS"/. "$TMPTREE"/
  chmod -x "$TMPTREE/scripts/post-edit-format.sh"
  run bash "$LINT" "$TMPTREE"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "not executable"
}

@test "lint-hooks: fails when manifest has an invalid profile (exit 1)" {
  cp -r "$HOOKS"/. "$TMPTREE"/
  python3 - "$TMPTREE/hooks.manifest.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["hooks"][0]["profiles"] = ["minimal", "bogus-profile"]
json.dump(d, open(p, "w"), indent=2)
PY
  run bash "$LINT" "$TMPTREE"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "invalid profile"
}

@test "lint-hooks: fails when hooks.manifest.json is unparseable (exit 1)" {
  cp -r "$HOOKS"/. "$TMPTREE"/
  printf '{ not json ' > "$TMPTREE/hooks.manifest.json"
  run bash "$LINT" "$TMPTREE"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "does not parse"
}

@test "lint-hooks: fails when a script omits set -euo pipefail (exit 1)" {
  cp -r "$HOOKS"/. "$TMPTREE"/
  # Replace the script with a shebang-only file (missing set -euo + term.sh).
  printf '#!/usr/bin/env bash\necho hi\n' > "$TMPTREE/scripts/pre-commit-lint.sh"
  chmod +x "$TMPTREE/scripts/pre-commit-lint.sh"
  run bash "$LINT" "$TMPTREE"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "set -euo pipefail"
}
