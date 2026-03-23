#!/usr/bin/env python3
"""Tests for verify-x-urls.py"""

import sys
import os
import json
import tempfile
import importlib.util

# Import verify-x-urls.py (hyphenated filename)
spec = importlib.util.spec_from_file_location(
    "verify_x_urls",
    os.path.join(os.path.dirname(__file__), "..", "verify-x-urls.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

build_map = mod.build_map
verify_digest = mod.verify_digest
main = mod.main

SAMPLE_SCRAPE = {
    "alice": [
        {
            "text": "This is a post about AI and the future of large language models in production",
            "time": "2026-03-10T14:00:00Z",
            "url": "https://x.com/alice/status/1001",
            "displayName": "Alice",
            "externalLinks": [],
            "images": [],
            "metrics": {},
        },
        {
            "text": "Another thought on venture capital trends this quarter",
            "time": "2026-03-10T15:00:00Z",
            "url": "https://x.com/alice/status/1002",
            "displayName": "Alice",
            "externalLinks": [],
            "images": [],
            "metrics": {},
        },
    ],
    "bob": [
        {
            "text": "Short post",
            "time": "2026-03-10T16:00:00Z",
            "url": "https://x.com/bob/status/2001",
            "displayName": "Bob",
            "externalLinks": [],
            "images": [],
            "metrics": {},
        },
    ],
}


def _write_scrape(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _write_digest(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_build_map():
    """Build map from sample scrape data produces correct text prefixes and URLs."""
    result = build_map(SAMPLE_SCRAPE)

    assert "alice" in result
    assert "bob" in result
    assert len(result["alice"]) == 2
    assert len(result["bob"]) == 1

    assert result["alice"][0]["url"] == "https://x.com/alice/status/1001"
    assert result["alice"][0]["text_prefix"] == SAMPLE_SCRAPE["alice"][0]["text"][:60]
    assert result["bob"][0]["text_prefix"] == "Short post"
    print("PASS: test_build_map")


def test_verify_all_present():
    """Verify mode: all URLs present in scrape -> exit 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        digest_path = os.path.join(tmpdir, "digest.md")

        _write_scrape(scrape_path, SAMPLE_SCRAPE)
        _write_digest(digest_path, (
            "# Digest\n"
            "\n"
            "Alice posted about AI: https://x.com/alice/status/1001\n"
            "And VC trends: https://x.com/alice/status/1002\n"
            "Bob said: https://x.com/bob/status/2001\n"
        ))

        exit_code = main(["--scrape", scrape_path, "--digest", digest_path])

        assert exit_code == 0, f"Expected exit 0, got {exit_code}"
    print("PASS: test_verify_all_present")


def test_verify_missing_urls():
    """Verify mode: some URLs missing from scrape -> exit 1 with correct details."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        digest_path = os.path.join(tmpdir, "digest.md")

        _write_scrape(scrape_path, SAMPLE_SCRAPE)
        _write_digest(digest_path, (
            "# Digest\n"
            "\n"
            "Known post: https://x.com/alice/status/1001\n"
            "Unknown post: https://x.com/charlie/status/9999\n"
            "Another unknown: https://x.com/dave/status/8888\n"
        ))

        exit_code = main(["--scrape", scrape_path, "--digest", digest_path])

        assert exit_code == 1, f"Expected exit 1, got {exit_code}"

        report = verify_digest(digest_path, SAMPLE_SCRAPE)
        assert report["total_urls"] == 3
        assert report["verified"] == 1
        assert report["missing"] == 2
        assert len(report["missing_details"]) == 2

        missing_urls = {d["url"] for d in report["missing_details"]}
        assert "https://x.com/charlie/status/9999" in missing_urls
        assert "https://x.com/dave/status/8888" in missing_urls

        # Check line numbers
        for detail in report["missing_details"]:
            assert "line" in detail
            assert "context" in detail
            assert detail["line"] >= 1
    print("PASS: test_verify_missing_urls")


def test_digest_no_urls():
    """Digest with no x.com URLs -> exit 0, total_urls: 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        digest_path = os.path.join(tmpdir, "digest.md")

        _write_scrape(scrape_path, SAMPLE_SCRAPE)
        _write_digest(digest_path, (
            "# Digest\n"
            "\n"
            "No links in this digest at all.\n"
            "Just plain text summary.\n"
        ))

        exit_code = main(["--scrape", scrape_path, "--digest", digest_path])
        assert exit_code == 0, f"Expected exit 0, got {exit_code}"

        report = verify_digest(digest_path, SAMPLE_SCRAPE)
        assert report["total_urls"] == 0
        assert report["verified"] == 0
        assert report["missing"] == 0
    print("PASS: test_digest_no_urls")


def test_empty_scrape():
    """Empty scrape file (no handles) -> build-map returns empty, verify flags all as missing."""
    empty_scrape = {}

    # Build map
    result = build_map(empty_scrape)
    assert result == {}

    # Verify with a digest that has URLs
    with tempfile.TemporaryDirectory() as tmpdir:
        scrape_path = os.path.join(tmpdir, "scrape.json")
        digest_path = os.path.join(tmpdir, "digest.md")

        _write_scrape(scrape_path, empty_scrape)
        _write_digest(digest_path, (
            "# Digest\n"
            "Post: https://x.com/someone/status/123\n"
        ))

        exit_code = main(["--scrape", scrape_path, "--digest", digest_path])
        assert exit_code == 1, f"Expected exit 1 with empty scrape, got {exit_code}"

        report = verify_digest(digest_path, empty_scrape)
        assert report["total_urls"] == 1
        assert report["verified"] == 0
        assert report["missing"] == 1
    print("PASS: test_empty_scrape")


if __name__ == "__main__":
    test_build_map()
    test_verify_all_present()
    test_verify_missing_urls()
    test_digest_no_urls()
    test_empty_scrape()
    print("\nAll tests passed!")
