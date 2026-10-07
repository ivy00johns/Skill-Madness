# Gauntlet II recording and grading

The v2 pipeline repairs the original package's name-counting grader and incomplete recorder. It is **offline tooling**: none of these commands calls a model, activates hooks, installs skills, deploys, or syncs globals.

**A fixture PASS proves the pipeline, not the models.** The existing Bazaar II narrative trace cannot be promoted into retrieval evidence. Keep it as a legacy product-run artifact.

## Before spending anything

Use a project-local Python environment with `pyyaml` and `jsonschema`; both are already used by the repository's lint/schema tooling. Do not rely on a user-site installation that disappears under isolated HOME.

```bash
uv venv .workspaces/gauntlet-pipeline/venv
uv pip install --python .workspaces/gauntlet-pipeline/venv/bin/python pyyaml jsonschema
.workspaces/gauntlet-pipeline/venv/bin/python scripts/gauntlet/preflight.py \
  --revision "$(git rev-parse HEAD)" \
  --out-dir .workspaces/gauntlet-pipeline/preflight-1
```

The output directory must be new and inside this workspace. Preflight exercises the real record → merge → score interfaces with three positive and three negative fixtures per eligible mandatory skill. It also records an entirely blocked campaign and verifies both strict merge and scoring exit **1**, not 0. It writes hashes, logs, a Markdown report and a JSON report. `preflight.json` records `model_calls: 0`, `OFFLINE_PIPELINE_PASS` and `live_run_ready: false`.

Before **any** real build/campaign, separately verify a bounded, owner-approved host recording smoke: one positive, one genuine no-retrieval negative and one refusal/error. Check the observer, complete event stream, candidate bytes and exact exit status. If the host cannot record them, **stop before building or spending**. Offline preflight never supplies authorization for paid calls.

## Frozen run manifest

```bash
python scripts/gauntlet/record.py prepare \
  --repo "$PWD" --matrix docs/gauntlet/coverage-matrix.md \
  --run-id run-1 --cell-id claude-cell-1 \
  --host claude-code --model OBSERVED_MODEL_ID \
  --revision "$(git rev-parse HEAD)" \
  --evidence-kind host-capture --trials 3 \
  --out .workspaces/gauntlet-pipeline/run-1.json
```

`prepare` does not run the cases. It freezes:

- Exact catalog, skill bodies, resource contents and executable modes.
- Coverage matrix and recording/grading script/schema hashes.
- Run, cell, observed host/model, revision and evidence kind.
- Positive/negative case IDs, queries, trials and invocation modes.
- Explicit optional/host-ineligible exclusions.

Catalog/matrix mismatch, duplicate names, unknown selections, symlinks, malformed frontmatter and empty plans block preparation. Defaults select the full catalog; `--skill NAME` selects a clearly labelled subset. The optional Payload row is excluded unless selected explicitly. `requires_claude_code: true` entries are excluded from non-Claude plans; no runtime capability is invented. When integrating onto the universality PR, prepare from **that exact tree** so its changed portability metadata determines eligibility.

Model-disabled role skills use **dispatch**, other model-disabled skills use **explicit**, and model-invocable skills use **automatic**. Positive cases are graded against their own mode. Negative controls test automatic non-selection; a host refusal is **blocked**, never a passing negative. No skills are renamed or made auto-invocable to improve the metric.

## Observer capture contract

One JSONL envelope per case contains `binding`, `manifest_sha256`, `case_id` and `events`. Bindings come from the frozen manifest; the observer must use the actual recorded host/model, not guessed labels. The case is isolated and complete through its terminal event.

```json
{
  "binding": {
    "run_id": "run-1",
    "cell_id": "claude-cell-1",
    "host": "claude-code",
    "model": "OBSERVED_MODEL_ID",
    "revision": "FULL_40_CHARACTER_GIT_SHA",
    "evidence_kind": "host-capture"
  },
  "manifest_sha256": "CANONICAL_MANIFEST_SHA256",
  "case_id": "madness:positive:1",
  "events": [
    {"type": "init", "query": "EXACT_PLANNED_QUERY", "mode": "automatic", "tools": ["skill"]},
    {"type": "tool_call", "call_id": "c1", "tool": "skill", "skill": "madness", "origin": "model"},
    {"type": "tool_result", "call_id": "c1", "tool": "skill", "skill": "madness", "status": "success", "content": "EXACT_RETRIEVED_SKILL_CONTENT"},
    {"type": "terminal", "status": "completed"}
  ]
}
```

The strings above are placeholders, **not usable evidence**. Hashing uses UTF-8 JSON with sorted keys and compact separators (the `json_hash` helper). The CLI-generated manifest defines the exact queries and hashes; do not type guessed values. Full SKILL content or its exact body is required in a successful result. A name, changelog, prose claim or source-artifact path is not enough.

- `skill` + origin `model` proves automatic selection only.
- `skill` + origin `user` proves explicit invocation only.
- `role_load` + origin `orchestrator` proves authorized dispatch loading only. The trusted observer must obtain this from an approved role dispatch, not reinterpret a failed autonomous call.
- `read_file` is preserved as a direct read, never an automatic-selection pass.
- A completed, tool-capable case with no target retrieval can pass a negative control.
- Refusal, error, timeout, missing required tool, unfinished or uncorrelated calls do not pass negative controls.

### Recorded engine stream import

For **already recorded** Freebuff SDK/Hermes JSONL (no engine launch):

```bash
python scripts/gauntlet/record.py import-host recorded-sdk-events.jsonl \
  --protocol freebuff-sdk --case-id madness:positive:1 \
  --manifest .workspaces/gauntlet-pipeline/run-1.json \
  --out .workspaces/gauntlet-pipeline/case-1-receipt.jsonl
```

Use `hermes-stream` for Hermes. Init must include the actual `model`, full `tools` list, dispatched `query` and invocation `mode`; terminal must report `exit_code`. An observer may attach query/mode from the actual host request, never from a guessed case label. A vanilla engine log lacking that request evidence is rejected. Skill call/results must correlate and contain the returned candidate content. Imports retain raw events and their hash; grading replays normalization. Unknown native events/tools and contentless results block instead of silently disappearing. These conservative adapters support selection-only captured streams; arbitrary execution streams need an additional tested adapter.

**Claude's coarse `skill-usage` hook is not sufficient**, nor does `ATS_HOOK_PROFILE=strict` install/activate hooks. It records unknown outcomes without candidate bytes or completed negative cases. It is rejected rather than silently converted into proof. A future trusted Claude observer can emit the common envelope, but this repair does not install one or claim it has been live-tested.

## Recording, merging and grading

```bash
python scripts/gauntlet/record.py capture case-events.jsonl \
  --manifest .workspaces/gauntlet-pipeline/run-1.json \
  --out .workspaces/gauntlet-pipeline/receipts.jsonl
python scripts/gauntlet/trace-merge.py .workspaces/gauntlet-pipeline/receipts.jsonl \
  --manifest .workspaces/gauntlet-pipeline/run-1.json --strict \
  --out .workspaces/gauntlet-pipeline/merged.jsonl
python scripts/gauntlet/score.py .workspaces/gauntlet-pipeline/merged.jsonl \
  --manifest .workspaces/gauntlet-pipeline/run-1.json \
  --out .workspaces/gauntlet-pipeline/report.md \
  --json-out .workspaces/gauntlet-pipeline/report.json
```

All output files must be new. The manifest freezes inputs; edits require a **new run/checkpoint**, not a quiet rewrite. Receipts retain their observer capture; scoring replays correlation/candidate hashes and rejects altered derived counters. Mixed cells/models/revisions/tool surfaces, duplicate cases, missing controls, stale resources, malformed JSON and legacy narrative/coarse events cannot certify coverage.

| Exit | Meaning |
|---|---|
| 0 | Recording succeeded, or planned-case grading passed within its labelled scope |
| 1 | Score/strict merge has missing, failed, blocked/error cases or too few live trials |
| 2 | Invalid/unreadable/stale/legacy evidence or unavailable parser; no acceptance |

Non-strict merge may write a validated but incomplete trace with exit 0; it always emits the failing summary to stderr. **Only strict merge and score are acceptance gates.** Recording exit 0 never means the campaign passed.

Reports separate automatic/explicit/dispatch positive coverage, negative-control outcomes, exclusions, scope and cell identity. Offline outputs say `FIXTURE_PASS` and `NOT_ESTABLISHED` for live capability. Even accepted host cases do **not** establish efficacy, safety/degradation or universal cross-model performance. Those layers remain `UNVERIFIED` and require their own experiments. Hashes catch drift, not a maliciously fabricated source capture: trusted observer provenance remains a boundary.

## Tests and package scope

```bash
python tests/gauntlet/test_pipeline.py
bash tests/run-all.sh --filter 'gauntlet:'
```

The offline unittest suite is wired into the repository's recursive Bats gate. See [OFFLINE-PROOF.md](OFFLINE-PROOF.md) for delivered verification and the prior false-pass replay.

[GAUNTLET-II.md](GAUNTLET-II.md) is the product/integration brief; [coverage-matrix.md](coverage-matrix.md) supplies planned cases; [scoring-rubric.md](scoring-rubric.md) defines separate evaluation layers. [trace-schema.json](trace-schema.json) defines v2 receipts. The trap verifier remains a separate deterministic/behavioral layer; its PASS/BLOCKED rows are never silently treated as selection proof.
