#!/usr/bin/env python3
"""RSS/Atom XML feed parser. Outputs YAML list of feed items to stdout."""

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import yaml


ATOM_NS = "{http://www.w3.org/2005/Atom}"


def normalize_date(date_str):
    """Normalize a date string to ISO 8601 UTC format."""
    if not date_str:
        return None
    date_str = date_str.strip()

    # Try RFC 2822 (common in RSS)
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass

    # Try ISO 8601 variants (common in Atom)
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    return None


def truncate(text, length=200):
    """Truncate text to the given length."""
    if not text:
        return None
    text = text.strip()
    if len(text) <= length:
        return text
    return text[:length]


def text_of(element, tag):
    """Get text content of a child element, or None."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


def parse_rss(root, source_name):
    """Parse RSS feed items from an XML root."""
    items = []
    for item in root.iter("item"):
        entry = {"url": text_of(item, "link"), "title": text_of(item, "title")}
        if not entry["url"] and not entry["title"]:
            continue
        entry["source_name"] = source_name
        entry["source_type"] = "rss"

        pub_date = normalize_date(text_of(item, "pubDate"))
        if pub_date:
            entry["published"] = pub_date

        desc = truncate(text_of(item, "description"))
        if desc:
            entry["description"] = desc

        items.append(entry)
    return items


def parse_atom(root, source_name):
    """Parse Atom feed entries from an XML root."""
    items = []
    for entry_el in root.iter(f"{ATOM_NS}entry"):
        title = text_of(entry_el, f"{ATOM_NS}title")

        link_el = entry_el.find(f"{ATOM_NS}link")
        url = link_el.get("href") if link_el is not None else None

        entry = {"url": url, "title": title}
        if not entry["url"] and not entry["title"]:
            continue
        entry["source_name"] = source_name
        entry["source_type"] = "rss"

        pub_date = normalize_date(text_of(entry_el, f"{ATOM_NS}published"))
        if pub_date:
            entry["published"] = pub_date

        desc = truncate(text_of(entry_el, f"{ATOM_NS}summary"))
        if desc:
            entry["description"] = desc

        items.append(entry)
    return items


def parse_feed(xml_content, source_name):
    """Parse an RSS or Atom feed from XML string. Returns list of dicts."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"XML parse error: {e}")

    # Detect feed type
    if root.find("channel") is not None:
        return parse_rss(root, source_name)
    if root.tag == f"{ATOM_NS}feed" or root.tag == "feed":
        return parse_atom(root, source_name)

    # Check for RSS items at root level (rare but possible)
    if root.tag == "rss":
        return parse_rss(root, source_name)

    raise ValueError("Unrecognized feed format (not RSS or Atom)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Parse RSS/Atom XML feed")
    parser.add_argument("--source-name", required=True, help="Name of the source")
    parser.add_argument("--file", default=None, help="Path to XML file (reads stdin if omitted)")
    args = parser.parse_args(argv)

    try:
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                xml_content = f.read()
        else:
            xml_content = sys.stdin.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 2

    try:
        items = parse_feed(xml_content, args.source_name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    print(yaml.dump(items, default_flow_style=False, allow_unicode=True, sort_keys=False), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
