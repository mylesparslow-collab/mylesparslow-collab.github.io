"""Build styles/index.html: the archive of portfolio styles.

Every version renders the same case studies in a different style. Screenshots live in
styles/shots/<key>.jpg (1440x900 homepage captures, made by themed/shoot_styles.mjs).
Run: python3 -I themed/render_styles.py
"""
import html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'styles'

# newest first; href is relative to styles/index.html
VERSIONS = [
    dict(key='i', name='Transit Map', date='Nov 2026', href='../index.html', family='Map',
         line='Five rooms as transit lines and every project a station, on an octilinear network map with real interchanges.',
         knobs=dict(ground='Map white', type='Overpass signage', layout='Network map and line strip maps',
                    motion='Lines draw in once', signature='Isolate a line, ride it into the room')),
    dict(key='h', name='Orbit', date='Nov 2026', href='../mockup-h/index.html', family='Globe',
         line='A slowly turning dot globe ringed by five orbits, one per room, with every project as a satellite.',
         knobs=dict(ground='Deep night', type='Space Grotesk', layout='Planetary system and mission log',
                    motion='Rotation, drag with inertia', signature='Focus an orbit to open its room')),
    dict(key='g', name='Sticker Wall', date='Nov 2026', href='../mockup-g/index.html', family='Loud pop',
         line='Full-bleed colour slabs, an extra-wide display face, and every project as a sticker you can pick up and move.',
         knobs=dict(ground='Tomato, butter, violet, mint slabs', type='Wide display (Unbounded)', layout='Sticker walls per room',
                    motion='Drag and elastic settle', signature='Draggable project stickers')),
    dict(key='f', name='Plain Web', date='Nov 2026', href='../mockup-f/index.html', family='Plain web',
         line='One system font at one size, blue underlined links, every project in one list, and a footer that weighs the page.',
         knobs=dict(ground='White', type='System sans, one size', layout='One long index',
                    motion='None', signature='Live page-weight footer')),
    dict(key='e', name='Case File', date='Nov 2026', href='../mockup-e/index.html', family='Handmade paper',
         line='A court caption, a stack of manila folders, pleading paper with numbered lines, exhibit stickers and Bates numbers.',
         knobs=dict(ground='Desk and manila', type='Caslon serif + hand notes', layout='Folder stack, then exhibits',
                    motion='Paper lifts and settles', signature='Manila folder stack')),
    dict(key='d', name='MPWP 5.1', date='Nov 2026', href='../mockup-d/index.html', family='Retro computer',
         line='The law-firm word processor of 1991: a blue screen, a List Files directory, Reveal Codes and Print Preview.',
         knobs=dict(ground='DOS blue', type='IBM Plex Mono + VT323', layout='Directory listing and documents',
                    motion='Boot sequence', signature='Arrow-key List Files')),
    dict(key='c', name='The Museum', date='Nov 2026', href='../mockup-c/index.html', family='Exhibition index',
         line='Five rooms as museum galleries: a floor plan sized by project count, deep room colours and a wall label per exhibit.',
         knobs=dict(ground='Charcoal and deep room colours', type='Condensed signage (Archivo)', layout='Floor plan and exhibits',
                    motion='Room opens out of the plan', signature='Clickable floor plan')),
    dict(key='b', name='Five Rooms', date='Nov 2026', href='../mockup-b/index.html', family='Award look, warm editorial',
         line='Warm paper, Fraunces serif, a sticky card stack per room and red curtain wipes between rooms.',
         knobs=dict(ground='Paper, dark or red', type='Fraunces + Hanken Grotesk', layout='Sticky card stack',
                    motion='GSAP and smooth scroll', signature='Curtain wipes')),
    dict(key='a', name='The Index', date='Nov 2026', href=None, family='Award look, studio index',
         line='Near-black, one pinned index of every project with a hover preview and corner labels.',
         knobs=dict(ground='Near-black', type='Geist + Instrument Serif', layout='Pinned project index',
                    motion='GSAP and smooth scroll', signature='Hover preview in an index')),
    dict(key='old', name='The Original', date='Oct 2026', href=None, family='Single page',
         line='The first portfolio: one long page of expandable case studies with a table of contents.',
         knobs=dict(ground='Light', type='System sans', layout='Expandable list',
                    motion='None', signature='Everything on one page')),
]

e = html.escape


def card(v, n):
    shot = OUT / 'shots' / f"{v['key']}.jpg"
    img = (f'<img src="shots/{v["key"]}.jpg" alt="Homepage of the {e(v["name"])} version" width="1440" height="900" loading="lazy" decoding="async">'
           if shot.exists() else '<div class="noshot" aria-hidden="true">No capture</div>')
    rows = ''.join(f'<div><dt>{e(k.title())}</dt><dd>{e(val)}</dd></div>' for k, val in v['knobs'].items())
    open_link = (f'<a class="open" href="{e(v["href"])}">Open this version <span aria-hidden="true">&rarr;</span></a>'
                 if v['href'] else '<span class="open off">Not published</span>')
    current = ' <span class="now">Live now</span>' if v['key'] == 'i' else ''
    return f'''<article class="v" id="v-{v["key"]}">
  <figure>{img}</figure>
  <div class="vt">
    <p class="meta"><span>No. {n:02d}</span><span>{e(v["date"])}</span><span>{e(v["family"])}</span></p>
    <h2>{e(v["name"])}{current}</h2>
    <p class="line">{e(v["line"])}</p>
    <dl>{rows}</dl>
    {open_link}
  </div>
</article>'''


def page():
    cards = '\n'.join(card(v, len(VERSIONS) - i) for i, v in enumerate(VERSIONS))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Style archive · Myles Parslow</title>
<meta name="description" content="Every version of Myles Parslow's portfolio: the same case studies, rendered in a different style each time.">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wdth,wght@75..100,400..700&display=swap">
<style>
:root{{--bg:#f4f3f0;--fg:#141414;--mute:#5d5b57;--line:#d8d5cf;--card:#fff;--acc:#d6401f;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121212;--fg:#ecebe8;--mute:#a19e98;--line:#2c2b29;--card:#1b1b1a;--acc:#ff6a45;color-scheme:dark}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:400 17px/1.55 "Instrument Sans",system-ui,sans-serif}}
a{{color:inherit}}
.wrap{{max-width:1240px;margin:0 auto;padding:0 max(20px,env(safe-area-inset-right)) 80px max(20px,env(safe-area-inset-left))}}
header.top{{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:22px 0;border-bottom:1px solid var(--line)}}
header.top a{{text-decoration:none;font-weight:600}}
.intro{{padding:64px 0 40px;max-width:46rem}}
h1{{font-stretch:75%;font-weight:700;font-size:clamp(44px,7vw,96px);line-height:.95;margin:0 0 20px;letter-spacing:-.01em;text-wrap:balance}}
.intro p{{color:var(--mute);margin:0 0 12px}}
.list{{display:grid;gap:28px}}
.v{{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:28px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}
.v figure{{margin:0;border-radius:8px;overflow:hidden;border:1px solid var(--line);aspect-ratio:16/10;background:var(--bg)}}
.v img{{display:block;width:100%;height:100%;object-fit:cover;object-position:top}}
.noshot{{display:grid;place-items:center;height:100%;color:var(--mute)}}
.vt{{display:flex;flex-direction:column;gap:10px;min-width:0;padding:6px 4px}}
.meta{{display:flex;flex-wrap:wrap;gap:6px 14px;margin:0;color:var(--mute);font-size:14px}}
h2{{margin:0;font-stretch:75%;font-weight:700;font-size:clamp(30px,3.4vw,44px);line-height:1}}
.now{{display:inline-block;vertical-align:middle;font:600 13px/1 "Instrument Sans",sans-serif;font-stretch:100%;background:var(--acc);color:#fff;border-radius:99px;padding:5px 9px;margin-left:8px}}
.line{{margin:0}}
dl{{margin:4px 0 0;display:grid;gap:0;border-top:1px solid var(--line)}}
dl div{{display:grid;grid-template-columns:7.5rem 1fr;gap:12px;padding:7px 0;border-bottom:1px solid var(--line);font-size:15px}}
dt{{color:var(--mute)}} dd{{margin:0}}
.open{{margin-top:auto;align-self:flex-start;font-weight:600;text-decoration:none;border-bottom:2px solid var(--acc);padding:2px 0}}
.open.off{{border:0;color:var(--mute);font-weight:400}}
footer{{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--mute);font-size:15px}}
@media (max-width:820px){{.v{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="wrap">
<header class="top"><a href="../index.html">&larr; Myles Parslow</a><span>{len(VERSIONS)} versions</span></header>
<main>
<section class="intro">
<h1>Style archive</h1>
<p>This portfolio is also a running design experiment. Each version renders the same case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor.</p>
<p>Every version is built with AI from one shared content file, and checked against the ones before it so no two come out alike: they have to differ on at least four of eight traits, from the background colour to the one signature interaction.</p>
</section>
<div class="list">
{cards}
</div>
</main>
<footer>Same work, new clothes. <a href="../index.html">Back to the portfolio</a>.</footer>
</div>
</body>
</html>
'''


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    (OUT / 'index.html').write_text(page())
    print('wrote styles/index.html with', len(VERSIONS), 'versions;',
          sum((OUT / 'shots' / f"{v['key']}.jpg").exists() for v in VERSIONS), 'screenshots present')
