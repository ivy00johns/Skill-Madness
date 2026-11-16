This directory is what this repository remembers, kept by [Andon](https://github.com/psci-labs/andon) and readable by
anyone. `memory/<kind>/` holds one entry a file: a convention, a decision, a gotcha, a how-to, a word, a person.
Never edit an entry in place: to change one, add a new file whose `supersedes` names the old id; to remove one, add
a file with `status: retired`. `knowledge/` holds longer notes, one topic a file, edited in place. Each file starts
with YAML front matter; `docs/andon-directory.md` in Andon's repository is the format. New entries from a run are
`status: proposed` until a review accepts them. `plans/<project>/plan.md` is what Andon intends for a project (edited
in place); `plans/<project>/groups/` holds each pull-request group's plan, written when the group starts building.
