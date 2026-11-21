# Mockup K: "Liner Notes" (jury sheet)

Written 2026-11-21. Source: `themed/render_k.py` + `themed/k/` (k.css, k.js); output: `mockup-k/`. Checks: `python3 -I themed/check_k.py`.

**Concept sentence.** The portfolio pressed as a record label's catalogue: the five rooms are five records (an EP, LPs and double LPs, by track count), every project is a numbered track on a side, and the homepage opens on a crate of sleeves you flip through.

**Why this one.** It comes from his own taste and making: hip-hop (Alchemist, Knxwledge, Freddie Gibbs, MF DOOM), beats and songs made with Suno, and the way rap credits name the producer on every track. The grammar maps onto what the site already says instead of decorating it:

| Site content | Record grammar |
|---|---|
| Five rooms | Five records, catalogue numbers MPK-001 to MPK-005; format by length (Design = EP, Legal and Research = 2×LP) |
| 86 case studies | Tracks numbered by side, eight to a side (A1 to A8, B1 ...), as on a real LP side |
| "How it was built" (on 78 projects) | The credits panel; it already says who produced what (Claude, ChatGPT, Codex, Suno) |
| The three linked project pairs | Samples: one track lifting a part from another, across records |
| Three routes for three visitors | Three compilations, one per kind of listener |
| Rules I bring to every project | Liner notes |
| Which AI for what | Personnel |
| Legal's practice-area groups | Movements |
| Style archive notice | Other pressings |

**Rejected directions.**
- *Contact sheet* (close): every project as a frame on a film contact sheet with grease-pencil picks. Rejected: The Museum and Working Drawings already use the "archive of plates" grammar, and a contact sheet gives the 86 projects no order beyond a grid.
- *Trading floor* (far): rooms as tickers on a terminal tape. Rejected: it makes the work read as numbers, and invites "stats" the site doesn't have.

**Tier / audience / job.** DOM-first, CSS 3D only (no WebGL, no libraries). Same three audiences (law-firm people, business owners, engineers). One job: show a large body of real, working things and get each visitor to the relevant record, track and contact address fast.

**Sameness check** (differs / same vs the newest versions).

| Knob | This build | vs Working Drawings | vs Transit Map | vs Orbit | vs The Museum |
|---|---|---|---|---|---|
| Ground | vinyl black headers + neutral grey pages, light and dark | differs | differs | differs (night, but no sleeve grey) | differs |
| Type | Anybody, driven by its width axis (condensed 56–72 for display, 150 for "AI.") + Instrument Sans | differs | differs | differs | differs (Archivo condensed, fixed width) |
| Colour | one label colour per record, only on its disc label, sleeve band, dot and current track | differs | same idea (line colours) | differs | differs |
| Layout | crate, catalogue, sides and a sticky tracklist | differs | differs | differs | differs |
| Imagery | screenshots as sleeve art (2×2 grid), never tinted | differs | differs | differs | differs |
| Chrome | black top bar with record chips; a small turntable "Now playing" deck | differs | differs | differs | differs |
| Motion | sleeves flip, records slide out and spin; the deck turns with scroll | differs | differs | differs | differs |
| Signature | a 3D crate of sleeves | differs | differs | differs | differs |

**Signature.** The crate (homepage hero): five sleeves standing in a bin, viewed from just above. The front sleeve stands up and its record slides out and spins; the ones behind show their catalogue numbers. Flip with the arrow buttons, arrow keys, the mouse wheel over the crate (the page scrolls normally once the crate is at either end), a touch drag, or by clicking a sleeve behind (first click brings it forward, the second opens it). One slow demo flip runs 1.6 s after load unless the visitor has already touched the crate. On phones it becomes a swipe row of sleeves with the records peeking out.

**Second signature (room pages).** A small turntable fixed bottom right: the record turns as you scroll, the tonearm moves inward with reading progress, and it names the track on screen ("B2 Citation Gate"). Tapping it opens the tracklist. On narrow phones it shrinks to just the platter.

**Type.** Anybody (OFL, Google Fonts, variable wdth 50–150 and wght 300–900) for display; Instrument Sans (variable wdth 75–100) for reading. Sizes: 13 px labels, 17 px body, `clamp(24px, 2.5vw, 36px)` middle, `clamp(40px, 5.6vw, 92px)` section heads, `clamp(54px, 7.6vw, 136px)` hero. Labels are sentence case, weight 600, no tracked capitals and no mono. The hero's "AI." widens from width 50 to 150 on load (reduced motion: set wide from the start).

**Palette.** Light: page `#f2f2ef`, ink `#121211`, dim `#5a5a54`. Dark: `#0f0f0e`, `#efeee8`, `#a3a29b`. Headers and footer stay vinyl black `#0c0c0b` in both themes. Label colours: Legal `#ff4d2e`, Business `#ffc21a`, Creative `#2bc770`, Design `#5b93ff`, Research `#c98bff`, always with black text on them.

**A11y.** Real DOM everywhere; the crate is a list of links with a live caption ("Front of the crate: Legal, 1 of 5"), only the front sleeve is in the tab order and arrow keys move it; sleeves and discs are decorative (`aria-hidden`) with text alternatives. Skip link; in-page jumps move focus; the records menu closes on Esc and on focus leaving; visible focus rings; `prefers-reduced-motion` stops every spin, flip transition and the demo flip. Without JavaScript every link works and the crate shows as a static stack.

**Themes.** Light and dark, system default, saved per visitor (`mpk-theme`), set before first paint.

**Pages.** Catalogue + five records, all 86 projects, old `/#hash` links redirected (73).

**Checks run (2026-11-21).**
- `check_k.py` parity: 0 text blocks of the live pages missing (Transit Map's own wording, such as station codes and "You are here", is listed and re-worded).
- `check_k.py` links: 1009 local refs across 6 pages, 73 redirects, 0 broken.
- Playwright: no console errors on any page; crate buttons, arrow keys, Home/End, wheel, click-behind and the wheel hand-off to the page all work; A–Z catalogue builds 86 rows; theme toggle; `/#vigilmark` redirects to Legal; the deck names the track on screen.
- Screenshots looked at: home 1440 and 390, crate at two positions, Legal 1440 (full page) and 390, Legal mid-page in dark, Creative 390 in dark. No horizontal overflow at 390 or 1440.

**Not done.** Not checked on a real phone or in Safari (CSS 3D hit-testing differs between engines; the crate sets `pointer-events` so only sleeves take clicks). No sound, on purpose.
