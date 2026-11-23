#!/bin/sh
# Checks for mockup O ("Civitas"). Run from the repo root with a static server on the repo:
#   python3 -m http.server 8898 --bind 127.0.0.1 &   then   sh themed/check_o.sh [base-url]
# 1. parity: every text block of the live pages is present in mockup-o. The --ignore-regex list is ONLY the
#    Transit Map theme's own wording (stations, lines, zones, map squares, "Change here for", its headings);
#    each of those is re-worded in this theme, not dropped. Case-study bodies are compared in full.
#    Four deliberate edits are also ignored, each still said on the page in other words:
#      - the per-stop "Flagship system" badge in the three routes (all ten stops carry it; the index key says it once);
#      - the sentence explaining the badges in the index intro (the key under it says the same);
#      - "Every client, matter and person in the demos is invented." on Legal (the lede above it says the same);
#      - "Show all 48 projects": the count was stale; this theme computes it from the table's rows.
# 2. links: every internal link, #anchor, media file and old-#hash redirect resolves.
set -e
SK="$HOME/.claude/skills/websiteoftheyear/scripts"
BASE="${1:-http://localhost:8898}"
TMP="$(mktemp -d)"
for r in legal business creative design research; do mkdir -p "$TMP/$r"; cp "$r/index.html" "$TMP/$r/"; done
cp index.html "$TMP/"
python3 -I "$SK/parity.py" --old "$TMP" --new mockup-o --show 40 \
  --ignore-regex '^.*Map square.*$' --ignore-regex '^.*[0-9]+ stations.*$' --ignore-regex '^.*Change (here )?for.*$' \
  --ignore-regex '^Zone [0-9].*$' --ignore-regex '^Interchange: .*$' \
  --ignore-regex '^System map · November 2026.*$' --ignore-regex '^Myles Parslow [0-9]+ builds with AI, shown in full$' \
  --ignore-regex '^Pick your line\.$' --ignore-regex 'or go straight to the full map below\.$' --ignore-regex '^Open the full map ↓$' \
  --ignore-regex '^The full network$' --ignore-regex '^Select a line to filter the map\..*$' --ignore-regex '^Central hub: .*$' \
  --ignore-regex '^Weekend build Study' --ignore-regex '^Every project indexed by station, line, zone and map square\.' \
  --ignore-regex '^Rules of travel$' --ignore-regex '^How I work with AI · ' --ignore-regex '^Which AI for what · ' \
  --ignore-regex '^Style archive\. You’re looking at: Transit Map\. ' --ignore-regex '^Hover or tab across stations to inspect them\..*$' --ignore-regex '^This line at a glance$' \
  --ignore-regex '^[0-9]+ tools in [0-9]+ groups, flagships first, then by practice area\. marks a flagship system\. Every client, matter and person in the demos is invented\.' \
  --ignore-regex '(?<=[A-Za-z])Flagship system(?=[A-Z0-9])' \
  --ignore-regex ' Flagship system marks the production systems; Weekend build and Study mark sprints and benchmarks\.' \
  --ignore-regex '^Show all 48 projects$'
rm -rf "$TMP"
node "$SK/check_links.mjs" "$BASE/mockup-o/" --crawl --redirect-map-var M --no-external
