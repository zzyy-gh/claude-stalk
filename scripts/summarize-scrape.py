#!/usr/bin/env python3
"""Summarize scrape.json data for X pipeline skills.

Two modes:
  --stats   Output aggregate counts (totalPosts, totalAccounts, totalImages, totalExternalLinks)
  --links   Output posts with external links, sorted by engagement
"""

import argparse
import json
import re
import sys

import yaml


def load_scrape(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_metric(value):
    """Parse metric string ('1', '1.2K', '3.5M') to int."""
    if not value:
        return 0
    s = str(value).strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([KkMm]?)$", s)
    if not m:
        return 0
    num = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix == "K":
        return int(num * 1000)
    if suffix == "M":
        return int(num * 1000000)
    return int(num)


def engagement_score(metrics):
    """Sum likes + retweets from a metrics dict."""
    return parse_metric(metrics.get("like", 0)) + parse_metric(metrics.get("retweet", 0))


def compute_stats(scrape_data):
    total_posts = 0
    total_accounts = 0
    total_images = 0
    total_external_links = 0

    for handle, posts in scrape_data.items():
        if not posts:
            continue
        total_accounts += 1
        for post in posts:
            total_posts += 1
            imgs = post.get("images")
            if imgs:
                total_images += len(imgs)
            links = post.get("externalLinks")
            if links:
                total_external_links += len(links)

    return {
        "totalPosts": total_posts,
        "totalAccounts": total_accounts,
        "totalImages": total_images,
        "totalExternalLinks": total_external_links,
    }


def extract_links(scrape_data):
    results = []
    for handle, posts in scrape_data.items():
        for post in posts:
            links = post.get("externalLinks")
            if not links:
                continue
            metrics = post.get("metrics", {})
            results.append({
                "handle": handle,
                "postUrl": post.get("url", ""),
                "text": (post.get("text", "") or "")[:60],
                "externalLinks": links,
                "metrics": {
                    "like": parse_metric(metrics.get("like", 0)),
                    "retweet": parse_metric(metrics.get("retweet", 0)),
                },
            })

    results.sort(key=lambda x: engagement_score(x["metrics"]), reverse=True)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarize scrape.json for X pipeline")
    parser.add_argument("--scrape", required=True, help="Path to scrape.json")
    parser.add_argument("--stats", action="store_true", help="Output aggregate counts")
    parser.add_argument("--links", action="store_true", help="Output posts with external links")

    args = parser.parse_args(argv)

    if args.stats and args.links:
        print("Error: provide either --stats or --links, not both", file=sys.stderr)
        return 2
    if not args.stats and not args.links:
        print("Error: provide either --stats or --links", file=sys.stderr)
        return 2

    try:
        scrape_data = load_scrape(args.scrape)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading scrape file: {e}", file=sys.stderr)
        return 2

    if args.stats:
        result = compute_stats(scrape_data)
        yaml.dump(result, sys.stdout, default_flow_style=False, sort_keys=False)
        return 0

    if args.links:
        result = extract_links(scrape_data)
        yaml.dump(result, sys.stdout, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return 0


if __name__ == "__main__":
    sys.exit(main())
