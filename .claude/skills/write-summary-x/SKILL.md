---
name: write-summary-x
description: >
  Generates the final markdown digest from analyzed X feed data.
  Handles formatting, URL verification, and quality checks.
  Trigger phrases: "write digest", "generate digest", "build x summary".
version: "1.0"
forked: true
compatibility: "None — file I/O only."
---

# Skill: Write Summary X

Produces a markdown digest file from enriched X analysis data. HTML generation is handled separately by the shared generate-html skill.

---

## Input Contract

Reads from files produced by upstream skills:

- **`{UPDATE_DIR}/scrape.json`** — raw post data (keyed by handle) from stalk-x
- **`{UPDATE_DIR}/analysis.json`** — analysis notes, link summaries, and skip ledger from analyze-x
- **Config values** — `name`, `prompt` from pipeline orchestrator
- **Scrape timing** — `startTime`, `endTime`, and `listMembers` from orchestrator (for metadata table)

**First step:** Compute stats for the metadata table, then read both JSON files:

```bash
python scripts/summarize-scrape.py --scrape "{UPDATE_DIR}/scrape.json" --stats
```

Do NOT rely on conversation context for post data or analysis notes.

---

## Custom Prompt Application

The custom prompt from the session config (or the default VC-oriented analyst prompt)
shapes the analysis tone. Apply it when writing the digest content.

---

## Section 1: Metadata Table

A markdown table at the top, immediately after the `#` title:

```markdown
# X Feed Digest — [date range]

| Field                | Value                                                                                                                                                                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Report generated     | Must reflect the actual current time when the report is generated — timezone comes from the orchestrator                                                                                                                                     |
| Period               | e.g. "Last 24 hours (Mar 3–4, 2026)"                                                                                                                                                                                                     |
| Source               | For list: `[List Name](https://x.com/i/lists/ID) (N members)` using `listMembers` from orchestrator. If `listMembers` is null, fall back to totalAccounts from stats with "(N accounts)" label. For following: `[@username](https://x.com/username) Following feed`. Source URL comes from config `source` field. |
| Posts captured       | N posts from N accounts                                                                                                                                                                                                                  |
| External links found | N links (N analyzed in depth)                                                                                                                                                                                                            |
| Images found         | N images across posts                                                                                                                                                                                                                    |
```

---

## Section 2: Digest Body

```markdown
## [Digest Name from config, or "VC Feed Digest"]

**What happened:** 2-3 sentences summarizing the dominant stories and themes of the period. Professional analyst tone — direct, specific, no filler.

**What to watch:** 2-3 sentences on emerging risks, developing situations, or things that could escalate or matter in coming days. Forward-looking and actionable.

### [Themed subsection title]

1-2 paragraphs of flowing prose synthesizing what was said, who said it, and why it matters. Weave in external-link and image insights naturally. Inline-hyperlink every key claim to its source post.

### [Another themed subsection]

...more subsections as needed...
```

**Writing voice**: Read like an analyst wrote it, not a feed dump. Think morning briefing
memo. Synthesize across accounts — if three people discuss the same fundraise, weave their
perspectives into one paragraph. Be direct, specific, opinionated. Reference actual handles.
No filler. Say what happened and what it means.

**Hyperlinks and attribution**:

Two cases to distinguish:

1. **Poster is the subject** (account posting its own content, opinion, or announcement):
   - Use `@handle` as visible text, linked to profile: `[@AnthropicAI](https://x.com/AnthropicAI)`
   - Link the claim verb to the post URL: `[@AnthropicAI](https://x.com/AnthropicAI) [published](https://x.com/AnthropicAI/status/REAL_ID) a blog post on...`
   - Always use `@` prefix to make it clear this is an X account

2. **Poster is reporting on a different subject** (news accounts, commentators covering third-party events):
   - Do NOT link the subject to the poster's profile -- just link the claim to the post URL
   - Correct: `Arm [announced](https://x.com/TechCrunch/status/REAL_ID) its first in-house chip...`
   - Wrong: `[Arm](https://x.com/TechCrunch) [announced](https://x.com/TechCrunch/status/REAL_ID)...`
   - If attribution to the poster matters, add it naturally: `...per [@FirstSquawk](https://x.com/FirstSquawk)` or `[@TechCrunch](https://x.com/TechCrunch) [reported](post_url) that Arm announced...`

General rules:
- Post URLs must come from scrape/analysis data -- never construct or guess URLs.
- Roughly one link per sentence in data-heavy paragraphs.
- Use `@handle` format consistently in both digest body and skipped content sections.
- **Do not add due-diligence flags** (italic parentheticals like `_(unverified)_`). Present claims as-is -- the due-diligence skill handles flagging in a separate pipeline step.

**Length**: 2-4 pages equivalent. Substantive enough to be useful, short enough to read
in 5 minutes.

---

## Section 3: Skipped Content

```markdown
## Skipped Content

**News wire / market data feeds:** Approximately N posts from [@handle](url)...

**Reposts and viral content:** ...

**Unvisited external links:** ...

**Low-signal posts:** ...
```

Aggregated overview, not post-by-post. Each category starts with a **bold label and colon**.
Include hyperlinked @handles. Half a page max.

---

## URL Verification (mandatory before writing)

**Pre-write:** Build a URL lookup map from the scrape file:
```bash
python scripts/verify-x-urls.py --scrape "{UPDATE_DIR}/scrape.json" --build-map
```
Output is a YAML map of `handle -> [{text_prefix, url}]`. Use this map when writing the digest — every post URL (`x.com/.../status/...`) MUST be looked up from this map by handle + text substring. **Never construct or guess status URLs.** If you can't find a matching URL, omit the link rather than fabricate one.

**Post-write:** Verify all URLs in the generated digest:
```bash
python scripts/verify-x-urls.py --scrape "{UPDATE_DIR}/scrape.json" --digest "{UPDATE_DIR}/digest.md"
```
Exit code 0 = all URLs verified. Exit code 1 = missing URLs found — check `missing_details` in the output and fix them.

---

## Build Pipeline

1. Save markdown to `{UPDATE_DIR}/digest.md`
2. Due diligence is handled by the shared due-diligence skill (called by the agent after this skill)

---

## Verification

Before presenting, quality-check the markdown:

1. **Structure**: All three sections present (metadata table, digest body with themed
   subsections, skipped content).
2. **Hyperlinks**: Spot-check 3-5 links — must have natural descriptive link text (not "[link]", raw URLs, or clustered at paragraph ends).
3. **Post URL accuracy**: Spot-check 3 post URLs against the scrape JSON to confirm they match exactly. No fabricated or guessed URLs.
4. **Tone and prose quality**: Re-read the opening paragraph and one subsection. Flag
   and rewrite any feed-dump patterns.
5. **Completeness**: Metadata table numbers match actual scraping results.

If any check fails, fix the issue and re-save.

---

## Output Contract

- **Markdown file**: `{UPDATE_DIR}/digest.md`
