# Claude Stalker

Monitor YouTube channels and RSS feeds for new content, ingest transcripts, and run custom per-session processing pipelines.

## Architecture

```
[update] → iterates enabled sessions → [process] (per-session pipeline):
                                        [stalk] → [ingest] → [transcribe] → [summarize]
```

- **update**: Minimal orchestrator — loops enabled sessions, runs each session's process
- **stalk**: Checks YouTube RSS feeds and RSS/Atom feeds for new entries, filters against stalk history, writes new items to `stalk-history.yaml`
- **ingest**: Downloads content (yt-dlp for YouTube, WebFetch for articles) into `01-input-*` files
- **transcribe**: Produces `02-generated-transcript.md` from captions, audio (Groq Whisper MCP), or web content
- **process**: Per-session pipeline definition — starts with stalk, then ingests/transcribes/summarizes new items

## Skills

| Skill | Purpose | Trigger |
|---|---|---|
| **stalk** | Check feeds for new content | `/stalk`, "check feeds", "what's new" |
| **ingest** | Download/ingest content from URLs | `/ingest`, "download this", "ingest" |
| **transcribe** | Produce transcript from source material | `/transcribe`, "transcribe this" |
| **update** | Run full update cycle for sessions | `/update`, "run update", "check all" |
| **session-init** | Create a new monitoring session | `/session-init`, "new session", "create session" |

## Session Structure

```
sessions/{name}/
├── config.yaml            # Sources, frequency, enabled flag, output_dir
├── stalk-history.yaml     # URLs already seen by stalk
├── process/               # Per-session pipeline definition
│   ├── SKILL.md
│   ├── assets/
│   └── examples/
└── updates/
    └── YYYY-MM-DD-HHMM/
        ├── {item-slug}/
        │   ├── 01-input-*, metadata.yaml, 02-generated-transcript.md
        └── summary.md
```

## Environment

- **yt-dlp**: `pip install yt-dlp`
- **Groq MCP**: Configured in `.claude/settings.json` for Whisper transcription
- **GROQ_API_KEY**: Set in environment

## Conventions

- Read the skill file before executing a stage
- Stalk owns `stalk-history.yaml` — writes it after finding new items
- Process is the full pipeline definition per session; update just invokes it
- Slug format: `short-descriptive-name` (lowercase, hyphenated)
- Update folder format: `YYYY-MM-DD-HHMM`
