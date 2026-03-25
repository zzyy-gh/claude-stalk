#!/usr/bin/env python3
"""Build stalk candidates YAML from configured sources.

Reads a session config.yaml, fetches all sources in parallel
(YouTube via stalk-youtube.sh, RSS via parse-feed.py), and writes
the combined candidates YAML file.

Usage:
    python build-candidates.py --config PATH --output PATH [--max-items N]

Exit codes: 0 = success, 1 = bad args, 2 = no sources fetched
"""

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WINDOWS = sys.platform == "win32"


def run_cmd(cmd_list, **kwargs):
    """Run a command, using shell=True on Windows for path compatibility."""
    if IS_WINDOWS:
        cmd_str = " ".join(shlex.quote(str(c)) for c in cmd_list)
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
            capture_output=True, text=True, timeout=30,
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


FETCHERS = {
    "youtube_channel": fetch_youtube,
    "rss": fetch_rss,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build stalk candidates YAML")
    parser.add_argument("--config", required=True, help="Path to session config.yaml")
    parser.add_argument("--output", required=True, help="Path to write candidates YAML")
    parser.add_argument("--max-items", type=int, default=15, help="Max items per source (default: 15)")
    args = parser.parse_args(argv)

    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading config: {e}", file=sys.stderr)
        return 1

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
