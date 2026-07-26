# Audit Evidence — committed projections of the local audit working tree

> **What this is:** the citable, in-repo record of audit findings. The full audit
> working tree (`audit/`) is gitignored (`.gitignore` line 34) — it holds bulky
> machine-generated JSON, workflow scratch, and worker briefs that only ever
> existed on one machine. This directory is its curated projection: every report
> republished here has been sanitized, given a typed header, and human-reviewed
> before commit, so anyone with the repo can re-check a cited finding against a
> later revision. (Ledger row `HE-1` is why this exists.)

## Relationship to `audit/`

- `audit/` **stays gitignored.** It is the working directory where audit passes
  run and write their raw output. Nothing in it is citable, because nobody else
  can read it.
- `docs/audit-evidence/` is **append-mostly and committed.** Reports move here
  one at a time, on demand — a report gets republished when something needs to
  cite it (typically a ledger entry via `plan-intake`), not wholesale.
- The projection never edits report content. A republished report is the source
  file verbatim, with exactly one addition: the typed header block (plus a
  staleness note) above a `---` divider. Everything below the divider is
  byte-identical to the source.

## The typed header

Every republished report opens with a fenced `yaml` block carrying these fields:

| Field | Rule |
|---|---|
| `report` | `<pass-dir> / <report-name>` — matches the file's location here. |
| `skill` | The skill audited (path + version at audit time), or the scope for pass-wide synthesis reports. |
| `audit-date` | The date recorded in the source report. |
| `revision-reviewed` | The git SHA the audit ran against, **if the source records one**. If it does not, write `unrecorded (pre-convention)` — never reconstruct or guess a SHA. New audit passes must record the SHA at run time so this field stops being `unrecorded`. |
| `worker-config` | How the audit was produced: orchestration mechanism (workflow/subagent structure, verification stages) and the worker model **if recorded**; `unrecorded` otherwise. |
| `verdict` | The report's own verdict, condensed but not reinterpreted. |
| `evidence-links` | In-repo **relative** paths the findings cite, so a reader can re-open each one against the current tree. |
| `source` | The `audit/…` path this was republished from, labeled as the gitignored local working tree. |
| `republished` | Date of republication + the statement that the body is verbatim. |

## How a finding gets republished here

1. Something needs to cite an audit finding — usually `plan-intake` filing a
   ledger entry whose source is an audit report.
2. Copy the source report from `audit/…` **verbatim**; prepend the typed header
   and a staleness note; place it at
   `docs/audit-evidence/<audit-date>-<pass-slug>/<report-name>.md`.
3. Sanitize-check: no absolute local paths (nothing machine-specific), no
   personal machine details, nothing that reads as a credential. Repo-relative
   paths only. If the source body itself violates this, it cannot be republished
   verbatim — flag it for a redacted projection instead, and say so in the header.
4. Human review of the fragment before it is committed — republishing is
   publishing.
5. Cite the `docs/audit-evidence/…` path from the ledger, never the `audit/…`
   path. Update `INDEX.md`.

## Staleness

A republished report is evidence of **what an audit found at its audit date**,
not a description of current state. Most findings get fixed; the projection is
kept anyway so the claim → evidence chain survives. Each report's staleness note
says where its remediation landed (usually `docs/COMPLETED-WORK.md`). Re-check
any finding against the current tree before acting on it.

## Layout

```text
docs/audit-evidence/
├── README.md                          # this convention
├── INDEX.md                           # every audit pass + what is projected vs local-only
└── <audit-date>-<pass-slug>/          # one directory per audit pass
    └── <report-name>.md               # typed header + verbatim source body
```
