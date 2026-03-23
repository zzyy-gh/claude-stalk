---
name: stalk-audio
description: "Check YouTube channels and RSS/Atom feeds for new content. Trigger: 'check feeds', 'check for new videos', 'what's new', 'stalk audio'. Returns only new (unseen) items."
version: "2.1"
forked: true
---

# Skill: Stalk Audio

Check configured sources for new content using a datetime-aware algorithm. Returns only new (unseen) items.

## Inputs

- A session directory or session name (folder under `podcast/`)
- Reads `podcast/{name}/config.yaml` for source list
- Reads `podcast/{name}/stalk-history.yaml` for already-seen items and watermarks

## Algorithm Overview

The stalk algorithm is **datetime-aware**: it tracks the latest `published` date per source and only returns items newer than that watermark.

- **Sources with dates** (YouTube, most RSS): Use `published` date as the primary filter. Only items published after the source's watermark are considered new.
- **Sources without dates**: Fall back to URL-based dedup — any URL not in history is new.
- **Seed run** (no history for a source): Record the latest 5 items per source to establish the watermark. Return zero new items.

## Steps

1. **Load config**: Read `podcast/{name}/config.yaml` to get the `sources` list.

2. **Load stalk history**: Read `podcast/{name}/stalk-history.yaml`.
   - Extract `latest_published` per `source_name` — this is the **watermark** for each source.
   - Also extract all `url` values into a set (for URL-based fallback).
   - If file doesn't exist or is empty, all sources are in **seed** mode.

3. **Fetch each source**:

### YouTube channel

- Fetch the latest videos:
  ```bash
  bash scripts/stalk-youtube.sh "{handle}" 15
  ```
- Output is tab-delimited, one line per video: `videoId\ttitle\tupload_date_YYYYMMDD`
- `upload_date` may be empty (flat-playlist returns it inconsistently)
- Convert `upload_date` to ISO 8601 (e.g., `20260310` → `2026-03-10T00:00:00Z`)
- Build item: `url` as `https://www.youtube.com/watch?v={videoId}`, `title`, `published`
- Set `source_type: youtube`
- Set `source_name` from the config entry's `name` field

### RSS/Atom feed
- Fetch the feed URL using WebFetch
- Extract from each `<item>` (RSS) or `<entry>` (Atom):
  - `title` from `<title>`
  - `url` from `<link>` (RSS) or `<link href="...">` (Atom)
  - `published` from `<pubDate>` (RSS) or `<published>` (Atom) — **optional**, may not exist
  - `description` from `<description>` or `<summary>` (first 200 chars)
- Set `source_type: rss`
- Set `source_name` from the config entry's `name` field

4. **Filter** (per source):

### Datetime-aware filtering (when `published` dates are available)
- Find the **watermark** for this source: the `latest_published` value from stalk history for this `source_name`
- If watermark exists: keep only items where `published > watermark`
- Also check URLs against history set as a safety net (skip items already recorded)

### URL-based fallback (when dates are unavailable)
- If a source's items have no `published` dates, fall back to URL dedup
- Keep items whose `url` is not in the stalk history set

5. **Metadata + duration check** (YouTube items only):
   - Run only on candidates that survived filtering in step 4 (not all fetched items). Skip if zero candidates remain.
   - Batch-fetch dates and durations:
     ```bash
     bash scripts/batch-check-metadata.sh id1 id2 id3 ...
     ```
   - Output is tab-delimited: `videoId\tupload_date_YYYYMMDD\tduration_seconds`
   - Use `upload_date` for watermark filtering if not already available from step 3
   - If `duration ≤ 60` seconds or empty: mark as `short: true` — record in stalk history but **exclude from new_items**

6. **Seed run** (per source, not global):
   - A source is in seed mode if it has **no entries** in stalk history
   - For seed sources: sort fetched items by `published` (newest first), take the **latest 5**
   - Record these 5 in history (establishing the watermark) but return **zero new items** for this source
   - Report: "Seed: {source_name} — recorded {count} items, latest: {date}"
   - Non-seed sources in the same session are processed normally

7. **Write stalk history**: Append new items (including shorts) + seed items to `podcast/{name}/stalk-history.yaml`:
   ```yaml
   - url: "https://..."
     title: "Item Title"
     source_name: "Channel Name"
     source_type: youtube
     published: "2026-03-10T09:15:00Z"
     first_seen: "2026-03-11T14:00:00Z"
     short: true  # only present when true
   ```
   - `published` is optional (omit if unavailable)
   - `first_seen` is always set to current time
   - `short` is only set when `true` (omit for normal videos)
   - The **watermark** for each source is derived at read time as `max(published)` for that `source_name` — it's not stored separately

8. **Return** structured list of new items (excludes shorts):

```yaml
new_items:
  - title: "Video Title"
    url: "https://www.youtube.com/watch?v=XXXXX"
    source_type: youtube
    source_name: "Channel Name"
    published: "2026-03-10T14:00:00Z"
    first_seen: "2026-03-11T14:00:00Z"
```

## Important

- If a feed fetch fails, log the error and continue with remaining sources.
- Report any fetch failures at the end.
- Seed mode is **per source**, not per session — adding a new source to an existing session seeds just that source.
- The watermark is always derived as `max(published)` from history entries for that source_name. No separate field needed.
- Always use URL check as a safety net even when filtering by date, to avoid duplicate entries.

## Output

Print the list of new items as a formatted table:

```
| # | Source | Title | Published | URL |
|---|--------|-------|-----------|-----|
| 1 | Channel Name | Video Title | 2026-03-10 14:00 | https://... |
| 2 | Blog Name | Article Title | — | https://... |
```

For seed sources, report the seed message:
```
Seed: Lex Fridman — recorded 5 items, latest: 2026-03-10T14:00:00Z
Seed: 20VC — recorded 5 items, latest: 2026-03-09T08:00:00Z
```

If no new items found (and no seeds), report "No new content for {session-name}."
