---
name: loop-controller
version: 1.1.0
description: >-
  Wrap any task in a verifiable stop condition plus a mandatory guardrail stack
  so an autonomous loop converges instead of thrashing or burning the budget —
  the foundation harness every loop skill composes on. Use whenever you want
  Claude to keep working until something is provably true (tests pass, coverage
  hits a target, a contract's criteria hold, a queue is empty), to schedule a
  recurring check, or to pick the right loop primitive (/goal vs /loop vs
  Stop-hook vs a bash Ralph loop vs a dynamic workflow). Trigger on: "loop
  until", "keep going until", "run until green", "work until done", "autonomous
  loop", "agentic loop", "ralph loop", "/goal", "iterate until", "loop safely",
  "iteration cap", "loop budget", "runaway agent", "overnight build". Read it
  first when authoring any new loop skill.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "Workflow"]
composes_with: ["orchestrator", "fix-until-green", "orchestrator-task-loop", "contract-conformance-loop", "babysit", "coverage-loop", "perf-loop", "self-healing-loop", "migration-loop", "nightly-docs-and-changelog", "dependency-health-loop", "codebase-exploration-loop", "repo-cleanup-loop", "qe-agent", "contract-auditor", "diagnose-loop", "context-manager", "model-adaptation", "find-unknowns", "loop", "schedule"]
spawned_by: ["orchestrator"]
---

# loop-controller

> **Why this is a deliberate (`disable-model-invocation`) skill.** A loop edits,
> commits, and spends tokens on its own. You want to *type* `/loop-controller`
> (or have the orchestrator dispatch it), not have Claude silently start an
> autonomous loop because a test happened to fail. The discipline below is what
> makes that safe.

## The one rule that governs every loop

**A loop is only as good as its stopping condition.** Loops *converge* when
"done" is an external signal the agent cannot argue with — a test exit code, a
coverage percentage, an empty queue, a fresh evaluator's verdict. They *diverge*
— oscillate, thrash, or run the budget to zero — when "done" is a subjective
judgment the agent grades itself on. Agents are pathological optimists about
their own work; left to self-assess, they declare victory early.

There is a subtler failure an objective proof does **not** cure: a signal that
is mechanical, default-FAIL, and un-gameable can still measure the **wrong
thing**. A test suite green against a mock, a stub, or a fixture is all three of
those — and proves nothing about whether the real product works. That is
*convergence on a fiction*, and because it wears the costume of rigor (an exit
code! a number!) it slips past review more easily than a subjective claim would.
65 green tests against a mocked backend look exactly like 65 green tests against
the real one. So the proof must measure the **real goal**, not a stand-in for it
(Step 2) — un-gameable *and* pointed at the thing that actually matters.

So the entire job of this skill is to turn a fuzzy "keep working on X" into a
**convergent** loop: a mechanical proof *of the real goal*, the right execution
primitive, and a guardrail stack that stops the loop whether or not the proof is
ever met.

Everything else here — fix-until-green, coverage-loop, perf-loop — is a *config*
of this harness: a specific proof plugged into the same machinery. Author new
loops against this skill; don't reinvent the loop engine.

## Step 0 — Should this even be a loop?

A loop has real setup cost and its own failure modes; the mistake is looping
things that don't earn one. Before building anything, put the task through four
questions — a "no" on any of them is a strong signal to just do the work manually
(or once) instead:

1. **Does it repeat?** A one-off is usually faster by hand. Loops pay off on work
   that comes back — every PR, every night, every new ticket.
2. **Can "done" be verified mechanically?** If nothing but a human can reject a
   bad result, the human is still the real gate and the loop saves little. This is
   the same requirement as Step 2 — no mechanical proof, no convergent loop.
3. **Can the agent act end-to-end?** If it must stop for permission or missing
   context every few minutes, that's assisted manual work, not a loop.
4. **Is "done" objective?** "Tests pass" / "queue empty" loops; "the design feels
   right" / "the strategy is sound" does not. Subjective, high-stakes, judgment-
   heavy work (architecture rewrites, auth, payments, prod deploys) is where a
   human stays in the driver's seat — keep it manual, or gate it hard (guardrail 4).

Pass all four and the 5-part contract below will fill in cleanly. Fail one and
the honest move is to not build the loop.

## The 5-part loop contract (required)

Before running anything, write the loop's contract. A loop that can't fill in
all five lines isn't ready — the blank is the bug.

| Part | Question it answers | Example |
|---|---|---|
| **trigger** | What starts this loop? | "red CI on branch X" / "every 30m" / "user runs `/fix-until-green`" |
| **action** | What does one iteration *do*? | "run the gate, fix one root-cause failure, re-run the whole gate" |
| **proof** | What mechanical signal proves done? | "`npm test` exits 0 **and** lint exits 0 **and** typecheck exits 0" |
| **memory** | What state survives between iterations? | "`PROGRESS.md`, the feature-list JSON, git history" |
| **stop** | Every way this loop ends | "proof passes **OR** 20 iterations **OR** no-progress for 3 rounds **OR** budget cap" |

The `proof` and `stop` lines are load-bearing. Keep this contract in the loop
skill's body (or at the top of the run) so any reviewer can audit convergence at
a glance. This is the Forward Future "loop library" 5-part schema, adopted as the
required contract. The taxonomy of common loop shapes (fix-until-green,
build-until-spec, refine-until-quality, research, review, migration, coverage,
perf, self-healing, exploration) lives in `references/authoring.md`.

## Step 1 — Choose the primitive

The first decision is *which engine runs the loop*. Get this wrong and you burn
money: a scheduler pointed at finishable work re-runs blindly on the clock; a
"work until done" wrapper pointed at an external poll spins forever.

**The decision rule:** *Are you pushing work to a finish line, or watching for
something to change?*

| If the job is… | Use | Because |
|---|---|---|
| Push to a finish line, proof is **provable from Claude's own output** (test exits 0, git clean) | **`/goal`** | A small fast model judges the transcript each turn; "no" feeds the reason back. The closest native "loop until done." |
| Push to a finish line, proof needs a **script/file/tool check** the model can't just assert | **Stop-hook gate** | A hook runs the real check and blocks exit until it passes — ships *with* the skill. |
| **Watch / poll** for an external change on a cadence | **`/loop`** | A thin scheduler that re-runs a prompt or slash command on an interval; it does not push to a finish line. |
| One big mechanical change across **many files in parallel** | **`/batch` / dynamic workflow** | Fans out across worktree-isolated subagents; compose with the `orchestrator`'s Workflow mode. |
| **Greenfield**, want a fresh context window every iteration | **`claude -p` bash loop (Ralph)** | State lives on disk; each pass starts clean. Needs a sandbox (`--dangerously-skip-permissions`). |

Do not conflate `/goal` (finish line) with `/loop` (watch). They are different
primitives with different failure modes. Full mechanics, constraints, and the
exact invocations for each — including `/goal`'s evaluator-can't-read-files
limit and `/loop`'s session-scope/expiry/no-catch-up rules — are in
`references/primitives.md`. **Read it before authoring.**

## Step 2 — Make "done" mechanical and default-FAIL

A convergent loop needs a proof signal the agent cannot rationalize past.

- **Phrase "done" as an observable.** "all tests in `test/auth` pass and lint is
  clean," not "the auth code looks correct." If the proof is a number, name the
  artifact that produces it (coverage report, benchmark output, the gate's exit
  code).
- **Default-FAIL.** Every criterion starts `false` and only flips on *evidence*.
  Store the criteria as JSON, not prose — a model is far less likely to quietly
  rewrite a JSON `"passed": false` than to soften a sentence. (Anthropic's
  long-running-agent harness stores the feature list as JSON for exactly this
  reason.)
- **Measure the goal, not a stand-in.** An objective signal is necessary but not
  sufficient — it also has to exercise the *real* thing the loop is for. If the
  goal depends on a real dependency (a live service, real data, an integration, a
  deploy) and the proof only touches a mock / stub / fixture of it, the loop will
  converge — green, confident, and wrong. Either the proof exercises the real
  path at least once, or it is *explicitly* labelled scaffold-level ("the mocked
  build is internally consistent") with a separate goal-level proof named. A
  green that came from measuring the stand-in instead of the goal is a coverage
  gap wearing a green badge — the same class of bug as a green that came from
  moving the number instead of fixing the cause (Step 3, guardrail 6), and just
  as much a *finding*.
- **Separate the grader from the doer for any subjective bar.** When "done"
  can't be reduced to an exit code (UI quality, doc clarity, API ergonomics),
  the proof is a **fresh-context evaluator subagent** — spawned with **no
  Write/Edit tools** so it cannot "fix" a failure by lowering the bar, and
  blind to how the work was built so it can't rubber-stamp its own reasoning.
  This is the GAN / Plan-Generate-Evaluate pattern. A same-model critic that
  saw the build approves mediocre work; an external signal (tests) or a fresh
  evaluator is what stops the rubber-stamp. See `references/authoring.md`.

## Step 3 — Install the guardrail stack (mandatory)

Every loop ships with all of these. They are not optional polish — a documented
multi-agent loop ran **11 days and burned tens of thousands of dollars** because
it had observability but no *enforcement*. Alerting is not a guardrail;
termination is.

1. **Iteration cap.** A hard `--max-iterations` (or "stop after N turns" baked
   into the `/goal` condition — `/goal` has no native cap). This is the primary
   backstop when the proof is never met.
2. **Token / cost budget with enforcement.** A ceiling that *terminates* the
   loop, not just warns. `/goal` has no built-in budget — embed a turn cap and
   watch `/cost`; dynamic workflows take an explicit token budget; bash loops
   need an external counter. A 50-iteration run on a large codebase can cost
   $50–100+. The number that actually tells you whether the loop is worth running
   is **cost per *accepted* result**, not tokens spent or iterations run: a loop
   that opens five PRs where you merge one, or emits a daily report no one reads,
   can cost more than doing the work by hand. Track yield, not spend — a low
   accept rate means the loop is manufacturing review debt, and the fix is a
   tighter proof (Step 2), not a bigger budget.
3. **No-progress / oscillation detection.** Stop if iterations stop changing
   state, or if output repeats (≥~90% similarity to a recent iteration), or if
   token use grows quadratically rather than linearly. Thrashing and budget
   exhaustion are the two dominant non-convergence modes — detect both.
4. **HITL checkpoint before anything irreversible.** Pause for a human before a
   DB write, a deploy, an external API call, a force-push. Unattended loops run
   only what is reversible and has a hard verifier.
5. **Checkpoint commits.** Commit working state every iteration with a
   descriptive message. On a wedged codebase, `git reset --hard` to the last
   green checkpoint and re-loop is usually cheaper than rescuing it.
6. **Never let the loop weaken its own gate.** Forbid editing or deleting tests
   to make them pass, silencing a check with an ignore directive, or relocating
   a violation into the checker's blind spot. A green that came from moving the
   number instead of fixing the cause is a *finding*, not a win. When a gate
   flips red→green, read the diff that did it.

The full stack — including the `stop_hook_active` guard for Stop-hook loops, the
oscillation thresholds, and the staged-adoption / rollback ladder — is in
`references/safety.md`.

## Step 4 — Externalize state (so iterations are stateless)

A loop that remembers across iterations only through the conversation breaks the
moment context compacts or a fresh-context pass starts. Externalize to
**path-addressable files**:

- a **progress file** (`PROGRESS.md` / `claude-progress.txt`) — what's done, what's next;
- a **task / feature-list JSON** — the default-FAIL criteria;
- a live **plan/TODO** (`fix_plan.md`) — rewritten freely each pass;
- an **`init.sh`** — how to build and run;
- **git history** — the durable checkpoint trail.

Each iteration starts by *reading* these, does one increment, then *updates*
them and commits. Read the caps (max-iterations, budget) and the state-file
paths from `.claude/profile.yaml` when present, so the same loop skill works
across projects without hard-coding. (This is the orchestrator/role-skill
convention; loops follow it.)

## Step 5 — Run, watch for divergence, know when to kill

- **One task per iteration.** Trust the loop to pick the most important next
  thing; don't batch. Spawn subagents for expensive search/verification, but
  **cap build/test parallelism at 1** — two agents building at once destroy the
  backpressure signal.
- **Re-verify the whole, not just the change.** After each fix, re-run the
  *entire* proof (full suite, every page, the whole rubric), not only the unit
  you touched. "Restart the streak" is how you catch a fix that broke something
  else.
- **Roll a loop back to attended (or kill it) when** any of: token spend grows
  non-linearly, output similarity >90% across iterations, a fresh evaluator and
  your own judgment disagree, or it's about to touch an irreversible resource
  without a checkpoint. A suspiciously easy convergence is itself a finding —
  inspect before trusting.

## Step 6 — Long-run behavioral hygiene (Claude 5 family)

Steps 1–5 make the loop *converge*. This step keeps the **model's behavior** honest over
a long run on the Claude 5 family (Fable 5 / Mythos 5), where a single turn can run for
minutes and an autonomous run for hours. These are prompt-level additions to the loop's
brief — the harness enforces convergence; these keep the agent from lying, quitting early,
or panicking about context on the way there. Drop-in instruction text and the 5-part
mapping for each are in `model-adaptation/references/long-run-hygiene.md`; wire what the
loop needs:

- **Evidence-backed progress (anti-fabrication).** Instruct the agent to audit each
  progress claim against an actual tool result before reporting it. This is *distinct from*
  guardrail 6: guardrail 6 stops the loop from gaming the mechanical *gate*; this stops the
  model from *narrating* work it never verified. Both matter; neither substitutes.
- **Don't end a turn on a promise.** Deep in a run the model can say "I'll now run X" with
  no tool call, or pause to ask when it already has enough. `/goal` + Stop-hooks catch this
  mechanically (Step 1); add the prompt-level last-paragraph self-check and, for unattended
  runs, the autonomous-operation reminder so the agent doesn't lean on the hook.
- **Don't surface the budget countdown to the model.** Guardrail 2 watches `/cost` for
  *enforcement* — but that number is a **harness** stop signal, not something to show the
  model. Seeing a remaining-token countdown makes the Claude 5 family prematurely summarize,
  offer to hand off, or trim its own work. Read the budget from externalized state (Step 4)
  and decide in the harness; if a count must be visible, add the "you have ample context,
  continue" reassurance.
- **Effort per iteration.** Effort is the primary intelligence/latency/cost dial: `high`
  default, `xhigh` for the hardest proof/verify steps, `medium`/`low` for routine passes.
  Lower effort on the Claude 5 family often beats `xhigh` on prior models — reduce it if a
  loop converges but each iteration runs longer than the work needs.
- **Send-to-user for verbatim mid-turn output.** A loop otherwise only speaks by *ending*
  its turn for HITL. For long async loops that must surface a deliverable or a direct answer
  *without* stopping, give the agent a client-side `send_to_user` tool plus the elicitation
  line — never route the model's reasoning through it (that's the `reasoning_extraction`
  refusal landmine; see `model-adaptation`).

The fresh-context evaluator (Step 2) is itself one of these patterns — the guide's
"fresh verifiers beat self-critique" — so it's already wired; just run it *periodically*
on a long build, not only at the end.

## Comprehension debt — the human-side stop condition

Steps 1–6 keep the *machine* honest. There is one failure they don't catch,
because it lands on the human, not the loop: a loop that ships correct, green
diffs faster than anyone reads them. Each merge feels like progress, but the
codebase starts moving faster than the team's understanding of it — the tests
pass, yet nobody can say *why* the code is shaped the way it is. That's
**comprehension debt**, and it's the antidote's mirror image of convergence-on-a-
fiction: there the proof was too weak, here the proof was fine but human
understanding silently fell behind. The bill arrives at the next bug, in a module
no one can reason about.

The guardrails don't fix this because it isn't a convergence problem — it's a
review problem. Keep it in check by keeping loops on **small, readable diffs**,
having a human actually read the diff a red→green flip produced (guardrail 6
already asks for this), and — for any substantial or fully agent-driven change —
running a **comprehension quiz before merge**: `find-unknowns` owns that move
(explain the diff and what it touches, then test that you can pass a quiz on the
non-obvious behavior). Autonomy that outruns understanding isn't a faster team;
it's a deferred debugging session.

## Using it as the harness other loops compose on

Concrete loop skills don't re-implement any of the above — they *fill in the
contract* and inherit the machinery:

- **`fix-until-green`** — proof = test+lint+typecheck all exit 0; primitive =
  `/goal` or a Stop-hook gate; the canonical first instance.
- A new loop = a new `skills/loops/<name>/` whose SKILL.md states its 5-part
  contract, names its proof artifact, and points back here for the guardrails.
  The authoring walkthrough (with the loop taxonomy and a frontmatter template)
  is `references/authoring.md`.

Under the **orchestrator**, loops slot in at two levels: an inner loop per role
(QE runs fix-until-green; performance runs profile-optimize-reprofile) and an
outer loop over the shared task list (re-assign until every task passes its
gate). That orchestrator wiring is a separate, later skill — this foundation is
what it will build on.

## Reference files

- `references/primitives.md` — `/goal`, `/loop`, `/batch`, dynamic workflows,
  Stop-hooks, and the bash-Ralph loop: exact mechanics, constraints, invocations,
  and the implementation-approach tradeoff table. Read before choosing a primitive.
- `references/safety.md` — the full guardrail stack, `stop_hook_active`,
  oscillation/no-progress detection, the cost footguns, and the staged-adoption
  and rollback ladder.
- `references/authoring.md` — the 10-archetype loop taxonomy, the fresh-context
  evaluator / default-FAIL pattern in detail, and a step-by-step template for
  writing a new loop skill that composes on this one.
