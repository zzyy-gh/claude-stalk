---
name: transcribe
description: "This skill should be used when the user asks to 'transcribe', 'get transcript', 'transcribe this', or 'convert to text'. It produces a clean transcript from ingested source material using captions, Groq Whisper MCP, or text extraction."
version: "1.0"
---

# Skill: Transcribe

Produce a clean, canonical transcript from whatever the ingest skill brought in.

The output is `02-generated-transcript.md` — the single source of truth for downstream processing.

## Steps

1. **Read `metadata.yaml`** in the item directory to determine `transcript_source` and find `01-input-*` files.

2. **Process by transcript source type**:

### youtube_captions
- Read `01-input-video.en.vtt` or `.srt`
- Strip all timestamps, formatting tags, and position metadata
- Merge fragmented caption lines into coherent paragraphs
- Remove duplicate lines (captions often overlap)
- Result: clean prose transcript

### whisper
- Find `01-input-audio.*` or `01-input-video.*`
- Check file size:
  - **≤25MB**: Send directly to Groq Whisper MCP
  - **>25MB**: Note limitation, ask user for guidance
- Use Groq MCP transcription tool with model `whisper-large-v3-turbo`
- Request `text` or `verbose_json` format
- Clean up the output: fix obvious spacing issues, add paragraph breaks at natural pauses

### web_extract
- Read `01-input-article.html` or `01-input-article.md`
- If HTML: extract body text, strip navigation, ads, boilerplate
- Clean up: fix formatting, preserve headings and structure

3. **Write `02-generated-transcript.md`**:
   - Start with a header: `# Transcript: {title}`
   - Include source URL as a brief comment
   - Clean, readable prose organized into paragraphs
   - If speakers are identifiable, format as:
     ```
     **Speaker Name:** Their words here.

     **Other Speaker:** Their response here.
     ```

4. **Update `metadata.yaml`**:
   - Set `stages.transcribe` to `{ completed: true, timestamp: "..." }`

## Quality checks

- No leftover timestamp artifacts (e.g., `00:01:23.456 --> 00:01:25.789`)
- No HTML tags or VTT formatting codes
- No duplicate consecutive lines
- Paragraphs are reasonable length
- Speaker labels are consistent if present

## Edge cases

- **Auto-generated YouTube captions**: Lower quality — do extra cleanup, fix common speech-to-text errors where obvious
- **Multiple languages**: Note in metadata; transcribe the primary language
- **Very long content (>2hrs)**: Still produce the full transcript, do not truncate
- **No usable input**: Update metadata with an error note and stop

## Output checklist

- [ ] `02-generated-transcript.md` written
- [ ] Clean, readable prose with no artifacts
- [ ] Speaker labels if identifiable
- [ ] `metadata.yaml` updated with transcribe stage completion
