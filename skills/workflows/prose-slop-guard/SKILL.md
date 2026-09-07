---
name: prose-slop-guard
version: 1.0.0
composes_with: ["orchestrator", "docs-agent", "code-review-agent", "git-pr", "wiki-research", "interactive-doc", "llm-wiki", "skill-writer"]
description: >-
  Source-level gate that catches AI-slop prose ("claudenese") before it ships:
  em dashes, AI vocabulary (delve, leverage, seamless, tapestry), negative
  parallelism ("it's not X, it's Y"), throat-clearing openers, sycophantic
  filler, rule-of-three rhythm, bullet soup. Use whenever writing or reviewing
  outward prose — READMEs, docs, announcements, blog posts, PR descriptions,
  wiki pages, marketing copy — before committing or declaring a writing task
  done, when setting up enforcement so slop can't ship again, or as an
  orchestrator/docs-agent wave-gate. Trigger on: "sounds like AI",
  "reads as AI-written", "humanize this", "make it sound human", "de-AI this",
  "too ChatGPT", "AI tells", "AI slop", "claudenese", "stop writing like a
  bot". A deterministic lexical checker plus a judgment rewrite pass; don't
  skip it because it "looks fine" — self-grading is the failure mode this
  guards.
compatibility: Claude Code or any host with Bash; requires Python 3.8+ (stdlib only) for scripts/check_prose_slop.py
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
---

# prose-slop-guard

## The problem this solves

AI-slop prose passes every existing gate. Tests don't read English. Render
review checks pixels. Code review checks logic. A doc full of em dashes,
"delve", and "it's not X, it's Y" ships green — and readers clock it as
machine-written in two sentences, which costs the text its credibility no
matter how correct it is.

Worse, the author-model can't self-grade: the same distribution that produced
the tells rates them as fine. Community consensus (HN, on anti-slop skills)
is blunt about this — filtered output can still read as slop when the filter
and the writer are the same pass.

So the fix is the same shape as `design-token-guard` and
`class-extraction-guard`: a **source-level gate** with a deterministic layer a
hook can run, plus a **fresh-eyes judgment pass** for the tells no regex can
catch. The canonical spec is Wikipedia's
[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
page — the same ground truth the Humanizer skill family builds on — mirrored
and condensed in `references/slop-patterns.md`.

## Layer 1 — Lexical audit (deterministic)

Run the bundled checker from the project root:

```bash
python3 SKILL_DIR/scripts/check_prose_slop.py --root .
```

What it catches (the mechanical tells):

| rule | catches | default |
|---|---|---|
| `no-em-dash` | em/en dashes in prose (use ` - `, comma, or parentheses) | error |
| `banned-phrases` | throat-clearing openers, "not only... but also", "it is worth noting", "a testament to", "let's dive in", "ever-evolving" | error |
| `sycophancy` | "great question", "you're absolutely right", "I hope this helps" | error |
| `banned-vocabulary` | delve, leverage, seamless, tapestry, unleash, harness, elevate, landscape, game-changer, paradigm, synergy, empower, streamline, unprecedented, testament, boasts, furthermore... (each with a plain replacement hint) | warn |
| `negative-parallelism` | "it's not just...", "isn't merely..." setups | warn |

Scoping is prose-aware: fenced code blocks, inline code, link targets, URLs,
YAML frontmatter, and blockquotes are skipped (quoted content keeps its
author's punctuation — an em dash inside a quote is not your finding).

Useful flags:
- `--staged` — only git-staged files (what the pre-commit hook runs).
- `--stdin` — pipe a commit message or PR body through the same rules:
  `git log -1 --format=%B | python3 .../check_prose_slop.py --stdin`
- `--json` — `{ ok, summary, findings }` for a gate/CI to parse.
- `PATHS…` — limit to the files you just wrote.

Exit code `1` on error-severity findings, `0` when clean — drops straight into
a hook or CI step.

## Layer 2 — Judgment pass (model, fresh eyes)

The regex layer cannot see rhythm, structure, or voice. After (or instead of,
for a quick review) the lexical audit, read `references/slop-patterns.md` and
sweep the text for the judgment-level categories:

- **Rule-of-three rhythm** — triplet lists as a crutch ("fast, simple, and
  powerful"). One is fine; a pattern is a tell.
- **Bullet soup / formatting inflation** — bullets, bold, and headers where a
  paragraph would carry the argument. Structure should encode information, not
  decorate it.
- **Vague attribution** — "experts say", "studies show", "many users report"
  with no named source. Name it or cut it.
- **Inflated symbolism** — "stands as", "serves as a reminder", "underscores
  the importance of". State the fact; skip the ceremony.
- **Superficial -ing analysis** — trailing participial glosses ("...,
  highlighting the need for...", "..., showcasing its versatility").
- **Hedged everything-ness** — "whether you're a beginner or an expert".
- **Sycophantic or performative openers/closers** in context the regexes miss.

Rewrite toward the require-list: short active sentences with varied length,
direct "you/your" address, concrete examples over abstractions, specific
attribution, direct claims with evidence, prose paragraphs by default.

**Who runs the judgment pass matters.** If you wrote the text this session, do
not grade it yourself — dispatch a fresh-context reviewer (a subagent that gets
only the text plus `references/slop-patterns.md`, not your drafting context) or
run the lexical checker plus a self-sweep and say plainly that the judgment
pass was self-graded. This is the same evaluator principle as
`loop-controller`'s fresh-context evaluator: the writer's context contaminates
the grade.

## Interpret and fix

Two kinds of findings, different fixes — don't blur them:

- **Mechanical** (em dash, banned word, banned phrase): replace per the hint.
  Safe, fast, no meaning change.
- **Judgment** (rule of three, vague attribution, bullet soup): these usually
  signal a missing fact, not a wrong word. "Studies show" means *go find the
  study or delete the claim*. A triplet means *pick the one that matters*.
  Rewriting the surface while keeping the emptiness is how "humanized" text
  still reads as slop.

**Legitimate exceptions** — leave these alone and, where recurring, encode them
in config: quoted material (already exempt), upstream changelog text,
vocabulary that is a real term of art in the domain ("harness" in an agent
harness, "landscape" in ecology), and any project whose house style explicitly
allows em dashes (`"rules": {"no-em-dash": "warn"}`). The guard serves the
project's voice; it does not impose one.

## Enforce (scaffold into the repo)

A one-time cleanup doesn't stop regression — the next generated README
reintroduces everything. Wire the gate in:

1. **Write `.prose-guard.json`** at the repo root (template:
   `assets/prose-guard.config.json`). Tune rules, add domain terms to
   `allowVocabulary`, scope `extensions`/`skipPaths`.
2. **Add a script entry** — `"lint:prose": "python3 scripts/check_prose_slop.py --root ."`
   (copy the checker into the project's `scripts/` or reference the skill path).
3. **Pre-commit hook** — run `check_prose_slop.py --staged`; block on errors.
   Wire via Husky/lefthook if present, else a plain `.git/hooks/pre-commit`.
4. **CI step** — run `lint:prose` next to lint/typecheck.
5. **Standing style rules** — for repos where agents generate prose routinely,
   add the CLAUDE.md block from `references/wiring-into-agents.md` so the rules
   apply at generation time, not just at gate time. Prevention beats filtering.

Tell the user which layers you installed and which you skipped.

## Using it as an agent / orchestrator gate

- A **docs-agent** (or any agent producing READMEs, docs, PR bodies) runs the
  checker with `--json` against the files it changed *before* reporting done;
  error findings mean the task isn't done.
- The **orchestrator** runs it at the wave gate alongside typecheck/test;
  non-zero `summary.errors` blocks the wave and routes back to the owning
  agent.
- **git-pr** pipes the drafted PR body through `--stdin` before `gh pr create`.
- The **judgment pass** at gate time goes to a fresh-context reviewer, never
  the agent that wrote the text.

Exact snippets: `references/wiring-into-agents.md`.

## Reference files

- `references/slop-patterns.md` — the full pattern catalog by category
  (Vocabulary, Phrases, Structure, Voice, Sycophancy, Rhythm, Specificity,
  Formatting), each with why it reads as slop and what to write instead;
  provenance and upstream sources.
- `references/wiring-into-agents.md` — agent self-check, orchestrator
  wave-gate, git-pr `--stdin` check, the fresh-context evaluator dispatch, and
  the copy-paste CLAUDE.md standing-rules block.
