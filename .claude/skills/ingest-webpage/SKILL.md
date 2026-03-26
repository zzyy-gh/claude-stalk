---
name: ingest-webpage
description: "Fetch webpage content via WebFetch or playwright script. Trigger: 'ingest webpage', 'fetch article'. Saves extracted text and metadata."
version: "1.0"
forked: true
---

# Skill: Ingest Webpage

Fetch a webpage and extract its text content into a target directory.

## Inputs

- `URL`: the article URL to fetch
- `TARGET_DIR`: path to save output files
- `TIMESTAMP`: provided by the calling agent (e.g., `2026-03-25 14:30 CST`). Use for `date_processed`. Do not run `date` independently.
- `SOURCE_NAME` (optional): human-readable source name from config. If not provided, extract from page metadata or domain.
- `METHOD` (optional): `webfetch` (default) or `playwright`. Passed by the agent from config.
- `NOTES` (optional): per-source notes from config, for context on edge cases.

## Steps

1. **Create target directory** if it doesn't exist.

2. **Fetch the page**:

### Default: WebFetch
- Use the WebFetch tool to fetch the URL
- WebFetch returns markdown content directly
- Save as `01-input-article.md`
- If WebFetch returns less than 200 characters of content, fall back to playwright

### Playwright fallback
- Run when `METHOD=playwright` or WebFetch returned minimal content:
  ```bash
  node scripts/fetch-webpage.js \
    --url "{URL}" \
    --html-output "{TARGET_DIR}/01-input-webpage.html" \
    --text-output "{TARGET_DIR}/01-input-article.md"
  ```
- Script outputs JSON metadata to stdout: `{title, byline, siteName, excerpt, wordCount, url}`
- Use the metadata when writing `metadata.yaml`

### PDF detection
- If URL ends in `.pdf` or content-type is `application/pdf`:
  - Download the PDF to `{TARGET_DIR}/01-input-article.pdf`
  - Use the Read tool to extract text
  - Save extracted text as `01-input-article.md`

3. **Detect paywall signals**:
   - Content is truncated (significantly shorter than expected for an article)
   - Contains phrases: "subscribe to continue", "sign in to read", "members only", "paywall", "premium content"
   - Login wall detected (form elements, redirect to login)
   - If detected: set `paywall: true` in metadata. Still save whatever content is available.

4. **Extract source name** (if not provided):
   - From `<meta property="og:site_name">` or `<meta name="application-name">`
   - From the page `<title>` (before the separator like " | " or " - ")
   - Fallback: domain name (e.g., "blog.anthropic.com")

5. **Identify speakers** (optional):
   - If the article is an interview or Q&A, identify interviewees with roles
   - Otherwise leave speakers empty

6. **Write `metadata.yaml`** in the target directory:

```yaml
title: "Article Title"
source_url: "https://..."
source_name: "Blog Name"
source_type: webpage
date_published: "2026-03-25"
date_processed: "2026-03-25 14:30 CST"
extraction_method: webfetch    # or "playwright"
speakers: []
paywall: false
word_count: 2400
language: "en"
```

### Field sources
- `title` -- from WebFetch page title, playwright metadata, or `<title>` tag
- `source_url` -- the input URL (or final URL after redirects for playwright)
- `source_name` -- from `SOURCE_NAME` input, or extracted per step 4
- `date_published` -- from RSS metadata passed by agent, or `<meta>` tags, or JSON-LD
- `date_processed` -- the `TIMESTAMP` input
- `extraction_method` -- which method was used (webfetch or playwright)
- `word_count` -- count words in `01-input-article.md`
- `paywall` -- true if paywall detected

## Output checklist

- [ ] Target directory exists
- [ ] `01-input-article.md` contains extracted text
- [ ] `01-input-webpage.html` saved (playwright only)
- [ ] `metadata.yaml` written with all available fields
- [ ] Paywall flagged if detected
