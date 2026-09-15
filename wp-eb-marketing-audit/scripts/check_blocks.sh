#!/usr/bin/env bash
# Cross-check every block's demo + doc URL (from blocks.json, produced by
# extract_blocks.py) against the live site. Runs checks concurrently but
# capped, to avoid hammering essential-blocks.com.
#
# Usage: check_blocks.sh <blocks.json> <site_base_url> [concurrency]
# Writes TSV to stdout: key<TAB>kind<TAB>url<TAB>http_code<TAB>looks_404
# (label/is_pro are looked up from blocks.json separately when building the
# report -- keeping job fields space-free lets plain BSD/GNU xargs word-split
# them safely, no custom delimiter handling needed.)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKS_JSON="$1"
BASE_URL="${2:-https://essential-blocks.com/}"
CONCURRENCY="${3:-6}"

jobs_file=$(mktemp)
trap 'rm -f "$jobs_file"' EXIT

jq -r --arg base "$BASE_URL" '
  (.[] | select(.demo_path != null) | [.key, "demo", ($base + .demo_path)] | @tsv),
  (.[] | select(.doc_path != null)  | [.key, "doc",  ($base + .doc_path)]  | @tsv)
' "$BLOCKS_JSON" > "$jobs_file"

xargs -P "$CONCURRENCY" -L 1 "$SCRIPT_DIR/run_one_check.sh" < "$jobs_file"
