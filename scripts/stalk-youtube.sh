#!/bin/bash
# Usage: stalk-youtube.sh <channel_handle> [max_items=15]
# Output: Tab-delimited, one line per video:
#   videoId\ttitle\tupload_date_YYYYMMDD
# upload_date may be empty (flat-playlist returns it inconsistently)
# Exit: 0 = success (even 0 results), 1 = bad args, 2 = yt-dlp failed

set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: stalk-youtube.sh <channel_handle> [max_items]" >&2
  exit 1
fi

handle="$1"
max_items="${2:-15}"

if ! command -v yt-dlp &>/dev/null; then
  echo "Error: yt-dlp not found" >&2
  exit 1
fi

yt-dlp --flat-playlist \
  --print $'%(id)s\t%(title)s\t%(upload_date)s' \
  --playlist-items "1-${max_items}" \
  "https://www.youtube.com/@${handle}/videos" 2>/dev/null || exit 2
