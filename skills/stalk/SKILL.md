---
name: stalk
description: "This skill should be used when the user asks to 'check feeds', 'check for new videos', 'what's new', 'stalk', or 'check channels'. It checks YouTube channels and RSS/Atom feeds for new content and returns a list of unseen items."
version: "1.0"
---

# Skill: Stalk

Check configured sources for new content. Compare against the seen list and return only new (unseen) items.

## Inputs

- A session name (folder under `sessions/`)
- Reads `sessions/{name}/config.yaml` for source list
- Reads `sessions/{name}/seen.yaml` for already-processed URLs

## Steps

1. **Load config**: Read `sessions/{name}/config.yaml` to get the `sources` list.

2. **Load seen list**: Read `sessions/{name}/seen.yaml`. Extract all `url` values into a set for fast lookup. If file doesn't exist or is empty, treat as empty set.

3. **Fetch each source**:

### YouTube channel
- Fetch `https://www.youtube.com/feeds/videos.xml?channel_id={id}` using WebFetch
- Prompt WebFetch to extract from each `<entry>`:
  - `videoId` from `<yt:videoId>`
  - `title` from `<title>`
  - `url` as `https://www.youtube.com/watch?v={videoId}`
  - `published` from `<published>`
  - `author` from `<author><name>`
- Set `source_type: youtube`
- Set `source_name` from the config entry's `name` field

### RSS/Atom feed
- Fetch the feed URL using WebFetch
- Prompt WebFetch to extract from each `<item>` (RSS) or `<entry>` (Atom):
  - `title` from `<title>`
  - `url` from `<link>` (RSS) or `<link href="...">` (Atom)
  - `published` from `<pubDate>` (RSS) or `<published>` (Atom)
  - `description` from `<description>` or `<summary>` (first 200 chars)
- Set `source_type: rss`
- Set `source_name` from the config entry's `name` field

4. **Filter**: Remove any item whose `url` appears in the seen set.

5. **Return** structured list of new items:

```yaml
new_items:
  - title: "Video Title"
    url: "https://www.youtube.com/watch?v=XXXXX"
    source_type: youtube
    source_name: "Channel Name"
    published: "2026-03-10T14:00:00Z"
  - title: "Article Title"
    url: "https://blog.example.com/post"
    source_type: rss
    source_name: "Blog Name"
    published: "2026-03-10"
```

## Important

- Do NOT update `seen.yaml` — that is the update skill's job after successful processing.
- If a feed fetch fails, log the error and continue with remaining sources.
- Report any fetch failures at the end.

## Output

Print the list of new items as a formatted table:

```
| # | Source | Title | Published | URL |
|---|--------|-------|-----------|-----|
| 1 | Channel Name | Video Title | 2026-03-10 | https://... |
```

If no new items found, report "No new content for {session-name}."
