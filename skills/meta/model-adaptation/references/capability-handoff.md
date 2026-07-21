# Capability handoff — extract an operating manual from a stronger model

The technique behind the circulating "clone Fable 5 into Opus 4.8" article,
reviewed, hardened, and adopted here (2026-07-08 maxed-out-window review §4;
intaken as MR-8). One strong model writes an **operating manual of working
procedures** for a cheaper successor; the manual then runs as the successor's
system prompt / project instructions.

**The honest verdict first: the mechanic is real but oversold.** A manual ports
*discipline* — decomposition habits, verification procedures, delivery
structure — not *capability*. A weaker model running the manual still can't do
what it couldn't do; it just stops making the sloppy-process class of mistakes.
That makes this the prompt-level cousin of the **optimizer/target split**
(`model-effort-tiering.md`): author the artifact on the strong tier, execute
under it on the cheap tier — and per SkillOpt's measurement, the weaker
executor gains the most from it.

## What ships with this reference

- **`scripts/extract_operating_manual.py`** — the hardened extractor
  (originally `fable_to_opus.py`). Run it with an `ANTHROPIC_API_KEY`; it asks
  the donor model for the manual and saves it, with `--test` comparing the heir
  model bare vs manual-loaded on a trap question.
- **`references/operating-manual.md`** — a manual already extracted from
  Fable 5 (169 lines, model-portable). Reusable as-is: paste it as a system
  prompt or Claude Project instructions for the model doing the work.
  **On-demand only — do not inject it into Claude Code sessions**; the Claude
  Code harness already covers most of what it says, and doubling it up is
  noise.

## The three hardenings (why not the article's script)

1. **Refusal handling.** The Claude 5 family runs a reasoning-extraction
   classifier: "write down how you think" phrasing can return HTTP 200 with
   `stop_reason: "refusal"`. The article's script silently saved an empty
   manual; ours detects the refusal, prints the category, and exits non-zero.
   (See `refusal-and-fallback.md` — this is the same landmine.)
2. **Continuation.** Continuing a Claude 5 turn requires echoing the assistant
   content blocks back **unchanged** (thinking blocks included). Appending only
   the text can 400 on continuation; ours appends `resp.content` verbatim.
3. **Prompt framing.** Ask for *forward-looking working procedures for a
   successor*, never a description of the model's own reasoning — the same
   manual comes back at far lower refusal risk. This is the documented-fine
   category, not reasoning-transcript extraction.

**Cost note (corrected from the article):** the script uses the API, which
bills per token regardless of any subscription plan — "free inside your plan"
applies only to claude.ai / Claude Code sessions. Fable 5 API access also
requires the org to allow 30-day data retention.

## Unverified claims (flagged, not asserted)

Three API details baked into the script were reviewed as plausible but not
confirmed against current docs — verify before relying on them:

1. `thinking: {"type": "adaptive"}` being accepted by Opus 4.8 (it may be
   Claude-5-family-only).
2. The `stop_details.category` / `stop_details.explanation` response shape on
   refusals.
3. The 4,096-token prompt-cache minimum the script's size note cites.

If one turns out wrong, the script degrades loudly (an API 400), not silently.

## Portability note

`convert.sh` ships skills' `scripts/` directories to other hosts (as of PF1),
so this extractor travels with the skill on per-skill-layout hosts. The script
itself is plain `anthropic`-SDK Python and runs anywhere with an API key.
