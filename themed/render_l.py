#!/usr/bin/env python3
"""Render mockup L, "Tesserae": the portfolio set like a mosaic wall.

    python3 -I themed/render_l.py

Reads themed/live.json and writes everything under mockup-l/: index.html (the wall),
<room>/index.html (one panel per room), plus l.css, l.js, wall.js, fonts/ and vendor/ copied
from themed/l/. Stdlib only. Safe to re-run. It never touches the live site.

Concept: five panels of glass tesserae set into one wall, one panel per room; every project is
one larger tessera in its panel (flagships in gold leaf). The homepage hero is that wall, drawn
by wall.js (WebGL, three r180, instanced tiles + a short bloom chain); each room page opens with
a band of its own panel. Without WebGL or JavaScript a static CSS version of the wall shows.

Paths: room pages live at mockup-l/<room>/, so the live bodies' ../assets/ and ../demos/ gain
one more ../ (the repo root holds assets/ and demos/). Room-to-room links stay in the theme.
"""
import html
import json
import os
import re
import shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'themed', 'l')
OUT = os.path.join(ROOT, 'mockup-l')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape
NAME = 'Tesserae'


def esc(s):
    return html.escape(s, quote=False)


def qa(s):
    return html.escape(s, quote=True)


def plain(t):
    return re.sub(r'\s+', ' ', unesc(re.sub(r'<[^>]+>', '', t))).strip()


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
    return re.sub(r'<a\b[^>]*>', a, b)




# ------------------------------------------------------------------ chrome
GLASS = {'legal': 'var(--g-legal)', 'business': 'var(--g-business)', 'creative': 'var(--g-creative)',
         'design': 'var(--g-design)', 'research': 'var(--g-research)'}
THEME_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t;d.className+=' js';
try{t=localStorage.getItem('mpl-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);})();
</script>"""


def chip(slug, flag=False):
    """A small tessera: the room's glass, or gold leaf for a flagship system."""
    return '<i class="tess tess--%s%s" aria-hidden="true"></i>' % (slug, ' tess--gold' if flag else '')


def top_bar(depth, cur):
    up = '../' * depth
    lis = []
    for r in ROOMS:
        on = r['slug'] == cur
        lis.append('<li><a href="%s%s/index.html"%s>%s<span class="bar__nm">%s</span><span class="bar__n">%d<span class="vh"> projects</span></span></a></li>'
                   % (up, r['slug'], ' aria-current="page"' if on else '', chip(r['slug']), esc(r['short']), r['n']))
    return ('<nav class="bar" id="nav" aria-label="Site">'
            '<a class="bar__home" href="%sindex.html"%s>Myles Parslow<span class="vh"> (home)</span></a>'
            '<button type="button" class="bar__menu btn" id="menu" aria-expanded="false" aria-controls="rooms">Rooms</button>'
            '<ul class="bar__rooms" id="rooms">%s</ul>'
            '<button type="button" class="bar__theme" id="theme" aria-label="Switch between light and dark">%s</button>'
            '</nav>') % (up, ' aria-current="page"' if cur == 'home' else '', ''.join(lis), THEME_ICON)


def page(title, desc, depth, cls, inner, cur, head_extra='', tail=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n'
            '<link rel="preload" href="%sfonts/Switzer.woff2" as="font" type="font/woff2" crossorigin>\n'
            '<link rel="preload" href="%sfonts/ClashDisplay.woff2" as="font" type="font/woff2" crossorigin>\n'
            '%s\n%s<link rel="stylesheet" href="%sl.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="%s">%s</a>\n%s\n%s\n'
            '<script src="%sl.js" defer></script>\n%s</body>\n</html>\n') % (
        esc(title), qa(desc), up, up, up, HEAD_SCRIPT, head_extra, up, cls,
        '#index' if depth == 0 else '#main', 'Skip to the rooms' if depth == 0 else 'Skip to the projects', top_bar(depth, cur), inner, up, tail)


def contact_mail():
    return re.search(r'href="mailto:([^"]+)"', HOME['foot_html']).group(1)


def footer_html(depth):
    foot = HOME['foot_html']
    mail = contact_mail()
    gh = re.search(r'<a href="(https://github.com/[^"]*)">GitHub</a>', foot).group(1)
    lp = re.search(r'<a href="([^"]*)">Legal portfolio</a>', foot).group(1)
    sign = re.search(r'<span>([^<]*)</span>\s*</div>', foot).group(1)
    up = '../' * depth
    extra = '' if depth == 0 else '<a href="../index.html#tools">Which AI for what by project &rarr;</a>'
    extra += '<a href="%s../pets/index.html">Meet the cats</a>' % up
    return ('<div class="frieze" aria-hidden="true"></div>'
            '<footer class="foot" id="contact" aria-labelledby="h-foot"><div class="foot__in">'
            '<div class="foot__l"><p class="lab">Contact</p><h2 id="h-foot" class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><a href="mailto:%s">%s</a></p>'
            '<p class="foot__copy"><button type="button" class="btn" id="copy" data-copy="%s">Copy address</button> <span id="copystat" class="foot__st" aria-live="polite"></span></p></div>'
            '<div class="foot__r"><p class="foot__row"><a href="%s" target="_blank" rel="noopener">GitHub</a><a href="%s" target="_blank" rel="noopener">Legal portfolio</a><a class="foot__top" href="#top">Back to top &uarr;</a>%s</p>'
            '<p class="foot__mlp"><b>Want this for your business?</b> Through MLP Consulting I build fast websites, automated follow-up and private, human-approved AI tools for owner-run businesses and legal teams. <a href="https://mlpconsults.com/" target="_blank" rel="noopener">Visit MLPConsults.com &rarr;</a></p>'
            '<p class="foot__sign">%s</p></div></div></footer>') % (mail, mail, mail, gh, lp, extra, sign)


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


# ------------------------------------------------------------------ the wall (shared by home and rooms)
# Average colour of each project's own screenshot (thumb), measured once with macOS sips into themed/l/thumb-colors.json
# (8x8 downsample, mean of the pixels). wall.js tints each non-gold project tessera toward it.
try:
    THUMB_COL = json.load(open(os.path.join(SRC, 'thumb-colors.json'), encoding='utf-8'))
except OSError:
    THUMB_COL = {}


def wall_stage(rooms, href_of, depth):
    """The mosaic stage: a canvas for wall.js over a static CSS wall. The CSS grid of .field boxes is the layout:
    wall.js reads their rectangles, so the static wall and the WebGL wall always agree on where each panel sits."""
    up = '../' * depth
    fields = []
    for r in rooms:
        sq = ''.join('<i%s></i>' % (' class="g"' if it.get('tier') == 'flagship' else '') for it in r['cases'])
        tag = ('<a class="field__tag" href="%s%s/index.html">%s<span>%s</span> <span class="field__n">%d</span></a>'
               % (up, r['slug'], chip(r['slug']), esc(r['short']), r['n'])) if len(rooms) > 1 else ''
        fields.append('<div class="field field--%s" data-room="%s"><span class="field__tiles" aria-hidden="true">%s</span>%s</div>'
                      % (r['slug'], r['slug'], sq, tag))
    return ('<div class="stage" id="wall" data-wall>'
            '<canvas class="stage__gl" aria-hidden="true"></canvas>'
            '<div class="stage__fields stage__fields--%d">%s</div>'
            '<a class="stage__label" id="wall-label" href="%s" tabindex="-1" aria-hidden="true" hidden>'
            '<span class="stage__img"><img id="wl-img" alt="" width="240" height="150" decoding="async"></span>'
            '<span class="stage__lm"><i class="tess" id="wl-chip"></i><span id="wl-code"></span></span>'
            '<b id="wl-t"></b><span id="wl-s"></span></a>'
            '</div>') % (len(rooms), ''.join(fields), href_of(rooms[0]['cases'][0]))


def wall_data(rooms, href_of, depth):
    P = []
    for ri, r in enumerate(rooms):
        for it in r['cases']:
            th = ('../' * depth + it['thumb']) if it['thumb'] else ''
            P.append(dict(r=ri, c=it['code'], t=plain(it['title']), s=plain(it['sub']), h=href_of(it), f=1 if it.get('tier') == 'flagship' else 0,
                          i=th, a=THUMB_COL.get(os.path.basename(it['thumb']), '') if it['thumb'] else ''))
    d = dict(rooms=[dict(slug=r['slug'], n=r['n']) for r in rooms], projects=P)
    return '<script type="application/json" id="wall-data">%s</script>\n' % json.dumps(d, ensure_ascii=False).replace('</', '<\\/')


def vendor_tags(depth):
    up = '../' * depth or './'                                   # import-map values must be URL-like, never bare
    return ('<script type="importmap">{"imports":{"three":"%svendor/three.module.min.js"}}</script>\n'
            '<script type="module" src="%swall.js"></script>\n') % (up, up)


# ------------------------------------------------------------------ home
PIDX = {}
for _r in ROOMS:
    for _it in _r['cases']:
        PIDX[_it['id']] = len(PIDX)


def routes_html():
    rows = []
    for k, rt in enumerate(HOME.get('routes', [])):
        ln = BY[rt['line']]
        stops = []
        for cid, why in rt['stops']:
            it = CASE[cid]
            stops.append('<li><a href="%s/index.html#%s" data-p="%d">%s<span class="code">%s</span> <span class="t">%s</span></a><span class="why">%s</span></li>'
                         % (it['room']['slug'], cid, PIDX[cid], chip(it['room']['slug'], it.get('tier') == 'flagship'), it['code'], it['title'], why))
        rows.append('<li class="route" id="route-%s"><p class="route__n">%sRoute %d</p><div class="route__h"><h3>%s</h3><p class="route__p">%s</p>'
                    '<a class="more" href="%s/index.html">Explore all %d %s builds &rarr;</a></div><ol class="route__stops">%s</ol></li>'
                    % (rt['key'], chip(ln['slug']), k + 1, rt['who'], rt['pitch'], ln['slug'], ln['n'], esc(ln['short']), ''.join(stops)))
    if not rows:
        return ''
    return ('<section class="sec start" id="start" aria-labelledby="h-start"><div class="sec__h"><p class="lab">Where to start</p>'
            '<h2 id="h-start">Three routes, one for each kind of visitor</h2>'
            '<p class="sec__l">%d projects is a lot to explore cold. Start with the route built for what you care about, or go straight to the full index below.</p></div>'
            '<ol class="routes">%s</ol>'
            '<p class="start__alt"><span>Just browsing?</span> <button type="button" class="btn" id="surprise">Take me somewhere random</button> '
            '<a href="#index">Open the full index &darr;</a></p></section>') % (N_CASES, ''.join(rows))


def home():
    hhtml = HOME['hero_html']
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    href_home = lambda it: '%s/index.html#%s' % (it['room']['slug'], it['id'])
    nums = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (dt, dd) for dt, dd in stats)
    n_flag = sum(1 for c in CASE.values() if c.get('tier') == 'flagship')
    legend = ('<ul class="wall__legend" aria-label="Rooms on the wall">%s<li class="wall__lg">%s<span>Flagship system</span></li></ul>'
              % (''.join('<li><a href="%s/index.html">%s<span>%s</span> <span class="n">%d</span></a></li>' % (r['slug'], chip(r['slug']), esc(r['short']), r['n']) for r in ROOMS),
                 chip('legal', True)))
    wall = ('<header class="wall" id="top">%s'
            '<div class="wall__panel" id="inscription"><p class="lab">%d projects in %d rooms</p>'
            '<h1 class="wall__t"><span class="wall__t1">Myles Parslow</span> <span class="wall__t2">makes things with AI.</span></h1>'
            '<p class="wall__lede">%s</p><dl class="wall__nums">%s</dl>'
            '<p class="wall__hint" id="wall-hint" hidden>Each larger tile on the wall is one project, and the %d gold ones are the flagship systems. Point at or tap a tile to see its name, or use the index below.</p>'
            '</div></header>') % (wall_stage(ROOMS, href_home, 0) + legend, N_CASES, len(ROOMS), lede, nums, n_flag)

    # the full index: every project by room
    def ser(r):
        rows = []
        for it in r['cases']:
            see = ''.join('<span class="see">See also <a href="%s/index.html#%s">%s</a> in %s</span>'
                          % (CASE[o]['room']['slug'], o, CASE[o]['title'], esc(CASE[o]['room']['short'])) for o, _ in XOF.get(it['id'], []))
            rows.append('<li data-t="%s"><a href="%s/index.html#%s" data-p="%d">%s<span class="code">%s</span> <span class="t">%s</span></a><span class="s">%s %s</span>%s</li>'
                        % (qa(plain(it['title']).lower()), r['slug'], it['id'], PIDX[it['id']], chip(r['slug'], it.get('tier') == 'flagship'),
                           it['code'], it['title'], it['sub'], tier_tag(it), see))
        return ('<section class="ser ser--%s" id="ser-%s" aria-labelledby="hs-%s"><div class="ser__h"><h3 id="hs-%s"><a href="%s/index.html">%s'
                '<span class="ser__t">%s</span> <span class="ser__n">%d projects</span></a></h3><p class="ser__l">%s</p></div><ol class="ser__ol">%s</ol></section>'
                ) % (r['slug'], r['slug'], r['slug'], r['slug'], r['slug'], chip(r['slug']), r['title'], r['n'], r['lede'], ''.join(rows))
    index = ('<section class="sec index" id="index" aria-labelledby="h-ix"><div class="sec__h"><p class="lab">The index</p>'
             '<h2 id="h-ix">All %d projects</h2>'
             '<p class="sec__l">Every project, listed by room. Choose any entry to jump straight to its write-up.</p>'
             '<ul class="key"><li>%s<span><b>Flagship system:</b> the full-scale production builds. Every guided route is made of them.</span> <span class="tier tier--flagship">Flagship system</span></li>'
             '<li>%s<span><b>Weekend build</b> and <b>Study:</b> Focused prototypes, creative sprints and benchmarks.</span> <span class="tier tier--weekend">Weekend build</span> <span class="tier tier--study">Study</span></li></ul>'
             '<p class="index__ctl" id="ixctl" hidden><button type="button" class="btn" id="by-room" aria-pressed="true">By room</button>'
             '<button type="button" class="btn" id="by-az" aria-pressed="false">A to Z</button></p></div>'
             '<div class="index__rooms" id="byroom">%s</div><ol class="index__az" id="byaz" hidden></ol></section>') % (
        N_CASES, chip('legal', True), chip('research'), ''.join(ser(r) for r in ROOMS))

    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><p class="cross__k">%s%s<b>%s.</b></p><p class="cross__p"><a href="%s/index.html#%s">%s</a> (%s) and <a href="%s/index.html#%s">%s</a> (%s). %s</p></li>'
                  % (chip(a['room']['slug'], a.get('tier') == 'flagship'), chip(b['room']['slug'], b.get('tier') == 'flagship'),
                     esc(x['key'][0].upper() + x['key'][1:]), a['room']['slug'], a['id'], a['title'], esc(a['room']['short']),
                     b['room']['slug'], b['id'], b['title'], esc(b['room']['short']), esc(x['why'])))
    cross = ('<section class="sec cross" id="cross" aria-labelledby="h-cross"><div class="sec__h"><p class="lab">Cross-references</p>'
             '<h2 id="h-cross">Projects that share a part</h2></div><ul class="cross__l">%s</ul></section>') % ''.join(xk)

    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="sec rules" id="rules" aria-labelledby="h-rules"><div class="sec__h"><p class="lab">%s</p>'
                  '<h2 id="h-rules">%s</h2></div><ol class="rules__l">%s</ol></section>') % (
        r_eb, r_t, ''.join('<li><span class="rules__n" aria-hidden="true">%s</span><h3>%s</h3><p>%s</p></li>' % (n, t, p) for n, t, p in rules))

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
    tools_html = ('<section class="sec sch" id="tools" aria-labelledby="h-tools"><div class="sec__h"><p class="lab">%s</p>'
                  '<h2 id="h-tools">%s</h2><p class="sec__l">%s</p></div>'
                  '<div class="sch__b"><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div>'
                  '<details class="sch__more"><summary>%s</summary><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div></details></div></section>'
                  ) % (t_eb, t_t, t_l, head, ''.join(trow(x) for x in trs[:first]), t_sum, head, ''.join(trow(x) for x in trs[first:]))

    notice = ('<section class="sec rev" id="archive" aria-labelledby="h-rev"><div class="rev__in"><h2 class="lab" id="h-rev">About this version</h2>'
              '<p class="rev__p"><b>Style archive.</b> You&rsquo;re looking at: %s. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a href="../styles/index.html">See every version &rarr;</a></p></div></section>') % (NAME, N_CASES)

    inner = '<main id="main">\n' + '\n'.join([wall, routes_html(), index, cross, rules_html, tools_html, notice]) + '\n</main>\n' + footer_html(0)
    redirect = '<script>(function(){var M = %s;\nvar h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    tail = wall_data(ROOMS, href_home, 0) + vendor_tags(0)
    desc = 'Myles Parslow: %d builds with AI, from law-firm software to novels and games, each shown with the work behind it, set like tesserae in one mosaic wall.' % N_CASES
    return page('Myles Parslow', desc, 0, 'pg-home', inner, 'home', redirect, tail)


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
            '<a class="btn btn--solid" href="%s">%s &rarr;</a></aside>') % (qa(name), lead, body, qa(href), cta)


def case_html(r, it):
    kick = tier_tag(it) + ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    see = ''
    for o, x in XOF.get(it['id'], []):
        oc = CASE[o]
        see += ('<p class="xref"><span class="xref__l">See also</span> <a href="../%s/index.html#%s">%s</a> in %s. %s</p>'
                % (oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    fig = ''
    if it['thumb']:
        pw, ph = img_size(os.path.join(ROOT, it['thumb'].replace('../', '', 1)))
        if not pw or not ph:
            pw, ph = 1120, 700
        tall = pw / ph < 1.05
        fig = ('<figure class="case__fig%s" style="--w:%dpx"><img src="%s" alt="" width="%d" height="%d" loading="lazy" decoding="async"></figure>'
               % (' case__fig--tall' if tall else '', pw if not tall else min(pw, 420), qa('../' + it['thumb']), pw, ph))
    return ('<article class="case" id="%s" aria-labelledby="t-%s">'
            '<header class="case__h"><p class="case__meta">%s<span class="code">%s</span><span class="cnt">%s</span>%s</p>'
            '%s<h2 class="case__t" id="t-%s">%s</h2><p class="case__sub">%s</p></header>'
            '%s<div class="case__intro"><p class="case__lede">%s</p>%s</div>'
            '<div class="cbody">%s</div>%s</article>') % (
        it['id'], it['id'], chip(r['slug'], it.get('tier') == 'flagship'), it['code'], it['count'], kick, alias_html(r['slug'], it['id']), it['id'], it['title'], it['sub'],
        fig, it['lede'], see, fix_body(it['body_html'], r['slug']), ask_html(r, it))


def room(r):
    i = r['i']
    parts, lst, g = [], [], 0
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            g += 1
            gh = fix_body(it['html'], r['slug']).replace('<h2 class="gdiv__t">', '<p class="lab">Group %d</p><h2 class="gdiv__t">' % g, 1)
            parts.append('<div class="grp">%s</div>' % gh)
            t = re.search(r'gdiv__t">(.*?)</h2>', it['html'], re.S).group(1)
            lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t))
        elif k == 'extra':
            parts.append('<div class="extra">%s</div>' % fix_body(it['html'], r['slug']))
            t = re.search(r'<h2[^>]*>(.*?)</h2>', it['html'], re.S)
            if t and it.get('id'):
                lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t.group(1)))
        else:
            parts.append(case_html(r, it))
            lst.append('<li><a href="#%s" data-p="%d">%s<span class="code">%s</span> <span class="t">%s</span></a></li>'
                       % (it['id'], it['k'], chip(r['slug'], it.get('tier') == 'flagship'), it['code'], it['title']))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="next" href="../%s/index.html"><span class="lab">Next room</span>'
                  '<span class="next__t">%s%s &rarr;</span></a>') % (nxt['slug'], chip(nxt['slug']), nxt['title'])
    else:
        change = ('<a class="next" href="../index.html"><span class="lab">End of the wall</span>'
                  '<span class="next__t">Back to the wall (Home) &rarr;</span></a>')
    groups = sum(1 for it in r['items'] if it['kind'] == 'group')
    glance = ''
    if r['slug'] == 'legal':
        glance = ('<p class="band__note">%d tools in %d groups, flagships first, then by practice area. <span class="tier tier--flagship">Flagship system</span> marks the largest builds.</p>') % (r['n'], groups)
    href_room = lambda it: '#%s' % it['id']
    head = ('<header class="band band--%s" id="top">%s%s<div class="band__panel">'
            '<p class="lab">%s<span>%s</span> <span class="band__cnt">%s</span></p>'
            '<h1 class="band__t">%s</h1><p class="band__lede">%s</p>%s</div></header>') % (
        r['slug'], alias_html(r['slug'], 'top'), wall_stage([r], href_room, 1), chip(r['slug']), r['eyebrow'], '%d projects' % r['n'], r['title'], r['lede'], glance)
    rail = ('<nav class="rail" id="list" aria-label="%s projects"><details class="rail__d" open><summary><span class="lab">In this room <span class="rail__n">%d</span></span></summary>'
            '<ol>%s</ol></details></nav>') % (esc(r['short']), r['n'], ''.join(lst))
    inner = (head + '\n<div class="room">' + rail + '\n<main id="main" class="cases">\n%s\n%s\n</main></div>' % ('\n'.join(parts), change)
             + '\n' + footer_html(1))
    tail = wall_data([r], href_room, 1) + vendor_tags(1)
    return page('%s — Myles Parslow' % r['plain'], plain(r['lede']), 1, 'pg-room room-%s' % r['slug'], inner, r['slug'], '', tail)


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, 'index.html'), home())
    for r in ROOMS:
        write(os.path.join(OUT, r['slug'], 'index.html'), room(r))
    for name in ('l.css', 'l.js', 'wall.js'):
        shutil.copyfile(os.path.join(SRC, name), os.path.join(OUT, name))
    for d in ('fonts', 'vendor'):
        dst = os.path.join(OUT, d)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(SRC, d), dst)
    assert sum(r['n'] for r in ROOMS) == N_CASES
    print('mockup-l: the wall + %d rooms, %d projects, %d flagships' % (len(ROOMS), N_CASES, sum(1 for c in CASE.values() if c.get('tier') == 'flagship')))



def _switcher():
    import importlib.util
    spec = importlib.util.spec_from_file_location('add_switcher', os.path.join(ROOT, 'themed', 'add_switcher.py'))
    sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw); sw.run('l')

if __name__ == '__main__':
    main()
    _switcher()
