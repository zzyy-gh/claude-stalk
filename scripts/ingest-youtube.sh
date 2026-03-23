#!/bin/bash
# Usage: ingest-youtube.sh <url> <target_dir>
# Output: Single tab-delimited line:
#   transcript_source\ttitle\tduration_seconds\tupload_date_YYYYMMDD
# transcript_source: captions, whisper, or none
# Exit: 0 = got captions or audio, 1 = bad args, 2 = both downloads failed

set -euo pipefail

if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
  echo "Usage: ingest-youtube.sh <url> <target_dir>" >&2
  exit 1
fi

url="$1"
target_dir="$2"

if ! command -v yt-dlp &>/dev/null; then
  echo "Error: yt-dlp not found" >&2
  exit 1
fi

mkdir -p "$target_dir"

# Step 1: Download captions + metadata JSON (no video)
yt-dlp --write-sub --write-auto-sub --sub-lang en --skip-download \
  --print-json \
  -o "${target_dir}/01-input-video" \
  "$url" > "${target_dir}/01-input-yt-metadata.json" 2>/dev/null || true

# Step 2: Check if captions were downloaded
transcript_source="none"
if ls "${target_dir}"/01-input-video.en.vtt &>/dev/null || ls "${target_dir}"/01-input-video.en.srt &>/dev/null; then
  transcript_source="captions"
fi

# Step 3: If no captions, try audio fallback
if [ "$transcript_source" = "none" ]; then
  if yt-dlp -x --audio-format mp3 \
    -o "${target_dir}/01-input-audio.%(ext)s" \
    "$url" 2>/dev/null; then
    transcript_source="whisper"
  fi
fi

# Step 4: Extract metadata from JSON
if [ -f "${target_dir}/01-input-yt-metadata.json" ] && [ -s "${target_dir}/01-input-yt-metadata.json" ]; then
  PYTHON=$(command -v python3 || command -v python)
  json_path="${target_dir}/01-input-yt-metadata.json"
  # Convert Git Bash /c/ paths to C:/ for Windows Python
  if [[ "$json_path" =~ ^/([a-zA-Z])/ ]]; then
    json_path="${BASH_REMATCH[1]^}:${json_path:2}"
  fi
  IFS=$'\t' read -r title duration upload_date < <("$PYTHON" -c "
import json
with open(r'${json_path}') as f:
    d = json.load(f)
title = d.get('title', '').replace('\t', ' ')
duration = str(d.get('duration', ''))
upload_date = d.get('upload_date', '')
print(f'{title}\t{duration}\t{upload_date}')
")
else
  title=""
  duration=""
  upload_date=""
fi

# Step 5: Output result
if [ "$transcript_source" = "none" ]; then
  printf '%s\t%s\t%s\t%s\n' "$transcript_source" "$title" "$duration" "$upload_date"
  exit 2
fi

printf '%s\t%s\t%s\t%s\n' "$transcript_source" "$title" "$duration" "$upload_date"
