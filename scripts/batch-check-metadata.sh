#!/bin/bash
# Usage: batch-check-metadata.sh <video_id> [video_id...]
# Output: Tab-delimited, one line per video:
#   videoId\tupload_date_YYYYMMDD\tduration_seconds
# Fields may be empty if unavailable. Private/deleted videos are skipped.
# Exit: 0 = got data, 1 = no args, 2 = yt-dlp failed, 3 = zero results

set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Usage: batch-check-metadata.sh <video_id> [video_id...]" >&2
  exit 1
fi

if ! command -v yt-dlp &>/dev/null; then
  echo "Error: yt-dlp not found" >&2
  exit 2
fi

# Build URL list from video IDs
urls=()
for id in "$@"; do
  urls+=("https://www.youtube.com/watch?v=${id}")
done

output=$(yt-dlp --skip-download \
  --print $'%(id)s\t%(upload_date)s\t%(duration)s' \
  "${urls[@]}" 2>/dev/null) || exit 2

if [ -z "$output" ]; then
  exit 3
fi

echo "$output"
