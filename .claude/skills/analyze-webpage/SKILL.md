---
name: analyze-webpage
description: "Produce per-article relevance determination and summary from extracted webpage content. Called by webpage-digest and webpage-adhoc agents."
version: "1.0"
forked: true
---

# Skill: Analyze Webpage

Read an extracted article and produce a relevance determination and summary.

## Inputs

- `ITEM_DIR`: path to the article directory containing `01-input-article.md` and `metadata.yaml`
- `MODE`: `batch` or `single`
  - **batch**: produce a concise one-paragraph summary (3-6 sentences)
  - **single**: produce a deeper multi-paragraph analysis (2-6 paragraphs)
- `PROMPT` (optional): custom analysis prompt from session config (e.g., "Focus on AI development, industry trends...")

## Execution

1. Read `{ITEM_DIR}/01-input-article.md` (the extracted article text)
2. Read `{ITEM_DIR}/metadata.yaml` for context (title, source, paywall status)
3. Determine relevance based on:
   - The `PROMPT` (if provided) — does the article match the focus criteria?
   - Default: VC/AI relevance — would a VC or AI practitioner benefit from knowing this?
   - If not relevant: set `relevance: skipped` with a one-line reason
4. Produce a summary:
   - **batch mode**: one paragraph, 3-6 sentences. Cover the main point, key data/claims, and why it matters.
   - **single mode**: multiple paragraphs, 2-6 depending on article length. Cover main arguments, key data points, notable claims, and implications. Short articles (< 1000 words) get 2-3 paragraphs; deep dives get 4-6.
   - Scale summary length with article significance and depth, not just word count
5. If `paywall: true` in metadata:
   - Summarize whatever content is available
   - Set `paywall_note` describing the limitation (e.g., "Summary based on first 3 paragraphs; rest behind paywall.")

## Output

Write `{ITEM_DIR}/analysis.yaml`:

```yaml
title: "Article Title"
url: "https://..."
source_name: "Blog Name"
published: "2026-03-25"
relevance: relevant          # or "skipped"
skip_reason: null             # or "Not relevant to VC/AI"
summary: |
  The summary text here. For batch mode, this is one paragraph.
  For single mode, this is multiple paragraphs separated by blank lines.
paywall: false
paywall_note: null
extraction_method: webfetch
word_count: 2400
```

Multiple items can run in parallel when called from a batch context.
