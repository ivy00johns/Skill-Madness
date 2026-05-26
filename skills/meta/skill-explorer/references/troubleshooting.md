# Skill Troubleshooting

Named symptom taxonomy for skill discovery and routing problems. Use when a skill isn't firing, the wrong skill is firing, or triggers are colliding.

Source: Anthropic Agent Skills guide (pp.25-27) + this repo's observed failure modes.

---

## Symptom: Skill Won't Trigger

The skill exists, is loaded in the session, but Claude handles the request itself instead of invoking the skill.

**Common causes:**

1. **Description is too vague.** "Helps with backend development" won't fire. The description needs specific trigger contexts — phrases users actually type. Rewrite the description using the 3-slot anatomy in `skill-writer/references/description-patterns.md`.

2. **Description doesn't enumerate the user's actual phrasing.** Claude matches on the description. If the user says "walk me through deploying this" and the description only says "manages the deployment pipeline", the match may fail. Add "walk me through", "step by step", and other natural phrasings as keyword variants.

3. **Body is empty or too short.** A stub body (< 50 words) is a lint warning, but it can also signal that the skill isn't doing enough to be distinguishable from inline handling. Add meaningful instructions.

4. **Skill is not installed in this session.** Run `skill-explorer` to list what's loaded. If the skill doesn't appear, it may not be symlinked. Run `sync-skills` to push it to `~/.claude/skills/` and restart the session.

5. **`disable-model-invocation: true` is set.** Skills with this flag only fire via explicit slash command or orchestrator dispatch — never by auto-trigger. Check the frontmatter.

**Fix checklist:**
- [ ] Is the skill listed when you run `skill-explorer` (catalog mode)?
- [ ] Does the description contain a phrase close to what the user said?
- [ ] Is `disable-model-invocation` set to `false` (or absent)?
- [ ] Run `scripts/lint-skills.sh <path>` — does it pass?

---

## Symptom: Wrong Skill Triggers

A different skill fires when the intended one should. Usually a trigger collision.

**Common causes:**

1. **Overlapping descriptions.** Two skills use the same trigger phrases. Example: both `plan-builder` and `claude-mem:make-plan` describe planning; both fire on "make a plan". The more specific description wins, but if both are generic, the result is unpredictable.

2. **Missing exclusions.** If skill A does everything skill B does plus more, and skill A's description doesn't exclude skill B's use case, A will over-trigger. Add an explicit "Also use when..." / "NOT for..." boundary in the description.

3. **Ambiguous task framing.** The user's phrase is genuinely ambiguous. `skill-explorer` should surface this as a routing question rather than auto-routing. If it's happening silently, the wrong skill's description is too greedy.

**Fix:**
- Add exclusion phrases to the over-triggering skill's description: "Use `skill-B` instead when..."
- Tighten the trigger contexts in the under-triggering skill: be more specific about when it should fire.
- See `routing-table.md` § Disambiguation for known collision pairs and how they're resolved.

---

## Symptom: Skill Triggers Too Often

The skill fires on requests that aren't its domain.

**Common causes:**

1. **Description is too broad.** Trigger contexts that match many unrelated user requests. "Use when working on code" will match almost anything.

2. **Missing "NOT for" boundary.** The description doesn't say what it doesn't cover, so Claude treats it as a default.

3. **Keyword overlap with a high-frequency topic.** If a skill has "review" in its description, it may absorb every "review this code" request even when `code-review` or `git-pr-feedback` would be more appropriate.

**Fix:**
- Add negative trigger guidance: "NOT for single-skill tasks..." or "Use `X` instead when..."
- Tighten trigger contexts: replace "working on" with a specific verb + object.
- For skills that should only fire on explicit slash-command invocation: set `disable-model-invocation: true` in the frontmatter.

---

## Symptom: Instructions Not Followed

The skill triggers correctly but Claude doesn't follow its instructions — it handles the request in a generic way instead.

**Common causes:**

1. **Body is too long.** When the skill body exceeds 5,000 words or 500 lines, parts of it may fall outside the model's effective attention window. Move peripheral content to `references/` and link it explicitly from the relevant step.

2. **Steps are buried in prose.** Numbered steps with imperative voice ("Read the contract", "Run the lint") are followed more reliably than paragraphs of explanation. Restructure.

3. **Model laziness on long outputs.** When a skill asks for a large, multi-section output, the model may truncate or abbreviate. Add explicit encouragement at the step that requires complete output — see `performance-notes.md` for the `## Performance Notes` pattern.

4. **Conflicting instructions.** If the frontmatter's `allowed-tools` restricts a tool the body instructs the model to use, the restriction wins. Align `allowed-tools` with the body's actual tool calls.

**Fix:**
- Run `scripts/lint-skills.sh <path>` — check body word count and line count warnings.
- Move tables, checklists, and templates to `references/`.
- Restructure prose into numbered steps with imperative voice.
- Add explicit performance encouragement if output truncation is the symptom.

---

## Symptom: Large Context / Slow Response

The skill loads into context but makes responses slow or hits context limits.

**Cause:** Too much content in the skill body that loads automatically at trigger time. References are loaded on demand — body content is not.

**Fix:**
- Move detailed tables, long checklists, and technical specs to `references/`.
- Link reference files explicitly from the step that needs them: "Before reporting done, read `references/validation-checklist.md`."
- Check body line count (`scripts/lint-skills.sh` warns at 500 non-blank lines).

---

## Symptom: Skill Not Found After `sync-skills`

The skill appears in the repo but not in `~/.claude/skills/`.

**Common causes:**

1. Symlink target path is wrong — the repo was moved or the skills root changed.
2. `sync-skills` wasn't re-run after adding the new skill directory.
3. The skill directory name doesn't match the `name` field in frontmatter — `lint-skills.sh` would have caught this.

**Fix:**
- Run `sync-skills` from the repo root.
- Confirm `name` in frontmatter matches the directory name exactly (kebab-case).
- Check `~/.claude/skills/` to see if the symlink target resolves correctly (`ls -la ~/.claude/skills/<skill-name>`).

---

## Diagnostic Flow

When a skill isn't behaving, work through this in order:

1. **Is it installed?** `skill-explorer` catalog mode — does it appear?
2. **Is the description specific enough?** Read it as if you'd never seen the skill — would you know exactly when to invoke it?
3. **Is there a collision?** `skill-explorer` route mode — which skill does it recommend for the failing request?
4. **Does lint pass?** `scripts/lint-skills.sh skills/path/to/skill/` — no errors?
5. **Is the body under 500 lines and 5,000 words?** Check with `wc -w` on the body section.
6. **Are references linked and loading?** Confirm the `references/` filenames match what the body links to.
