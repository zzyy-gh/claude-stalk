#!/bin/bash
# Usage: slugify.sh "Some Video Title: With Special Chars!"
# Output: some-video-title-with-special-chars
# Exit: 0 = success, 1 = no input / empty result

set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: slugify.sh <title>" >&2
  exit 1
fi

slug=$(echo "$1" \
  | tr '[:upper:]' '[:lower:]' \
  | sed 's/[^a-z0-9 -]//g' \
  | sed 's/  */ /g' \
  | sed 's/ /-/g' \
  | sed 's/--*/-/g' \
  | sed 's/^-//;s/-$//')

# Truncate to 50 chars at a hyphen boundary
if [ ${#slug} -gt 50 ]; then
  slug="${slug:0:50}"
  # Cut at last hyphen to avoid partial words
  if [[ "$slug" == *-* ]]; then
    slug="${slug%-*}"
  fi
fi

if [ -z "$slug" ]; then
  echo "Error: title produced empty slug" >&2
  exit 1
fi

echo "$slug"
