# DeepSeek adaptation — the cross-vendor landscape

Depth for the model-adaptation SKILL.md's DeepSeek coverage. Everything here is
model- and pricing-specific and therefore **ages** — re-verify against the
[DeepSeek API docs](https://api-docs.deepseek.com/) on every model release, the
same cadence as the *Current landscape* table and the priced Anthropic ladder.

Facts below verified **2026-08-16** against
[Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) and
[Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/).

## Why DeepSeek is in scope

The toolkit runs cross-vendor in practice: the 2026-08-03 deep-dive vendor
review (DV-1–DV-5) was a **Freebuff/DeepSeek session** — the repo's own skills
(plan-intake, living-plan, qa-gate, …) executed under a DeepSeek model. The
tiering doctrine's "never cross-vendor" always meant *don't mix vendors to save
tokens*, but it read as "don't run on DeepSeek at all." This file makes the
declared-provider shape explicit for DeepSeek and records what actually differs
from the Anthropic baseline.

## Current DeepSeek landscape (2026-08)

| Model | Model version | Role today | Off-peak $/1M (in miss / out) |
|---|---|---|---|
| `deepseek-v4-flash` | DeepSeek-V4-Flash-0731 | Cheap tier | $0.22 / $0.66 |
| `deepseek-v4-pro` | DeepSeek-V4-Pro-0813 | Top tier | $0.66 / $1.98 |

Shared facts:

- **Context 1M, max output 384K** across the family — long-horizon runs have
  more headroom than Claude 5, so long-run-hygiene's context-budget reassurance
  is even less pressing here.
- **Cache-hit input is ~30× cheaper than cache-miss** (flash: $0.007 vs $0.22
  off-peak). The dominant cost lever on DeepSeek is **prompt-cache hits**, not
  output trimming — keep the shared prefix (system prompt, skill bodies, tool
  definitions) byte-stable across turns.
- **Peak pricing**: 01:00–04:00 and 06:00–10:00 UTC are peak (2× off-peak);
  all other hours are off-peak.
- Both models support **JSON output, tool calls, the Responses API, and an
  Anthropic-format endpoint** (`https://api.deepseek.com/anthropic`) — Claude-
  shaped tool calls and effort params work directly, which is the mechanism that
  lets Claude-shaped scaffolding run on DeepSeek with least friction.
- Legacy aliases `deepseek-chat` / `deepseek-reasoner` (V3.1-era names) map to
  non-thinking / thinking modes; the current family is exposed as
  `deepseek-v4-flash` / `deepseek-v4-pro`.

## Thinking mode — the capability dial

On Anthropic, model + effort are two dials. On DeepSeek the primary capability
dial is **thinking mode + effort**:

- Thinking is **on by default**, default effort `high`.
- Toggle/effort controls:
  - OpenAI format: `extra_body={"thinking": {"type": "enabled|disabled"}}` +
    `reasoning_effort: low|high|max`.
  - Anthropic format: `{"reasoning": {"effort": "none|low|high|max"}}` —
    **`none` disables thinking**.
- **Effort mapping**: requested `low`→`low`, `medium`→`high`, `high`→`high`,
  `xhigh`→`high`, `max`→`max`. There is no `medium` effort on the wire, and
  `xhigh` is silently mapped to `high`.
- The chain of thought arrives in **`reasoning_content`**, a sibling of
  `content` at the same level — never in the answer text.
- In thinking mode, `temperature`, `top_p`, `presence_penalty`, and
  `frequency_penalty` are **accepted but ignored** (no error).
- **Tool calls work in thinking mode** (multiple reasoning+tool turns per
  request). When a turn includes tool calls, the assistant's `reasoning_content`
  **must** be passed back on all subsequent requests in that turn chain — the
  API returns a 400 if you drop it. Between user turns *without* tool calls,
  prior `reasoning_content` is ignored and does not need to be persisted.
  → Any harness (loop-controller Step 6, use-freellmapi, custom relay code)
  that relays DeepSeek turns must carry the reasoning channel, not just
  `content` + `tool_calls`.

## How the tiering doctrine instantiates on DeepSeek

The shape — cheapest-that-clears-the-bar for grunt, top tier for the reasoning
gate — maps onto the two-model family + thinking toggle:

| Task class | DeepSeek instantiation |
|---|---|
| Mechanical / high-volume | `deepseek-v4-flash`, thinking off (or low) |
| Standard implementation | `deepseek-v4-flash` thinking on (high), or `deepseek-v4-pro` thinking low/high |
| Load-bearing reasoning | `deepseek-v4-pro`, thinking high/max |

Provider-relative: a project that declares `provider: deepseek` (`.claude/
profile.yaml`) runs the **whole** toolkit on the DeepSeek ladder and never mixes
in Anthropic models to save tokens — same rule as the Anthropic-native default,
now explicit per vendor. FreeLLMAPI remains the only *aggregating* carve-out.

## What's different vs Anthropic (the adaptation map)

| Anthropic fact | DeepSeek fact | Toolkit move |
|---|---|---|
| `reasoning_extraction` refusal classifier | No such classifier; CoT is a separate `reasoning_content` channel | Keep the "never narrate reasoning into the response" rule for **cost + answer quality** (thinking mode already emits CoT; echoing doubles output and buries the answer), not for refusal avoidance. Read `reasoning_content` / structured thinking instead. |
| Refused request reroutes to Opus 4.8 | No Opus fallback; DeepSeek has its own alignment filters | The orchestrator/loop "refusal reroute contract" is Claude-specific. On DeepSeek, retry **within the ladder**: toggle thinking, switch flash↔pro. Never cross vendors as a fallback. |
| Effort dial `low–max` (+`xhigh`) | `low/high/max` (+`none` = thinking off); `medium`→`high`, `xhigh`→`high` | Don't emit `xhigh`/`medium` on DeepSeek (both map to `high`). The practical dial is `none/low/high/max`. |
| Output tokens cost 5× input → trim output | Output ≈ 3× input (cache miss); cache-hit input ~30× cheaper | For DeepSeek projects the dominant lever is **prompt-cache hits**: keep the shared prefix byte-stable. Stable scaffolding beats output-trimming here. |
| No thinking toggle in the API | Thinking toggle + effort **is** the capability dial | Use "thinking off" for cheap grunt instead of switching to a separate cheap model — the same model, cheaper. |
| Extended-thinking budgets / summarized thinking | 1M context / 384K output, CoT fully returned via `reasoning_content` | Even more long-run headroom; harness must handle the reasoning channel on tool-call turns (400 otherwise). |
| Image-proxy allowlist: Fable/Mythos pass the glyph sweep | DeepSeek V4 models **unlisted → not allowed** (fail-closed default) | Run the pxpipe ~20-call glyph sweep on V4 flash/pro before enabling the image proxy in a DeepSeek session. |

## Image-proxy status

`use-pxpipe` treats the allowlist in `model-effort-tiering.md` as its safety
gate. DeepSeek V4 (flash and pro) are currently **not allowlisted** — they
default to *not allowed* behind the image proxy until they pass the dense-glyph
sweep. This matters because a DeepSeek session is a plausible proxy candidate:
the model is cheap, so the pxpipe token-saver proxy's *session* economics look
different — the proxy trades image tokens for input tokens, and DeepSeek's
cache-hit input is already ~30× cheaper. Run the sweep and measure read
fidelity before enabling; a model that misreads dense glyphs produces confident
wrong answers from garbled input.

## Audit additions for DeepSeek runs

When reviewing a skill for DeepSeek execution (or a DeepSeek session is the
consumer), check:

1. **Model IDs.** No `claude-*` model IDs as required tiers; tier by role with
   the DeepSeek ladder (flash/pro × thinking mode).
2. **Narrated reasoning.** Same grep as the Anthropic landmine — hits that
   route reasoning into the response are wrong on DeepSeek too (cost + answer
   quality), they just won't trip a refusal. The canonical sweep lives in
   `refusal-and-fallback.md`; the *why* differs by vendor but the instruction
   is identical.
3. **Effort.** Don't emit `xhigh`/`medium`; emit `none/low/high/max`.
4. **Refusal fallback.** Any "reroute to Opus" language is Claude-specific; on
   DeepSeek the retry is within-ladder.
5. **Portable surface.** `requires_claude_code: false` skills are the DeepSeek
   surface (the 2026-07-03 full-library review, SR1, counted ~14 portable vs
   57 Claude-Code-only) — they must not *require* Claude-only tools (Task,
   Artifact). Advisory mentions of Claude Code are fine.

## Wiring into consumers

- **loop-controller (Step 6) / orchestrator role dispatch** — already point at
  the tiering doctrine; on a DeepSeek project they resolve models + effort via
  this file's ladder instead of the Anthropic one.
- **use-freellmapi** — unchanged (the only aggregating carve-out); a DeepSeek
  *project* is not a FreeLLMAPI project and stays on the DeepSeek ladder.
- **use-pxpipe** — checks the image-proxy allowlist in `model-effort-tiering.md`;
  DeepSeek models are not allowed until they pass the glyph sweep.
