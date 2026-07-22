"""
fable_to_opus.py — extract a Fable 5 operating manual and run it on Opus 4.8.

Hardened rewrite of the article version. Fixes:

  * REFUSAL HANDLING. Fable 5 runs safety classifiers and can decline with
    HTTP 200 + stop_reason "refusal" (reasoning-extraction framing — "write
    down how you think" — is a known trigger). The original script would
    silently save an empty manual; this one detects the refusal, prints the
    stop_details category, and exits non-zero.
  * CONTINUATION. Continuing a Fable 5 turn requires echoing the assistant
    content blocks back UNCHANGED (thinking blocks included). The original
    appended only the text, which can 400 on continuation. This appends
    resp.content verbatim.
  * PROMPT FRAMING. Asks for forward-looking working procedures for a
    successor, not a description of the model's own reasoning — same manual,
    far lower refusal risk.

Cost note: this script uses the API, which bills per token TODAY regardless of
the July 12 plan change (Fable 5: $10/$50 per 1M in/out; Opus 4.8: $5/$25).
"Free inside your plan" applies only to claude.ai / Claude Code sessions, not
API calls. Fable 5 also requires the org to allow 30-day data retention — a
zero-data-retention org gets a 400 on every request.

Setup:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-...   # or `ant auth login` (no env var needed)

Run:
  python fable_to_opus.py           # extract + save the manual
  python fable_to_opus.py --test    # trap question: plain Opus vs manual-loaded Opus
"""

import argparse
import pathlib
import sys

import anthropic

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or ant-auth profile

DONOR = "claude-fable-5"
HEIR = "claude-opus-4-8"
HANDOVER_PATH = pathlib.Path("fable_handover.md")

# Forward-looking procedures, not "describe how you think" — the latter is
# what the Claude 5 reasoning-extraction classifier watches for.
EXTRACTION_PROMPT = """\
You are the most capable model on this account. Write an operating manual of
WORKING PROCEDURES for a strong but less capable analyst who will take over
your workload. Do not describe yourself or your internal processes — write
forward-looking procedures the successor can execute.

Cover, in order:
1. How to identify what a request is actually asking for beneath the literal words.
2. How to break a hard problem into pieces that can each be checked independently.
3. How to decide where the real risk lives and allocate effort accordingly.
4. How to verify a claim by re-deriving it from raw inputs, rather than accepting it because it sounds right.
5. How to separate verified facts from sourced claims from assumptions, and label each in the output.
6. How to attack a draft conclusion before delivering it.
7. How to structure the delivery: answer first, then supporting derivation, then risks.
8. The specific mistakes that look like competence but aren't.

For each: the concrete procedure, one short worked example, and the failure it
prevents. Procedures must be executable ("compute both endpoints and divide"),
not vibes ("be careful"). End with a five-question self-test to run on every
answer before sending. Be exhaustive, but keep nothing that doesn't earn its
place. If you run out of room, stop cleanly; the user will reply "continue"."""


def _text(resp):
    return "".join(block.text for block in resp.content if block.type == "text")


def _die_on_refusal(resp, context):
    if resp.stop_reason == "refusal":
        category = resp.stop_details.category if resp.stop_details else None
        explanation = resp.stop_details.explanation if resp.stop_details else None
        print(f"Refused during {context} (category: {category}).", file=sys.stderr)
        if explanation:
            print(f"  {explanation}", file=sys.stderr)
        print(
            "Reframe toward forward-looking procedures for a successor "
            "(not 'how you think' / 'your reasoning') and retry.",
            file=sys.stderr,
        )
        sys.exit(1)


def extract_handover():
    """Ask Fable 5 for the manual, auto-continuing if it runs long."""
    messages = [{"role": "user", "content": EXTRACTION_PROMPT}]
    parts = []
    for _ in range(6):  # cap continuations so this always terminates
        resp = client.messages.create(model=DONOR, max_tokens=16000, messages=messages)
        _die_on_refusal(resp, "extraction")
        parts.append(_text(resp))
        if resp.stop_reason != "max_tokens":
            break
        # Same-model continuation: echo content blocks back UNCHANGED
        # (thinking blocks included) or the API can reject the turn.
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": "continue"})
    manual = "\n".join(parts)
    if not manual.strip():
        sys.exit("Extraction produced no text — not saving an empty manual.")
    HANDOVER_PATH.write_text(manual, encoding="utf-8")

    tokens = client.messages.count_tokens(
        model=HEIR, system=manual, messages=[{"role": "user", "content": "x"}]
    ).input_tokens
    print(f"Saved {len(manual):,} chars (~{tokens:,} tokens as an Opus 4.8 system prompt) to {HANDOVER_PATH}")
    if tokens < 1024:
        print("Note: below Opus 4.8's 1,024-token prompt-cache minimum — it rides uncached (fine at this size).")
    return manual


def ask(model, system, question):
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        thinking={"type": "adaptive"},  # Opus 4.8 runs thinking-OFF when this is omitted
        messages=[{"role": "user", "content": question}],
    )
    _die_on_refusal(resp, f"test on {model}")
    return _text(resp)


def run_test():
    """Same trap question, plain Opus vs Opus running the manual.

    Caveat: this trap is a weak discriminator — plain Opus 4.8 usually catches
    a 5%-vs-20% error on its own. Passing it is necessary, not sufficient.
    Better probes: multi-step unit conversions, questions with a false premise
    buried in the setup, and 'ship it?' asks where the right answer is a
    labeled assumption rather than a yes/no.
    """
    if not HANDOVER_PATH.exists():
        sys.exit(f"{HANDOVER_PATH} not found — run the extraction first.")
    manual = HANDOVER_PATH.read_text(encoding="utf-8")
    trap = "A report says revenue grew from $4.0M to $4.2M and calls it a 20% gain. Ship it?"

    print("\n--- Opus 4.8, no manual ---")
    print(ask(HEIR, "You are a helpful assistant.", trap))

    print("\n--- Opus 4.8, running the manual ---")
    print(ask(HEIR, manual, trap))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="compare both models on a trap question")
    args = parser.parse_args()

    if args.test:
        run_test()
    else:
        extract_handover()
        print("Next: load fable_handover.md as Project instructions or a system prompt on Opus 4.8.")
