# Slop pattern catalog

The full catalog behind both layers of prose-slop-guard. Categories mirror
Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
(the community's canonical spec), condensed and tuned for repo prose:
READMEs, docs, announcements, PR bodies, wiki pages.

For every pattern: what it looks like, why it reads as slop, what to write
instead. The lexical checker (`scripts/check_prose_slop.py`) enforces the
mechanical subset; everything marked *(judgment)* belongs to the model pass.

## Contents

1. [Punctuation and mechanics](#1-punctuation-and-mechanics)
2. [Vocabulary](#2-vocabulary)
3. [Phrases and setups](#3-phrases-and-setups)
4. [Structure](#4-structure) *(judgment)*
5. [Rhythm](#5-rhythm) *(judgment)*
6. [Specificity and attribution](#6-specificity-and-attribution) *(judgment)*
7. [Voice and sycophancy](#7-voice-and-sycophancy)
8. [Formatting](#8-formatting) *(judgment)*
9. [The require-list](#9-the-require-list)
10. [Provenance](#10-provenance)

## 1. Punctuation and mechanics

**Em dashes and en dashes** (`—`, `–`) — checker rule `no-em-dash`, error.
The single most-cited AI tell across every source in the research window. AI
prose uses them several times per paragraph where a human reaches for a comma
or parenthesis. Fix: ` - ` (hyphen with spaces), a comma, parentheses, or a
full stop. Exception: quoted content keeps its author's punctuation (the
checker exempts blockquotes); a project whose house style embraces em dashes
can downgrade the rule in `.prose-guard.json`.

**Title Case Headings And Excessive Boldface** *(judgment)* — sentence-case
headings read as human; Title Case everywhere plus bold-scattered-through-body
reads as generated.

## 2. Vocabulary

Checker rule `banned-vocabulary`, warn (words can be legitimate terms of art;
that's why it warns instead of failing, and why `allowVocabulary` exists).

| tell | write instead |
|---|---|
| delve | dig into, examine |
| leverage / utilize / harness | use |
| seamless(ly) | smooth(ly), or cut it |
| tapestry | name the actual things |
| unleash | release, enable |
| elevate | improve, raise |
| landscape | field, space, or the actual market |
| game-changer / groundbreaking / cutting-edge / transformative | state the actual change |
| paradigm | model, approach |
| synergy | say who gains what |
| empower | let, enable |
| streamline | simplify |
| unprecedented | new, first (only if literally true) |
| testament | evidence, sign |
| pivotal | key |
| foster | encourage, build |
| realm | area |
| embark | start |
| boasts | has |
| furthermore / moreover | also, or just start the sentence |

The test for a term-of-art exception: would a practitioner in this domain use
the word to a colleague? "Agent harness" passes; "harness the power of AI"
does not.

## 3. Phrases and setups

Checker rules `banned-phrases` (error) and `negative-parallelism` (warn).

- **Throat-clearing openers** — "In today's fast-paced digital landscape...".
  Delete the sentence; start with the point. If the first sentence of a doc
  could open any doc, it opens none.
- **"Not only X but also Y"** — paired construction that inflates two mild
  claims into fake momentum. Make one direct claim.
- **Negative parallelism** — "It's not just a tool, it's a platform." /
  "This isn't merely about speed." The setup borrows drama the content hasn't
  earned. State the positive claim.
- **"It is worth noting that"** — if it's worth noting, note it.
- **"A testament to"** — state the evidence directly.
- **"Let's dive in" / "Look no further" / "ever-evolving"** — filler; delete.

## 4. Structure *(judgment)*

- **Bullet soup** — bullets where a paragraph would carry the argument. A
  list is for genuinely enumerable, parallel items. If the bullets have to be
  read in order to make sense, they're a paragraph wearing a costume.
- **The three-bullet summary nobody asked for** — a closing recap of a text
  short enough to remember. Delete.
- **Rigid formula** — intro, three body sections of equal length, conclusion
  that restates the intro. Human structure follows the material's shape.
- **Superficial -ing glosses** — trailing participial analysis bolted onto
  facts: "..., highlighting the need for robust solutions", "..., showcasing
  its versatility". The gloss asserts significance instead of demonstrating
  it. Cut the clause or replace it with the actual consequence.
- **Inflated symbolism** — "stands as", "serves as a reminder", "underscores
  the importance of". Ceremony around a fact. State the fact.

## 5. Rhythm *(judgment)*

- **Rule of three** — "fast, simple, and powerful". One triplet is fine;
  triplets as the default rhythm are the tell. Pick the item that matters.
- **Uniform sentence length** — every sentence 15-25 words creates the
  characteristic drone. Vary it. Short lands.
- **Dramatic fragmentation** — "The result? Pure magic." Rhetorical
  question-and-payoff as a repeated device.

## 6. Specificity and attribution *(judgment)*

- **Vague attribution** — "experts say", "studies show", "many users report",
  "it is widely regarded". Name the source or delete the claim. In repo prose
  this usually means: link the issue, the benchmark, the thread, the doc.
- **Hedged everything-ness** — "whether you're a beginner or a seasoned
  expert". Pick the actual audience.
- **False agency** — "the code allows users to...", "the feature enables
  teams to...". Say what it does: "you can...".
- **Unfalsifiable praise** — "robust", "comprehensive", "powerful" with no
  measurable referent. Replace with the number, the list, or nothing.

## 7. Voice and sycophancy

Checker rule `sycophancy`, error (for the fixed phrases); context-level
sycophancy is judgment.

- "Great question", "Excellent point", "You're absolutely right" — filler
  that answers the person instead of the question. Delete; answer directly.
- "I hope this helps", "Happy to help" — closers that add nothing in written
  prose.
- Performative hedging — "It's important to remember that...", "Of course,
  this depends on your use case" repeated as a reflex rather than carrying
  real conditions.

## 8. Formatting *(judgment)*

- Bold scattered mid-sentence for **emphasis** that the sentence should carry.
- Headers on every three paragraphs of a short doc.
- Emoji bullets in technical prose (unless the project's voice uses them).
- Tables for two rows of two cells.

The principle: structure encodes information; when it decorates, it signals
generation.

## 9. The require-list

What the text should read like after the pass:

- Short, active sentences; varied length.
- Direct "you/your" address where the text instructs.
- Concrete examples over abstractions; the command over the description of
  the command.
- Direct claims with evidence; specific attribution (link it).
- Prose paragraphs by default; lists only for parallel enumerable items.
- Sentence-case headings; formatting only where it carries information.

## 10. Provenance

Built from the 2026-09-01 research pass recorded in the repo root's
`anti-slop-writing-research.md` (full link inventory there). Primary sources:

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) - the canonical spec (WikiProject AI Cleanup).
- [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) - 70+ pattern catalog for prose.
- [BioInfo/slopless](https://github.com/BioInfo/slopless) - production CLAUDE.md integration style.
- [adenaufal/anti-slop-writing](https://github.com/adenaufal/anti-slop-writing) - cross-agent system prompt; banned-word replacements; four-question filter.
- The Humanizer skill family ([blader](https://github.com/blader/humanizer), [jooray](https://github.com/jooray/humanizer), [WhimseyAI](https://github.com/WhimseyAI/humanizer-skill), [Aparnabuilds](https://github.com/Aparnabuilds/humanizer)) - Wikipedia-spec implementations.

Patterns were re-derived and re-worded from the public spec and this repo's
research; no upstream text or identity is copied (see ACKNOWLEDGMENTS.md
convention).
