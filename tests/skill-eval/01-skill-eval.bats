#!/usr/bin/env bats
# 01-skill-eval.bats — skills/meta/skill-eval/scripts/skill_eval.py free modes.
#
# Builds a throwaway skill with a skill-creator evals.json under $BATS_TEST_TMPDIR
# and exercises convert / lint / report / run-argument checks. Nothing here calls
# `claude plugin eval` — the only paid mode is `run`, and it is tested only for
# refusing to start without a cap.
#
# Cases:
#   - convert writes one case dir per eval + a fired check + a judge rubric
#   - convert never overwrites an existing case dir
#   - lint fails a suite with no must-not-fire case, passes once one is added
#   - lint fails a ~/ path and a runs below the floor
#   - convert notes sandbox paths and file-writing skills
#   - report reads an aggregate-result.json (schemaVersion 1)
#   - run refuses without --max-cost-usd

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  SE="$REPO_ROOT/skills/meta/skill-eval/scripts/skill_eval.py"
  SK="$BATS_TEST_TMPDIR/demo-skill"
  mkdir -p "$SK/evals"
  printf -- '---\nname: demo-skill\nversion: 0.1.0\ndescription: Demo.\n---\n\n# demo\n' > "$SK/SKILL.md"
  cat > "$SK/evals/evals.json" <<'EOF'
{"skill_name": "demo-skill", "evals": [
  {"id": 1, "name": "draw-it", "prompt": "draw the pipeline as a flowchart",
   "expected_output": "a mermaid flowchart", "assertions": [{"text": "has a mermaid block"}]},
  {"id": 2, "prompt": "deep dive on ~/code/thing and write the docs",
   "expected_output": "00-INDEX.md and 01-overview.md", "files": []}
]}
EOF
}

@test "convert writes one case per eval with a fired check and a rubric" {
  run python3 "$SE" convert "$SK"
  [ "$status" -eq 0 ]
  [ -f "$SK/evals/01-draw-it/prompt.md" ]
  grep -q '^type: tool_used' "$SK/evals/01-draw-it/graders/fires.md"
  grep -q 'has a mermaid block' "$SK/evals/01-draw-it/graders/outcome.md"
  grep -q '^runs: 3' "$SK/evals/01-draw-it/prompt.md"
}

@test "convert never overwrites an existing case dir" {
  python3 "$SE" convert "$SK"
  echo "hand-edited" > "$SK/evals/01-draw-it/graders/outcome.md"
  run python3 "$SE" convert "$SK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"kept"* ]]
  [ "$(cat "$SK/evals/01-draw-it/graders/outcome.md")" = "hand-edited" ]
}

@test "lint requires a must-not-fire case" {
  python3 "$SE" convert "$SK"
  rm -rf "$SK"/evals/02-*
  run python3 "$SE" lint "$SK"
  [ "$status" -eq 1 ]
  [[ "$output" == *"no must-not-fire case"* ]]
  python3 "$SE" convert "$SK" --negative "what time is it in Tokyo"
  rm -rf "$SK"/evals/02-*  # convert re-creates it; its ~/ path would fail lint
  run python3 "$SE" lint "$SK"
  [ "$status" -eq 0 ]
  grep -q '^arm: both' "$SK"/evals/neg-01-*/graders/not-fired.md
}

@test "lint fails a ~/ path and runs below the floor" {
  python3 "$SE" convert "$SK" --negative "what time is it in Tokyo"
  sed -i.bak 's/^runs: 3/runs: 1/' "$SK/evals/01-draw-it/prompt.md"
  run python3 "$SE" lint "$SK"
  [ "$status" -eq 1 ]
  [[ "$output" == *"absolute or ~/ path"* ]]
  [[ "$output" == *"runs: 1"* ]]
}

@test "convert notes sandbox paths and file-writing skills" {
  run python3 "$SE" convert "$SK"
  [[ "$output" == *"02-"*"absolute or ~/ path"* ]]
  [[ "$output" == *"02-"*"writes files"* ]]
  [[ "$output" != *"01-draw-it: looks like the skill writes files"* ]]
}

@test "report reads aggregate-result.json schemaVersion 1" {
  mkdir -p "$SK/evals/results/2026-01-01T00-00-00Z"
  cat > "$SK/evals/results/2026-01-01T00-00-00Z/aggregate-result.json" <<'EOF'
{"schemaVersion": 1, "costUsd": 0.004, "partial": false,
 "suite": {"plugins": [{"name": "demo-skill"}]},
 "cases": [{"name": "neg-01", "arms": {"with": [{"error": null}], "without": [{"error": null}]},
            "aggregates": {"score": 1, "scoreWithout": 1, "delta": 0}}],
 "aggregates": {"casesTotal": 1, "casesPassed": 1, "meanDelta": 0}}
EOF
  run python3 "$SE" report "$SK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"1/1 cases passed"* ]]
  [[ "$output" == *"over 2 session(s)"* ]]
}

@test "run refuses to start without --max-cost-usd" {
  run python3 "$SE" run "$SK"
  [ "$status" -eq 2 ]
  [[ "$output" == *"--max-cost-usd"* ]]
}
