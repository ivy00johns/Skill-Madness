# Anti-Claudenese / Anti-Slop Writing Research

> Research brief: getting Claude to write plain, human English instead of "claudenese"
> (em dashes, "delve", "it's not X, it's Y", rule-of-three, bullet soup, sycophantic openers).
>
> - **Date:** 2026-09-01 · window 2026-08-02 → 2026-09-01
> - **Method:** `/last30days` engine (Reddit, X, YouTube, TikTok, Instagram, HN, GitHub, Digg) + web supplements
> - **Raw data:** `~/Documents/Last30Days/claude-plain-english-writing-anti-slop-raw-v3.md`
> - **Coverage caveat:** Reddit was partial (HTTP 429 after 35 threads) — Reddit-side conclusions are under-sampled.
> - **Purpose:** integration source for a Skill-Madness writing-style skill / CLAUDE.md rule block.

---

## TL;DR — the three findings that matter

1. **The community converged on a single canonical spec:** [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). A whole family of "Humanizer" skills is built directly off it rather than off personal taste.
2. **Specific named rules beat vague asks.** "Humanize this" does nothing; "zero em dashes, no 'delve', short active sentences, direct you/your wording" works.
3. **Persistence is the delivery mechanism.** The recommendation moved from per-chat prompts to standing config: a skill folder, a plugin, or CLAUDE.md rules that fire on every response.

---

## 1. The canonical spec

| Resource | Link | Notes |
|---|---|---|
| Wikipedia: Signs of AI writing | <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing> | ~15,000-word field guide from WikiProject AI Cleanup; the ground truth every serious skill now cites. Covers vocabulary, structure, formatting, vague attribution, inflated symbolism. |
| Talk page (ongoing debate) | <https://en.wikipedia.org/wiki/Wikipedia_talk:Signs_of_AI_writing> | Editor discussion; useful for edge cases and false-positive caveats. |
| TechCrunch coverage | <https://techcrunch.com/2025/11/20/the-best-guide-to-spotting-ai-writing-comes-from-wikipedia/> | "The best guide to spotting AI writing comes from Wikipedia." |
| MakeUseOf coverage | <https://www.makeuseof.com/wikipedia-best-ai-writing-detection-guide/> | Secondary coverage of the same page. |
| Blake Stockton: 10 takeaways | <https://www.blakestockton.com/takeaways-from-wikipedias-signs-of-ai-writing-2/> | Condensed practitioner digest of the Wikipedia page. |
| Worldcom Group: 7 telltale patterns | <https://worldcomgroup.com/insights/how-to-spot-ai-writing-tips-from-wikipedia-on/> | Another condensed digest. |
| Beutler Ink digest | <https://www.beutlerink.com/blog/how-to-spot-ai-writing> | Agency-side summary of the Wikipedia signs. |
| Erkan Saka (Medium) on the page's discussion | <https://medium.com/@sakaerka/wikipedia-discussion-signs-of-ai-writing-11a98ff61669> | Commentary on the editorial debate around the page. |

## 2. Skills & repos (primary integration targets)

### The Humanizer family (Wikipedia-spec implementations)

Multiple independent implementations of the same idea: package Wikipedia's signs list as a Claude skill. Enforce 9 rule categories — Vocabulary, Structure, Opinions, Voice, Sycophancy, Rhythm, Specificity, Formatting, Context Windows.

| Repo | Link | Install / notes |
|---|---|---|
| blader/humanizer | <https://github.com/blader/humanizer> | `git clone https://github.com/blader/humanizer.git ~/.claude/skills/humanizer` |
| jooray/humanizer | <https://github.com/jooray/humanizer> | Claude Code plugin: `/plugin marketplace add jooray/humanizer` then `/plugin install humanizer@humanizer` |
| WhimseyAI/humanizer-skill | <https://github.com/WhimseyAI/humanizer-skill> | claude.ai path: upload humanizer.zip at claude.ai/customize/skills; also works for ChatGPT |
| Aparnabuilds/humanizer | <https://github.com/Aparnabuilds/humanizer> | 63 patterns from Wikipedia's signs + AI-detector research; also enforces honest claims |
| jpeggdev/humanize-writing | <https://github.com/jpeggdev/humanize-writing> | Claude Code skill that rewrites AI-generated content to sound human |

Directory/marketplace listings for the Humanizer skill:
[OneAway](https://oneaway.io/skills/humanizer) · [samuelasantos claude-skills](https://samuelasantos.github.io/claude-skills/skills/humanizer.html) · [discoveraiskills.com](https://discoveraiskills.com/skills/humanizer) · [skillsrep.com](https://skillsrep.com/skill/humanizer)

### stop-slop (biggest adoption signal)

| Resource | Link | Notes |
|---|---|---|
| hardikpandya/stop-slop | <https://github.com/hardikpandya/stop-slop> | 70+ cataloged prose patterns as a skill file; the engine's GitHub pull showed ~16.6K combined stars across the anti-slop pair, with stop-slop the bulk of it. Prose-focused (posts, docs, emails). |
| Marketplace listing | <https://claudemarketplaces.com/skills/hardikpandya/stop-slop/stop-slop> | Listed at ~7.1k on claudemarketplaces.com. |
| Author write-up | <https://hardik.substack.com/p/new-claude-skill-stop-ai-slop-in> | "New Claude Skill: Stop AI Slop in Your Content." |
| Gabriel Cassady review | <https://gabrielcassady.com/tools/stop-slop-claude-skill-to-remove-ai-writing-tells/> | Third-party review of the skill. |

### Standing-config systems (CLAUDE.md / system prompt)

| Repo | Link | Notes |
|---|---|---|
| BioInfo/slopless | <https://github.com/BioInfo/slopless> | Production-tested CLAUDE.md from 18 months of daily use; 78 numbered principles; anti-slop writing + behavioral guidelines + model routing. Strongest practitioner-testimony signal in the corpus. |
| adenaufal/anti-slop-writing | <https://github.com/adenaufal/anti-slop-writing> | Universal system prompt: 60+ banned words with plain-English replacements, 8 banned-phrase categories, structural clichés (binary contrasts, dramatic fragmentation, rhetorical setups, false agency), a four-question filter. Works across Claude Code, Codex, Cursor, Gemini CLI, Copilot. |
| jalaalrd/anti-ai-slop-writing | <https://github.com/jalaalrd/anti-ai-slop-writing> | Same category; claims compatibility with 8+ agents. |
| anti-slop (MCP Hub listing) | <https://www.aimcp.info/en/skills/a26214e0-740d-4eb2-a566-937a5b4b70bb> | Directory listing for an anti-slop skill. |

## 3. Guides & prompt articles

| Source | Link | Key contribution |
|---|---|---|
| Will Francis | <https://willfrancis.com/how-to-stop-claude-writing-like-an-ai/> | Ready-made prompt: ban-list (delve, leverage, seamless, game-changer…), max one em dash per response, no "not only… but also", vary sentence length. |
| Sabrina Ramonov (sabrina.dev) | <https://www.sabrina.dev/p/how-to-make-chatgpt-and-claude-sound-human> | The "specific rules beat vague asks" argument; companion to her Instagram reel below. |
| Vibe Working (Substack) | <https://vibeproductmarketing.substack.com/p/ai-writes-like-ai-slop> | Prevention-side framing: fix the system prompt, don't post-edit slop. |
| AI Academy / Techpresso | <https://academy.techpresso.co/prompts/claude-write-like-a-human-prompt> | 20 Claude "write like a human" prompts; source of the common banned-words list. |
| AI Solopreneur Hub | <https://aisolopreneurhub.substack.com/p/how-to-humanize-ai-text-a-complete> | Complete humanizing walkthrough (scan for "delve"/"tapestry"/"unlock", replace with conversational synonyms). |
| PromptPal Community Vault | <https://promptpal.substack.com/p/community-vault-drop-04-popular-reddit> | Archives the popular Reddit "humanize AI content" post. |
| MindStudio | <https://www.mindstudio.ai/blog/claude-design-avoid-ai-slop-design-system> | The same anti-slop idea applied to design output (design-system approach). |
| Maverick AI guide | <https://mavgpt.ai/resources/humanize-ai-text-guide-2026> | 2026 humanize-AI-text overview. |

## 4. Social evidence (30-day window, with engagement)

| Platform | Item | Link | Signal |
|---|---|---|---|
| TikTok | @lvl_aiautomations: "How to stop AI-Slop Writing" | <https://www.tiktok.com/@lvl_aiautomations/video/7679989573916658951> | Pitches the Humanizer skill as "built directly off Wikipedia's own documented list of AI writing tells. Two-line install." (2026-08-31) |
| Instagram | @sabrina_ramonov: Claude style prompt reel | <https://www.instagram.com/reel/DcEKRJMCPTM/> | 1,934 likes / 5,559 comments. "Specific rules instead of a vague request to 'humanize this'": no em dashes, short active sentences, direct you/your wording, no generic AI phrases. |
| Instagram | @thedigital.indian: humanize-via-Wikipedia reel | <https://www.instagram.com/reel/DcOkCRbCbJj/> | 1,791 likes / 3,990 comments. Manual version of the Humanizer play: point Claude at the Wikipedia signs page, list every tell, apply. Framed around beating AI detectors ("0% AI-generated") — detector-gaming framing, treat with caution. |
| TikTok | @aiunlocked.0: multi-tool "relay race" | <https://www.tiktok.com/@aiunlocked.0/video/7678785139547114774> | Brainstorm→ChatGPT, draft→Claude, edit→Grammarly. Engagement-bait shape, low signal; recorded for completeness. |
| YouTube | "Stop AI Slop: Free Anti-Slop Skill for Claude Code and Codex" | <https://www.youtube.com/watch?v=jxTGZEcvtsU> | Walkthrough of a free anti-slop skill. |
| LinkedIn | Jenna Potter: "I built a Claude skill that stops AI…" | <https://www.linkedin.com/posts/videojenna_i-built-a-claude-skill-that-stops-ai-from-activity-7445889349021265920-yWnV> | Another independent skill-builder data point. |
| Threads | @ainspirehub: 5 Claude prompts to remove AI tells | <https://www.threads.com/@ainspirehub/post/DURFUkLDtRK/> | Prompt-pack format of the same rules. |

Adjacent (surfaced by the engine, on-Claude but not on-topic — kept for context only):
[Anthropic: Claude Code best practices](https://www.youtube.com/watch?v=gv0WHhKelSE) (550K views) · [Vaibhav Sisinty: Claude Code 2026 full course](https://www.youtube.com/watch?v=_0xa6RVqTC8) (380K views) · [Nate Herk: Master 95% of Claude Code Skills](https://www.youtube.com/watch?v=zKBPwDpBfhs) (224K views)

## 5. Hacker News threads

| Thread | Link | Takeaway |
|---|---|---|
| Hallmark — Anti-AI-Slop Design Skill | <https://news.ycombinator.com/item?id=49058547> | The skeptical counterweight: a commenter noted most examples generated from the skill file still looked like slop. A skill is a filter, not a guarantee. |
| "i took a swing at an anti-slop skill for Claude Code" | <https://news.ycombinator.com/item?id=45684305> | Grassroots skill-building thread. |

## 6. The distilled rule set (what recurs across every source)

The intersection of the Wikipedia spec, stop-slop, slopless, anti-slop-writing, and the creator prompts:

**Ban outright**
- Em dashes and en dashes (use ` - `, commas, or parentheses; some sources allow max one em dash per response)
- Vocabulary tells: delve, leverage, seamless, tapestry, unlock, unleash, harness, elevate, landscape, game-changer, cutting-edge, transformative, groundbreaking, paradigm, synergy, empower, streamline, utilize, unprecedented, innovative
- Throat-clearing openers ("In today's rapidly evolving landscape…")
- Negative parallelism ("It's not X, it's Y" / "not only… but also")
- Rule-of-three everywhere (triplet lists as a rhythm crutch)
- Sycophantic openers and performative hedging
- The three-bullet summary nobody asked for; excessive boldface/headers/title case

**Require instead**
- Short, active sentences; varied sentence length
- Direct "you/your" address; concrete examples over abstractions
- Direct claims with evidence instead of hype framing
- Specific attribution instead of vague "experts say" / "studies show"
- Prose paragraphs by default; structure only when it carries information

**Delivery**
- Persistent config (skill folder / plugin / CLAUDE.md), not a re-pasted prompt
- Anchor on the Wikipedia spec so the rules are citable and updatable, not taste-based

## 7. Integration notes for Skill-Madness

- **Best-fit shape:** a source-level writing gate in the spirit of `design-token-guard` / `class-extraction-guard` — a "prose-slop-guard" that role agents (docs-agent, git-pr, wiki-research, interactive-doc, llm-wiki) compose with, plus a distillable CLAUDE.md block.
- **Spec anchoring:** build the ban/require lists off [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) with a `references/` file mirroring the categories (Vocabulary, Structure, Opinions, Voice, Sycophancy, Rhythm, Specificity, Formatting), the same way the Humanizer family does.
- **Prior art worth reading before writing anything:** [stop-slop](https://github.com/hardikpandya/stop-slop) (pattern catalog), [slopless](https://github.com/BioInfo/slopless) (CLAUDE.md integration style + 78 principles), [adenaufal/anti-slop-writing](https://github.com/adenaufal/anti-slop-writing) (cross-agent portability, four-question filter). Note the repo already ships a `hallmark` skill; check overlap with the [Hallmark HN thread](https://news.ycombinator.com/item?id=49058547) lineage before duplicating design-side anti-slop.
- **Known limitation to encode:** the HN skepticism — filtered output can still read as slop. Pair the rule set with a fresh-context evaluator pass (the `loop-controller` evaluator pattern) rather than trusting self-grading.
- **License hygiene:** per repo convention (CB-3 lesson), borrow patterns with attribution in ACKNOWLEDGMENTS.md; never take upstream identities/names.
