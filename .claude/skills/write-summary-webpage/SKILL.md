---
name: write-summary-webpage
description: "Read analysis.yaml files and a template to produce a web digest summary. Supports batch (webpage-digest) and single (webpage-adhoc) modes."
version: "1.0"
forked: true
---

# Skill: Write Summary Webpage

Read per-article analysis files and produce a web digest markdown summary.

## Inputs

- `ITEM_DIRS`: list of item directory paths. Each directory contains `analysis.yaml` and `metadata.yaml`.
- `TEMPLATE`: path to summary template. Default: `.claude/skills/write-summary-webpage/assets/summary-webpage-template.md`
- `OUTPUT`: path to write `summary.md`
- `MODE`: `batch` (multi-item) or `single` (single deep article)
- `TIMESTAMP`: for the summary heading date
- `NO_NEW_SOURCES` (optional, batch mode): list of source names with no new content

## Execution

- For each directory in `ITEM_DIRS`:
  - Read `analysis.yaml` for the summary, relevance, paywall status
  - Read `metadata.yaml` for source info (source_name, source_url, speakers)
- Read the template (`TEMPLATE`)
- Write `OUTPUT`

### Formatting rules

- Title as a markdown link: `### [Article Title](url)`
- **Metadata line**: `**Source**: [Source Name](source_base_url) | **Published**: YYYY-MM-DD HH:MM | **People**: Name, Name`
  - All three fields are mandatory on every article card
  - `source_base_url` is the homepage of the source site (from config `url` field), not the article URL
  - `Published` datetime comes from `analysis.yaml` `published` field. Use `--` if unavailable.
  - `People` lists notable people mentioned or quoted in the article. Use `--` if none.
- **Do not add due-diligence flags** — the due-diligence skill handles flagging separately
- **What happened** block: 2-3 sentences synthesizing dominant themes across articles
- **What to watch** block: 2-3 sentences on emerging signals and forward-looking items
- **Paywall articles**: append `_(paywalled -- {paywall_note})_` after the summary paragraph

### Batch mode (`MODE: batch`)

- Heading: `# Web Digest -- {YYYY-MM-DD HH:MM TZ}`
- Overview with count: "N new articles found across M monitored sources."
- Short What happened / What to watch
- **Articles section**: one H3 per relevant article with Source line and one-paragraph summary
- **Skipped section**: table with Title, Source, Reason columns
- **No new content section**: list of source names with links: `- [Source Name](url)`

### Single mode (`MODE: single`)

- Heading: `# Web Digest -- {Article Title}`
- Overview: short TLDR
  - What happened: 2-3 sentences
  - What to watch: 2-3 sentences on implications
- **Article section**: H3 with Source line, then the deeper multi-paragraph summary from analysis.yaml (no further condensation — use the summary as written by analyze-webpage)

## Output checklist

- [ ] `summary.md` written to `OUTPUT`
- [ ] All article titles are clickable markdown links to the article URL
- [ ] All source names are clickable markdown links to the source homepage
- [ ] Paywall notes included for paywalled articles
- [ ] No due-diligence flags added (that's a separate pipeline step)
