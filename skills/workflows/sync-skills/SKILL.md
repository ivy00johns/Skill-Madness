---
name: sync-skills
version: 2.2.0
description: |
  Sync skills between this repo and the global skill directories of EVERY agent host — Claude Code, Cursor, Codex, Gemini CLI, the shared ~/.agents dir, Devin, and Hermes (main + every profile) — using symlinks (default) or copies, and find skills stranded in a single host's folder. Use when the user wants to link, sync, publish, push, or copy skills globally, check sync status, unlink, or pull a skill from a global location back into the repo. Trigger on "sync skills", "link skills", "publish skills", "skill status", "/sync-skills", "are my skills linked", "unlink skills", "why doesn't Codex/Hermes/Gemini have this skill", "skill only exists in one host", "orphaned skills".
requires_agent_teams: false
requires_claude_code: false
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

Link or copy skills between this repo and the global skill directories every agent host reads from. Symlinks are the default — edits in the repo are instantly available everywhere without copying.

This repo is a multi-host skill library. A skill built inside one host's folder (say `~/.hermes/skills/devops/`) is invisible to every other host — that is how a Cloudflare deploy skill once existed only for Hermes while Claude sessions couldn't deploy a hello world. New skills go in the repo, then `--link --to-all`; `--orphans` finds skills that slipped into a single host.

## Skill Locations

| Location | Path | Used by |
| -------- | ---- | ------- |
| Repo (source of truth) | `skills/` | This workspace |
| Claude Code (global) | `~/.claude/skills/` | All Claude Code projects |
| Cursor (global) | `~/.cursor/skills-cursor/` | All Cursor workspaces |
| Codex | `~/.codex/skills/` | Codex CLI |
| Gemini CLI | `~/.gemini/skills/` | Gemini CLI |
| Shared agents | `~/.agents/skills/` | Hosts that read the cross-agent dir |
| Devin | `~/.config/devin/skills/` | Devin |
| Hermes | `~/.hermes/skills/skill-madness/` and `~/.hermes/profiles/<p>/skills/skill-madness/` | Hermes Agent, main + every profile |

The repo organizes skills into category directories (`contracts/`, `meta/`, `roles/`, `workflows/`, `orchestrator/`, `git/`). For Claude Code, symlinks are **flattened** — each individual skill is linked directly under `~/.claude/skills/` (no category subdirs) because Claude Code only discovers skills at `~/.claude/skills/<skill-name>/SKILL.md`. Codex, Gemini, shared agents, Devin, and Hermes are flattened the same way (Hermes under a `skill-madness/` category it scans). For Cursor, symlinks are created at the category level.

### Excluded directories

Two top-level directories under `skills/` are excluded from discovery and never get symlinked:

- `skills/archive/` — retired skills kept as reference-only audit trail
- `skills/in-progress/` — drafts under active development

The exclusion list lives in `SKIP_CATEGORIES` near the top of `scripts/sync-skills.sh`. Add a new entry there if another staging directory ever gets introduced. The corresponding paths must also be kept out of `.claude-plugin/plugin.json`'s `skills` array — otherwise the plugin would load them even though `sync-skills` doesn't.

## Quick Reference

```bash
SCRIPT="skills/workflows/sync-skills/scripts/sync-skills.sh"

# Link all repo skills into every host
$SCRIPT --link --to-all

# Find skills living in a host folder but not in the repo
$SCRIPT --orphans

# Check what's linked, copied, or missing
$SCRIPT --status

# Remove broken symlinks (e.g. after deleting a skill from the repo)
$SCRIPT --clean

# Link just one category to Claude Code
$SCRIPT --link --to-claude meta

# Copy instead of link (for machines without repo access)
$SCRIPT --copy --to-all

# Remove symlinks (restore independence)
$SCRIPT --unlink --to-all

# Pull a skill from Cursor into the repo
$SCRIPT --from-cursor shell

# Preview what would happen
$SCRIPT --dry-run --link --to-all
```

## Modes

### Link Mode (default for `--to-*`)

Creates symlinks from global locations pointing to repo directories. This is the development workflow — edit skills in the repo and they're instantly live in Claude Code and Cursor.

- **Claude Code**: Skills are **flattened** — each individual skill gets its own symlink directly under `~/.claude/skills/` (e.g., `~/.claude/skills/skill-review` → `repo/skills/meta/skill-review`). This is required because Claude Code only discovers skills at `~/.claude/skills/<skill-name>/SKILL.md`.
- **Cursor**: Symlinks are created at the **category level** (e.g., `~/.cursor/skills-cursor/meta` → `repo/skills/meta`)
- Non-repo skills in global locations (e.g., `~/.claude/skills/builtWithAgent/`) are untouched
- If a copy already exists where a symlink would go, Claude Code and Cursor replace the copy with a symlink (use `--dry-run` to preview first). The other hosts **skip** real directories and say so — a host-local copy may hold work the repo doesn't; compare and replace it by hand.

### Copy Mode (`--copy`)

Copies skill directories instead of symlinking. Use this when:

- Deploying skills to a machine that doesn't have the repo cloned
- You need a frozen snapshot that won't change with repo edits
- The target location is on a different filesystem that doesn't support symlinks

### Pull Mode (`--from-cursor`, `--from-claude`)

Copies skills FROM global locations INTO the repo. Always copies (not symlinks) since the repo is the destination. Useful for importing skills created outside this repo.

## Script Flags

| Flag | Purpose |
| ---- | ------- |
| `--link` | Create symlinks (default for `--to-*` operations) |
| `--copy` | Copy files instead of symlinking |
| `--unlink` | Remove symlinks to repo (restores global locations to independent state) |
| `--to-cursor` | Target `~/.cursor/skills-cursor/` |
| `--to-claude` | Target `~/.claude/skills/` |
| `--to-codex` / `--to-gemini` / `--to-agents` / `--to-devin` | Target that host's flat skill dir |
| `--to-hermes` | Target Hermes main + every profile's `skill-madness/` |
| `--to-all` | Target every host above |
| `--from-cursor` | Pull from Cursor into repo |
| `--from-claude` | Pull from Claude Code into repo |
| `--from-all` | Pull from both |
| `--status` | Show what's linked, copied, or missing across all locations |
| `--clean` | Remove broken symlinks from global locations |
| `--orphans` | List skills in any host folder that aren't in the repo (`host-only`), or that share a repo skill's name but aren't linked to it (`DIVERGED COPY`) |
| `--dry-run` | Preview what would happen without making changes |
| `-h, --help` | Show help |

Append category or skill names after flags to target specific ones:

```bash
$SCRIPT --link --to-claude meta roles    # Link only meta/ and roles/
$SCRIPT --from-cursor shell              # Pull only the shell skill
```

## How It Works

**Linking:** For Claude Code, discovers every individual skill within category directories and creates a flattened symlink for each (e.g., `~/.claude/skills/skill-review` → `repo/skills/meta/skill-review`). For Cursor, creates category-level symlinks. If the target already exists as a real directory, warns before replacing.

**Status detection:** Checks each expected location and reports whether it's a symlink (and where it points), a copy, or missing. Also detects broken symlinks.

**Non-repo skills are safe:** The script only manages categories that exist in this repo. Skills like `~/.claude/skills/builtWithAgent/` or Cursor's native skills are never touched.

## After Linking

Once linked, skills are available automatically:

- **Claude Code**: Skills in `~/.claude/skills/` are picked up by new sessions
- **Cursor**: Skills in `~/.cursor/skills-cursor/` appear in all workspaces
- **Codex, Gemini, Devin, shared agents, Hermes**: picked up by the next session or agent restart

Edit any skill in the repo and the change is live immediately — no sync step needed.

To verify: `$SCRIPT --status`
