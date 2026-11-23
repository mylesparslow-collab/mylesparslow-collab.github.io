#!/usr/bin/env python3
"""Render mockup O, "Civitas": the portfolio as a walled medieval city.

    python3 -I themed/render_o.py

Reads themed/live.json and writes everything under mockup-o/: index.html (the map of the city, then the
home sections as manuscript leaves), <room>/index.html (one building per room, every project a leaf with an
illuminated initial), plus o.css, o.js and fonts/ copied from themed/o/. The map itself is drawn by
themed/o/citymap.py and the manuscript furniture by themed/o/marg.py. Stdlib only. Safe to re-run. It never
touches the live site.

Paths: room pages live at mockup-o/<room>/, so the live bodies' ../assets/ and ../demos/ gain one more ../
(the repo root holds assets/ and demos/). Room-to-room links stay in the theme.
"""
import html
import json
import os
import re
import shutil
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'themed', 'o')
OUT = os.path.join(ROOT, 'mockup-o')
sys.path.insert(0, SRC)
import citymap  # noqa: E402
import marg  # noqa: E402

D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape
NAME = 'Civitas'


def esc(s):
    return html.escape(s, quote=False)


def qa(s):
    return html.escape(s, quote=True)


def plain(t):
    return re.sub(r'\s+', ' ', unesc(re.sub(r'<[^>]+>', '', t))).strip()


def roman(n):
    out = ''
    for v, s in ((1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'),
                 (5, 'v'), (4, 'iv'), (1, 'i')):
        while n >= v:
            out += s
            n -= v
    return out


for i, r in enumerate(ROOMS):
    r['i'] = i
    r['plain'] = unesc(r['title'])
    r['cases'] = [it for it in r['items'] if it['kind'] == 'case']
    r['n'] = len(r['cases'])
    for k, it in enumerate(r['cases']):
        for key in ('links_html', 'thumb', 'sub', 'lede', 'body_html', 'title'):
            it.setdefault(key, '')
        it.setdefault('kickers', [])
        it['k'] = k
        it['code'] = '%s-%02d' % (r['letter'], k + 1)
        it['count'] = '%02d / %02d' % (k + 1, r['n'])
        it['room'] = r
BY = {r['slug']: r for r in ROOMS}
CASE = {it['id']: it for r in ROOMS for it in r['cases']}
# live.json carries three lead images on the wrong project (fieldwork.jpg on rsctiktok, northfield.jpg on money,
# aftercare.jpg on mecfs) while the projects those files are named after have none: the old extractor ran on from an
# image-less index row into the next row. When a thumb is named after another project that has no thumb, give it back.
for _it in list(CASE.values()):
    _stem = os.path.splitext(os.path.basename(_it['thumb']))[0]
    if _stem and _stem != _it['id'] and _stem in CASE and not CASE[_stem]['thumb']:
        CASE[_stem]['thumb'], _it['thumb'] = _it['thumb'], ''
N_CASES = len(CASE)
SLUGS = [r['slug'] for r in ROOMS]
ID_ROOM = {}
for r in ROOMS:
    for it in r['items']:
        if it.get('id'):
            ID_ROOM[it['id']] = r['slug']
REDIRECT = json.loads(HOME['redirect_map'])
# Old #hashes whose target id no longer exists on the room page (true on the live site too): land them on the
# case that now holds that content, or on the room heading. Rendered as empty anchors.
ALIAS_TO = {'hollowhours': 'ascii', 'auroralake': 'ascii', 'prismtrip': 'ascii', 'notredame': 'ascii', 'empirestate': 'ascii',
            'skippy3d': 'ascii', 'livingprocesses': 'ascii', 'writing': 'noearcuttwice'}
ALIASES = {}
for _old, _room in REDIRECT.items():
    if _old not in ID_ROOM:
        ALIASES.setdefault((_room, ALIAS_TO.get(_old, 'top')), []).append(_old)


def alias_html(slug, target):
    return ''.join('<span class="alias" id="%s"></span>' % a for a in ALIASES.get((slug, target), []))


# Real links stated in the case text: the same pairs the live site shows as interchanges.
XCH = [
    dict(a='rscads', b='clayexplainers', key='same Blender clay kit',
         why='One Blender claymation kit powers both the client video ads and the explainer shorts.'),
    dict(a='citationgate', b='citationaudit', key='both check citations',
         why='The same check of whether a cited source backs up the claim, applied to court opinions in one build and clinical guidelines in the other.'),
    dict(a='skippy', b='atlas', key='Atlas finds the files',
         why='Skippy searches the private legal files on the Mac through Atlas’s index before a single word of the answer is written.'),
]
XOF = {}
for x in XCH:
    XOF.setdefault(x['a'], []).append((x['b'], x))
    XOF.setdefault(x['b'], []).append((x['a'], x))

TIERS = {'flagship': 'Flagship system', 'weekend': 'Weekend build', 'study': 'Study'}


def tier_tag(it):
    t = it.get('tier')
    return '<span class="tier tier--%s">%s</span>' % (t, TIERS[t]) if t else ''


# ------------------------------------------------------------------ the city: which building holds what
BLD = {
    'legal': dict(key='castle', name='The Castle and Assize Hall', short='Castle', wash='ochre'),
    'business': dict(key='guild', name='The Guildhall', short='Guildhall', wash='red'),
    'creative': dict(key='cathedral', name='The Cathedral', short='Cathedral', wash='green'),
    'design': dict(key='lodge', name='The Masons’ Lodge', short='Masons’ Lodge', wash='ochre'),
    'research': dict(key='college', name='The Scriptorium and College', short='Scriptorium', wash='green'),
}
GATE = {'legal': ('gate-l', 'The Lawyers’ Gate', 'Lawyers’ Gate'), 'business': ('gate-r', 'The Merchants’ Gate', 'Merchants’ Gate'),
        'builders': ('gate-s', 'The Builders’ Gate', 'Builders’ Gate')}
HOMEB = {   # home sections and the buildings that hold them
    'index': 'The Survey of the City', 'start': 'The Three Gates', 'cross': 'The Bridges', 'rules': 'The Market Cross',
    'tools': 'The Mint', 'archive': 'The Old Town', 'contact': 'The Harbour'}


# ------------------------------------------------------------------ body markup
def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b, slug):
    """Deepen relative paths by one level, keep room-to-room links in the theme, open outbound and demo links in a new tab."""
    b = re.sub(r'((?:src|href|poster)=")\.\./', r'\1../../', b)

    def a(m):
        t = m.group(0)
        hr = attr(t, 'href') or ''
        new = hr
        m2 = re.match(r'(?:https://mylesparslow\.com)?/(%s)/(?:index\.html)?(#[\w-]+)?$' % '|'.join(SLUGS), hr)
        m3 = re.match(r'\.\./\.\./(%s)/(?:index\.html)?(#[\w-]+)?$' % '|'.join(SLUGS), hr)
        if m2 or m3:
            g = m2 or m3
            new = ('' if g.group(1) == slug else '../%s/index.html' % g.group(1)) + (g.group(2) or '')
            if not new:
                new = '#top'
        elif hr.startswith('#') and hr[1:] in ID_ROOM and ID_ROOM[hr[1:]] != slug:
            new = '../%s/index.html%s' % (ID_ROOM[hr[1:]], hr)
        elif hr in ('/', 'https://mylesparslow.com/', '../../', '../../index.html'):
            new = '../index.html'
        if new != hr:
            t = t.replace('href="%s"' % hr, 'href="%s"' % new, 1)
            if new.startswith(('#', '../')) and not new.startswith('../../'):
                t = re.sub(r'\s(?:target|rel)="[^"]*"', '', t)
                return t
        if (re.match(r'https?://', new) or new.startswith('../../demos/') or new.startswith('../../assets/')) and 'target=' not in t:
            t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
        elif 'target="_blank"' in t and 'rel=' not in t:
            t = t.replace('<a ', '<a rel="noopener" ', 1)
        return t
    b = re.sub(r'<a\b[^>]*>', a, b)
    # the boxed rubric on every "How it was built" note
    b = b.replace('<div class="made"><b>', '<div class="made"><span class="qf" aria-hidden="true">Quomodo factum est</span><b>')
    return b


# ------------------------------------------------------------------ chrome
THEME_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t;d.className+=' js';
try{t=localStorage.getItem('mpo-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);})();
</script>"""


def bar(depth, cur):
    up = '../' * depth
    lis = []
    for r in ROOMS:
        on = r['slug'] == cur
        lis.append('<li><a href="%s%s/index.html"%s><span class="bar__b">%s</span><span class="bar__r">%s</span><i>%d<span class="vh"> projects</span></i></a></li>'
                   % (up, r['slug'], ' aria-current="page"' if on else '', BLD[r['slug']]['short'], esc(r['short']), r['n']))
    return ('<header class="bar" id="nav"><a class="bar__home" href="%sindex.html"%s>Myles Parslow<span class="vh"> (home)</span></a>'
            '<nav class="bar__nav" aria-label="Buildings"><ul class="bar__list">%s</ul></nav>'
            '<details class="bar__menu"><summary>Buildings</summary><ul>%s</ul></details>'
            '<button type="button" class="bar__theme" id="theme" aria-label="Switch between light and dark">%s</button></header>'
            ) % (up, ' aria-current="page"' if cur == 'home' else '', ''.join(lis), ''.join(lis), THEME_ICON)


def page(title, desc, depth, cls, inner, cur, head_extra='', tail=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n'
            '<link rel="preload" href="%sfonts/Cardo-Regular.woff2" as="font" type="font/woff2" crossorigin>\n'
            '%s\n%s<link rel="stylesheet" href="%so.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="%s">%s</a>\n%s\n%s\n'
            '<script src="%so.js" defer></script>\n%s</body>\n</html>\n') % (
        esc(title), qa(desc), up, up, HEAD_SCRIPT, head_extra, up, cls,
        '#index' if depth == 0 else '#main', 'Skip to the rooms' if depth == 0 else 'Skip to the projects', bar(depth, cur), inner, up, tail)


def contact_mail():
    return re.search(r'href="mailto:([^"]+)"', HOME['foot_html']).group(1)


def rhead(left, folio):
    """The running head: the building's name in alternating rubric and blue words, the folio number at right."""
    words = ''.join('<b>%s</b> ' % w for w in left.split())
    return '<p class="rh" aria-hidden="true"><span class="rh__l">%s</span><span class="rh__r">Folium %s</span></p>' % (words.strip(), roman(folio))


def footer_html(depth, fol):
    foot = HOME['foot_html']
    mail = contact_mail()
    gh = re.search(r'<a href="(https://github.com/[^"]*)">GitHub</a>', foot).group(1)
    lp = re.search(r'<a href="([^"]*)">Legal portfolio</a>', foot).group(1)
    sign = re.search(r'<span>([^<]*)</span>\s*</div>', foot).group(1)
    up = '../' * depth
    extra = '' if depth == 0 else '<a href="../index.html#tools">Which AI for what by project &rarr;</a>'
    extra += '<a href="%s../pets/index.html">Meet the cats</a>' % up
    ship = '<svg class="foot__ship cv" viewBox="1150 128 100 80" aria-hidden="true" focusable="false">%s</svg>' % citymap.ship(1196, 196)
    return ('<footer class="leaf foot" id="contact" aria-labelledby="h-foot"><div class="leaf__in">%s'
            '<div class="foot__l"><p class="lab">Contact &middot; The Harbour</p><h2 id="h-foot" class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><a href="mailto:%s">%s</a> <button type="button" class="btn" id="copy" data-copy="%s">Copy address</button> <span id="copystat" class="foot__st" aria-live="polite"></span></p>%s</div>'
            '<div class="foot__r"><p class="foot__row"><a href="%s" target="_blank" rel="noopener">GitHub</a><a href="%s" target="_blank" rel="noopener">Legal portfolio</a><a href="#top">Back to top &uarr;</a>%s</p>'
            '<p class="foot__mlp"><b>Want this for your business?</b> Through MLP Consulting I build fast websites, automated follow-up and private, human-approved AI tools for owner-run businesses and legal teams. <a href="https://mlpconsults.com/" target="_blank" rel="noopener">Visit MLPConsults.com &rarr;</a></p>'
            '<p class="foot__sign">%s</p></div></div></footer>') % (rhead('The Harbour', fol), mail, mail, mail, ship, gh, lp, extra, sign)


def img_size(path):
    """Pixel size of a JPEG or PNG on disk (the width/height attributes in the bodies are display sizes, not file sizes)."""
    try:
        with open(path, 'rb') as f:
            b = f.read()
    except OSError:
        return 0, 0
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return int.from_bytes(b[16:20], 'big'), int.from_bytes(b[20:24], 'big')
    i = 2
    while i + 9 < len(b) and b[i] == 0xFF:
        m, n = b[i + 1], int.from_bytes(b[i + 2:i + 4], 'big')
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(b[i + 7:i + 9], 'big'), int.from_bytes(b[i + 5:i + 7], 'big')
        i += 2 + n
    return 0, 0


def small_bld(kind):
    """A building from the map, alone, for the margin of the leaf it opens."""
    rnd = __import__('random').Random(5)
    if kind == 'gate':
        body, vb = citymap.gatehouse(60, 90), (20, 16, 84, 84)
    elif kind == 'bridge':
        body, vb = citymap.bridge(30, 120, 140, rnd), (24, 20, 120, 104)
    elif kind == 'cross':
        body, vb = citymap.market_cross(40, 80), (14, 6, 52, 80)
    elif kind == 'mint':
        body, vb = citymap.mint(40, 110), (6, 34, 112, 82)
    elif kind == 'ruin':
        body, vb = citymap.old_town(40, 20, rnd), (0, 0, 250, 270)
    else:
        body, vb = '', (0, 0, 1, 1)
    return '<svg class="cv cvb cvb--%s" viewBox="%s" aria-hidden="true" focusable="false">%s</svg>' % (kind, ' '.join(str(v) for v in vb), body)


# ------------------------------------------------------------------ home
def map_links():
    L = {}
    for r in ROOMS:
        b = BLD[r['slug']]
        sub = '%s · %d projects' % (unesc(r['short']) if r['slug'] != 'creative' else 'Creative & games', r['n'])
        if r['slug'] == 'design':
            sub = 'Design & 3D · %d projects' % r['n']
        if r['slug'] == 'research':
            sub = 'AI & research · %d projects' % r['n']
        L[b['key']] = dict(href='%s/index.html' % r['slug'], label='%s, the %s room' % (b['name'], r['plain']),
                           name=b['name'], sub=sub, wash=b['wash'])
    for rt in HOME.get('routes', []):
        key, name, short = GATE[rt['key']]
        who = plain(rt['who'])
        L[key] = dict(href='#route-%s' % rt['key'], label='Where to start for %s: %d stops' % (who.lower(), len(rt['stops'])),
                      name=name, sub='Where to start · %s' % who, short=short, wash='ochre')
    L['bridges'] = dict(href='#cross', label='Projects that share a part', name='The Bridges',
                        sub='Projects that share a part · %d pairs' % len(XCH), wash='green')
    L['cross'] = dict(href='#rules', label='The rules I bring to every project', name='The Market Cross',
                      sub='Rules I bring to every project', wash='red')
    L['mint'] = dict(href='#tools', label='Which AI made which part of each project', name='The Mint',
                     sub='Which AI for what', wash='ochre')
    L['oldtown'] = dict(href='#archive', label='The style archive of earlier versions of this site', name='The Old Town',
                        sub='The style archive', wash='ochre')
    L['harbour'] = dict(href='#contact', label='Contact', name='The Harbour', sub='Contact · say hello', wash='green')
    return L


def routes_html():
    cards = []
    for k, rt in enumerate(HOME.get('routes', [])):
        ln = BY[rt['line']]
        key, gname, _ = GATE[rt['key']]
        stops = []
        for cid, why in rt['stops']:
            it = CASE[cid]
            stops.append('<li><a href="%s/index.html#%s"><span class="code">%s</span> <span class="t">%s</span></a><span class="why">%s</span></li>'
                         % (it['room']['slug'], cid, it['code'], it['title'], why))
        cards.append('<li class="gate" id="route-%s"><div class="gate__h"><p class="gate__n">%s &middot; Route %d</p><h3>%s</h3><p class="gate__p">%s</p>'
                     '<a class="more" href="%s/index.html">Explore all %d %s builds &rarr;</a></div><ol class="gate__stops">%s</ol></li>'
                     % (rt['key'], gname, k + 1, rt['who'], rt['pitch'], ln['slug'], ln['n'], esc(ln['short']), ''.join(stops)))
    if not cards:
        return ''
    return ('<section class="leaf gates" id="start" aria-labelledby="h-start"><div class="leaf__in">%s'
            '<div class="sec__h"><p class="lab">Where to start &middot; The three gates</p>'
            '<h2 id="h-start">Three routes, one for each kind of visitor</h2>'
            '<p class="sec__l">%d projects is a lot to explore cold. Start with the route built for what you care about, or go straight to the survey of the city above. Each kind of visitor comes into the city by a different gate.</p>'
            '<div class="sec__m">%s</div></div>'
            '<ol class="gates__l">%s</ol>'
            '<p class="start__alt"><span>Just browsing?</span> <button type="button" class="btn" id="surprise">Take me somewhere random</button> '
            '<a href="#index">Open the full index &uarr;</a></p></div></section>') % (rhead(HOMEB['start'], 3), N_CASES, small_bld('gate'), ''.join(cards))


def home():
    hhtml = HOME['hero_html']
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    links = map_links()
    svg, meta, info = citymap.build(links)
    cx, cy, cw, chh = info['cart']
    W, H = citymap.W, citymap.H
    snaps = ''.join('<span class="snap" style="left:%.2f%%;top:%.2f%%"></span>' % (m['x'] / W * 100, m['y'] / H * 100) for m in meta)
    walk = json.dumps([dict(k=m['key'], x=round(m['x'] / W, 4), y=round(m['y'] / H, 4), bx=[round(m['box'][0] / W, 4), round(m['box'][1] / H, 4),
                                                                                            round(m['box'][2] / W, 4), round(m['box'][3] / H, 4)])
                       for m in meta])
    intro = '<h1 class="city__t">Myles Parslow makes things with AI.</h1><p class="city__lede">%s</p>' % lede
    dims = ''.join('<div class="dim"><dd>%s</dd><dt>%s</dt></div>' % (dd, dt) for dt, dd in stats)
    city = ('<section class="city" id="top" aria-label="The map of the city"><div class="city__w">'
            '<div class="city__intro city__intro--top">%s</div>'
            '<div class="city__frame" id="frame"><div class="city__plate" id="plate">%s%s'
            '<div class="city__intro city__intro--cart" style="left:%.3f%%;top:%.3f%%;width:%.3f%%;height:%.3f%%">%s</div>'
            '<a class="note" id="note" href="#" tabindex="-1" aria-hidden="true" hidden><b class="note__n"></b><span class="note__s"></span><span class="note__go">Enter &rarr;</span></a>'
            '</div></div>'
            '<div class="walk" id="walk" hidden><button type="button" class="btn" id="w-prev">Previous building</button>'
            '<p class="walk__cur" id="w-cur" aria-live="polite"></p><button type="button" class="btn" id="w-next">Next building</button></div>'
            '<div class="city__cap"><dl class="dims">%s</dl><p class="city__hint">Every great building on the map is a door: point at one, or tab to it, to see what it holds. '
            'The same doors are listed in plain text in the survey below.</p></div>'
            '<script type="application/json" id="walk-data">%s</script>'
            '</div></section>') % (
        intro, svg, snaps, (cx + 14) / W * 100, (cy + 26) / H * 100, (cw - 28) / W * 100, (chh - 40) / H * 100, intro, dims, walk)

    # the survey: every project by room
    def ser(r):
        b = BLD[r['slug']]
        rows = []
        for it in r['cases']:
            see = ''.join('<span class="see">See also <a href="%s/index.html#%s">%s</a> in %s</span>'
                          % (CASE[o]['room']['slug'], o, CASE[o]['title'], esc(CASE[o]['room']['short'])) for o, _ in XOF.get(it['id'], []))
            rows.append('<li><a href="%s/index.html#%s"><span class="code">%s</span> <span class="t">%s</span></a><span class="s">%s</span>%s%s</li>'
                        % (r['slug'], it['id'], it['code'], it['title'], it['sub'], tier_tag(it), see))
        return ('<section class="ser" id="ser-%s" aria-labelledby="hs-%s"><p class="ser__b">%s</p><h3 id="hs-%s"><a href="%s/index.html">'
                '<span class="ser__t">%s</span> <span class="ser__n">%d projects</span></a></h3><p class="ser__l">%s</p><ol>%s</ol></section>'
                ) % (r['slug'], r['slug'], b['name'], r['slug'], r['slug'], r['title'], r['n'], r['lede'], ''.join(rows))
    cols = ('<div class="col">%s</div><div class="col">%s%s</div><div class="col">%s%s</div>'
            % (ser(BY['legal']), ser(BY['business']), ser(BY['creative']), ser(BY['design']), ser(BY['research'])))
    index = ('<section class="leaf survey" id="index" aria-labelledby="h-ix"><div class="leaf__in">%s<div class="sec__h"><p class="lab">Survey of the city</p>'
             '<h2 id="h-ix">All %d projects</h2>'
             '<p class="sec__l">Every project, listed by room. Choose any entry to jump straight to its write-up.</p>'
             '<ul class="key"><li><span class="tier tier--flagship">Flagship system</span> <span><b>Flagship system:</b> the full-scale production builds. Every guided route is made of them.</span></li>'
             '<li><span><span class="tier tier--weekend">Weekend build</span> <span class="tier tier--study">Study</span></span> <span><b>Weekend build</b> and <b>Study:</b> Focused prototypes, creative sprints and benchmarks.</span></li></ul></div>'
             '<div class="survey__cols">%s</div></div></section>') % (rhead(HOMEB['index'], 2), N_CASES, cols)

    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><b>%s.</b> <a href="%s/index.html#%s">%s</a> (%s) and <a href="%s/index.html#%s">%s</a> (%s). %s</li>'
                  % (esc(x['key'][0].upper() + x['key'][1:]), a['room']['slug'], a['id'], a['title'], esc(a['room']['short']),
                     b['room']['slug'], b['id'], b['title'], esc(b['room']['short']), esc(x['why'])))
    cross = ('<section class="leaf cross" id="cross" aria-labelledby="h-cross"><div class="leaf__in">%s<div class="sec__h"><p class="lab">Cross-references &middot; The bridges</p>'
             '<h2 id="h-cross">Projects that share a part</h2><p class="sec__l">Where two projects share a part, a bridge joins them, like the two banks of the river.</p>'
             '<div class="sec__m">%s</div></div><ul class="cross__l">%s</ul></div></section>') % (rhead(HOMEB['cross'], 4), small_bld('bridge'), ''.join(xk))

    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="leaf rules" id="rules" aria-labelledby="h-rules"><div class="leaf__in">%s<div class="sec__h"><p class="lab">%s &middot; The market cross</p>'
                  '<h2 id="h-rules">%s</h2><p class="sec__l">Read out at the market cross, where the town charter was read: the rules the city lives by.</p>'
                  '<div class="sec__m">%s</div></div><ol class="rules__l">%s</ol></div></section>') % (
        rhead(HOMEB['rules'], 5), r_eb, r_t, small_bld('cross'),
        ''.join('<li><span class="rules__n" aria-hidden="true">%s</span><h3>%s</h3><p>%s</p></li>' % (roman(int(n)), t, p) for n, t, p in rules))

    th = HOME['tools_html']
    t_eb = re.search(r'<p class="eyebrow">(.*?)</p>', th).group(1)
    t_t = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', th, re.S).group(1)
    t_l = re.search(r'<p class="sec-lede">(.*?)</p>', th, re.S).group(1)
    trs = re.findall(r'<article class="trow">(.*?)</article>', th, re.S)
    first = sum(1 for _ in re.finditer(r'<article class="trow">', th.split('<details')[0]))
    # the data's summary says "Show all 48 projects", a count that went stale; this says how many rows the disclosure holds
    t_sum = 'Show the other %d projects' % (len(trs) - first)

    def trow(row):
        name = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        cells = re.findall(r'<span class="lab">(.*?)</span>\s*<p>(.*?)</p>', row, re.S)
        assert 1 <= len(cells) <= 2, name
        std = ('Built with', 'Runs on')

        def cell(k):
            if k >= len(cells):
                return '<span class="sch__none">&mdash;</span>'
            lab, p = cells[k]
            return '<span class="sch__l%s">%s</span>%s' % ('' if lab == std[k] else ' sch__lx', lab, p)
        return '<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (name, cell(0), cell(1))
    head = '<thead><tr><th scope="col">Project</th><th scope="col">Built with</th><th scope="col">Runs on</th></tr></thead>'
    tools_html = ('<section class="leaf mint" id="tools" aria-labelledby="h-tools"><div class="leaf__in">%s<div class="sec__h"><p class="lab">%s &middot; The mint</p>'
                  '<h2 id="h-tools">%s</h2><p class="sec__l">%s</p><div class="sec__m">%s</div></div>'
                  '<div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div>'
                  '<details class="sch__more"><summary>%s</summary><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div></details></div></section>'
                  ) % (rhead(HOMEB['tools'], 6), t_eb, t_t, t_l, small_bld('mint'), head, ''.join(trow(x) for x in trs[:first]), t_sum, head,
                       ''.join(trow(x) for x in trs[first:]))

    notice = ('<section class="leaf rev" id="archive" aria-labelledby="h-rev"><div class="leaf__in">%s<div class="sec__h"><p class="lab">The old town</p>'
              '<h2 id="h-rev" class="rev__h">Earlier versions of this site</h2><div class="sec__m">%s</div></div>'
              '<p class="rev__p"><b>Style archive.</b> You&rsquo;re looking at: %s. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a href="../styles/index.html">See every version &rarr;</a></p></div></section>') % (rhead(HOMEB['archive'], 7), small_bld('ruin'), NAME, N_CASES)

    leaves = [index, routes_html(), cross, rules_html, tools_html, notice]
    body = []
    for k, s in enumerate(leaves):
        body.append(s)
        body.append('<div class="filler">%s</div>' % marg.filler(k))
    inner = city + '\n<main id="main">\n' + '\n'.join(body) + '\n</main>\n' + footer_html(0, 8)
    redirect = '<script>(function(){var M = %s;\nvar h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    desc = 'Myles Parslow: %d builds with AI, from law-firm software to novels and games, drawn as a walled medieval city whose buildings open onto manuscript leaves.' % N_CASES
    return page('Myles Parslow', desc, 0, 'pg-home', inner, 'home', redirect), info


# ------------------------------------------------------------------ rooms
def ask_html(r, it):
    """A low-friction way to reach out from the case itself: a prefilled email, no form."""
    name = unesc(plain(it['title']))
    if r['slug'] in ('legal', 'business') or it.get('tier') == 'flagship':
        subj, lead, body, cta = ('Walkthrough: ' + name, 'Want to see %s running?' % it['title'],
                                 'I can walk you through it on a short screen share and answer questions about how it was built and what it would take for your team.',
                                 'Book a walkthrough')
    else:
        subj, lead, body, cta = ('About ' + name, 'Questions about %s?' % it['title'],
                                 'Happy to talk through how it was made and which AI did which part.', 'Email me')
    href = 'mailto:%s?subject=%s' % (contact_mail(), quote(subj))
    return ('<aside class="ask" aria-label="Contact about %s"><p class="ask__t"><b>%s</b> %s</p>'
            '<a class="btn" href="%s">%s &rarr;</a></aside>') % (qa(name), lead, body, qa(href), cta)


def folio(r, it, n):
    """One project as one leaf."""
    kick = tier_tag(it) + ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    see = ''
    for o, x in XOF.get(it['id'], []):
        oc = CASE[o]
        see += ('<p class="xref"><span class="lab">See also</span> <a href="../%s/index.html#%s">%s</a> in %s. %s</p>'
                % (oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    lede = it['lede']
    ini = vine = ''
    m = re.match(r'([A-Za-z0-9])', lede)
    if m:
        ch = m.group(1)
        v = (it['k'] + r['i']) % 4
        ini = '<span class="ini-w">%s</span>' % marg.initial(ch.upper(), v, 'ic-%s' % it['id'])
        vine = marg.vine(it['k'] + r['i'])
        lede = '<span class="ini-l">%s</span>%s' % (ch, lede[1:])
    plate = ''
    if it['thumb'] and '<img' not in it['body_html'] and '<video' not in it['body_html']:
        pw, ph = img_size(os.path.join(ROOT, it['thumb'].replace('../', '', 1)))
        if not pw or not ph:
            pw, ph = 1120, 700
        plate = ('<figure class="frontis%s"><img src="%s" alt="" width="%d" height="%d" loading="lazy" decoding="async"></figure>'
                 % (' frontis--tall' if pw / ph < 1.05 else '', qa('../' + it['thumb']), pw, ph))
    draw = ''
    fixed = {'songs': 'cat', 'noearcuttwice': 'hare', 'byzantium': 'owl'}     # a drawing that suits the project
    if it['id'] in fixed:
        draw = '<div class="mg" aria-hidden="true">%s</div>' % marg.drawing(fixed[it['id']])
    elif it['k'] % 3 == 1:
        draw = '<div class="mg" aria-hidden="true">%s</div>' % marg.drawing(marg.SET[(it['k'] // 3 + r['i'] * 2) % len(marg.SET)])
    hand = ''
    if it.get('tier') == 'flagship' and '<p class="links">' in it['body_html']:
        hand = 'cbody--hand'
    return ('<article class="fol" id="%s" aria-labelledby="t-%s">%s%s'
            '<header class="fol__h"><p class="fol__meta"><span class="code">%s</span> <span class="cnt">%s</span>%s</p>'
            '<h2 class="fol__t" id="t-%s">%s</h2><p class="fol__sub">%s</p>%s</header>'
            '<div class="fol__lede">%s%s<p class="lede">%s</p>%s</div>%s'
            '<div class="cbody %s">%s%s</div>%s</article>') % (
        it['id'], it['id'], alias_html(r['slug'], it['id']), rhead(BLD[r['slug']]['name'], n),
        it['code'], it['count'], kick, it['id'], it['title'], it['sub'], draw,
        vine, ini, lede, see, plate,
        hand, '<span class="hand" aria-hidden="true">%s</span>' % marg.drawing('manicule', 'mani') if hand else '', fix_body(it['body_html'], r['slug']),
        ask_html(r, it))


def room(r):
    i = r['i']
    parts, lst, g, n = [], [], 0, 2
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            g += 1
            gh = fix_body(it['html'], r['slug']).replace('<h2 class="gdiv__t">', '<p class="grp__n">Part %s</p><h2 class="gdiv__t">' % roman(g), 1)
            parts.append('<div class="grp grp--%d">%s</div>' % (g % 2, gh))
            t = re.search(r'gdiv__t">(.*?)</h2>', it['html'], re.S).group(1)
            lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t))
        elif k == 'extra':
            parts.append('<div class="extra">%s</div>' % fix_body(it['html'], r['slug']))
            t = re.search(r'<h2[^>]*>(.*?)</h2>', it['html'], re.S)
            if t and it.get('id'):
                lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t.group(1)))
        else:
            parts.append(folio(r, it, n))
            parts.append('<div class="filler">%s</div>' % marg.filler(n))
            n += 1
            lst.append('<li%s><a href="#%s"><span class="code">%s</span> %s</a></li>'
                       % (' class="f"' if it.get('tier') == 'flagship' else '', it['id'], it['code'], it['title']))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="next" href="../%s/index.html"><span class="lab">Next building</span>'
                  '<span class="next__t">%s: %s &rarr;</span></a>') % (nxt['slug'], BLD[nxt['slug']]['name'], nxt['title'])
    else:
        change = ('<a class="next" href="../index.html"><span class="lab">End of the walk</span>'
                  '<span class="next__t">Back to the map of the city (Home) &rarr;</span></a>')
    groups = sum(1 for it in r['items'] if it['kind'] == 'group')
    glance = ''
    if r['slug'] == 'legal':
        glance = ('<p class="rhead__note">%d tools in %d groups, flagships first, then by practice area. <span class="tier tier--flagship">Flagship system</span> marks the largest builds.</p>') % (r['n'], groups)
    b = BLD[r['slug']]
    head = ('<section class="leaf rhead" id="top" aria-labelledby="h-room">%s<div class="leaf__in">%s<div class="rhead__txt">'
            '<p class="rhead__back"><a href="../index.html">&larr; The map of the city</a></p>'
            '<p class="lab">%s &middot; %d projects</p><h1 class="rhead__t" id="h-room">%s</h1><p class="rhead__b">%s</p>'
            '<p class="rhead__lede">%s</p>%s</div><div class="rhead__fig">%s</div></div></section>') % (
        alias_html(r['slug'], 'top'), rhead(b['name'], 1), r['eyebrow'], r['n'], r['title'], b['name'], r['lede'], glance,
        citymap.building_svg(b['key']))
    capit = ('<nav class="leaf capit" id="list" aria-label="%s projects"><div class="leaf__in"><details class="capit__d" open><summary>'
             'Capitula: the %d projects in this building</summary><ol>%s</ol></details></div></nav>') % (esc(r['short']), r['n'], ''.join(lst))
    inner = (head + '\n' + capit + '\n<main id="main" class="leaves">\n%s\n%s\n</main>' % ('\n'.join(parts), change) + '\n' + footer_html(1, n))
    return page('%s — Myles Parslow' % r['plain'], plain(r['lede']), 1, 'pg-room room-%s' % r['slug'], inner, r['slug'])


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    h, info = home()
    write(os.path.join(OUT, 'index.html'), h)
    for r in ROOMS:
        write(os.path.join(OUT, r['slug'], 'index.html'), room(r))
    css = open(os.path.join(SRC, 'o.css'), encoding='utf-8').read() + '\n' + open(os.path.join(SRC, 'map.css'), encoding='utf-8').read()
    write(os.path.join(OUT, 'o.css'), css)
    shutil.copyfile(os.path.join(SRC, 'o.js'), os.path.join(OUT, 'o.js'))
    dst = os.path.join(OUT, 'fonts')
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(SRC, 'fonts'), dst)
    assert sum(r['n'] for r in ROOMS) == N_CASES
    print('mockup-o: the city + %d buildings, %d projects, %d houses on the map' % (len(ROOMS), N_CASES, info['houses']))



def _switcher():
    import importlib.util
    spec = importlib.util.spec_from_file_location('add_switcher', os.path.join(ROOT, 'themed', 'add_switcher.py'))
    sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw); sw.run('o')

if __name__ == '__main__':
    main()
    _switcher()
