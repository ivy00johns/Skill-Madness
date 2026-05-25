# Contract: Plan/Apply Install + Install-State + Profiles (P1-B)

**Version:** 1.0.0
**Status:** ACTIVE — orchestrator, AllTheSkills P1
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P1)
**Models:** ECC's `install-plan.js` / `install-apply.js` / `list-installed.js` / `uninstall.js` (pure resolution → serializable plan → executor → recorded install-state with content hashes).

Today `scripts/install.sh` is convert-then-copy: it works, but has no dry-runnable operation list, no record of what it wrote, no drift detection, no uninstall, and no named profiles. This contract adds that discipline **alongside** the existing installer — `install.sh` is NOT modified or removed (it stays as the legacy path, exactly as ECC keeps a legacy shim beside its plan/apply scripts).

## Hard guardrails

- **Build new scripts only. Do NOT edit `scripts/install.sh` or `scripts/convert.sh`.** Read `contracts/installer/install-locations.md` for the source→dest matrix; resolve the plan from `integrations/` + that matrix, do not import install.sh logic.
- **Never run a real install / never write to the real `~/.claude/`.** All apply/state behavior is verified with a temp `--root`/`HOME` in tests.
- Bash 3.2 portable, `set -euo pipefail`, source `scripts/lib/term.sh`. Hashing via a helper that uses `shasum -a 256` (macOS) or `sha256sum` (linux) — detect once.

## Components

### 1. Profiles — `manifests/profiles.json`
Named subsets of skills selected by category (resolved against disk the same way `catalog.sh` defines a skill — exclude `archive/`, `in-progress/`):

```json
{
  "full":               { "categories": ["orchestrator","roles","contracts","meta","git","workflows"] },
  "orchestration-only": { "categories": ["orchestrator","contracts"] },
  "roles":              { "categories": ["orchestrator","roles","contracts"] },
  "git":                { "categories": ["git"] },
  "minimal":            { "categories": ["orchestrator"] }
}
```

### 2. `scripts/install-plan.sh` — pure resolution, no mutation
```
scripts/install-plan.sh --tool NAME[,NAME...] [--profile NAME] [--root DIR] [--out FILE]
```
- Resolves: selected tools × profile-selected skills → the set of file operations, reading dests from the install-locations matrix (honor `--root` to override `$HOME`/`$PWD` so tests never touch real locations).
- Emits a **serializable JSON plan** (to `--out` or stdout): `{ schema_version, generated_at, profile, tools, operations:[ {tool, source, dest, action: "create"|"overwrite"|"skip", sha256} ] }`. `action` is computed by comparing source hash to any existing dest file. **No writes.**

### 3. `scripts/install-apply.sh` — executor + state
```
scripts/install-apply.sh --plan FILE [--root DIR] [--dry-run]
```
- Consumes a plan, performs the file operations (respecting `--dry-run`), then writes **install-state** to `<root>/.claude/.ats-install-state.json`: `{ schema_version, applied_at, profile, tools, files:[ {dest, sha256, tool} ] }`. Idempotent: re-applying an unchanged plan is a no-op.

### 4. `scripts/install-state.sh` — list / drift / uninstall / repair
```
scripts/install-state.sh list      [--root DIR]      # show recorded install-state
scripts/install-state.sh drift     [--root DIR]      # compare recorded sha256 vs on-disk; report added/changed/removed; exit 1 if drift
scripts/install-state.sh uninstall [--root DIR] [--dry-run]   # remove recorded files; clear state
scripts/install-state.sh repair    [--root DIR] [--dry-run]   # re-copy files whose on-disk hash != recorded (needs source still in integrations/)
```

## Tests (`tests/install-plan/`, bats, bash-3.2, all under a temp `--root`)
- plan: `--profile minimal --tool claude-code` → JSON parses; operations reference only orchestrator-category sources; every op has a sha256; `action=create` into an empty root.
- plan idempotent action: pre-place an identical dest file → `action=skip`; pre-place a differing file → `action=overwrite`.
- apply: applying a plan into a temp root creates the files and writes a parseable install-state whose hashes match; re-apply is a no-op.
- state list: reflects applied files. drift: mutate an installed file → `drift` reports it + exit 1; pristine → exit 0. uninstall: removes recorded files + clears state. repair: restores a mutated file to source hash.
- profile resolution: `git` profile selects only git-category skills; `full` selects all categories; counts match `catalog.sh` per-category.

## Ownership (P1-B agent)
OWNS exclusively: `scripts/install-plan.sh`, `scripts/install-apply.sh`, `scripts/install-state.sh`, `scripts/lib/install-state.sh` (shared helpers if needed), `manifests/profiles.json`, `tests/install-plan/`, and a `## Plan/Apply install` section appended to `scripts/README.md`.
MUST NOT touch: `scripts/install.sh`, `scripts/convert.sh`, `.github/workflows/`, `README.md`, `.claude-plugin/*` (P1-A owns counts), `scripts/catalog.sh`, `tests/catalog/`, `hooks/`, `skills/workflows/repo-deep-dive/`.

## DoD
plan→apply→list→drift→uninstall→repair all work against a temp root; install-state records content hashes (the provenance ECC itself lacks); profiles resolve correctly; `bash -n` clean; bats pass; `scripts/install.sh` untouched and still passing its 172 installer tests. **No git operations. No real `~/.claude` writes.**

## Changelog
- 1.0.0 — initial (orchestrator, P1-B).
