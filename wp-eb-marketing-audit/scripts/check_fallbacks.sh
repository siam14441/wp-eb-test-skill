#!/usr/bin/env bash
# Verify each fallback URL resolve_fallbacks.py suggested -- an accepted
# fallback is a GUESS (token-overlap match) until an independent live check
# confirms it actually resolves. Reuses run_one_check.sh so fallback rows get
# the exact same status + video-detection treatment as primary rows.
#
# Usage: check_fallbacks.sh <fallbacks.tsv> [concurrency]
#   fallbacks.tsv columns: key  kind  original_url  fallback_url  score
# Writes TSV to stdout: key  kind  fallback_url  http_code  looks_404  has_video  video_id  video_title
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FALLBACKS_TSV="$1"
CONCURRENCY="${2:-6}"

[ -s "$FALLBACKS_TSV" ] || exit 0

jobs_file=$(mktemp)
trap 'rm -f "$jobs_file"' EXIT
awk -F'\t' '{print $1"\t"$2"\t"$4}' "$FALLBACKS_TSV" > "$jobs_file"

xargs -P "$CONCURRENCY" -L 1 "$SCRIPT_DIR/run_one_check.sh" < "$jobs_file"
