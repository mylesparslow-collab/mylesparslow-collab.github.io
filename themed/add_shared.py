"""Shared features for every alternate style (mockup-b to mockup-h), applied after each render.

The live Transit Map (render_i.py) builds these natively. Every other style gets them here,
from themed/live.json, so a new project, a new flagship or a new Start-here pick shows up in
all styles with no per-style work:

  1. Flagship star: a star after each flagship's title wherever a page links to it, and a
     "Flagship system" line under the title of its case study.
  2. "Start here if you're..." routes (live.json home.routes) on each style's home page.
  3. One stylesheet, /assets/site/shared.css, linked from every page.

Runs from add_switcher.py, which every render_*.py calls at its end, and is idempotent.
Run by hand: python3 -I themed/add_shared.py

A new style: add its folder to add_switcher.DIRS and, if needed, an entry to STYLES below
(where its home page's routes go and which element holds a linked title). Without an entry
the routes go after the home page's first </header> and the star after the link text.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / 'themed' / 'live.json'
PAGES = ['index.html'] + [f'{r}/index.html' for r in ['legal', 'business', 'creative', 'design', 'research']]
SKIP = {'i'}  # the Transit Map renders these itself
MARK = 'data-shared="1"'
CSS_TAG = '<link rel="stylesheet" href="/assets/site/shared.css" %s>' % MARK

# Per style: `before` = the home page element the routes go in front of (regex),
# `titles` = regexes, tried in order, for the element inside a project link that holds its
# title (group 1 = opening tag + title text, group 2 = its closing tag).
STYLES = {
    'b': dict(before=r'<div class="rooms" id="rooms"', titles=[r'(<span class="row__n">.*?)(</span>)']),
    'c': dict(before=r'<section class="sec plan-sec" id="plan"', titles=[r'(<span class="d-t"><b>.*?)(</b>)']),
    'd': dict(before=r'<section class="scr" id="files"', titles=[r'(<span class="t">.*?)(</span>)']),
    'e': dict(before=r'<section class="stack-sec" id="folders"', titles=[]),
    'f': dict(before=None, titles=[]),
    'g': dict(before=r'<section class="slab slab-legal"', titles=[r'(<b class="st__t">.*?)(</b>)']),
    'h': dict(before=r'<section class="log" id="log"', titles=[r'(<span class="lt">.*?)(</span>)']),
}

STAR = '<span class="xstar" role="img" aria-label="Flagship system" title="Flagship system">&#9733;</span>'
BADGE = '<p class="xflag"><span aria-hidden="true">&#9733;</span> Flagship system</p>'


def load():
    d = json.loads(LIVE.read_text(encoding='utf-8'))
    cases, room_of = {}, {}
    for r in d['rooms']:
        for it in r['items']:
            if it['kind'] == 'case':
                cases[it['id']] = it
                room_of[it['id']] = r
    return d, cases, room_of


def star_links(t, flags, cfg):
    """Add the star after the title inside every link to a flagship case."""
    def a(m):
        open_, inner = m.group(1), m.group(3)
        if m.group(2) not in flags or 'xstar' in inner:
            return m.group(0)
        for rx in cfg.get('titles', []):
            n = re.subn(rx, lambda q: q.group(1) + STAR + q.group(2), inner, count=1, flags=re.S)
            if n[1]:
                return open_ + n[0] + '</a>'
        text = re.sub(r'<[^>]+>', '', inner)
        if len(re.findall(r'[A-Za-z]', text)) >= 2 and len(text) <= 80:  # a plain title link, not a '#' permalink
            return open_ + inner + STAR + '</a>'
        return m.group(0)
    return re.sub(r'(<a\b[^>]*\bhref="[^"#]*#([\w-]+)"[^>]*>)(.*?)</a>', a, t, flags=re.S)


def badge_cases(t, flags):
    """Add 'Flagship system' under the title of each flagship's case study."""
    for cid in flags:
        m = re.search(r'<(article|section|div)\b[^>]*\bid="%s"' % re.escape(cid), t)
        if not m:
            continue
        h = t.find('</h2>', m.end())
        if h < 0 or h - m.end() > 4000 or t.startswith(BADGE, h + 5):
            continue
        t = t[:h + 5] + BADGE + t[h + 5:]
    return t


def routes_html(d, cases, room_of):
    rts = d['home'].get('routes') or []
    if not rts:
        return ''
    cards = []
    for rt in rts:
        lis = ''.join('<li><a href="%s/index.html#%s">%s</a>%s<span class="xroute__why">%s</span></li>'
                      % (room_of[cid]['slug'], cid, cases[cid]['title'], STAR if cases[cid].get('tier') == 'flagship' else '', why)
                      for cid, why in rt['stops'])
        cards.append('<li class="xroute"><h3>%s</h3><p>%s</p><ol>%s</ol><a class="xroute__more" href="%s/index.html">See all of %s &rarr;</a></li>'
                     % (rt['who'], rt['pitch'], lis, rt['line'], next(r['title'] for r in d['rooms'] if r['slug'] == rt['line'])))
    return ('<section class="xroutes" id="start" aria-labelledby="h-xstart" %s><h2 id="h-xstart" class="xroutes__h">Start here if you&rsquo;re&hellip;</h2>'
            '<p class="xroutes__l">Three short routes through the strongest work for each kind of visitor. &#9733; marks a flagship system.</p>'
            '<ol class="xroutes__g">%s</ol></section>') % (MARK, ''.join(cards))


def add_routes(t, html, cfg):
    if not html or 'class="xroutes"' in t:
        return t
    m = re.search(cfg['before'], t) if cfg.get('before') else None
    if m:
        return t[:m.start()] + html + t[m.start():]
    main = t.find('<main')
    h = t.find('</header>', main if main >= 0 else 0)
    assert h >= 0, 'no place for the Start-here routes'
    return t[:h + 9] + html + t[h + 9:]


def run(keys=None):
    from add_switcher import DIRS  # same folder list as the Style dropdown
    d, cases, room_of = load()
    flags = {cid for cid, it in cases.items() if it.get('tier') == 'flagship'}
    routes = routes_html(d, cases, room_of)
    n = 0
    for k, folder in DIRS.items():
        if k in SKIP or (keys and k not in keys):
            continue
        cfg = STYLES.get(k, {})
        for p in PAGES:
            f = folder / p
            if not f.exists():
                continue
            t = f.read_text(encoding='utf-8')
            if MARK in t:
                continue
            assert '</head>' in t, f'no </head> in {f}'
            t = t.replace('</head>', CSS_TAG + '\n</head>', 1)
            t = star_links(t, flags, cfg)
            t = badge_cases(t, flags)
            if p == 'index.html':
                t = add_routes(t, routes, cfg)
            f.write_text(t, encoding='utf-8')
            n += 1
    return n


if __name__ == '__main__':
    print('shared features added to', run(), 'pages')
