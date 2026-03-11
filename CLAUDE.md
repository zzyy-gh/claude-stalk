# Claude Stalker

Monitor YouTube channels and RSS feeds for new content, ingest transcripts, and run custom per-session processing pipelines.

## Architecture

```
[update] → iterates sessions → [stalk] → finds new items → [custom-skill] → orchestrates pipeline
                                                                 ↓
                                                    uses shared skills as building blocks:
                                                    [ingest] → [transcribe] → custom processing
```

- **update**: High-level loop — iterates sessions, stalks for new content, delegates to each session's custom skill
- **stalk**: Checks YouTube RSS feeds and RSS/Atom feeds for new entries, filters against seen list
- **ingest**: Downloads content (yt-dlp for YouTube, WebFetch for articles) into `01-input-*` files
- **transcribe**: Produces `02-generated-transcript.md` from captions, audio (Groq Whisper MCP), or web content
- **custom-skill**: Per-session pipeline orchestrator — decides what to do with new items

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
├── config.yaml          # Sources, frequency, output_dir
├── seen.yaml            # Already-processed URLs
├── custom-skill/        # Per-session SKILL.md with assets/examples
│   ├── SKILL.md
│   ├── assets/
│   └── examples/
└── updates/
    └── YYYY-MM-DD-HHMM/
        ├── {item-slug}/
        │   ├── 01-input-*, metadata.yaml, 02-generated-transcript.md
        └── summary.md   # Cross-item output from custom skill
```

## Environment

- **yt-dlp**: `pip install yt-dlp`
- **Groq MCP**: Configured in `.claude/settings.json` for Whisper transcription
- **GROQ_API_KEY**: Set in environment

## Conventions

- Read the skill file before executing a stage
- Custom skills call shared skills (ingest, transcribe) as building blocks
- `seen.yaml` is only updated after successful processing
- Slug format: `short-descriptive-name` (lowercase, hyphenated)
- Update folder format: `YYYY-MM-DD-HHMM`
