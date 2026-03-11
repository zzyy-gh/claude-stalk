---
name: session-init
description: "This skill should be used when the user asks to 'create session', 'new session', 'add session', 'setup stalker', or 'session-init'. It creates a new monitoring session with sources, config, and a custom processing skill."
version: "1.0"
---

# Skill: Session Init

Interactive wizard to create a new monitoring session.

## Steps

1. **Ask for session name**:
   - Get a short descriptive name from the user (e.g., "ai-research", "tech-podcasts")
   - Slugify: lowercase, hyphens, no spaces or special characters
   - This becomes the folder name under `sessions/`

2. **Ask for sources** (one at a time, loop until user says done):

   **YouTube channel**:
   - Accept channel URL, channel ID, or handle
   - If given a URL like `https://www.youtube.com/channel/UCxxxxx` or `https://www.youtube.com/@handle`, extract the channel ID
   - If given a handle (`@name`), warn that the channel ID is needed for RSS feeds — the user should find it from the channel page source or use `https://www.youtube.com/@handle` and look for the canonical channel ID
   - Verify the RSS feed works: `https://www.youtube.com/feeds/videos.xml?channel_id={ID}`
   - Ask for a human-readable name for this source

   **RSS/Atom feed**:
   - Accept the feed URL directly
   - Optionally verify by fetching it
   - Ask for a human-readable name

3. **Ask for update frequency** (informational hint for `/loop`):
   - Default: `6h`
   - Common options: `1h`, `6h`, `12h`, `24h`

4. **Ask about custom processing**:
   - Does the user want a custom skill for this session?
   - If yes, ask what it should do (summarize, extract quotes, just collect links, etc.)
   - If no, use the default template (ingest → transcribe → summarize)

5. **Ask for output directory** (optional):
   - Where should the custom skill export results?
   - Default: `null` (results stay in the update folder)

6. **Create session structure**:

```bash
mkdir -p sessions/{name}/custom-skill/assets sessions/{name}/custom-skill/examples sessions/{name}/updates
```

7. **Write `config.yaml`** using the template from `skills/session-init/assets/config-template.yaml`:

```yaml
name: "{Session Name}"
sources:
  - type: youtube_channel
    id: "{channel_id}"
    name: "{Channel Name}"
frequency: "{frequency}"
output_dir: null
```

8. **Write `seen.yaml`**:
```yaml
seen: []
```

9. **Scaffold custom skill**:
   - Copy `skills/session-init/assets/custom-skill-template/` contents into `sessions/{name}/custom-skill/`
   - If the user described specific processing, adapt the SKILL.md accordingly
   - If using defaults, copy the template as-is

10. **Confirm**: Print the created config and session path. Suggest running `/update {name}` to do the first check.
