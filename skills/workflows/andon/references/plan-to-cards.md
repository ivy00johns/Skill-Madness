# Plan to cards: put work on the board with its skills

The job: take a plan (usually `plan-builder`'s, reached through `/madness`) and make one Andon card per buildable unit,
each card's notes telling the run which skills to load. Checked against the Andon commit in `andon-pin.json`.

## How a card reaches the run

- A card's **title and notes are the run's prompt**, rendered into the recipe's template (`{{title}}`, `{{notes}}`).
  Captured notes pass through as instructions. Only a card imported from a tracker (`source = link`) has its notes
  fenced as untrusted data, so **never put the skills block on an imported card**; capture a new card instead.
- Captures land in the team's first column (the **Backlog**) and never start a run.
- Andon has no per-card skills (andon PR #499 removes the incomplete skills shelf: the card's Skill field,
  `use_skill`, `list_skills`, Settings → Skills). The notes are the only way to tell a run which skills to use.
- A plain Claude Code run sees skills by name: the repository's `.claude/skills` and `~/.claude/skills` (symlinks
  from `/sync-skills` are fine). Codex sees `~/.agents/skills` and `~/.codex/skills`. A run under a harness gets its
  own Claude home with only the harness's skills, so the block also says where to read each `SKILL.md`.

## Step 1: get the plan into cards

From a `plan-builder` plan, one card per **Key Feature** (or per component when features are small). Each
component and feature carries a `**Skills:**` line; when one doesn't, choose skills now (`skill-explorer`'s routing
table) and say which you chose. Set `repo` to the team repository's checkout when cards name skills that live in its
`.claude/skills`. Write `cards.json` beside the plan:

```json
{
  "team": "Web",
  "project": "Login revamp",
  "recipe": "code-change",
  "group": null,
  "plan": "docs/plans/login-revamp.md in the team's repo",
  "cards": [
    {
      "key": "contract",
      "title": "Define the session API contract",
      "goal": "An OpenAPI spec for /session that the backend and frontend cards build against.",
      "where": "api/openapi/; the plan's Shared Data Models section",
      "done": ["spec validates", "every endpoint has an example"],
      "skills": [{ "name": "contract-author", "why": "writes the spec from its templates" }, "git-pr"],
      "depends_on": []
    },
    {
      "key": "backend",
      "title": "Implement the session endpoints",
      "goal": "…",
      "done": ["contract-auditor passes", "tests green"],
      "skills": ["backend-agent", "fix-until-green", "contract-auditor", "git-pr"],
      "depends_on": ["contract"]
    }
  ]
}
```

| Field                 | Level      | Meaning                                                                                       |
| --------------------- | ---------- | --------------------------------------------------------------------------------------------- |
| `team`, `project`     | file, card | Exact names (or ids) as the board shows them. A project alone brings its team                 |
| `recipe`              | file, card | Recipe **slug**: `code-change`, `bug`, `app-new`, `generic`, `plan`, `study`, … (the board's own list wins) |
| `template`            | file, card | A card template's name; a name that matches nothing refuses the capture                       |
| `repo`                | file       | The team repo's local checkout; its `.claude/skills` count as installed for the name check |
| `group`               | file       | `null` for separate cards and PRs; `"new"` for one planned PR group holding every card, in order; or an open group's name |
| `skills`              | card       | Names, or `{name, why}`. Each must be installed on this machine (the script checks)           |
| `goal`, `where`, `done`, `notes`, `url` | card | The rest of the notes, in that order after the skills block                       |
| `depends_on`          | card       | Keys of cards in this file. Sets capture order and writes a "Depends on" section              |

**Pick skills per card, not per plan.** Name the skill that does the card's work (a role like `backend-agent`, a
loop like `fix-until-green`), what checks it (`contract-auditor`, `render-sanity`), and how it ships (`git-pr`). Three
or four is typical; a long list gets skimmed. Don't name `madness` on a card that already knows its work.

## Step 2: dry run, then confirm

```sh
python3 skills/workflows/andon/scripts/push_cards.py cards.json          # prints every card's notes and payload
```

It refuses unknown skill names, cycles, and unknown `depends_on` keys. Show the person a short list (title, team › project, recipe, skills) and capture on a yes.

## Step 3: send

```sh
python3 skills/workflows/andon/scripts/push_cards.py cards.json --send
```

- Cards go in dependency order, so a later card's "Depends on" names the earlier card's key (`WEB-12`).
- It stops at the first failed capture and writes `cards.receipt.json` (keys, ids, links). Running `--send` again
  resumes: cards the receipt records as landed are skipped, so a retry doesn't duplicate the board. `--again`
  ignores the receipt and captures everything.
- Auth: the capture token (`ANDON_CAPTURE_TOKEN`, the agent config's `captureToken`, or `~/.config/andon/capture.env`).
  The URL is the agent config's `apiUrl` + `/functions/v1/capture` unless `ANDON_CAPTURE_URL` is set.
- `401`: the token is wrong or for another board (a token belongs to one board; moving boards needs a new one).
  `429`: over 30 a minute; wait a minute and `--send` again to resume.

## Step 4: check what landed

Capture **silently drops** an unknown recipe or project and still returns `201`. After sending, run `andon list` (or
open each link) and confirm each card's team › project and recipe. A dropped recipe means the card would run as a
plain to-do.

## Step 5: start them

- Dependencies are written in the notes, not enforced: Andon's native dependencies come only from its own planners
  (a Plan card's `propose_steps`, a study's accepted proposal, Start Work's plan). So start cards in order: the first, then each
  one whose dependencies are done. A `"group": "new"` push ships as one PR and runs its cards in order by itself.
- Start one with the card's **Run** button, or `andon run <KEY>` (`andon run "<group name>"` for a group) where the
  installed agent has it (`andon --help`). Ask before starting runs the person didn't ask to start.
- A team on the **Ship** preset with Autopilot builds cards moved to **Ready** by itself; moving many cards to Ready
  there starts them all.

## Other ways in (and why they're not the default)

- **Start Work** (the board's `W` box) takes a pasted brief and asks Gemini to break it into cards. Its cards carry no
  skills block. Use it when the person wants Andon's own breakdown.
- **A Plan or Study card** asks a run to plan inside Andon; its proposal becomes cards with real dependencies once a
  person accepts. Put the skills you want in that card's notes, and its proposal may still drop them.
- **One card by hand**: `andon add "title" -n "<notes>" -t <team> -p <project> -r <recipe>`, with the notes from a
  one-card `cards.json` dry run so the skills block is the same.
