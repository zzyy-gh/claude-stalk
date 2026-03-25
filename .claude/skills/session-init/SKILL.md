---
name: session-init
description: "Create a new monitoring session. Trigger: 'create session', 'new session', 'add session', 'session-init'. Supports youtube-digest (audio) and x-digest (X) session types."
version: "2.0"
---

# Skill: Session Init

Interactive wizard to create a new monitoring session for any supported content category.

## Steps

1. **Ask for category**:
   - `youtube-digest` — YouTube channels and RSS feeds (audio/video content)
   - `x-digest` — X (Twitter) lists or Following feed
   - Future: `website` — web monitoring

2. **Ask for session name**:
   - Get a short descriptive name (e.g., "ai-research", "tai-ai", "tech-podcasts")
   - Slugify: lowercase, hyphens, no spaces or special characters
   - This becomes the folder name under the category directory

3. **Category-specific source setup**:

### YouTube Stalker (audio)

Ask for sources (one at a time, loop until user says done):

**YouTube channel**:
- Accept channel URL, channel ID, or handle
- If given a URL like `https://www.youtube.com/channel/UCxxxxx` or `https://www.youtube.com/@handle`, extract the channel ID
- If given a handle (`@name`), warn that the channel ID is needed — user should find it
- Ask for a human-readable name

**RSS/Atom feed**:
- Accept the feed URL directly
- Optionally verify by fetching it
- Ask for a human-readable name

**Frequency**: Default `6h`, options: `1h`, `6h`, `12h`, `24h`

### X Stalker (X)

- **Source**: `"following"` or an X list URL
- **Account**: Session identifier for multi-account management (default: `"main"`)
- **Days**: Lookback window in days (default: 1)
- **Prompt**: Custom analysis prompt (default: VC/AI focused)

4. **Ask for export directory** (optional):
   - Where should HTML results be exported?
   - Default: `null` (results stay in the update folder)

5. **Create session structure**:

### YouTube Stalker
```bash
mkdir -p output/youtube-digest/{name}/updates
```
Use template: `.claude/skills/session-init/assets/config-template-audio.yaml`

Write `stalk-history.yaml` and `retry.yaml` as `[]`.

### X Stalker
```bash
mkdir -p output/x-digest/{name}/updates
```
Use template: `.claude/skills/session-init/assets/config-template-x.yaml`

6. **Confirm**: Print the created config and session path. Suggest running the appropriate agent.
