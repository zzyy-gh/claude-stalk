---
name: ingest
description: "This skill should be used when the user asks to 'ingest', 'download content', 'get transcripts', or 'ingest this URL'. It downloads source material from a URL into a target directory without transforming content."
version: "1.0"
---

# Skill: Ingest

Collect raw source material into a target directory. **Do not transform or extract text** — that is the transcribe skill's job.

## Inputs

- A URL to ingest
- A target directory path (the item's subfolder within an update)

## Steps

1. **Identify the input type** from the URL:
   - YouTube URL → use yt-dlp
   - Podcast URL → web fetch to find audio URL, download audio
   - Web article URL → web fetch to save page content

2. **Create target directory** if it doesn't exist.

3. **Download source material** into the target directory as `01-input-*` files:

### YouTube URL
```bash
# Download captions + metadata (do NOT download video)
yt-dlp --write-sub --write-auto-sub --sub-lang en --skip-download --print-json -o "{target_dir}/01-input-video" "{url}" > {target_dir}/01-input-yt-metadata.json
```
- Captions saved as `01-input-video.en.vtt` (or `.en.srt`)
- If no captions available, download audio as fallback:
```bash
yt-dlp -x --audio-format mp3 -o "{target_dir}/01-input-audio.%(ext)s" "{url}"
```
- Set `transcript_source: youtube_captions` or `whisper` (if audio fallback)

### Podcast URL
- Web fetch the page to find the audio file URL (look for `.mp3`, `<audio>` tags, RSS enclosures)
- Download the audio file as `01-input-audio.mp3`
- Set `transcript_source: whisper`

### Web article URL
- Web fetch the page
- Save extracted text as `01-input-article.md`
- Set `transcript_source: web_extract`

4. **Write `metadata.yaml`** in the target directory:

```yaml
title: "Content Title"
source_url: "https://..."
source_type: youtube | podcast | web_article
transcript_source: youtube_captions | whisper | web_extract
date_published: "2026-03-11 14:30"
date_processed: "2026-03-11 14:30"
speakers: []
tags: []
duration: "1:23:45"
language: "en"
stages:
  ingest: { completed: true, timestamp: "2026-03-11 14:30" }
  transcribe: { completed: false }
```

### Field sources
- `title` — from yt-dlp metadata JSON, page title, or URL
- `source_url` — the input URL
- `source_type` — youtube, podcast, web_article
- `transcript_source` — as determined by input type and availability
- `date_published` — from metadata if available, otherwise omit or leave empty
- `date_processed` — current timestamp
- `duration` — from yt-dlp metadata if available

## Edge cases

- **YouTube with no captions AND no audio download possible**: Note in metadata, flag for user
- **Large files (>25MB audio)**: Note in metadata that chunking will be needed for transcription
- **Non-English content**: Set `language` field appropriately; yt-dlp `--sub-lang` may need adjusting

## Output checklist

- [ ] Target directory exists
- [ ] All source material saved as `01-input-*` files
- [ ] `metadata.yaml` written with all available fields
- [ ] `stages.ingest.completed` set to `true`
