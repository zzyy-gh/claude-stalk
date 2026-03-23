# TODO

## Local audio-to-text transcription with timestamps

**Need**: Videos without YouTube captions (e.g., newly published, auto-captions disabled) need a local transcription path that produces timestamped output.

**Current gap**: Groq Whisper MCP has a 25MB file size limit. Very long videos (e.g., 5hr Lex Fridman episodes) exceed this even after audio extraction, requiring chunking logic that doesn't exist yet.

**Desired**: A local Whisper model (`whisper.cpp`, `faster-whisper`, or similar) that can:

- Handle arbitrarily large audio files
- Produce word- or segment-level timestamps
- Output in a format compatible with `02-generated-transcript.md` (e.g., `[HH:MM:SS]` markers)

**Bonus**: Removes dependency on external API for transcription — runs fully offline, no rate limits or file size constraints.

## Future: Website monitoring category

Add a `website/` category for monitoring blogs, documentation pages, and other web content on a schedule.
