# Vault Detection (Phase 0) & Wiki Integration (Phase 5)

Deep dives are far more valuable when they land *inside* a user's existing knowledge base instead of in an isolated folder. Many users keep a dedicated deep-research / Obsidian "second-brain" vault with an established convention for where deep dives live and how they cross-link. This skill is otherwise vault-blind — it would ask for an output directory from scratch and produce an unlinked island. Phases 0 and 5 fix that **without** hardcoding any user-specific path: detect a vault if one exists, integrate on the vault's own terms, and stay fully generic when no vault is present.

## Phase 0 — Locate the vault

Run this *before* asking the user for an output directory. The goal is to set a smart default, not to override the user.

### Detection heuristic

A directory is a **knowledge vault** if it shows the markers below. Search likely roots first: the cloned repo's parent and sibling directories, then common locations (`~/Repos/*`, `~/Documents/*`, `~/vaults/*`, `~/notes/*`). Cheap signals:

```bash
# Strong signals (any one is a good indicator; two+ is near-certain):
#   .obsidian/        → an Obsidian vault
#   index.md + log.md at root, plus a wiki/ dir
#   a CLAUDE.md (or similar) that self-describes as a wiki/knowledge base
# Existing convention: sibling dirs ending in _deepdive (the established naming)
find <search-root> -maxdepth 2 -type d -name '.obsidian' 2>/dev/null
find <search-root> -maxdepth 3 -type d -name '*_deepdive' 2>/dev/null | head
ls <candidate>/index.md <candidate>/log.md <candidate>/CLAUDE.md 2>/dev/null
ls -d <candidate>/wiki/{entities,concepts,comparisons,sources} 2>/dev/null
```

If a vault is found, **read its governing doc first** (usually `CLAUDE.md` or `README.md` at the vault root). It typically defines: the directory structure, the page frontmatter format, the wikilink style, where deep dives go, and how `index.md`/`log.md` are maintained. The vault's own rules always win over the defaults in this file — never modify the vault's governing doc.

### Offer it as the default

When the AskUserQuestion for output location fires, make the detected vault's deep-dive convention the **recommended** option (e.g. `<vault>/<sub-area>/<project>_deepdive/source-material/`), inferring the sub-area from where similar deep dives already live. Still present alternatives and still confirm — detection sets the default, the user decides.

If **no** vault is found, fall back to the standard behavior: ask the user for `{output_dir}` with no silent default.

## Phase 5 — Wiki integration

Run this **only when the output target is a detected vault**, and only *after* the deep-dive series (Phases 1-4) is complete. The deep-dive folder is the raw artifact; the wiki layer is the synthesized, cross-linked second-brain surface. Skipping this leaves an orphan folder inside the vault.

**Always follow the vault's own conventions** (read from its governing doc in Phase 0). The steps below describe the *common* Obsidian-vault shape; adapt field names and paths to what the vault actually uses.

1. **Source page** — one summary page in `wiki/sources/<project>-codebase.md`: what was analyzed, the verified-vs-claimed numbers, the 3-4 findings that matter, and what the reference project should take. Link to the deep-dive folder.
2. **Entity pages** — create/update `wiki/entities/<project>.md` and a page for any major named subsystem worth its own node (e.g. a security scanner, a notable engine). Synthesis, not a dump.
3. **Concept pages** — create/update `wiki/concepts/<idea>.md` for any cross-cutting pattern the deep dive surfaced that spans multiple projects (e.g. a learning loop, a merge strategy). Link which systems implement it and how they differ.
4. **Comparison page** — `wiki/comparisons/<project>-vs-<reference>.md` distilling the Phase 4 comparison + the build list.
5. **Update the catalog** — add entries for every new page to `index.md` in its correct section (Entities / Concepts / Comparisons / Sources).
6. **Append the log** — add one append-only entry to `log.md` in the vault's format (commonly `## [YYYY-MM-DD] deep-dive | <Title>`) noting sources, outputs, wiki pages touched, and key findings.

### Page format (typical Obsidian vault)

```markdown
---
title: Page Title
type: entity | concept | comparison | source
tags: [tag1, tag2]
sources: [path/to/deepdive/source-material/]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Page Title

One-paragraph synthesis.

## Section
Content with [[wikilinks]] to related pages.

> **Contradiction:** flag conflicts between the marketing/research and the code explicitly.

## Related
- [[linked-page]] — why it's related
```

Use the vault's wikilink convention (short `[[name]]` or full `[[wiki/entities/name]]` — match existing pages). Link liberally; a `[[name]]` pointing at a page that doesn't exist yet is a fine forward-reference. Flag research-vs-code contradictions explicitly — they are the highest-value content a deep dive produces.

## Why this matters

A deep dive that lands in a vault and wires itself into the existing graph compounds: the next question the user asks can be answered from `index.md` → the relevant pages, and the new project's patterns are now comparable against everything already ingested. An unlinked `_deepdive/` folder is just files. The whole point of detecting the vault is to make the analysis *findable and connected*, not merely *stored*.
