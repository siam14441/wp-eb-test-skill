#!/usr/bin/env bash
# Fetch one URL and report: HTTP status + whether the WP theme's soft-404
# marker ("Page Not Found") appears in the body, even on a 200 response.
# Essential Blocks' site returns genuine HTTP 404s for dead /docs/ and
# /demo/ pages (verified 2026-08-23), but this second check guards against
# any soft-404 page elsewhere on the site that returns 200 with error content.
#
# Usage: check_url.sh <url>
# Output (tab-separated): <url> <http_code> <looks_like_404: yes|no>
set -euo pipefail
url="$1"

body_file=$(mktemp)
trap 'rm -f "$body_file"' EXIT

http_code=$(curl -sL -o "$body_file" -w "%{http_code}" --max-time 20 "$url" || echo "000")

looks_404="no"
if grep -qi "page not found\|nothing here\|404 error" "$body_file" 2>/dev/null; then
    looks_404="yes"
fi

printf "%s\t%s\t%s\n" "$url" "$http_code" "$looks_404"
