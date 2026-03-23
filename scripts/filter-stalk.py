#!/usr/bin/env python3
"""Filter stalk candidates against history using datetime-aware logic.

Usage:
    python filter-stalk.py --history PATH --candidates PATH --now TIMESTAMP

Reads candidates (fetched items) and stalk history, outputs YAML with:
  - new_items: candidates that passed filtering (excludes seeds)
  - history_additions: all items to append to stalk-history.yaml (includes seeds)
  - seed_reports: human-readable seed messages (empty list if none)

Exit codes: 0 = success, 1 = bad args, 2 = file error
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone

import yaml


SEED_LIMIT = 5


def parse_dt(s):
    """Parse an ISO 8601 datetime string to a timezone-aware datetime."""
    if not s:
        return None
    s = str(s).strip()
    # Handle YYYYMMDD format from yt-dlp
    if len(s) == 8 and s.isdigit():
        s = f"{s[:4]}-{s[4:6]}-{s[6:8]}T00:00:00Z"
    # Ensure timezone
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    elif "+" not in s and s.count("-") <= 2:
        s += "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def load_yaml(path):
    """Load a YAML file, returning an empty list if missing or empty."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []


def build_watermarks(history):
    """Build per-source watermark (max published) and a set of all URLs."""
    watermarks = {}
    urls = set()
    for entry in history:
        url = entry.get("url")
        if url:
            urls.add(url)
        source = entry.get("source_name")
        pub = parse_dt(entry.get("published"))
        if source and pub:
            if source not in watermarks or pub > watermarks[source]:
                watermarks[source] = pub
    return watermarks, urls


def sources_in_history(history):
    """Return set of source_names that have at least one history entry."""
    return {e.get("source_name") for e in history if e.get("source_name")}


def filter_candidates(history, candidates, now_str):
    """Core filtering logic. Returns (new_items, history_additions, seed_reports)."""
    watermarks, seen_urls = build_watermarks(history)
    known_sources = sources_in_history(history)

    # Group candidates by source_name
    by_source = defaultdict(list)
    for item in candidates:
        by_source[item.get("source_name", "unknown")].append(item)

    new_items = []
    history_additions = []
    seed_reports = []

    for source_name, items in by_source.items():
        # Seed mode: source has no history entries
        if source_name not in known_sources:
            # Sort by published (newest first), take top SEED_LIMIT
            dated = [(item, parse_dt(item.get("published"))) for item in items]
            dated.sort(key=lambda x: x[1] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            seed_items = dated[:SEED_LIMIT]

            latest_dt = None
            for item, dt in seed_items:
                entry = {
                    "url": item["url"],
                    "title": item.get("title", ""),
                    "source_name": source_name,
                    "source_type": item.get("source_type", ""),
                    "first_seen": now_str,
                }
                if item.get("published"):
                    entry["published"] = item["published"]
                if dt and (latest_dt is None or dt > latest_dt):
                    latest_dt = dt
                history_additions.append(entry)

            latest_str = latest_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if latest_dt else "unknown"
            seed_reports.append(
                f"Seed: {source_name} -- recorded {len(seed_items)} items, latest: {latest_str}"
            )
            continue

        # Normal filtering
        watermark = watermarks.get(source_name)

        for item in items:
            url = item.get("url")

            # URL safety net: skip anything already in history
            if url in seen_urls:
                continue

            pub = parse_dt(item.get("published"))

            if watermark and pub:
                # Datetime-aware: only items newer than watermark
                if pub <= watermark:
                    continue
            elif watermark and not pub:
                # Have watermark but candidate has no date: fall through to URL dedup
                # (already passed URL check above)
                pass
            # No watermark but source is known (all history entries lacked dates):
            # URL dedup only -- already handled above

            entry = {
                "url": url,
                "title": item.get("title", ""),
                "source_name": source_name,
                "source_type": item.get("source_type", ""),
                "first_seen": now_str,
            }
            if item.get("published"):
                entry["published"] = item["published"]

            new_items.append(entry)
            history_additions.append(dict(entry))
            seen_urls.add(url)  # prevent duplicates within this run

    return new_items, history_additions, seed_reports


def main():
    parser = argparse.ArgumentParser(description="Filter stalk candidates against history")
    parser.add_argument("--history", required=True, help="Path to stalk-history.yaml")
    parser.add_argument("--candidates", required=True, help="Path to candidates YAML file")
    parser.add_argument("--now", required=True, help="Current ISO 8601 timestamp for first_seen")
    args = parser.parse_args()

    history = load_yaml(args.history)
    candidates = load_yaml(args.candidates)

    if not candidates:
        yaml.dump({"new_items": [], "history_additions": [], "seed_reports": []}, sys.stdout,
                  default_flow_style=False, sort_keys=False)
        return

    new_items, history_additions, seed_reports = filter_candidates(history, candidates, args.now)

    output = {
        "new_items": new_items,
        "history_additions": history_additions,
        "seed_reports": seed_reports,
    }
    yaml.dump(output, sys.stdout, default_flow_style=False, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    main()
