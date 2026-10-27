# Content design for accessibility

Anyone who writes a page, an email, a PDF or a social post is a content
creator, and most content barriers are fixed in the words. This file is the
content pass (SKILL.md Step 3b, and all of `content` mode).

Sources: Digital.gov "Best practices for writing for the accessible web" and the
2020 "Writing for the accessible web" talk (18F); 18F's 2022 "Content design for
the ADA" case study (the ADA.gov redesign); Digital.gov plain language guides
(the Plain Writing Act of 2010). Links at the bottom, checked 2026-10-27.

## 1. Plain language (3.1.5 AAA; Plain Writing Act for US federal)

- **Name the audience and their task first.** Who reads this, what do they
  need to do or decide, and what do they already know? Everything below follows
  from that answer.
- **Lead with what the reader needs.** The action, answer or deadline goes
  first. Background goes after it.
- **Short sentences, common words, active voice.** Use "you" for the reader and
  "we" for the organization.
- **Define legal and technical terms with a concrete example.** The ADA.gov
  team paired broad legal wording ("fundamentally alter") with a real scenario,
  "descriptive without being prescriptive". That's more useful than either the
  wording or the example alone.
- **Stay focused.** Answering every possible question makes the page too dense
  to use, and it adds maintenance burden. Cover what the audience asks most.
  Find that out from analytics, support or helpline staff, and interviews.
- **Reading level is a signal, not a target.** WCAG 3.1.5 (AAA) asks for
  supplemental content when text needs more than a lower-secondary reading
  level. Many teams aim for roughly grade 8 for public content. Report the
  score as context and judge the text yourself. Never "fix" a score by
  chopping sentences until they stop making sense.

## 2. Structure (1.3.1, 2.4.6, 2.4.10 AAA)

- **Use headings deliberately to mark the key points**, in outline order, so
  screen-reader users can jump between them and skimmers can find their part.
  A heading that's only there to make text big is a finding.
- **Lists for parallel items.** For example, a bulleted list of what a service
  animal _is_ next to what it _is not_ is clearer than a paragraph.
- **Progressive disclosure for detail only some readers need.** Definitions,
  comparisons and edge cases can go in accordions or other collapsible
  patterns, so readers skip what doesn't apply to them. The widget must be
  accessible itself: a `<button aria-expanded>` that controls the region, or
  native `<details>`/`<summary>`. Never hide content a reader needs to finish
  the main task.
- **Tables for data only**, with header cells. Never use a table for layout.

## 3. Links (2.4.4, 1.4.1)

- Link text describes the destination or action: "Download the 2026 fee
  schedule (PDF, 2 MB)", not "click here", "link", "learn more" or "read more".
- Don't paste full URLs as the visible link text. Screen readers spell them out.
- Links look like links: a color _and_ an underline in body text.
- Name the format and size when a link opens a file, and say so when it opens
  in a new window.

## 4. Images and media (1.1.1, 1.4.5, 2.2.2, 2.3.1)

- **Ask first whether the image supports the page's purpose.** Don't add images
  for decoration only. If it stays and is decorative, use `alt=""`.
- Alt text conveys the purpose in context, not a literal inventory. A chart's
  alt gives the takeaway, and the data goes in a table or text nearby.
- **Never share text as an image.** That includes screenshots of text in emails,
  slides, social posts, and "images of text" on pages. Screen readers treat
  them as photos and can't read them, and they don't reflow or zoom.
- Avoid looping GIFs and parallax. Prefer static images and a simple scrollable
  layout. Motion causes strain and nausea for some readers, and it distracts
  everyone.
- Video: reviewed captions and a transcript. Audio: a transcript.

## 5. Emails and announcements

- Write the full message as text in the body. Don't attach a flyer image or a
  PDF as the only copy of the content.
- Use real headings and lists in HTML email, with descriptive links. Keep the
  plain-text part of the email complete.
- Emoji are read aloud by name ("rolling on the floor laughing"). Use them
  sparingly, at the end of a sentence, and never as the only carrier of meaning.

## 6. PDFs and documents (508 E205.4; WCAG via WCAG2ICT; PDF/UA)

- **Prefer HTML.** Publish the content as a web page and offer the PDF as a
  download, not as the only format.
- **Export from a word processor or a design tool with tagging on.** Use real
  heading styles, list styles, table headers, document language and title, and
  alt text on images. A PDF is only as accessible as its source file.
- **Never publish a scanned PDF.** Its text can't be selected or read by screen
  readers. OCR is a last resort, and the result still needs tagging and checking.
- Check the output: the reading order, the tags tree, the bookmarks for long
  documents, and the alt text. Use a checker such as PAC (PDF Accessibility
  Checker) or Acrobat's accessibility check. Then actually tab and read through it.
- Pick color pairings with sufficient contrast. The US Web Design System
  (designsystem.digital.gov) publishes pre-checked pairs, and those also work
  for documents.

## 7. Sensory and directional language (1.3.3, 1.4.1)

- Don't rely on shape, color, position or sound: write "Select **Submit**",
  not "click the green button on the right".
- Don't use bold, italics or ALL CAPS as the only signal of meaning. Screen
  readers usually don't announce them, and long ALL CAPS text is harder to read.

## 8. Test content with people (process, not a criterion)

- Test content with people with disabilities in every phase, and design _with_
  them, not _for_ them. The ADA.gov team did this from prototype to launch.
- Test with several audiences and iterate after each round. Fast prototypes are
  fine for this.
- Content is never finished. Review it when user needs, the law or the product
  change, and put an owner and review date on pages that cite rules or deadlines.

An agent can't run this research. In an audit, record whether it happened. If it
didn't, recommend it with the specific audiences and flows to test. Don't treat
its absence as a WCAG failure.

## Content finding template

```markdown
### [Moderate] Link text doesn't say where it goes: 2.4.4 (A)

- Where: /benefits/apply, "Eligibility" section, 6 links reading "click here"
- Who it blocks: screen-reader users browsing a links list hear "click here" ×6
- Fix (proposed rewrite, copy owner to approve):
  "To apply, click here" → "[Start your benefits application]"
```

## Sources (checked 2026-10-27)

- https://digital.gov/resources/best-practices-writing-for-accessible-web
- https://digital.gov/event/2020/03/20/writing-for-accessible-web
- https://blog.18f.org/2022/07/13/content-design-ada/
- https://digital.gov/guides/plain-language
- https://designsystem.digital.gov/ (USWDS color pairings)
