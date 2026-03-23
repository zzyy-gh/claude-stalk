#!/usr/bin/env python3
"""Tests for filter-stalk.py"""

import sys
import os
import importlib.util

# Import filter-stalk.py (hyphenated filename)
spec = importlib.util.spec_from_file_location(
    "filter_stalk",
    os.path.join(os.path.dirname(__file__), "..", "filter-stalk.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
filter_candidates = mod.filter_candidates
parse_dt = mod.parse_dt

NOW = "2026-03-23T12:00:00Z"


def test_seed_mode():
    """Source with no history -> seed mode, record top 5, zero new items."""
    history = []
    candidates = [
        {"url": f"https://youtube.com/watch?v=vid{i}", "title": f"Video {i}",
         "source_name": "TestChannel", "source_type": "youtube",
         "published": f"2026-03-{20+i:02d}T10:00:00Z"}
        for i in range(7)
    ]

    new_items, additions, reports = filter_candidates(history, candidates, NOW)

    assert len(new_items) == 0, f"Seed mode should return 0 new items, got {len(new_items)}"
    assert len(additions) == 5, f"Seed mode should record 5 items, got {len(additions)}"
    assert len(reports) == 1
    assert "Seed: TestChannel" in reports[0]
    print("PASS: test_seed_mode")


def test_watermark_filtering():
    """Items older than watermark are excluded, newer ones pass."""
    history = [
        {"url": "https://youtube.com/watch?v=old1", "title": "Old 1",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-15T10:00:00Z", "first_seen": "2026-03-15T12:00:00Z"},
    ]
    candidates = [
        {"url": "https://youtube.com/watch?v=older", "title": "Older",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-10T10:00:00Z"},
        {"url": "https://youtube.com/watch?v=same", "title": "Same time",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-15T10:00:00Z"},
        {"url": "https://youtube.com/watch?v=newer", "title": "Newer",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-20T10:00:00Z"},
    ]

    new_items, additions, reports = filter_candidates(history, candidates, NOW)

    assert len(new_items) == 1, f"Expected 1 new item, got {len(new_items)}"
    assert new_items[0]["url"] == "https://youtube.com/watch?v=newer"
    assert len(reports) == 0
    print("PASS: test_watermark_filtering")


def test_url_dedup():
    """Already-seen URLs are skipped even if newer than watermark."""
    history = [
        {"url": "https://youtube.com/watch?v=seen", "title": "Seen",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-10T10:00:00Z", "first_seen": "2026-03-10T12:00:00Z"},
    ]
    candidates = [
        {"url": "https://youtube.com/watch?v=seen", "title": "Seen again",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-20T10:00:00Z"},
        {"url": "https://youtube.com/watch?v=fresh", "title": "Fresh",
         "source_name": "Chan", "source_type": "youtube",
         "published": "2026-03-20T10:00:00Z"},
    ]

    new_items, additions, reports = filter_candidates(history, candidates, NOW)

    assert len(new_items) == 1
    assert new_items[0]["url"] == "https://youtube.com/watch?v=fresh"
    print("PASS: test_url_dedup")


def test_no_dates_fallback():
    """When items have no published dates, filter by URL only."""
    history = [
        {"url": "https://example.com/old", "title": "Old",
         "source_name": "Blog", "source_type": "rss",
         "first_seen": "2026-03-10T12:00:00Z"},
    ]
    candidates = [
        {"url": "https://example.com/old", "title": "Old post",
         "source_name": "Blog", "source_type": "rss"},
        {"url": "https://example.com/new", "title": "New post",
         "source_name": "Blog", "source_type": "rss"},
    ]

    new_items, additions, reports = filter_candidates(history, candidates, NOW)

    assert len(new_items) == 1
    assert new_items[0]["url"] == "https://example.com/new"
    print("PASS: test_no_dates_fallback")


def test_mixed_sources():
    """Multiple sources: one in seed mode, one normal."""
    history = [
        {"url": "https://youtube.com/watch?v=a", "title": "A",
         "source_name": "Known", "source_type": "youtube",
         "published": "2026-03-10T10:00:00Z", "first_seen": "2026-03-10T12:00:00Z"},
    ]
    candidates = [
        # Known source - newer item
        {"url": "https://youtube.com/watch?v=b", "title": "B",
         "source_name": "Known", "source_type": "youtube",
         "published": "2026-03-20T10:00:00Z"},
        # New source - should seed
        {"url": "https://youtube.com/watch?v=x", "title": "X",
         "source_name": "NewChan", "source_type": "youtube",
         "published": "2026-03-20T10:00:00Z"},
    ]

    new_items, additions, reports = filter_candidates(history, candidates, NOW)

    assert len(new_items) == 1, f"Expected 1 new (from Known), got {len(new_items)}"
    assert new_items[0]["source_name"] == "Known"
    assert len(reports) == 1
    assert "Seed: NewChan" in reports[0]
    print("PASS: test_mixed_sources")


if __name__ == "__main__":
    test_seed_mode()
    test_watermark_filtering()
    test_url_dedup()
    test_no_dates_fallback()
    test_mixed_sources()
    print("\nAll tests passed!")
