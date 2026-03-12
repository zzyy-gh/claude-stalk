---
name: process
description: "Processing pipeline for ai-podcast session. Stalks for new content, ingests, transcribes, then produces a VC/AI-focused briefing."
version: "1.0"
---

# Process — ai-podcast

Processing pipeline tailored for a venture capitalist tracking AI and VC news across podcast channels.

## Inputs

- `SESSION_DIR`: Path to the session folder (`sessions/ai-podcast/`)

## Steps

### 1. Stalk

Read `.claude/skills/stalk/SKILL.md` and execute it for this session (`SESSION_DIR`).

- If no new items are found → report "No new content for ai-podcast" and **stop here**.
- Otherwise, continue with the new items list.

### 2. Create update directory

Create `{SESSION_DIR}/updates/{YYYY-MM-DD-HHMM}/` for this batch.

### 3. For each new item

**a. Create item folder**:

- Slugify the title → `{UPDATE_DIR}/{item-slug}/`

**b. Ingest**:

- Read `.claude/skills/ingest/SKILL.md` and execute it
- URL: the item's `url`
- Target directory: `{UPDATE_DIR}/{item-slug}/`

**c. Transcribe**:

- Read `.claude/skills/transcribe/SKILL.md` and execute it on `{UPDATE_DIR}/{item-slug}/`

### 4. Summarize — VC/AI Briefing

After all items are processed:

- Read all `02-generated-transcript.md` files from this update's item folders
- For each item, determine **relevance** to VC and AI:
  - **Relevant**: Covers AI technology, startups, venture capital, fundraising, markets, company building, tech industry trends, founder interviews, investment theses, or adjacent topics (fintech, enterprise software, regulation, etc.) — even mildly relevant counts
  - **Skipped**: Completely unrelated (e.g., pure lifestyle, sports, cooking with no business angle)
- Produce a briefing using the template in `assets/summary-template.md`:
  - For each **relevant** item:
    - Title as a markdown link: `### [Item Title](url)`
    - Guest speaker(s) with a brief identifier (role/company). Use "-" for solo essays/monologues or unidentified speakers
    - 2-3 sentence executive summary highlighting what matters for a VC
    - 3-6 bullet points for key moments/insights, each with a `[MM:SS]` timestamp referencing the nearest `[HH:MM:SS]` marker from the transcript
    - For YouTube items: convert each `[HH:MM:SS]` timestamp to total seconds and make the `[MM:SS]` a clickable link: `[MM:SS]({video_url}&t={seconds})`
    - For non-YouTube items (articles): use a plain title link and plain `[MM:SS]` timestamps without deep links
  - For **skipped** items: list them with a one-line reason why they were skipped
  - Cross-cutting themes across the relevant items
  - Actionable takeaways from a VC perspective
- When citing specific claims or insights in key moments, reference the nearest `[HH:MM:SS]` marker from the transcript
  - For items that **could not be transcribed** (missing captions, download failures): list them with the reason
  - For **channels with no new content**: list them with links to their YouTube channel pages (`https://www.youtube.com/@{handle}`)
  - **Link all source/channel names** to their YouTube channel page: `[{source_name}](https://www.youtube.com/@{handle})`
  - **Link all item titles** to their video URL — including in Skipped and Not transcribed tables
- Save as `{UPDATE_DIR}/summary.md`

### 5. Generate HTML and export

**a. Generate HTML**:

- Read `{UPDATE_DIR}/summary.md`
- Read `assets/summary-html-template.html` — this is the styled wrapper with a `{content}` placeholder
- Convert the markdown content to semantic HTML with inline styles, following the mapping in `assets/summary-html-styles.md`
- Insert the converted HTML into the template's `{content}` placeholder
- Save as `{UPDATE_DIR}/summary.html`

**b. Export**:

- Read `output_dir` from `config.yaml`
- If `output_dir` is set (not null):
  - Copy `{UPDATE_DIR}/summary.html` to `{output_dir}/Youtube {YYYY-MM-DD-HHMM}.html`
  - Ensure the output directory exists (create if needed)
  - Report the exported file path
