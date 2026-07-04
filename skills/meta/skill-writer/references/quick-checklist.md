# Quick Pre-Ship Checklist

Run through this before declaring a skill done. It covers the most common failures caught by `skill-review` and the frontmatter spec. For the complete field reference, see `references/frontmatter-spec.md`.

Source: Anthropic Agent Skills guide (Reference A, p.30) + this repo's PSFS v1.1.0 spec.

---

## Before You Start

- [ ] You have a real task the skill will run against — not a hypothetical. (Anthropic guide: "iterate on a single task before extracting to a skill".)
- [ ] The skill earns its keep with references, scripts, or composition logic. Single-prompt templates belong as slash commands, not skills.
- [ ] You've checked `skill-explorer` (or the skills catalog) and confirmed no existing skill covers this. Duplicate skills erode trigger reliability.

---

## Frontmatter Valid

- [ ] `name` is kebab-case, ≤64 chars, matches the folder name, unique in the collection
- [ ] `name` does not start with `claude-` or `anthropic-` — unless the skill explicitly targets that Anthropic product (document the exception in the body)
- [ ] `version` is valid semver starting at `1.0.0`
- [ ] `description` is present and uses the 3-slot anatomy: `[What] + [When] + [Key capabilities or keyword variants]`
- [ ] `description` target ≤200 chars; hard ceiling 1024 chars; never exceeds it
- [ ] `description` starts with an action verb
- [ ] `description` contains at least one trigger context (`when`, `for`, `whenever`, or a sample phrase users would say)
- [ ] No `<` or `>` anywhere in frontmatter values (security rule — frontmatter is injected into the system prompt)
- [ ] `allowed-tools` uses the hyphenated form (not `allowed_tools`)
- [ ] `compatibility` string present if the skill requires specific environments (Claude Code, Bash, MCP server, agent teams)

For agent role skills:

- [ ] `owns.directories` declared; does not overlap with any existing agent (check `frontmatter-spec.md` §Resolved Conflicts v1.1)
- [ ] `requires_agent_teams: true` if the skill needs the experimental agent teams env var
- [ ] Degradation path documented in the body if `requires_agent_teams: true`

---

## Description Anatomy

- [ ] Slot 1 — What it does: starts with an action verb ("Generate", "Audit", "Verify", "Run")
- [ ] Slot 2 — When to use it: at least 3 specific trigger contexts users might actually type
- [ ] Slot 3 — Key capabilities or keyword variants: domain keywords, file types, or "also trigger when" phrases
- [ ] Passes the "would Claude invoke this?" test — read the description cold and ask whether the trigger contexts are specific enough to fire reliably

See `description-patterns.md` for templates and examples.

---

## Body Length and Structure

- [ ] Body is ≤5,000 words (Anthropic guideline) and ≤500 non-blank lines (repo soft warning)
- [ ] Detailed checklists, large tables, and technical guides are in `references/` — not in the body
- [ ] Each reference file is linked from the body with a clear instruction on when to read it
- [ ] No content is duplicated between the body and its reference files
- [ ] Body follows the recommended structure: role statement → inputs → process (numbered steps, imperative voice) → coordination rules → guidelines

For agent role skills, the body also includes:

- [ ] Step 0: Read Contracts (before any implementation)
- [ ] Ownership section listing owned and off-limits files
- [ ] Right-sizing guidance
- [ ] Link to `references/validation-script-pattern.md` for how to wire a validation step into the new skill's body

---

## Triggers Tested

Before shipping, write at least 3 "should trigger" and 2 "should NOT trigger" phrases and verify them mentally against the description:

```
Should trigger:
- "..."
- "..."
- "..."

Should NOT trigger:
- "..."
- "..."
```

(Anthropic guide p.15 — include these as a comment in the skill body or in an adjacent notes file.)

---

## Cross-References Resolve

- [ ] All `composes_with` entries name real skills (in-repo: kebab-case names; plugin: `plugin:skill-name`)
- [ ] All `spawned_by` entries name real skills
- [ ] All `references/` files mentioned in the body actually exist at the path listed
- [ ] `skill-review` (or `scripts/lint-skills.sh`) passes with no errors

---

## After You Ship

- [ ] Run `scripts/lint-skills.sh skills/path/to/skill/` — no errors, warnings reviewed
- [ ] Run `scripts/scan-skills.sh skills/path/to/skill/` — no HIGH findings
- [ ] If the skill affects the skill ecosystem itself (meta skills), run `skill-review --scope=<name>` for a deep check
- [ ] Sync to global: run `sync-skills` if the skill should be available outside this repo

---

## Red Flags (Stop and Fix)

- Description is vague ("helps with X", "manages Y") — it will under-trigger. Rewrite with specific trigger contexts.
- Body is over 500 lines before references are moved out — context cost will be high.
- `owns.directories` overlaps with another agent — will cause merge conflicts on every parallel build.
- `composes_with` references a skill name that doesn't exist — cross-skill lint will flag this.
- No `references/` dir but the body has a 50-row table or a 300-line checklist — move them.
