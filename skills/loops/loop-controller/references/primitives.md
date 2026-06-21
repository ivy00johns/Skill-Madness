# Loop primitives — mechanics, constraints, and how to choose

The five native ways to run an autonomous loop in Claude Code, plus the bash
"Ralph" loop. Pick by the decision rule in SKILL.md Step 1, then use the exact
mechanics here. **Version- and plan-dependent — verify against your build;** the
version floors below were current at research time (Opus 4.8 / Fable 5 era).

## Contents
- [`/goal` — the "loop until done" wrapper](#goal)
- [`/loop` — the scheduler](#loop)
- [Stop / SubagentStop hooks — the gate that ships with a skill](#stop-hooks)
- [`/batch` and dynamic workflows — fan-out](#batch-and-dynamic-workflows)
- [The bash "Ralph" loop — fresh context every iteration](#ralph)
- [Implementation-approach tradeoff table](#tradeoffs)

---

## /goal

The real "loop until done." Requires Claude Code **v2.1.139+**.

You set a completion condition. After each turn a **small fast model (defaults
to Haiku)** judges from the transcript whether the condition holds, returning
yes/no + a reason. "No" feeds the reason back as guidance for the next turn;
"yes" clears the goal. It is a wrapper around a session-scoped, prompt-based Stop
hook.

**The critical constraint:** the evaluator **does not run tools or read files** —
it judges *only what Claude has surfaced in the conversation*. So the condition
must be phrased as something Claude's own output can demonstrate:

- ✅ `"npm test exits 0 and git status is clean"`
- ✅ `"every acceptance criterion in DESIGN.md is shown satisfied, or stop after 20 turns"`
- ❌ `"the code is correct"` (nothing in the transcript proves it)

Other mechanics:
- Condition up to **4,000 characters**; **one goal per session** (a new `/goal`
  replaces the old); `/goal clear` cancels.
- **No built-in token budget.** It runs until the condition is met or you
  Ctrl+C. Embed a turn cap *in the condition* (`"… or stop after N turns"`) —
  this is the official recommendation, and your iteration-cap guardrail.
- Works interactive, headless (`claude -p "/goal …"`), desktop, and Remote
  Control. The recommended unattended combo is **auto mode + `/goal`**: auto mode
  removes per-tool prompts, `/goal` removes per-turn prompts.
- Requires accepting the workspace-trust dialog; unavailable if
  `disableAllHooks` or `allowManagedHooksOnly` is set.

Anthropic's canonical use cases: migrate a module until every call site compiles
and tests pass; implement a design doc until all acceptance criteria hold; split
a large file until each module is under a size budget; work a labeled-issue
backlog until empty.

## /loop

A scheduler, **not** a "loop until done." A bundled skill that re-runs a prompt
or slash command on a cron interval. Requires **v2.1.71/72+**.

```
/loop 5m check if the deploy finished
/loop 20m /review-pr 1234          # schedule ANY slash command or skill
/loop 30m /slack-feedback
```

This is the key composition point — **skills + loops**. Boris Cherny's
documented daily setup: `/loop 5m /babysit` (auto-address review comments,
auto-rebase PRs) and `/loop 30m /slack-feedback`.

Mechanics:
- Interval = number + unit (`s` rounds up to 1 min, `m`, `h`, `d`); **default 10
  minutes**. Omit the interval and Claude picks a **dynamic self-paced delay
  (1 min–1 hour)** based on what it observed, or runs `loop.md` if present.
- **Session-scoped** — dies when you close the terminal.
- **No catch-up** — fires once when idle, not once per missed interval.
- **Auto-expires after 3 days** (some docs say 7 — treat **3 days** as the safe
  assumption and verify on your version).
- Max **50 scheduled tasks** per session; **Esc** clears the pending wakeup.
- It does **not** automate Claude's internal agentic loop — it's a thin
  scheduler that periodically restarts that loop from the outside.
- Disable entirely with `CLAUDE_CODE_DISABLE_CRON=1`.

## Stop hooks

The gate that ships *with* a skill. A **Stop / SubagentStop** hook intercepts the
agent trying to exit; returning `decision: "block"` (or exit code 2) forces it to
keep working until a real condition clears — "don't stop until tests pass."

- A Stop hook declared in a skill/agent's frontmatter is **automatically
  converted to SubagentStop** when that agent runs as a subagent — so a loop gate
  travels with the skill into orchestrated builds.
- The hook can be a **script** (run the real check, block on non-zero) or a
  **prompt/agent** evaluation (`{"type":"prompt","prompt":"Evaluate if Claude
  should stop: $ARGUMENTS"}`) — the latter is how `/goal` is implemented under
  the hood.
- **MUST guard `stop_hook_active`** in the hook payload. A hook that always
  blocks is an infinite loop; check the flag and let the stop through once the
  condition is genuinely met.
- Related lifecycle hooks for orchestrated loops: **TaskCompleted** (a
  validation gate — exit 2 rolls a task back), **TeammateIdle** ("assign new
  work" — keeps an outer loop fed).

This repo already ships a hooks layer (`hooks/`, e.g. the `qa-gate` Stop hook).
A loop skill's gate plugs in the same way.

## /batch and dynamic workflows

Fan-out, not convergence-in-place.

- **`/batch`** spreads one large change across **5–30 parallel worktree-isolated
  subagents**, each opening a PR.
- **Dynamic workflows** (debuted as a research preview at CLI **v2.1.154**; the
  opt-in keyword was renamed `workflow` → **`ultracode`** at v2.1.160, and the
  feature ships default-on for Max/Team/API at v2.1.170 / Fable 5): Claude writes a
  **JavaScript orchestration script** that fans out across up to **1,000
  subagents (16 concurrent)**, keeping intermediate results in script variables
  (not context). Primitives: `agent()` (one subagent, optional JSON-schema-
  validated output), `parallel()` (barrier — awaits all), `pipeline()` (stream
  items through stages, no barrier), with `isolation: 'worktree'` and a token
  budget. Named patterns: **fan-out → reduce → synthesize**, **judge panel**,
  **loop-until-dry** (spawn finders until K rounds find nothing new).

In this repo, **don't hand-roll this** — it's the `orchestrator`'s Workflow mode
(ultracode). A migration/fan-out loop composes the orchestrator rather than
writing its own JS. Caveat: workflows are "meaningfully more usage" — one
developer spawned 90 review agents and hit monthly token limits. Budget hard.

## Ralph

The bash loop — `while :; do cat PROMPT.md | claude -p ; done` — Geoffrey
Huntley's pattern, the philosophical root the native commands absorbed.

Use it when you want a **genuinely fresh context window every iteration** (state
lives entirely on disk, so context never overflows) — primarily **greenfield**
bootstrapping. Hard-won principles worth carrying into any loop:

- **"Deterministically bad in an undeterministic world"** — failures are
  predictable; tune the prompt ("erect a sign") each time it falls off the slide.
- **One thing per loop.** Trust the loop to pick the most important thing.
- **Primary context as scheduler** — spawn subagents for expensive work; cap
  build/test parallelism at 1 to preserve backpressure.
- **File-system-as-memory** — `fix_plan.md`, `@AGENT.md`, `specs/*`; state and
  git history survive between fresh-context passes.
- **Backpressure is the engineering** — wire in type checkers, tests, scanners;
  "the wheel has got to turn fast."
- **Anti-cheating** — Claude is biased toward placeholder/minimal
  implementations; prompt emphatically against stubs and run a separate pass to
  hunt them down.

Requires `--dangerously-skip-permissions` → **must run sandboxed** (Docker / a
throwaway box). No native budget — wrap an external iteration + token counter.
Huntley's own caveat: Ralph is greenfield-only and gets "~90% done"; senior
judgment is still required. The official `ralph-loop` plugin implements the same
idea via a Stop hook with `--completion-promise` (exact-string match) and
`--max-iterations` (the real safety mechanism).

## Tradeoffs

| Approach | Mechanism | Best for | Tradeoff |
|---|---|---|---|
| **`/goal`** | Haiku evaluator loops turns until a transcript-provable condition holds | "work until correct" where done is provable from output | evaluator can't read files/run tools; no built-in budget |
| **Stop/SubagentStop hook** | hook blocks exit until a script/prompt condition passes | deterministic gates ("tests must pass"); ships with the skill | must guard `stop_hook_active`; always-block = infinite loop |
| **`/loop` + skill** | scheduler re-runs a slash command on an interval | recurring/poll workflows (babysit PRs, nightly sweeps) | session-scoped, ~3-day expiry, no catch-up |
| **`/batch` / dynamic workflow** | fan-out across worktree subagents | large parallel migration/research/review | token-hungry; research preview; use via orchestrator |
| **bash Ralph** | `while :; do claude -p < PROMPT.md ; done` | greenfield, fresh context per iteration | needs sandbox; no native budget; ~90% done |

**Fresh-context vs same-session:** Stop-hook loops continue the *same* session
(risking context overflow + lossy compaction); the Ralph school **restarts each
iteration with clean context**, reading state from disk. For long migrations,
prefer fresh-context-per-task; for short refine loops, same-session is fine.
