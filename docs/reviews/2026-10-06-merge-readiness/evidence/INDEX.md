# Audit evidence index

These receipts support [the merge-readiness audit](../REPORT.md). Exit 0 from a **probe** means it reproduced/completed its experiment, not that the target meets acceptance. No live model campaign or global sync was performed.

## Library and branch state

- [Check statuses and timings](check-status.tsv): exact PR #82 revision, offline lint/catalog/security, 123 Python tests, 384 Bats tests, all-host conversion.
- [Open/closed PR inventory](pr-inventory.json): #79/#82 open; #80/#81 closed.
- [Combined merge simulation](pr79-pr82-merge-tree.txt): four conflicts; no branch merge performed.
- [Dirty-worktree reconciliation](dirty-worktree-reconciliation.json): 96 identical files, 31 differing files, zero absent from #82.
- [Follow-up test result](followup-tests.log): 87 pass, one actual-engine test skipped.
- [PR #82 Markdown lint](pr82-markdownlint.log): one MD033 violation in incoming source; the audit's own Markdown is separately linted clean.

## Evidence-harness defects

- [Trace audit](trace-audit.json): 24 active skill names, 52 without any record, zero near-miss controls, no unforced retrieval certification, stale frozen digest.
- [Synthetic all-blocked score](synthetic-all-blocked-score.txt): scorer incorrectly calls 76 blocked records fired.
- [Absolute target trap verification](traps-absolute.log): 5 PASS / 7 BLOCKED, exit 2.
- [Relative target trap verification](traps-relative.log): T8 false FAIL, exit 1.
- [Isolated-HOME Python dependency reproduction](python-isolated-home.log): PyYAML user-site import disappears under isolated HOME.
- [PR #79 unowned collision reproduction](pr79-unowned-collision.log): disposable HOME's local sentinel deleted by old sync; no real global skills changed.

## Product checks

- [Adversarial API/WebSocket observations](bazaar-adversarial.json): uninvited tenant/admin, private socket data, expired bid and unauthorized settlement probes, all using new simulated fixtures.
- [Clean-install typecheck failure](bazaar-typecheck.log): missing unbuilt contracts package.
- [Tests after contracts build](bazaar-tests-after-build.log): 10/10 pass.
- [Cross-instance Redis E2E](bazaar-cluster.log): 7/7 pass.
- [Headed playtest result](bazaar-playtest.json): 49 checks pass, zero defects; intentional 4xx probe console errors retained.
- [Headed playtest exit status](bazaar-playtest-exit.txt): separately completed run, not inferred from a timed-out enclosing shell.

## Reproduction scripts

- [Offline library checks](../run-checks.sh)
- [Trace/scorer/frozen-boundary probes](../probe-evidence.py)
- [Fresh-fixture product probes](../probe-bazaar.mjs)

Full logs, copied raw trace, isolated candidate/product clones and Python environment remain under the ignored `.workspaces/today-audit/` directory. These durable receipts contain no credential values. No commit was created.
