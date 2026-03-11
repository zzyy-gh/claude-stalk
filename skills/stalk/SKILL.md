---
name: stalk
description: "This skill should be used when the user asks to 'check feeds', 'check for new videos', 'what's new', 'stalk', or 'check channels'. It checks YouTube channels and RSS/Atom feeds for new content and returns a list of unseen items."
version: "1.2"
---

# Skill: Stalk

Check configured sources for new content. Compare against stalk history and return only new (unseen) items.

## Inputs

- A session directory or session name (folder under `sessions/`)
- Reads `sessions/{name}/config.yaml` for source list
- Reads `sessions/{name}/stalk-history.yaml` for already-seen URLs

## Steps

1. **Load config**: Read `sessions/{name}/config.yaml` to get the `sources` list.

2. **Load stalk history**: Read `sessions/{name}/stalk-history.yaml`. Extract all `url` values into a set for fast lookup. If file doesn't exist or is empty, treat as empty set — this is a **seed run** (see below).

3. **Fetch each source**:

### YouTube channel
- Fetch `https://www.youtube.com/feeds/videos.xml?channel_id={id}` using WebFetch
- Prompt WebFetch to extract from each `<entry>`:
  - `videoId` from `<yt:videoId>`
  - `title` from `<title>`
  - `url` as `https://www.youtube.com/watch?v={videoId}`
  - `published` from `<published>` (may be absent)
  - `author` from `<author><name>`
- Set `source_type: youtube`
- Set `source_name` from the config entry's `name` field

### RSS/Atom feed
- Fetch the feed URL using WebFetch
- Prompt WebFetch to extract from each `<item>` (RSS) or `<entry>` (Atom):
  - `title` from `<title>`
  - `url` from `<link>` (RSS) or `<link href="...">` (Atom)
  - `published` from `<pubDate>` (RSS) or `<published>` (Atom) — **optional**, may not exist
  - `description` from `<description>` or `<summary>` (first 200 chars)
- Set `source_type: rss`
- Set `source_name` from the config entry's `name` field

4. **Filter**: Remove any item whose `url` appears in the stalk history set.

5. **Seed run check**: If the stalk history was empty or didn't exist before this run, this is a **seed run**:
   - Write all fetched items to stalk history (step 6)
   - But return **zero new items** — do not process anything
   - Report: "Seed run for {session-name}: recorded {count} existing items. New content will be detected on the next run."

6. **Write stalk history**: Append new items to `sessions/{name}/stalk-history.yaml`:
   ```yaml
   - url: "https://..."
     title: "Item Title"
     source_name: "Channel Name"
     first_seen: "2026-03-11 14:00"
     published: "2026-03-10 09:15"   # omit if unavailable
   ```
   If the file doesn't exist, create it with these entries. If it exists, append to the existing list.
   The `published` field is optional — some sources don't provide dates. `first_seen` is always set.

7. **Return** structured list of new items:

```yaml
new_items:
  - title: "Video Title"
    url: "https://www.youtube.com/watch?v=XXXXX"
    source_type: youtube
    source_name: "Channel Name"
    published: "2026-03-10 14:00"
    first_seen: "2026-03-11 14:00"
  - title: "Article Title"
    url: "https://blog.example.com/post"
    source_type: rss
    source_name: "Blog Name"
    first_seen: "2026-03-11 14:00"
```

Note: `published` is included when available, omitted when the source doesn't provide it. `first_seen` is always present.

## Important

- If a feed fetch fails, log the error and continue with remaining sources.
- Report any fetch failures at the end.
- Items are tracked by URL — dates are informational, not used for deduplication.

## Output

Print the list of new items as a formatted table:

```
| # | Source | Title | Published | URL |
|---|--------|-------|-----------|-----|
| 1 | Channel Name | Video Title | 2026-03-10 14:00 | https://... |
| 2 | Blog Name | Article Title | — | https://... |
```

If seed run, report the seed message instead.

If no new items found, report "No new content for {session-name}."
