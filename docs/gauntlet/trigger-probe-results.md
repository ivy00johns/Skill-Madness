# Trigger probe results — 2026-10-06

The first cross-model run of `scripts/gauntlet/trigger-probe.py`, after the
description fixes and the work-scoring change landed.

## Method

- **Host:** Hermes, in `isolated-home` mode. The probe installs all 78 on-disk
  skills into a scratch `HERMES_HOME`, so the injected skill index is the only
  catalog in play.
- **Models:** `deepseek-v4-flash` and `gemini-3-5-flash`.
- **Rows:** the sixteen skills that failed or wavered in the first probe pass —
  the five `explicit` rows (`code-review-agent`, `frontend-agent`,
  `loop-controller`, `perf-loop`, `zoom-out`) plus `context-manager`,
  `grill-me`, `living-plan`, `model-adaptation`, `orchestrator`, `render-sanity`,
  `skill-catalog`, `skill-explorer`, `skill-review`, `skill-update` and
  `skill-writer`.
- **Prompts:** the matrix positive trigger for each row, run once
  (`--repeat 1`). Selection is stochastic, so a single miss is a signal to
  investigate, not a verdict.
- **Verdicts:** `PASS` = the skill loaded; `WORKED` = it did not load but the
  host did the requested work; `MISS` = neither.

## Roll-up (first run)

| Model | PASS | WORKED | MISS | FALSE_POSITIVE | BLOCKED |
|---|---|---|---|---|---|
| deepseek-v4-flash | 11 | 1 | 4 | 0 | 0 |
| gemini-3-5-flash | 15 | 1 | 0 | 0 | 0 |

## Skills that fire for one model but not the other

Every difference runs in the same direction: Gemini selects these and DeepSeek
does not. No skill fired for DeepSeek but not Gemini.

| Skill | Mode | deepseek-v4-flash | gemini-3-5-flash | DeepSeek outcome |
|---|---|---|---|---|
| code-review-agent | explicit | MISS | PASS | asked for a diff instead of loading the skill |
| grill-me | must_fire | MISS | PASS | asked for the missing input instead of interviewing |
| model-adaptation | must_fire | MISS | PASS | refused; loaded sibling plan skills instead |
| render-sanity | must_fire | MISS | PASS | refused; loaded diagnose-loop and playwright instead |

This is worth a description pass: DeepSeek reads each of these prompts as a
request for an artifact it does not have, while Gemini loads the skill and
proceeds.

## Fix pass

Each of the four misses had a real cause, and in every case the fix belonged to
the skill, the trigger prompt, or the probe rather than to the model.

| Skill | Root cause | Fix |
|---|---|---|
| grill-me | The probe read the first interview question as a request for input because the answer ended in `?`. | `assess_work` now only treats a concrete artifact request (paste / provide / point me to / clarify) as a punt; a question can be the work itself. |
| code-review-agent | The trigger dangled a diff the probe never supplies, so the host asked for one. | The description front-loads "load this for any review request even when no diff is pasted; it locates the change itself", and the matrix trigger carries a small inline diff. |
| model-adaptation | The trigger named a brief that was never attached; the host asked for it instead of loading the skill. | The description front-loads "adapts whatever is in context; when nothing is supplied it emits the per-cell rules". |
| render-sanity | The skill hard-requires a browser, so a Playwright-less host refused instead of loading it. | The description now front-loads a checklist framing: apply it with whatever tools the host has and report checks it cannot run as `BLOCKED`, never decline for lack of a browser. |

### The four rows, before and after

The `after` columns are the group verdict over three reps per model, except
where noted below.

| Skill | deepseek before | deepseek after | gemini before | gemini after |
|---|---|---|---|---|
| code-review-agent | MISS | WORKED | PASS | WORKED |
| grill-me | MISS | WORKED | PASS | PASS |
| model-adaptation | MISS | PASS | PASS | PASS |
| render-sanity | MISS | FLAKY (1 PASS / 2 MISS) | PASS | PASS |

The other twelve probed skills are untouched by this pass; their first-run
results stand.

DeepSeek's `render-sanity` result was flaky on Venice, not fixed: one rep loads
the skill, two refuse. Its final checklist rewording could not be re-verified on
Venice `deepseek-v4-flash` because that provider ran out of credit mid-pass
(`HTTP 402`), which the probe reports as `BLOCKED`, never as a pass. Gemini
loads it in all three reps. The follow-up run below re-checks the rewording on
DeepSeek's own API.

## Redundant on an index-injecting host

`skill-explorer` scored `WORKED` on both models: neither loaded it, and both
answered the routing prompt from the injected index. Under the old load-only
score that read as a failure; the work signal now reports it as served.

## Follow-up: render-sanity on DeepSeek, via the direct API

Venice credits were still exhausted on the re-check date, so the exact
`deepseek-v4-flash` row could not be re-run. DeepSeek's own API (`provider:
deepseek`, `https://api.deepseek.com/v1`) was reachable and serves
`deepseek-flash` — DeepSeek-V4.1-Flash, a point release of the same family, not
the identical weights Venice resells. The probe was pointed at it with a
seed config (`model.provider: deepseek`, `model.default: deepseek-flash`) and
`render-sanity` was probed on its matrix trigger across three runs: three reps
(`gauntlet-probe-2026-10-07T01:47:21Z`), a single rep, and then six more.

| Run | Reps | PASS | MISS | Verdict |
|---|---|---|---|---|
| direct, 3 reps | 3 | 3 | 0 | PASS |
| direct, 1 rep | 1 | 0 | 1 | MISS |
| direct, 6 reps | 6 | 4 | 2 | FLAKY |
| **combined** | **10** | **7** | **3** | **FLAKY (~70%)** |

**The checklist rewording helps but does not make it reliable.** The first
three-rep run scored a clean 3/3, which looked like a fix; a larger sample
shows the truth — `render-sanity` still fires roughly seven times in ten on
this build. That is a real improvement over Venice `deepseek-v4-flash` (one of
three), but the skill remains `FLAKY`, not reliable.

The residual miss mode is the original one, unchanged: on the miss reps the
model reads the browser/shell requirement as unsatisfiable — the probe's host
exposes only `skill_view` and `skills_list` — and declines outright instead of
loading the skill, sometimes reaching for `frontend-agent` or `playwright`
first. Two representative misses:

> I can't run this in the current session, and I'd rather tell you that than hand
> you a fabricated bug list. What's actually available to me here: only skill
> loading (skills_list / skill_view).

So the description front-loads the checklist framing well enough to win most
reps, but a refusal path still wins the rest. The remaining fix belongs in the
skill body (a hard "load this even when the host lacks a browser, then report
what you cannot check") rather than in another description tweak.

## Follow-up: the render-sanity body fix (v1.2.2)

The previous section located the residual miss in the skill *body*, not the
description. `render-sanity` v1.2.2 adds a hard directive — load and apply the
skill even on a host with no browser or shell, run the checks the tools allow,
and mark the rest `BLOCKED`, never decline — and reframes the non-negotiable
rules so "no browser" no longer reads as "cannot start." The report template
gained a `BLOCKED` verdict and an `INCOMPLETE` pass/fail outcome.

Re-probed on the same DeepSeek-direct build and the same trigger, as two
independent six-rep batches:

| Run | Reps | PASS | MISS | Verdict |
|---|---|---|---|---|
| body fix, batch A | 6 | 6 | 0 | PASS |
| body fix, batch B | 6 | 6 | 0 | PASS |
| **combined** | **12** | **12** | **0** | **PASS** |

Every rep now loads `render-sanity`, announces the degraded scope, and returns a
report whose browser-dependent checks are `BLOCKED` with reasons — the behavior
the fix targets. Two representative answers:

> Using render-sanity — but in fully-blocked mode. ... Per the skill that's not a
> reason to refuse — but it does mean every result below is BLOCKED, not a pass.

and:

> render-sanity loaded and applied. ... every unobservable check reported BLOCKED.

Against the pre-fix 7-of-10 result above, the load rate moved from `FLAKY` (~70%)
to 12-of-12. Selection is stochastic and the sample is small, so 12/12 is not a
claim of 100%; it is a clean verdict on two six-rep batches in which the previous
build produced misses.

**Still open:** the exact Venice `deepseek-v4-flash` row remains unverified. The
proxy result is evidence about the DeepSeek family, but it is a different model
build and does not settle the Venice row — re-run it with
`--model deepseek-v4-flash --only render-sanity --repeat 6` once credits are
restored.

## Post-load refusal grading (LOADED_REFUSED)

The probe used to score a skill `PASS` the moment it loaded, so a skill that
loaded and then declined the work looked identical to one that did it. The rubric
adds a fourth positive verdict:

| Verdict | Meaning |
|---|---|
| `PASS` | Loaded in every rep and did the work — or applied its degraded `BLOCKED` fallback |
| `LOADED_REFUSED` | Loaded in every rep but flatly declined: no work and no `BLOCKED` fallback |
| `WORKED` | Not loaded, but the request was served anyway (index-injecting host) |
| `MISS` | Not loaded and no work |

An answer counts as declined only when it carries a refusal marker **and** no
`BLOCKED` result — so a skill that folds its degrade contract into a BLOCKED
report still scores `PASS`; only a flat punt is `LOADED_REFUSED`. `FLAKY` now
means "loaded in some reps" specifically. `LOADED_REFUSED` is a finding: the
selection worked, the outcome did not.

Live re-probe (`deepseek-flash`, direct API, 2 reps, the same tool-less host):

| Skill | Verdicts | Group | Reading |
|---|---|---|---|
| render-sanity | PASS, PASS | PASS | loaded + applied its BLOCKED fallback |
| design-token-guard | PASS, PASS | PASS | loaded + applied its new degrade clause (v1.1.1) |
| class-extraction-guard | PASS, PASS | PASS | loaded + applied its new degrade clause (v1.1.1) |
| playwright | LOADED_REFUSED, LOADED_REFUSED | LOADED_REFUSED | loaded, then flatly refused — no fallback exists |

That is the distinction the audit asked for: selection success (`PASS`) versus a
selected skill that still declines (`LOADED_REFUSED`), with `playwright` the
clean example of the latter on a host that cannot run a browser. The two guards
passing here is the `design-token-guard` / `class-extraction-guard` degrade clause
(v1.1.1) doing its job.

## Follow-up: the guards on a file-read-without-shell host

The tool-less host exercises only the *last* rung of the two source-level guards'
degrade ladder: no checker and no file read, so the answer is a `BLOCKED` report.
That proves a skill no longer declines flatly, but not that the middle rung — a
hand-scan of the source — actually finds anything. To exercise it, the probe grew
three flags:

- `--toolsets TOOLSETS` — the host's `-t` value. The default `skills` is the
  tool-less host; `skills,file` adds `read_file`/`search_files` **without a
  shell** (the `file` toolset carries no terminal).
- `--max-turns N` — tool-calling iterations per probe (default 4), raised to 8 so
  a multi-file hand-scan has room to read and search.
- `--seed-work DIR` — copies a source tree into the probe work dir before
  probing, so a source-level fallback has source to scan.
- `--ground-truth PATH` — a skill → expected-files map; a loaded positive answer
  that cites no `path:line` in an expected file scores `LOADED_UNGROUNDED`.

The fixture now lives in the repo at `tests/gauntlet/fixtures/handscan-source/`
(committed, so the run is reproducible), with `ground-truth.json` beside it. It is
a five-file tree with planted violations: `src/ui/theme.ts` (the token source of
truth) plus `Button.tsx`, `Card.tsx`, and `Row.tsx`, carrying hardcoded colors
(`#1d4ed8`, `#ffffff`, `rgb(229, 231, 235)`, `hsl(0, 0%, 0%)`) and one
five-utility class string copy-pasted at three call-sites. An offline bats
assertion (`tests/gauntlet/01-trigger-probe.bats`) pins the fixture's planted
violations and the ground-truth map, so the probe cannot silently lose its teeth.

### A machine-checkable hand-scan contract

A `PASS` should require *correct findings*, not just a loaded skill. The probe
now extracts `path:line` locations from the answer and, when `--ground-truth`
names expected files **and the host has a file-read tool**, marks a loaded answer
with no expected location `LOADED_UNGROUNDED`. The file-read gate matters: a host
with no file read is *supposed* to return a `BLOCKED` report, so it is never
graded this way.

| Verdict | Meaning |
|---|---|
| `PASS` | Loaded and, when ground truth applies, cited an expected `path:line` |
| `LOADED_UNGROUNDED` | Loaded on a file-read host but cited no expected finding |
| `LOADED_REFUSED` | Loaded but flatly declined: no work and no `BLOCKED` fallback |

Re-probed on the file-read host (`deepseek-flash`, direct API, 2 reps,
`--toolsets skills,file --max-turns 8 --seed-work …/handscan-source
--ground-truth …/ground-truth.json`):

| Skill | Verdicts | Group | Grounded | Outcome |
|---|---|---|---|---|
| design-token-guard | PASS, PASS | PASS | yes, yes | hand-scan, `file:line` findings |
| class-extraction-guard | PASS, PASS | PASS | yes, yes | hand-scan, `file:line` findings |

Every rep loaded the skill, named the missing shell, and returned **source
findings with `file:line` locations** — a `BLOCKED` report in none:

> No shell in this environment, so the bundled checker could not be executed — I
> ran the gate by hand with the checker's exact semantics (read every source
> file, enumerated the full tree: 5 files…). VERDICT: NOT clean. 4 error-severity
> token bypasses across 2 files. — `design-token-guard`, rep 1

and:

> one finding — repeated-class-string (warning) … five utilities, three
> call-sites: `src/ui/Button.tsx:4`, `src/ui/Row.tsx:3`, `src/ui/Card.tsx:4` —
> `class-extraction-guard`, rep 2

Both guards therefore degrade correctly at every rung: run the bundled checker
when there is a shell, hand-scan the source when there is only file read, and
report every check `BLOCKED` when there is neither. As a control, the same two
skills were re-run with `--ground-truth` on the **tool-less** host: both `PASS`
with `grounded = null`, because the gate sees no file read and does not penalise
the correct `BLOCKED` report. The hand-scan is a model heuristic, so the counts
wobble between reps (`design-token-guard` reported 4 bypasses in one rep and 3 in
the other); the axis the audit cared about — findings, not a refusal — is stable,
and `BLOCKED` never appeared.

```bash
python3 scripts/gauntlet/trigger-probe.py --model deepseek-flash \
  --seed-config /tmp/gauntlet-seed-deepseek.yaml \
  --kind positive --repeat 2 --toolsets skills,file --max-turns 8 \
  --seed-work tests/gauntlet/fixtures/handscan-source \
  --ground-truth tests/gauntlet/fixtures/handscan-source/ground-truth.json \
  --only design-token-guard --only class-extraction-guard \
  --out .workspaces/gauntlet-trigger-probe/handscan-graded.jsonl \
  --summary .workspaces/gauntlet-trigger-probe/handscan-graded.md
```

## Full matrix on both hosts

The single-skill re-probe above proves the middle rung works; it does not
show what file read changes across the corpus. So the whole positive matrix was
run twice — once per host — with everything else held constant (`deepseek-flash`
via the direct API, one rep, all 71 probed skills):

| Host | Toolsets | Max turns | PASS | WORKED | LOADED_REFUSED | MISS | BLOCKED |
|---|---|---|---|---|---|---|---|
| tool-less | `skills` | 4 | 23 | 1 | 46 | 1 | 0 |
| file-read | `skills,file` | 8 | 31 | 24 | 12 | 0 | 4 |

`LOADED_UNGROUNDED`, `FLAKY`, and `FALSE_POSITIVE` were zero on both. Neither run
passed `--ground-truth`, so no skill was graded for findings here (grounding is
`null` throughout and `LOADED_UNGROUNDED` is zero by construction); this sweep asks
only *selection and outcome*, which is what the two hosts differ on.

Fifty-one of the 71 rows changed verdict. Grouped by transition:

| Transition | n | Skills |
|---|---|---|
| `LOADED_REFUSED` → `PASS` | 20 | architecture-rescue, babysit, codebase-exploration-loop, context-manager, contract-author, dependency-coordinator, find-unknowns, living-plan, llm-wiki, madness, maintain-context, plan-builder, project-profiler, prose-slop-guard, self-healing-loop, settings-consolidator, setup-project-skills, ui-brief, wiki-research, work-item-brief |
| `LOADED_REFUSED` → `WORKED` | 16 | backend-agent, contract-auditor, coverage-loop, db-migration-agent, diagnose-loop, docs-agent, git-commit, git-pr, git-pr-feedback, infrastructure-agent, mermaid-charts, migration-loop, nano-banana, payload-cms, performance-agent, repo-deep-dive |
| `PASS` → `WORKED` | 6 | grill-me, playwright, qe-agent, render-sanity, security-agent, skill-creator |
| `PASS` → `LOADED_REFUSED` | 4 | artifact-publish, skill-catalog, sync-skills, use-pxpipe |
| `PASS` → `BLOCKED` | 2 | contract-conformance-loop, skill-review |
| `LOADED_REFUSED` → `BLOCKED` | 2 | orchestrator, plan-intake |
| `MISS` → `WORKED` | 1 | fix-until-green |

**Read as a whole.** File read turns 36 of the tool-less host's 46 refusals into
work — 20 rows reach a full `PASS` (the skill's degrade ladder now has a middle
rung to stand on) and 16 become `WORKED` (the request is served from the injected
index with a usable tool, without a load). The net refusal count falls 46 → 12
because four rows that previously passed also became refusals (see the marker
artifact below). Selection does not degrade: there is no new
`MISS`, `FLAKY`, or `FALSE_POSITIVE`, and the tool-less run's single `MISS`
(`fix-until-green`) also resolves. The two sweeps are consistent with the thesis
that the tool-less host's refusals are a capability gap, not a description bug —
give the host a file read and they mostly disappear.

**The four `BLOCKED` rows are not host-quality findings.** `BLOCKED` is the
probe's crash path — a non-zero host exit *with nothing loaded* — not a graded
outcome; it is taken before the refusal/work grading runs. All four answers are
substantive (1.5–3.4 k chars) and their traces show `read_file`/`search_files`
activity, and reading them shows flat refusals after reconnaissance (orchestrator:
"I can't run it — there's no approved plan to run"; plan-intake: "I could not do
this as stated"). So the four are really *declined without loading* and the
`BLOCKED` label is the misleading one here: it names the exit code, not the
behaviour. Rerun with `--repeat 3` (and more turns) before treating any of them as
a finding.

**The four `PASS` → `LOADED_REFUSED` rows are a marker artifact.** `PASS` with a
refusal marker present is only possible when the answer also contains the literal
`blocked`, which the probe reads as a structured degraded report; all four
answers did exactly that on the tool-less host (e.g. artifact-publish: "Blocked on
both ends of this") and then phrased the same blocker without the literal on the
file-read host. The flip is how the refusal was worded, not a change in host
quality. Recorded answers are truncated at 500 chars, so the artifact is inferred
from the verdict's own preconditions rather than read directly. Tightening
`_reports_blocked` to require a structured marker is a follow-up, not a fix here.

```bash
python3 scripts/gauntlet/trigger-probe.py \
  --model deepseek-flash --seed-config /tmp/gauntlet-seed-deepseek.yaml \
  --kind positive --repeat 1 \
  --out .workspaces/gauntlet-trigger-probe/full-tool-less.jsonl \
  --summary .workspaces/gauntlet-trigger-probe/full-tool-less.md
python3 scripts/gauntlet/trigger-probe.py \
  --model deepseek-flash --seed-config /tmp/gauntlet-seed-deepseek.yaml \
  --kind positive --repeat 1 --toolsets skills,file --max-turns 8 \
  --out .workspaces/gauntlet-trigger-probe/full-file-read.jsonl \
  --summary .workspaces/gauntlet-trigger-probe/full-file-read.md
```

Raw JSONL and summaries stay in the gitignored
`.workspaces/gauntlet-trigger-probe/`.

## Caveats

- One rep per prompt. A `MISS` here is a lead, not proof; rerun with
  `--repeat 3` before filing a description bug.
- The work signal is a heuristic over the host's tool activity and final text.
  It rejects refusals and input requests and accepts a short but substantive
  answer, so it can still be fooled in both directions. `--strict` disables it.
- The host returns a non-zero exit on many successful one-shot runs. The probe
  only scores `BLOCKED` when nothing loaded, so those rows are still graded.
- Raw JSONL and the per-model summaries stay in the gitignored
  `.workspaces/gauntlet-trigger-probe/`.

## Reproduce

```bash
python3 scripts/gauntlet/trigger-probe.py --model gemini-3-5-flash \
  --include-explicit --kind positive --repeat 1 \
  --only code-review-agent --only grill-me --only model-adaptation \
  --only render-sanity --only skill-explorer
```

The DeepSeek-direct proxy run needs a seed config whose `model.provider` is
`deepseek` (the built-in Hermes provider):

```bash
python3 scripts/gauntlet/trigger-probe.py --model deepseek-flash \
  --seed-config /tmp/gauntlet-seed-deepseek.yaml \
  --kind positive --repeat 3 --only render-sanity
```
