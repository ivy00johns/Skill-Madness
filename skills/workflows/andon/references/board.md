# The board: read it, start cards, route, check

Checked against the Andon commit in `andon-pin.json`. Run `andon --help` first; if it disagrees with this file, it wins.
Commands marked **(new)** are in the source but not in older installed agents (0.2.11 lacks them); `andon update`
brings them, which is the person's call.

## The work model

Work is **teams › projects › PR groups › cards**. A team is bound to a repository (it was called a project before
AND-143). A project is a goal inside a team, and every team has a **General** project. A PR group is cards that
ship in one pull request. Every card has a key such as `WEB-12`, used in URLs, branches, PRs and the CLI. The board
calls the attention list **Needs you**.

## Capture one card

For a plan, or any card that should name its skills, use `plan-to-cards.md`. For a quick one-off:

```sh
andon add "Fix the flaky login test" -n "fails 1 in 5 on CI since #142" -t Web -p General -r bug
andon add -u https://github.com/org/repo/issues/88          # a link alone is enough
andon add --template bug "Login fails" -t Web               # (new) fill the card from the team's Bug template
```

- `-n` notes, `-t` team **(new)**, `-p` project (a project alone brings its team), `-g` group name or `new`
  **(new)**, `-r` recipe slug, `-T` template **(new)**, `-u` url. Success prints `✓ Added WEB-12 to Inbox`.
- **Recipe slugs are not the board's display names.** Built-ins include `code-change`, `bug`, `app-new`,
  `generic`, `image-assets`, `plan` and `study`; an org adds its own. **An unknown recipe or project is silently
  dropped**: the capture still returns 201. Check the card afterwards.
- It needs a capture token for **this** board. `andon add` reads only `ANDON_CAPTURE_TOKEN` (and
  `ANDON_CAPTURE_URL`) from the environment, or `captureToken` in the agent config. It does **not** read
  `~/.config/andon/capture.env`; `push_cards.py` does. Keep the token in that file and export it from the shell
  profile (`set -a; . ~/.config/andon/capture.env; set +a`) so both work. The person makes one in **Settings → Connections → Developer → Capture tokens**;
  it starts `andon_cap_` and is shown once. A machine moved to a new board needs a new token.
- Without the CLI, `POST <apiUrl>/functions/v1/capture` with `Authorization: Bearer <token>` and JSON
  `{title, notes, team, project, group, recipe, template, url}`. `201 {card_id, card_key, path, group, group_error}`;
  `400` nothing sent or an unknown template; `401` bad token; `413` files too large; `429` over 30 a minute.
  Multipart takes up to 10 files (25 MB each, 30 MB total) as attachments.

**Recipe inputs and custom fields outrank the notes, and capture can't set them.** The New app recipe has a
**Stack** input. When the stack or a field matters, tell the person to set it on the card before pressing Run.

## Read the board

```sh
andon list            # every column with its cards: key, title, (team › project), [group: …], [run status]
andon groups          # (new) the open PR groups and their cards; --all for every state
andon status          # this machine: name, slug, board URL, launcher, agent version and protocol
```

Summarise by column for the person, and lead with anything failed or waiting. Run states include `[queued]`,
`[launching]`, `[running]`, `[needs_input]`, `[waiting]`, `[review]` and `[ended]`. A **waiting** run (finished its turn, needs a reply, review or decision)
still holds its machine slot, so a machine full of waiting runs starves the queue. When cards sit queued, look for
waiting runs first.

**"Is my plan done?" from any harness:** read the receipt `push_cards.py` wrote (`cards.receipt.json`, with keys),
then `andon list` and find those keys. Report each as Backlog / running / waiting / in review / done, with its link.
Then check Needs you (`attention.md`) for any of them. Done means the card is in Done or its PR merged, not that a
run ended.

## Start a card

- The card's **Run** button, or **(new)** `andon run WEB-12`, which moves it into Working and starts it.
  `andon run "<group name>"` runs a planned group (its cards in order, one PR).
- A capture never starts a run. On a team whose preset is **Ship** with Autopilot on, a card moved to **Ready** is
  built automatically.
- **Plan a workstream needs a team bound to a repo.** From such a card, approval creates step cards that run in
  dependency order in their own worktrees. A plan from a card with no team fails on approval.

## Why a card runs where it does

```sh
andon route WEB-12               # a key, a title, or the first 4+ characters of the card id
andon route "flaky login" --json
```

It reports the eligible machines, the preferred one (a queued run's 30-second head start) and the queue reason,
straight from the routing functions. A card whose `skill` field names a skill the machine's catalog doesn't have
queues with `no_skill`; that's why `plan-to-cards.md` keeps skills in the notes instead. A machine-policy reason (a
recipe or harness not approved there) is fixed in `machine-admin.md` with the person's yes.

## Check a machine

```sh
andon doctor          # everything the agent needs: Orca or tmux, the runtimes, the workspace operations
andon profiles        # the agents on this machine, one per board
```

Run `doctor` before blaming the board for a run that never started. Read out what failed in its own words.

## What the team has learned

```sh
andon memory list
andon memory search "migration order"
andon memory show [path]          # (new) the repository's own .andon/ memory, from the files
```

Read-only and safe. Memory is per team; `andon memory reflect <run-id>` proposes entries from a finished run, and
they wait on the board for the person. `--apply` records them at once: don't pass it without asking.
