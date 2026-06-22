# Exploration mechanics

The three pieces specific to this loop: the seed-question / default-FAIL
mechanism, the read-only fan-out pattern, and the hand-off boundary to
`repo-deep-dive`. The loop machinery (caps, no-progress, budget, state
externalization) lives in `loop-controller`'s `references/safety.md` — not here.

## Contents
- [The seed-question proof (default-FAIL)](#proof)
- [The read-only fan-out pattern](#fanout)
- [Hand-off to repo-deep-dive](#handoff)

---

## Proof

`seed-questions.json` is the loop's default-FAIL contract. One entry per
question; every entry starts unanswered and flips **only** on a real code
citation.

```json
{
  "questions": [
    {
      "id": "q1",
      "question": "Where does an HTTP request enter the system?",
      "answered": false,
      "citation": null,
      "notes": ""
    },
    {
      "id": "q2",
      "question": "How is authentication enforced on a protected route?",
      "answered": false,
      "citation": null,
      "notes": ""
    }
  ]
}
```

Rules that make it default-FAIL rather than a checkbox the loop pencil-whips:

1. **`answered` flips to `true` only with a non-null `citation`.** The citation
   is a real `path:line` or a named symbol the reader can open — `src/server.ts:42`
   or `class AuthMiddleware`. "It's handled in the API layer" is not a citation;
   it's a restatement of the question. No citation → still `false`.
2. **The summary must back the JSON.** A question is genuinely answered only when
   `ARCHITECTURE-SUMMARY.md` has prose that cites the same code. The two artifacts
   are cross-checked; a `true` in the JSON with nothing in the summary is a
   *finding*, not a win.
3. **The list grows — that is the loop, not a failure.** Each synthesis round
   reads the summary as a whole and asks "what can I still not explain?" Every
   such gap becomes a **new** entry, `answered: false`. The loop is done only when
   the list is fully `true` **and** a round adds no new entry. This is the
   loop-until-dry stop: answers-nothing-new **and** finds-no-new-gap = dry.
4. **Never empty the list by deletion.** A hard question that needs the code's
   author gets surfaced to the human (per the no-progress rule in the SKILL body),
   not quietly dropped to make the list look complete.

## Fanout

Each round is a parallel dispatch of **read-only mapper subagents** — the
`/deep-research` fan-out shape pointed at local code instead of the web.

**The dispatch:**

- **One mapper per open subsystem or question** still `answered: false` — but cap
  the concurrent width (default ~4-6, per `loop-controller` Step 5). Excess
  parallel readers produce memos you can't reconcile and a budget you can't
  predict. If more questions are open than the cap, prioritize the ones that
  unblock the most others (entry points and data model before leaf details).
- **Read-only tools only.** Mappers get Read / Grep / Glob / Bash-to-inspect.
  **No Write, no Edit, no web.** A mapper that cannot edit cannot "fix" the code
  to match its hypothesis, and (per the evaluator pattern in `loop-controller`)
  a fresh read-only agent reports what is *there*, not what it hopes is there.
- **Each mapper returns a short findings memo:** the subsystem's responsibility,
  its key files, the call/data path it traced, and a `path:line` citation for
  every claim. Memos are inputs to synthesis — they are not written into the
  summary by the mapper; the orchestrating loop synthesizes.

**How this differs from `/deep-research`:** identical *shape* (fan-out → verify
each claim against the primary source → synthesize), different *corpus and
citation*. `/deep-research` fetches the web and cites URLs; this reads the local
tree and cites `path:line`. There is no network step and no source-credibility
weighting — the code *is* the ground truth, so "verify" means "the cited line
actually says this," which a second read confirms cheaply.

## Handoff

This loop stops when **your** questions are answered. It deliberately does **not**
produce a comprehensive reference series, and should not grow into one. Two
explicit hand-offs:

- **Want the full reference series?** When the user wants every subsystem
  documented to a consistent template — the 12-14 document deep-dive, not just
  answers to a question list — **invoke [`repo-deep-dive`]**. Pass it
  `ARCHITECTURE-SUMMARY.md` as orienting context (it can stand in for, or augment,
  the deep-research markdown that skill normally wants). Signal to hand off: the
  user asks for "full docs," "a reference for the whole repo," or "document every
  subsystem," or the seed-question list has effectively become "explain
  everything."
- **Want the profile refreshed?** When the loop has learned enough that the
  project's `CLAUDE.md` / `profile.yaml` is stale or missing, **invoke
  [`project-profiler`]** as a separate, explicit step to regenerate it from what
  the loop learned. The loop never writes those files itself — mappers are
  read-only, and profiling is project-profiler's owned artifact.

The boundary in one line: **this loop converges on a question list; its neighbors
produce fixed artifacts. It delegates to them — it does not reimplement them.**

[`repo-deep-dive`]: ../../../workflows/repo-deep-dive/SKILL.md
[`project-profiler`]: ../../../workflows/project-profiler/SKILL.md
