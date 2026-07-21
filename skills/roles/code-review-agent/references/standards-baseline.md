# Standards-lane baseline — the built-in code-smell checklist

The floor the **Standards lane** applies even when the repo documents no
coding standards at all. When the repo *does* document standards (CLAUDE.md,
lint configs, `docs/agents/*`), those come first and this baseline runs
underneath them — a documented repo rule that contradicts a smell wins, and the
contradiction is worth one LOW note.

Adapted from mattpocock `engineering/code-review` (v1.1.0), which anchors its
baseline on Fowler's named smells. Names are load-bearing: cite the smell by
name in the finding so the fix is searchable.

## The twelve named smells

| Smell | What to look for | Typical severity |
|---|---|---|
| **Duplicated Code** | The same logic in ≥2 places; copy-paste with small edits | MEDIUM (HIGH if the copies already diverge) |
| **Long Function** | One function doing several jobs; can't be named honestly with one verb phrase | MEDIUM |
| **Large Class / Module** | A file accumulating unrelated responsibilities; the "and" in its description | MEDIUM |
| **Long Parameter List** | ≥4–5 positional params, or booleans that flip behavior | LOW–MEDIUM |
| **Divergent Change** | One module edited for many unrelated reasons across the diff's history | MEDIUM |
| **Shotgun Surgery** | One logical change forcing edits in many files; the diff itself is the evidence | MEDIUM–HIGH |
| **Feature Envy** | A function reaching into another module's data more than its own | LOW–MEDIUM |
| **Data Clumps** | The same group of fields/params travelling together unbundled | LOW |
| **Primitive Obsession** | Domain concepts passed as bare strings/ints (IDs, money, states) | LOW–MEDIUM |
| **Message Chains** | `a.b().c().d()` — the caller navigating someone else's structure | LOW |
| **Middle Man** | A class/function that only delegates; deleting it loses nothing | LOW |
| **Speculative Generality** | Abstractions, hooks, or options for callers that don't exist ("might need it later") | MEDIUM — pairs with the Spec lane's unrequested-additions check |

## Always-on non-smell checks

Beyond the named smells, the Standards lane always covers:

- **Error handling** — failures swallowed, `catch {}` blocks, errors logged
  without being handled or propagated.
- **Security conventions** — input validation at trust boundaries, no string-
  built queries/commands, secrets out of source, authz on every mutating path.
  (Deep security review remains `security-agent`'s job; this is the smell-level
  screen.)
- **Obvious performance smells** — N+1 queries, work in loops that belongs
  outside them, unbounded reads. Only flag what is *clearly* problematic.
- **Naming and consistency** — names that lie, conventions that flip mid-diff.

## What this lane never does

- It never reads the originating issue/contract — spec fidelity is the Spec
  lane's question, and the isolation is deliberate.
- It never merges its verdict with the Spec lane's (binding rule 1 in the
  SKILL.md).
- It never blocks on taste. A finding cites either a documented repo standard
  or a named smell from this file; "I'd have written it differently" is not a
  finding.
