#!/usr/bin/env python3
"""Tests for normalize_url.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from normalize_url import normalize_url


def test_strip_utm_params():
    assert normalize_url("https://example.com/post?utm_source=rss&utm_medium=feed") == "https://example.com/post"


def test_strip_fbclid():
    assert normalize_url("https://example.com/post?fbclid=abc123") == "https://example.com/post"


def test_strip_gclid():
    assert normalize_url("https://example.com/post?gclid=xyz") == "https://example.com/post"


def test_preserve_non_tracking_params():
    assert normalize_url("https://example.com/post?id=123&page=2") == "https://example.com/post?id=123&page=2"


def test_mixed_tracking_and_real_params():
    result = normalize_url("https://example.com/post?id=456&utm_source=rss&page=1")
    assert "id=456" in result
    assert "page=1" in result
    assert "utm_source" not in result


def test_strip_www():
    assert normalize_url("https://www.example.com/post") == "https://example.com/post"


def test_force_https():
    assert normalize_url("http://example.com/post") == "https://example.com/post"


def test_normalize_trailing_slash():
    assert normalize_url("https://example.com/post/") == "https://example.com/post"


def test_preserve_root_trailing_slash():
    assert normalize_url("https://example.com/") == "https://example.com/"


def test_strip_fragment():
    assert normalize_url("https://example.com/post#section") == "https://example.com/post"


def test_lowercase_host():
    assert normalize_url("https://EXAMPLE.COM/Post") == "https://example.com/Post"


def test_sort_query_params():
    result = normalize_url("https://example.com/post?z=1&a=2")
    assert result == "https://example.com/post?a=2&z=1"


def test_empty_url():
    assert normalize_url("") == ""
    assert normalize_url(None) is None


def test_combined_normalization():
    url = "http://www.EXAMPLE.com/blog/post/?utm_source=newsletter&id=42&fbclid=abc#top"
    assert normalize_url(url) == "https://example.com/blog/post?id=42"


def test_all_params_stripped():
    url = "https://example.com/post?utm_source=x&utm_medium=y&utm_campaign=z&fbclid=a&gclid=b&msclkid=c"
    assert normalize_url(url) == "https://example.com/post"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
