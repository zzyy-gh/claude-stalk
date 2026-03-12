---
name: process
description: "Processing pipeline for this session. Stalks for new content, then ingests, transcribes, and summarizes."
version: "2.0"
---

# Process

Default processing pipeline for a session. Called by `/update` or run directly.

## Inputs

- `SESSION_DIR`: Path to the session folder (`sessions/{name}/`)

## Steps

### 1. Stalk

Read `.claude/skills/stalk/SKILL.md` and execute it for this session (`SESSION_DIR`).
- If no new items are found → report "No new content for {session}" and **stop here**.
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

### 4. Summarize

After all items are processed:
- Read all `02-generated-transcript.md` files from this update's item folders
- Produce a combined summary using the template in `assets/summary-template.md`:
  - Overview of what was found
  - Key points per item
  - Cross-cutting themes
  - Actionable takeaways
- Save as `{UPDATE_DIR}/summary.md`

## Customization

Edit this file to change how your session processes content. Examples:
- Filter items by keyword before processing
- Skip transcription for RSS articles
- Summarize from a specific angle (technical, business, etc.)
- Add post-processing steps (trend analysis, notifications, etc.)
