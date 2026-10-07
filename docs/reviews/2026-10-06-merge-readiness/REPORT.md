# October 6 merge-readiness audit

## Verdict

**HOLD: do not merge PR #79 and PR #82 together, and do not sync globals yet.**

The library's deterministic changes are substantially working. Bazaar II is a real, working local demo. Neither establishes that every skill triggers correctly, that Claude Code's native orchestration still works end to end, or that other models behave correctly. The existing scorer can falsely certify completely blocked retrievals. The combined PRs conflict, and PR #79's sync path can delete unowned local work.

This is an independent, **offline-first audit**, not a repair or a live-model certification. The owner selected offline audit first. No model batch, deployment, commit, push, merge, permission change, or global sync was performed. Product probes created only fresh, clearly named simulated audit accounts/auctions; no existing records were edited or deleted.

## Scope and exact revisions

Audit conducted October 6, 2026, local time. The work under review was authored October 5 local time, with CI running October 6 UTC.

| Item | Revision | State | Recommendation |
|---|---|---|---|
| Main / this thread's starting branch | `51106e1` | Latest merged changes September 24 | Baseline, not today's candidate |
| [PR #82](https://github.com/ivy00johns/Skill-Madness/pull/82), universality audit/fix wave/Gauntlet package | `19b48b1` | Open; 169 changed files, much of the volume captured evidence | Hold for evidence-harness, macOS and integration repairs |
| [PR #79](https://github.com/ivy00johns/Skill-Madness/pull/79), Cloudflare skill/all-host sync | `d06cc28` | Open; all historical CI checks green | Rebase onto the safe ownership-aware sync implementation; do not preserve destructive old sync code |
| PRs #80 and #81 | Gauntlet package | Closed, not merged | Package is already in #82; do not try to merge duplicate PRs |
| Freebuff trigger-eval follow-up | `36c5390`, includes `0892ee6` | Local branch, not in #82 | Offline tests promising; actual SDK-engine check skipped; not live trigger proof |
| Role-loading follow-up | `337f2cf` | Local branch, not in #82 | Include after confirming host permission semantics; distinguishes dispatched role loading from auto-triggering |
| FreeLLMAPI key-discovery follow-up | `39d0dea` | Local branch, not in #82 | Useful, but narrow credential discovery to authorized paths; do not indiscriminately source sibling environment files |
| Bazaar II product | `150f37b` | Separate clean repository | Functional demo, not complete Gauntlet acceptance |
| Parked orchestration/walkthrough work | `44eb381` | Explicit WIP branch | Keep separate; not implicitly approved by this audit |

The built product is at `/Users/johns/Projects/Random/Gauntlet-II/.workspaces/gauntlet-ii`. Its original reports and trace were read without changing them. Tests/builds and generated browser reports were run from a local audit clone.

The older `e1ab2a96-7570-4f3f-8333-87a7bf914145` worktree contains **127 dirty/untracked files** compared here: **96 byte-identical to #82, 31 different, zero absent from #82**. The differences include pre-follow-up descriptions, sequential execution, capability defaults and trap verification. They are not a new missing patch set by default. Preserve that worktree until its owner confirms reconciliation; do not reset or bulk-merge it. The main project also has an untracked universal-audit proposal, left untouched.

## Acceptance questions

| Question | Answer |
|---|---|
| Was Bazaar II built? | **Yes.** Build, normal API/ledger tests and live browser paths work after contracts are built. |
| Did all 76 skills trigger? | **No such proof exists.** Only 24 active skill names occur in the 30-record trace; 52 have no record. No correlated unforced retrieval receipts exist. |
| Were negative/near-miss controls tested? | **No:** zero near-miss trace records. |
| Was the Claude Code primary cell run? | **No.** The product report explicitly says not run. |
| Are other models certified? | **No.** One Freebuff/DeepSeek run used explicit reads/manual doctrine. GPT/Gemini/other cells were not tested. |
| Do all portable exports generate correctly? | Deterministic conversion is separately checked; it is delivery evidence, not behavioral certification. |
| Can both open PRs be merged unchanged? | **No:** four combined merge conflicts, unsafe sync behavior in #79, and invalid coverage grading in #82. |
| Should globals be updated now? | **No.** First reconcile the implementation, approve the final revision, then preview/apply from the stable checkout. |

## Blocking findings

### A1 — Coverage grader accepts blocked records as successful firing (P0)

Both `scripts/gauntlet/score.py` and `trace-merge.py` derive firing from the mere presence of a `skill` field. They do not require successful retrieval, accepted proof, matched control, or a host tool-call receipt. The scorer ignores gate receipts, mixes cells, and does not implement the four-layer rubric it advertises. Malformed JSON can be skipped; a missing matrix need not fail closed.

**Reproduction:** supply one schema-valid record for each of the 76 active skills, all explicitly `outcome=blocked`, `proof=blocked`, `retrieval_proof=NOT RETRIEVED`. The scorer exits **0**, reports **76/76 fired and zero missed**; strict trace merge also exits **0**. This is a harness defect, not proof that a model cheated.

The actual product trace is schema-valid but contains skipped/blocked/failing entries and six non-skill identifiers. The existing scorer calls all 30 distinct identifiers fired, then reports only 24 as catalog skills. Artifacts such as an API source file or changelog are task-output evidence, not evidence that the corresponding skill was retrieved.

**Required repair:** separate direct invocation, role dispatch, successful unforced selection, blocked/error/no selection, and task efficacy. Validate inputs/schema/catalog; bind cell/model/revision and tool-call receipts; grade negative controls; make strict acceptance fail on blocked/error/invalid proof. Add the all-blocked negative regression before relying on any coverage percentage.

### A2 — No cross-model or Claude Code live acceptance (P0 for the requested claim)

The existing run is a single Freebuff/DeepSeek product build. It explicitly forced reads and performed work inline. That can exercise instructions, not measure automatic selection. Its host limitation must not be generalized into “Freebuff never has a Skill tool”: the new local Freebuff evaluator is specifically adding the engine's skill tool, and available host capabilities vary by version/session.

Role agents intentionally disable model invocation. Their acceptance criterion is authorized dispatch/load, not autonomous triggering. The matrix must distinguish these modes rather than treating every skill as an identical natural-language trigger candidate. Twelve concrete loops and other workflows remain Claude-only; the portable population is 52 of 76, not 76.

**Required repair:** pre-register per-host eligibility and execution mode, then run positive and near-miss cases with repeated trials on a pinned Claude Code cell and an approved second cell. Do not force-load or disclose answers in a selection test. Test task efficacy separately with comparable treatment/control. Keep paid endpoints/call/spend caps subject to owner approval.

### A3 — PR #79 and PR #82 conflict and carry different sync safety contracts (P0)

A non-mutating `git merge-tree --write-tree 19b48b1 d06cc28` returns **1** with conflicts in README, START-HERE, sync-skills/SKILL.md and sync-skills.sh. “MERGEABLE” against today's main individually does not mean both can merge cleanly in sequence.

**Reproduction of data loss:** in an isolated fake HOME, create an unowned Claude skill directory with `local-work.txt`, then run #79's link sync. It exits **0**, deletes the directory/sentinel, and replaces it with a symlink without backup or explicit replacement approval. Extra hosts avoid replacing real directories in link mode, but copy mode still uses destructive mirroring; that is not the ownership-safe #82 contract. The targeted invocation also synced the whole catalog rather than just the selected new skill.

**Required repair:** keep #82's reviewed ownership/collision/backup logic and port #79's additional host destinations and new skill onto it. Add all-host fake-HOME tests for unowned copies, foreign links, edited owned copies, selection, dry-run and rollback. Respect capability filtering on non-Claude hosts. Never resolve this conflict by restoring the old shell script wholesale.

### A4 — macOS CI dependency isolation actually fails (P1)

PR #82 has green required Ubuntu jobs but both macOS smoke runs failed in Bats test 329, the resource-delivery suite, with 17 Python failures. The repeated error is `ModuleNotFoundError: No module named 'yaml'`.

Cause: CI installs PyYAML with `pip --user`; resource-delivery tests replace HOME for isolation, so subprocess Python loses the user-site installation. Reproduced locally: Python imports yaml under real HOME, then fails under a fresh temporary HOME. The audit's project-local virtualenv preserves the dependency independently of HOME, and the full suite passes there.

**Required repair:** pin a project/CI virtualenv interpreter, or otherwise install dependencies into the interpreter's environment, while retaining fake-HOME isolation. Do not skip the tests or weaken isolation. Rerun the macOS job authoritatively.

### A5 — Final product's frozen receipt no longer matches (P1)

The recorded frozen boundary digest is `cd52d250…c9`; recomputing with #82's actual `frozen_digest()` gives `bf01e1c3…d6d`. Product history shows the frozen test files changed after the initial product commit: 74 insertions and 8 deletions across two files.

This does **not** establish malicious gate weakening; fixes and new assertions are legitimate. It does establish that the old receipt cannot certify the final edited artifact. A new versioned freeze/checkpoint and rerun are needed, preserving the old receipt/history rather than silently overwriting the criteria.

### A6 — Bazaar II security/behavior acceptance is incomplete (P1; independent of library merge)

Fresh audit fixtures reproduced:

| Boundary | Actual result |
|---|---|
| Tenant membership | New user supplies existing marketplace name, joins private tenant, reads its listing: HTTP 200 |
| Privilege grant | Public registration accepts `role=admin`; that user settles another seller's auction: HTTP 200 |
| Realtime tenant privacy | WebSocket without any token subscribes to a private auction and receives its comment |
| Auction closing | Auction with `closesAt=2020-01-01` accepts a bid today: HTTP 201 |

The original report already noticed open tenant enrollment and unenforced closing, but its green happy-path tests did not catch admin self-assignment or unauthenticated realtime leakage. Add adversarial contract/security checks and explicit product fixes before claiming marketplace acceptance. The demo uses simulated money; it must not be deployed as a secure production marketplace.

## Other confirmed findings and corrections

- **T8 relative-path bug:** absolute trap target returns 5 PASS / 7 BLOCKED (exit 2); relative target gives T8 false FAIL (exit 1). Normalize target before changing cwd; classify checker execution failure as BLOCKED. T5's verifier text still says “attended” after the one-approval policy changed.
- **CSS finding was overstated in the harvest:** stylesheet scanning is intentionally off by default. A raw hex in CSS yields zero scanned files/default clean; enabling `scanStyleSheets=true` detects it and exits 1. The issue is bootstrap/policy coverage and explaining token-definition exclusions, not an absent CSS parser.
- **Guard exclusion mismatch:** class/shared-layout collection does not honor `ignorePathContains`, unlike design-token collection. Make the sibling policy interfaces consistent and test explicit/staged/directory scans.
- **Clean-install product ordering:** `npm ci` followed immediately by typecheck or tests fails because `@bazaar/contracts` points at unbuilt dist. Build works; then typecheck and 10 tests pass. Add a contracts build/pretest dependency or clearly document/wire bootstrap order. README's one-command startup should not depend on stale build outputs.
- **Product playtest exit code:** it records failed checks but exits nonzero only for “broken” defects. A failed check with no broken-severity defect can produce exit 0. Make assertion failures part of the exit condition.
- **Product dev stack:** startup waits for Postgres but does not explicitly invoke its advertised migrations; shutdown can stop shared Compose services. Make startup reproducible on a new DB and constrain cleanup to owned processes/services.
- **Dependency audit:** 8 advisories: 5 moderate, 1 high, 2 critical. This is not a clean dependency gate. Scope production versus dev exposure, then upgrade/test rather than assuming `audit fix` no-op means safe.
- **Markdown:** #82's 88 changed Markdown files have one MD033 violation, the unescaped `<missing tool>` in sequential-execution.md. Escape/code-format it and rerun lint. The new Freebuff host reference and skill body lint clean.
- **CI coverage:** #82's main workflow runs Bats and schema/lint, but does not explicitly run the new model-eval/orchestrator pytest suites. Green CI does not cover all of the 123 offline Python tests run in this audit. Add an explicit Python suite job/step with dependencies.
- **Freebuff evaluator:** 87 tests pass, one real SDK/fake-endpoint test is skipped due to missing setup. Its skill-only tool set is disclosed and can inflate selection rates versus normal file/shell-enabled sessions. Record and verify actual SDK checkout version as well as the root-agent snapshot before capability claims; do not call mocks live-host evidence.
- **Cloudflare skill:** reusable published instructions currently assume this particular machine's login/projects and equate a request to “see” something with deploy consent. Make observed access conditional and require a deploy request; keep preview default consistent with the hello-world example's production command.

## Verification results

The #82 candidate was tested at its exact revision with a project-local Python environment. Root credentials were copied privately into the ignored candidate root for environment parity; they were not printed, used for model calls, exported into audit artifacts or staged.

| Check | Result |
|---|---|
| Skill lint | PASS, exit 0 |
| Version-drift against main | PASS, exit 0 |
| Catalog check | PASS, 76 active skills |
| Hook lint | PASS |
| Supply-chain scan | PASS for its blocking HIGH gate |
| Offline Python suites | **123 passed**, plus 2 subtests |
| Full Bats on local macOS with isolated venv | **384 passed**, exit 0, 547 seconds |
| Historical macOS CI | FAIL, dependency isolation; not waived by local pass |
| All-host converter | PASS, exit 0: 596 exports across 11 hosts (76 Claude + 10 × 52), 240 skips, 0 errors; 189 seconds |
| Absolute trap verifier | 5 PASS, 7 BLOCKED; **not a full acceptance pass** |
| Relative trap verifier | FAIL, T8 reproduced |
| Trace schema | 30/30 structurally valid; semantic retrieval proof absent |
| All-blocked scorer negative control | Harness failure: accepted 76 blocked records |
| Follow-up model-eval/orchestrator suites | 87 passed, **1 skipped**; no live-model test |
| #79 catalog/new skill | Catalog passes, single new-skill lint passes with advisory warnings |
| Combined #79/#82 merge simulation | FAIL, four conflicting files |
| Product build/guards | PASS |
| Product typecheck/tests after contracts build | PASS / 10 passed |
| Product HTTP/WebSocket happy-path E2E | 11 checks pass against existing local API |
| Product cluster E2E | 7 pass; Redis cross-instance fan-out |
| Product headed Chromium playtest | 49 pass, 0 defects; 28 logged console errors are deliberate 4xx probes |
| Independent browser panel | Loaded/rendered landing; clicked Auctions; signed-out access denied with sign-in link; observed expected 401 and router warnings |
| Product adversarial probes | Four demonstrated boundary failures, not acceptance passes |

One combined product shell invocation timed out at 120 seconds after writing its browser report. The outputs above were inspected, typecheck/tests and cluster results were recovered, and headed browser completion was rerun separately before recording its exit status. An individual command's exit is not inferred from the enclosing shell returning 0.

## Improvements worth making

1. **Truthful receipts instead of “fired” counters.** A reusable receipt should identify revision, candidate hash, host/model/tools, invocation mode, exact retrieval tool-call/result, eligibility, outcome/proof/architecture, and budget. Use the same vocabulary in the brief, trace schema, scorer and report.
2. **A small repeatable trigger lab rather than another huge product rebuild.** Generate a held-out prompt/control campaign from the catalog with per-host eligibility and role dispatch cases. It is cheaper to isolate a bad trigger there; reserve Bazaar II for integrated efficacy/security behavior.
3. **One safe delivery engine, many thin host adapters.** Add host paths to the ownership-aware implementation instead of growing a second shell sync system. Test it with disposable homes and a post-install discovery/resource smoke per host.
4. **Independent adversarial product gate.** Tenant enrollment, admin grants, socket authorization, expired auctions, concurrent wallet holds, dependency readiness and fresh-install behavior deserve tests distinct from a happy-path browser driver. Balanced postings alone do not prove safe concurrency; `holdBid()` reads balance without locking the account, so test bids on multiple auctions sharing one wallet before certifying ledger safety.
5. **Versioned audit checkpoints.** Capture the exact branch set, approved plan, frozen receipts and machine-readable status once per run. This reduces model-switch ambiguity without erasing work or carrying forward stale success claims.

## Proposed landing and sync sequence

This is a plan, **not authorization to merge or publish**.

1. Repair coverage grading, macOS dependency isolation, relative trap paths and Markdown; add their regression tests.
2. Integrate #79 onto #82's safe delivery engine and resolve docs/catalog coherently; adding Cloudflare makes 77 skills, so regenerate the Gauntlet inventory instead of leaving its 76-row snapshot stale.
3. Review/include the three local follow-ups deliberately. Retest the exact integrated tree, including all Python suites and macOS CI. Keep parked WIP and the older dirty worktree out of the commit unless specifically recovered.
4. Rerun final product gates against a new versioned freeze; address the adversarial failures or explicitly narrow the demo's acceptance claims.
5. Approve a bounded live trigger campaign. Until it runs, a structural merge can only be accepted with a clearly recorded live-host limitation, **not** “everything works across models.”
6. Obtain explicit approval for the final merges and then update the **stable main checkout**, not this temporary audit clone. Existing global links mostly point at that stable checkout and will reflect file edits immediately; model sessions may still cache skill discovery, so reload/new sessions are needed.
7. From that stable checkout preview:

   ```bash
   ATS_CHECKOUT_ROOT="$PWD" bash skills/workflows/sync-skills/scripts/sync-skills.sh --link --to-all --dry-run
   ```

   **Important:** #82's current `--to-all` covers only Claude and Cursor. It will not update Codex/Gemini/shared agents/Devin/Hermes. Do not use this command as an all-host promise until the repaired adapter explicitly supports those destinations. Inventory and obtain approval for every unowned/edited collision before `--replace-with-backup`; never use blanket force deletion.

8. After approval apply the reviewed plan, save ownership/backup receipts, verify every eligible installed skill's resources/hash and discovery path, then start fresh Claude Code and other-host sessions and perform load/trigger smoke checks. Preserve rollback backups until the owner confirms success.

The read-only stable-checkout preview succeeded today: **76 Claude links safely adoptable, 52 Cursor operations**. Previewing from the audit clone instead correctly reports foreign-checkout collisions; do not apply from the clone. Existing symlinks were observed in shared agents/Codex/Gemini/Hermes too, but the current safe adapter does not reconcile them. Existing external/community skill counts differ per host and must not be mistaken for the canonical catalog count.

## Evidence and reproducibility

Durable evidence is linked from [evidence/INDEX.md](evidence/INDEX.md). Complete verbose logs and disposable clones remain under the ignored `.workspaces/today-audit/` checkpoint while this workspace is retained.

- [Audit check runner](run-checks.sh)
- [Independent trace/frozen/scorer probe](probe-evidence.py)
- [Fresh-fixture product adversarial probe](probe-bazaar.mjs)

The probes reproduce findings; their exit 0 means the probe completed, **not** that the target passed acceptance. No production/library source was repaired in this audit. The report's hold remains until the stated checks and evidence are corrected.
