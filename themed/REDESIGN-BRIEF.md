# Portfolio redo v2: shared rules for mockup C and mockup D

Repo: `~/portfolio-woty` (branch `claude/redo-v2`). The live site is mylesparslow.com, and the deployed files are `index.html`, `<room>/index.html` and `assets/site/*`. **Don't edit any of those**, nor `themed/source/`, `mockup-a/`, `mockup-b/`, `render_b.py` or `promote_b.py`. Write only your own renderer and your own mockup folder.

## Content source
`themed/live.json` was made by `themed/extract_live.py` from the live pages. It holds:
- `home`: `hero_html`, `rules_html`, `tools_html`, `foot_html`, `redirect_map` (a JS object literal mapping old homepage hashes to room slugs).
- `rooms[]`, one per room (legal, business, creative, design, research), each with title, short, letter, eyebrow, count and lede (HTML), plus `items` in page order:
  - `case` items carry id, count ("03 / 16"), kickers[], title, sub, lede, `body_html`, `links_html` and `thumb` (the path from a room page, `../assets/...`; empty for 5 cases, so use the first `<img>` in `body_html` for those).
  - `group` items (`div.gdiv` with `.gdiv__t`, `.gdiv__p`) and `extra` items (`section.xsec`, the business "Smaller pieces").

53 case studies in all. **Every piece of text in live.json must appear on your pages.** Restyle the body markup, don't rewrite it. The classes in use are `block`, `cols`, `made`, `links`, `shots`, `wide`, `grid3`, `stats`, `portrait`, `gallery`, `compare`/`compare-fig`/`cmp-*`, `reels`, `book(s)`, `facts`, `tags`/`tag`, `note`, `logline`, `flow` and `piece`. Read `assets/site/rooms.js` and `assets/site/rooms.css` to see what the live site does with them (compare sliders, galleries, video), and port any behaviour the markup needs.

## Paths and links
- Your output goes in `mockup-X/index.html` and `mockup-X/<room>/index.html`, plus your CSS and JS inside `mockup-X/`.
- Body paths are written for a room page at the site root (`../assets/`, `../demos/`). From `mockup-X/<room>/` they need one more `../`. From `mockup-X/index.html`, a thumb `../assets/x.jpg` becomes `../assets/x.jpg` (the same, since mockup-X sits one level down).
- Room-to-room and homepage-to-room links stay in-theme (`../legal/index.html#vigilmark`, with explicit `index.html`). Demos and external links open in a new tab with `rel="noopener"`, added only when missing.
- Old links: `mockup-X/index.html#vigilmark` must redirect to `legal/index.html#vigilmark` via `redirect_map`.
- Deep links must land below any fixed chrome (`scroll-margin-top`).

## Must-haves
- Plain HTML/CSS/JS, Google Fonts only, no libraries unless one does real work (pin exact versions). No external images.
- A real DOM, a skip link, visible focus, keyboard access to everything, and `prefers-reduced-motion` honoured.
- Works at 375, 768, 1440 and 1920 with no horizontal overflow.
- Screenshots stay sharp. Never filter or tint the project screenshots: they are the work.
- A renderer `themed/render_X.py` (stdlib only, `python3 -I`) that rebuilds the whole mockup from live.json. Re-runnable.

## Verify before reporting
1. `cd ~/portfolio-woty && python3 -m http.server <port>` in the background (C uses 8811, D uses 8812).
2. `node ~/.claude/skills/websiteoftheyear/scripts/shoot.mjs http://localhost:<port>/mockup-X/ <scratch>/X-home --only desk,mob --wait 1500`, and the same for `mockup-X/legal/` and `mockup-X/business/`. **Open and look at every screenshot**, fix what's wrong, and re-shoot.
3. Parity: `python3 -I ~/.claude/skills/websiteoftheyear/scripts/parity.py --old index.html legal/index.html business/index.html creative/index.html design/index.html research/index.html --new mockup-X/index.html mockup-X/legal/index.html ... --map index.html=mockup-X/index.html --map legal/index.html=mockup-X/legal/index.html ...`. Aim for 0 missing; explain any you leave.
4. Links: `node ~/.claude/skills/websiteoftheyear/scripts/check_links.mjs http://localhost:<port>/mockup-X/ --crawl --no-external --concurrency 4`.
5. Kill your server.

Write your jury sheet to `mockup-X/JURY.md`. In your report, include: what you built, the check results, the screenshots you looked at, anything you didn't finish, and anything in this brief that was wrong.

## Style archive blurb (every mockup, added 2026-11-07)
This portfolio doubles as an archive of portfolio styles: each version renders the same 53 case studies in a different style. Every mockup homepage carries a short section near the footer, set in that mockup's own style:

> **Style archive.** This site is also a running design experiment. Each version renders the same 53 case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. **See every version →**

The link goes to `../styles/index.html` (the archive page, at repo root `styles/`; it may not exist yet). Name the current style in the blurb, e.g. "You're looking at: The Museum."
