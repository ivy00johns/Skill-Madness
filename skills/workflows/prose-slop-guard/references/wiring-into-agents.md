# Wiring prose-slop-guard into agents and gates

Snippets for the four integration points: agent self-check, orchestrator
wave-gate, git-pr body check, and the fresh-context judgment reviewer. Plus
the standing CLAUDE.md block for prevention at generation time.

## 1. Agent self-check (docs-agent, or any agent shipping prose)

Before reporting a writing task done, the agent runs the checker against
exactly the files it touched:

```bash
python3 SKILL_DIR/scripts/check_prose_slop.py --json README.md docs/guide.md
```

Parse the JSON: `ok: false` (any error-severity finding) means the task is
not done — fix per the hints and re-run. Warnings are surfaced in the agent's
report but don't block. This mirrors the design-token-guard /
class-extraction-guard self-check contract, so an orchestrator can treat all
three guards uniformly.

## 2. Orchestrator wave-gate

At the wave gate, alongside typecheck/test/design-token checks:

```bash
python3 SKILL_DIR/scripts/check_prose_slop.py --root . --json > /tmp/prose-gate.json
python3 -c "import json,sys; d=json.load(open('/tmp/prose-gate.json')); sys.exit(1 if d['summary']['errors'] else 0)"
```

Non-zero exit blocks the wave; route the findings back to the agent that owns
the flagged files (ownership per the orchestrator's file-ownership map — prose
findings in `README.md` go to docs-agent, findings in a PR body go to the
authoring agent).

Definition-of-Done line this closes: *"Outward prose (README, docs,
announcements, PR bodies) passes prose-slop-guard: zero error-severity lexical
findings, and a fresh-context judgment pass found no structural slop."*

## 3. git-pr: gate the PR body

Before `gh pr create`, pipe the drafted body through the same rules:

```bash
printf '%s' "$PR_BODY" | python3 SKILL_DIR/scripts/check_prose_slop.py --stdin
```

Same for commit messages when a repo wants it:
`git log -1 --format=%B | python3 SKILL_DIR/scripts/check_prose_slop.py --stdin`.

## 4. Fresh-context judgment reviewer

The writer must not grade its own prose — the distribution that produced the
tells rates them as fine. Dispatch a reviewer subagent whose entire context is
the text plus the pattern catalog, none of the drafting history:

> Read `references/slop-patterns.md` in the prose-slop-guard skill. Then read
> ONLY the file(s) listed below and review them against the judgment-level
> categories (Structure, Rhythm, Specificity, Voice, Formatting). For each
> finding: quote the passage, name the category, and give a concrete rewrite.
> End with a verdict: SHIP or REVISE. Do not fix the files; report only.
>
> Files: {paths}

Rules of engagement:

- The reviewer gets file paths, not pasted drafts, so it can't inherit the
  writer's framing.
- REVISE verdicts route back to the writer with the findings; the reviewer
  never edits (writer fixes forward, reviewer re-checks).
- In a solo session with no subagent budget, run the lexical checker, do a
  self-sweep against the catalog, and say plainly in the report that the
  judgment pass was self-graded. Honest degradation beats fake independence.

## 5. Standing CLAUDE.md block (prevention at generation time)

For repos where agents routinely generate prose, filtering after the fact is
the expensive path. Add this to the project's CLAUDE.md so the rules apply
while writing:

```markdown
## Prose style (enforced by prose-slop-guard)

Outward prose (README, docs, announcements, PR bodies) follows these rules:

- No em or en dashes: use " - ", a comma, or parentheses.
- No AI vocabulary: delve, leverage, utilize, seamless, tapestry, harness,
  elevate, landscape, game-changer, paradigm, synergy, empower, streamline,
  unprecedented, testament, boasts, furthermore, moreover.
- No setups: "not only... but also", "it's not just X, it's Y", "in today's
  ...", "it is worth noting", "a testament to", "let's dive in".
- No vague attribution: name the source and link it, or cut the claim.
- Short active sentences, varied length. Direct "you" address. Concrete
  examples. Prose paragraphs by default; lists only for parallel items.
- Sentence-case headings. Formatting carries information or gets cut.

Gate: `python3 scripts/check_prose_slop.py --staged` must pass before commit.
```

Tune the vocabulary line to the project (drop words that are terms of art
here; the config's `allowVocabulary` should match).

## 6. Known limitation (encode it, don't hide it)

A pattern filter makes text pass the filter; it does not make text good.
Community experience with anti-slop skills says filtered output can still
read as slop when the underlying content is empty — the vague claim rewritten
in plain words is still vague. That's why the judgment pass focuses on
missing facts (find the study, pick the item that matters, link the source)
rather than surface substitution, and why the reviewer is fresh-context. When
a text passes both layers but still feels off, the problem is usually the
content, not the prose — say so.
