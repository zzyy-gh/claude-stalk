#!/bin/bash
# Usage: get-timestamp.sh
# Output: Two lines:
#   Line 1: TIMESTAMP    — display format (YYYY-MM-DD HH:MM TZ)
#   Line 2: TIMESTAMP_PATH — path-safe format (YYYY-MM-DD-HHMM-TZ)

date +"%Y-%m-%d %H:%M %Z"
date +"%Y-%m-%d-%H%M-%Z"
