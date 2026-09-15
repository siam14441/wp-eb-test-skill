#!/usr/bin/env bash
# Checks the WordPress admin "Welcome to Essential Blocks" dashboard screen
# for staleness -- this lives in wp-admin (views/welcome.php), NOT on
# essential-blocks.com, so it's invisible to every other check in this
# skill. It's also the first screen a user sees right after activating the
# plugin, so it's high-visibility.
#
# Verified (2026-08-25): current plugin version is 6.4.3 (readme.txt Stable
# tag), but welcome.php hardcodes the header "Welcome To Essential Blocks
# 4.0.0" -- a 2+ major version gap. Its only video embed sits under a
# "New Block: Google Maps" callout (Google Maps shipped well before 6.4.3)
# and resolves to "How To Add Google Maps In WordPress With Essential
# Blocks?" -- i.e. a brand-new user's first plugin experience is an outdated
# feature announcement with an unrelated tutorial video, not a real welcome.
#
# Usage: check_dashboard_welcome.sh <essential-blocks-plugin-dir>
# Output (tsv):
#   version_check  <plugin_version>  <welcome_screen_version>  <stale:yes|no>
#   video  <video_id>  <video_title>  <looks_like_generic_welcome:yes|no>
# (zero or more "video" rows -- welcome.php can embed more than one)
set -euo pipefail
PLUGIN_DIR="$1"
WELCOME_FILE="$PLUGIN_DIR/views/welcome.php"
README_FILE="$PLUGIN_DIR/readme.txt"

if [ ! -f "$WELCOME_FILE" ]; then
    echo "error: $WELCOME_FILE not found" >&2
    exit 1
fi

plugin_version=$(grep -m1 -i "Stable tag" "$README_FILE" | sed -E 's/.*:[[:space:]]*//' | tr -d '\r')
welcome_version=$(grep -oE "Welcome To Essential Blocks [0-9]+\.[0-9]+\.[0-9]+" "$WELCOME_FILE" \
    | head -1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" || true)

stale="unknown"
if [ -n "$plugin_version" ] && [ -n "$welcome_version" ]; then
    if [ "$plugin_version" != "$welcome_version" ]; then
        stale="yes"
    else
        stale="no"
    fi
fi

printf "version_check\t%s\t%s\t%s\n" "$plugin_version" "${welcome_version:-none found}" "$stale"

video_ids=$(grep -oE "youtube\.com/embed/[A-Za-z0-9_-]+" "$WELCOME_FILE" | sed 's#.*/##' | sort -u)
for video_id in $video_ids; do
    video_title=$(curl -s --max-time 10 \
        "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${video_id}&format=json" \
        | jq -r '.title // empty' 2>/dev/null || true)
    video_title=$(printf '%s' "$video_title" | tr '\t' ' ')
    looks_generic="no"
    lower_title=$(printf '%s' "$video_title" | tr '[:upper:]' '[:lower:]')
    case "$lower_title" in
        *welcome*|*introduc*|*get\ started*|*overview*) looks_generic="yes" ;;
    esac
    printf "video\t%s\t%s\t%s\n" "$video_id" "$video_title" "$looks_generic"
done
