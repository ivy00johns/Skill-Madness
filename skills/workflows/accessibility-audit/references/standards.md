# Standards map

**Last verified: 2026-10-27.** Regulatory dates move. Before quoting a deadline,
check the sources at the bottom. If you can't, quote it as "as of 2026-10-27".
Nothing here is legal advice.

## Contents

1. WCAG 2.2 A/AA criteria, tagged by version
2. Section 508 (US federal)
3. ADA Title II (US state and local government)
4. ADA Title III (US public accommodations)
5. HHS Section 504 rule (US health and human services recipients)
6. EU: European Accessibility Act and EN 301 549
7. Sources

## 1. WCAG 2.2 A/AA criteria by version

Audit at 2.2 AA. To cut a report down to an older version, drop the rows newer
than it. 4.1.1 Parsing exists only in 2.0 and 2.1. For HTML, the W3C errata
treat it as always satisfied, so report it **Supports** with that note.

| SC     | Name                                      | Level | Since                | Check                                       |
| ------ | ----------------------------------------- | ----- | -------------------- | ------------------------------------------- |
| 1.1.1  | Non-text Content                          | A     | 2.0                  | auto + manual (alt quality)                 |
| 1.2.1  | Audio-only and Video-only (Prerecorded)   | A     | 2.0                  | manual                                      |
| 1.2.2  | Captions (Prerecorded)                    | A     | 2.0                  | manual                                      |
| 1.2.3  | Audio Description or Media Alternative    | A     | 2.0                  | manual                                      |
| 1.2.4  | Captions (Live)                           | AA    | 2.0                  | manual                                      |
| 1.2.5  | Audio Description (Prerecorded)           | AA    | 2.0                  | manual                                      |
| 1.3.1  | Info and Relationships                    | A     | 2.0                  | auto + manual                               |
| 1.3.2  | Meaningful Sequence                       | A     | 2.0                  | manual                                      |
| 1.3.3  | Sensory Characteristics                   | A     | 2.0                  | manual                                      |
| 1.3.4  | Orientation                               | AA    | 2.1                  | manual                                      |
| 1.3.5  | Identify Input Purpose                    | AA    | 2.1                  | auto (`autocomplete-valid`) + manual        |
| 1.4.1  | Use of Color                              | A     | 2.0                  | manual                                      |
| 1.4.2  | Audio Control                             | A     | 2.0                  | manual                                      |
| 1.4.3  | Contrast (Minimum)                        | AA    | 2.0                  | auto + manual (images, gradients)           |
| 1.4.4  | Resize Text                               | AA    | 2.0                  | manual (200% zoom)                          |
| 1.4.5  | Images of Text                            | AA    | 2.0                  | manual                                      |
| 1.4.10 | Reflow                                    | AA    | 2.1                  | scanner (320px) + manual                    |
| 1.4.11 | Non-text Contrast                         | AA    | 2.1                  | manual                                      |
| 1.4.12 | Text Spacing                              | AA    | 2.1                  | manual (spacing bookmarklet / injected CSS) |
| 1.4.13 | Content on Hover or Focus                 | AA    | 2.1                  | manual                                      |
| 2.1.1  | Keyboard                                  | A     | 2.0                  | manual                                      |
| 2.1.2  | No Keyboard Trap                          | A     | 2.0                  | manual                                      |
| 2.1.4  | Character Key Shortcuts                   | A     | 2.1                  | manual                                      |
| 2.2.1  | Timing Adjustable                         | A     | 2.0                  | manual                                      |
| 2.2.2  | Pause, Stop, Hide                         | A     | 2.0                  | manual                                      |
| 2.3.1  | Three Flashes or Below Threshold          | A     | 2.0                  | manual                                      |
| 2.4.1  | Bypass Blocks                             | A     | 2.0                  | auto (`bypass`, landmarks)                  |
| 2.4.2  | Page Titled                               | A     | 2.0                  | auto + manual                               |
| 2.4.3  | Focus Order                               | A     | 2.0                  | manual                                      |
| 2.4.4  | Link Purpose (In Context)                 | A     | 2.0                  | auto + manual                               |
| 2.4.5  | Multiple Ways                             | AA    | 2.0                  | manual                                      |
| 2.4.6  | Headings and Labels                       | AA    | 2.0                  | manual                                      |
| 2.4.7  | Focus Visible                             | AA    | 2.0                  | manual                                      |
| 2.4.11 | Focus Not Obscured (Minimum)              | AA    | 2.2                  | manual                                      |
| 2.5.1  | Pointer Gestures                          | A     | 2.1                  | manual                                      |
| 2.5.2  | Pointer Cancellation                      | A     | 2.1                  | manual                                      |
| 2.5.3  | Label in Name                             | A     | 2.1                  | auto (partial) + manual                     |
| 2.5.4  | Motion Actuation                          | A     | 2.1                  | manual                                      |
| 2.5.7  | Dragging Movements                        | AA    | 2.2                  | manual                                      |
| 2.5.8  | Target Size (Minimum)                     | AA    | 2.2                  | auto (`target-size`) + manual               |
| 3.1.1  | Language of Page                          | A     | 2.0                  | auto                                        |
| 3.1.2  | Language of Parts                         | AA    | 2.0                  | manual                                      |
| 3.2.1  | On Focus                                  | A     | 2.0                  | manual                                      |
| 3.2.2  | On Input                                  | A     | 2.0                  | manual                                      |
| 3.2.3  | Consistent Navigation                     | AA    | 2.0                  | manual                                      |
| 3.2.4  | Consistent Identification                 | AA    | 2.0                  | manual                                      |
| 3.2.6  | Consistent Help                           | A     | 2.2                  | manual                                      |
| 3.3.1  | Error Identification                      | A     | 2.0                  | manual                                      |
| 3.3.2  | Labels or Instructions                    | A     | 2.0                  | auto + manual                               |
| 3.3.3  | Error Suggestion                          | AA    | 2.0                  | manual                                      |
| 3.3.4  | Error Prevention (Legal, Financial, Data) | AA    | 2.0                  | manual                                      |
| 3.3.7  | Redundant Entry                           | A     | 2.2                  | manual                                      |
| 3.3.8  | Accessible Authentication (Minimum)       | AA    | 2.2                  | manual                                      |
| 4.1.1  | Parsing                                   | A     | 2.0 (removed in 2.2) | n/a for HTML (see above)                    |
| 4.1.2  | Name, Role, Value                         | A     | 2.0                  | auto + manual                               |
| 4.1.3  | Status Messages                           | AA    | 2.1                  | manual                                      |

axe tags for the scanner's `--standard`: `wcag2a wcag2aa` (2.0), adding
`wcag21a wcag21aa` (2.1), adding `wcag22aa` (2.2). `best-practice` rules are
useful but aren't WCAG failures. Report them separately.

## 2. Section 508 (US federal ICT)

The Revised 508 Standards (36 CFR Part 1194, Appendices A, C and D) apply to ICT
that federal agencies develop, buy, maintain or use. Contractors meet them through
procurement, usually by supplying an ACR.

- **E205 Electronic content.** Public-facing content and nine kinds of agency
  official communications must conform to **WCAG 2.0 Level A and AA**.
  E205.4 applies the same criteria to non-web documents (PDF, Word, slides),
  with word substitutions ("document" for "web page"). For PDFs, PDF/UA
  techniques are the practical route to the WCAG criteria.
- **Chapter 3, Functional Performance Criteria (302).** Use without vision,
  with limited vision, without color perception, without hearing, with limited
  hearing, without speech, with limited manipulation, strength or reach, and
  with limited language, cognitive and learning abilities. These apply when
  WCAG doesn't address a feature, or when an exception is claimed.
- **Chapter 5, Software (501–504).** Interoperability with assistive technology
  (502), application preferences and captions (503), and authoring tools (504).
  WCAG 2.0 AA applies to software too, through E207.2 with the WCAG2ICT
  interpretation.
- **Chapter 6, Support documentation and services (602–603).** Help docs must
  themselves be accessible and describe accessibility features. Support
  services must accommodate users who are deaf, hard of hearing or blind.
- **Chapter 4 (hardware)** is out of scope for a web audit. Mark it Not Applicable.

508 hasn't adopted WCAG 2.1 or 2.2. Agencies and buyers often ask for 2.1 or 2.2
AA anyway, which is why auditing at 2.2 AA and cutting down is the default.

## 3. ADA Title II (state and local government)

- **Rule:** DOJ final rule, April 2024 (28 CFR Part 35, Subpart H). Technical
  standard: **WCAG 2.1 Level AA** for web content and mobile apps.
- **Compliance dates as of 2026-10-27:** an interim final rule issued
  2026-04-20 moved them one year later: **2027-04-26** for public entities
  serving a population of 50,000 or more, and **2028-04-26** for smaller
  entities and all special district governments. The technical standard didn't
  change. DOJ said it may revisit the technical standard in later rulemaking.
- **Litigation:** the National Federation of the Blind sued to challenge the
  extension. No ruling was found as of 2026-10-12. Re-check before quoting.
- **Exceptions** (narrow; verify each against the rule text): archived web
  content, preexisting conventional electronic documents, content posted by
  third parties, individualized password-protected documents, and preexisting
  social media posts. "We'll claim an exception" isn't a remediation plan for
  anything users need today.

## 4. ADA Title III (businesses open to the public)

There's no DOJ technical regulation for websites under Title III. DOJ's
position is that the ADA covers the web services of public accommodations.
Courts are split on sites with no physical location. In practice, demand
letters, settlements and consent decrees name **WCAG 2.1 AA** (increasingly
2.2 AA). Audit at 2.2 AA and report the 2.1 AA cut.

## 5. HHS Section 504 rule (health and human services recipients)

HHS's 2024 Section 504 rule requires recipients of HHS funding to meet **WCAG
2.1 AA** for web content and mobile apps. Recipients with 15 or more employees
had until 2026-05-11, and smaller ones until 2027-05-10. As of 2026-10-27,
**whether HHS extended its date is unverified.** Check before quoting.

## 6. EU: European Accessibility Act and EN 301 549

- **EAA** (Directive (EU) 2019/882) has applied since **2025-06-28** to
  products and services in scope, including e-commerce, banking, e-books,
  transport ticketing and electronic communications. Microenterprises providing
  services are exempt. Each member state enforces it under its own law.
- **EN 301 549** is the harmonized standard. Clause 9 (web) and clause 10 (non-web
  documents) match **WCAG 2.1 AA**, and clause 11 covers software. Extra
  clauses cover things WCAG doesn't, such as real-time text, video caption
  handling and accessibility documentation (clause 12). An update aligning it
  with WCAG 2.2 has been in progress. Its publication status is unverified as
  of 2026-10-27.
- The public sector is covered separately by the Web Accessibility Directive
  (EU) 2016/2102, which also uses EN 301 549.

## 7. Sources (checked 2026-10-27)

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Revised 508 Standards: https://www.access-board.gov/ict/
- DOJ Title II extension coverage:
  https://www.insidehighered.com/news/government/colleges-localities/2026/04/21/doj-extends-web-accessibility-deadline ·
  https://www.jacksonlewis.com/insights/doj-extends-public-entities-compliance-deadline-ada-related-website-accessibility-hhss-may-2026-deadline-still-looms ·
  https://titleii.org/title-ii-updates
- ITI VPAT: https://www.itic.org/policy/accessibility/vpat
- EAA: https://eur-lex.europa.eu/eli/dir/2019/882/oj
