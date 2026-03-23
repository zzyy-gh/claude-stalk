---
name: stalk-x
description: >
  Scrapes X.com feeds (Following or lists) — handles session detection, login flow,
  and feed scraping. Returns raw post data for downstream analysis.
  Trigger phrases: "scrape feed", "scrape following", "scrape my X", "stalk x".
version: "1.0"
compatibility: "Requires playwright npm package installed."
---

# Skill: Stalk X

Authenticates to X.com and scrapes feed data (posts, links, images, metrics) for downstream analysis.

All auth, navigation, and scraping is handled by `scripts/scrape-x.js` — a standalone Node script using Playwright directly. Login (headed) is handled by the script; no headed MCP server needed.

---

## Input Contract

Receives from the pipeline orchestrator:

- **`source`** — `"following"` or an X list URL (e.g. `https://x.com/i/lists/123456`)
- **`days`** — lookback window (default: 1)
- **`account`** — account identifier for session management
- **`UPDATE_DIR`** — path to the session's update directory for this run

---

## Step 1 — Run the scrape script

Execute via Bash:

```bash
node scripts/scrape-x.js --source SOURCE --days DAYS --account ACCOUNT --output "{UPDATE_DIR}/scrape.json"
```

Where:
- `SOURCE` is `"following"` or the list URL from config
- `DAYS` is the numeric lookback window from config
- `ACCOUNT` is the account identifier from config (default: `"main"`)
- `{UPDATE_DIR}` is the session's update directory for this run

The script handles everything internally:
1. **Session check** — launches headless browser, navigates to x.com/home, verifies login
2. **Account verification** — if `--account` is set (not "main"), checks logged-in username matches
3. **Login flow** — if not logged in or wrong account, opens headed browser for manual 2FA login, auto-detects completion
4. **Navigation** — clicks Following tab or navigates to list URL
5. **Scraping** — scrolls feed, extracts posts (original only, skips retweets/replies), stops after 3 consecutive all-old scrolls or 1000 post cap
6. **Save** — writes JSON to the output path
7. **Cleanup** — closes browser automatically

### stdout output

The script prints a single JSON line to stdout:

```json
{"startTime":1711180800000,"endTime":1711184400000,"stats":{"totalPosts":286,"totalAccounts":24,"hitCutoff":true},"error":null}
```

Human-readable messages (login prompts, progress) go to stderr.

### Step 2 — Record timing

Parse the stdout JSON and save `startTime` and `endTime` for downstream use.

---

## Output Contract

This skill produces:

- **`{UPDATE_DIR}/scrape.json`** — file keyed by handle, each value an array of post objects with: `text`, `time`, `url`, `displayName`, `externalLinks`, `images`, `metrics`
- **Scrape timing** — `startTime` and `endTime` timestamps (from stdout JSON)

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| Not logged in | Script auto-opens headed browser for manual login |
| Wrong account logged in | Script clears session, opens headed login for correct account |
| Session expires mid-run | Script detects and triggers login flow |
| Private/inaccessible list | Script exits with error in stdout JSON — report to user |
| account unset or "main" | Script accepts whatever account is logged in |
| List URL invalid or inaccessible | Script exits with error — report to user |
| Very large feed (many posts) | Capped at 1000 posts. Posts accumulate in-memory, written to disk at end. |
| Browser closed during login | Script treats as session saved, re-checks headless |
| User asks for > 7 days lookback | Warn about time; proceed if confirmed |
| Login timeout (default 120s) | Script exits with error — report to user |
