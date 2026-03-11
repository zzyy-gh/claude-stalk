---
name: transcribe
description: "This skill should be used when the user asks to 'transcribe', 'get transcript', 'transcribe this', or 'convert to text'. It produces a timestamped transcript from ingested source material using captions, Groq Whisper MCP, or text extraction."
version: "2.0"
---

# Skill: Transcribe

Produce a timestamped, readable transcript from whatever the ingest skill brought in.

The output is `02-generated-transcript.md` — the single source of truth for downstream processing.

## Steps

1. **Read `metadata.yaml`** in the item directory to determine `transcript_source` and find `01-input-*` files.

2. **Process by transcript source type**:

### youtube_captions
- Read `01-input-video.en.vtt` or `.srt`
- Parse cues into `(start_time, text)` pairs
- Deduplicate overlapping text (VTT often repeats lines across consecutive cues)
- Merge consecutive cues into paragraphs. Insert a paragraph break + new `[HH:MM:SS]` timestamp when:
  - Gap of 2+ seconds between cues (speech pause)
  - Speaker change detected
  - ~150-200 words accumulated in the current paragraph
- Each paragraph gets a `[HH:MM:SS]` marker from its first cue's start time
- Strip all VTT/SRT formatting tags and position metadata — only the timestamp markers and clean text remain

### whisper
- Find `01-input-audio.*` or `01-input-video.*`
- Check file size:
  - **≤25MB**: Send directly to Groq Whisper MCP
  - **>25MB**: Note limitation, ask user for guidance
- Use Groq MCP transcription tool with model `whisper-large-v3-turbo`
- Request `verbose_json` format to get segment-level timestamps
- Merge segments into paragraphs using the same logic as youtube_captions:
  - New paragraph + `[HH:MM:SS]` marker on 2+ second gaps, speaker changes, or ~150-200 words accumulated

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

4. **Update `metadata.yaml`**:
   - Set `stages.transcribe` to `{ completed: true, timestamp: "..." }`

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

## Output checklist

- [ ] `02-generated-transcript.md` written
- [ ] Timestamped paragraphs with `[HH:MM:SS]` markers (audio/video sources)
- [ ] Speaker labels if identifiable
- [ ] `metadata.yaml` updated with transcribe stage completion
