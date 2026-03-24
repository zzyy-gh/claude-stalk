#!/bin/bash
# Usage: notify-telegram.sh "message"
source "$(dirname "$0")/../.env" 2>/dev/null
[ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] && exit 0
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=$1" \
  -d "parse_mode=Markdown" > /dev/null 2>&1
