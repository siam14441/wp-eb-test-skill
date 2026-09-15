#!/usr/bin/env python3
"""
Find "feature" doc pages -- /docs/ pages on the live site that AREN'T any
block's demo/doc URL. blocks.php's list only covers the 79 Gutenberg blocks;
the site also documents plugin-wide features (AI image generation, ACF
support, dynamic tags, license activation, Templately import if it existed,
etc.) that deserve the same video-coverage scrutiny but were entirely outside
scope before this. Confirmed value (2026-08-25): the artifact this compares
against flagged "no video for Generate AI Images" and "no tutorial for
Templately import" -- both are feature pages, not blocks, so a block-only
audit structurally cannot see them.

Deliberately excludes pages that are clearly internal/setup-only rather than
feature tutorials (activate-license-key, verify-*-license-key, requirements,
regenerate-assets, slow-down-site, themes-supported-by-*) -- those aren't the
kind of content a marketing video would ever cover, so flagging "no video"
on them would be noise, not signal.

Usage:
    list_feature_docs.py <blocks.json> <sitemap_urls.txt>
Output (tsv): slug  derived_label  url
"""
import json
import re
import sys

SETUP_ONLY_SLUGS = {
    "activate-license-key", "verify-essential-blocks-pro-license-key",
    "requirements", "regenerate-assets", "slow-down-site",
    "themes-supported-by-esssential-blocks", "purchase-essential-blocks-pro-version",
    "install-activate-essential-blocks-pro", "new-block-editors-essential-blocks",
    "essential-blocks-free-or-pro", "essential-blocks-quick-action-toolbar",
    "how-to-install-essential-blocks",
}


def derive_label(slug):
    words = re.sub(r"^eb-", "", slug).replace("-", " ").split()
    return " ".join(w.upper() if w.lower() in ("ai", "acf", "api", "toc", "seo") else w.capitalize()
                     for w in words)


STOPWORDS = {"eb", "block", "blocks", "the", "for", "in", "with", "and", "of", "to",
             "how", "add", "create", "gutenberg", "wordpress", "on", "your", "a"}


def tokens(s):
    words = re.split(r"[-_/\s]+", s.lower())
    return {w for w in words if w and w not in STOPWORDS and len(w) >= 3}


def main():
    if len(sys.argv) != 3:
        print("usage: list_feature_docs.py <blocks.json> <sitemap_urls.txt>", file=sys.stderr)
        sys.exit(1)

    blocks = json.load(open(sys.argv[1], encoding="utf-8"))
    known_doc_paths = set()
    block_token_sets = []
    for b in blocks:
        if b.get("doc_path"):
            known_doc_paths.add(b["doc_path"].rstrip("/"))
        block_token_sets.append(tokens(b.get("label", "")) | tokens(b["key"]))

    site_urls = [u.strip() for u in open(sys.argv[2], encoding="utf-8") if u.strip()]
    seen_slugs = set()
    out = []
    for url in site_urls:
        if "/docs/" not in url or "/docs-" in url:
            continue
        path = url.split("essential-blocks.com/", 1)[-1].rstrip("/")
        if path in known_doc_paths:
            continue
        slug = path.rsplit("/", 1)[-1]
        if slug in SETUP_ONLY_SLUGS or slug in seen_slugs:
            continue
        # Skip pages that are almost certainly a block's real page reached via
        # a different (often redirecting) URL than blocks.php stores -- e.g.
        # blocks.php points image_gallery's doc at "eb-filterable-gallery/"
        # but the site's actual canonical URL is "eb-image-gallery"; without
        # this check that shows up as a fake "new feature," double-counting a
        # block that's already covered under Part 1/1b.
        slug_tokens = tokens(slug)
        if any(len(slug_tokens & bt) >= 2 for bt in block_token_sets):
            continue
        seen_slugs.add(slug)
        out.append(f"{slug}\t{derive_label(slug)}\t{url.rstrip('/')}")

    print("\n".join(sorted(out)))


if __name__ == "__main__":
    main()
