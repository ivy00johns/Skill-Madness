---
name: accessibility-audit
version: 1.0.0
composes_with:
  [
    "frontend-agent",
    "qe-agent",
    "playwright",
    "ux-review",
    "ui-brief",
    "render-sanity",
    "design-token-guard",
    "code-review-agent",
    "orchestrator",
  ]
description: >-
  Audit and fix web accessibility against WCAG 2.2 AA, Section 508 and the ADA:
  axe scan, keyboard, screen-reader and zoom checks, plain-language content and
  PDFs, source fixes, and an honest conformance report (ACR/VPAT draft). Use for
  any a11y review, fix or compliance question. Trigger on "accessibility
  audit", "is this ADA compliant", "Section 508", "WCAG", "VPAT", "a11y".
compatibility: Read/edit/shell host; the scanner needs Node 18+ with playwright and @axe-core/playwright in the target project. Degrades to a source-only pass without them.
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
---

# accessibility-audit

## What this is for

Find and fix the barriers that stop disabled people from using a web UI and its
content (pages, emails, PDFs and documents), and say truthfully how close it is
to the standard a user is held to: WCAG 2.2 AA, Section 508, ADA Title II or
III, or the EU's EN 301 549.

Accessibility isn't only an engineering problem. Whoever writes a page, an
email or a PDF is a content creator, and most barriers there (vague link text,
headings used for looks, a scanned PDF, a screenshot of text, dense legal prose)
are fixed in the words, not the code. This skill covers both.

The hard part is honesty, not finding bugs. Automated engines such as axe find
roughly a third to a half of real WCAG failures. The rest (focus order, whether
alt text is meaningful, whether an error message is announced, whether a flow
works by keyboard alone) needs a human or a careful manual pass. A clean axe run
means "no machine-detectable failures on the pages scanned", nothing more.
So the rules of this skill are:

- **Never say "compliant" or "conformant"** unless every success criterion in
  scope was evaluated, including the manual ones, and passed. Say what was
  checked, what passed, what failed, and what was **Not Evaluated**.
- **Not legal advice.** You can map findings to standards and say what a
  regulation references. Whether an organization is legally exposed is a
  question for counsel. Say so once, plainly, when the user asks about legal
  compliance.
- **Never recommend an overlay widget** (a script that claims to make a site
  accessible on load) as a fix. Overlays don't change the underlying markup.
  Disabled users and advocacy groups widely oppose them, and they don't produce
  conformance. If the site already ships one, audit with it disabled too.

## Step 0: Pick the target standard

The user often names a law, not a standard. Map it, then audit against the
standard. WCAG 2.2 AA is a superset of 2.0 and 2.1 AA (except 4.1.1 Parsing,
which 2.2 removed), so auditing at 2.2 AA covers every row below. Tag each
finding with the version it first appears in, so a report can be cut to any of
them.

| The user says                                                  | Audit against                                                  | Notes                                                                                               |
| -------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| "Section 508", federal agency or contractor                    | WCAG 2.0 A + AA, plus 508 chapters 3, 5 and 6 where they apply | Revised 508 (36 CFR 1194) incorporates WCAG 2.0 AA by reference for web, documents and software.    |
| ADA Title II (state and local government, public universities) | WCAG 2.1 AA                                                    | DOJ 2024 rule. Dates were pushed back by an April 2026 interim rule; see `references/standards.md`. |
| ADA Title III (businesses open to the public)                  | WCAG 2.1 AA in practice, 2.2 AA advisable                      | No technical regulation. Settlements and court orders usually name WCAG 2.1 AA.                     |
| EU, European Accessibility Act, EN 301 549                     | WCAG 2.1 AA (EN 301 549 clause 9) plus the EN extras           | EAA has applied since 2025-06-28.                                                                   |
| "WCAG", "a11y", nothing specific                               | WCAG 2.2 AA                                                    | The current W3C recommendation.                                                                     |

Regulatory dates change, and one is under litigation as of 2026-10. Before
quoting a deadline to the user, re-check the current date in
`references/standards.md` and say when it was last verified.

## Step 1: Scope

Write down, before scanning:

- **Pages and states.** Not just routes. Also open modals, menus, error states,
  empty states, logged-in views, and every step of the key flows (sign up,
  checkout, search, submit). Most serious failures live in states, not in the
  initial render.
- **What you have.** A running URL (full audit), source only (source pass plus
  a runtime BLOCKED list), or both.
- **Mode.** `audit` (find and report; the default), `fix` (audit, then remediate
  and re-verify), `gate` (check a diff before it's called done), `content`
  (review or rewrite copy, emails, PDFs and documents; Step 3b only), or
  `report` (produce an ACR/VPAT draft from findings).

## Step 2: Automated scan

With a running app and a shell, run the bundled scanner from the target
project's root, so it resolves that project's Playwright install:

```bash
node <skill-dir>/scripts/axe_scan.mjs \
  --url http://localhost:3000/ --url http://localhost:3000/checkout \
  --widths 1440,320 --standard wcag22aa
```

It runs axe-core on every URL at every width, checks 320px reflow (WCAG 1.4.10),
and writes `.playwright/<run-id>/a11y/` with raw JSON per page, `summary.json`
and `summary.md`. Exit 0 means no violations at or above `--fail-on` (default
`serious`), 1 means violations, 2 means the scan could not run. **Exit 2 is
never a clean pass.** If the dependencies are missing, the script prints the
install command. Ask before installing them into the user's project.

axe also returns **incomplete** results: things it could not decide, such as
contrast over a background image. They go on the manual list, not into "passed".

To reach a state the URL alone doesn't open (a modal, a step 3), drive it with
the `playwright` skill, then inject axe on that page. The script's `--help`
shows the pattern. If only the Playwright MCP is available, inject axe-core
from its CDN build with `browser_evaluate` and run `axe.run()`. Same rules,
same report shape.

## Step 3: Source pass

Run this pass whether or not the scan ran. It catches what a single render
misses, and it's the whole audit when there's no running app. Use the project's
linter first if it has one (`eslint-plugin-jsx-a11y`, `eslint-plugin-vuejs-accessibility`,
`@angular-eslint` template a11y rules) and report its findings with `file:line`.
Then grep for the high-yield patterns in `references/fix-patterns.md`:
click handlers on non-interactive elements, `outline: none` with no
replacement, positive `tabindex`, `<img>` without `alt`, inputs without labels,
`aria-hidden` on focusable content, and `user-scalable=no`.

## Step 3b: Content pass

Read the words as well as the markup. Engineering checks can pass on a page
that still fails its readers. Work through `references/content-design.md`.
The high-yield checks:

- **Plain language for a named audience.** Who reads this, and what do they
  need to do? Lead with that, use short sentences and common words, and define
  jargon and legal terms with a concrete example. US federal public content is
  required to be plain by the Plain Writing Act of 2010.
- **Headings and lists that carry the structure.** Headings mark the key points
  in outline order. Lists separate items. Neither is chosen for looks.
- **Link text that says where it goes.** No "click here", "learn more" or bare
  URLs as the visible text.
- **Images that earn their place.** Alt text conveys the purpose, decorative
  images are dropped or marked `alt=""`, and text is never shared as a
  screenshot (including in emails and social posts).
- **Documents.** PDFs are exported from a tagged source document, never scanned.
  Better still, the content is published as an HTML page with the PDF as an
  extra.
- **No sensory-only instructions and no motion for decoration.** No "the green
  button on the right", and no looping GIFs or parallax.

Report content findings in the same shape as code findings, with the location
(page and section, or `file:line` for copy in source) and a suggested rewrite.
Rewrites go to the person who owns the copy. Agents propose them, and the
user decides. In `content` mode this pass is the whole job.

## Step 4: Manual checks

Required for any statement about conformance, and the most valuable part of the
audit. Work through `references/manual-checks.md`. In short:

1. **Keyboard only.** Every flow, start to finish, with Tab, Shift+Tab, Enter,
   Space, Escape and the arrow keys. No traps. Focus is always visible and never
   hidden behind a sticky header (2.4.11). Order follows the visual order.
2. **Names, roles, states.** Read the accessibility tree
   (`locator.ariaSnapshot()` in Playwright, or the MCP's `browser_snapshot`).
   Every control needs a meaningful name, the right role, and its state
   (expanded, selected, invalid). Async changes are announced through a live
   region.
3. **Zoom and reflow.** 200% zoom with no loss of content. At 320 CSS px, no
   horizontal scroll except on content that needs two dimensions, such as data
   tables and maps. Text-spacing override (1.4.12) doesn't clip text.
4. **Color and contrast.** Text 4.5:1 (3:1 for large text), and UI components
   and focus indicators 3:1 (1.4.11). Information never carried by color alone.
5. **Forms and errors.** Visible labels, errors identified in text and tied to
   their field, required fields marked, no re-entering data already given
   (3.3.7), and no cognitive puzzle to log in (3.3.8).
6. **Motion, media, time.** `prefers-reduced-motion` honored, nothing flashes
   more than 3 times a second, captions and transcripts present, auto-playing
   content can be paused, and time limits can be extended.
7. **Pointer.** Targets at least 24×24 CSS px (2.5.8), every drag action has a
   single-pointer alternative (2.5.7), and no action fires on press-down alone.

A real screen-reader pass (VoiceOver, NVDA, JAWS) is the strongest evidence.
An agent can't fully do it. Report it as **Not Evaluated, needs a human with
<reader>**, unless the user did it and told you the result.

## Step 5: Triage and report findings

One finding per barrier, not per element. Group the 40 unlabeled icon buttons
into one finding with a count and a selector list.

```markdown
### [Serious] Icon-only buttons have no accessible name — 1.1.1 / 4.1.2 (A)

- Where: `src/components/Toolbar.tsx:42`, 40 instances (`button.icon-btn`)
- Who it blocks: screen-reader users hear "button" with no purpose
- Evidence: axe `button-name`; aria snapshot shows `button` with no name
- Fix: add `aria-label="Delete row"` (or visible text); see fix-patterns §Names
```

Severity: **Blocker**, a user group can't complete a key task. **Serious**, a
task is possible but very hard, or a whole content type is lost. **Moderate**,
real friction with a workaround. **Minor**, a small deviation. Map axe impact
levels to these, but upgrade by context: a `serious` contrast failure on the
checkout button is a Blocker.

End every audit with this summary:

```markdown
## Accessibility audit — <scope>, <date>

Standard: WCAG 2.2 AA (cuttable to 2.1 AA / 2.0 AA)
Pages and states covered: N (list)
Automated: axe <version>, N violations (B/S/M/m), N incomplete → manual list
Manual: keyboard ✓, names/roles ✓, zoom/reflow ✓, contrast ✓, forms ✓,
motion/media ✓, screen reader — Not Evaluated (needs human, NVDA/VoiceOver)
Verdict: Does not yet conform — N Blockers, N Serious. Not a legal opinion.
```

## Step 6: Fix (fix mode)

Native HTML first, ARIA last: a `<button>` beats `<div role="button" tabindex="0">`
plus key handlers, because the native element brings focus, keyboard and
semantics for free. Use `references/fix-patterns.md` for the common fixes. Fix
at the shared component, not at each call site. After fixing, re-run the scan
and repeat the manual check that found the failure. The finding is closed only
when the re-check passes.

Never "fix" a finding by disabling the axe rule, adding `aria-hidden` to make a
control disappear from the tree, or adding `role="presentation"` to silence a
warning. Those hide the barrier from the tool and leave it in place for the user.

Color fixes go through the design tokens. Change the token, not the component,
and let `design-token-guard` confirm no literal was inlined.

## Step 7: Conformance report (report mode)

For an ACR (Accessibility Conformance Report) built on the ITI VPAT template,
follow `references/conformance-report.md`. Use the VPAT edition that matches the
buyer: 508, EU (EN 301 549), WCAG, or INT for all of them. Every criterion gets
**Supports**, **Partially Supports**, **Does Not Support**, **Not Applicable**,
or **Not Evaluated**, with remarks that name the failing component. Mark it a
**draft for human review**. An ACR is a vendor's legal representation, and an
agent-drafted one must be checked by someone accountable for it.

## Gate mode (before UI work is called done)

For a diff, run Step 3 on the changed files and Step 2 on the pages they
render, then do the keyboard and names checks from Step 4 on any changed
interactive component. Blockers and Serious findings in the diff mean not
done. Report pre-existing issues outside the diff separately. Don't block the
change on them.

## When the tools can't run

- **Shell, no browser or deps:** source pass (Step 3) plus a static read for
  labels, alt text, heading order and landmarks. Every runtime check (contrast
  on rendered colors, reflow, focus visibility, keyboard flow) goes on a
  **BLOCKED — needs a running app** list.
- **No shell, file read only:** the same source pass with grep and read tools.
- **Nothing readable:** give the plan (scope, standard, checks) and mark every
  result **Not Evaluated**. Don't infer pass from absence of evidence.

## How it composes

- **frontend-agent** builds to its Accessibility rule and runs gate mode before
  reporting done.
- **qe-agent** runs audit mode on the running app in integration verification
  and puts the summary in its QA report. Blockers are CRITICAL.
- **ui-brief** §8 names the target standard. This skill is how the definition
  of done is checked.
- **ux-review** looks at the overall experience. This skill goes deeper on
  accessibility and the standards, and ux-review defers here for compliance
  questions.
- **playwright** supplies the browser, the state-driving and the
  `.playwright/<run-id>/` layout.
- **render-sanity** and **design-token-guard** stay narrow and send a11y work
  here.

## References

- `references/standards.md`: WCAG 2.2 AA criteria by version, Section 508
  chapters, ADA Title II and III status with last-verified dates, and EN 301 549/EAA.
- `references/manual-checks.md`: step-by-step manual procedures, with pass and
  fail evidence for each.
- `references/fix-patterns.md`: grep patterns for the source pass and the
  standard fix for each common failure.
- `references/content-design.md`: plain language, headings, links, images,
  emails, PDFs and documents, and testing content with disabled users.
- `references/conformance-report.md`: how to fill in an ACR/VPAT honestly.
- `scripts/axe_scan.mjs`: the Playwright + axe-core scanner. Run `--help` for
  flags.
