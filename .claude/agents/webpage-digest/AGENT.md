---
name: webpage-digest
description: "Full webpage monitoring pipeline: checks RSS feeds, ingests articles, analyzes, and produces summaries. Trigger: 'run webpage update', 'check blogs', 'run webpage-digest'."
version: "1.0"
---

# Agent: Webpage Stalker

Full pipeline orchestrator for webpage/blog content. Checks RSS feeds for new articles, ingests content, analyzes, and produces summaries.

## Inputs

- `SESSION`: session name or `all` (default: all enabled sessions under `output/webpage-digest/`)

### Setup

Run `bash scripts/get-timestamp.sh` to get the actual current time. It outputs two lines:
- Line 1 = `{TIMESTAMP}` (e.g., `2026-03-25 14:30 CST`) -- for metadata, summary heading
- Line 2 = `{TIMESTAMP_PATH}` (e.g., `2026-03-25-1430-CST`) -- for directory names, export filenames

Do not guess or infer the time from other sources -- always check the real clock.

## Multi-session orchestration

When `SESSION` is `all` (or omitted):
- List all `output/webpage-digest/*/config.yaml`
- Filter to `enabled: true`
- Run the pipeline below for each enabled session
- Print final summary across sessions

When `SESSION` is a specific name:
- Run the pipeline for `output/webpage-digest/{SESSION}/` only

## Pipeline (per session)

`SESSION_DIR` = `output/webpage-digest/{name}/`

### 0. Check for pending retries

- Read `{SESSION_DIR}/retry.yaml` (skip if doesn't exist or empty)
- Filter entries where `enabled: true`
- For each enabled entry:
  - Resolve `path` relative to `SESSION_DIR`
  - **Inspect what exists** in the item directory:
    - No `01-input-article.md` → re-run ingest-webpage
    - Has `01-input-article.md` but no `analysis.yaml` → re-run analyze-webpage
    - Has `analysis.yaml` → already done, remove from retry
  - On success: remove entry, add to `retried_items` list
  - On failure: ask user whether to keep retrying or stop

### 1. Stalk

Read `.claude/skills/stalk-webpage/SKILL.md` and execute it for this session (`SESSION_DIR`).

- If no new items and no retried items -- report "No new content for {name}" and **stop here**.
- Otherwise, continue with the new items list.

### 2. Create update directory

Create `{SESSION_DIR}/updates/{TIMESTAMP_PATH}/`

### 3. For each new item -- ingest (parallel)

All items can run in parallel. For each item:

1. **Create item folder**: `slug=$(bash scripts/slugify.sh "$title")` -> `{UPDATE_DIR}/{slug}/`
2. **Look up source config**: Match the item's `source_name` to the config source entry to get `method` and `notes`
3. **Ingest**: Execute the ingest-webpage skill
   - URL: the item's `url`
   - TARGET_DIR: `{UPDATE_DIR}/{slug}/`
   - TIMESTAMP: `{TIMESTAMP}`
   - METHOD: from config (default: `webfetch`)
   - NOTES: from config (if any)
   - SOURCE_NAME: from the item's `source_name`
4. **On failure**: add to `{SESSION_DIR}/retry.yaml` and continue with remaining items

### 4. Analyze (per item, parallel)

All items can run in parallel. For each item, execute the analyze-webpage skill:

- `ITEM_DIR`: `{UPDATE_DIR}/{slug}/`
- `MODE`: `batch`
- `PROMPT`: from `config.yaml` `prompt` field (if set)

### 5. Write summary

Execute the write-summary-webpage skill:

- `ITEM_DIRS`: all `{UPDATE_DIR}/{slug}/` directories + any retried item directories
- `OUTPUT`: `{UPDATE_DIR}/summary.md`
- `MODE`: `batch`
- `TIMESTAMP`: `{TIMESTAMP}`
- `NO_NEW_SOURCES`: list source names from config that had zero new items

### 6. Due diligence

Execute the due-diligence skill:
- `SUMMARY`: `{UPDATE_DIR}/summary.md`

### 7. Generate HTML

Execute the generate-html skill:
- `SUMMARY`: `{UPDATE_DIR}/summary.md`
- `CATEGORY`: `webpage`
- `OUTPUT`: `{UPDATE_DIR}/summary.html`

### 8. Verify HTML

Execute the verify-html skill on `{UPDATE_DIR}/summary.md` and `{UPDATE_DIR}/summary.html`. If any critical check fails, regenerate with `python scripts/md-to-html.py`.

### 9. Export (if configured)

If `config.yaml` has `export_dir`:
- Ensure the directory exists: `mkdir -p "{export_dir}"`
- Copy: `cp "{UPDATE_DIR}/summary.html" "{export_dir}/{name} {TIMESTAMP_PATH}.html"`
- Report the exported file path
