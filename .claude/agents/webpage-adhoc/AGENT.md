---
name: webpage-adhoc
description: "Ad-hoc processing of one or more webpage URLs. Single URL gets deep analysis; multiple URLs get batch-style output. Trigger: 'summarize this article', 'summarize this page', 'summarize these articles'."
version: "1.0"
---

# Agent: Webpage Adhoc

Run the webpage pipeline on one or more URLs, producing output in `output/webpage-adhoc/`.

## Inputs

- One or more webpage URLs (required)

## Steps

### 0. Setup

Run `bash scripts/get-timestamp.sh` to get the actual current time. It outputs two lines:
- Line 1 = `{TIMESTAMP}` (e.g., `2026-03-25 14:30 CST`) -- for metadata, summary heading
- Line 2 = `{TIMESTAMP_PATH}` (e.g., `2026-03-25-1430-CST`) -- for directory names, export filenames

Do not guess or infer the time from other sources -- always check the real clock.

### 1. Determine mode

- **Single URL**: `MODE = single`, output dir = `output/webpage-adhoc/{slug}/`
- **Multiple URLs**: `MODE = batch`, output dir = `output/webpage-adhoc/{TIMESTAMP_PATH}/`

---

## Single URL flow

### 2s. Ingest

1. **Ingest**: Execute the ingest-webpage skill
   - URL: the provided URL
   - Target directory: `output/webpage-adhoc/temp-ingest/`
   - TIMESTAMP: `{TIMESTAMP}`
   - METHOD: `webfetch` (default -- no config to look up)
2. **Read metadata**: Read `output/webpage-adhoc/temp-ingest/metadata.yaml` to get the title
3. **Slugify**: `slug=$(bash scripts/slugify.sh "$title")`
4. **Guard**: If `output/webpage-adhoc/{slug}/` already exists:
   - Read its `metadata.yaml` and compare `source_url` to the current URL
   - **Same URL**: stop and report it was already processed
   - **Different URL**: append `-2` (or next available number) to the slug
5. **Rename**: `output/webpage-adhoc/temp-ingest/` to `output/webpage-adhoc/{slug}/`

### 3s. Analyze

Execute the analyze-webpage skill:
- `ITEM_DIR`: `output/webpage-adhoc/{slug}/`
- `MODE`: `single`

### 4s. Write summary

Execute the write-summary-webpage skill:
- `ITEM_DIRS`: `output/webpage-adhoc/{slug}/`
- `OUTPUT`: `output/webpage-adhoc/{slug}/summary.md`
- `MODE`: `single`
- `TIMESTAMP`: `{TIMESTAMP}`

### 5s-7s. Due diligence, Generate HTML, Verify HTML

Same as batch flow steps 5-7 below, using `output/webpage-adhoc/{slug}/` paths.

---

## Multiple URL flow

### 2m. Create update directory

Create `output/webpage-adhoc/{TIMESTAMP_PATH}/`

### 3m. For each URL -- ingest (parallel)

All URLs can run in parallel. For each URL:

1. **Ingest to temp**: Execute the ingest-webpage skill
   - URL: the URL
   - Target directory: `output/webpage-adhoc/{TIMESTAMP_PATH}/temp-{i}/`
   - TIMESTAMP: `{TIMESTAMP}`
2. **Read metadata**: Get the title from metadata.yaml
3. **Slugify and rename**: `slug=$(bash scripts/slugify.sh "$title")`, rename temp dir to `{TIMESTAMP_PATH}/{slug}/`

### 4m. For each item -- analyze (parallel)

Execute the analyze-webpage skill for each item:
- `ITEM_DIR`: `output/webpage-adhoc/{TIMESTAMP_PATH}/{slug}/`
- `MODE`: `batch`

### 5. Write summary

Execute the write-summary-webpage skill:
- `ITEM_DIRS`: all `{TIMESTAMP_PATH}/{slug}/` directories
- `OUTPUT`: `output/webpage-adhoc/{TIMESTAMP_PATH}/summary.md`
- `MODE`: `batch`
- `TIMESTAMP`: `{TIMESTAMP}`

### 6. Due diligence

Execute the due-diligence skill:
- `SUMMARY`: path to `summary.md`

### 7. Generate HTML

Execute the generate-html skill:
- `SUMMARY`: path to `summary.md`
- `CATEGORY`: `webpage`
- `OUTPUT`: path to `summary.html`

### 8. Verify HTML

Execute the verify-html skill. If any critical check fails, regenerate with `python scripts/md-to-html.py`.

## Output checklist

- [ ] Output directory created
- [ ] Each article has `01-input-article.md` and `metadata.yaml`
- [ ] Each article has `analysis.yaml`
- [ ] `summary.md` with due diligence flags
- [ ] `summary.html` generated and verified
