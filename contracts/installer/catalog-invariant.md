# Contract: Catalog-as-CI-Invariant (P1-A)

**Version:** 1.2.0
**Status:** ACTIVE — orchestrator, AllTheSkills P1
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P1)
**Models:** ECC's `scripts/ci/catalog.js` (counts asserted vs disk, build fails on drift, `--sync`).

The repo's advertised skill counts have **already drifted**: `README.md` says "47 skills" while its own per-category subgraphs sum to 46 and `.claude-plugin/plugin.json` says "46 skills". This contract adds a single source of truth — the filesystem — and a check that fails CI when prose disagrees with disk.

## Source of truth

The authoritative inventory is computed from disk:

- **A skill** = a directory directly under a category (`skills/<category>/<skill>/SKILL.md`) or the top-level `skills/orchestrator/SKILL.md`, **excluding** anything under `skills/archive/`, `skills/in-progress/`, or `node_modules/` — and anything nested deeper than a skill root (e.g. a bundled `node_modules` `SKILL.md`). The `find` scan is depth-bounded (`-maxdepth 3`) to enforce this.
- **Category** = the immediate subdirectory of `skills/` a skill lives in (`orchestrator`, `roles`, `contracts`, `meta`, `git`, `workflows`). `orchestrator/SKILL.md` at the category root counts as category `orchestrator` (count 1).
- Counts: total active skills + per-category counts.

`scripts/catalog.sh` computes these the same way every run (bash 3.2 portable, `find skills -name SKILL.md` minus the two excluded trees).

## CLI

```
scripts/catalog.sh [--check | --sync | --text] [--help]
  --check   (default) compute counts from disk, compare to the asserted counts in
            README.md + plugin.json + marketplace.json + CLAUDE.md + PLAN.md +
            START-HERE.md, AND verify the plugin.json `skills` array lists exactly
            the on-disk skills; exit 1 on any mismatch, 0 if clean.
  --sync    rewrite the asserted counts in those files + reconcile the plugin.json
            `skills` array (register missing, drop stale) to match disk; exit 0.
  --text    print the computed catalog (total + per-category table) to stdout; exit 0.
```

## Asserted-count locations (the check targets)

The check must compare disk truth against every place a count is hard-coded:

- `README.md`: the shields badge (`badge/skills-<N>-…`), the "**N skills, six categories**" line, the "installs all N skills" line, the "N skills organized into six categories" line, the "doesn't see all N skills" line, the "Skill library — N skills" line, and the mermaid per-category subgraph labels (`contracts/ — N skills`, `roles/ — N agents`, `meta/ — N skills`, `git/ — N skills`, `workflows/ — N skills`). As of 1.2.0 also: the "**N portable skills**" hero tagline, the "out of all N" front-door phrasings, the "skill library (N)" project-tree comment, the per-category badges/prose ("N role agents", "N contract skills", "N git-workflow skills", "N meta-skills", "N cross-cutting workflow skills", "N autonomous-loop skills", "N loop skills", "N autonomous loops"), the one-row-per-skill **catalog table** (row count + skill names == disk; `--check` only — rows are hand-maintained), and the **architecture-diagram boxes** (named nodes + the `"+ N more"` overflow == disk per category box; node ids unique per mermaid block; `--sync` repairs only the overflow number).
- `.claude-plugin/plugin.json`: the "<N> skills" phrase in `description`, AND the `skills` array itself — every on-disk skill registered, no entry pointing at a skill that no longer exists. Array reconciliation is delegated to `scripts/sync-catalog-skills.py`, which preserves the existing curated order and appends new skills to their category group. *(v1.0.0 deliberately left the array alone, assuming "existing tooling" verified it; nothing did — that is the drift this version closes.)*
- `.claude-plugin/marketplace.json`: any "<N> skills" phrase; as of 1.2.0 also the plugin description's per-category breakdown ("N role agents", "N contract skills", …).
- `CLAUDE.md`: the "N OSS-publishable skills" line; as of 1.2.0 also the per-category "- **`skills/<cat>/`** (N)" breakdown lines.
- `PLAN.md` (additional, 1.2.0): the "**N-skill autonomous-loop library**" phrase.
- `PLAN.md`: the "**N-skill** library" line.
- `START-HERE.md`: the "library of **N skills**" line.

Across every file, only **live** current-count phrasings are targeted; historical notes ("catalog reshaped to 47 skills", "across 49 skills") use distinct wording and are deliberately left untouched. A file that does not exist is a no-op.

Detect counts by regex (`[0-9]+ skills`, `skills-[0-9]+`, `— [0-9]+ (skills|agents)`); `--sync` rewrites the number in place without touching surrounding text. Per-category labels are synced from the per-category disk counts.

## CI

A new job/step (orchestrator wires it into `.github/workflows/lint-skills.yml` — **do not edit the workflow yourself**) runs `scripts/catalog.sh --check` and the `tests/catalog/` bats suite, failing the build on drift.

**Local enforcement.** A `catalog-sync` lifecycle hook (`hooks/scripts/catalog-sync.sh`, registered in `hooks/hooks.manifest.json`, `PreToolUse` on `git commit`) checks the catalog before a commit lands; on real drift it runs `--sync` and **re-stages** the corrected files so the commit is self-consistent. It acts only on drift and never blocks. The `skill-catalog` skill documents the whole single-source-of-truth model for humans and agents.

## Tests (`tests/catalog/`, bats, bash-3.2)

- `--text` prints total == sum of per-category counts.
- `--check` PASSES on a temp fixture where prose matches disk.
- `--check` FAILS (exit 1) on a temp fixture where a README count is wrong by one.
- `--sync` makes a failing fixture pass (`--sync` then `--check` → 0).
- archive/ and in-progress/ skills are excluded from the count.
- (1.2.0) catalog-table check: pass on a matching table, fail on a missing row and on a stale row.
- (1.2.0) previously-unguarded phrasings (hero / "out of all N" / tree comment), CLAUDE.md per-category lines, and the marketplace breakdown: `--check` fails on drift, `--sync` repairs.
- (1.2.0) mermaid boxes: `--check` fails on box math drift and duplicate node ids; `--sync` repairs the overflow node.

## Ownership (P1-A agent)

OWNS exclusively: `scripts/catalog.sh`, `scripts/sync-catalog-skills.py`, `hooks/scripts/catalog-sync.sh` (+ its `hooks.manifest.json` entry), `skills/meta/skill-catalog/`, `tests/catalog/`, and the asserted-count regions of `README.md`, `CLAUDE.md`, `PLAN.md`, `START-HERE.md`, `.claude-plugin/plugin.json` (the count phrase **and** the `skills` array), and `.claude-plugin/marketplace.json` (via `--sync`).
MUST NOT touch: `.github/workflows/` (orchestrator wires CI), `scripts/install*.sh`, `scripts/convert.sh`.

## DoD

`catalog.sh --check` reflects true disk counts; running `--sync` then `--check` is clean and leaves README + plugin.json + marketplace.json internally consistent (the existing 46/47 drift resolved to the real disk number). `bash -n` clean. bats pass. **No git operations.**

## Changelog
- 1.2.0 — close the drift classes that bit three times while `--check` stayed green: guard the README hero ("N portable skills"), "out of all N", and tree-comment ("skill library (N)") phrasings; per-category phrases across README badges/prose, `plugin.json`, and the `marketplace.json` breakdown; CLAUDE.md's per-category "(N)" lines; PLAN.md's loops-library phrase. New architecture-diagram box check (named nodes + "+ N more" == disk per category, node ids unique; `--sync` repairs only the overflow). Single-pass cached disk inventory (`_inventory`) replaces the per-file subshell loops — `--check` drops ~4.4s → ~0.7s. Also retroactively records the README catalog-table check (row count + names vs disk) that landed unversioned in PR #34 (CL3).
- 1.1.0 — extend count coverage to `CLAUDE.md` / `PLAN.md` / `START-HERE.md` (live phrasings only); reconcile the `plugin.json` `skills` array from disk via `scripts/sync-catalog-skills.py` (register missing, drop stale); exclude `node_modules` via `-maxdepth 3`; add the `catalog-sync` pre-commit hook (auto-fix + re-stage) and the `skill-catalog` skill. `sed_replace` treats a missing file as a no-op.
- 1.0.0 — initial (orchestrator, P1-A).
