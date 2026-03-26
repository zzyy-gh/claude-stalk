---
name: write-summary-audio
description: "Read candidates.yaml files and a template to produce a YouTube Digest summary for podcast/YouTube content. Supports batch (multi-item update) and single (youtube-adhoc) modes."
version: "1.0"
forked: true
---

# Skill: Write Summary Audio

Read candidate key moments and a template to produce a YouTube Digest summary.

## Inputs

- `ITEM_DIRS`: list of item directory paths. Each directory contains `candidates.yaml` and `01-input-yt-metadata.json`.
- `TEMPLATE`: (optional) path to summary template. Default: `.claude/skills/write-summary-audio/assets/summary-audio-template.md`
- `OUTPUT`: path to write `summary.md`
- `MODE`: `batch` (multi-item update) or `single` (youtube-adhoc single-item)
- `TIMESTAMP`: (batch mode only) for the summary heading date

## Execution

- For each directory in `ITEM_DIRS`:
  - Read `candidates.yaml` for key moments, speakers, and relevance
  - Read `01-input-yt-metadata.json` for channel info (`channel`, `channel_url` fields). Use this for the **Source** line and channel links.
- Read the template (`TEMPLATE`)
- Includes **all candidates** per item as key moments
- Writes `OUTPUT`

### Relevance determination

For each item, determine **relevance** to VC and AI:
- **Relevant**: Covers AI technology, startups, venture capital, fundraising, markets, company building, tech industry trends, founder interviews, investment theses, or adjacent topics (fintech, enterprise software, regulation, etc.) — even mildly relevant counts
- **Skipped**: Completely unrelated (e.g., pure lifestyle, sports, cooking with no business angle)

### Formatting rules

- For each **relevant** item:
  - Title as a markdown link: `### [Item Title](url)`
  - Speaker(s) with role. Use "-" for unidentified speakers
  - 2-3 sentence executive summary highlighting what matters for a VC (batch mode only — in single mode, the "What happened" block in the overview serves this purpose)
  - A bullet point for each candidate moment/insight, each with a `[MM:SS]` timestamp referencing the nearest `[HH:MM:SS]` marker from the transcript
  - For YouTube items: convert each `[HH:MM:SS]` timestamp to total seconds and make the `[MM:SS]` a clickable link: `[MM:SS]({video_url}&t={seconds})`
  - For non-YouTube items (articles): use a plain title link and plain `[MM:SS]` timestamps without deep links
- When citing specific claims or insights in key moments, reference the nearest `[HH:MM:SS]` marker from the transcript
- **Do not add due-diligence flags** (italic parentheticals like `_(unverified)_`). Present claims as-is -- the due-diligence skill handles flagging in a separate pipeline step
- **Link all source/channel names** to their YouTube channel page: `[{source_name}](https://www.youtube.com/@{handle})`
- **Link all item titles** to their video URL — including in Skipped and Not transcribed tables
- **What happened** block (after Overview): 2-3 sentences synthesizing dominant stories and common threads across relevant items — market shifts, emerging consensus, contrarian takes (may split into paragraphs when topics are distinct)
- **What to watch** block: 2-3 sentences on emerging risks, developing situations and forward-looking signals (may split into paragraphs when topics are distinct)

### Batch mode (`MODE: batch`)

- Heading: `# YouTube Digest -- {YYYY-MM-DD HH:MM TZ}`
- For **skipped** items: list them with a one-line reason why they were skipped
- For items that **could not be transcribed** (missing captions, download failures): list them with the reason
- For **channels with no new content**: list them with links to their YouTube channel pages (`https://www.youtube.com/@{handle}`)
- Include per-item executive summary paragraph

### Single mode (`MODE: single`)

- Heading: `# YouTube Digest -- {title}` (use the video title, not the slug)
- No executive summary paragraph for the item — the "What happened" block in the overview serves this purpose
- No "Skipped", "Not transcribed", "No new content" sections — this is a single-item summary
