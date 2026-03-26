#!/usr/bin/env python3
"""Build stalk candidates YAML from configured sources.

Reads a session config.yaml, fetches all sources in parallel
(YouTube via stalk-youtube.sh, RSS via parse-feed.py, webpages via
RSS auto-discovery), and writes the combined candidates YAML file.

Usage:
    python build-candidates.py --config PATH --output PATH [--max-items N]
    python build-candidates.py --config PATH --output PATH --feed-cache PATH  (webpage sources)

Exit codes: 0 = success, 1 = bad args, 2 = no sources fetched
"""

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_url import normalize_url

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = sys.platform == "win32"

# Ensure subprocesses use UTF-8 encoding (Windows defaults to cp1252)
_SUBPROCESS_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"} if IS_WINDOWS else None


def run_cmd(cmd_list, **kwargs):
    """Run a command, using shell=True on Windows for path compatibility."""
    if IS_WINDOWS:
        # Use double quotes on Windows (cmd.exe doesn't understand single quotes)
        def _win_quote(s):
            s = str(s)
            if ' ' in s or '&' in s or '(' in s or ')' in s:
                return f'"{s}"'
            return s
        cmd_str = " ".join(_win_quote(c) for c in cmd_list)
        return subprocess.run(cmd_str, shell=True, **kwargs)
    return subprocess.run(cmd_list, **kwargs)


def fetch_youtube(source, max_items):
    """Fetch videos from a YouTube channel via stalk-youtube.sh."""
    handle = source.get("handle")
    name = source.get("name", handle)
    if not handle:
        print(f"  SKIP: YouTube source missing 'handle': {source}", file=sys.stderr)
        return []

    script = os.path.join(SCRIPTS_DIR, "stalk-youtube.sh")
    try:
        result = run_cmd(
            ["bash", script, handle, str(max_items)],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(f"  FAIL: {name} — timed out", file=sys.stderr)
        return []

    if result.returncode != 0:
        print(f"  FAIL: {name} — exit {result.returncode}", file=sys.stderr)
        return []

    candidates = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        video_id = parts[0]
        title = parts[1]
        upload_date = parts[2] if len(parts) > 2 else ""

        entry = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": title,
            "source_name": name,
            "source_type": "youtube",
        }

        if upload_date and upload_date != "NA" and len(upload_date) == 8 and upload_date.isdigit():
            entry["published"] = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T00:00:00Z"

        candidates.append(entry)

    print(f"  OK: {name} — {len(candidates)} videos", file=sys.stderr)
    return candidates


def fetch_rss(source, _max_items):
    """Fetch items from an RSS/Atom feed via parse-feed.py."""
    url = source.get("url")
    name = source.get("name", url)
    if not url:
        print(f"  SKIP: RSS source missing 'url': {source}", file=sys.stderr)
        return []

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as tmp:
            tmp_path = tmp.name
            req = urllib.request.Request(url, headers={"User-Agent": "claude-stalk/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                tmp.write(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  FAIL: {name} — fetch error: {e}", file=sys.stderr)
        return []

    script = os.path.join(SCRIPTS_DIR, "parse-feed.py")
    try:
        result = run_cmd(
            ["python", script, "--source-name", name, "--file", tmp_path],
            capture_output=True, text=True, timeout=30, env=_SUBPROCESS_ENV,
        )
    finally:
        os.unlink(tmp_path)

    if result.returncode != 0:
        print(f"  FAIL: {name} — parse error: {result.stderr.strip()}", file=sys.stderr)
        return []

    try:
        items = yaml.safe_load(result.stdout)
        if not isinstance(items, list):
            items = []
    except yaml.YAMLError:
        print(f"  FAIL: {name} — invalid YAML from parse-feed.py", file=sys.stderr)
        return []

    print(f"  OK: {name} — {len(items)} items", file=sys.stderr)
    return items


# --- Feed cache for webpage sources (thread-safe) ---

_feed_cache = {}
_feed_cache_lock = threading.Lock()
_feed_cache_path = None
_feed_cache_dirty = False


def _load_feed_cache(path):
    """Load feed-cache.yaml into the module-level cache."""
    global _feed_cache, _feed_cache_path
    _feed_cache_path = path
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    _feed_cache = data
        except Exception as e:
            print(f"  Warning: could not read feed cache: {e}", file=sys.stderr)


def _save_feed_cache():
    """Write the feed cache back to disk if dirty."""
    global _feed_cache_dirty
    if _feed_cache_path and _feed_cache_dirty:
        with open(_feed_cache_path, "w", encoding="utf-8") as f:
            yaml.dump(_feed_cache, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _discover_feed_url(site_url):
    """Discover RSS/Atom feed URL from a webpage's HTML link tags."""
    try:
        req = urllib.request.Request(site_url, headers={"User-Agent": "claude-stalk/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Discovery fetch failed for {site_url}: {e}", file=sys.stderr)
        return None

    # Look for <link rel="alternate" type="application/rss+xml" href="...">
    # or <link rel="alternate" type="application/atom+xml" href="...">
    patterns = [
        r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
        r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/atom\+xml["\']',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            feed_url = m.group(1)
            # Handle relative URLs
            if feed_url.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(site_url)
                feed_url = f"{parsed.scheme}://{parsed.netloc}{feed_url}"
            return feed_url

    return None


def fetch_webpage(source, _max_items):
    """Fetch items from a webpage source via RSS auto-discovery + parse-feed.py."""
    global _feed_cache_dirty

    site_url = source.get("url")
    name = source.get("name", site_url)
    feed_url = source.get("feed_url")  # Explicit feed URL from config

    if not site_url:
        print(f"  SKIP: Webpage source missing 'url': {source}", file=sys.stderr)
        return []

    # Priority: config feed_url > cached feed_url > auto-discover
    if not feed_url:
        with _feed_cache_lock:
            feed_url = _feed_cache.get(site_url)
        if feed_url:
            print(f"  Using cached feed for {name}: {feed_url}", file=sys.stderr)

    if not feed_url:
        print(f"  Discovering feed for {name}...", file=sys.stderr)
        feed_url = _discover_feed_url(site_url)
        if feed_url:
            print(f"  Discovered feed: {feed_url}", file=sys.stderr)
            with _feed_cache_lock:
                _feed_cache[site_url] = feed_url
                _feed_cache_dirty = True
        else:
            print(f"  FAIL: {name} — no RSS/Atom feed found at {site_url}", file=sys.stderr)
            return []

    # Fetch and parse the feed (reuse the RSS fetching logic)
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as tmp:
            tmp_path = tmp.name
            req = urllib.request.Request(feed_url, headers={"User-Agent": "claude-stalk/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                tmp.write(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  FAIL: {name} — feed fetch error: {e}", file=sys.stderr)
        return []

    script = os.path.join(SCRIPTS_DIR, "parse-feed.py")
    try:
        result = run_cmd(
            ["python", script, "--source-name", name, "--file", tmp_path],
            capture_output=True, text=True, timeout=30, env=_SUBPROCESS_ENV,
        )
    finally:
        os.unlink(tmp_path)

    if result.returncode != 0:
        print(f"  FAIL: {name} — parse error: {result.stderr.strip()}", file=sys.stderr)
        return []

    try:
        items = yaml.safe_load(result.stdout)
        if not isinstance(items, list):
            items = []
    except yaml.YAMLError:
        print(f"  FAIL: {name} — invalid YAML from parse-feed.py", file=sys.stderr)
        return []

    # Normalize URLs for dedup
    for item in items:
        if "url" in item:
            item["url"] = normalize_url(item["url"])
        # Set source_type to webpage (parse-feed.py sets it to rss)
        item["source_type"] = "webpage"

    print(f"  OK: {name} — {len(items)} items", file=sys.stderr)
    return items


FETCHERS = {
    "youtube_channel": fetch_youtube,
    "rss": fetch_rss,
    "webpage": fetch_webpage,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build stalk candidates YAML")
    parser.add_argument("--config", required=True, help="Path to session config.yaml")
    parser.add_argument("--output", required=True, help="Path to write candidates YAML")
    parser.add_argument("--max-items", type=int, default=15, help="Max items per source (default: 15)")
    parser.add_argument("--feed-cache", default=None, help="Path to feed-cache.yaml for webpage feed URL caching")
    args = parser.parse_args(argv)

    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading config: {e}", file=sys.stderr)
        return 1

    # Load feed cache for webpage sources
    if args.feed_cache:
        _load_feed_cache(args.feed_cache)

    sources = config.get("sources", [])
    if not sources:
        print("No sources in config", file=sys.stderr)
        return 1

    all_candidates = []
    errors = []

    print(f"Fetching {len(sources)} sources...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futures = {}
        for source in sources:
            src_type = source.get("type", "")
            fetcher = FETCHERS.get(src_type)
            if not fetcher:
                print(f"  SKIP: unknown source type '{src_type}'", file=sys.stderr)
                continue
            future = pool.submit(fetcher, source, args.max_items)
            futures[future] = source.get("name", src_type)

        for future in as_completed(futures):
            name = futures[future]
            try:
                items = future.result()
                all_candidates.extend(items)
            except Exception as e:
                print(f"  FAIL: {name} — {e}", file=sys.stderr)
                errors.append(name)

    # Save feed cache if any webpage sources discovered new feeds
    _save_feed_cache()

    if not all_candidates:
        print("No candidates fetched from any source", file=sys.stderr)
        # Still write empty file so downstream doesn't break
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("[]\n")
        return 2

    with open(args.output, "w", encoding="utf-8") as f:
        yaml.dump(all_candidates, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Fetched {len(all_candidates)} candidates from {len(sources) - len(errors)} sources", file=sys.stderr)
    if errors:
        print(f"Failed sources: {', '.join(errors)}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
