# Mockup J: "Working Drawings" (jury sheet)

Written 2026-11-20 with the websiteoftheyear skill, before the build. Source: `themed/render_j.py` + `themed/j/`; output: `mockup-j/`. The three explored directions and their shots are in `themed/directions/` (open `contact-sheet.html`).

**Concept sentence.** A portfolio built like a set of working drawings, so the layout is bordered sheets with a title strip, general notes, schedules and a drawing list; the type is single-stroke drafting lettering; the colour is ink on drafting film with one red pencil; and the motion is the drawing being built: every project appears first as an ink drawing of its own screenshot and then becomes the built thing.

**Why this one.** It comes from his own making: the hand-cranked orrery designed in code, the ring and knife models, the RSC room modeler that draws dimensioned plans, his dad's design-build trade. The grammar maps onto what the site already says: "Rules I bring to every project" are a drawing set's general notes, "Which AI for what" is a schedule (project / built with / runs on), every case study's "How it was built" is its title block, the rooms are series (L, B, C, D, R) and the project codes are drawing numbers. Rule 01 on the site is "Write the system before the thing", and a drawing before the build is that rule made visible.

**The two rejected directions.**
- *Word for Word* (close): every project starts as its own write-up, set as a block of prose, and the screenshot develops out of the text. Rejected because app screenshots are too fine to read as pictures at text size, so the plate is a wall of small prose, which he has called a dense grey wall before. One detail was kept from it: the pointer-driven reveal between a "before" layer and the built screenshot.
- *Strandfall* (far): his hanging fuse-bead sculpture; the name strung in beads you can brush, lists hanging from a rail. Rejected because it reads as pixel lettering with sprinkles unless it gets a full lighting and depth-of-field treatment, and it gives the 86 projects nothing to do: delete the hero and the concept is gone.
- Dropped before rendering: a "patch sheet" matrix of which AI did which project. 74 of the 81 "How it was built" notes name Claude, so the matrix would be one solid column.

**Tier / family / audience / job.** Tier B (DOM-first with one GL accent). Family: own (drawing set), nearest are 03 plain web and 09 argument-and-data. Three audiences (law-firm people, business owners, engineers). The page's one job: show a large body of real, working things and get each visitor to the relevant ones and to the contact address within five seconds.

**References and moves.** (1) Real construction and mechanical drawing sets: sheet border with centring marks, title block, general notes, schedules, drawing numbers by series, dimension lines. Structure only: no blueprint blue, no paper texture, no hand-lettering. (2) Lando Norris's hero as measured in `gl-techniques.md` §2: a fluid simulation whose output is the mask between two renders, with a contour on the edge.

**Sameness check** (8 knobs; differs / same).

| Knob | This build | vs Opening Act v2 | vs Opening Act | vs Reliable Rooter v2 | vs live Transit Map | vs award defaults |
|---|---|---|---|---|---|---|
| Ground | drafting-film grey-green `#f1f4f1` (dark: `#17191a`) | differs | differs | same | same | same |
| Type class | single-stroke lettering sans (National Park) | differs | differs | same | same | same |
| Weight / case | display 300, sentence case | differs | differs | differs | differs | same |
| Layout | bordered sheet: cover plate, ruled lists and schedules; rooms = sticky drawing list + sheet | differs | differs | differs | differs | differs |
| Imagery | screenshots shown first as ink line drawings of themselves | differs | differs | differs | same source | differs |
| Chrome | fixed sheet border + bottom title strip | differs | differs | differs | differs | differs |
| Motion | plot wipes and a pointer fluid, nothing else | differs | differs | differs | differs | differs |
| Signature | the pointer builds the drawing into the real thing | differs | differs | differs | differs | differs |
| **Differs** | | **8 / 8** | **8 / 8** | **6 / 8** | **5 / 8** | **5 / 8** |

Labels: small sentence-case lettering at weight 650, no mono and no tracked capitals (the first render used tracked capitals everywhere and the critique flagged it; no label is set in capitals now). The last build's labels were reversed black boxes and sentence-case mono.

**Signature.** The cover sheet's plate, which runs off the top and right edges of the sheet: the current project as an ink drawing; the pointer stirs a fluid that turns it into the built screenshot, with a red pencil line on the edge. A button does the same thing in one straight plot.

**Loader to hero.** No loader. The first drawing plots in from the left in 0.9 s, then a ghost pointer starts building it.

**Type.** National Park (OFL; `fonts/google-fonts/ofl/nationalpark` in the local library), one family, self-hosted as a 39 KB Latin subset. Sizes: 13 px, 16.5 px body, `clamp(25px, 2.7vw, 42px)` middle, `clamp(44px, 6.5vw, 108px)` display. Display weight 300, sentence case, tracking -0.022em. Body headings inside case studies use the body size at weight 650.

**Palette.** Film `#f1f4f1` (a cool tint; the first render used a warm off-white and the critique read it as the cream-and-rust default), ink `#111413`, red pencil `#d32d1b`; dark: `#17191a`, `#e9ebe5`, `#ff5b45`. The canvas reads the same CSS tokens, so the theme switch reaches the shader. Red is reserved for the plot line and build edge, the current entry in a drawing list, cross-reference marks and link hover.

**Motion.** Two curves: the plot `cubic-bezier(.65,0,.35,1)` at 0.9–1.1 s, and hard cuts for hovers. No scroll reveals, no smooth-scroll library. Persistent actor: the red pencil line. The one hard cut: hover states invert instantly.

**GL.** One technique: cursor-driven fluid, full pressure solve (`gl-techniques.md` §2), used as the reveal mask between the drawing and the screenshot. Started from `assets/gl-demos/fluid-reveal.html`: same shaders and step order, ported to plain WebGL2 so the page ships no 3D library. Layer A is not an asset: the composite shader computes the drawing from the screenshot. Two tests per pixel: distance from a blurred copy taken from the mip chain (type becomes single strokes) and a Sobel pass for faint rules, gated off where the first test already sees detail. Post chain: none; the composite is the only full-resolution pass and has nothing to anti-alias. Pixel ratio cap 2 (one full-res pass). Budget: 8 + 14 = 22 passes a frame on a sim about a quarter of the plate, at most 60 steps a second. Baked: nothing.

**Chrome.** Fixed 1 px sheet border with two centring marks; a title strip along the bottom edge holding Home, the five rooms with their letters and counts, the sheet name and the theme switch. On phones the rooms fold into a menu above the strip.

**Sound.** None.

**Mobile path.** Same content, one column. The plate stays live (touch drags paint; vertical drags scroll). Room pages: the drawing list becomes a collapsed disclosure; tables stack.

**Budget.** About 160 KB of HTML, CSS and JS (about 31 KB gzipped apart from the HTML) plus a 39 KB font and the first plate image before first interaction. No libraries, no CDN.

**A11y.** Everything is real DOM; both canvases are `aria-hidden` and sit over a real `<img>`. Skip link; in-page jumps move focus; the phone menu closes on Esc and on focus leaving; the build button is a real toggle with `aria-pressed`. Reduced motion or no WebGL2: a 2D-canvas drawing with the same button, no animation. No JavaScript: the photographs show and every link works.

**Themes.** Light and dark, system default, saved per visitor, set before first paint.

**Pages.** Cover sheet + the five rooms, all 86 projects in theme, old `/#hash` links redirected.
