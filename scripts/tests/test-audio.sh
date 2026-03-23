#!/bin/bash
# Test suite for pipeline scripts.
# Usage: bash scripts/tests/test-audio.sh [--online]
#   --online: also run tests that require network (yt-dlp)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
PASS=0
FAIL=0
SKIP=0
ONLINE=false

if [[ "${1:-}" == "--online" ]]; then
  ONLINE=true
fi

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1 -- $2"; }
skip() { SKIP=$((SKIP + 1)); echo "  SKIP: $1"; }

# ============================================================
echo "=== get-timestamp.sh ==="
# ============================================================

output=$(bash "$SCRIPT_DIR/get-timestamp.sh")
line1=$(echo "$output" | sed -n '1p')
line2=$(echo "$output" | sed -n '2p')

# Line 1: YYYY-MM-DD HH:MM TZ
if [[ "$line1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}\ [A-Z]{2,5}$ ]]; then
  pass "display format matches YYYY-MM-DD HH:MM TZ"
else
  fail "display format" "got: $line1"
fi

# Line 2: YYYY-MM-DD-HHMM-TZ
if [[ "$line2" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}-[A-Z]{2,5}$ ]]; then
  pass "path format matches YYYY-MM-DD-HHMM-TZ"
else
  fail "path format" "got: $line2"
fi

# Two lines exactly
line_count=$(echo "$output" | wc -l | tr -d ' ')
if [[ "$line_count" == "2" ]]; then
  pass "exactly 2 lines"
else
  fail "line count" "expected 2, got $line_count"
fi

# ============================================================
echo "=== slugify.sh ==="
# ============================================================

assert_slug() {
  local input="$1" expected="$2" label="$3"
  local actual
  actual=$(bash "$SCRIPT_DIR/slugify.sh" "$input")
  if [[ "$actual" == "$expected" ]]; then
    pass "$label"
  else
    fail "$label" "expected '$expected', got '$actual'"
  fi
}

assert_slug "Hello World" "hello-world" "basic words"
assert_slug "Video Title: With Colons!" "video-title-with-colons" "colons and punctuation"
assert_slug "React vs Vue | Which is Better?" "react-vs-vue-which-is-better" "pipe characters"
assert_slug "  Leading   Spaces  " "leading-spaces" "extra whitespace"
assert_slug "123 Numbers First" "123-numbers-first" "leading numbers"
assert_slug "ALL CAPS TITLE" "all-caps-title" "uppercase"
assert_slug "a--b---c" "a-b-c" "consecutive hyphens"

# Truncation at 50 chars
long_input="This Is A Very Long Title That Should Be Truncated At Fifty Characters On A Hyphen Boundary"
slug=$(bash "$SCRIPT_DIR/slugify.sh" "$long_input")
if [[ ${#slug} -le 50 ]]; then
  pass "truncation <= 50 chars (got ${#slug})"
else
  fail "truncation" "expected <= 50 chars, got ${#slug}: $slug"
fi

# No trailing hyphen after truncation
if [[ ! "$slug" =~ -$ ]]; then
  pass "no trailing hyphen after truncation"
else
  fail "trailing hyphen" "slug ends with hyphen: $slug"
fi

# Empty input exits 1
if ! bash "$SCRIPT_DIR/slugify.sh" "" 2>/dev/null; then
  pass "empty input exits non-zero"
else
  fail "empty input" "should have exited non-zero"
fi

# No args exits 1
if ! bash "$SCRIPT_DIR/slugify.sh" 2>/dev/null; then
  pass "no args exits non-zero"
else
  fail "no args" "should have exited non-zero"
fi

# ============================================================
echo "=== vtt-to-transcript.py ==="
# ============================================================

PYTHON=$(command -v python3 || command -v python)
VTT_FILE="$TEST_DIR/sample.vtt"

# Convert Git Bash path for Windows Python
VTT_FILE_PY="$VTT_FILE"
if [[ "$VTT_FILE_PY" =~ ^/([a-zA-Z])/ ]]; then
  VTT_FILE_PY="${BASH_REMATCH[1]^}:${VTT_FILE_PY:2}"
fi

transcript=$("$PYTHON" "$SCRIPT_DIR/vtt-to-transcript.py" "$VTT_FILE_PY" "Test Title" "https://example.com" 2>&1)

# Header present
if echo "$transcript" | grep -q "^# Transcript: Test Title$"; then
  pass "header present"
else
  fail "header" "missing '# Transcript: Test Title'"
fi

# Source URL comment
if echo "$transcript" | grep -q "<!-- Source: https://example.com -->"; then
  pass "source URL comment"
else
  fail "source URL" "missing source comment"
fi

# Timestamps in [HH:MM:SS] format
ts_count=$(echo "$transcript" | grep -c '^\[[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\]' || true)
if [[ "$ts_count" -ge 3 ]]; then
  pass "has $ts_count timestamped paragraphs"
else
  fail "timestamps" "expected >= 3 paragraphs, got $ts_count"
fi

# No VTT timing tags remain
if echo "$transcript" | grep -qE '<[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}>'; then
  fail "tag cleanup" "VTT timing tags still present"
else
  pass "no VTT timing tags remain"
fi

# No <c> tags remain
if echo "$transcript" | grep -q '</?c>'; then
  fail "c tag cleanup" "<c> tags still present"
else
  pass "no <c> tags remain"
fi

# Echo cues filtered (no duplicate-only lines)
# The word "Welcome" should appear only once in context
welcome_count=$(echo "$transcript" | grep -c "Welcome to the show" || true)
if [[ "$welcome_count" -le 1 ]]; then
  pass "echo cues filtered (Welcome appears $welcome_count time)"
else
  fail "echo cues" "Welcome appears $welcome_count times"
fi

# Gap-based paragraph break (5s gap at 00:20 -> 00:25)
if echo "$transcript" | grep -q '^\[00:00:25\]'; then
  pass "gap-based paragraph break at 00:25"
else
  fail "gap break" "expected new paragraph at [00:00:25]"
fi

# Manual captions (no timing tags) handled
if echo "$transcript" | grep -q "manually created caption"; then
  pass "manual captions handled"
else
  fail "manual captions" "untagged cue not found"
fi

# ============================================================
echo "=== stalk-youtube.sh (offline) ==="
# ============================================================

# Bad args
if ! bash "$SCRIPT_DIR/stalk-youtube.sh" 2>/dev/null; then
  pass "no args exits non-zero"
else
  fail "no args" "should have exited non-zero"
fi

# ============================================================
echo "=== batch-check-metadata.sh (offline) ==="
# ============================================================

if ! bash "$SCRIPT_DIR/batch-check-metadata.sh" 2>/dev/null; then
  pass "no args exits non-zero"
else
  fail "no args" "should have exited non-zero"
fi

# ============================================================
echo "=== ingest-youtube.sh (offline) ==="
# ============================================================

if ! bash "$SCRIPT_DIR/ingest-youtube.sh" 2>/dev/null; then
  pass "no args exits non-zero"
else
  fail "no args" "should have exited non-zero"
fi

if ! bash "$SCRIPT_DIR/ingest-youtube.sh" "https://example.com" 2>/dev/null; then
  pass "missing target_dir exits non-zero"
else
  fail "missing target_dir" "should have exited non-zero"
fi

# ============================================================
# Online tests (require network + yt-dlp)
# ============================================================

if $ONLINE; then
  echo "=== stalk-youtube.sh (online) ==="

  output=$(bash "$SCRIPT_DIR/stalk-youtube.sh" "lexfridman" 2)
  line_count=$(echo "$output" | wc -l | tr -d ' ')
  if [[ "$line_count" -ge 1 ]]; then
    pass "returns results ($line_count lines)"
  else
    fail "results" "no output"
  fi

  # Tab-delimited: at least 2 tabs per line
  first_line=$(echo "$output" | head -1)
  tab_count=$(echo "$first_line" | tr -cd '\t' | wc -c | tr -d ' ')
  if [[ "$tab_count" -ge 2 ]]; then
    pass "tab-delimited ($tab_count tabs)"
  else
    fail "delimiter" "expected >= 2 tabs, got $tab_count"
  fi

  # First field looks like a video ID (11 chars)
  vid_id=$(echo "$first_line" | cut -f1)
  if [[ ${#vid_id} -eq 11 ]]; then
    pass "video ID length (11 chars: $vid_id)"
  else
    fail "video ID" "expected 11 chars, got ${#vid_id}: $vid_id"
  fi

  echo "=== batch-check-metadata.sh (online) ==="

  output=$(bash "$SCRIPT_DIR/batch-check-metadata.sh" "$vid_id")
  first_line=$(echo "$output" | head -1)
  tab_count=$(echo "$first_line" | tr -cd '\t' | wc -c | tr -d ' ')
  if [[ "$tab_count" -ge 2 ]]; then
    pass "tab-delimited ($tab_count tabs)"
  else
    fail "delimiter" "expected >= 2 tabs, got $tab_count"
  fi

  # Duration field is numeric
  duration=$(echo "$first_line" | cut -f3)
  if [[ "$duration" =~ ^[0-9]+$ ]]; then
    pass "duration is numeric ($duration seconds)"
  else
    fail "duration" "expected numeric, got: $duration"
  fi

  echo "=== ingest-youtube.sh (online) ==="

  INGEST_DIR="/c/Users/zzyy/Desktop/claude-stalk/test-ingest-$$"
  # Use a short Creative Commons video
  output=$(bash "$SCRIPT_DIR/ingest-youtube.sh" "https://www.youtube.com/watch?v=$vid_id" "$INGEST_DIR" 2>/dev/null) || true

  if [[ -n "$output" ]]; then
    pass "produces output"
    tab_count=$(echo "$output" | tr -cd '\t' | wc -c | tr -d ' ')
    if [[ "$tab_count" -ge 3 ]]; then
      pass "tab-delimited ($tab_count tabs)"
    else
      fail "delimiter" "expected >= 3 tabs, got $tab_count"
    fi

    source_type=$(echo "$output" | cut -f1)
    if [[ "$source_type" == "captions" || "$source_type" == "whisper" || "$source_type" == "none" ]]; then
      pass "transcript_source valid ($source_type)"
    else
      fail "transcript_source" "expected captions/whisper/none, got: $source_type"
    fi
  else
    fail "output" "no output produced"
  fi

  # Check files exist
  if ls "$INGEST_DIR"/01-input-yt-metadata.json &>/dev/null; then
    pass "metadata JSON created"
  else
    fail "metadata JSON" "file not found"
  fi

  if ls "$INGEST_DIR"/01-input-video.en.* &>/dev/null || ls "$INGEST_DIR"/01-input-audio.* &>/dev/null; then
    pass "caption or audio file created"
  else
    fail "media files" "no caption or audio files found"
  fi

  # Cleanup
  rm -rf "$INGEST_DIR"
else
  skip "stalk-youtube.sh online (use --online)"
  skip "batch-check-metadata.sh online (use --online)"
  skip "ingest-youtube.sh online (use --online)"
fi

# ============================================================
echo ""
echo "=== Results ==="
echo "PASS: $PASS  FAIL: $FAIL  SKIP: $SKIP"
if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
