---
name: skill-catalog
version: 1.0.0
description: |
  Keep the Skill-Madness catalog in sync with the filesystem. The published
  plugin.json `skills` array and every advertised skill count (README, CLAUDE.md,
  PLAN.md, START-HERE.md, marketplace.json) are DERIVED from disk by one command,
  so they never drift. Use this whenever you add, remove, or rename a skill,
  register a skill in plugin.json, notice mismatched skill counts ("47 vs 49"),
  hit a CI "catalog drift" failure, ask "how many skills are there", or need
  skills symlinked into ~/.claude for global use. The filesystem is the single
  source of truth: run `scripts/catalog.sh --sync` (a pre-commit hook also
  auto-fixes drift on commit), then `sync-skills` for the global symlinks. Never
  hand-edit the counts or the plugin.json array — let the tooling regenerate them.
compatibility: Claude Code
requires_claude_code: true
requires_agent_teams: false
min_plan: starter
allowed-tools: ["Read", "Bash", "Edit", "Glob", "Grep"]
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
composes_with: ["sync-skills", "skill-writer", "skill-update", "skill-review"]
---

# Skill Catalog

> **One rule:** the filesystem under `skills/` is the single source of truth for
> what skills exist and how many there are. Everything else — the `plugin.json`
> manifest, the README badge, the counts in `CLAUDE.md` / `PLAN.md` /
> `START-HERE.md` / `marketplace.json` — is *derived* from it. You never edit
> those by hand; you run one command and they regenerate.

This skill exists because the alternative — hand-maintaining a skill count in
six files plus a manifest array — drifts every single time. A skill gets added,
the array isn't updated, three of the six counts get bumped and three don't, and
now the repo disagrees with itself. The fix is to stop treating those numbers as
facts to maintain and start treating them as *outputs* to generate.

## The one command

```bash
scripts/catalog.sh --sync     # make every derived count + the plugin array match disk
scripts/catalog.sh --check    # verify they match (exit 1 + a drift report if not); CI runs this
scripts/catalog.sh --text     # print the per-category table (disk truth)
```

`--sync` is **idempotent** — run it as often as you like; if nothing drifted it
changes nothing. It is safe to run any time.

## What it keeps in sync

| Artifact | What's reconciled |
|---|---|
| `.claude-plugin/plugin.json` `skills` array | every on-disk skill is registered; stale entries (deleted skills) are removed; your curated order is preserved and new skills are appended to their category group |
| `.claude-plugin/plugin.json` description | the "with N skills" count |
| `README.md` | badge, all prose counts, the per-category mermaid labels |
| `CLAUDE.md` | the "N OSS-publishable skills" line |
| `PLAN.md` | the "**N-skill** library" line |
| `START-HERE.md` | the "library of **N skills**" line |
| `.claude-plugin/marketplace.json` | the two "N-skill" / "all N" phrases |

Only the **live** count phrasings are touched. Historical notes — `PLAN.md`'s
"catalog reshaped to 47 skills", "across 49 skills", etc. — use different wording
on purpose and are left exactly as written. They're a record of what was true
then, not an assertion about now.

## What counts as a skill

A directory directly under a category (`skills/<category>/<skill>/SKILL.md`) or
the top-level `skills/orchestrator/SKILL.md`. **Not** a skill: anything under
`archive/`, `in-progress/`, or `node_modules/` — including the `SKILL.md`
scaffolds that some bundled npm packages (e.g. `playwright-core`) ship deep
inside a skill's `scripts/node_modules/`. The scan is depth-bounded so those
never inflate the count. (This is why the count used to read "52" locally after
an `npm install` but "50" in CI — that bug is gone.)

## You usually don't run it at all

A `catalog-sync` pre-commit hook (`hooks/scripts/catalog-sync.sh`, registered in
`hooks/hooks.manifest.json`) intercepts `git commit`. If — and only if — the
catalog has drifted from disk, it runs `--sync` and **re-stages** the corrected
files so the commit is self-consistent. On an in-sync repo it does nothing. So
in practice: add your skill directory, commit, and the counts + manifest are
already correct in that commit. The drift can't land.

CI is the backstop: the "Installer + Catalog" job runs `catalog.sh --check`, so
even a commit made outside Claude Code (a terminal commit with the hook profile
off) is caught before merge.

## Workflows

### Add a skill

1. Create `skills/<category>/<new-skill>/SKILL.md` (use the `skill-writer` skill
   to scaffold it correctly).
2. Commit. The hook reconciles the manifest + counts into your commit. (Or run
   `scripts/catalog.sh --sync` first if you want to see the changes before
   committing.)
3. Run `sync-skills` to symlink it into `~/.claude/skills/` so it's available
   globally — see "Global availability" below.

### Remove or rename a skill

Delete or rename the directory, then commit (or `--sync`). The reconciler drops
the stale `plugin.json` entry and registers the new path; the counts fall or hold
automatically. A rename is just a remove + add.

### "The counts are wrong" / a CI catalog failure

Run `scripts/catalog.sh --check` to see exactly which files disagree and by how
much, then `scripts/catalog.sh --sync` to fix all of them at once, and commit.
Don't open the files and edit numbers — that's how the drift started.

## Global availability (symlinks) — `sync-skills`

Catalog sync is about the *repo's* internal consistency. Making the skills
actually loadable by Claude Code / Cursor is a separate axis: symlinking the
skill directories into `~/.claude/skills/` (and `~/.cursor/skills-cursor/`). That
is the `sync-skills` skill's job. The two compose into one "I added a skill"
story:

```bash
scripts/catalog.sh --sync     # repo agrees with itself (counts + manifest)
# … then, via the sync-skills skill:
/sync-skills                  # the skill is linked into the global dirs
```

Run catalog sync first (so the manifest is right), then `sync-skills` (so the
filesystem links are right). `sync-skills` also has a `--status` mode to answer
"are my skills linked?" the same way `catalog.sh --check` answers "are my counts
right?".

## Anti-patterns

- **Hand-editing a skill count anywhere.** The moment you type a number into
  `CLAUDE.md` or `plugin.json`, you've created a second source of truth that will
  drift. Run `--sync` instead.
- **Hand-adding a `plugin.json` `skills` entry.** Same problem, and easy to
  forget (that's the bug where a freshly-added skill silently never publishes).
  The reconciler registers it from disk.
- **Committing with `--no-verify` or the hook profile off, then wondering why
  CI fails on "catalog drift."** The check is there to catch exactly that. Run
  `--sync` and recommit.
- **Bumping the total but not the per-category breakdown** (the curated
  `skills/workflows/ (N) — name, name, …` list in `CLAUDE.md`). The *counts*
  sync automatically; that one enumerated prose list is still curated by hand —
  update it when you add a workflow skill, or the number and the names will
  disagree.

## Reference

- `scripts/catalog.sh` — the count + invariant engine (bash; the CI gate).
- `scripts/sync-catalog-skills.py` — the `plugin.json` `skills` array reconciler.
- `hooks/scripts/catalog-sync.sh` — the auto-fix-on-commit hook.
- `contracts/installer/catalog-invariant.md` — the catalog-as-CI-invariant contract.
