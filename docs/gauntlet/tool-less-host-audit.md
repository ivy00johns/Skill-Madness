# Tool-less-host refusal audit

**Question.** The trigger probe exposed one real defect on `render-sanity`: on a
host that exposed only skill-loading tools, the model read the skill's browser
requirement as unsatisfiable and **refused without loading it** — a positive
`MISS` (3 of 10 reps before the v1.2.2 body fix). Does that failure shape recur
in the other browser- or tool-dependent skills?

**Answer.** No — not on the loading axis. Probed on the same tool-less host,
**every** tool-dependent skill loaded on its trigger and *then* declined to do
work it genuinely could not do. Zero loading misses across 18 reps.

## Method

Same instrument as the render-sanity work: the DeepSeek-direct proxy
(`--model deepseek-flash --seed-config /tmp/gauntlet-seed-deepseek.yaml`), a
hermetic host whose isolated home carries only this repo's skills, and whose
`-t skills` toolset exposes exactly `skill_view` and `skills_list` — no shell, no
file read, no browser. Each candidate was asked its coverage-matrix trigger,
twice. A `MISS` means the model declined without even loading the skill; `PASS`
means it loaded it.

## Results

| Skill | Must-fire | Reps | Verdicts | Loaded |
|---|---|---|---|---|
| playwright | yes | 2 | PASS, PASS | yes |
| website-walkthrough-video | yes | 2 | PASS, PASS | yes |
| nano-banana | yes | 2 | PASS, PASS | yes |
| artifact-publish | yes | 2 | PASS, PASS | yes |
| railway-deploy | yes | 2 | PASS, PASS | yes |
| payload-cms | yes (optional) | 2 | PASS, PASS | yes |
| design-token-guard | yes | 2 | PASS, PASS | yes |
| class-extraction-guard | yes | 2 | PASS, PASS | yes |
| deployment-checklist | yes | 2 | PASS, PASS | yes |
| **total** | | **18** | **18 PASS · 0 MISS** | 9/9 |

Raw JSONL and summaries: `.workspaces/gauntlet-trigger-probe/audit-toolful-{a,b}.jsonl`
(gitignored).

## Finding 1 — the loading miss does not recur

Every probe loaded its skill. Representative answers, all of which name the
loaded skill and then report the blocker:

> I can't run this here, and I won't hand you a fabricated report or fake
> screenshot paths. Blocker: this session has no execution surface. ... The
> `playwright` skill I loaded is exactly the right playbook for the job, but
> every step in it ... needs a shell. — `playwright`

and:

> Loaded the design-token-guard skill ... and read its bundled checker,
> `scripts/check_design_tokens.py`. Tried to run it. This session exposes only
> two tools: skill_view and skills_list. — `design-token-guard`

The distinction from `render-sanity` is *why* the model refused, not *whether*:
`render-sanity`'s trigger is a browser action **and** its body framed the browser
as non-negotiable, so the model reasoned "this skill cannot apply here" and never
opened it. The nine here name a capability in their trigger but their identity is
the capability itself, so the model opens the skill and reports the blocker from
inside it. That is the correct behavior — the probe counts the load, and the
answer is honest.

These 18 reps were recorded under the load-only rubric that predated
`LOADED_REFUSED`. Re-graded under the current rubric the loading result is
unchanged — **0 misses** — but every row's outcome reclassifies to
`LOADED_REFUSED`: selected, then declined the work this host could not run. That
is the outcome axis this audit prompted, and Finding 3 is the fix. (The re-grade
reads stored 500-character answer excerpts, so a late `BLOCKED` fallback could be
missed; the live re-probe in `trigger-probe-results.md` is authoritative.)

## Finding 2 — where the refusal is wrong, and where it is right

Every one of these nine can only be *fully* run with a tool the probe host lacks,
so refusing the work is honest. But two of them have a **tool-free reduced scope**
that their bodies did not describe, and were the only candidates that would
benefit from a `render-sanity`-style *degrade-and-mark-BLOCKED* clause:

- **`design-token-guard`** — the gate is a **source-level** check (find inline
  styles / hardcoded colors), and the skill ships `check_design_tokens.py`. On a
  host with file-read but no shell, the check is still doable by reading source;
  the body only documented running the script, so the model reported a flat
  blocker instead of a static pass.
- **`class-extraction-guard`** — same shape: a source-level detector
  (`check_class_extraction.py`) with a script-only body. A host that can read
  source can still find the utility-class runs the gate is about.

By contrast, `playwright`, `website-walkthrough-video`, `nano-banana`,
`artifact-publish`, `railway-deploy`, `payload-cms`, and `deployment-checklist`
have **no meaningful tool-free fallback** — the browser / ffmpeg / image API /
network / shell is the whole job. For those, the honest refusal is the correct
outcome and a "degrade" clause would only tempt the model to fabricate.

**Both guards are now fixed (v1.1.1).** Each gained a "When the checker can't
run" section: run the script when the host has a shell; hand-scan the source with
the read/grep tools when it has file-read but no shell; and, with neither, load
the skill and report every check `BLOCKED` with the command to run. Re-probed on
the same host with the new `LOADED_REFUSED` grading, both now **PASS** — they load
and return a BLOCKED report instead of a flat refusal — while `playwright`, which
has no fallback, is correctly flagged `LOADED_REFUSED`.

## Finding 3 — the probe could not see a post-load refusal (now fixed)

The render-sanity defect was a *loading* miss, so the old probe caught it. The
pattern the nine show — **loaded, then declined** — was invisible: loading alone
scored `PASS`, and `assess_work` was only consulted when the skill was *not*
loaded. A skill that loads and then does nothing looked identical to one that
loads and works.

The probe now grades this. A loaded answer that declines **and** hands back no
structured `BLOCKED` result scores `LOADED_REFUSED`, distinct from `PASS`. An
answer that declines but still applies the skill's degraded fallback (a `BLOCKED`
report) stays `PASS` — it did the work the skill allows. See
`trigger-probe-results.md` for the verdict definition and the live re-probe.

## Recommendation

1. ~~Add the "degrade, don't decline" directive to `design-token-guard` and
   `class-extraction-guard`.~~ **Done** (both v1.1.1) — and re-probed green.
2. Leave the other seven as-is; their refusal is correct when the capability is
   genuinely absent.
3. ~~Extend the probe to score a post-load refusal.~~ **Done** — the
   `LOADED_REFUSED` verdict now surfaces this class (`--repeat` shows it per row).
