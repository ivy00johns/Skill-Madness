# Conformance reports (ACR / VPAT)

An **ACR** (Accessibility Conformance Report) is the filled-in document. The
**VPAT** (Voluntary Product Accessibility Template) from ITI is the blank
template most ACRs use. Buyers, especially US federal agencies under 508,
public universities, and EU public-sector buyers, ask vendors for one.

An ACR is a representation the vendor makes to a buyer. An agent can draft it
from audit evidence. A person accountable for the product has to review it and
sign off. Put this line at the top of every draft:

> DRAFT prepared from an automated and manual audit on <date>. Not reviewed.
> Not a legal opinion. Verify every row before release.

## Pick the edition

ITI publishes VPAT 2.5Rev (verify the current version at
https://www.itic.org/policy/accessibility/vpat before you use it) in four editions:

| Edition | Use when the buyer is       | Tables                                                |
| ------- | --------------------------- | ----------------------------------------------------- |
| 508     | US federal                  | WCAG 2.x A/AA, 508 chapters 3, 5 and 6                |
| EU      | EU (EN 301 549)             | EN 301 549 clauses 4–13, WCAG 2.1 AA via clauses 9–11 |
| WCAG    | anyone asking for WCAG only | WCAG 2.x A/AA (optionally AAA)                        |
| INT     | several of these at once    | all of the above                                      |

Use the official template's table structure. Don't invent columns. If you can't
fetch the template, produce the same tables in Markdown and say the final has to
be moved onto the official template.

## Conformance levels (use exactly these terms)

- **Supports**: the product meets the criterion without known defects, or meets
  it through an equivalent facilitation.
- **Partially Supports**: some functionality does not meet the criterion.
- **Does Not Support**: the majority of functionality does not meet it.
- **Not Applicable**: the criterion isn't relevant to the product (for example
  1.2.x when there's no media). Say why.
- **Not Evaluated**: allowed only for AAA criteria in the official template.
  For an A or AA row the audit didn't cover, the honest move is to finish that
  check. If you can't, mark the row in the draft as **NOT YET EVALUATED,
  BLOCKS RELEASE** so it can't ship as "Supports" by default.

## Remarks: where the value is

The remarks column is what buyers read. Make each one specific and verifiable:

- Bad: "Mostly supports. Some issues."
- Good: "Partially Supports. Icon-only buttons in the data-table toolbar
  (Export, Filter, Columns) have no accessible name. All other controls have
  names. Fix scheduled for 4.2."

Name the component, the scope of the failure, and the workaround if one exists.
Don't name internal ticket numbers unless the vendor wants them public.

## From audit findings to rows

1. Start every in-scope criterion as **NOT YET EVALUATED, BLOCKS RELEASE**.
2. For each criterion, collect the findings tagged with it (the audit tags every
   finding with SC numbers) and the manual-check results for it.
3. No findings and the check was done: **Supports**. Findings in a limited part
   of the product: **Partially Supports**. Findings across most of it: **Does Not Support**.
4. Write the remarks from the findings' "Where" and "Who it blocks" lines.
5. For 508: fill the chapter 3 functional performance criteria from the manual
   checks (keyboard → limited manipulation, screen reader → without vision,
   zoom → limited vision, captions → without hearing). Chapter 6: is the help
   documentation itself accessible, and does it describe the accessibility features?
6. Fill the header: product name and version, report date, contact, the
   evaluation methods (tools with versions, browsers, assistive tech actually
   used, and manual procedures), and the applicable standards.

## Evaluation methods paragraph (template)

> The product was evaluated on <date> against WCAG 2.2 Level A and AA, cut to
> <2.0/2.1> for this report. Automated testing used axe-core <version> through
> Playwright <version> in Chromium <version> at 1440 px and 320 px widths, on
> <N> pages and states (listed in the appendix). Manual testing covered
> keyboard-only operation, the accessibility tree, 200% zoom and 320 px reflow,
> text spacing, color contrast, forms and errors, reduced motion, and pointer
> target size. <Screen-reader testing with NVDA <ver> / Firefox <ver> and
> VoiceOver / Safari was performed by <role> — OR — Screen-reader testing was
> not performed.>
