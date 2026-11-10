# Give Andon runs these skills: Skill-Madness as a harness

An Andon **harness** is a versioned bundle of skills plus an outline of the stages a card goes through. A run under a
harness gets the bundle's skills in its own Claude config directory (never the person's `~/.claude`), and a brief
listing them. The run records the bundle's hash, so runs can be compared by the harness they used. Andon's own
`docs/harnesses.md` uses "madness" as its example; this is how to make that real.

Rules below mirror the Andon commit in `andon-pin.json` (`packages/shared/src/harness.ts`, `apps/agent/src/harness.ts`).
A harness is **team-scoped**, and it is the only way Andon itself installs skills for a run (the per-card skills shelf
is being removed, andon PR #499). For skills that differ per card, use the notes (`plan-to-cards.md`).

## Why a build step

`andon harness add <dir>` reads **every** file under the directory and every `SKILL.md` in it. Pointing it at the
repo would pull in docs, tests and whatever is untracked in your checkout (eval workspaces, `node_modules`). The
importer refuses more than 600 files or 8 MB, and the bundle's hash would change whenever local leftovers did. So build
a bundle of exactly the committed skill files you want:

```sh
python3 skills/workflows/andon/scripts/build_harness.py --preset core --dry-run     # check first
python3 skills/workflows/andon/scripts/build_harness.py --preset core               # writes integrations/andon-harness/madness
python3 skills/workflows/andon/scripts/build_harness.py --skills madness,plan-builder,git-pr,fix-until-green
```

- `--preset core` is the router plus what a single run most often needs: `madness`, `plan-builder`, `git-commit`,
  `git-pr`, `git-pr-feedback`, `fix-until-green`, `diagnose-loop`. Every live skill also fits (about 320 files,
  2.4 MB), but a smaller set gives the run a shorter skill index to choose from.
- Only git-tracked files are copied. Symlinks and `node_modules`-style directories are skipped, as Andon skips them.
- `--entry` sets the skill a run opens first; it defaults to `madness` when bundled. `--slug` (default `madness`)
  is the name Andon registers.
- The script runs Andon's own checks before writing: file and size limits, at most 200 skills, no duplicate names,
  descriptions present and at most 1024 characters, the entry skill in the bundle, and a valid outline. A bundle it
  writes has also passed Andon's compiled `validateHarness` (checked 2026-10-30, all 79 live skills, no issues).

`madness` routes to other skills by name. In a bundle that leaves some out, it can only hand off to the ones present;
the run's brief lists exactly which. Bundle the skills the team's cards actually need.

## The outline

The bundle's `harness.json` declares the stages. The default is:

| key      | actor | gate                                                      |
| -------- | ----- | --------------------------------------------------------- |
| `plan`   | agent | "a plan a person approved", one round; produces `plan.md` |
| `build`  | agent | after `plan`                                              |
| `verify` | agent | after `build`; "typecheck, lint and tests pass"           |

Andon then appends its own `review` → `ci` → `merge`, which a bundle cannot redefine. The harness brief tells a run
whose skill plans work to call `propose_steps`, so that work becomes cards on the board rather than files. To change the stages, pass
`--outline stages.json` (a JSON list of stages, or a whole `harness.json`). Stage fields: `key`, `label`,
`actor` (`agent` or `human`), `recipe`, `gate` (`requires`, `max_rounds`), `depends_on`, `produces`. At most 12
stages. Today a run is told it is in the first stage; the runner that walks later stages is not built yet.

## Import and approval

```sh
andon harness add integrations/andon-harness/madness     # copies it into the agent's state dir, hashes it
andon harness list                                       # slug, first 12 of the hash, skills, approved or not
andon harness approve madness                            # Tier 3: the person's call, on this machine
```

- Import executes nothing. It records the bundle on the board unless `--no-register` is passed.
- Expect import warnings that a skill "asks for tools this machine's policy doesn't allow" even for `Read` or `Grep`.
  As of 0.2.11, Andon's `parseAllowedTools` splits on commas only, so the `["Read", "Bash"]` form Skill-Madness uses (and
  the spec's space-separated form) never matches the ceiling. The warning is wrong, not the bundle; tell the person
  rather than rewriting every skill's frontmatter.
- **Approval is per machine and per hash.** With the default policy (`policy.harnesses.mode = approve`), a run whose
  team names a hash nobody approved on that machine fails with `blocked by machine policy` and the exact approve
  command. Every rebuild that changes a byte is a new hash and needs approving again. That is deliberate, so never
  approve on the person's behalf. Show the command and let them run it or say yes.
- `andon harness add <git-url> --ref <sha>` imports from a repo instead of a directory, but it reads the whole repo,
  so this one won't fit. Use a local bundle.
- On the board, **Settings → Teams → Harness** attaches the harness to a team (it inherits down the team tree). A
  team without one runs Andon's own pipeline.

## After an import, tell the person

1. The slug and the first 12 characters of the hash (`andon harness list`).
2. The approve command for each machine that should run it.
3. Where to attach it on the board.
