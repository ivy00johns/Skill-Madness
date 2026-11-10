# Attention: what needs the person

Checked against the Andon commit in `andon-pin.json` (`apps/server/src/instances/routes.ts`). This API is served by the
portable backend (`apps/server`) and is what the board's **Needs you** inbox and the desktop app use. (The org-scoped
`GET /api/v1/attention/items` in `docs/api.md` is a different, raw list; use the one below.)

An **attention item** is anything waiting on the human: a question a run asked, a tool permission it requested, a
failed run, a PR problem, an output to review, or a run that ran out of usage credits. Andon exists so the person is
pulled in only for these. Treat each one as theirs.

## Read

```sh
curl -sS "$ANDON_URL/api/v1/attention" -H "Authorization: Bearer $ANDON_CONNECT_TOKEN"
```

The response is `{"api": 1, "rows": [...]}`, covering every org the person belongs to (cards in a Done column and
items triage kept quiet are left out). A row, as returned on 2026-10-30:

```json
{
  "key": "waiting:<run id>:<timestamp>",
  "orgId": "<uuid>",
  "orgSlug": "johns",
  "kind": "waiting",
  "kindLabel": "Waiting for you",
  "tier": 1,
  "verb": "Reply",
  "title": "<card title>",
  "machine": "John-S-MacBook-Air.local",
  "detail": "API Error: Your computer went to sleep mid-response.",
  "question": "",
  "since": "2026-10-30T23:04:08.113Z",
  "path": "/o/johns/card/<card id>",
  "actions": [
    { "id": "reply", "label": "Reply", "input": true },
    { "id": "dismiss" },
    { "id": "snooze" }
  ]
}
```

- **`actions` is the authority on what can be done to that row.** Offer only those ids; `input: true` means the
  action takes `text`. Lower `tier` is more urgent.
- `path` is the card on the board; give the person `<board URL><path>`.
- A held permission or question also carries what is being asked (`question`, and the request's tool and input).

Present them oldest first, with what each is asking for in plain words. For a permission, show the tool and its
input; that is what the person is deciding on.

A whole batch of `waiting` rows with the detail `API Error: Your computer went to sleep mid-response.` means the
machine slept, not that the runs need a decision. A `reply` asking them to continue resumes each one. Say that's what
happened, and confirm before replying on cards that aren't part of a task the person gave you.

A run's **report** can carry decisions ("1 decision" in the row's `detail`): a question with offered options, such
as a conflict between the card's notes and a recipe input. Those are answered on the card itself (pick an option,
then **Send answer**), not through `actions`. Give the person the card link and the options, with your
recommendation.

A `run_failed` row whose detail reads "You've hit your 5-hour limit · resets <time>" is the account's usage cap, not a
bug in the card. Retrying before the reset fails the same way. Tell the person the reset time, and that every run
on the board draws on the same subscription as their own sessions.

## Act

```sh
curl -sS -X POST "$ANDON_URL/api/v1/attention/action" \
  -H "Authorization: Bearer $ANDON_CONNECT_TOKEN" -H 'content-type: application/json' \
  -d '{"key":"<item key>","orgId":"<org uuid>","action":"retry"}'
```

The server runs the same SQL the board's tiles call, as the person. A `reply` also sends `"text": "…"`. The answer is
`{"ok": true, "message": ""}` on success; a message means it couldn't be done. Say so; don't retry with a different
action. Auth is `Authorization: Bearer <connect token>` from another origin, or the board's session cookie from the
board's own origin.

| `action`              | Applies to                | What it does                                                               | Confirm first?                  |
| --------------------- | ------------------------- | -------------------------------------------------------------------------- | ------------------------------- |
| `allow` / `deny`      | a held permission request | decides it                                                                 | **Yes:** show tool + input      |
| `answer:<label>`      | a held question           | answers with that option; for `andon.ask`, also continues the card with it | **Yes:** show the question      |
| `reply` (with `text`) | a card                    | continues the card with the text as a new run                              | **Yes:** show the text          |
| `retry`               | a card                    | starts a retry run                                                         | Ask unless they said "retry it" |
| `fix`                 | a PR link                 | starts a fix run for the PR                                                | Ask unless they said "fix it"   |
| `merge`               | a card                    | merges the PR now (`merge_now`)                                            | **Yes, always**                 |
| `snooze`              | any item                  | hides it for an hour                                                       | No                              |
| `dismiss`             | any item                  | hides it for good                                                          | Ask                             |

"Confirm first" means: put the exact item and action in front of the person and wait for a yes in this
conversation. A general "handle my attention items" covers `snooze`; it does not cover `allow` or `merge`.

## Without the API

On a Supabase-only board there is no `/api/v1`. Say so, give the person the board link for the card, and offer to
read the board with `andon list` instead. Don't call the database's RPCs directly with a service key.
