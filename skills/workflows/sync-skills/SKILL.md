---
name: sync-skills
version: 2.2.0
description: |
  Sync approved Skill-Madness skills into Claude Code and Cursor skill directories with links or resource-complete copies. Use for "sync skills", "link skills", "skill status", "unlink skills", or importing an explicitly selected local skill. Honor category/skill subsets, preserve unrelated copies and links, and require explicit backed-up collision approval. Global mutation is never implicit in catalog maintenance.
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: ["skills/workflows/sync-skills/"]
  patterns: []
  shared_read: ["skills/"]
allowed-tools: ["Read", "Bash"]
composes_with: ["skill-update", "skill-review"]
spawned_by: []
---

# Sync Skills Between Repo and Global Locations

Native link/copy behavior remains available for **Claude Code and Cursor only**.
Do not imply additional host acceptance. Converted rules and native skill-directory
sync are distinct format adapters, but share eligibility and resource policy.

## Runtime and authority

Run `scripts/sync-skills.sh` under this skill's actual `SKILL_ROOT`. A native
symlink resolves the canonical checkout; an installed copy requires explicit
`ATS_CHECKOUT_ROOT` pointing at the approved Skill-Madness checkout. The shared
resolver is root tooling and is not bundled as a fake independent checkout.
Missing checkout/helpers are BLOCKED.

Global mutation requires owner approval for target, subset and mode. Preview
first. `--replace-with-backup` is a separate explicit collision approval; it
renames the existing item to a unique sibling backup before replacement.
Never use the flag merely to get past a warning.

## Locations and projection

| Host | Destination | Layout |
|---|---|---|
| Claude Code | `~/.claude/skills/<slug>/` | Individual native skill links/copies |
| Cursor | `~/.cursor/skills-cursor/<slug>/` | Individual skill-directory links/copies |

Individual entries make category/skill subsets exact. Old category links are
not automatically removed or migrated. Archive/in-progress are excluded.
Claude retains native gated skills; Cursor uses conversion's
`requires_claude_code` filter. Native metadata is unchanged.

Copy mode retains scripts, references, assets, agents, viewer and template
resources, exact source executable modes and runtime receipts. It excludes env
files, keys, node modules, bytecode and evaluation-workspace debris. Link mode
points at live source; source checkout security still matters.

## CLI

```bash
SCRIPT="$SKILL_ROOT/scripts/sync-skills.sh"
# Read-only status / preview:
bash "$SCRIPT" --status
bash "$SCRIPT" --dry-run --link --to-claude meta
# After scoped approval:
bash "$SCRIPT" --link --to-claude skill-review
bash "$SCRIPT" --copy --to-cursor workflows
# After explicit collision backup approval:
bash "$SCRIPT" --link --to-claude --replace-with-backup skill-review
# Only recorded exact links are eligible for these operations:
bash "$SCRIPT" --unlink --to-all skill-review
bash "$SCRIPT" --clean
# Import selected skills; collisions need explicit backup approval:
bash "$SCRIPT" --dry-run --from-cursor my-skill
```

Supported directions: `--to-claude`, `--to-cursor`, `--to-all`,
`--from-claude`, `--from-cursor`, `--from-all`. Modes: `--link` (default),
`--copy`, `--unlink`, `--status`, `--clean`. Category, slug or category/slug
arguments select exact subsets; unknown selections fail.

## Ownership and failures

Each destination holds `.ats-sync-owned.json` recording this checkout's links
or copy byte/mode fingerprint. Unowned/edited collisions block before changes;
no `rm -rf` or `rsync --delete` against arbitrary local skills. Only unchanged
owned copies may be replaced automatically. An exact canonical-source link
can be adopted without deleting it. Unlink/clean affect only recorded links
whose target still matches; unrelated broken links remain untouched.

A receipt belonging to a different checkout blocks until the owner explicitly
reconciles it. Dry run writes no receipt or destination. Status is discovery,
not certification that a host loaded the skill. Pull/import copies only selected
skill source/resources into a real category, skips links back into the checkout,
and requires backed-up approval for existing destinations. Review imported
instructions before use.

## Verification

Inspect the reported subset and backups, then run status. A copied helper should
run from its resource root in an isolated project; missing runtime/credentials
remain BLOCKED. No provider calls or real global install is part of the offline
delivery tests.
