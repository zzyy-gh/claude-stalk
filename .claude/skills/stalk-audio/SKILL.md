---
name: stalk-audio
description: "Check YouTube channels and RSS/Atom feeds for new content. Trigger: 'check feeds', 'check for new videos', 'what's new', 'stalk audio'. Returns only new (unseen) items."
version: "2.1"
forked: true
---

# Skill: Stalk Audio

Check configured sources for new content using a datetime-aware algorithm. Returns only new (unseen) items.

## Inputs

- A session directory or session name (folder under `output/youtube-digest/`)
- Reads `output/youtube-digest/{name}/config.yaml` for source list
- Reads `output/youtube-digest/{name}/stalk-history.yaml` for already-seen items and watermarks

## Algorithm Overview

The stalk algorithm is **datetime-aware**: it tracks the latest `published` date per source and only returns items newer than that watermark.

- **Sources with dates** (YouTube, most RSS): Use `published` date as the primary filter. Only items published after the source's watermark are considered new.
- **Sources without dates**: Fall back to URL-based dedup — any URL not in history is new.
- **Seed run** (no history for a source): Record the latest 5 items per source to establish the watermark. Return zero new items.

## Steps

1. **Load config**: Read `output/youtube-digest/{name}/config.yaml` to get the `sources` list.

2. **Load stalk history**: Confirm `output/youtube-digest/{name}/stalk-history.yaml` exists (or will be created). No manual parsing needed — `filter-stalk.py` handles watermark extraction and URL dedup internally.

3. **Fetch all sources + build candidates file** (single script):
   ```bash
   python scripts/build-candidates.py \
     --config "output/youtube-digest/{name}/config.yaml" \
     --output /tmp/stalk-candidates-{timestamp}.yaml
   ```
   - Reads `config.yaml`, fetches all YouTube channels (via `stalk-youtube.sh`) and RSS feeds (via `parse-feed.py`) in parallel
   - Writes combined candidates YAML to the output path
   - Progress and errors are printed to stderr

4. **Filter + seed** (via script):
   ```bash
   python scripts/filter-stalk.py \
     --history "output/youtube-digest/{name}/stalk-history.yaml" \
     --candidates /tmp/stalk-candidates-{timestamp}.yaml \
     --now "{TIMESTAMP}"
   ```
   - The script handles datetime-aware filtering (watermark comparison), URL dedup fallback, and seed mode (per source)
   - Output is YAML with three keys: `new_items`, `history_additions`, `seed_reports`
   - Save the output to a file or parse it directly

5. **Metadata + duration check** (YouTube items only):
   - Run only on `new_items` from step 4. Skip if zero candidates remain.
   - Batch-fetch dates and durations:
     ```bash
     bash scripts/batch-check-metadata.sh id1 id2 id3 ...
     ```
   - Output is tab-delimited: `videoId\tupload_date_YYYYMMDD\tduration_seconds`
   - Use `upload_date` for watermark filtering if not already available from step 3
   - If `duration <= 60` seconds or empty: mark as `short: true` on the corresponding `history_additions` entry and **remove from new_items**

6. **Write stalk history**: Append `history_additions` from step 4 (with any `short` flags from step 5) to `output/youtube-digest/{name}/stalk-history.yaml`
   - Each entry has: `url`, `title`, `source_name`, `source_type`, `first_seen`, and optionally `published` and `short`

7. **Print seed reports**: Print any messages from `seed_reports` (e.g., "Seed: Lex Fridman -- recorded 5 items, latest: 2026-03-10T14:00:00Z")

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
- Filtering, seed detection, watermark comparison, and URL dedup are all handled by `scripts/filter-stalk.py` -- do not reimplement this logic inline.

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
