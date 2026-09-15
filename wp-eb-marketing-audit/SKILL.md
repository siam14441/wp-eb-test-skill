---
name: wp-eb-marketing-audit
description: >
  Audit essential-blocks.com (the Essential Blocks marketing site) for missing or broken
  marketing content: dead demo/doc links per block, doc pages with no embedded tutorial video
  or a mismatched one, and broken links across the wider site. Cross-references the plugin's
  own includes/blocks.php (the canonical 79-block list, free + pro) against the live site via
  curl -- no browser, no paid API required for the core check. Produces a markdown report.
  Use this skill whenever asked to audit essential-blocks.com, find missing marketing content,
  check for broken docs/demo links, verify tutorial video coverage, or "crawl the essential
  blocks website" / "check every url on the site" for gaps.
---

# Essential Blocks Marketing Site Auditor

Audits **essential-blocks.com** (an external, live WordPress site -- not built or launched
from this repo) against the plugin's own block registry. There is no app to launch here; the
driver is a curl-based crawl-and-check pipeline that hits the live site directly.

**Paths below are relative to this skill's directory**
(`.claude/skills/wp-eb-marketing-audit/`), not the plugin repo.

## Prerequisites

Verified present in this environment 2026-08-23: `curl`, `python3` (3.9+), `jq`, `bash`.
No `php` CLI needed -- `extract_blocks.py` parses `blocks.php` with regex, not a PHP parser.
No firecrawl/API credits needed for the core check (Phases 1-2 are pure `curl`). Firecrawl is
only used, optionally, to regenerate the site-wide URL list (Phase 2) and for the deeper
content-quality pass (Phase 4).

## Run (agent path)

### Phase 1: Extract the canonical block list

```bash
python3 scripts/extract_blocks.py \
  "<path-to-essential-blocks-plugin>/includes/blocks.php" > /tmp/eb-blocks.json
```

Default plugin path on this machine (adjust if different):
`<path-to-local-wp-install>/wp-content/plugins/essential-blocks/includes/blocks.php`

Sanity check -- should print `79` (58 free + 21 pro, including hidden sub-blocks like
Loop Builder's children and Form's field types):
```bash
jq 'length' /tmp/eb-blocks.json
```

If it prints something else, `blocks.php`'s structure changed and the regex in
`extract_blocks.py` needs updating -- see Gotchas.

### Phase 2: Check every block's demo + doc URL against the live site

```bash
bash scripts/check_blocks.sh /tmp/eb-blocks.json "https://essential-blocks.com/" 6 \
  > /tmp/eb-block-check.tsv
```

Takes ~2-4 minutes for all 79 blocks (158 URLs; doc URLs that resolve get a second fetch to
check for an embedded tutorial video, plus a YouTube oEmbed lookup -- see Phase 3). Runs at
concurrency 6 by default (3rd arg) -- keep it modest, this hits someone else's production site.

Output columns (TSV, no header):
`key  kind(demo|doc)  url  http_code  looks_like_soft_404(yes|no)  has_video(yes|no|n/a)  video_id  video_title`

### Phase 2b: Resolve dead blocks.php links to their real live page

`blocks.php`'s hardcoded URLs go stale (e.g. it points `facebook_feed`'s doc at
`docs/facebook-feed/` but the live page is actually `docs/eb-facebook-feed`). Left unfixed, a
dead link **masks** whatever real problem the live page has -- e.g. Facebook Feed's real doc
page turns out to have zero embedded video, invisible until you actually reach it. Needs the
sitemap URL list from Phase 3, so grab that first if you haven't:
```bash
firecrawl map "https://essential-blocks.com/" -o /tmp/eb-sitemap.json
```
```bash
python3 scripts/resolve_fallbacks.py /tmp/eb-blocks.json /tmp/eb-block-check.tsv \
  /tmp/eb-sitemap.json > /tmp/eb-fallbacks.tsv
bash scripts/check_fallbacks.sh /tmp/eb-fallbacks.tsv 3 > /tmp/eb-fallback-check.tsv
```
Only accepts a candidate with 2+ shared significant words with the block's name (tested
2026-08-23: single-word matches were wrong 2 of 3 times) -- a missed-but-correct fallback just
reports "still broken" in the final report, which is honest; a wrong guess reported as "found"
would not be. Both outputs can be empty/missing with no broken links -- that's fine, later
phases treat them as optional.

### Phase 3: Site-wide broken-link check + non-block feature pages (optional but cheap -- it's just curl)

Reuse the sitemap map from Phase 2b, or regenerate it (~1 credit):
```bash
firecrawl map "https://essential-blocks.com/" -o /tmp/eb-sitemap.json
```

Filter out non-marketing noise -- WordPress auto-generated taxonomy/author archives and the
WooCommerce demo-store's sample products aren't authored marketing content, and checking all
~1300 of them is mostly noise plus unnecessary load on the live site:
```bash
grep -vE '/(tag|docs-tag|product|product-category|author)/' /tmp/eb-sitemap.json \
  | sort -u > /tmp/eb-marketing-urls.txt
```
(On the 2026-08-25 run this cut ~1740 URLs to 440. Re-check the ratio if the site's grown a lot
differently -- the excluded prefixes are a judgment call, documented in the report's Scope
Notes section, not a hardcoded truth.)

```bash
bash scripts/check_sitemap.sh /tmp/eb-marketing-urls.txt 8 > /tmp/eb-sitemap-check.tsv
```
~440 URLs takes several minutes at concurrency 8. Pure curl -- free, no credits.

**Feature/non-block doc pages** -- `blocks.php` only covers the 79 blocks; the site also
documents plugin-wide features (AI tools, global controls, API key setup guides, etc.) that
deserve the same video-coverage scrutiny but were entirely out of scope before this. Found by
diffing the site's live `/docs/` pages against every block's `doc_path`:
```bash
python3 scripts/list_feature_docs.py /tmp/eb-blocks.json /tmp/eb-sitemap.json \
  > /tmp/eb-feature-docs.tsv
awk -F'\t' '{print $1"\tdoc\t"$3}' /tmp/eb-feature-docs.tsv > /tmp/eb-feature-jobs.tsv
xargs -P 6 -L 1 scripts/run_one_check.sh < /tmp/eb-feature-jobs.tsv > /tmp/eb-feature-check.tsv
```
On the 2026-08-25 run this found 35 feature pages (27 with no video at all).

### Phase 3b: WP-admin dashboard welcome screen (local file check, not a URL check)

Lives in the plugin itself, not on essential-blocks.com -- invisible to every check above, but
it's the first screen a user sees right after activating the plugin:
```bash
bash scripts/check_dashboard_welcome.sh "<path-to-essential-blocks-plugin>" \
  > /tmp/eb-dashboard-check.tsv
```
Checks two things: (1) does `views/welcome.php`'s hardcoded "Welcome To Essential Blocks
X.Y.Z" header match the plugin's actual `readme.txt` Stable tag, and (2) does the page's
embedded video (if any) read as a generic welcome/intro, or as a specific feature
announcement being shown out of context. On the 2026-08-25 run: plugin is v6.4.3, welcome
screen says v4.0.0, and its only video is "How To Add Google Maps In WordPress With Essential
Blocks?" under a "New Block: Google Maps" callout -- both flagged stale/mismatched.

### Phase 4: Generate the report

```bash
python3 scripts/generate_report.py \
  --blocks /tmp/eb-blocks.json \
  --block-check /tmp/eb-block-check.tsv \
  --sitemap-check /tmp/eb-sitemap-check.tsv \
  --fallback-list /tmp/eb-fallbacks.tsv --fallback-check /tmp/eb-fallback-check.tsv \
  --feature-list /tmp/eb-feature-docs.tsv --feature-check /tmp/eb-feature-check.tsv \
  --dashboard-check /tmp/eb-dashboard-check.tsv \
  > marketing-audit-report-essential-blocks-com-<date>.md
```
Every flag except `--blocks`/`--block-check` is optional -- omit any phase's flags to skip
that section of the report (it'll say "not run this pass" instead of silently pretending
there's nothing to find).

Save to `wp-content/plugins/eb-qa-reports/` (sibling of the plugin dirs, survives their
auto-updates -- matches this user's existing `qa-report-*.md` / `reproduce-report-*.md`
naming convention there). New file per run, never overwrite a prior report, no filename/body
references to "round N."

### Phase 5 (manual, not scripted): deeper content-quality pass

The automated phases only prove a URL resolves and (for docs) whether a video is embedded --
not whether the *content* is complete, current, or well-written. For that, scrape and actually
read a handful of key pages (homepage, pricing, comparison pages, and any block flagged in
Phase 2/3) with `firecrawl scrape --only-main-content`, then judge: thin sections, placeholder
text, stale screenshots, missing CTAs, feature claims that don't match current blocks. This
step needs judgment, not just a script -- budget firecrawl credits accordingly (each scrape
costs roughly 1 credit for a plain markdown fetch, seen in practice on this site).

## Verified run (2026-08-25, extends the 2026-08-23 run)

Ran all phases for real against the live site (79 blocks, 158 block-URL checks, 35 feature
pages, 1 dashboard file, ~440 site-wide URL checks). This run added demo-page video checking,
fallback resolution, feature-page discovery, and the dashboard check -- prompted by comparing
against an independent findings list (a Google Doc, compiled by someone else) that flagged 7
issues; 3 were already caught, 4 were structurally invisible to the block-only, doc-only,
site-only version of this skill. Results:

- **6 broken block-URL links**, of which 2 (`facebook_feed` doc, `advanced_heading` doc) were
  auto-resolved to their real live page via Phase 2b's fallback matching, and re-checked --
  **both real pages have zero embedded video**, a finding that was invisible before because
  the dead link stopped the check before it ever reached the live page. The remaining 4
  (`image_hotspots` demo, `form_phone_field` demo, `add_to_cart` doc, `form_phone_field` doc)
  have no confident fallback and are still just broken.
- **Doc-page video gaps: 13 no-video + 2 mismatches** (Countdown auto-caught, Button manually
  confirmed -- see prior run notes). **Demo-page video gaps (new): 33 no-video + 1 manually
  confirmed mismatch.** Checking demo pages roughly *tripled* the no-video count and confirmed
  Button's mismatch isn't a one-off: its demo page embeds a **different** wrong Call-to-Action
  video (`WjIgXQbZVM8`) than its doc page does (`54W79IkVXIo`) -- both of Button's marketing
  surfaces show the wrong tutorial, independently.
- **Feature pages (new): 35 found, 27 with no video.** These are plugin-wide feature docs
  (`write-with-ai`, `configure-acf-support-for-gutenberg`, API key setup guides, etc.) that
  `blocks.php`'s 79-block list structurally cannot see -- this is exactly the category the
  independent findings list flagged with "no video for Generate AI Images" / "no tutorial for
  Templately import." (Templately: confirmed live -- no `/docs/` page for it exists at all,
  only `/tag/templately*` archive pages, so it's not even in the feature-doc list; the gap is
  "page doesn't exist," one level worse than "page exists but has no video.")
- **Dashboard welcome screen (new): stale, confirmed two ways.** Plugin is v6.4.3;
  `views/welcome.php`'s header hardcodes "Welcome To Essential Blocks 4.0.0" -- a 2+ major
  version gap. Its only video embed sits under a "New Block: Google Maps" callout (shipped
  well before 6.4.3) and resolves via oEmbed to "How To Add Google Maps In WordPress With
  Essential Blocks?" -- so a brand-new user's first plugin experience is an outdated feature
  announcement with an unrelated tutorial, not a welcome video at all.
- **440/440 site-wide marketing-relevant URLs resolved cleanly** (0 broken) -- consistent
  with the 2026-08-23 run's 433/433.
- A page with NO embedded video does not always mean "no tutorial exists" -- e.g.
  `eb-shape-divider`'s doc page in fact embeds a real, correctly-titled video
  ("How To Add Shape Divider In Your Gutenberg Website", id `RhPzljhTeF4`) that simply isn't
  part of the specific YouTube playlist checked in an earlier manual pass. Direct page-content
  inspection is more authoritative than title-matching against one playlist.

## Gotchas

- **`grep` finding zero matches exits 1, and under `set -euo pipefail` that silently kills the
  whole worker script** -- `run_one_check.sh` greps a doc page's body for a YouTube embed; on
  a page that genuinely has NO video, that's a *correct, expected* zero-match, not an error,
  but `pipefail` treated it as one and the job died before printing its output row. First real
  run (2026-08-23) silently dropped exactly the 13 doc pages with no video -- the report looked
  clean ("no missing videos!") when in fact those rows were just missing from the dataset
  entirely, not present-and-passing. Fix: wrap the grep in `{ grep ... || true; }` so a
  legitimate no-match doesn't abort the pipeline. **Lesson for this whole skill**: a
  suspiciously-clean section of the report is itself a signal to check row counts against
  expected totals, not just trust an empty "issues" list.
- **`php` is not on PATH** in this environment even though this is a WordPress dev machine
  (Local by Flywheel bundles its own PHP, not linked into the shell). Don't shell out to
  `php -r` to parse `blocks.php` -- `extract_blocks.py` uses regex instead. `perl` and
  `python3` are both available if you need an alternate parser.
- **The last entry in each PHP array in `blocks.php` has no trailing comma** before its
  closing `);` (`$free_blocks`, `$new_blocks`, and `$pro_blocks` each drop it on their final
  block: `icon`, `image_hotspots`, `animated_wrapper`). A naive regex requiring a comma after
  each entry's closing `),`  silently drops exactly those 3 blocks. `extract_blocks.py`'s
  `ENTRY_RE` makes the comma optional and matches end-of-section as an alternate terminator --
  don't regress this if you touch the regex.
- **BSD `xargs` (macOS default) chokes on `-I{}` + an inline `bash -c` string that itself does
  field-splitting** (`IFS=$'\t' read -r ... <<< "{}"` inside a quoted `-c` body) -- it fails
  with `xargs: command line cannot be assembled, too long` on inputs far below any real length
  limit. It's a quoting/escaping issue, not a size issue. Fix: keep job fields free of spaces
  (`key`, `kind`, `url` -- no `label` in the job line) and call a **separate script**
  (`run_one_check.sh`) as the xargs command, taking `$1 $2 $3`, instead of embedding logic in
  the xargs invocation itself. Don't reach for `bash -c` inside `xargs -I{}` on this platform.
- **essential-blocks.com returns genuine HTTP 404s** for dead `/docs/` and `/demo/` pages, not
  soft-404s with a 200 status -- confirmed by direct `curl -o /dev/null -w '%{http_code}'`
  checks. The soft-404 body-text check in `check_url.sh` is a safety net for pages elsewhere on
  the site, not the primary signal; don't assume you need JS rendering or a content check to
  catch dead block links -- a plain status-code check already does.
- **Some doc URLs hardcoded in `blocks.php` are stale but still "work" via redirect** -- e.g.
  the plugin says `docs/facebook-feed/`  but that's actually a dead link (confirmed 404, not a
  redirect) while the *real* content lives at `docs/eb-facebook-feed`. Don't assume "the plugin
  links to X" means X is live; always check.
- **`youtube.com/playlist` and `youtube-player` appear on EVERY doc page** (nav/footer
  boilerplate), so grepping for those as a "has video" signal gives false positives on every
  page. The reliable marker is specifically `youtube.com/embed/<id>` -- only present when a
  video is actually embedded in the page body.
- **The plugin's `essential-blocks-pro/includes/blocks.php` has no demo/doc metadata at all**
  -- it only registers block objects. The free plugin's `includes/blocks.php` is the single
  source of truth for label/demo/doc URLs for ALL 79 blocks (free AND pro -- it renders the
  pro upsell tiles in the free plugin's block inserter). Don't go looking for pro block URLs in
  the pro plugin's own files.
- **Rate limit yourself.** This is someone's live production marketing site, not a local
  sandbox. Concurrency defaults (6 for block checks, 8 for sitemap checks) are deliberately
  modest -- don't crank them up "for speed" without a reason.
- **BSD `sed` (macOS) does not support `\s`** -- `sed -E 's/.*:\s*//'` silently leaves a
  leading space behind instead of stripping it (`check_dashboard_welcome.sh` hit this parsing
  `readme.txt`'s "Stable tag:  6.4.3" line -- note the file has TWO spaces after the colon).
  Use the POSIX class `[[:space:]]` instead. Confirmed macOS `grep` (unlike `sed`) DOES support
  `\s` fine, so this is a `sed`-specific gotcha, not a general BSD-tools one -- don't assume it
  generalizes.
- **A block's "real" doc page found via redirect can look like a brand-new orphan "feature"
  page** if you naively diff the sitemap against `blocks.php`'s stored `doc_path` strings.
  E.g. `image_gallery`'s stored `doc_path` is `eb-filterable-gallery/`, which 301-redirects to
  the site's actual `eb-image-gallery` -- so `curl -L` reports the ORIGINAL URL as 200 (not
  broken, no fallback needed), but the sitemap independently lists the REDIRECT TARGET as its
  own distinct URL, which then looks like an unrelated new feature page if you're not
  filtering for this. `list_feature_docs.py` guards against it with the same 2+-token
  overlap-against-any-block-label check used by the fallback resolver -- don't remove that
  filter, it cut the false "feature" count from 44 to 35 on the 2026-08-25 run.
- **Short block names lose their only distinguishing token to the stopword list.** "Add To
  Cart" tokenizes to just `{"cart"}` once "add"/"to" are stripped as filler words -- so even
  a CORRECT fallback match for it can only ever score 1, identical to the score of a wrong
  guess elsewhere. This is a known, accepted false-negative source in both
  `resolve_fallbacks.py` and `list_feature_docs.py`'s filters -- it means `add_to_cart` shows
  up as "still broken, no fallback" even though a human would immediately recognize
  `eb-woo-add-to-cart` as the answer, and separately still shows up once in the feature-docs
  list under the same URL. Not worth chasing further: the alternative (loosening the
  stopword list) risks reintroducing wrong matches elsewhere for a small one-block payoff.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `extract_blocks.py` prints a "WARNING: extracted 0 blocks" and exits with no JSON output | `blocks.php`'s array structure changed. Read the file, check `SECTION_RE`/`ENTRY_RE` in `extract_blocks.py` still match the current `'key' => array( ... ),` shape. |
| `jq 'length'` on the extracted JSON doesn't equal 79 | Diff the extracted keys against a fresh manual read of `blocks.php` (`jq -r '.[].key' file.json \| sort` vs grepping `'([a-z_]+)' => array(` in the source) to see which entries got dropped, then fix the regex boundary -- this is what happened with the no-trailing-comma issue above. |
| `xargs: command line cannot be assembled, too long` | You're on BSD xargs (macOS) and something upstream reintroduced spaces into a job line, or reintroduced an inline `bash -c` with quoting. Keep job fields space-free and call a real script file, not an inline `-c` block. |
| `check_blocks.sh` runs but every row shows `http_code=000` | Network/DNS issue, or `--max-time 20` in `check_url.sh` is too short for a slow connection -- bump it. |
| oEmbed lookups return empty `video_title` even though `has_video=yes` | YouTube's oEmbed endpoint can rate-limit or the video was deleted/made private since the page embedded it -- re-run just that one lookup manually with `curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<id>&format=json"` to see the raw response. |

## Report conventions

Reuse this project's existing report conventions (from `wp-eb-test`): a new report file per
run (never overwrite a prior one), no "round N" framing anywhere in title/filename/body, and
report editor-facing findings honestly rather than hedging. Save reports outside of the
`essential-blocks`/`essential-blocks-pro` plugin directories -- an in-plugin location got wiped
by a WP auto-update in the past.

## What this skill does NOT do

- Does not render JavaScript / does not need a headless browser -- essential-blocks.com's
  docs/demo pages are server-rendered WordPress, plain `curl` sees the same content a browser
  would (verified: `curl` output and `firecrawl scrape` output agreed on every page checked).
- Does not judge content quality (thin sections, stale screenshots, weak copy) automatically --
  that's Phase 5, manual, by design. A script can tell you a page loads; it can't tell you the
  page is *good*.
- Does not modify anything. Read-only against a live external site.
