# Mockup O: "Civitas" (jury sheet)

Written 2026-11-23 before the build. Myles's ask: "a new version of the portfolio that's like a medieval map with each of the sections assigned to an important building in the medieval city. should be all medieval styled with the margin illustrations and illuminated letters and all that stuff, medieval sketch map style on the map itself. Make it a map of a city". Shared rules for content, checks and what not to touch: `themed/v4/BRIEF.md` (read it; everywhere it says `<key>` use `o`, theme storage key `mpo-theme`).

**Concept sentence.** The portfolio as a walled medieval city drawn in the hand of a 16th-century bird's-eye city view: every section of the site is an important building, the home page is the map of the city, and every building opens onto a manuscript leaf with an illuminated initial, rubricated headings and drawings in the margin.

## References studied (in `themed/o/refs/`, licences in `refs/CREDITS.txt`)

1. **Braun and Hogenberg, Civitates Orbis Terrarum, "Colonia Agrippina" (Cologne), 1575** (`sm-dr_vol-i-38-colonia…jpg`, public domain). What it does: the city is a tilted bird's-eye view inside a heavy wall ring with round towers at even intervals; the river runs along one side with boats; the city fabric is hundreds of tiny house blocks drawn as little elevations (gable fronts, a roof plane, a door), packed along curving streets; the big buildings (cathedral, churches, town hall) are drawn several times larger than houses with their towers standing up; fields and orchards outside the wall are drawn as hatched strips and dotted rows; the title is a strapwork cartouche on a ribbon; compass words ("Oriens", "Occidens") are lettered on the edges; small figures in costume stand in a corner; everything is pen line on white with almost no fill. Take: the projection (tilted, elevations), the wall ring with towers, the dense small house fabric, the scale jump for the important buildings, the cartouche, the lettered directions, the hatched fields. Do not take: the engraved cross-hatching density everywhere (keep it lighter), the coats of arms.
2. **Bible leaf, Proverbs, c. 1275, with historiated initial P (Cleveland Museum of Art)** (`sm-clevelandart-2008…jpg`, public domain). What it does: a two-column text block on a ruled grid; a running title across the top in alternating red and blue capitals with pen flourishes; a historiated initial (a scene inside the bowl of the P) with a long bar border running the full height of the column that ends in a curl and a small beast; red (rubric) for the opening words and headings; generous margins, wider at the bottom and outside.
3. **Psalter leaf with historiated initial D, c. 1310 (Cleveland Museum of Art)** (`sm-clevelandart-1999…jpg`, public domain). What it does: a single column of text with one large initial in a gold-framed square of lapis and rose, a vine bar along the left edge ending in ivy curls at top and bottom, small two-line initials in alternating gold and blue on each verse, and line-fillers (painted bars with zigzags and knots) filling the end of short lines. Take: the bar border with ivy terminals, the alternating small initials, the line-fillers as section dividers.
4. **Nuremberg Chronicle, 1493, folio XII** (`sm-mma_registrum…jpg`, *personal-use only, reference only, never shipped*). What it does: woodcut figures in boxes down both margins beside the text block; a single woodcut initial; a running head "Secunda etas mundi … Folium XII". Take: folio numbering in the running head, the idea of figures in the outer margin. Do not copy any figure.

Every drawing in the site is drawn new for this site in SVG. Nothing from the scans is traced or shipped.

## Building assignments (every section has one; none dropped)

| Section | Building | Why |
|---|---|---|
| Legal (room) | **The Castle and Assize Hall** on the hill: keep, curtain wall, a great hall where the court sits | The largest room (33 projects) gets the largest building; medieval courts sat in the castle hall |
| Business (room) | **The Guildhall** on the Market Square, with the market stalls and the market cross in front | Where trade, books and fees were kept |
| Creative & games (room) | **The Cathedral**, west front with two towers, rose window, a choir | Songs, plays, pictures and stories: the cathedral was the city's theatre, music room and picture book |
| Design & 3D (room) | **The Masons' Lodge** beside the cathedral works, with a crane and scaffolding on the unfinished tower | The people who designed and built things in three dimensions |
| AI & research (room) | **The Scriptorium and College** with a cloister and a library tower | Reading, copying, reference works and study |
| Routes ("Where to start", home) | **The three gates** of the city, one per route, each with its road coming in | Each kind of visitor enters by a different gate |
| The full index (home) | **The map itself**, and a plain "Survey of the city" list | The second, plain way in |
| Cross-references (home) | **The bridges** over the river | Projects that share a part are joined like two banks |
| Rules (home) | **The Market Cross**, where the town charter was read out | The rules the city lives by |
| Tool schedule, "Which AI for what" (home) | **The Mint**, where every coin is struck with the maker's mark | Which tool made which part |
| Style archive notice (home) | **The Old Town**, a ruined earlier wall line outside the present walls | The earlier versions of the site |
| Contact (footer) | **The Harbour** with a ship and the harbour master's house | The way out of the city: send word |

Each building on the map is a link (to the room page, or to the home section's anchor), with a visible lettered label on a small ribbon (banderole) and a keyboard focus ring.

## Tier, family, signature

- **Tier C+**: SVG and DOM. No WebGL. The map must read fully with no JavaScript (it is an inline SVG with real `<a>` links). JavaScript adds only the pointer effect and pan/zoom on phones.
- **Family**: own (city view + manuscript), nearest 02 exhibition index.
- **Signature**: the city map. Pointing at or focusing a building lifts its drawing slightly, washes it in its colour, inks its banderole in vermilion and shows a small manuscript-style note beside it ("The Castle and Assize Hall · Legal · 33 projects") and a "Enter" link. That is the one pointer effect. A second, gentle one is allowed: the map tilts a few degrees with the pointer on desktop. Nothing else moves on pointer.
- **Phones**: the map is shown at a readable scale inside a frame the visitor can pan with a finger (CSS overflow scroll with scroll-snap to each building, not a custom gesture engine), plus "Previous building / Next building" buttons that walk the route through the buildings; the plain "Survey of the city" list sits directly under the map.

## The map (drawn by the generator)

Write a Python module `themed/o/citymap.py` that builds the SVG deterministically (seeded random), so the map is code, not an image file. Drawing rules:
- Projection: tilted bird's-eye like the Cologne view. Ground plan squashed vertically (about 0.6), buildings drawn as elevations standing up from their footprint.
- Pen line: iron-gall ink at 1–1.4 px for important buildings, 0.6–0.8 px for houses, with a slight seeded wobble on long lines (no perfect geometric look, no wobble so strong it looks like a cartoon). `vector-effect: non-scaling-stroke` where needed so lines stay fine when the map is scaled.
- Washes: flat, light, transparent fills (mix-blend multiply): roofs in a pale vermilion wash on some houses, verdigris on church roofs and copper spires, a pale ochre on the streets and squares, the river in a pale verdigris with horizontal ripple strokes. No gradients, no textures, no drop shadows.
- City: an irregular oval wall ring with round towers every ~40–60 px (along the path) and three gatehouses where the three roads come in; a river along one side with the harbour, two bridges and boats; a street network (a main street gate to gate, a market square, curving lanes); 300–600 small houses as little gable-front blocks packed along the streets (seeded sizes and orientations, never overlapping the important buildings or the streets); gardens and orchards inside the walls as dotted rows; outside the walls hatched fields, a few trees drawn as lollipop canopies, the ruined old wall line (Old Town) as a dashed broken wall with a fallen tower.
- Important buildings: drawn by hand-written SVG path functions, each 4–8× a house, recognisable at a glance: castle with keep and crenellations on a hill (hatched slope), cathedral with two west towers and a rose window, guildhall with arcade and steep roof and a clock, masons' lodge with a wooden crane and scaffolding against the cathedral's unfinished north tower, scriptorium and college with a cloister court and a library tower, the mint with a chimney and anvil sign, the market cross on steps, the harbour with a quay, a crane and a ship.
- Lettering: a banderole (ribbon scroll) over each important building with its name in the display face; street and river names in small italic in the body face along the curve (`textPath`); the city's name in a strapwork cartouche ("Civitas Mylesiana" is fine as the map's title, followed by the real title "Myles Parslow makes things with AI." in the cartouche's text); direction words "Oriens", "Occidens", "Septentrio", "Meridies" on the four edges and a wind rose in one corner; a scale of paces in the other.
- Margin of the map: a ruled double border like the Cologne plate. Two small figures may stand in the bottom corner (a scribe and a mason), drawn as simple pen figures.
- Size: one viewBox about 1600×1000; the SVG must stay under ~400 KB.

## Manuscript leaves (every page apart from the map: home sections below the map, and all five rooms)

- A ruled text block (light ruling lines visible in the margins, like a prepared leaf), one column for body text at about 64–68 characters, generous margins: inner and top narrower, outer and bottom wider (about 2:3:4:6 in the classic canon, scaled to screen).
- A running head on every leaf: the building's name at left and a folio number at right ("Folium xii"), set in red and blue alternating capitals like reference 2.
- Each case study opens with a **historiated or illuminated initial**: the first letter of its lede drawn by the generator as an SVG square (gold frame, lapis or rose ground with a fine white pen pattern) with the letter set in the display face, three to four text lines tall, and a vine bar extension down the margin ending in ivy-leaf curls (reference 3). Make a small set of initial designs and rotate them; never the same two in a row.
- Section and project headings rubricated (vermilion), small two-line initials on group intros in alternating gold and lapis.
- **Margin drawings**: a set of 10–16 original pen drawings in the manner of English psalter marginalia, used sparingly (one per case study at most, placed in the outer margin, never over text): a snail facing a knight, a cat playing a lute (his cats and cat songs), a hare with a book, a rabbit scribe, a heron, a fox in a hood, a dragon with a vine tail, a pointing hand (manicule) beside a project's main link, a monkey with a mirror, a goose with a pen. Simple, confident pen line, flat wash in one or two colours. On phones they move into the text flow between sections at small size, or are hidden.
- Line-fillers (painted bars with zigzag and knot, reference 3) as the dividers between case studies.
- Figures (his screenshots) sit inside a thin double ruled frame with a red caption label ("Figura ii") above the caption text. Keep screenshots sharp and full colour; do not tint them.
- The "How it was built" note on each case: a boxed rubric "Quomodo factum est" heading **plus** the original words "How it was built" (parity needs them).

## Type (from `~/Desktop/ClaudeStuff/fonts/INDEX.csv`, all OFL, self-hosted, licence files copied)

- Display, banderoles, running heads: **UnifrakturMaguntia** (textura blackletter), used only at large sizes and for short labels.
- Initial letters inside the illuminated squares: **Cardo** bold capitals or **Uncial Antiqua** (pick the one that reads better in the square; Lombardic/uncial forms are the period-correct choice for initials).
- Body text of the leaves: **Cardo** (a scholarly old-style designed for medievalists) at 19–20 px, line height 1.55. If Cardo's weights are too few, **EB Garamond**.
- Interface text (buttons, the theme switch, the Style menu, the phone controls, form-like UI): **Alegreya Sans** (humanist sans that pairs with the calligraphic faces). Myles wants interface text in sans.
- Map street and river names: Cardo italic.
- Never Papyrus-like novelty faces, never MedievalSharp, Almendra, Pirata One or Jacquard (pixel).

## Palette

- Light (default): vellum `#f5f0e4` as a flat colour (no image, no stains, no vignette, no "aged" edges), iron-gall ink `#2b231c`, dim `#5e5346`, ruling `#d9cfbb`, vermilion (rubric) `#b8321c`, verdigris `#3d7a66`, lapis `#1f3f86` (used only inside initials and small two-line initials, never for links, buttons or focus), gold `#b08a2e` (initial frames, small initials; a flat colour, no metallic gradient).
- Dark: night `#1a1713`, text `#ece4d2`, dim `#b3a993`, rubric `#e2603f`, verdigris `#6fb59b`, gold `#d1ac52`; the map in dark keeps light lines on the night ground (invert the ink, keep washes very low).
- Focus ring: 2 px vermilion with 2 px offset. Links: ink with a vermilion underline. No purple, no periwinkle.

## Chrome

A slim top bar on the vellum: "Myles Parslow" at left (home), the five buildings as text links with their counts ("Castle · Legal 33"), the theme switch at right with `id="theme"` (the Style dropdown is inserted before it). On phones: name, a "Buildings" menu, theme switch.

## Motion

Only the two pointer effects above. No scroll animation, no smooth scroll, no page-load animation. Reduced motion: no tilt, no lift transition (instant highlight).

## Accessibility

- The SVG map has a `<title>` and `<desc>`; every building link has an accessible name ("The Castle and Assize Hall: Legal, 33 projects"); decorative houses, fields and drawings are `aria-hidden`.
- The "Survey of the city" list right after the map gives every building and every project as plain links.
- Illuminated initials are decorative: the real first letter stays in the text for screen readers and copy-paste (draw the initial as an `aria-hidden` element and visually hide the first letter of the text, or render the drop letter with CSS so the text is unchanged). Parity must still pass.
- Blackletter only for short display text; anything a visitor must read is in Cardo or Alegreya Sans.

## Sameness check (vs the last three ledger builds and the award defaults)

vs Flipbook (light box, condensed grotesk, exposure sheet, film frames), Redline (white document, Tinos, comment margin), Tesserae (dark grout, Clash Display, WebGL wall): ground (vellum), type class (blackletter + old-style), layout (city map + manuscript leaves), imagery (drawn map and marginalia), chrome, motion (two pointer effects only) and signature (buildings as doors) all differ. vs award defaults: everything but the DOM-first stack differs.

## Hard "no" list (Myles has rejected these)

Fake-old: no brown parchment photo, no coffee stains, no burnt or torn edges, no drop shadows under "paper", no page-curl, no wax seals as decoration, no Papyrus-style fonts, no sepia filter on screenshots, no "Ye Olde" spellings in UI text. Refined: real manuscript proportions, clean vector line that holds at 2×, flat washes. Keep his copy as it is.
