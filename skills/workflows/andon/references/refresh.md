# Refresh this skill when Andon changes

Andon ships many changes a week. This skill records the commit it was last checked against
(`andon-pin.json`) and the files whose changes matter to it (`watched`). Refreshing means re-checking those, updating
what moved, and moving the pin. It edits only this skill's own files.

Run it when `andon --help` disagrees with a reference, when the person says Andon changed, or weekly. It can be
scheduled: `/loop 7d` or a `/schedule` routine that runs Step 1 and opens a PR only when it reports drift.

## Step 1: measure

```sh
python3 skills/workflows/andon/scripts/check_drift.py              # fetches ~/Work/andon; --andon-repo elsewhere
```

It prints the commits since the pin that touch the watched files, the CLI usage lines that changed in the source,
the installed agent's version against the pin, and any `andon <command>` this skill names that the installed help
lacks. Exit 0 means nothing moved, so stop. Exit 1 means there's drift to review.

## Step 2: read what moved

For each changed watched file, read the diff from the pin (`git -C ~/Work/andon diff <pin>..origin/main -- <file>`),
then the doc that explains it. Sort each change:

| Change                                               | Update                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| A CLI command or flag added, renamed or removed      | `board.md` / `machine-admin.md`, and mark it **(new)** until installed agents have it |
| Capture fields or responses (`supabase/functions/capture`) | `board.md` capture section, `plan-to-cards.md`, `push_cards.py` |
| How notes reach the prompt (`template.ts`, recipes)  | `plan-to-cards.md` "How a card reaches the run"; recheck the skills block |
| Skills: catalog, `use_skill`, card `skill` field, capture setting skills | `plan-to-cards.md`, the skills block in `push_cards.py`, SKILL.md "Why skills go in the notes" |
| Attention / Needs you API                            | `attention.md`                                               |
| Harness format or limits                             | `harness.md`, `build_harness.py`                             |
| A new area the skill should know about               | Add the file to `watched` and a line to the routing table    |

**Watch for native skill support.** The notes-based skills block exists because capture can't set skills, a card
holds one, and the catalog skips symlinks. When Andon fixes one of those, update that part of the workaround, and
retire it entirely once runs get every named skill natively.

## Step 3: verify against the live system

Every changed claim needs proof from this session: `andon --help` output, a dry run of `push_cards.py`, a read
of the source, or one real capture on a card the person agrees to. Mark a claim you couldn't check "unverified" in
the file, not silently kept.

## Step 4: move the pin and ship

1. Set `commit` and `date` in `andon-pin.json` to the Andon commit you checked, and `installed_agent` to
   `andon version` on this machine.
2. Bump this skill's `version` (patch for wording, minor for a changed procedure or script).
3. Re-run `check_drift.py`; only (new) commands not yet installed should remain.
4. Lint (`scripts/lint-skills.sh`), then commit and open a PR with `git-pr`. List the Andon commits that drove each
   change in the PR body.
