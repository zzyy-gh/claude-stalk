---
name: adhoc
description: "Ad-hoc processing of a single URL. Detects URL type (YouTube, X, article) and routes to the appropriate pipeline. Trigger: 'summarize', 'summarize this', 'summarize this video'."
version: "1.0"
---

# Agent: Adhoc

Run the full pipeline on a single URL, producing output in `custom/{slug}/`.

## Inputs

- A URL (required) — YouTube, X post, or web article

## Steps

### 0. Setup

Run `bash scripts/get-timestamp.sh` to get the actual current time. It outputs two lines:
- Line 1 = `{TIMESTAMP}` (e.g., `2026-03-20 00:21 CST`) -- for metadata, summary heading
- Line 2 = `{TIMESTAMP_PATH}` (e.g., `2026-03-20-0021-CST`) -- for export filenames

Do not guess or infer the time from other sources -- always check the real clock.

### 1. Detect URL type and route

- **YouTube URL** (contains `youtube.com` or `youtu.be`) → Audio pipeline
- **X/Twitter URL** (contains `x.com` or `twitter.com`) → X pipeline (limited — analyze single post)
- **Other URL** → Audio pipeline (web article path via ingest-audio)

---

## Audio Pipeline (YouTube / Web article)

### 2. Ingest + Transcribe

1. **Ingest**: Execute the ingest-audio skill
   - URL: the provided URL
   - Target directory: `custom/temp-ingest/`
2. **Read metadata**: Read `custom/temp-ingest/metadata.yaml` to get the title
3. **Slugify**: `slug=$(bash scripts/slugify.sh "$title")`
4. **Guard**: If `custom/{slug}/` already exists:
   - Read its `metadata.yaml` and compare `source_url` to the current URL
   - **Same URL**: stop and report it was already processed
   - **Different URL**: append `-2` (or next available number) to the slug
5. **Rename**: `custom/temp-ingest/` to `custom/{slug}/`
6. **Transcribe**: Execute the transcribe-audio skill on `custom/{slug}/`

### 3. Write metadata additions

Update `custom/{slug}/metadata.yaml` to add:
```yaml
custom: true
```

### 4. Analyze

Execute the analyze-audio skill:
- `TRANSCRIPT`: `custom/{slug}/02-generated-transcript.md`
- `OUTPUT`: `custom/{slug}/candidates.yaml`

### 5. Write summary

Execute the write-summary-audio skill:
- `ITEM_DIRS`: `custom/{slug}/`
- `OUTPUT`: `custom/{slug}/summary.md`
- `MODE`: `single`
- `TIMESTAMP`: `{TIMESTAMP}` from Setup

### 6. Due diligence

Execute the due-diligence skill:
- `SUMMARY`: `custom/{slug}/summary.md`

### 7. Generate HTML

Execute the generate-html skill:
- `SUMMARY`: `custom/{slug}/summary.md`
- `CATEGORY`: `audio`
- `OUTPUT`: `custom/{slug}/summary.html`

## Output checklist

- [ ] `custom/{slug}/` directory created
- [ ] Ingest files present (`01-input-*`)
- [ ] `02-generated-transcript.md` generated
- [ ] `candidates.yaml` written
- [ ] `metadata.yaml` has `custom: true`
- [ ] `summary.md` with due diligence flags
- [ ] `summary.html` generated
