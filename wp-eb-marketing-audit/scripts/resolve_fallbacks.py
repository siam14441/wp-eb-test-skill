#!/usr/bin/env python3
"""
For every broken block demo/doc link, search the site's own URL list (from
`firecrawl map`) for the real page -- blocks.php's hardcoded URLs go stale
(e.g. it points doc="docs/facebook-feed/" but the live page is actually at
docs/eb-facebook-feed). Without this, a stale link masks whatever real
content/video-coverage problem the live page has, because the checker never
reaches it. Verified case (2026-08-23): facebook_feed's doc link 404s, so the
video-coverage check never ran against the real eb-facebook-feed page, which
in fact has zero embedded video -- a genuine gap invisible to the plain
link-check alone.

Matching is a simple token-overlap score between the block's label and each
candidate URL's slug, restricted to the same URL kind (doc candidates only
from /docs/, demo candidates only from /demo/). Not perfect, but every match
is re-verified by an independent live check afterward (Phase 2b) -- a wrong
guess just means "no fallback found," not a false claim of resolution.

Usage:
    resolve_fallbacks.py <blocks.json> <block_check.tsv> <sitemap_urls.txt>
Output (tsv, one row per broken link WITH a candidate found):
    key  kind  original_url  fallback_url  score
"""
import json
import re
import sys


STOPWORDS = {"eb", "block", "blocks", "the", "for", "in", "with", "and", "of", "to",
             "how", "add", "create", "gutenberg", "wordpress", "on", "your", "a"}


def tokens(s):
    words = re.split(r"[-_/\s]+", s.lower())
    return {w for w in words if w and w not in STOPWORDS and len(w) >= 3}


def main():
    if len(sys.argv) != 4:
        print("usage: resolve_fallbacks.py <blocks.json> <block_check.tsv> <sitemap_urls.txt>",
              file=sys.stderr)
        sys.exit(1)

    blocks = {b["key"]: b for b in json.load(open(sys.argv[1], encoding="utf-8"))}

    broken = []  # (key, kind, url)
    with open(sys.argv[2], encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            key, kind, url, code, looks404 = parts[0], parts[1], parts[2], parts[3], parts[4]
            if code != "200" or looks404 == "yes":
                broken.append((key, kind, url))

    site_urls = [u.strip() for u in open(sys.argv[3], encoding="utf-8") if u.strip()]
    docs_urls = [u for u in site_urls if "/docs/" in u and "/docs-" not in u]
    demo_urls = [u for u in site_urls if "/demo/" in u]

    out = []
    for key, kind, orig_url in broken:
        label = blocks.get(key, {}).get("label", key)
        label_tokens = tokens(label) | tokens(key)
        candidates = docs_urls if kind == "doc" else demo_urls if kind == "demo" else []
        best_url, best_score = None, 0
        for cand in candidates:
            if cand == orig_url:
                continue
            slug = cand.rstrip("/").rsplit("/", 1)[-1]
            score = len(label_tokens & tokens(slug))
            if score > best_score:
                best_url, best_score = cand, score
        # Require 2+ shared tokens. Tested against the 6 known-broken links
        # (2026-08-23): score-2 matches (facebook_feed->eb-facebook-feed,
        # advanced_heading->eb-advanced-heading) were both correct; score-1
        # matches were wrong 2 of 3 times (e.g. image_hotspots incorrectly
        # matched to "image-masking-and-morphing" on the shared word "image"
        # alone). A missed-but-correct fallback just reports "still broken" --
        # honest. A wrong fallback reported as "found" would be actively
        # misleading, so the bar favors precision over recall here.
        if best_url and best_score >= 2:
            out.append(f"{key}\t{kind}\t{orig_url}\t{best_url}\t{best_score}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
