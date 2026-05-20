# skill-creator Worker Brief (eval-skipped)

You are running the **skill-creator** improvement workflow on a batch of skills. The user's directive: *"run /skill-creator:skill-creator on every skill, minus the eval flow."*

## What skill-creator does on an existing skill (the parts you DO)

Per `skill-creator:skill-creator` documentation, when applied to an existing skill the loop is:

1. **Read the skill** (SKILL.md + every references/*.md)
2. **Read its audit report** for known issues — at `audit/reports/{skill-name}.{md,json}`
3. **Improve** the skill applying these principles:
   - **Generalize from feedback** — make patterns work for many cases, not just one example. Avoid overfit/oppressive MUSTs.
   - **Keep the prompt lean** — remove anything not pulling its weight. Read transcripts/symptoms; if text is making the model waste time, drop it.
   - **Explain the why** — replace ALWAYS/NEVER MUSTs with reasoning. LLMs are smart; they extrapolate from intent.
   - **Look for repeated work** — if every invocation reinvents a helper, bundle it as `scripts/foo.py` and reference it.
4. **Description optimization** — apply skill-creator's description guidance:
   - **Pushy** (combats under-triggering) — over-enumerate trigger contexts, keyword variants, edge phrasings
   - **Action verb at start**
   - **Both what AND when** (all "when to use" lives in description)
   - **Under 1024 chars** (Anthropic hard ceiling — non-negotiable)
   - Target ≤800 chars to leave headroom; never exceed 1024
5. **Progressive disclosure** — keep SKILL.md ≤500 lines; for dense tables / templates / pattern catalogs, extract to `references/*.md` with clear pointers (`see references/X.md for the full table`)
6. **Bump version** — minor bump (X.Y.0 → X.Y+1.0) for skill-creator improvement pass

## What you SKIP (per "minus the eval flow")

- No `evals/evals.json`
- No `eval_metadata.json`, baseline runs, with_skill vs without_skill comparisons
- No `benchmark.json`, no aggregation scripts
- No eval viewer / `generate_review.py`
- No iteration directories, no per-eval grading
- No description-optimization run loop (`scripts/run_loop.py`)
- No blind comparison / `agents/comparator.md`
- No packaging

You're applying improvements directly, then moving on. The user reviews the diff at PR time.

## Per-skill workflow

For each skill in your assigned batch:

1. **Read** `skills/{category}/{name}/SKILL.md` and every `references/*.md` it has
2. **Read** `audit/reports/{name}.md` for the per-dimension scoring + top 3 fixes
3. **Decide** what changes to make based on skill-creator principles + audit findings. For most skills the improvements cluster around:
   - Description: trim to ≤800 chars while preserving pushiness; ensure action verb start; keep all important trigger phrases
   - Body: convert MUSTs/ALWAYS/NEVER to explained reasoning; trim redundancy; ensure imperative voice
   - Progressive disclosure: extract any inline table/template >30 lines to `references/*.md`
   - Frontmatter: add missing optional fields (`compatibility`, `requires_agent_teams`, `min_plan`, `owns` for stateless workflows)
   - Cross-refs: ensure `composes_with` / `spawned_by` resolve (in-repo OR `plugin:skill-name` namespaced)
4. **Apply** with Edit/Write tools
5. **Version bump** (minor: `1.2.1 → 1.3.0`)
6. **Verify** description char count under 1024 (use `awk` or grep)

## Constraints

- **Do NOT touch** any file outside your assigned skill set's `skills/{category}/{name}/` directories
- **Do NOT add** evals/, eval_metadata.json, benchmark.json, scripts/run_loop.py etc. — eval flow is explicitly skipped
- **Do NOT remove** valuable content that was added in the recent ecosystem audit pass (cross-ref fixes, compatibility additions, frontmatter normalization, Step 0 sections, plugin-namespacing)
- **Keep emojis out** (house style)
- **Imperative voice only** ("Read the file", not "the agent should read")
- **No trailing whitespace; all code fences declare a language**

## Reference: how the render-sanity pilot was improved

Look at `skills/workflows/render-sanity/SKILL.md` and its new `references/` directory for an example of what the output should look like:

- Description: 1388 → 1018 chars (pushy preserved, failure-mode enumeration moved to body / references)
- Body: 217 → ~180 lines (smell-pattern table + report template extracted)
- Added optional frontmatter (`compatibility`, `requires_agent_teams`, `min_plan`, `owns`)
- New `references/smell-patterns.md` + `references/report-template.md`
- Version: 1.0.1 → 1.1.0

## What to skip per-skill (when nothing to do)

If a skill is already SHIP-grade (per audit) AND already follows skill-creator principles AND has no missing optional frontmatter, leave it alone. Better to skip than to add churn. Note "no changes needed" in your report for that skill.

## Report

When done, one line per skill: `{name}: {what changed, terse}` or `{name}: no changes — already SHIP-grade`.
