# Universal audit — Sol review and corrected closure

**Date:** 2026-10-05
**Baseline:** `9e0289a2b83e82ff5920fe87358f218845b7d7c0` (audit over source `51106e1`)
**Delivery:** uncommitted isolated Freebuff worktree; no primary-checkout transfer
**Review independence:** same-context source/tooling review, not independent QE

## Acceptance and authority

The approved scope is [UA-01–UA-32](09-ledger-intake.md), with native Claude
teams/agents/workflows/hooks and explicit opt-ins preserved. Outcomes must be
proved through the actual CLI or artifact interface, not only prose assertions.
Author frontmatter stays canonical; portable exports adapt types separately.
Dry-run remains read-only; install/sync protect unrelated data and preserve
reviewed bytes/modes. Evaluation requires isolated candidate/home, a pinned
worker, unforced exact retrieval, tri-state errors and frozen real-task holdouts.

No paid model calls, production operations, real-HOME installation, account
creation, commits, pushes or PRs were performed. Provider policies are not
permission to spend or publish. No performance speedup is claimed.

## Findings and repairs

- **Evaluation proof:** inherited stdout/log heuristics and wrong event names
  could score fictional retrieval. The runner now validates Hermes stream-json
  init/model, correlated `skill_view` use/result, exact successful candidate and
  terminal result. Truncated output uses only the exact session/call/tool SQLite
  record. Invalid/error/timeout/database failures have no trigger score.
- **Isolation:** candidate YAML round-trips through existing PyYAML; isolated
  HOME, HERMES_HOME, XDG and user-profile overrides prevent touching real skills.
  Bundled skill seeding/config/rules are disabled; model and call limits are explicit.
- **Holdout leakage:** deterministic assignments no longer rebalance empty
  splits. Synthetic/unproven tasks train only. Persistent query hashes freeze
  labels/provenance/splits even for train-only restarts; final test is burned
  before dispatch, and errors stop optimization. Selection uses dev/train,
  never test; optimizer sees train feedback only. Report separates all scores.
- **UA-19 receipt validator:** implemented inside the creator, not a new eval
  platform. Rejects malformed containers/types, nonfinite numbers, unknown
  layers/kinds, budget breaches, forced treatment, changed baseline worker/host,
  reused holdout and single-rollout efficacy. Offline fixtures cannot establish
  live capability. Validation does not enforce a running process's budget.
- **Export/capabilities:** standard adapter preserves body/native arrays and
  stringifies exported tools/metadata/extensions. Resolver no longer invents
  host capabilities or swallows YAML failures; malformed safety fields block.
  Converter validates resolver status/JSON. Antigravity's host metadata remains
  intact; its failing golden assertions were retained, not weakened.
- **Resource diagnostics:** verbose lint inventories filtered regular files,
  bytes and literal local paths; missing files/symlinks block. Qualified external
  skill/checkout references are reported and declared in runtime receipts;
  generated project outputs are not mistaken for bundled helpers. This is a
  narrow source diagnostic, not a complete executable-path parser or host proof.
- **Bounded capture:** route/height/decoded-byte limits are executable, including
  device scale and post-lazy growth. Oversized input is refused (tiling is not
  implemented). Failed navigation is not swallowed, and recapture invalidates
  stale manifests. Build refuses missing/oversized screenshots and scaled images.
- **Authority/policy:** repaired missing-config consent in consumers; wiki
  provenance/current-source checks; paginated unresolved review-thread handling;
  read-only tag cleanup classification and exact deletion approval; PR lookup
  errors block duplicate creation. Native-only spawn/no-implementation rules
  are scoped away from attended sequential BUILD_SLICE. Publish/settings/install/
  deploy approval is exact, and loop checkpoints no longer authorize automatic
  commits or destructive resets.
- **Mechanical loop controls:** added the shared `run_guarded.py` POSIX wrapper
  to loop-controller, not a new runner skill. It reserves worst-case adapter
  call/token/cost liability before each dispatch, rejects unknown limits,
  refuses lock/consumed-state reuse, cancels process groups and checks frozen
  verifier/config/test/dataset hashes before/during/after commands. Six real
  subprocess tests cover reservation cap, restart, lock, timeout-child cleanup,
  unknown liability and verifier tampering. Provider-specific hidden traffic
  requires a proven adapter; local hash checking is not an OS sandbox.
- **Quality claims:** removed unsupported live-host/macOS-gate/body-line claims
  and distinguished physical lines, nonblank lines, words and approximate tokens.
  Historical completion prose is retained only with an explicit supersession.

## Verification

Final receipts are saved in the ignored [review workspace](../../../.workspaces/sol-review/).
They describe local source/CLI checks, not independent review or host efficacy.
The final command results are recorded in the closing verification subsection.

A real local Chromium fixture captures a 1,200px page, refuses a 9,000px page,
refuses unreachable navigation and removes stale success receipts. The accepted
capture builds a real H.264 MP4; ffprobe and browser playback validate the artifact.
No external site or provider is involved.

Historical adversarial fixtures/generated installs/test snapshots were moved,
not deleted, into `.workspaces/sol-review/inherited-audit/`. Tracked audit reports
and logs remain unchanged; old absolute scratch paths in historical logs are
not current runnable instructions. Scratch copies are not source changes and
are not reformatted as if authored evidence.

## Corrected row status

**31 rows have local implementation/proof within their stated scope. UA-19
remains open for live-host retrieval and held-out efficacy.** This supersedes the inherited claim that
all 32 were complete. CB-10 remains speculative; F3/F5/F9/F15/F16 products are
not silently promoted or completed.

| Wave | IDs | Current scope and evidence |
|---|---|---|
| A | UA-08, UA-12 | Fake-root dry-run and strict QA failure/freshness/reentry regressions; not independent QE |
| B | UA-01, UA-04–07, UA-31 | Explicit solo/native branches and 33 source/bootstrap regressions; conservative parsers, not rendered-app certification |
| C | UA-09–11, UA-20–21, UA-26 | 20 fake-root delivery/install/sync regressions, preserved modes/resources/rollback; no hostile-race filesystem guarantee |
| D | UA-02, UA-03, UA-24 | Fail-closed resolver/schema, sequential protocol and role/gate reconciliation; state graph is specified, not an executable scheduler |
| D | UA-13, UA-14 | Bundled POSIX controller reserves worst-case liability, locks/cancels process groups and hashes frozen boundaries; six real subprocess regressions; unknown/unbounded provider adapters remain refused |
| E | UA-15–18 | Provider consent policy and offline tested trigger/split runner repairs; live model behavior NOT RUN |
| E | UA-19 | **OPEN:** receipt interface and offline fixtures exist; cross-host unforced retrieval and held-out task efficacy are NOT RUN |
| F | UA-22–23, UA-25, UA-27–30, UA-32 | Scoped Git/config/wiki/authority doctrine, standard export and real bounded capture; policy text is not a remote mutation or live model trial |

## Remaining acceptance gates

1. **Native/provider adapter boundary (UA-13/14):** the generic local controller
   cannot measure hidden traffic, authenticate a reviewer or sandbox hostile
   transient verifier edits. Unknown internal liability, detached process groups
   and missing hard-bound adapters remain refused. These are explicit limits,
   not completion of F9/F15/F16 or approval to run unattended paid calls.
2. **UA-19:** obtain explicit host/model/provider/egress and spend ceilings, then
   run a small frozen matrix with unforced traces, same-worker baselines, fresh
   real holdouts and repeated trials. Deterministic fake-root exports do not
   substitute for live-host task outcomes.

Independent QE/reviewer acceptance is still required before release. Passing
local checks does not grant this session that independence.
