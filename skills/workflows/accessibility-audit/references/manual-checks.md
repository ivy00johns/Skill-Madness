# Manual checks

The automated scan can't decide these. Each check lists how to do it, what a
pass looks like, and the evidence to record. With Playwright, most of them can
be driven and recorded. The judgment ("is this alt text meaningful?") is still
yours, so write it down as a judgment.

Record each check as **Pass**, **Fail** (with a finding), or **Not Evaluated**
(with the reason). Never leave one blank. An unrecorded check reads as a pass.

## 1. Keyboard (2.1.1, 2.1.2, 2.4.3, 2.4.7, 2.4.11, 3.2.1)

How: start at the top of the page, then Tab through to the end and Shift+Tab
back. In each widget use the keys users expect: Enter or Space on buttons,
arrow keys in menus, tabs, radio groups and listboxes, Escape to close dialogs
and popovers. Complete every key flow without the mouse.

With Playwright: `page.keyboard.press('Tab')` in a loop, recording
`document.activeElement` (tag, accessible name, bounding box) and taking a
screenshot at each stop. The sequence is your focus-order evidence.

Pass:

- Every interactive element is reachable, and nothing non-interactive is a tab stop.
- Order follows reading order. Positive `tabindex` is almost always the cause
  when it doesn't.
- Focus is always visible. Check each stop's screenshot for a visible indicator
  with at least 3:1 contrast against its surroundings.
- Focus is never fully hidden under a sticky header, footer or cookie banner (2.4.11).
- Opening a dialog moves focus into it, Tab stays inside, Escape closes it, and
  focus returns to the control that opened it.
- Receiving focus never changes context by itself (no auto-submit, no navigation).
- A skip link, or landmarks, lets users bypass repeated navigation (2.4.1).

## 2. Names, roles and states (1.1.1, 1.3.1, 2.4.6, 2.5.3, 4.1.2, 4.1.3)

How: read the accessibility tree, not the DOM. `await page.locator('body').ariaSnapshot()`
or `browser_snapshot` gives roles, names and states as a screen reader would get them.

Pass:

- Every control's name says what it does: "Delete invoice 1042", not "button",
  "click here" or an icon's file name.
- The visible label text is contained in the accessible name (2.5.3), so voice
  users can say what they see.
- Roles match behavior. A thing that opens a menu is a button with
  `aria-expanded`, not a link. Tabs are `tab`/`tablist`/`tabpanel` with
  `aria-selected`.
- States update: expanded/collapsed, checked, selected, invalid, disabled.
- Images: informative images have alt text that conveys the same information.
  Decorative images have `alt=""`. Complex images (charts) have a text
  equivalent nearby.
- Headings form an outline (one `h1`, no skipped levels used for styling), and
  landmarks exist (`main`, `nav`, `header`, `footer`).
- Status messages (saved, 3 results, error) are in a live region (`role="status"`,
  `aria-live="polite"`, or `role="alert"` for errors) that exists before the
  message is inserted.

## 3. Zoom, reflow and text spacing (1.4.4, 1.4.10, 1.4.12, 1.3.4)

How:

- **200% zoom:** set the viewport to half width at the same device scale, or use
  browser zoom. Nothing is cut off or overlapped, and every function is still
  reachable.
- **Reflow:** at a 320 CSS px wide viewport, there's no horizontal scrolling of
  the page. The scanner checks `scrollWidth > clientWidth` at each width. Data
  tables, maps, diagrams and toolbars that need two dimensions are exempt. Note
  them, don't fail them.
- **Text spacing:** inject this CSS and look for clipped or overlapping text:
  `* { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; } p { margin-bottom: 2em !important; }`
- **Orientation:** the layout works in both portrait and landscape, unless one is
  essential.

## 4. Color and contrast (1.4.1, 1.4.3, 1.4.11)

- Text: 4.5:1, or 3:1 for large text (≥24px regular or ≥18.66px bold).
  axe checks most text. Check by hand the text over images and gradients, text
  in disabled-looking but enabled controls, and placeholder text used as a label.
- Non-text: 3:1 for input borders, focus rings, icons that carry meaning, chart
  segments, and the checked state of toggles.
- Color alone: links in body text are distinguishable without color (underline,
  or 3:1 against the text plus a non-color cue on hover and focus). Errors aren't
  shown only by turning a border red. Chart series differ by more than hue.

## 5. Forms and errors (1.3.5, 3.3.1–3.3.4, 3.3.7, 3.3.8)

How: submit each form empty, then with invalid values, using the keyboard only.

Pass:

- Every field has a visible, persistent label. Placeholder alone fails.
- Required fields are indicated in text or with an accessible marker, not only
  by color.
- Errors name the field and the problem in text, are tied to the field with
  `aria-describedby`, set `aria-invalid="true"`, and are announced (live
  region, or focus moves to an error summary).
- Suggestions are given where known ("Use the format MM/YYYY").
- Legal, financial and data-deleting submissions can be reviewed, corrected or reversed.
- Personal-data fields use `autocomplete` tokens (`email`, `given-name`, `tel`, …).
- Nothing already entered in the same process is asked for again, unless it's a
  security re-entry (3.3.7).
- Login doesn't require a cognitive function test (memorizing, transcribing, or
  solving a puzzle) without an alternative. Pasting into password fields and
  password managers works (3.3.8).

## 6. Motion, media and time (1.2.x, 2.2.1, 2.2.2, 2.3.1)

- With `prefers-reduced-motion: reduce` (Playwright `emulateMedia({ reducedMotion: 'reduce' })`),
  non-essential animation stops or is replaced by a fade.
- Anything that moves, blinks or auto-updates for more than 5 seconds has a
  pause control.
- Nothing flashes more than three times a second.
- Video has accurate captions, not auto-captions left unreviewed. Prerecorded
  video has audio description, or a transcript where 1.2.3 allows. Audio has a
  transcript. Auto-playing audio longer than 3 seconds can be stopped.
- Session timeouts warn the user and let them extend, unless the limit is essential.

## 7. Pointer and input (2.5.1, 2.5.2, 2.5.4, 2.5.7, 2.5.8, 2.1.4, 1.4.13)

- Targets are at least 24×24 CSS px, or have enough spacing (2.5.8). 44×44 is
  the comfortable floor for touch.
- Multi-point or path gestures (pinch, swipe) have a single-pointer alternative,
  and drag-and-drop has a click alternative, such as move-up/move-down buttons
  or a menu (2.5.7).
- Actions fire on release (`click`), not on `mousedown` or `touchstart`, so
  users can slide off to cancel.
- Shake or tilt features have a button alternative and can be turned off.
- Single-character shortcuts can be turned off or remapped, or are active only on focus.
- Tooltips and hover cards can be dismissed with Escape, can be hovered without
  vanishing, and stay until dismissed (1.4.13).

## 8. Content and consistency (1.3.3, 2.4.2, 2.4.4, 2.4.5, 3.1.x, 3.2.3, 3.2.4, 3.2.6)

- Each page has a unique, descriptive `<title>`, and `<html lang>` is set.
  Passages in another language carry their own `lang`.
- Instructions don't rely only on shape, position or sound ("click the round
  button on the right").
- Navigation and repeated components appear in the same order and with the
  same names on every page. Help (contact, chat, FAQ) is in the same place on
  every page that has it.
- There's more than one way to find a page (nav plus search or a sitemap),
  except for steps in a process.

## 9. Screen reader pass (strongest evidence; usually needs a human)

An agent can approximate this with the accessibility tree (check 2). A real pass
is with NVDA or JAWS on Windows (Chrome or Firefox) and VoiceOver on macOS and
iOS (Safari), plus TalkBack on Android for mobile. Run each key flow listening
only: the reading order makes sense, every control announces its name, role
and state, and dynamic updates are spoken. If no one ran it, the report says
**Not Evaluated, needs a human with <reader>/<browser>**. Never infer it from axe.
