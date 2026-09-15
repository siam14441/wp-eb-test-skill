#!/usr/bin/env bash
# Curl-check every URL in a newline-delimited URL file (e.g. from
# `firecrawl map <site> -o urls.txt`). Free (no API credits) -- this is why
# it's safe to run against the FULL site map (1000+ URLs) rather than a
# sample.
#
# Usage: check_sitemap.sh <urls-file> [concurrency]
# Writes TSV to stdout: url<TAB>http_code<TAB>looks_404
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URLS_FILE="$1"
CONCURRENCY="${2:-8}"

grep -v '^\s*$' "$URLS_FILE" | xargs -P "$CONCURRENCY" -I{} "$SCRIPT_DIR/check_url.sh" {}
