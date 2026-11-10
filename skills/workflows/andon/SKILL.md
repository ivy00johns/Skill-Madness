---
name: andon
version: 0.2.0
description: |
  Run work through a live Andon board (the kanban that dispatches cards to Claude Code, Codex and Gemini on your machines): push a plan's cards with the skills each run must load, read the board, answer what needs you, administer a machine, and refresh this skill when Andon changes. Trigger on "/andon", "put this plan on andon", "what needs me on andon", "why isn't my card running".
compatibility: "Any host with a shell and python3; the andon CLI on an enrolled machine, a capture token, or a connect token for the board's API"
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
composes_with: ["madness", "plan-builder", "sync-skills", "git-pr"]
spawned_by: []
---

# andon

Andon is a kanban board for coding agents. A card that is run becomes a **run**: an agent daemon on one of the
person's machines claims it, opens a worktree, starts Claude Code, Codex or Gemini in it with the card's title and
notes as the prompt, and reports status, questions, permission requests and a final report back to the board. The
person is pulled in only when a run needs them, through **Needs you** (the attention API).

This skill works _with_ a live Andon, from any repo and any harness. It does not change Andon's code; inside
`~/Work/andon`, that repo's own `andon-dev` and `andon-qe` skills cover that.

**The rule:** questions about the _state_ of the work (what's on the board, what's stuck, what needs the person,
where a card will run) are answered by asking Andon through its CLI or API, never from memory, the Andon source, or a
guess. Questions about how Andon _works_ are answered from its docs or code.

## The flow this skill serves

1. **`/madness`** routes the idea to `plan-builder`, which writes a plan whose components and features each name
   the **skills** the work should use.
2. **`/andon`** turns that plan into cards: one per buildable unit, each card's notes opening with a **Skills to use**
   block, captured in dependency order (`references/plan-to-cards.md`, `scripts/push_cards.py`).
3. The person (or `andon run <KEY>`) starts the cards; Andon runs them.
4. From **any** harness, `/andon` reads the board and the Needs you list to say what's running, done, or waiting
   (`references/board.md`, `references/attention.md`).

**Why skills go in the notes.** Andon does have native skills (a card's `skill` field, `use_skill`, the machine
catalog), but today capture can't set the field, the field holds one skill, and the catalog skips symlinked skills,
which is every Skill-Madness skill on a `/sync-skills` machine. Until Andon handles this itself, the run learns which
skills to load from its prompt, so the notes must say it, in the same words every time. `push_cards.py` writes that
block; don't hand-write it.

## Andon moves fast: check before you trust this file

Every command here was checked against Andon `main` at the commit in `references/andon-pin.json`. The installed
agent can be older than the source (the pin records both), and newer commands such as `andon run` and `-t`/`-g` on
`andon add` only exist once the machine has updated.

1. Run `andon --help` (or `andon <command> --help`). The CLI's own help wins over this file. A command this skill
   names that the help lacks means say so; don't invent a workaround.
2. When a repo has a `.andon/` directory, read its `README.md` and `settings.json` first. It is the team's memory and
   plans, and newer than this skill.
3. Report what you ran and what it returned. "Andon says X" needs this session's output behind it.
4. When the help and this skill disagree, or the person says "Andon changed", follow `references/refresh.md`.

## Step 1: find out what you can reach

Check these once per session, in order; use the first that works.

| Check                                                                       | What it gives you                                                       |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `andon status` (retry with `ANDON_CONFIG_DIR=~/.andon/agent` if "not set up") | An enrolled machine: list, route, doctor, policy, accounts, harness, memory |
| `ANDON_CAPTURE_TOKEN` set, `captureToken` in the agent config, or `~/.config/andon/capture.env` | Capture: add cards to the Backlog |
| A connect token or a signed-in session for the board's `/api/v1`            | Needs you: read and act on attention items                              |

- `andon status` prints the board URL; that is the board, wherever it's hosted (a laptop's `localhost:8787`, a NAS
  over Tailscale, a hosted board). `andon profiles` (newer agents) lists the boards a machine is enrolled with when there are several;
  `andon --profile <name> …` picks one.
- A board can be alive but wedged: the process exists and HTTP hangs. Check with `curl -m 5 <board>/api/v1/info`;
  when it hangs, say so rather than calling it healthy. Restarting a self-hosted board is an install-level action: ask.
- If nothing works, stop and say what's missing and where the person gets it: `andon setup --url <board>` (the
  board's installer), **Settings → Connections → Developer → Capture tokens**, or the board's connect flow. Never ask
  for a token that may already be in the environment or the agent config; look first, and never print one.

## Step 2: route the request

| The person wants to…                                                                         | Read                          | Risk                            |
| -------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------- |
| put a plan (or one piece of work) on the board, with the skills each card should use          | `references/plan-to-cards.md` | Confirm the batch before sending |
| see the board, start a card, know why a card runs where it does, check a machine              | `references/board.md`         | Low                             |
| see or answer what needs them: questions, permissions, failed runs, PR problems               | `references/attention.md`     | Some actions need confirmation  |
| set up or change a machine: enroll, policy, accounts, providers, keys, repos, tunnel, update  | `references/machine-admin.md` | Trust changes need confirmation |
| give Andon runs these skills as a bundle: import Skill-Madness as a harness                   | `references/harness.md`       | Approval is the person's call   |
| bring this skill up to date with Andon                                                        | `references/refresh.md`       | Edits this skill only           |

## What needs the person's yes first

Andon exists to keep a human on the cord, so this skill never removes them from it. Ask before:

- **Sending a batch of cards.** Show the dry run's list (titles, team/project, skills per card) and capture on a yes.
  One card the person just described needs no extra confirmation.
- **Starting runs** (`andon run`) unless the person said to run them.
- **Allowing a permission request, answering a question, replying on a card, or merging.** These act as the person on
  a live run. Show the item (tool, input, card) and the exact action, then wait.
- **Changing trust on a machine:** `policy trust-org`, `policy preset open`, `policy auto-merge on`,
  `policy signatures off`, `keys approve`, `harness approve`. Each one widens what runs without a human.
- **Anything that installs or re-runs the installer** (`andon setup`, `andon update`, `install-service`).

Reading the board, `route`, `doctor`, `status`, `list`, `groups`, and the attention list need no confirmation.

## Anti-patterns

| Anti-pattern                                                          | Why it fails                                                                       |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| A card whose notes don't name its skills                              | The run picks its own approach; the plan's skill choices are lost                  |
| Hand-writing the skills block, or putting it after the goal            | Runs read the top of the prompt first; the fixed wording is what makes them comply |
| Answering "what's stuck?" from the Andon source or a deep-dive report | The board is live; the source describes what could happen, not what did            |
| Hard-coding a flag from this file without checking `--help`           | The CLI changes weekly; a stale flag fails or, worse, does something else          |
| Allowing a permission or merging because the run "obviously" needs it | That decision is the reason Andon pulls the person in                              |
| Pointing `andon harness add` at the whole Skill-Madness repo          | It is over Andon's 600-file / 8 MB limit; build a bundle (`references/harness.md`) |
| Editing Andon's code to work around a missing feature                 | Say what's missing; capture a card for it on the board if the person wants one     |
