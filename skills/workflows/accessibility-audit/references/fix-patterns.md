# Source-pass patterns and fixes

Each row has a grep that finds candidates and the fix. Grep hits are
**candidates**. Read the surrounding code before you file a finding, because
many hits are fine in context (an `onClick` on a `<button>`, `outline: none`
next to a `:focus-visible` style).

## Grep patterns (ripgrep syntax)

| Pattern                                                                | Finds                                              | Likely SC          |
| ---------------------------------------------------------------------- | -------------------------------------------------- | ------------------ |
| `<(div\|span\|li\|td\|img)[^>]*\bon(Click\|click\|:click\|\(click\))`  | click handler on a non-interactive element         | 2.1.1, 4.1.2       |
| `outline:\s*(none\|0)`                                                 | focus indicator removed                            | 2.4.7              |
| `tabindex="?[1-9]` / `tabIndex=\{[1-9]`                                | positive tabindex (breaks focus order)             | 2.4.3              |
| `<img(?![^>]*\balt=)` (needs `rg -P`)                                  | image with no alt                                  | 1.1.1              |
| `alt="(image\|photo\|picture\|icon\|logo)?"` with an informative image | missing or useless alt                             | 1.1.1              |
| `<input(?![^>]*(aria-label\|aria-labelledby\|id=))` (needs `rg -P`)    | input that likely has no label                     | 1.3.1, 3.3.2       |
| `placeholder=` with no adjacent `<label`                               | placeholder used as the label                      | 3.3.2              |
| `aria-hidden="?true` on an element containing a link, button or input  | focusable content hidden from AT                   | 4.1.2              |
| `user-scalable\s*=\s*no\|maximum-scale\s*=\s*1(\.0)?\b`                | zoom disabled                                      | 1.4.4              |
| `role="button"`                                                        | custom button; check for tabindex and key handlers | 2.1.1, 4.1.2       |
| `<a(?![^>]*href)` (needs `rg -P`)                                      | anchor used as a button                            | 2.1.1, 4.1.2       |
| `onMouseDown\|onmousedown\|@mousedown\|onTouchStart`                   | action fires on press-down                         | 2.5.2              |
| `autoplay`                                                             | auto-playing media                                 | 1.4.2, 2.2.2       |
| `<html(?![^>]*\blang=)` (needs `rg -P`)                                | missing page language                              | 3.1.1              |
| `@keyframes\|animation:` with no `prefers-reduced-motion` anywhere     | motion with no reduced-motion path                 | 2.3.3 (AAA), 2.2.2 |

Framework linters cover most of this with fewer false positives. When the
project has `eslint-plugin-jsx-a11y` (React), `eslint-plugin-vuejs-accessibility`
(Vue), `@angular-eslint/template` accessibility rules, or `svelte-check` a11y
warnings, run them first and report their output. Recommend adding one when
none is configured. That's the regression guard, the same role
`design-token-guard` plays for colors.

## Fixes

### Names (1.1.1, 2.5.3, 4.1.2)

- Icon-only button: `<button aria-label="Close dialog"><XIcon aria-hidden="true" /></button>`.
  Or add visually hidden text with a `.sr-only` / `.visually-hidden` class.
- The visible label must be part of the name. A button that reads "Send" gets
  `aria-label="Send message"`, not `aria-label="Submit form"`.
- Decorative image: `alt=""`. An image inside a link that has text: `alt=""`.
  An image that is the only content of a link: alt names the destination.
- SVG icons: `aria-hidden="true" focusable="false"` when decorative, or
  `role="img"` with a `<title>` when informative.

### Keyboard (2.1.1, 2.1.2, 2.4.3)

- Replace `<div onClick>` with `<button type="button">`. If the element must stay
  a div, it needs `role="button"`, `tabindex="0"`, and Enter and Space handlers.
  That's three things to get right instead of zero, which is why the native
  element wins.
- Links navigate and buttons act. `<a href="#" onClick>` becomes `<button>`.
- Remove positive `tabindex`. Fix the DOM order instead.
- Composite widgets (menu, tabs, listbox, grid) use roving `tabindex` or
  `aria-activedescendant` with arrow keys. Follow the WAI-ARIA Authoring
  Practices pattern for that widget, and prefer a well-tested library
  primitive (Radix, React Aria, Headless UI, Angular CDK) over hand-rolled code.

### Focus (2.4.7, 2.4.11, 1.4.11)

- Never remove an outline without replacing it:
  `:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }`
  The ring color comes from a design token and needs 3:1 against adjacent colors.
- Sticky headers that cover focused elements: add `scroll-padding-top` equal to the header height.
- Dialogs: use the native `<dialog>` with `showModal()`, or a library dialog. It
  traps focus, closes on Escape, and returns focus to the trigger.

### Forms (1.3.1, 1.3.5, 3.3.1–3.3.3)

```html
<label for="email">Email</label>
<input
  id="email"
  type="email"
  autocomplete="email"
  required
  aria-invalid="true"
  aria-describedby="email-err"
/>
<p id="email-err">Enter an email address like name@example.com</p>
```

- Group radio buttons and checkboxes in a `<fieldset>` with a `<legend>`.
- On submit with errors, either move focus to an error summary that links to
  each field, or move focus to the first invalid field. The summary should be
  `role="alert"` or receive focus.

### Live regions (4.1.3)

- Render the region empty on page load, then change its text:
  `<div role="status" aria-live="polite" class="sr-only">{message}</div>`.
  A region inserted together with its message is often not announced.
- Use `role="alert"` only for errors and time-critical messages. It interrupts.

### Structure (1.3.1, 2.4.1, 2.4.6)

- One `<main>`, plus `<nav>`, `<header>` and `<footer>`. A skip link as the first
  focusable element: `<a href="#main" class="skip-link">Skip to content</a>`.
- Headings by outline level, not by size. Style a heading with CSS. Don't pick a
  heading level for its look.
- Data tables: `<th scope="col">`, plus a `<caption>`. Layout tables:
  `role="presentation"`, or better, CSS grid.

### Contrast and color (1.4.1, 1.4.3, 1.4.11)

- Fix the token, not the instance, and re-run `design-token-guard`.
- Add a non-color cue: an underline on links in body text, an icon plus text on
  errors, and patterns or labels on chart series.

### Motion (2.2.2, 2.3.1)

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Carousels and auto-advancing content get a visible pause button.

### Target size and drag (2.5.7, 2.5.8)

- Give small icon buttons `min-width` and `min-height` of 24px (44px on touch),
  or pad the hit area with a pseudo-element.
- Sortable lists: add move-up and move-down buttons or a "Move to…" menu next to
  the drag handle.

## Anti-fixes (these hide the barrier from the tool, not from the user)

- Disabling an axe or lint rule, inline or in config, to get a clean run.
- Adding `aria-hidden="true"` or `role="presentation"` to a control so it stops being flagged.
- `aria-label` on a `<div>` with no role. It's ignored by most screen readers.
- ARIA that contradicts native semantics, such as `<button role="link">` or
  `<h2 role="button">`.
- Overlay widgets, and "accessibility mode" toggles that are the only
  accessible path.
- Alt text stuffed with keywords, or alt equal to the file name.
