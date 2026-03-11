---
name: custom-processor
description: "Custom processing pipeline for this session. Orchestrates what happens with new items found by the stalk skill."
version: "1.0"
---

# Custom Processing Skill

Pipeline orchestrator for this session. Called by the update skill with a list of new items.

## Context provided by update skill

- `NEW_ITEMS`: List of new items from stalk, each with: title, url, source_type, source_name, published
- `UPDATE_DIR`: Path to this update's folder (e.g., `sessions/{name}/updates/2026-03-11-1400/`)
- `SESSION_DIR`: Path to session root
- `OUTPUT_DIR`: From config (null if not set)

## Pipeline

For each item in `NEW_ITEMS`:

1. **Create item folder**: Slugify the title → `{UPDATE_DIR}/{item-slug}/`

2. **Ingest**: Read `skills/ingest/SKILL.md` and execute it with:
   - URL: the item's `url`
   - Target directory: `{UPDATE_DIR}/{item-slug}/`

3. **Transcribe**: Read `skills/transcribe/SKILL.md` and execute it on `{UPDATE_DIR}/{item-slug}/`

After all items are processed:

4. **Summarize**: Read all `02-generated-transcript.md` files from this update's item folders. Produce a combined summary covering all items:
   - Key themes across all items
   - Notable points per item
   - Source links

5. **Write summary**: Save as `{UPDATE_DIR}/summary.md`

6. **Export** (if `OUTPUT_DIR` is set): Copy `summary.md` to `{OUTPUT_DIR}/YYYY-MM-DD-summary.md`

## Customization

Edit this skill to change the pipeline. Examples:
- Skip transcription for web articles (just save the article text)
- Add perspective-based summarization (technical, business, etc.)
- Extract specific data (quotes, references, claims)
- Compare against previous updates
- Send notifications

See `assets/summary-template.md` for the summary format template.
See `examples/example-output.md` for an example of the expected output.
