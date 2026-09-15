#!/usr/bin/env python3
"""
Extract the canonical block list (label, demo URL, doc URL, pro/free, hidden)
from Essential Blocks' own includes/blocks.php.

Why this file and not the pro plugin: essential-blocks-pro/includes/blocks.php
only registers block *objects* (no label/demo/doc metadata). The free plugin's
includes/blocks.php is the single source of truth for marketing metadata for
ALL 79 blocks, including pro ones (it's what renders the upsell block-inserter
tiles). Verified 2026-08-23 by reading both files directly.

Usage:
    python3 extract_blocks.py /path/to/essential-blocks/includes/blocks.php > blocks.json
"""
import json
import re
import sys

SECTION_RE = re.compile(
    r"\$(free_blocks|new_blocks|pro_blocks)\s*=\s*array\(\s*(.*?)\n\);",
    re.DOTALL,
)
ENTRY_RE = re.compile(
    # trailing comma is optional: the last entry in each PHP array has none
    r"'([a-z_0-9]+)'\s*=>\s*array\(\s*(.*?)\n    \),?(?:\n|\Z)",
    re.DOTALL,
)
LABEL_RE = re.compile(r"'label'\s*=>\s*__\(\s*'([^']*)'")
DEMO_RE = re.compile(r"'demo'\s*=>\s*ESSENTIAL_BLOCKS_SITE_URL\s*\.\s*'([^']*)'")
DOC_RE = re.compile(r"'doc'\s*=>\s*ESSENTIAL_BLOCKS_SITE_URL\s*\.\s*'([^']*)'")
IS_PRO_RE = re.compile(r"'is_pro'\s*=>\s*true")
HIDDEN_RE = re.compile(r"'show_in_admin'\s*=>\s*false")
PARENT_RE = re.compile(r"'parent'\s*=>\s*array\(\s*\"([^\"]*)\"")


def main():
    if len(sys.argv) != 2:
        print("usage: extract_blocks.py <path-to-blocks.php>", file=sys.stderr)
        sys.exit(1)

    text = open(sys.argv[1], encoding="utf-8").read()

    blocks = []
    for section_name, section_body in SECTION_RE.findall(text):
        section_is_pro = section_name == "pro_blocks"
        for key, entry_body in ENTRY_RE.findall(section_body):
            label_m = LABEL_RE.search(entry_body)
            demo_m = DEMO_RE.search(entry_body)
            doc_m = DOC_RE.search(entry_body)
            parent_m = PARENT_RE.search(entry_body)
            blocks.append({
                "key": key,
                "label": label_m.group(1) if label_m else key,
                "section": section_name,
                "is_pro": section_is_pro or bool(IS_PRO_RE.search(entry_body)),
                "hidden_subblock": bool(HIDDEN_RE.search(entry_body)) or bool(parent_m),
                "parent": parent_m.group(1) if parent_m else None,
                "demo_path": demo_m.group(1) if demo_m else None,
                "doc_path": doc_m.group(1) if doc_m else None,
            })

    if not blocks:
        print("WARNING: extracted 0 blocks -- regex likely out of sync with "
              "blocks.php's current structure. Inspect the file manually.",
              file=sys.stderr)

    print(json.dumps(blocks, indent=2))


if __name__ == "__main__":
    main()
