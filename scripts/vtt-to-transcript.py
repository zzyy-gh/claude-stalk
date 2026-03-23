#!/usr/bin/env python3
"""Convert VTT captions to a clean timestamped transcript.

Usage: vtt-to-transcript.py <vtt_file> <title> [source_url]
Output: Transcript markdown to stdout

Handles auto-generated YouTube VTT:
- Skips echo cues (near-zero duration)
- Extracts only new content (lines with inline timing tags)
- Merges into paragraphs (~175 words, breaking on 4s+ gaps)
- Outputs [HH:MM:SS] timestamp markers
"""

import re
import sys
import io


def parse_timestamp(ts):
    """Parse VTT timestamp (HH:MM:SS.mmm) to seconds."""
    parts = ts.replace(",", ".").split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


def format_timestamp(seconds):
    """Format seconds as [HH:MM:SS]."""
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    return f"[{h:02d}:{m:02d}:{s:02d}]"


def strip_tags(text):
    """Remove VTT formatting tags and inline timestamps."""
    text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
    text = re.sub(r"</?c>", "", text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    return text.strip()


def has_timing_tags(line):
    """Check if a line contains inline VTT timing tags (marks new content)."""
    return bool(re.search(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", line))


def parse_vtt(filepath):
    """Parse VTT file, extracting only new content from each cue.

    Auto-generated YouTube VTT pattern:
    - Content cues have 2 lines: repeated context (no tags) + new words (with timing tags)
    - Echo cues have near-zero duration and just repeat accumulated text -- skip these
    - Some cues have only a tagged line (new sentence start)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    cues = []

    # Parse line-by-line: find timing lines, collect text until next timing or blank gap
    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for timing line
        if "-->" not in line:
            i += 1
            continue

        timing_line = line
        text_lines = []
        i += 1

        # Collect text lines: everything after timing until a blank line
        # followed by another timing line (or end of file)
        while i < len(lines):
            curr = lines[i]
            # Stop if we hit another timing line
            if "-->" in curr:
                break
            # Stop at truly blank line only if next non-blank has timing
            if not curr.strip():
                # Peek ahead for next timing line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j >= len(lines) or "-->" in lines[j]:
                    i = j
                    break
            text_lines.append(curr)
            i += 1

        if not text_lines:
            continue

        # Parse start and end time
        match = re.match(r"([\d:.]+)\s*-->\s*([\d:.]+)", timing_line)
        if not match:
            continue

        start = parse_timestamp(match.group(1))
        end = parse_timestamp(match.group(2))

        # Skip echo cues (duration < 0.1s)
        if end - start < 0.1:
            continue

        # Extract only new content from the cue.
        # Auto-gen VTT pattern: line 1 = repeated context, line 2 = new words
        # New content lines have inline timing tags; context lines don't.
        tagged_lines = [l for l in text_lines if has_timing_tags(l)]
        if tagged_lines:
            # Take only lines with timing tags (new content)
            raw_text = " ".join(tagged_lines)
        elif len(text_lines) > 1:
            # Multi-line, no tags: last non-empty line is new content
            non_empty = [l for l in text_lines if l.strip()]
            raw_text = non_empty[-1] if non_empty else ""
        else:
            # Single line, no tags (manual captions or plain text)
            raw_text = text_lines[0]

        clean = strip_tags(raw_text)
        if not clean.strip():
            continue

        cues.append((start, clean))

    return cues


def merge_into_paragraphs(cues, gap_threshold=4.0, word_limit=175):
    """Merge cues into paragraphs.

    Break on:
    - Gap of gap_threshold+ seconds between cues
    - Accumulated ~word_limit words
    """
    if not cues:
        return []

    paragraphs = []
    current_words = []
    current_start = cues[0][0]
    prev_time = cues[0][0]

    for start, text in cues:
        gap = start - prev_time
        word_count = len(" ".join(current_words).split())

        if current_words and (gap >= gap_threshold or word_count >= word_limit):
            paragraphs.append((current_start, " ".join(current_words)))
            current_words = []
            current_start = start

        current_words.append(text)
        prev_time = start

    if current_words:
        paragraphs.append((current_start, " ".join(current_words)))

    return paragraphs


def main():
    if len(sys.argv) < 3:
        print("Usage: vtt-to-transcript.py <vtt_file> <title> [source_url]", file=sys.stderr)
        sys.exit(1)

    # Force UTF-8 stdout on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    vtt_file = sys.argv[1]
    title = sys.argv[2]
    source_url = sys.argv[3] if len(sys.argv) > 3 else ""

    cues = parse_vtt(vtt_file)
    paragraphs = merge_into_paragraphs(cues)

    print(f"# Transcript: {title}")
    if source_url:
        print(f"<!-- Source: {source_url} -->")
    print()

    for start, text in paragraphs:
        print(f"{format_timestamp(start)} {text}")
        print()


if __name__ == "__main__":
    main()
