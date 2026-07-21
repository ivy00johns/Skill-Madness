# Performance Notes Pattern

Documents the optional `## Performance Notes` section that can appear in any SKILL.md body.

> **Prior-model tactic — apply sparingly.** This pattern was developed against models where
> output laziness ("[...continued]" placeholders, silently compressed later sections) was a
> common failure mode. On the Claude 5 family (Fable 5 / Mythos 5) it rarely is, and
> reflexive "do not truncate / produce it in full" nagging is now itself an anti-pattern —
> `skill-review` flags it (see `model-adaptation`: prune scaffolding the model no longer
> needs). Add this section only when a **measured** truncation failure exists for *this
> specific skill* on the *current* model — a reproduced case of abbreviated output, not a
> precaution. Default to leaving it out.

Source: Anthropic Agent Skills guide (p.26) — "Add explicit encouragement for model laziness" — written for prior-generation models.

---

## When to Include It

Only with a measured truncation failure on the current model (see the note above). When that bar is met, the failure usually involves output that is:

- **Large and structured** — full JSON schemas, multi-section reports, complete code files, 50+ row tables. The model will abbreviate if not told otherwise.
- **Multi-part** — the skill produces 3+ distinct artifacts in one run (e.g., a brief, a checklist, and a diagram). Without encouragement, later artifacts get compressed.
- **Iterative** — the skill has a loop or refinement cycle where each iteration is expected to produce a complete revision, not a partial patch.
- **Long-running** — the task takes many tool calls. Laziness tends to increase as the call count climbs.

Do NOT add it for:
- Short-answer skills (recall, routing, status checks)
- Skills where truncation is acceptable (summaries, excerpts)
- Skills that already have strong output format enforcement via numbered steps and explicit examples

---

## What Goes In It

A `## Performance Notes` section is a direct instruction to the model, placed near the end of the body (before `## References`). It names the specific laziness pattern likely to appear and tells the model how to avoid it.

**Template:**

```markdown
## Performance Notes

[Artifact name] must be complete — do not abbreviate, truncate, or use "[...continued]"
placeholders. If the output is long, produce it in full rather than summarizing.

[If multi-part:] Produce all [N] sections in one response. Do not omit a section because
the previous section was long.

[If iterative:] Each revision must be a complete replacement of the previous draft —
not a patch or a list of diffs. The output of each iteration is the new canonical version.
```

Adjust the language to match the specific failure mode. The goal is to name the temptation and preempt it.

---

## Examples from This Repo

These illustrate the *shape* a section would take — none of these skills currently carries one, and none should gain one without the measured-failure bar above being met.

### `repo-deep-dive`

This skill produces 12-14 document reference series. Without explicit guidance, later documents in the series get shorter as the run length climbs. Its Performance Notes section (if added) would say:

> Each of the 12-14 output documents must be fully written — not outlined, not abbreviated. Document length should reflect the source material, not the position in the series.

### `contract-author`

Produces complete integration contracts with all fields populated. A laziness failure here produces contracts with placeholder fields, which breaks downstream agents that parse them. Performance Notes:

> The contract must contain every required field with a real value — no `null`, `TBD`, or placeholder strings. Downstream agents parse this contract programmatically; missing fields cause their builds to fail.

### `orchestrator`

Produces a multi-phase execution plan with agent assignments. Laziness shows up as agents with empty `instructions` fields. Performance Notes:

> Every agent's `instructions` block must be fully written — a specific, actionable brief, not a one-liner. The agents receive only what is in `instructions`; vague instructions produce vague work.

---

## Placement

Put `## Performance Notes` after the main instruction steps and before `## References`. It reads as a final reminder just before the model starts executing, which is when it has the most effect.

```markdown
## Step 3: Produce the Report
...

## Performance Notes
[encouragement here]

## References
...
```

---

## Anti-patterns

- **Do not add Performance Notes to every skill.** Most skills don't need it. Adding it routinely dilutes its effect.
- **Do not be vague.** "Do your best" is not a Performance Note. Name the specific failure mode: "do not truncate the second half of the checklist" is actionable.
- **Do not repeat it in multiple places.** One section at the end is enough. Scattering the same instruction through the body creates noise.
