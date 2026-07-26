# QA Report — ledger-drain build

**Build session:** `ledger-drain-06ae2f7` (branch `build/ledger-drain`, HEAD `06ae2f7`)
**Reviewed:** commits `da0711c..HEAD` (11 commits)
**Status:** PASS — **gate: proceed = true**

## Scope

Nine ledger rows: RV2 (LICENSE), HE-1 (audit-evidence versioning), HE-2 (decision-keyed
routing + load budget), WC-1 ($ARGUMENTS lint guard), WC-2 (agent-brief concretization),
PX-1 (`use-pxpipe`), PX-2 (madness proxy hook), PX-3 (image-proxy model allowlist), CB-3
(`yagni-gate`). Catalog ripple 71→73.

## Test execution (all observed live, this session)

| Check | Result |
|---|---|
| `bash tests/run-all.sh` (full bats suite, 17 files) | **346/346 passed, 0 failed, 0 skipped**, exit 0 |
| `bash scripts/lint-skills.sh` | **0 errors**, 117 warnings (all pre-existing style classes, none new-in-kind) |
| `bash scripts/catalog.sh --check` | clean at 73, plugin.json matches disk |
| `$ARGUMENTS` guard, hand-verified | fresh fixture skill with a literal `$ARGUMENTS` token → ERROR + exit 1, message names the token |
| `git log da0711c..HEAD --oneline` | 11 commits, all map to a ledger row or an explained scaffold/ripple purpose |

Full suite took ~5 minutes; ran in background while frontmatter/integration checks proceeded in parallel.

## Per-row verification

- **RV2** — `LICENSE` exists at root, standard MIT text, copyright "ivy00johns" 2026. README badge (:14) and both in-body `[MIT](LICENSE)` links (:746) resolve to it.
- **HE-1** — `[FAUDIT]` short-link in `docs/REMAINING-WORK.md:20` now points to `docs/audit-evidence/2026-05-28-functional-audit/master-audit.md` (in-repo, exists, along with `qe-agent.md` and `README.md`). `plan-intake/SKILL.md:110,138` gained an explicit "cite in-repo evidence only" rule.
- **HE-2** — `skill-explorer/references/routing-table.md` has a new `## By unresolved decision` index (:151). `madness/SKILL.md` has a new `## The load budget: one skill, or none` section (:109) with an anti-pattern row against multi-skill routing.
- **WC-1** — `lint-skills.sh` gained the `$ARGUMENTS` body guard (verified live, see table above). `contracts/installer/lint-rules.md` bumped 1.3.0→1.4.0 with the rule documented. 2 new bats cases pass (`ok 262`, `ok 263` in the full run).
- **WC-2** — `orchestrator/references/agent-spawning.md:65` has the numeric "~60 lines" split gate plus a pre-dispatch checklist item (:80). `skill-writer/references/patterns.md:67` documents the cost-tagged anti-pattern convention ("price every warning you keep").
- **PX-1** — `skills/workflows/use-pxpipe/SKILL.md` is complete and well-formed; frontmatter conformant (see below).
- **PX-2** — `madness/SKILL.md:145-166` asks the token-saver question once on expensive routes, suggest-only, never auto-enables, states when not to ask.
- **PX-3** — `model-adaptation/SKILL.md:196-220` has the "Image-proxy model allowlist" section with measured read rates (Fable 5 / Mythos 5 allowed; Opus 4.8 not allowed, 6/15); `use-pxpipe/SKILL.md:65-66` cites that exact section — the three-skill chain resolves end to end.
- **CB-3** — `skills/workflows/yagni-gate/SKILL.md` is complete and well-formed; `plan-intake/SKILL.md:86` repointed to reference it by name.
- **Catalog ripple** — README's cumulative table has zero gaps 1–73; `use-pxpipe`/`yagni-gate` correctly inserted at rows 59–60 with every subsequent row (including the full 65–73 loops section) renumbered rather than appended.

## Frontmatter conformance (new skills)

Both `use-pxpipe` and `yagni-gate` checked against `skills/meta/skill-writer/references/frontmatter-spec.md`:

- `name` kebab-case, matches directory name — pass
- `version` top-level valid semver (`1.0.0`) — pass
- `description` — no literal `<`/`>` characters — pass (the `>-` on yagni-gate's description line is a YAML block-scalar indicator, not description content; lint-skills.sh's own angle-bracket walk of parsed frontmatter passed clean)
- `composes_with` entries all resolve to real skill directories on disk — pass (`model-adaptation`, `use-freellmapi`, `madness` / `caveman`, `architecture-rescue`, `plan-intake`)
- Both pass the schema-driven `tests/standard` GATE test (every real `SKILL.md` validates against `spec/frontmatter.schema.json`) as part of the green 346-test run

## Blockers

None.

## Issues

- **INFO** — `test_results`'s unit/integration/contract/e2e/security_scan split is an approximate directory-level mapping (this repo has no app-level unit/e2e split or dedicated security scanner). The raw total (346/0/0, exit 0) is exact; only the 5-way bucketing is inferred. See `qa-report.json` issue `ISSUE-1` for the exact mapping used.
- **LOW** — Both new skills' descriptions trip the pre-existing "may not start with an action verb" / length-soft-target lint warnings, same classes already present on ~40 other library skills and explicitly tolerated by `CLAUDE.md`'s "pushy descriptions" design decision. No action required.

## Recommendation

Ship as-is. Every gate-relevant check was independently re-derived this session (not taken on
commit-message trust): the full bats suite, the lint pass, the catalog check, frontmatter
conformance for both new skills, and the WC-1 contract-doc version bump. All nine ledger rows'
stated observable changes hold.
