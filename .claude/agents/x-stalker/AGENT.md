---
name: x-stalker
description: "X/Twitter digest pipeline: scrapes feeds, analyzes posts, produces digests. Trigger: 'run digest', 'digest my feed', 'run x digest', 'run x-stalker'."
version: "1.0"
---

# Agent: X Stalker

Full pipeline orchestrator for X (Twitter) feed digests. Scrapes feeds, analyzes posts, and produces markdown + HTML digests.

## Inputs

- `SESSION`: session name or `all` (default: all enabled sessions under `output/x-stalker/`)

### Setup

Run `node scripts/now.js` to get the local date for filenames.

## Multi-session orchestration

When `SESSION` is `all` (or omitted):
- List all `output/x-stalker/*/config.yaml`
- Filter to `enabled: true`
- Process sessions sequentially — each session completes its full pipeline before the next starts
- Print final summary across sessions

When `SESSION` is a specific name:
- Run the pipeline for `output/x-stalker/{SESSION}/` only

## Notification

Send Telegram notifications:

- On start: `bash scripts/notify-telegram.sh "[claude-stalk] X digest started."`
- On input needed: `bash scripts/notify-telegram.sh "[claude-stalk] Need your input -- check Remote Control"`

## Pipeline (per session)

`SESSION_DIR` = `output/x-stalker/{name}/`

### 1. Load config

Read `{SESSION_DIR}/config.yaml` for: `name`, `source`, `account`, `days`, `prompt`, `export_dir`.

Defaults (when config values are missing):

| Setting | Default |
|---------|---------|
| source | User's Following feed |
| days | 1 |
| prompt | VC/startup focused analysis |
| export_dir | *(none)* |
| account | "main" |

### 2. Create update directory

Create `{SESSION_DIR}/updates/{YYYY-MM-DD}/` using today's local date.

### 3. Stalk X

Read `.claude/skills/stalk-x/SKILL.md` and execute it:

- `source`: from config
- `days`: from config
- `account`: from config
- `UPDATE_DIR`: the update directory from step 2

After scraping, report one line: "Scraped N posts from N accounts."

### 4. Verify browser

Confirm headless MCP browser is still open (re-open if needed) before analysis.

### 5. Analyze X

Read `.claude/skills/analyze-x/SKILL.md` and execute it:

- `UPDATE_DIR`: the update directory

After analysis, report one line: "Analysis complete. N links investigated."

### 6. Write summary

Read `.claude/skills/write-summary-x/SKILL.md` and execute it:

- `UPDATE_DIR`: the update directory
- Config values: `name`, `prompt`
- Scrape timing: `startTime` and `endTime` from stalk-x output

### 7. Due diligence

Execute the due-diligence skill:

- `SUMMARY`: `{UPDATE_DIR}/digest.md`

### 8. Generate HTML

Execute the generate-html skill:

- `SUMMARY`: `{UPDATE_DIR}/digest.md`
- `CATEGORY`: `x`
- `OUTPUT`: `{UPDATE_DIR}/digest.html`

### 9. Verify HTML

Execute the verify-html skill on `{UPDATE_DIR}/digest.md` and `{UPDATE_DIR}/digest.html`. If any critical check fails, regenerate with `python scripts/md-to-html.py`.

### 10. Export (if configured)

If `config.yaml` has `export_dir`:
- Ensure the directory exists: `mkdir -p "{export_dir}"`
- Copy: `cp "{UPDATE_DIR}/digest.html" "{export_dir}/{name} {YYYY-MM-DD}.html"`
- Report the exported file path

### 11. Cleanup

Close headless MCP browser session, even if a prior step failed:
- `playwright-headless:browser_close`

## Conversation output rules

- **After stalk-x:** One line only, e.g. "Scraped 286 posts from 24 accounts."
- **After analyze-x:** One line only, e.g. "Analysis complete. 3 links investigated."
- **After write-summary-x:** Present the file path to the user.
- **Between steps:** No intermediate batch counts, scroll progress, or tool result narration — just the outcome.
- **write-summary-x reads from files**, not from conversation context. Never paste file contents into the conversation for the output skill to consume.
