# Mockup B: jury sheet (/websiteoftheyear)

Different from mockup A on every axis: A is dark, quiet and index-first; B is light, warm, editorial and loud in type.

Tier **B**, DOM-first, no WebGL. Primary pattern: **Zhenya Rynzhuk art-director folio**. Secondary: **Pangram Pangram sticky card stack**. Motion borrowed: Lando brand-shape mask exit, Zhenya pointer hard-cut, Locomotive scramble, Hello Monday liquid curtain, Mr. Pops/Lando colour bands.

- **Concept:** "A workshop with five rooms": the five areas of work (Legal, Business, Creative, Design & 3D, AI & research) are five stacked cards, each its own room with its own ground colour.
- **Signature interaction:** the hero portrait frame. Moving the pointer across the screen hard-cuts (0 ms, no tween) through project thumbnails, one per x-slice, and the caption under the frame names the project shown. On touch or idle it steps every 900 ms. Clicking the frame opens the shown project.
- **Loader → hero:** a stone screen with a big serif "M" drawn in red. The "M" becomes a clip-path mask that scales from its own size to cover the screen in 0.45 s expo-out, revealing the hero. The hero headline then builds word by word (Locomotive), at 70 ms per word and 0.9 s each.
- **Type:** Fraunces (display serif, variable; opsz high, SOFT 50, WONK 1 for the italic) + Hanken Grotesk (UI/body), both Google Fonts. Sizes: 12px UI (uppercase, +.1em), 17px body, middle `clamp(26px,2.6vw,40px)`, display `clamp(72px,12.5vw,240px)`, with a giant initial letter per room at `clamp(160px,28vw,520px)`, which reuses the display face.
- **Palette and themes:** three themes, **Light, Dark, Red**. No saved choice follows `prefers-color-scheme` (light or dark); the toggle cycles Light → Dark → Red and its label names the current theme ("In light" / "In dark" / "In red"). The choice is saved in `localStorage` (`mpb-theme`, in try/catch) and applied by a tiny head script before first paint on every page, so there is no flash. With JS off the CSS still follows `prefers-color-scheme`.
  - **Light:** paper `#ebe5da`, ink `#1b1a18`, red `#f23c0d`. Rooms: legal `#f3d7cf` pink, business `#cdd6c4` sage, creative `#efdfa6` butter, design `#d3dbe6` sky, research `#ddd5e8` lilac; ink text on all.
  - **Dark (designed, not inverted):** ground `#141312`, text paper `#ebe5da`, accent lifted to `#ff5a30` (the spec red is only 4.8:1 on the dark ground and reads hot; `#ff5a30` gives 5.97:1). Rooms keep their hue at low lightness: pink `#432a26`, sage `#2a3426`, butter `#403718`, sky `#26303f`, lilac `#322a43`, with paper text. Menu ground `#0b0a09`; loader stone `#1f1d1b`. Thumbnails and screenshots are unchanged.
  - **Red:** ground `#bf2400` with paper text (4.83:1), the rooms keep their light grounds and ink text; text that would have been a tint of paper (captions, kinds) is full paper because tints of paper on this red fall under 4.5:1.
- **Motion:** curves expo.out `(.19,1,.22,1)` and in-out `(.77,0,.175,1)` only. Exits ≤ .35 s, arrivals .8–1.2 s. Line-mask reveals, 90 ms stagger. Scramble on corner-label hover (pointerenter only, with aria-labels). The persistent actor is the red "M": it is the loader, then a small fixed mark top-left, then it wipes into the curtain on page transitions. The one hard cut is the hero portrait.
- **Chrome (v3):** one opaque strip across the top, in the ground colour of whatever section sits under it (page ground, or the room's own colour). TL pill: red "M" + "Myles Parslow · Business" (the room name follows the section in view; mobile shows the short name, "Business"). TR: theme toggle + "Menu". The two fixed bottom pills are gone: "48 projects · 5 rooms" now sits in the hero, and the room label lives in the TL pill. Content scrolls beneath the strip, never beneath a loose pill, so nothing fixed overlaps readable text at any width.
- **Rooms (sticky card stack):** each room card is ≥100svh, `position:sticky`, and the previous card scales to .92 and dims as the next arrives (Pangram). Card layout: the giant initial letter (L, B, C, D, R) on the left; room title + count; then that room's projects as a two-column list of stacked two-line titles (Locomotive: name on line 1 in the middle size, sub on line 2 in UI size), each with a small thumbnail that sharpens from a pixel mosaic on hover (Bizarro/Locomotive). "Open room →" links to the area page.
- **Also on the page:** the rules (01–03) as a big serif manifesto on the paper ground; the "right tool for each job" rows (keep all 43; 6 visible + "Show all"); footer with click-to-copy email, GitHub, Legal portfolio.
- **Transitions:** following a link to an area page or a project, a red liquid curtain with a wavy top edge rises in .35 s, then navigates.
- **Sound:** none.
- **Mobile:** the rooms stay sticky but the scale-down is skipped; the initial letter shrinks above the title; the hero frame steps automatically; no empty band.
- **Budget:** < 1 MB before interaction; thumbnails lazy, except the 10 used by the hero frame.
- **A11y:** real headings per room, all 48 project links in DOM order, h1 accessible name intact, theme toggle as a real button whose aria-label names the current and the next theme, reduced motion → no loader, no stack scaling, no hard-cut auto-advance, and everything visible.

## In-theme room pages (added 2026-11-05)

`themed/render_b.py` (stdlib Python, re-runnable) writes `mockup-b/<slug>/index.html` for legal, business, creative, design and research from `themed/cases.json`. It reads the homepage for the shared menu, chrome, fonts and pinned script tags, so those cannot drift. CSS and JS are shared: theme tokens, chrome, menu, curtain and reveals are in `b.css` / `b.js`; `rooms.css` holds the case-study type system and `rooms.js` only the before/after sliders.

- **Room header** on that room's ground: giant initial letter, title, count, the area lede, then an index of the projects (number, stacked two-line title with the project's own tagline, thumbnail), each linking to `#<case id>` on the same page.
- **Each case is an editorial chapter** with `id` = case id (deep links such as `legal/#conflara` land on it, offset below the strip by `scroll-margin-top`, and re-settle after fonts and load): "03 / 16" counter, kind and group in the rail, display-serif title, tagline, summary as lede, then the body fully styled: block, cols, made, links (demo pills with an arrow), shots, wide, grid3, stats (ruled strip of serif numbers), gallery, compare (slider kept, keyboard works through the range input), video (controls, poster, `preload="metadata"`), figure/figcaption, lists, books/book/cover/lead-text, reels, logline, tags/tag, facts, flow (numbered pipeline), note, piece, kind, count, more, sub-case. Portrait phone screenshots are capped at 360 px; every image has width and height, lazy loading and `max-width:100%`.
- **Paths from `mockup-b/<slug>/`:** media → `../../assets/…`; `demos/…` → `https://mylesparslow.com/demos/…` in a new tab (they are separate apps); same-site cross-room links stay in the theme; other external links open in a new tab.
- **Page transitions:** the wavy red curtain rises on leave (0.35 s) and, on the next page, the page opens covered and the curtain's lower edge lifts away (0.7 s, in-out). No loader replay on room pages. Previous / next room panels (each in its room colour) and a "Back to the rooms" link close every page. Reduced motion and JS off: no curtain, no reveals, everything visible; the index, chapters and prev/next work as plain links.
- **Homepage links** all resolve in-theme (`legal/#conflara`, `business/`, hero frame, menu, "Open room →"), and the old-URL redirect script (`/#conflara` → `legal/#conflara`) now lands on the in-theme page.

### The seven projects without a screenshot

Argument X-ray and Boardroom of One use the new real screenshots (`assets/thumbs-hd/xray.jpg`, `boardroom.jpg`). The other five (Marketing Studio, TikTok on autopilot, Money Desk, ME/CFS evidence map, Guideline citation audit) get a typographic tile: the project name in italic Fraunces, two lines, on a tint of the room colour, with a small room letter in the corner. The type size scales with the thumbnail width and with the longest line, so it is still readable at the 84 px mobile size. No invented imagery.

### Contrast (computed with the WCAG 2.x formula; `color-mix` tints replicated in sRGB)

All body and UI text passes 4.5:1 in all three themes; the only sub-4.5 pairs are graphics and 72 px display italic, which need 3:1 and pass. Chrome pills take the room's own foreground when the strip is in a room colour, which is what keeps the pills legible in Red mode.

| Pair (foreground on background) | Need | Light | Dark | Red |
|---|---|---|---|---|
| Body text on page ground | 4.5:1 | 13.87 | 14.80 | 4.83 |
| Muted text (captions, kinds, stat labels) on page ground | 4.5:1 | 6.53 | 8.41 | 4.83 |
| Code chip text on 10% tint | 4.5:1 | 11.43 | 11.72 | 6.04 |
| Book card text on 6% tint | 4.5:1 | 12.38 | 12.99 | 5.47 |
| Book card muted text on 6% tint | 4.5:1 | 5.83 | 7.38 | 5.47 |
| Inverted chips and hover (page ground on text colour) | 4.5:1 | 13.87 | 14.80 | 4.83 |
| Loader count on stone | 4.5:1 | 11.90 | 13.40 | 6.04 |
| Accent on ground (display italic "with AI.", 72px+ text; 3:1) | 3.0:1 | 3.09 | 5.97 | 4.83 |
| Menu text on menu ground | 4.5:1 | 13.87 | 15.78 | 13.87 |
| Menu accent on menu ground (hover, 36px+ text; 3:1) | 3.0:1 | 5.60 | 6.37 | 5.60 |
| Room text | 4.5:1 | 11.60 to 13.06 (5 rooms) | 9.42 to 10.82 (5 rooms) | 11.60 to 13.06 (5 rooms) |
| Room secondary line | 4.5:1 | 6.66 to 7.18 (5 rooms) | 6.44 to 7.23 (5 rooms) | 6.66 to 7.18 (5 rooms) |
| Chrome pill text on room strip | 4.5:1 | 11.60 to 13.06 (5 rooms) | 9.42 to 10.82 (5 rooms) | 11.60 to 13.06 (5 rooms) |
| M mark (graphic) on room strip | 3.0:1 | 3.76 to 4.23 (5 rooms) | 3.80 to 4.37 (5 rooms) | 3.76 to 4.23 (5 rooms) |
| Chrome pill text on page-ground strip | 4.5:1 | 13.87 | 14.80 | 4.83 |
| M mark on page-ground strip (graphic; 3:1) | 3.0:1 | 3.09 | 5.97 | 4.83 |

The typographic tiles put ink (or paper in Dark) on a 15% tint of the room colour; they are decorative (`aria-hidden`) and sit next to the real title, but they measure 8.69:1 or better in Light and Red and 6.29:1 or better in Dark.

## Self-judge (built 2026-11-05)

Contrast (computed): ink #1b1a18 on paper #ebe5da 14:1; ink on the five room grounds 11.6 to 13.1:1; paper on the red-mode ground 4.83:1 (AA). The spec red #f23c0d fails paper-on-red body text (3.09:1), so red mode uses ground #bf2400 and the accent italic turns paper. #f23c0d stays only for the M mark, the display italic "with AI." and the curtain (large text, 3.09:1 passes the 3:1 large-text bar).

| Axis | Score | Evidence |
|---|---|---|
| Design (40%) | 8 | Two families (Fraunces, Hanken Grotesk). Sizes: 12 UI, 17 body, mid 26 to 40, display 72 to 240, plus a half-display "statement" size for the rules (one more step than the sheet planned) and the room letter. Checked at 1440x900 and 375x812; no overflow, no collisions after fixes. |
| Usability (30%) | 8.5 | Work is one scroll away and every project link is in the room cards; menu has focus trap, Esc, inert page (tested: 25 Tabs stay inside, focus returns to Menu). Native scroll plus Lenis; no scroll-jacking. The fixed bottom pills are gone and the top pills sit on an opaque strip, so nothing fixed overlaps readable text (checked at 375, 768, 1440 and 1920 wide, mid-scroll, on the homepage and a room page). Every one of the 48 homepage links lands on its chapter in the in-theme room page. |
| Creativity (20%) | 8 | Pointer hard-cut hero frame verified: x=120, 720, 1320 gave Conflion, Hollow Hours, AgentForge with the caption updating. M-shaped mask exit and sticky room stack with scaled, dimmed previous card verified in screenshots. |
| Content (10%) | 8.5 | All 48 real projects, real About sentences, real stats and 43 tools rows; no lorem. All 48 case studies now have a full in-theme chapter (copy from the live pages, unedited). The five room blurbs are my own one-liners built from the project subtitles. |
| Dev | 8.5 | 0 console errors, 0 horizontal overflow (desktop, mobile, reduced). SRI on all three scripts. JS-off and reduced-motion show everything (JS-off screenshot checked). Thumbs under 300 KB before interaction. Room pages: 0 console errors and 0 horizontal overflow at 375, 768, 1440 and 1920 (the 1920 creative page timed out on the local Python server only because it does not serve video ranges; not a page fault). All 189 local media URLs on the room pages return 200. FPS and Lighthouse not measured. |


Added 2026-11-05: three themes (Light, Dark, Red) with every text pair at or above 4.5:1; Design and Creativity unchanged at 8 (the dark palette and the curtain arrival are nice, but they are polish on the same concept, not a new idea).
