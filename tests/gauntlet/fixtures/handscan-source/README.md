# Hand-scan fixture

A five-file source tree with deliberate violations, used to exercise the
source-level guards' *hand-scan* fallback — the rung between "run the bundled
checker" (needs a shell) and "report every check `BLOCKED`" (needs nothing).

The trigger probe copies this tree into a host's work directory (`--seed-work`)
and asks the guard its coverage-matrix trigger on a host with file read but no
shell. `ground-truth.json` names, per skill, the files that carry a violation;
a loaded answer that cites none of them is `LOADED_UNGROUNDED`, not `PASS`.

Planted violations, by file and line:

- `src/ui/Button.tsx:5` — inline `style` with hardcoded `#1d4ed8`, `#ffffff`;
  `:4` carries the repeated class string.
- `src/ui/Card.tsx:5` — inline `style` with hardcoded `rgb(229, 231, 235)`;
  `:7` hardcoded `hsl(0, 0%, 0%)`; `:4` the same class string.
- `src/ui/Row.tsx:3` — the same class string, third call-site.

`src/ui/theme.ts` is the token source of truth the guard compares against, not a
violation.
