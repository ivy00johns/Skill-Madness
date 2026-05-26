# Contradiction finding

A thinking move for surfacing where sources disagree before producing a synthesis.

When synthesizing three or more sources, claims that *look* compatible are often in tension: one source counts a feature as a strength, another treats the same feature as a liability; one puts a number at X, another at 2X. Skipping this move produces confident-sounding summaries that are actually averaging over a real debate.

## The move

Work through this sequence after reading all sources and before writing any synthesis:

1. **Surface consensus first.** List the 2-3 claims all sources agree on. This anchors the synthesis and makes contradictions stand out sharper.
2. **Name three specific contradictions.** Find three places where two or more sources give meaningfully different answers to the same question — different numbers, different causal stories, opposite recommendations. If you can only find one, keep looking; surface-level agreement often hides disagreement at one level of abstraction deeper.
3. **Find the weakest claim.** Which single claim in your source set has the thinnest support — cited by only one source, unfalsifiable, or dependent on a hidden assumption? Flag it.
4. **Identify the real debate.** Is the disagreement a factual dispute (different data), a framing dispute (same data, different conclusions), or a values dispute (different priorities)? Naming the type of disagreement tells you what evidence would actually resolve it.
5. **Deliver a confidence verdict.** Before writing the synthesis, state: "High confidence on X, low confidence on Y, genuine open question on Z." This prevents the synthesis from projecting false certainty onto contested claims.

## When to use it

- Synthesizing research from 3+ sources
- Summarizing a technology landscape or vendor comparison
- Producing a recommendation based on multiple reference documents
- Any time the sources come from different authors with different incentives

## What it prevents

Without this move, a synthesis tends to:
- Pick the first coherent narrative it finds and fit everything else around it
- Launder contested claims as settled facts
- Miss the real debate because it was framing-level, not data-level

## Worked example

Three sources discuss database choice for a new service. Source A recommends Postgres for ACID guarantees. Source B recommends DynamoDB for throughput at scale. Source C recommends Postgres for developer experience. Running the move:

1. **Consensus:** All three agree the service will have relational data and needs durability.
2. **Contradictions:** (a) A and C say Postgres, B says DynamoDB — disagree on primary criterion. (b) B projects 10M req/day; A and C never mention that number — disagree on scale assumptions. (c) B treats ops burden as negligible; A and C don't address it at all.
3. **Weakest claim:** B's 10M req/day projection — single source, no cited data.
4. **Real debate:** Framing dispute: A and C are optimizing for correctness and developer speed; B is optimizing for throughput. They are answering different questions.
5. **Verdict:** High confidence that Postgres fits current requirements. Low confidence that the throughput projection is real. Open question: if B's scale assumption is correct, the answer flips — this is the key thing to validate before deciding.
