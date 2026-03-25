---
name: transcribe-audio
description: "Produce a timestamped transcript from ingested source material using captions, Groq Whisper MCP, or text extraction. Trigger: 'transcribe', 'get transcript', 'transcribe this'."
version: "2.0"
forked: true
---

# Skill: Transcribe Audio

Produce a timestamped, readable transcript from whatever the ingest-audio skill brought in.

The output is `02-generated-transcript.md` — the single source of truth for downstream processing.

## Inputs

- `ITEM_DIR`: path to the item directory (contains `01-input-*` files and `metadata.yaml`)
- `TIMESTAMP`: provided by the calling agent (e.g., `2026-03-20 00:21 CST`)

## Steps

1. **Read `metadata.yaml`** in the item directory to determine `transcript_source` and find `01-input-*` files.

2. **Process by transcript source type**:

### youtube_captions
- Find `01-input-video.en.vtt` or `.srt` in the item directory
- Run the VTT-to-transcript script:
  ```bash
  PYTHON=$(command -v python3 || command -v python)
  "$PYTHON" scripts/vtt-to-transcript.py "{vtt_file}" "{title}" "{source_url}" > "{ITEM_DIR}/02-generated-transcript.md"
  ```
- The script handles: parsing cues, deduplicating overlapping text, stripping VTT formatting tags, and merging into paragraphs with `[HH:MM:SS]` timestamp markers (breaks on 4s+ gaps or ~175 words)
- After running, review the output for obvious speaker labels if identifiable (e.g., `**Jensen Huang:** [00:03:28] Welcome to GTC.`)

### whisper
- Find `01-input-audio.*` or `01-input-video.*`
- Check file size:
  - **≤25MB**: Send directly to Groq Whisper MCP
  - **>25MB**: Note limitation, ask user for guidance
- Use Groq MCP transcription tool with model `whisper-large-v3-turbo`
- Request `verbose_json` format to get segment-level timestamps
- Merge segments into paragraphs using the same logic as youtube_captions:
  - New paragraph + `[HH:MM:SS]` marker on 4+ second gaps, speaker changes, or ~175 words accumulated
- TODO: Extract this segment-merging logic into a script (like `vtt-to-transcript.py` handles VTT). Currently runs as inline code.

### web_extract
- Read `01-input-article.html` or `01-input-article.md`
- If HTML: extract body text, strip navigation, ads, boilerplate
- Clean up: fix formatting, preserve headings and structure
- No timestamps (articles don't have them)

3. **Write `02-generated-transcript.md`**:
   - Start with a header: `# Transcript: {title}`
   - Include source URL as a brief comment
   - Timestamped paragraphs for audio/video sources:
     ```
     [00:00:00] Introduction paragraph merged from caption cues...

     [00:01:15] Next paragraph begins here after a pause or topic shift...

     **Speaker Name:** [00:05:23] Their words here when speakers are identifiable...
     ```
   - For web content: clean readable prose organized into paragraphs (no timestamps)

## Quality checks

- Timestamps appear only at paragraph starts as `[HH:MM:SS]`
- No raw VTT/SRT timing metadata remains (e.g., `00:01:23.456 --> 00:01:25.789`)
- No HTML tags or VTT formatting codes
- No duplicate consecutive lines
- Paragraphs are reasonable length (roughly 150-200 words)
- Speaker labels are consistent if present

## Edge cases

- **Auto-generated YouTube captions**: Lower quality — do extra cleanup, fix common speech-to-text errors where obvious
- **Multiple languages**: Note in metadata; transcribe the primary language
- **Very long content (>2hrs)**: Still produce the full transcript, do not truncate
- **No usable input**: Update metadata with an error note and stop
- **Retry**: When retrying a previously failed transcription, re-check for captions first — they may now be available. Prefer captions over audio if found. If the method changed, update `transcript_source` in `metadata.yaml`. On success, the caller handles `retry.yaml` cleanup

## Output checklist

- [ ] `02-generated-transcript.md` written
- [ ] Timestamped paragraphs with `[HH:MM:SS]` markers (audio/video sources)
- [ ] Speaker labels if identifiable
