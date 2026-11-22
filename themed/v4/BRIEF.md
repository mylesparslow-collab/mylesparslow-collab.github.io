# Three new portfolio styles (L, M, N): shared brief for the builders

Written 2026-11-21. Myles asked for three more /websiteoftheyear redesigns of mylesparslow.com. Each one is a complete version of the site: the homepage plus the five room pages (legal, business, creative, design, research), every project and every sentence of the live content, in a new concept. Each lives in its own folder and is generated from `themed/live.json`, exactly like mockup J ("Working Drawings").

| Key | Name | Folder | Generator | Sources | Tier |
|---|---|---|---|---|---|
| L | Tesserae | `mockup-l/` | `themed/render_l.py` | `themed/l/` | B with one GL signature (instancing + a short post pass) |
| M | Redline | `mockup-m/` | `themed/render_m.py` | `themed/m/` | C: DOM craft, no canvas, no WebGL |
| N | Flipbook | `mockup-n/` | `themed/render_n.py` | `themed/n/` | B: canvas 2D, no WebGL |

Each style's concept, palette, type and signature are in `themed/<key>/JURY.md`. Read yours fully before writing code.

## Start from mockup J's generator, not from scratch

Copy `themed/render_j.py` to `themed/render_<key>.py` and keep its content pipeline. Rewrite the templates and the names. What must be kept exactly as J does it:

- **Data prep:** the `ROOMS`/`CASE`/`BY`/`ID_ROOM` tables and project codes; the thumbnail correction block (three thumbs in live.json sit on the wrong project); `img_size()`; `ALIASES`/`alias_html()` (landing anchors for old hashes whose targets no longer exist); `XCH`/`XOF` (the three cross-references).
- **`fix_body()`:** paths gain one `../`, room-to-room links stay in the theme, demos and external links open in a new tab.
- **Every piece of text:** the hero lede and the two statistics; the three routes (who, pitch, stops with their "why"); the full index of all projects by room (title, subtitle, tier); the three cross-references; the rules (eyebrow, title, three rules); the tool schedule ("Which AI for what": eyebrow, title, lede, the first table and the "Show the other N projects" disclosure with the rest, where N is computed); the style-archive notice ("Style archive. You’re looking at: <NAME>. This site is also a running design experiment. …" with the link to `../styles/index.html`); the footer (contact line, email, copy button, GitHub, Legal portfolio, Back to top, Which AI link on room pages, Meet the cats, MLP Consulting paragraph, sign-off); per room: eyebrow, count, title, lede, the Legal glance note, every group heading and intro, every case (code, count, kickers, title, sub, lede, full body, the "ask" box), the extra "Smaller pieces" section on Business, and the next-room link.
- **Navigation contracts:** skip links ("Skip to the rooms" → `#index` on the homepage, "Skip to the projects" → `#main` on room pages); every case keeps its `id` (old links point at them); the old-hash redirect script on the homepage in exactly this form: `<script>(function(){var M = {…};\nvar h=location.hash.slice(1);…` (the link checker reads `var M = `).
- **Head:** the theme script that sets `data-theme` before first paint (light + dark, system default, saved in localStorage under `mp<key>-theme`), `color-scheme`, favicon, description.

If your concept renames something (J called the rules "General notes"), keep the original sentence somewhere on the page as well. Parity is checked mechanically.

## Hard rules (Myles's standing preferences)

- Interface text in sans-serif. (M's document body may be a serif because it is a document page; its UI, balloons and controls stay sans.)
- No blue, purple or periwinkle anywhere, including focus rings and hover glows. Take colour from the concept.
- No fake-old facsimile: no paper stains, sepia, faux letterpress, page curls, torn edges, hand-lettering fonts.
- Never write two clipped fragments as a punchy pair ("Quote first. Then the work.") in any new UI text, alt text or JS string. Write plain complete sentences. Do not edit his existing copy.
- No invented facts, numbers or quotes about him or the projects. Anything computed must be computed from the data and labelled as what it is.
- No tracked uppercase mono labels with hairline rules (the current default tell). Labels in sentence case.
- Fonts from `~/Desktop/ClaudeStuff/fonts/` (index: `INDEX.csv`), self-hosted as woff2 in `themed/<key>/fonts/` and copied to `mockup-<key>/fonts/` by the generator. Subset with the scratch venv: `/private/tmp/claude-501/-Users-mylesparslow-Desktop-ClaudeStuff/b57db02b-96e0-4c16-8842-0a9ea5211d3a/scratchpad/venv/bin/pyftsubset` (see how J's font was made: Latin + punctuation + arrows, `--flavor=woff2 --layout-features='*'`). Copy the font's licence file next to it.
- No CDN, no third-party script, no analytics. Everything self-hosted.
- Light and dark themes, both readable (WCAG AA 4.5:1 for small text).
- Reduced motion: no animation, everything still usable. No JavaScript: every link works, every image shows, nothing stays hidden.
- Mobile at 390 px: no horizontal scroll, nothing fixed covering content, controls reachable.
- Images sharp at their display size (use `assets/thumbs-hd/` or the full screenshots, never upscale small ones).

## Do not touch

The live site (root `index.html`, the five room folders, `assets/`), `assets/site/styles.js`, `themed/add_switcher.py`, `themed/render_all.py`, `themed/render_styles.py`, `styles/`, other `mockup-*` folders, `themed/live.json`, other builders' `themed/<key>/` folders and generators. Do not run git commands that change state (no commit, checkout, stash, reset). Do not start or kill servers. The Style dropdown and archive entry are added later by the lead; in your report, name the CSS selector the dropdown should be inserted before (an element in your top or bottom chrome).

## Serving and checking

A static server is already running on the repo at `http://localhost:8898/` (pages at `http://localhost:8898/mockup-<key>/index.html`).

1. **Parity and links:** copy `themed/check_j.sh` to `themed/check_<key>.sh`, change `mockup-j` to `mockup-<key>` (and the comment), and run `sh themed/check_<key>.sh`. It must print two PASS lines. If your design rewords a heading the ignore list does not cover, keep the original words on the page; only add an ignore pattern for wording that belongs to the Transit Map theme.
2. **Screenshots:** `node ~/.claude/skills/websiteoftheyear/scripts/shoot.mjs http://localhost:8898/mockup-<key>/<page> <out-dir> --wait 2500` for the homepage and at least legal/ and creative/: must report errors=0 and overflowX=0px for desk, mob and reduced. For a real-GPU screenshot (WebGL), use `node /private/tmp/claude-501/-Users-mylesparslow-Desktop-ClaudeStuff/b57db02b-96e0-4c16-8842-0a9ea5211d3a/scratchpad/tools/shot.mjs <url> <out.png> <w> <h> <dpr> <waitMs> <fullPage 0|1> <light|dark> <scrollY> "<x,y;x,y mouse path>"` (it launches Chromium with the Metal GPU). Look at every screenshot with the Read tool and fix what is wrong: overlaps, clipped text, empty space, unreadable text, broken images.
3. **Frame cost:** `node ~/.claude/skills/websiteoftheyear/scripts/frame_perf.mjs http://localhost:8898/mockup-<key>/index.html --no-trace` and the same for legal/: verdict must be clean (no repeated frames over 33 ms).
4. **Accessibility:** `npx -y lighthouse http://localhost:8898/mockup-<key>/index.html --only-categories=accessibility --quiet --chrome-flags="--headless=new" --output=json --output-path=<file>` and read the score; fix anything under 100 that is fixable.

## Report back (short)

Files written; the check results (parity line, links line, shoot.mjs lines, frame_perf verdicts, Lighthouse scores); the dropdown mount selector; the paths of your best desktop and phone screenshots; anything that does not match `JURY.md` and why.
