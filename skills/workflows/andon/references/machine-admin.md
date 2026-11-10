# Machine setup and administration

Checked against `andon --help` and the usage strings in `apps/agent/src/cli.ts` at the Andon commit in `andon-pin.json`. The CLI is
under active expansion: run `andon --help` and `andon <command> --help` before using a flag from this file.

Every command here changes what **this machine** will run for the board, so sort each request into a tier before
running it.

## Tier 1: read, run freely

```sh
andon status | version | doctor | profiles
andon policy                # what each key allows or blocks, and the command to change it
andon policy show
andon keys list
andon repos list
andon accounts list
andon providers list
andon harness list
andon tunnel status
```

## Tier 2: ordinary changes; run when the person asked for that change

```sh
andon repos add <path> [--yes] | remove <path>        # where the agent looks for git repositories
andon accounts add claude|codex|gemini <name> [--current | --dir <path>] [--no-login] [--no-share]
andon accounts login claude|codex|gemini <name> | remove claude|codex|gemini <name>
andon providers add <slug> [--url <url>] [--name <name>] [--wire <form>] [--model <id>]...
andon providers key <slug> [--key-env <VAR>] | remove <slug>
andon policy executors claude,codex,gemini | runtimes orca,terminal | terminal-app <app>
andon policy context-summary on|off | recipe-detect on|off | improve-notes on|off | auto-open-terminal on|off
andon policy auto-build-planner on|off                 # auto-build's planner: this machine's Claude or Codex, no tools
andon policy orca-import off|worktrees|worktrees+sessions
andon tunnel tailscale | cloudflare | off [--no-terminal]
```

- Accounts are separate Claude, Codex or Gemini CLI logins, each in its own config directory; teams choose one on the board.
  The daemon reports names and signed-in state, never credentials.
- `providers key` stores a model endpoint's key **on this machine**. Use `--key-env <VAR>` so the key comes from the
  environment rather than the command line, where it would land in shell history.
- A tunnel exposes previews of sites runs serve (and the direct terminal unless `--no-terminal`). Say what it will
  expose before turning one on.

## Tier 3: trust and install changes; confirm every time

Each of these widens what runs without a person watching, or replaces the agent itself. State the effect in one line,
show the exact command, and wait for a yes in this conversation.

| Command                                                  | Effect                                                                                                                                    |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `andon policy trust-org` · `recipes trust-org`           | Runs any recipe the org defines, without per-recipe approval on this machine                                                              |
| `andon policy preset open` (or `standard`)               | Loosens several keys at once; `policy` alone shows what each preset sets                                                                  |
| `andon policy permission-mode <mode>` · `tools "<list>"` | Changes what a run may do without asking                                                                                                  |
| `andon policy new-repos on` · `terminal-input on` · `drive-answers on` | Lets runs clone repos, type into terminals, or have answers driven without the person                                     |
| `andon policy approve <recipe-slug>`                     | Lets that recipe run here                                                                                                                 |
| `andon policy auto-merge on` · `auto-push on`            | Runs merge or push PRs with no human in the loop                                                                                          |
| `andon policy signatures off`                            | Accepts board commands that aren't signed by an approved device                                                                           |
| `andon policy orchestrator on` | This machine hosts the board's orchestrator chat (its threads get only the `orch_*` tools) |
| `andon policy auto-update off`                           | Stops the daily self-update; the machine falls behind the board                                                                           |
| `andon keys approve <fingerprint>`                       | Accepts signed commands from that device. Check the 16-character fingerprint against the one the board shows (e.g. `3f2a-9c41-07be-d5e8`) |
| `andon harness approve <slug>`                           | Lets runs start under that exact harness hash (see `harness.md`)                                                                          |
| `andon setup --url <board> …` · `andon enroll …`         | Enrolls this machine with a board; `setup` also installs the service and may install Claude                                               |
| `andon update [--trust-board]`                           | Verifies and repairs the signed agent build; `--trust-board` installs the board's build with no release key pinned                         |
| `andon install-service` · `uninstall-service`            | Starts or removes the background service (Linux: `--linger` keeps it running when logged out)                                             |

`andon setup` takes flags that decide trust at enrollment time (`--trust-org`, `--approve-current`,
`--allow-auto-merge`). Prefer the conservative ones (`--no-auto-merge`, no `--trust-org`) unless the person names the
others.

## Machine-level failures

| Symptom                                      | First move                                                                                                  |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| A run fails with `blocked by machine policy` | It names the `andon policy approve …` or `andon harness approve …` command. That is Tier 3: show it and ask |
| A card never leaves the queue                | `andon route <card>` for the reason, then `andon doctor` on the preferred machine                           |
| `not set up; run: andon setup`               | This machine isn't enrolled; nothing else here will work until it is                                        |
| The agent is out of date                     | It updates daily by itself; `andon update` forces it (Tier 3)                                               |
