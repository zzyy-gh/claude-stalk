#!/usr/bin/env python3
"""X post URL verifier for digests.

Two modes:
  --build-map   Parse scrape.json and output a YAML lookup map (handle -> [{text_prefix, url}])
  --digest FILE  Verify all x.com status URLs in a digest markdown against scrape.json
"""

import argparse
import json
import re
import sys

import yaml


URL_PATTERN = re.compile(r"https?://x\.com/[^/\s\)]+/status/\d+")


def load_scrape(path):
    """Load scrape.json and return the parsed dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_map(scrape_data):
    """Build a handle -> [{text_prefix, url}] lookup from scrape data."""
    result = {}
    for handle, posts in scrape_data.items():
        entries = []
        for post in posts:
            text = post.get("text", "")
            entries.append({
                "text_prefix": text[:60],
                "url": post.get("url", ""),
            })
        if entries:
            result[handle] = entries
    return result


def collect_scrape_urls(scrape_data):
    """Collect all post URLs from scrape data into a flat set."""
    urls = set()
    for posts in scrape_data.values():
        for post in posts:
            url = post.get("url", "")
            if url:
                urls.add(url)
    return urls


def verify_digest(digest_path, scrape_data):
    """Verify all x.com status URLs in a digest against scrape data.

    Returns a dict with total_urls, verified, missing, and missing_details.
    """
    known_urls = collect_scrape_urls(scrape_data)

    with open(digest_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found_urls = []  # (url, line_number, line_text)
    for i, line in enumerate(lines, start=1):
        for match in URL_PATTERN.finditer(line):
            found_urls.append((match.group(0), i, line))

    missing_details = []
    verified_count = 0

    for url, line_num, line_text in found_urls:
        if url in known_urls:
            verified_count += 1
        else:
            # Extract ~40 chars of surrounding context
            idx = line_text.find(url)
            start = max(0, idx - 20)
            end = min(len(line_text), idx + len(url) + 20)
            context = line_text[start:end].strip()
            missing_details.append({
                "url": url,
                "line": line_num,
                "context": context,
            })

    return {
        "total_urls": len(found_urls),
        "verified": verified_count,
        "missing": len(missing_details),
        "missing_details": missing_details,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="X post URL verifier for digests")
    parser.add_argument("--scrape", required=True, help="Path to scrape.json")
    parser.add_argument("--build-map", action="store_true", help="Build lookup map from scrape data")
    parser.add_argument("--digest", help="Path to digest markdown to verify")

    args = parser.parse_args(argv)

    # Validate: exactly one of --build-map or --digest
    if args.build_map and args.digest:
        print("Error: provide either --build-map or --digest, not both", file=sys.stderr)
        return 2
    if not args.build_map and not args.digest:
        print("Error: provide either --build-map or --digest", file=sys.stderr)
        return 2

    try:
        scrape_data = load_scrape(args.scrape)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading scrape file: {e}", file=sys.stderr)
        return 2

    if args.build_map:
        result = build_map(scrape_data)
        yaml.dump(result, sys.stdout, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return 0

    # Verify mode
    try:
        report = verify_digest(args.digest, scrape_data)
    except FileNotFoundError as e:
        print(f"Error loading digest file: {e}", file=sys.stderr)
        return 2

    yaml.dump(report, sys.stdout, default_flow_style=False, allow_unicode=True, sort_keys=False)

    if report["missing"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
