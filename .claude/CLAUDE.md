# Claude Stalk

Unified content monitoring and intelligence platform. Monitors YouTube channels, RSS feeds, X (Twitter) feeds, and webpages/blogs, producing VC/AI-focused digests as markdown + styled HTML.

## Content Categories

| Category | Directory | Sources | Agent |
|----------|-----------|---------|-------|
| **YouTube Digest** | `output/youtube-digest/` | YouTube channels, RSS feeds | `youtube-digest` |
| **X Digest** | `output/x-digest/` | X lists, X Following feed | `x-digest` |
| **YouTube Adhoc** | `output/youtube-adhoc/` | Single YouTube URLs | `youtube-adhoc` |
| **Webpage Digest** | `output/webpage-digest/` | Blogs, websites via RSS | `webpage-digest` |
| **Webpage Adhoc** | `output/webpage-adhoc/` | One or more webpage URLs | `webpage-adhoc` |

## Agents

Agents are multi-step orchestrators that chain skills together. They live in `.claude/agents/` with `AGENT.md` files.

| Agent | Purpose | Trigger |
|---|---|---|
| **youtube-digest** | Full YouTube/audio pipeline: stalk, ingest, transcribe, analyze, summarize | "run update", "check all", "scheduled check" |
| **x-digest** | X digest pipeline: scrape, analyze, summarize | "run digest", "digest my feed", "run x digest" |
| **youtube-adhoc** | Ad-hoc processing of a single YouTube URL | "summarize", "summarize this", "summarize this video" |
| **webpage-digest** | Full webpage pipeline: stalk RSS, ingest, analyze, summarize | "run webpage update", "check blogs", "run webpage-digest" |
| **webpage-adhoc** | Ad-hoc processing of one or more webpage URLs | "summarize this article", "summarize this page", "summarize these articles" |
| **tester** | Quality checks on workspace (docs, scripts, configs) | "test", "verify", "run checks" |

## Skills

### Audio pipeline (suffix: `-audio`)

| Skill | Purpose | Trigger | Input | Output |
|---|---|---|---|---|
| **stalk-audio** | Check YouTube/RSS feeds | `/stalk-audio`, "check feeds" | `config.yaml`, `stalk-history.yaml` | Updated history, new items list |
| **ingest-audio** | Download content | `/ingest-audio`, "download this" | URL, target dir, `{TIMESTAMP}` | `01-input-*`, `metadata.yaml` |
| **transcribe-audio** | Produce transcript | `/transcribe-audio`, "transcribe this" | `ITEM_DIR`, `{TIMESTAMP}` | `02-generated-transcript.md` |
| **analyze-audio** | Extract key moments | Called by agent | `TRANSCRIPT`, `OUTPUT` | `candidates.yaml` |
| **write-summary-audio** | Produce summary | Called by agent | `ITEM_DIRS`, `TEMPLATE`, `OUTPUT`, `MODE` | `summary.md` |

### X pipeline (suffix: `-x`)

| Skill | Purpose | Trigger | Input | Output |
|---|---|---|---|---|
| **stalk-x** | Scrape X feeds | `/stalk-x`, "scrape feed" | `source`, `days`, `account`, `UPDATE_DIR` | `scrape.json` |
| **analyze-x** | Triage posts, investigate links | Called by agent | `UPDATE_DIR` | `analysis.json` |
| **write-summary-x** | Produce digest | Called by agent | `UPDATE_DIR`, config values | `digest.md` |

### Webpage pipeline (suffix: `-webpage`)

| Skill | Purpose | Trigger | Input | Output |
|---|---|---|---|---|
| **stalk-webpage** | Check RSS/Atom feeds | `/stalk-webpage`, "check blogs" | `config.yaml`, `stalk-history.yaml`, `feed-cache.yaml` | Updated history, new items list |
| **ingest-webpage** | Fetch article content | `/ingest-webpage`, "fetch article" | URL, target dir, `{TIMESTAMP}`, METHOD | `01-input-article.md`, `metadata.yaml` |
| **analyze-webpage** | Produce article summary | Called by agent | `ITEM_DIR`, `MODE` | `analysis.yaml` |
| **write-summary-webpage** | Produce summary | Called by agent | `ITEM_DIRS`, `TEMPLATE`, `OUTPUT`, `MODE` | `summary.md` |

### Shared (no suffix)

| Skill | Purpose | Trigger | Input | Output |
|---|---|---|---|---|
| **due-diligence** | Flag unverified claims | Called by agent | `SUMMARY` path | Modified in place |
| **generate-html** | Convert markdown to styled HTML | Called by agent | `SUMMARY`, `CATEGORY` | `.html` file |
| **verify-html** | Verify HTML against source markdown | Called by agent | Markdown + HTML paths | Pass/fail report |
| **session-init** | Create new session | `/session-init`, "new session" | Interactive wizard | Session directory with config |

## Directory Structure

```
output/youtube-digest/{name}/
├── config.yaml
├── stalk-history.yaml
├── retry.yaml
└── updates/
    └── YYYY-MM-DD-HHMM-TZ/
        ├── {item-slug}/
        │   ├── 01-input-*, metadata.yaml
        │   ├── 02-generated-transcript.md
        │   └── candidates.yaml
        ├── summary.md
        └── summary.html

output/x-digest/{name}/
├── config.yaml
└── updates/
    └── YYYY-MM-DD/
        ├── scrape.json
        ├── analysis.json
        ├── digest.md
        └── digest.html

output/webpage-digest/{name}/
├── config.yaml
├── stalk-history.yaml
├── feed-cache.yaml
├── retry.yaml
└── updates/
    └── YYYY-MM-DD-HHMM-TZ/
        ├── {article-slug}/
        │   ├── 01-input-article.md, metadata.yaml
        │   └── analysis.yaml
        ├── summary.md
        └── summary.html

output/youtube-adhoc/{slug}/      # Ad-hoc runs
output/webpage-adhoc/{slug}/      # Ad-hoc runs (single URL)
output/webpage-adhoc/YYYY-MM-DD-HHMM-TZ/  # Ad-hoc runs (multiple URLs)
```

## Pipeline Structure

All pipelines follow the same pattern:

```
stalk → [ingest → transcribe →] analyze → write-summary → due-diligence → generate-html → verify-html → [export]
```

Audio has extra ingest + transcribe steps because it needs to download and convert media before analysis.
Webpage has ingest (fetch article) but no transcribe step — fetching *is* extracting the text.

## Scripts

All scripts live in `scripts/`:
- **Shared**: `get-timestamp.sh`, `slugify.sh`, `notify-telegram.sh`, `md-to-html.py`
- **Audio**: `stalk-youtube.sh`, `batch-check-metadata.sh`, `build-candidates.py`, `filter-stalk.py`, `parse-feed.py`, `ingest-youtube.sh`, `vtt-to-transcript.py`
- **Webpage**: `fetch-webpage.js`, `normalize_url.py` (also uses `build-candidates.py`, `filter-stalk.py`, `parse-feed.py`)
- **X**: `scrape-x.js`, `now.js`, `verify-x-urls.py`, `summarize-scrape.py`, `lib/` (auth, extract, navigate)
- **Tests**: `tests/`

## Environment

- **yt-dlp**: `pip install yt-dlp`
- **Groq MCP**: Configured in `.claude/settings.json` for Whisper transcription
- **GROQ_API_KEY**: Set in environment
- **Playwright**: `npm install` in `scripts/` for X scraper
- **playwright-headless MCP**: Configured in `.mcp.json` for link investigation

## Conventions

- Read the skill/agent file before executing a stage
- Slug format: `short-descriptive-name` (lowercase, hyphenated). Use `bash scripts/slugify.sh "$title"` for canonical slugification.
- Update folder format: `YYYY-MM-DD-HHMM-TZ` (youtube-digest, webpage-digest) or `YYYY-MM-DD` (x-digest)
- Timestamps: always use local timezone. Agents capture the full timestamp with timezone once at the start of a run via `bash scripts/get-timestamp.sh` (line 1 = display format, line 2 = path-safe format). Skills never run `date` — they use the agent-provided timestamp.
