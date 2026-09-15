#!/usr/bin/env bash
# Worker invoked by check_blocks.sh's xargs pool. Args have no spaces
# (key, kind, url), so plain xargs word-splitting is safe -- no quoting
# gymnastics needed.
#
# For any URL that resolves (doc OR demo), also detects the embedded
# YouTube tutorial video (if any) and resolves its real title via YouTube's
# public oEmbed endpoint (no API key needed). This catches: (a) a page with
# NO embedded video at all, and (b) a page whose embedded video's title
# doesn't match the block -- e.g. the Button block was found (2026-08-23) to
# embed a Call-to-Action tutorial on BOTH its doc page ("How To Create A
# Call-To-Action Button In Gutenberg") AND its demo page (a DIFFERENT
# Call-to-Action video, "How To Create Call To Action Button Using Gutenberg
# In One Click?") -- checking demo pages too roughly doubles the video-gap
# surface area versus doc-only, and found this mismatch is not a fluke.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
key="$1"
kind="$2"
url="$3"

result=$("$SCRIPT_DIR/check_url.sh" "$url")
http_code=$(printf '%s' "$result" | cut -f2)
looks_404=$(printf '%s' "$result" | cut -f3)

has_video="n/a"
video_id=""
video_title=""

if [ "$http_code" = "200" ]; then
    body=$(curl -sL --max-time 20 "$url" || true)
    # grep exits 1 (no match) when a doc page genuinely has no video -- that's
    # an expected, valid outcome here, not a script failure. Don't let
    # pipefail/set -e kill the whole job over it.
    video_id=$(printf '%s' "$body" | { grep -oE "youtube\.com/embed/[A-Za-z0-9_-]+" || true; } | head -1 | sed 's#.*/##')
    if [ -n "$video_id" ]; then
        has_video="yes"
        video_title=$(curl -s --max-time 10 \
            "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${video_id}&format=json" \
            | jq -r '.title // empty' 2>/dev/null || true)
        video_title=$(printf '%s' "$video_title" | tr '\t' ' ')
    else
        has_video="no"
    fi
fi

printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$key" "$kind" "$url" "$http_code" "$looks_404" "$has_video" "$video_id" "$video_title"
