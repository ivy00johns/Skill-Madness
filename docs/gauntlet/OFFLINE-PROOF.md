# Gauntlet II v2 — offline repair proof

## Result

**Recording and grading semantics are proven with offline fixtures. Live skill/model behavior is not proven.** Zero model calls, merges, commits, deployments, global installs, hook activation or global sync were performed.

This repair is delivered in the current isolated worktree, starting at `51106e1762205ab5a0b06b0d77ad8c69e8e33aba`. The original Gauntlet package was present only on the audit branch, so its documents/trap scripts were brought into this worktree without merging that branch. Recording/grading are repaired here; unrelated universality/sync/product changes were not imported.

## What changed

- [record.py](../../scripts/gauntlet/record.py) freezes a catalog-bound run manifest and records complete observer captures; it can import already recorded Freebuff/Hermes streams without launching either host.
- [pipeline.py](../../scripts/gauntlet/pipeline.py) and [adapters.py](../../scripts/gauntlet/adapters.py) correlate call IDs/results, verify returned candidate bytes and replay retained evidence at grading time.
- [trace-merge.py](../../scripts/gauntlet/trace-merge.py) and [score.py](../../scripts/gauntlet/score.py) reject legacy name counts and distinguish automatic selection, explicit invocation and role dispatch.
- [trace-schema.json](trace-schema.json) now defines v2 evidence receipts, not narrative success claims.
- [preflight.py](../../scripts/gauntlet/preflight.py) proves the actual CLI chain and its rejection path offline before any proposed spending.
- [trap-verify.sh](../../scripts/gauntlet/trap-verify.sh) normalizes relative targets and reports failed/unavailable QA checker execution as BLOCKED, not a false verdict.
- [The recording guide](README.md) and [build brief](GAUNTLET-II.md) require a real-host recording smoke before an expensive build, rather than assuming a strict hook profile records everything.

## Verified final checks

| Check | Result |
|---|---|
| Offline regression suite | **33 tests passed**, no skips |
| Repository interface | `bash tests/run-all.sh --filter 'gauntlet:'` passes the new Bats gate, which runs the offline suite |
| Full mandatory-catalog fixture campaign | **450/450 cases**: 75 mandatory skills × 3 positive + 3 negative trials |
| Invocation modes | 48 automatic, 17 explicit, 10 dispatched skills, graded separately |
| Optional row | Payload CMS explicitly excluded, not a silently missed/passed skill |
| Negative controls | 225/225 synthetic no-retrieval controls pass |
| Entirely blocked v2 campaign | All 450 blocked cases remain blocked; strict merge and score both exit **1** |
| Old all-blocked narrative trace | Both grader and merge reject it with exit **2**; cannot pass as v2 evidence |
| Prior Bazaar II narrative trace | Both grader and merge reject it with exit **2**; no retrospective retrieval certification |
| Invalid/missing evidence | Rejected: malformed JSON, duplicate keys/cases, unknown skills, missing results/controls, altered counters, stale inputs, mixed cells/models/revisions/tool surfaces |
| Forced/manual reads | Cannot pass an automatic-selection case |
| Native stream fixture import | Freebuff SDK/Hermes calls correlate with exact result content; raw events are retained and replayed; wrong model/host/query and contentless streams reject |
| Relative trap target | Same T8 verdict as absolute target in a controlled fixture; checker exit 127 yields BLOCKED |
| Syntax/schema | Python compilation, Bash syntax and mandatory JSON Schema validation pass |
| Markdown | All delivered Gauntlet Markdown linted with the repository config |

The full-catalog preflight reports **FIXTURE_PASS**, `live_model_capability: NOT_ESTABLISHED` and `live_run_ready: false`. It does not claim that 75 real skills actually fired. Resource hashes bind source inputs; this is not a live installed-host resource test.

The first full-catalog preflight exposed an optional-selection re-derivation bug: default optional exclusions changed when the manifest was reloaded. The fix preserves default-versus-explicit selection, and all affected tests plus the full CLI preflight were rerun afterward. Earlier diagnostic runs are retained, not presented as final passes.

## Evidence

- [Final offline preflight receipt](evidence/preflight.json): six actual CLI checks with expected/actual exit statuses, manifest hash, artifact hashes and zero-model-call declaration.
- [Fixture coverage JSON](evidence/report.json): separate modes, controls, exclusions and fixture-only verdict.
- [All-blocked grading JSON](evidence/blocked-report.json): FAIL, 450 blocked outcomes, zero proven skills.
- [Legacy rejection receipt](evidence/legacy-replay.json): four CLI replays, all exit 2.
- [Final unittest log](evidence/gauntlet-pipeline-tests.log)
- [Repository Bats gate log](evidence/gauntlet-bats.log)

Raw fixture events, receipts, manifests and complete logs are retained at `.workspaces/gauntlet-pipeline/delivery-proof/`. Earlier checkpoints are retained under the same ignored workspace root. Durable evidence above is saved outside ignored directories; no secrets are present.

## Reproduce without a model call

Follow [README.md](README.md) for the local Python environment, then:

```bash
python tests/gauntlet/test_pipeline.py
bash tests/run-all.sh --filter 'gauntlet:'
python scripts/gauntlet/preflight.py \
  --revision "$(git rev-parse HEAD)" \
  --out-dir .workspaces/gauntlet-pipeline/new-offline-proof
```

Use a new output directory. Outputs never overwrite an existing manifest/receipt/report. Preserve the command's exit status; piping through a display command is not acceptance.

## Boundaries still requiring proof

1. **Actual host observer wiring.** Nothing was installed globally. Imported engine streams must include real dispatched query/mode, model/tool surface and candidate content. The old Claude coarse hook is not sufficient and is rejected. A trusted Claude observer has not been implemented/live-tested here; do not start a paid build assuming it exists.
2. **Source authenticity.** Replayed hashes detect changed receipts and source drift, not an observer deliberately fabricating source events. Actual provenance must come from a trusted host capture outside the worker's self-report.
3. **Live positive/negative selection.** No live Claude, Freebuff, Hermes, GPT, Gemini or other model was queried. The public matrix is calibration data, not an unseen representative holdout.
4. **Efficacy, product safety and installed-host resources.** These remain UNVERIFIED and require separate checks. Trap outputs do not replace selection receipts; selection receipts do not certify Bazaar II security or cross-model equivalence.
5. **Integration onto PR #82.** Eligibility in this proof comes from the current 76-skill source tree, not the audit branch's broader portable metadata. Re-prepare and rerun offline preflight on the exact future integrated tree; do not reuse a stale manifest. No merge-readiness/global-sync approval is implied.
