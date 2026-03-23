#!/usr/bin/env python3
"""Tests for parse-feed.py"""

import importlib.util
import os
import unittest

spec = importlib.util.spec_from_file_location(
    "parse_feed",
    os.path.join(os.path.dirname(__file__), "..", "parse-feed.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

parse_feed = mod.parse_feed
normalize_date = mod.normalize_date


class TestRSSFeedAllFields(unittest.TestCase):
    """1. RSS feed with all fields."""

    def test_rss_full(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Test Blog</title>
            <item>
              <title>First Post</title>
              <link>https://example.com/first</link>
              <pubDate>Mon, 10 Mar 2026 14:00:00 +0000</pubDate>
              <description>This is the first post description.</description>
            </item>
            <item>
              <title>Second Post</title>
              <link>https://example.com/second</link>
              <pubDate>Tue, 11 Mar 2026 09:30:00 +0000</pubDate>
              <description>This is the second post.</description>
            </item>
          </channel>
        </rss>"""
        items = parse_feed(xml, "Test Blog")
        self.assertEqual(len(items), 2)

        self.assertEqual(items[0]["url"], "https://example.com/first")
        self.assertEqual(items[0]["title"], "First Post")
        self.assertEqual(items[0]["source_name"], "Test Blog")
        self.assertEqual(items[0]["source_type"], "rss")
        self.assertEqual(items[0]["published"], "2026-03-10T14:00:00Z")
        self.assertEqual(items[0]["description"], "This is the first post description.")

        self.assertEqual(items[1]["title"], "Second Post")
        self.assertEqual(items[1]["published"], "2026-03-11T09:30:00Z")


class TestAtomFeedWithNamespace(unittest.TestCase):
    """2. Atom feed with namespace."""

    def test_atom_ns(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Atom Blog</title>
          <entry>
            <title>Atom Entry</title>
            <link href="https://example.com/atom-entry"/>
            <published>2026-03-15T10:00:00Z</published>
            <summary>Summary of the atom entry.</summary>
          </entry>
        </feed>"""
        items = parse_feed(xml, "Atom Source")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.com/atom-entry")
        self.assertEqual(items[0]["title"], "Atom Entry")
        self.assertEqual(items[0]["source_name"], "Atom Source")
        self.assertEqual(items[0]["source_type"], "rss")
        self.assertEqual(items[0]["published"], "2026-03-15T10:00:00Z")
        self.assertEqual(items[0]["description"], "Summary of the atom entry.")


class TestMissingOptionalFields(unittest.TestCase):
    """3. Missing optional fields (no pubDate, no description)."""

    def test_rss_missing_optional(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Sparse Blog</title>
            <item>
              <title>Bare Post</title>
              <link>https://example.com/bare</link>
            </item>
          </channel>
        </rss>"""
        items = parse_feed(xml, "Sparse Blog")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.com/bare")
        self.assertEqual(items[0]["title"], "Bare Post")
        self.assertNotIn("published", items[0])
        self.assertNotIn("description", items[0])

    def test_atom_missing_optional(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Sparse Atom</title>
          <entry>
            <title>Bare Atom Entry</title>
            <link href="https://example.com/bare-atom"/>
          </entry>
        </feed>"""
        items = parse_feed(xml, "Sparse Atom")
        self.assertEqual(len(items), 1)
        self.assertNotIn("published", items[0])
        self.assertNotIn("description", items[0])


class TestEmptyFeed(unittest.TestCase):
    """4. Empty feed (zero items)."""

    def test_empty_rss(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Empty Blog</title>
          </channel>
        </rss>"""
        items = parse_feed(xml, "Empty Blog")
        self.assertEqual(items, [])

    def test_empty_atom(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Empty Atom</title>
        </feed>"""
        items = parse_feed(xml, "Empty Atom")
        self.assertEqual(items, [])


class TestDateNormalization(unittest.TestCase):
    """5. Date normalization (RFC 2822 -> ISO 8601)."""

    def test_rfc2822_utc(self):
        self.assertEqual(
            normalize_date("Mon, 10 Mar 2026 14:00:00 +0000"),
            "2026-03-10T14:00:00Z",
        )

    def test_rfc2822_offset(self):
        self.assertEqual(
            normalize_date("Mon, 10 Mar 2026 10:00:00 -0400"),
            "2026-03-10T14:00:00Z",
        )

    def test_iso8601_zulu(self):
        self.assertEqual(
            normalize_date("2026-03-10T14:00:00Z"),
            "2026-03-10T14:00:00Z",
        )

    def test_iso8601_offset(self):
        self.assertEqual(
            normalize_date("2026-03-10T10:00:00-04:00"),
            "2026-03-10T14:00:00Z",
        )

    def test_none_input(self):
        self.assertIsNone(normalize_date(None))

    def test_empty_string(self):
        self.assertIsNone(normalize_date(""))


class TestDescriptionTruncation(unittest.TestCase):
    """Verify descriptions are truncated to 200 characters."""

    def test_long_description(self):
        long_desc = "A" * 300
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Blog</title>
            <item>
              <title>Post</title>
              <link>https://example.com/post</link>
              <description>{long_desc}</description>
            </item>
          </channel>
        </rss>"""
        items = parse_feed(xml, "Blog")
        self.assertEqual(len(items[0]["description"]), 200)


if __name__ == "__main__":
    unittest.main()
