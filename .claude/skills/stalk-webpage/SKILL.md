---
name: stalk-webpage
description: "Check RSS/Atom feeds for new webpage content. Trigger: 'check feeds', 'check for new articles', 'stalk webpage'. Returns only new (unseen) items."
version: "1.0"
forked: true
---

# Skill: Stalk Webpage

Check configured webpage sources for new articles via RSS/Atom feeds. Uses datetime-aware algorithm. Returns only new (unseen) items.

## Inputs

- A session directory or session name (folder under `output/webpage-digest/`)
- Reads `output/webpage-digest/{name}/config.yaml` for source list
- Reads `output/webpage-digest/{name}/stalk-history.yaml` for already-seen items and watermarks
- Reads/writes `output/webpage-digest/{name}/feed-cache.yaml` for auto-discovered feed URLs

## Algorithm Overview

Same datetime-aware algorithm as stalk-audio, but with RSS auto-discovery for webpage sources.

- **Sources with `feed_url` in config**: Use that feed directly.
- **Sources without `feed_url`**: Auto-discover RSS/Atom feed from the page's HTML `<link rel="alternate">` tags. Cache discovered URLs in `feed-cache.yaml` so discovery only happens once.
- **Discovery failure**: Log warning, skip source for this run. Does NOT cache a failure.
- **Seed run** (no history for a source): Record the latest 5 items per source to establish the watermark. Return zero new items.

## Steps

1. **Load config**: Read `output/webpage-digest/{name}/config.yaml` to get the `sources` list.

2. **Load stalk history**: Confirm `output/webpage-digest/{name}/stalk-history.yaml` exists (or will be created).

3. **Fetch all sources + build candidates file** (single script):
   ```bash
   python scripts/build-candidates.py \
     --config "output/webpage-digest/{name}/config.yaml" \
     --output /tmp/stalk-candidates-{timestamp}.yaml \
     --feed-cache "output/webpage-digest/{name}/feed-cache.yaml"
   ```
   - Reads `config.yaml`, fetches all webpage RSS feeds in parallel
   - Auto-discovers feeds for sources without `feed_url`, caches to `feed-cache.yaml`
   - Normalizes URLs via `normalize_url.py` before output
   - Writes combined candidates YAML to the output path

4. **Filter + seed** (via script):
   ```bash
   python scripts/filter-stalk.py \
     --history "output/webpage-digest/{name}/stalk-history.yaml" \
     --candidates /tmp/stalk-candidates-{timestamp}.yaml \
     --now "{TIMESTAMP}" \
     --normalize-urls
   ```
   - Handles datetime-aware filtering, URL dedup (with normalization), and seed mode
   - Output is YAML with three keys: `new_items`, `history_additions`, `seed_reports`

5. **Write stalk history**: Append `history_additions` to `output/webpage-digest/{name}/stalk-history.yaml`

6. **Print seed reports**: Print any messages from `seed_reports`.

7. **Return** structured list of new items.

## Important

- No metadata/duration check step (unlike stalk-audio which filters shorts). All new items pass through.
- Filtering, seed detection, watermark comparison, and URL dedup are all handled by `scripts/filter-stalk.py` -- do not reimplement this logic inline.
- The `--normalize-urls` flag ensures URL variants (tracking params, www, trailing slashes) are deduplicated.
- If a source's feed hasn't produced new content in 30+ days, warn the user.

## Output

Print the list of new items as a formatted table:

```
| # | Source | Title | Published | URL |
|---|--------|-------|-----------|-----|
| 1 | Anthropic Blog | New Model Release | 2026-03-25 | https://... |
| 2 | OpenAI Blog | Research Update | 2026-03-24 | https://... |
```

If no new items found (and no seeds), report "No new content for {session-name}."
