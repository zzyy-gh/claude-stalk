#!/usr/bin/env python3
"""Tests for summarize-scrape.py"""

import sys
import os
import json
import tempfile
import importlib.util

# Import summarize-scrape.py (hyphenated filename)
spec = importlib.util.spec_from_file_location(
    "summarize_scrape",
    os.path.join(os.path.dirname(__file__), "..", "summarize-scrape.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

parse_metric = mod.parse_metric
compute_stats = mod.compute_stats
extract_links = mod.extract_links
main = mod.main

SAMPLE_SCRAPE = {
    "alice": [
        {
            "text": "Post about AI models with an image attached for context",
            "time": "2026-03-10T14:00:00Z",
            "url": "https://x.com/alice/status/1001",
            "displayName": "Alice",
            "externalLinks": [{"url": "https://example.com/article", "text": "Article"}],
            "images": ["img1.jpg"],
            "metrics": {"reply": "2", "retweet": "10", "like": "50"},
        },
        {
            "text": "Another post with no links or images",
            "time": "2026-03-10T15:00:00Z",
            "url": "https://x.com/alice/status/1002",
            "displayName": "Alice",
            "externalLinks": [],
            "images": [],
            "metrics": {"reply": "0", "retweet": "1", "like": "5"},
        },
    ],
    "bob": [
        {
            "text": "Bob's post with two images and a link to a blog post",
            "time": "2026-03-10T16:00:00Z",
            "url": "https://x.com/bob/status/2001",
            "displayName": "Bob",
            "externalLinks": [{"url": "https://blog.example.com", "text": "Blog"}],
            "images": ["img2.jpg", "img3.jpg"],
            "metrics": {"reply": "1", "retweet": "3", "like": "1.2K"},
        },
    ],
    "charlie": [
        {
            "text": "No links no images just text",
            "time": "2026-03-10T17:00:00Z",
            "url": "https://x.com/charlie/status/3001",
            "displayName": "Charlie",
            "externalLinks": [],
            "images": [],
            "metrics": {"reply": "0", "retweet": "0", "like": "2"},
        },
    ],
}


def _write_scrape(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_parse_metric():
    """Parse metric strings to integers."""
    assert parse_metric("0") == 0
    assert parse_metric("42") == 42
    assert parse_metric("1.2K") == 1200
    assert parse_metric("3.5M") == 3500000
    assert parse_metric("1,234") == 1234
    assert parse_metric("") == 0
    assert parse_metric(None) == 0
    assert parse_metric("2k") == 2000
    print("PASS: test_parse_metric")


def test_compute_stats():
    """Compute correct aggregate stats from scrape data."""
    stats = compute_stats(SAMPLE_SCRAPE)

    assert stats["totalPosts"] == 4
    assert stats["totalAccounts"] == 3
    assert stats["totalImages"] == 3  # 1 + 0 + 2 + 0
    assert stats["totalExternalLinks"] == 2  # alice has 1, bob has 1
    print("PASS: test_compute_stats")


def test_compute_stats_empty():
    """Empty scrape returns all zeros."""
    stats = compute_stats({})
    assert stats["totalPosts"] == 0
    assert stats["totalAccounts"] == 0
    assert stats["totalImages"] == 0
    assert stats["totalExternalLinks"] == 0
    print("PASS: test_compute_stats_empty")


def test_extract_links():
    """Extract posts with external links, sorted by engagement."""
    results = extract_links(SAMPLE_SCRAPE)

    assert len(results) == 2  # alice/1001 and bob/2001

    # Bob's post has 1.2K likes = 1200, should be first
    assert results[0]["handle"] == "bob"
    assert results[0]["postUrl"] == "https://x.com/bob/status/2001"
    assert results[0]["metrics"]["like"] == 1200

    # Alice's post has 50 likes, second
    assert results[1]["handle"] == "alice"
    assert results[1]["postUrl"] == "https://x.com/alice/status/1001"
    assert results[1]["metrics"]["like"] == 50

    # Text is truncated to 60 chars
    assert len(results[0]["text"]) <= 60
    assert len(results[1]["text"]) <= 60
    print("PASS: test_extract_links")


def test_extract_links_empty():
    """No posts with links returns empty list."""
    scrape = {"alice": [{"text": "no links", "url": "https://x.com/a/status/1", "externalLinks": [], "images": [], "metrics": {}}]}
    results = extract_links(scrape)
    assert results == []
    print("PASS: test_extract_links_empty")


def test_main_stats():
    """CLI --stats mode outputs correct YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        _write_scrape(scrape_path, SAMPLE_SCRAPE)

        exit_code = main(["--scrape", scrape_path, "--stats"])
        assert exit_code == 0
    print("PASS: test_main_stats")


def test_main_links():
    """CLI --links mode exits 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        _write_scrape(scrape_path, SAMPLE_SCRAPE)

        exit_code = main(["--scrape", scrape_path, "--links"])
        assert exit_code == 0
    print("PASS: test_main_links")


def test_main_no_mode():
    """CLI with no mode flag exits 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        _write_scrape(scrape_path, SAMPLE_SCRAPE)

        exit_code = main(["--scrape", scrape_path])
        assert exit_code == 2
    print("PASS: test_main_no_mode")


def test_main_both_modes():
    """CLI with both mode flags exits 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        _write_scrape(scrape_path, SAMPLE_SCRAPE)

        exit_code = main(["--scrape", scrape_path, "--stats", "--links"])
        assert exit_code == 2
    print("PASS: test_main_both_modes")


if __name__ == "__main__":
    test_parse_metric()
    test_compute_stats()
    test_compute_stats_empty()
    test_extract_links()
    test_extract_links_empty()
    test_main_stats()
    test_main_links()
    test_main_no_mode()
    test_main_both_modes()
    print("\nAll tests passed!")
