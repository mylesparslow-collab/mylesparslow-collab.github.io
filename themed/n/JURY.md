# Mockup N: "Flipbook" (jury sheet)

Written 2026-11-21 before the build. Shared rules: `themed/v4/BRIEF.md`.

**Concept sentence.** A portfolio shot like a stop-motion film: the layout is an exposure sheet of numbered frames beside a light-box viewer; the type is a condensed grotesk with big frame numbers; the colour comes from the light box and the animator's onion skin (the previous frame tinted green, the next one tinted pink); the motion is stepped at 12 frames a second, the rate stop-motion is shot at.

**Why it is his.** His claymation explainers, the clay ads for his dad's company, "Ozymandias in clay", the pixel cat fairytales and the Suno music videos are all frame-by-frame work. The site's 87 projects become 87 frames of one short film.

**Tier / family.** Tier B: canvas 2D for the viewer, no WebGL. Family: own (exposure sheet), nearest 09 data.

**References and moves.** (1) The animator's exposure sheet (X-sheet / dope sheet): a tall ruled table, one row per frame, frame numbers down the left, columns for action, dialogue and camera. (2) Stop-motion capture software (Dragonframe): a viewer with onion skinning, a frame counter, a timeline strip of thumbnails, play / step buttons. Structure only: no app chrome imitation, no film grain, no sprocket holes, no fake paper.

**Signature.** The flipbook. Frame 001 to 087 is every project in room order. A sticky light-box viewer shows the current frame's screenshot; scrolling the exposure sheet steps the viewer frame by frame (it holds each frame, never cross-fades), with onion skin: the previous frame ghosted in green and the next in pink at low opacity, visible for 2 frames after each change. A Play button plays all 87 frames as a 7-second film at 12 fps (pausable, loops once, stops on the frame you were on), and the timeline strip under the viewer is a scrubber: drag across it to flip through the projects. Clicking the viewer or a row opens the project.

**Type.** One family: Sofia Sans (OFL, `~/Desktop/ClaudeStuff/fonts/google-fonts/ofl/`: Sofia Sans Condensed variable for display and numbers, Sofia Sans for body). Frame numbers in Sofia Sans Condensed 800 with tabular figures; display clamp(52px, 7.5vw, 128px) at 800, sentence case; body 17 px at 400; labels 13 px at 600, sentence case. No mono.

**Palette.** Desk `#d6d6d2` (mid grey), light box `#fbfbf9` (the glowing panel the viewer and sheet sit on), ink `#151515`, dim `#5a5a56`, ruling `#c4c4bf`. Onion skin: previous `#1fbf63` (green), next `#ff4f8b` (pink); the same two colours mark the current row in the sheet (a green left bar) and the playhead on the strip (pink). Dark theme: desk `#101010`, light box `#1b1b1b`, ink `#eeeeea`. No blue or purple.

**Layout.** Homepage: a title block across the top of the sheet ("Myles Parslow makes things with AI.", the lede, the two statistics as "Production notes"), then a two-column work area: left, the exposure sheet (one row per project: frame number, scene = room letter and name, action = title, dialogue = subtitle, a tier mark, with each room starting a new scene band); right, the sticky viewer (16:10 light box, frame counter "Frame 012 of 087 · Scene L", the Play button, step back/forward, and the thumbnail strip). Below: routes ("Three ways through the film"), cross-references, rules, tool schedule, archive notice, footer. Room pages: the room is a scene; a scene header with the same viewer showing that scene's frames only; then each case in a readable column (about 760 px text), headed by its frame number, title and subtitle, its full body below.

**Motion.** Stepped only: the viewer changes frame instantly; any CSS transition uses `steps(2)` or `steps(3)`. Play at 12 fps with `requestAnimationFrame` and a clamped clock. No smooth scroll, no fade-up reveals.

**Chrome.** A slim transport bar at the bottom of the window: "Myles Parslow" (home), the five scenes with frame ranges ("L 001–032"), the current frame number, the theme switch. The Style dropdown will be inserted before the theme switch.

**Mobile.** The viewer stacks above the sheet at full width and stays sticky at the top at about 30 vh; the strip scrolls horizontally; Play stays available.

**A11y.** The viewer canvas is `aria-hidden` and duplicated by a real `<img>` for no-JS; the sheet rows are real links; the frame counter is a polite live region only while scrubbing stops; Play is a button with `aria-pressed`. Reduced motion: no autoplay, no onion animation, Play steps one frame per click instead.

**Sameness check.** vs Working Drawings: type (condensed grotesk vs lettering sans), weight (800 numbers vs 300), layout (exposure sheet + sticky viewer vs sheet + drawing list), imagery (screenshots as film frames vs line drawings), chrome (transport bar vs title strip), motion (stepped 12 fps vs plot wipes), signature all differ. vs Transit Map, Liner Notes and the award defaults: layout, imagery, chrome, motion and signature differ.
