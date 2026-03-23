---
name: write-summary-x
description: >
  Generates the final markdown digest from analyzed X feed data.
  Handles formatting, URL verification, and quality checks.
  Trigger phrases: "write digest", "generate digest", "build x summary".
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
- **Scrape timing** — `startTime` and `endTime` from orchestrator (for metadata table)

**First step:** Read both JSON files. Do NOT rely on conversation context for post data or analysis notes.

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
| Source               | For list: `[List Name](https://x.com/i/lists/ID) by @username (N members)` / For following: `[@username](https://x.com/username) Following feed`. Link must work in both markdown and HTML. Source URL comes from config `source` field. |
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

- Use display names (e.g., "Ming-Chi Kuo") as visible link text, linked to the profile URL (`https://x.com/{handle}`).
- Post-specific claims link to the actual post URL from the scrape/analysis data — never construct or guess URLs.
- Example: `[Ming-Chi Kuo](https://x.com/mingchikuo) [reports](https://x.com/mingchikuo/status/REAL_ID) that...`
- Roughly one link per sentence in data-heavy paragraphs.

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

Before generating digest content, build a URL lookup map from the scrape file:

1. Read `{UPDATE_DIR}/scrape.json`
2. Build a map: `handle → [{text_prefix (first 60 chars), url}]`
3. When writing the digest, every post URL (`x.com/.../status/...`) MUST be looked up from this map — match by handle + text substring
4. **Never construct or guess status URLs.** If you can't find a matching URL in the map, omit the link rather than fabricate one.

**Post-write verification step:**

1. Grep the generated markdown for all `x.com/.*/status/` URLs
2. Check each against the scrape JSON — every URL must exist in the file
3. If any don't match, fix them (look up the correct URL from the map) and re-save

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
