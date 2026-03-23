---
name: podcast
description: "Full podcast/YouTube pipeline: checks feeds, ingests, transcribes, and produces summaries. Trigger: 'run update', 'check all', 'scheduled check', 'run podcast'."
version: "1.0"
---

# Agent: Podcast

Full pipeline orchestrator for podcast/YouTube content. Checks feeds, ingests new content, transcribes, and produces summaries.

## Inputs

- `SESSION`: session name or `all` (default: all enabled sessions under `podcast/`)

### Setup

Run `bash scripts/get-timestamp.sh` to get the actual current time. It outputs two lines:
- Line 1 = `{TIMESTAMP}` (e.g., `2026-03-20 00:21 CST`) -- for metadata, summary heading
- Line 2 = `{TIMESTAMP_PATH}` (e.g., `2026-03-20-0021-CST`) -- for directory names, export filenames

Do not guess or infer the time from other sources -- always check the real clock.

## Multi-session orchestration

When `SESSION` is `all` (or omitted):
- List all `podcast/*/config.yaml`
- Filter to `enabled: true`
- Run the pipeline below for each enabled session
- Print final summary across sessions

When `SESSION` is a specific name:
- Run the pipeline for `podcast/{SESSION}/` only

## Notification

Always send Telegram notifications at these points:

- On start: `bash scripts/notify-telegram.sh "[claude-stalk] Podcast check started."`
- On input needed: `bash scripts/notify-telegram.sh "[claude-stalk] Need your input -- check Remote Control"`

## Pipeline (per session)

`SESSION_DIR` = `podcast/{name}/`

### 0. Check for pending retries

- Read `{SESSION_DIR}/retry.yaml` (skip this step if the file doesn't exist or is empty)
- Filter entries where `enabled: true`
- For each enabled entry:
  - Resolve `path` relative to `SESSION_DIR` (e.g., `updates/2026-03-17-1309/travis-kalanick-michael-dell-austin`)
  - Read `.claude/skills/transcribe-audio/SKILL.md` and execute it on that directory
  - **On success**:
    - Remove the entry from `retry.yaml`
    - Update the item's `metadata.yaml`: set `stages.transcribe.completed: true`, `stages.transcribe.timestamp` to now, and update `transcript_source` if the method changed
    - Add the item to a `retried_items` list for inclusion in the summary
  - **On failure**:
    - Ask the user (via Telegram notification + direct question) whether to keep retrying or stop
    - If keep retrying (default): leave `enabled: true`
    - If stop: set `enabled: false`
    - Update `reason` with the new failure details either way
- Write back `retry.yaml` after processing all entries

### 1. Stalk

Read `.claude/skills/stalk-audio/SKILL.md` and execute it for this session (`SESSION_DIR`).

- If no new items are found **and** no retried items from Step 0 -- report "No new content for {name}" and **stop here**.
- Otherwise, continue with the new items list.

### 2. Create update directory

Create `{SESSION_DIR}/updates/{TIMESTAMP_PATH}/` using the path-safe timestamp from Setup.

### 3. For each new item -- ingest + transcribe (one per item, parallel)

All items can run in parallel. For each item:

1. **Create item folder**: `slug=$(bash scripts/slugify.sh "$title")` -> `{UPDATE_DIR}/{slug}/`
2. **Ingest**: Execute the ingest-audio skill
   - URL: the item's `url`
   - Target directory: `{UPDATE_DIR}/{slug}/`
3. **Transcribe**: Execute the transcribe-audio skill on `{UPDATE_DIR}/{slug}/`

### 4. Analyze (one per item, parallel)

All items can run in parallel. For each item, execute the analyze-audio skill:

- `TRANSCRIPT`: `{UPDATE_DIR}/{slug}/02-generated-transcript.md`
- `OUTPUT`: `{UPDATE_DIR}/{slug}/candidates.yaml`

### 5. Write summary

Execute the write-summary-audio skill:

- `ITEM_DIRS`: all `{UPDATE_DIR}/{slug}/` directories + any retried item directories
- `OUTPUT`: `{UPDATE_DIR}/summary.md`
- `MODE`: `batch`
- `TIMESTAMP`: `{TIMESTAMP}` from Setup (for the summary heading)

### 6. Due diligence

Execute the due-diligence skill:

- `SUMMARY`: `{UPDATE_DIR}/summary.md`

### 7. Generate HTML and export

Execute the generate-html skill:

- `SUMMARY`: `{UPDATE_DIR}/summary.md`
- `CATEGORY`: `audio`
- `OUTPUT`: `{UPDATE_DIR}/summary.html`
- `EXPORT_DIR`: from `config.yaml` `output_dir` (if set)
- `EXPORT_NAME`: `Youtube Updates {TIMESTAMP_PATH}.html`

## Loop integration

For automated polling: `/loop {frequency} run update`. The agent handles the "run update" trigger.
