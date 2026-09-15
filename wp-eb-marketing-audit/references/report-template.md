# Essential Blocks -- Marketing Content Audit

This is the shape `scripts/generate_report.py` produces. It's generated, not
hand-filled -- this file documents the structure for reference.

```
# Essential Blocks -- Marketing Content Audit

**Site:** https://essential-blocks.com/
**Run:** <UTC timestamp>
**Blocks checked:** <N> (from `essential-blocks/includes/blocks.php`)
**Block URLs checked:** <N> (demo + doc per block)
**Site-wide URLs checked:** <N>

## Verdict
<PASS, or count of broken links + list of fully-absent blocks>

## Block demo/doc link check
<table of broken demo/doc URLs, or "all resolved">

## Doc-page tutorial video coverage
<possible video/block title mismatches, and docs with zero embedded video>

## Site-wide broken links (marketing-relevant pages)
<table of broken URLs outside the block list, or "all resolved">

## Scope notes
<what was excluded and why -- always included, so the reader knows the
report's boundaries rather than assuming "checked everything">
```

## Severity framing (for whoever reads the report, human or agent)

- **Critical**: a block has BOTH demo and doc broken -- it's effectively
  invisible on the marketing site even though it ships in the plugin.
- **Broken link**: one URL (demo or doc) is dead. The block still has a
  presence, but half its marketing surface is gone.
- **Video gap**: doc page loads fine but has no tutorial video, or the
  embedded video's title doesn't match the block. Softer than a broken
  link -- the page still has written docs -- but it's still a real content
  gap worth a human's attention, especially the title-mismatch case (wrong
  content being shown, not just missing content).
- **Scope exclusions are not silent**: the report always states what was
  excluded (WooCommerce demo-store products, WP tag/author archives) so a
  0-issues verdict reads as "0 issues in what was checked," never
  "0 issues, full stop."
