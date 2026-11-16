---
id: 01M7K16Y1802RYHG6EJ5YH4AFG
kind: conventions
status: accepted
title: skills/meta/
tags: [skill-categories]
paths: [skills/meta, long-run/effort]
source: import CLAUDE.md:43 e3e4625ee4834189
confidence: 0.7
supersedes: none
created: 2026-11-16
---

**`skills/meta/`** (9) — skill-writer, skill-review, skill-update, skill-explorer, skill-catalog, madness (the front-door router: reads intent, picks the right starting skill — orchestrator / plan-builder / a loop / a role or workflow / skill-explorer — and launches it, confirming before anything expensive; the active counterpart to skill-explorer), model-adaptation (the model-migration reference: what to prune, what now triggers a `reasoning_extraction` refusal, and the long-run/effort scaffolding to add when the underlying Claude model changes — Fable 5 / Mythos 5 today; enforced via skill-review, loop-controller, and orchestrator), skill-triage (measures skill routing with TypeSafe's Jev decision model: route one request, score labeled routing cases, and find descriptions that steal each other's trigger phrases), skill-eval (proves a skill helps with `claude plugin eval`: runs each case with and without the skill under a required dollar cap and reports the delta).
