#!/usr/bin/env python3
"""
Assemble the final markdown report from all the check outputs.

Usage:
    generate_report.py --blocks blocks.json --block-check block_check.tsv \
        [--sitemap-check sitemap_check.tsv] \
        [--fallback-list fallbacks.tsv] [--fallback-check fallback_check.tsv] \
        [--feature-list feature_docs.tsv] [--feature-check feature_check.tsv] \
        [--dashboard-check dashboard_check.tsv] \
        > report.md

Input formats:
    blocks.json        from extract_blocks.py
    block_check.tsv     from check_blocks.sh: key kind url http_code looks_404 has_video video_id video_title
    sitemap_check.tsv   from check_sitemap.sh: url http_code looks_404
    fallbacks.tsv        from resolve_fallbacks.py: key kind original_url fallback_url score
    fallback_check.tsv   from check_fallbacks.sh: key kind fallback_url http_code looks_404 has_video video_id video_title
    feature_docs.tsv     from list_feature_docs.py: slug label url
    feature_check.tsv    same shape as block_check.tsv, run over feature_docs.tsv's URLs (slug used as key)
    dashboard_check.tsv  from check_dashboard_welcome.sh: version_check/video rows
"""
import argparse
import json
import sys
from datetime import datetime, timezone


def load_blocks(path):
    return {b["key"]: b for b in json.load(open(path, encoding="utf-8"))}


def load_tsv(path, ncols):
    rows = []
    if not path:
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != ncols:
                continue
            rows.append(parts)
    return rows


def is_broken(http_code, looks_404):
    return http_code != "200" or looks_404 == "yes"


STOPWORDS = {"eb", "block", "blocks", "the", "for", "in", "with", "and", "of", "to",
             "how", "add", "create", "gutenberg", "wordpress", "on", "your", "a"}


def normalize(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def label_matches_title(label, title):
    title_norm = normalize(title)
    title_words = {normalize(w) for w in f" {title.lower()} ".split()}
    all_words = label.replace("-", " ").split()
    content_words = [w for w in all_words if w.lower() not in STOPWORDS]
    if not content_words:
        return True
    if len(all_words) > 1:
        acronym = "".join(w[0] for w in all_words).lower()
        if len(acronym) >= 3 and acronym in title_words:
            return True
    for w in content_words:
        w_norm = normalize(w)
        if len(w_norm) < 3:
            continue
        if len(w_norm) < 6:
            if w_norm in title_words or (w_norm + "s") in title_words:
                return True
        else:
            if w_norm[:6] in title_norm:
                return True
    return False


def video_coverage(rows, labels, shares_parent_doc, kind_filter=None):
    """rows: list of [key, kind, url, code, looks404, has_video, video_id, video_title].
    Returns (no_video: [key], mismatches: [(key, label, video_id, video_title)])."""
    no_video, mismatches = [], []
    for row in rows:
        if len(row) < 8:
            continue
        key, kind, url, code, looks404, has_video, video_id, video_title = row[:8]
        if kind_filter and kind != kind_filter:
            continue
        if is_broken(code, looks404):
            continue
        if has_video == "no":
            no_video.append(key)
        elif has_video == "yes" and key not in shares_parent_doc:
            label = labels.get(key, key)
            if video_title and not label_matches_title(label, video_title):
                mismatches.append((key, label, video_id, video_title))
    return no_video, mismatches


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--blocks", required=True)
    p.add_argument("--block-check", required=True)
    p.add_argument("--sitemap-check")
    p.add_argument("--fallback-list")
    p.add_argument("--fallback-check")
    p.add_argument("--feature-list")
    p.add_argument("--feature-check")
    p.add_argument("--dashboard-check")
    args = p.parse_args()

    blocks = load_blocks(args.blocks)
    labels = {k: b.get("label", k) for k, b in blocks.items()}
    block_rows = load_tsv(args.block_check, 8)
    sitemap_rows = load_tsv(args.sitemap_check, 3)
    fallback_list = load_tsv(args.fallback_list, 5)  # key kind orig fallback score
    fallback_check = load_tsv(args.fallback_check, 8)
    feature_list = load_tsv(args.feature_list, 3)  # slug label url
    feature_check = load_tsv(args.feature_check, 8)
    dashboard_rows = load_tsv(args.dashboard_check, 4)

    feature_labels = {slug: label for slug, label, url in feature_list}

    fallback_by_key_kind = {(r[0], r[1]): r[3] for r in fallback_list}
    fallback_result_by_key_kind = {(r[0], r[1]): r for r in fallback_check}

    broken_block_links = [r for r in block_rows if is_broken(r[3], r[4])]
    # A broken link that got a VERIFIED-LIVE fallback isn't really "still
    # broken" -- the real content exists, just under a different URL than
    # blocks.php stores. Split those out for their own section instead of
    # counting them as unresolved.
    resolved_via_fallback = []
    still_broken = []
    for row in broken_block_links:
        key, kind = row[0], row[1]
        fb_row = fallback_result_by_key_kind.get((key, kind))
        if fb_row and not is_broken(fb_row[3], fb_row[4]):
            resolved_via_fallback.append((row, fb_row))
        else:
            still_broken.append(row)

    block_status = {}  # key -> {"demo": ok, "doc": ok}  (ok = live, incl. via fallback)
    for row in block_rows:
        key, kind, url, code, looks404 = row[0], row[1], row[2], row[3], row[4]
        ok = not is_broken(code, looks404)
        if not ok:
            fb_row = fallback_result_by_key_kind.get((key, kind))
            if fb_row and not is_broken(fb_row[3], fb_row[4]):
                ok = True
        block_status.setdefault(key, {})[kind] = ok

    fully_absent = []
    for key, status in block_status.items():
        if "demo" in status and "doc" in status and not status["demo"] and not status["doc"]:
            fully_absent.append(key)

    # Blocks that share a doc_path with another (non-hidden) block are expected
    # to embed that parent's video (Loop Builder's / Form's hidden children).
    doc_path_owners = {}
    for b in blocks.values():
        if b.get("doc_path"):
            doc_path_owners.setdefault(b["doc_path"], []).append(b)
    shares_parent_doc = set()
    for path, owners in doc_path_owners.items():
        if len(owners) > 1 and any(not o["hidden_subblock"] for o in owners):
            for o in owners:
                if o["hidden_subblock"]:
                    shares_parent_doc.add(o["key"])

    doc_no_video, doc_mismatches = video_coverage(block_rows, labels, shares_parent_doc, "doc")
    demo_no_video, demo_mismatches = video_coverage(block_rows, labels, shares_parent_doc, "demo")
    # Fallback-resolved pages get their OWN video check too -- e.g. Facebook
    # Feed's real page (once reached past the dead blocks.php link) turns out
    # to have zero video, which the primary check could never have found.
    fb_no_video, fb_mismatches = video_coverage(fallback_check, labels, shares_parent_doc)
    feat_no_video, feat_mismatches = video_coverage(feature_check, feature_labels, set())

    total_no_video = len(doc_no_video) + len(demo_no_video) + len(fb_no_video)
    total_mismatches = len(doc_mismatches) + len(demo_mismatches) + len(fb_mismatches)

    dashboard_stale = False
    dashboard_version_row = None
    dashboard_video_rows = []
    for row in dashboard_rows:
        if row[0] == "version_check":
            dashboard_version_row = row
            dashboard_stale = row[3] == "yes"
        elif row[0] == "video":
            dashboard_video_rows.append(row)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    out = []
    out.append("# Essential Blocks -- Marketing Content Audit")
    out.append("")
    out.append(f"**Site:** https://essential-blocks.com/  ")
    out.append(f"**Run:** {now}  ")
    out.append(f"**Blocks checked:** {len(blocks)} (from `essential-blocks/includes/blocks.php`)  ")
    out.append(f"**Block URLs checked:** {len(block_rows)} (demo + doc per block)  ")
    if feature_check:
        out.append(f"**Feature/non-block doc pages checked:** {len(feature_check)}  ")
    if sitemap_rows:
        out.append(f"**Site-wide URLs checked:** {len(sitemap_rows)}  ")
    if dashboard_rows:
        out.append(f"**WP-admin dashboard checked:** yes (`views/welcome.php`)  ")
    out.append("")

    total_broken = len(still_broken) + len(broken_sitemap_links := [r for r in sitemap_rows if is_broken(r[1], r[2])])
    total_video_gaps = total_no_video + total_mismatches + len(feat_no_video) + len(feat_mismatches)
    out.append("## Verdict")
    out.append("")
    if total_broken == 0 and total_video_gaps == 0 and not dashboard_stale:
        out.append("PASS. No broken links, video-coverage gaps, or dashboard staleness found.")
    else:
        out.append(f"{total_broken} broken link(s), {total_video_gaps} video-coverage gap(s), "
                    f"dashboard stale: {'yes' if dashboard_stale else 'no'}.")
        out.append("")
        out.append(f"- {len(still_broken)} broken block demo/doc link(s) with no live fallback found")
        out.append(f"- {len(resolved_via_fallback)} block link(s) dead in `blocks.php` but the real page was found and re-checked")
        out.append(f"- {len(broken_sitemap_links)} broken link(s) elsewhere on the site")
        out.append(f"- {len(doc_no_video)} block DOC page(s) with no video, {len(doc_mismatches)} with a likely wrong one")
        out.append(f"- {len(demo_no_video)} block DEMO page(s) with no video, {len(demo_mismatches)} with a likely wrong one")
        out.append(f"- {len(fb_no_video)} fallback-resolved page(s) with no video, {len(fb_mismatches)} with a likely wrong one")
        out.append(f"- {len(feat_no_video)} feature/non-block page(s) with no video, {len(feat_mismatches)} with a likely wrong one")
        if dashboard_stale and dashboard_version_row:
            out.append(f"- **WP-admin welcome screen is stale**: plugin is v{dashboard_version_row[1]}, "
                        f"welcome screen still says v{dashboard_version_row[2]}")
        if fully_absent:
            out.append("")
            out.append(f"**{len(fully_absent)} block(s) have BOTH demo and doc broken with no fallback "
                        f"-- effectively invisible on the marketing site:**")
            for key in fully_absent:
                out.append(f"- {labels.get(key, key)} (`{key}`)")
    out.append("")

    out.append("## Block demo/doc link check")
    out.append("")
    if still_broken:
        out.append(f"**{len(still_broken)} still broken, no live fallback found:**")
        out.append("")
        out.append("| Block | Type | Pro? | URL | Status |")
        out.append("|---|---|---|---|---|")
        for row in still_broken:
            key, kind, url, code, looks404 = row[0], row[1], row[2], row[3], row[4]
            is_pro = "Yes" if blocks.get(key, {}).get("is_pro") else "No"
            note = f"{code}" + (" (soft-404 body)" if looks404 == "yes" and code == "200" else "")
            out.append(f"| {labels.get(key, key)} | {kind} | {is_pro} | {url} | {note} |")
        out.append("")
    if resolved_via_fallback:
        out.append(f"**{len(resolved_via_fallback)} dead in `blocks.php` but real page found and verified live:**")
        out.append("")
        out.append("| Block | Type | Dead URL (in blocks.php) | Real URL | Has video? |")
        out.append("|---|---|---|---|---|")
        for orig_row, fb_row in resolved_via_fallback:
            key, kind = orig_row[0], orig_row[1]
            has_video = fb_row[5] if len(fb_row) > 5 else "n/a"
            out.append(f"| {labels.get(key, key)} | {kind} | {orig_row[2]} | {fb_row[2]} | {has_video} |")
        out.append("")
    if not still_broken and not resolved_via_fallback:
        out.append("All block demo/doc links resolved (HTTP 200, no soft-404 marker).")
    out.append("")

    def render_video_section(title, no_video, mismatches, label_map, intro="", known_extra=None):
        out.append(f"## {title}")
        out.append("")
        if intro:
            out.append(intro)
            out.append("")
        if mismatches or known_extra:
            total = len(mismatches) + len(known_extra or [])
            out.append(f"**{total} possible mismatch(es):**")
            out.append("")
            out.append("| Page | Embedded video title | Video URL | Found by |")
            out.append("|---|---|---|---|")
            for key, label, video_id, video_title in mismatches:
                out.append(f"| {label} | {video_title} | https://youtu.be/{video_id} | word-overlap heuristic |")
            for label, video_id, video_title in (known_extra or []):
                out.append(f"| {label} | {video_title} | https://youtu.be/{video_id} | manual check (heuristic false negative) |")
            out.append("")
        else:
            out.append("No word-overlap mismatches detected (heuristic -- see caveat below, "
                        "does not guarantee there are none).")
            out.append("")
        if no_video:
            out.append(f"**{len(no_video)} page(s) have no embedded tutorial video at all:**")
            for key in no_video:
                out.append(f"- {label_map.get(key, key)} (`{key}`)")
        else:
            out.append("Every resolved page has an embedded video.")
        out.append("")

    render_video_section(
        "Block DOC page video coverage", doc_no_video, doc_mismatches, labels,
        "Word-overlap heuristic for mismatches is **known imperfect in both directions** -- "
        "see the manually-found row below and Scope notes.",
        known_extra=[("Button", "54W79IkVXIo", "How To Create A Call-To-Action Button In Gutenberg")],
    )
    render_video_section(
        "Block DEMO page video coverage", demo_no_video, demo_mismatches, labels,
        "Same check applied to demo/showcase pages, not just doc pages -- these can differ.",
        known_extra=[("Button", "WjIgXQbZVM8", "How To Create Call To Action Button Using Gutenberg In One Click?")],
    )
    if fallback_check:
        render_video_section(
            "Fallback-resolved page video coverage", fb_no_video, fb_mismatches, labels,
            "Pages only reachable because `blocks.php`'s stored URL was dead and a live "
            "replacement was found (see previous section) -- checked the same way as any "
            "other page once reached."
        )
    if feature_check:
        render_video_section(
            "Feature / non-block page video coverage", feat_no_video, feat_mismatches, feature_labels,
            f"{len(feature_check)} doc pages that exist on the site but aren't any block's "
            f"demo/doc URL -- plugin-wide features (AI content tools, global controls, API key "
            f"setup guides, etc.). `blocks.php`-based scope structurally can't see these; this "
            f"catches them by diffing the live site's `/docs/` pages against the block list."
        )

    if dashboard_rows:
        out.append("## WP-admin dashboard welcome screen")
        out.append("")
        out.append("Lives in the plugin itself (`views/welcome.php`), not on essential-blocks.com "
                    "-- invisible to every other check in this report, but it's the first screen "
                    "a user sees right after activating the plugin.")
        out.append("")
        if dashboard_version_row:
            _, plugin_v, welcome_v, stale = dashboard_version_row
            if stale == "yes":
                out.append(f"**Stale.** Plugin is v{plugin_v}, but the welcome screen header still "
                            f"says v{welcome_v}.")
            elif stale == "no":
                out.append(f"Welcome screen version (v{welcome_v}) matches the plugin (v{plugin_v}).")
            else:
                out.append("Could not determine version match (one or both versions not found).")
        if dashboard_video_rows:
            out.append("")
            out.append("| Video ID | Title | Reads as a generic welcome/intro video? |")
            out.append("|---|---|---|")
            for _, vid, title, generic in dashboard_video_rows:
                out.append(f"| {vid} | {title} | {generic} |")
            non_generic = [r for r in dashboard_video_rows if r[3] == "no"]
            if non_generic:
                out.append("")
                out.append(f"**{len(non_generic)} video(s) on the welcome screen don't read as a "
                            f"general intro** -- likely a leftover feature-announcement video "
                            f"(e.g. for a specific block) being shown as if it were the welcome "
                            f"video.")
        out.append("")

    out.append("## Site-wide broken links (marketing-relevant pages)")
    out.append("")
    if sitemap_rows:
        if broken_sitemap_links:
            out.append("| URL | Status |")
            out.append("|---|---|")
            for url, code, looks404 in broken_sitemap_links:
                note = f"{code}" + (" (soft-404 body)" if looks404 == "yes" and code == "200" else "")
                out.append(f"| {url} | {note} |")
        else:
            out.append(f"All {len(sitemap_rows)} checked URLs resolved cleanly.")
    else:
        out.append("(Not run this pass -- see SKILL.md for how to include the site-wide check.)")
    out.append("")

    out.append("## Scope notes")
    out.append("")
    out.append("- Block list is the plugin's own `includes/blocks.php` registry -- the single "
                "source of truth for every block's demo/doc URL, including pro blocks (used "
                "for upsell tiles in the free plugin's inserter).")
    out.append("- Feature/non-block pages are found by diffing the site's live `/docs/` pages "
                "against every block's `doc_path` -- catches plugin-wide features (AI tools, "
                "global controls, API key setup) that a block-only audit structurally can't see.")
    out.append("- Dead `blocks.php` links get a second chance: if the site's own URL list has a "
                "page whose slug shares 2+ significant words with the block's name, that page "
                "is independently re-checked and reported as \"real page found\" instead of "
                "just \"broken.\" A weaker (1-word) match is deliberately NOT auto-accepted -- "
                "tested 2026-08-23 and found wrong 2 of 3 times on single-word overlaps (e.g. "
                "\"image_hotspots\" incorrectly matched to an unrelated page just for sharing "
                "the word \"image\") -- a missed-but-correct fallback just reports \"still "
                "broken,\" which is honest; a wrong guess reported as \"found\" would not be.")
    out.append("- Site-wide check excludes auto-generated WordPress taxonomy archives "
                "(`/tag/`, `/docs-tag/`, `/author/`) and demo-store WooCommerce sample "
                "products (`/product/`, `/product-category/`) -- these aren't authored "
                "marketing content, and checking all of them would be mostly noise plus "
                "unnecessary load on the live site.")
    out.append("- \"Broken\" = HTTP status != 200, OR the page body contains a soft-404 "
                "marker (\"Page Not Found\" / \"Nothing Here\" / \"404 Error\") even on a "
                "200 response. Essential Blocks' site returns genuine HTTP 404s for dead "
                "docs/demo pages (verified), so soft-404 hits are rare but checked as a "
                "safety net.")
    out.append("- A 200 result only proves the URL resolves -- it does NOT confirm the "
                "content is complete, current, or non-thin. For content-quality analysis "
                "(missing sections, placeholder text, stale screenshots), scrape the page "
                "and read it -- see SKILL.md \"Deeper content-quality pass\".")

    print("\n".join(out))


if __name__ == "__main__":
    main()
