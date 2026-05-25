# Contract: Catalog-as-CI-Invariant (P1-A)

**Version:** 1.0.0
**Status:** ACTIVE — orchestrator, AllTheSkills P1
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P1)
**Models:** ECC's `scripts/ci/catalog.js` (counts asserted vs disk, build fails on drift, `--sync`).

The repo's advertised skill counts have **already drifted**: `README.md` says "47 skills" while its own per-category subgraphs sum to 46 and `.claude-plugin/plugin.json` says "46 skills". This contract adds a single source of truth — the filesystem — and a check that fails CI when prose disagrees with disk.

## Source of truth

The authoritative inventory is computed from disk:

- **A skill** = a directory under `skills/` containing a `SKILL.md`, **excluding** anything under `skills/archive/` and `skills/in-progress/`.
- **Category** = the immediate subdirectory of `skills/` a skill lives in (`orchestrator`, `roles`, `contracts`, `meta`, `git`, `workflows`). `orchestrator/SKILL.md` at the category root counts as category `orchestrator` (count 1).
- Counts: total active skills + per-category counts.

`scripts/catalog.sh` computes these the same way every run (bash 3.2 portable, `find skills -name SKILL.md` minus the two excluded trees).

## CLI

```
scripts/catalog.sh [--check | --sync | --text] [--help]
  --check   (default) compute counts from disk, compare to the asserted counts in
            README.md + plugin.json + marketplace.json; exit 1 on any mismatch, 0 if clean.
  --sync    rewrite the asserted counts in those files to match disk; exit 0.
  --text    print the computed catalog (total + per-category table) to stdout; exit 0.
```

## Asserted-count locations (the check targets)

The check must compare disk truth against every place a count is hard-coded:

- `README.md`: the shields badge (`badge/skills-<N>-…`), the "**N skills, six categories**" line, the "installs all N skills" line, the "N skills organized into six categories" line, the "doesn't see all N skills" line, the "Skill library — N skills" line, and the mermaid per-category subgraph labels (`contracts/ — N skills`, `roles/ — N agents`, `meta/ — N skills`, `git/ — N skills`, `workflows/ — N skills`).
- `.claude-plugin/plugin.json`: the "<N> skills" phrase in `description`. (Do not try to reconcile the `skills` array here — that's verified separately by existing tooling; this check only owns the human-readable count.)
- `.claude-plugin/marketplace.json`: any "<N> skills" phrase.

Detect counts by regex (`[0-9]+ skills`, `skills-[0-9]+`, `— [0-9]+ (skills|agents)`); `--sync` rewrites the number in place without touching surrounding text. Per-category labels are synced from the per-category disk counts.

## CI

A new job/step (orchestrator wires it into `.github/workflows/lint-skills.yml` — **do not edit the workflow yourself**) runs `scripts/catalog.sh --check` and fails the build on drift.

## Tests (`tests/catalog/`, bats, bash-3.2)

- `--text` prints total == sum of per-category counts.
- `--check` PASSES on a temp fixture where prose matches disk.
- `--check` FAILS (exit 1) on a temp fixture where a README count is wrong by one.
- `--sync` makes a failing fixture pass (`--sync` then `--check` → 0).
- archive/ and in-progress/ skills are excluded from the count.

## Ownership (P1-A agent)

OWNS exclusively: `scripts/catalog.sh`, `tests/catalog/`, and the asserted-count regions of `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (via `--sync`).
MUST NOT touch: `.github/workflows/` (orchestrator wires CI), `scripts/install*.sh`, `scripts/convert.sh`, `scripts/README.md` (P1-B owns), `hooks/`, `skills/workflows/repo-deep-dive/`, or any P1-B file.

## DoD

`catalog.sh --check` reflects true disk counts; running `--sync` then `--check` is clean and leaves README + plugin.json + marketplace.json internally consistent (the existing 46/47 drift resolved to the real disk number). `bash -n` clean. bats pass. **No git operations.**

## Changelog
- 1.0.0 — initial (orchestrator, P1-A).
