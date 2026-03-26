#!/usr/bin/env python3
"""URL normalizer for deduplication.

Strips tracking parameters, normalizes trailing slashes, www prefixes,
and protocol to produce canonical URLs for comparison.

Usage:
    # Normalize a single URL
    python normalize-url.py "https://example.com/post?utm_source=rss"

    # Normalize URLs from stdin (one per line)
    cat urls.txt | python normalize-url.py --stdin

    # Use as a library
    from normalize_url import normalize_url
"""

import argparse
import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Tracking parameters to strip
TRACKING_PARAMS = frozenset({
    # Google Analytics / campaign
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_source_platform",
    # Facebook / Meta
    "fbclid", "fb_action_ids", "fb_action_types", "fb_ref", "fb_source",
    # Google Ads
    "gclid", "gclsrc", "dclid", "gbraid", "wbraid",
    # Microsoft / Bing
    "msclkid",
    # HubSpot
    "hsa_cam", "hsa_grp", "hsa_mt", "hsa_src", "hsa_ad", "hsa_acc",
    "hsa_net", "hsa_ver", "hsa_la", "hsa_ol", "hsa_kw",
    # Mailchimp
    "mc_cid", "mc_eid",
    # Generic tracking
    "ref", "source", "campaign_id", "ad_id",
    # Social sharing
    "s", "t", "share",
})


def normalize_url(url):
    """Normalize a URL for deduplication.

    - Force https
    - Strip www. prefix
    - Remove trailing slash (except root path)
    - Remove tracking query parameters
    - Remove fragment
    - Sort remaining query parameters
    - Lowercase scheme and host
    """
    if not url:
        return url

    parsed = urlparse(url)

    # Force https
    scheme = "https"

    # Lowercase and strip www.
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Normalize path: remove trailing slash (but keep "/" for root)
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Strip tracking params, sort remaining
    params = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {
        k: v for k, v in params.items()
        if k.lower() not in TRACKING_PARAMS
    }
    query = urlencode(sorted(filtered.items()), doseq=True) if filtered else ""

    # Drop fragment
    return urlunparse((scheme, netloc, path, "", query, ""))


def main():
    parser = argparse.ArgumentParser(description="Normalize URLs for deduplication")
    parser.add_argument("url", nargs="?", help="URL to normalize")
    parser.add_argument("--stdin", action="store_true", help="Read URLs from stdin (one per line)")
    args = parser.parse_args()

    if args.stdin:
        for line in sys.stdin:
            url = line.strip()
            if url:
                print(normalize_url(url))
    elif args.url:
        print(normalize_url(args.url))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
