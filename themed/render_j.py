#!/usr/bin/env python3
"""Render mockup J, "Working Drawings": the portfolio as a set of working drawings.

    python3 -I themed/render_j.py

Reads themed/live.json and writes everything under mockup-j/: index.html (the cover sheet),
<room>/index.html (one sheet per room), plus j.css, j.js, hero.js and fonts/ copied from
themed/j/. Stdlib only. Safe to re-run. It never touches the live site.

Concept: every project is shown first as an ink drawing of its own screenshot and then as the
built thing. The cover sheet's plate does that with a pointer-driven fluid (hero.js, WebGL);
the room pages do it with a 2D canvas and a left-to-right plot (j.js).

Paths: room pages live at mockup-j/<room>/, so the live bodies' ../assets/ and ../demos/ gain
one more ../ (the repo root holds assets/ and demos/). Room-to-room links stay in the theme.
"""
import html
import json
import os
import re
import shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'themed', 'j')
OUT = os.path.join(ROOT, 'mockup-j')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape
NAME = 'Working Drawings'


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
MARK = ('<svg class="mark" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">'
        '<path d="M4 19V5l8 9 8-9v14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')
THEME_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t;d.className+=' js';
try{t=localStorage.getItem('mpj-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);})();
</script>"""


def strip_nav(depth, cur):
    up = '../' * depth
    lis = []
    for r in ROOMS:
        on = r['slug'] == cur
        lis.append('<li><a href="%s%s/index.html"%s><b aria-hidden="true">%s</b><span>%s</span><i>%d<span class="vh"> projects</span></i></a></li>'
                   % (up, r['slug'], ' aria-current="page"' if on else '', r['letter'], esc(r['short']), r['n']))
    here = 'Cover sheet' if cur == 'home' else 'Sheet %d of %d &middot; %s' % (BY[cur]['i'] + 1, len(ROOMS), BY[cur]['title'])
    return ('<nav class="strip" id="nav" aria-label="Site">'
            '<a class="strip__home" href="%sindex.html"%s>%s<span>Myles Parslow</span><span class="vh"> (home)</span></a>'
            '<button type="button" class="strip__menu" id="menu" aria-expanded="false" aria-controls="sheets">Rooms</button>'
            '<ul class="strip__rooms" id="sheets">%s</ul>'
            '<p class="strip__here" id="here">%s</p>'
            '<button type="button" class="strip__theme" id="theme" aria-label="Switch between light and dark">%s</button>'
            '</nav>') % (up, ' aria-current="page"' if cur == 'home' else '', MARK, ''.join(lis), here, THEME_ICON)


def page(title, desc, depth, cls, inner, cur, head_extra='', tail=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n'
            '<link rel="preload" href="%sfonts/NationalPark.woff2" as="font" type="font/woff2" crossorigin>\n'
            '%s\n%s<link rel="stylesheet" href="%sj.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="%s">%s</a>\n%s\n<div class="frame" aria-hidden="true"></div>\n%s\n'
            '<script src="%sj.js" defer></script>\n%s</body>\n</html>\n') % (
        esc(title), qa(desc), up, up, HEAD_SCRIPT, head_extra, up, cls,
        '#index' if depth == 0 else '#main', 'Skip to the rooms' if depth == 0 else 'Skip to the projects', strip_nav(depth, cur), inner, up, tail)


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
    return ('<footer class="foot" id="contact" aria-labelledby="h-foot">'
            '<div class="foot__l"><p class="lab">Contact</p><h2 id="h-foot" class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><a href="mailto:%s">%s</a> <button type="button" class="btn" id="copy" data-copy="%s">Copy address</button> <span id="copystat" class="foot__st" aria-live="polite"></span></p></div>'
            '<div class="foot__r"><p class="foot__row"><a href="%s" target="_blank" rel="noopener">GitHub</a><a href="%s" target="_blank" rel="noopener">Legal portfolio</a><a href="#top">Back to top &uarr;</a>%s</p>'
            '<p class="foot__mlp"><b>Want this for your business?</b> Through MLP Consulting I build fast websites, automated follow-up and private, human-approved AI tools for owner-run businesses and legal teams. <a href="https://mlpconsults.com/" target="_blank" rel="noopener">Visit MLPConsults.com &rarr;</a></p>'
            '<p class="foot__sign">%s</p></div></footer>') % (mail, mail, mail, gh, lp, extra, sign)


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


# ------------------------------------------------------------------ home
def slides():
    """The 'Now showing' set, read from the hero markup. Each gets the sharpest 16:10-ish image the case has."""
    out = []
    for tag in re.findall(r'<img\b[^>]*data-n="[^"]*"[^>]*>', HOME['hero_html']):
        src, n, s, h = attr(tag, 'src'), attr(tag, 'data-n'), attr(tag, 'data-s'), attr(tag, 'data-h')
        room, _, cid = h.partition('/#')
        if cid not in CASE:
            hit = [c for c in CASE.values() if c['thumb'].endswith('/' + src.split('/')[-1])]
            if not hit:
                continue
            cid, room = hit[0]['id'], hit[0]['room']['slug']
            n, s = unesc(hit[0]['title']), unesc(hit[0]['sub'])
        it = CASE[cid]
        img = '../' + src
        w, hh = img_size(os.path.join(ROOT, src))
        for t in re.findall(r'<img\b[^>]*>', it['body_html']):
            rel = attr(t, 'src') or ''
            if not rel.startswith('../assets/') or 'class="after' in t:
                continue
            iw, ih = img_size(os.path.join(ROOT, rel[3:]))
            if iw >= 1500 and ih and 1.45 <= iw / ih <= 1.8:
                img, w, hh = rel, iw, ih
                break
        out.append(dict(n=unesc(n), s=unesc(s), h='%s/index.html#%s' % (room, cid), src=img, w=w, hh=hh, code=it['code']))
    return out


def routes_html():
    cards = []
    for k, rt in enumerate(HOME.get('routes', [])):
        ln = BY[rt['line']]
        stops = []
        for cid, why in rt['stops']:
            it = CASE[cid]
            stops.append('<li><a href="%s/index.html#%s"><span class="code">%s</span> <span class="t">%s</span></a><span class="why">%s</span></li>'
                         % (it['room']['slug'], cid, it['code'], it['title'], why))
        cards.append('<li class="set" id="route-%s"><div class="set__h"><p class="lab">Route %d</p><h3>%s</h3><p class="set__p">%s</p>'
                     '<a class="more" href="%s/index.html">Explore all %d %s builds &rarr;</a></div><ol>%s</ol></li>'
                     % (rt['key'], k + 1, rt['who'], rt['pitch'], ln['slug'], ln['n'], esc(ln['short']), ''.join(stops)))
    if not cards:
        return ''
    return ('<section class="start sec" id="start" aria-labelledby="h-start"><div class="sec__h"><p class="lab">Where to start</p>'
            '<h2 id="h-start">Three routes, one for each kind of visitor</h2>'
            '<p class="sec__l">%d projects is a lot to explore cold. Start with the route built for what you care about, or go straight to the full index below.</p></div>'
            '<ol class="sets">%s</ol>'
            '<p class="start__alt"><span>Just browsing?</span> <button type="button" class="btn" id="surprise">Take me somewhere random</button> '
            '<a href="#index">Open the full index &darr;</a></p></section>') % (N_CASES, ''.join(cards))


def home():
    hhtml = HOME['hero_html']
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    S = slides()
    s0 = S[0]
    dims = ''.join('<div class="dim"><dd><span>%s</span></dd><dt>%s</dt></div>' % (dd, dt) for dt, dd in stats)
    cover = ('<header class="cover" id="top">'
             '<p class="lab cover__lab">Cover sheet &middot; %d projects &middot; %d rooms</p>'
             '<div class="cover__l"><h1>Myles Parslow makes things with AI.</h1>'
             '<p class="cover__lede">%s</p><dl class="dims">%s</dl></div>'
             '<figure class="now" id="now" aria-labelledby="now-cap">'
             '<div class="now__plate" id="plate" style="--ar:16/10"><img id="now-img" src="%s" alt="" width="%d" height="%d" decoding="async" fetchpriority="high">'
             '<canvas id="now-ink" aria-hidden="true"></canvas><canvas id="now-gl" aria-hidden="true"></canvas></div>'
             '<figcaption class="now__cap"><p id="now-cap" aria-live="polite"><span class="lab">Now showing</span> '
             '<a id="now-link" href="%s"><span class="code" id="now-code">%s</span> <b id="now-n">%s</b> <span id="now-s">%s</span></a></p>'
             '<div class="now__ctl" id="now-ctl" hidden><button type="button" class="btn" id="now-build" aria-pressed="false">Show it built</button>'
             '<button type="button" class="btn sq" data-d="-1" aria-label="Previous project">&larr;</button>'
             '<span class="now__i" id="now-i" aria-hidden="true">01 / %02d</span>'
             '<button type="button" class="btn sq" data-d="1" aria-label="Next project">&rarr;</button></div></figcaption>'
             '<p class="now__hint" id="now-hint" hidden>Every project here starts as a drawing of itself. Move across this one to build it.</p>'
             '</figure></header>') % (N_CASES, len(ROOMS), lede, dims, qa(s0['src']), s0['w'], s0['hh'], s0['h'], s0['code'], esc(s0['n']), esc(s0['s']), len(S))

    # drawing index: every project by room
    def ser(r):
        rows = []
        for it in r['cases']:
            see = ''.join('<span class="see">See also <a href="%s/index.html#%s">%s</a> in %s</span>'
                          % (CASE[o]['room']['slug'], o, CASE[o]['title'], esc(CASE[o]['room']['short'])) for o, _ in XOF.get(it['id'], []))
            rows.append('<li data-t="%s"><a href="%s/index.html#%s"><span class="code">%s</span> <span class="t">%s</span></a><span class="s">%s</span>%s%s</li>'
                        % (qa(plain(it['title']).lower()), r['slug'], it['id'], it['code'], it['title'], it['sub'], tier_tag(it), see))
        return ('<section class="ser" id="ser-%s" aria-labelledby="hs-%s"><h3 id="hs-%s"><a href="%s/index.html"><b class="bal" aria-hidden="true">%s</b>'
                '<span class="ser__t">%s</span><span class="ser__n">%d projects</span></a></h3><p class="ser__l">%s</p><ol>%s</ol></section>'
                ) % (r['slug'], r['slug'], r['slug'], r['slug'], r['letter'], r['title'], r['n'], r['lede'], ''.join(rows))
    cols = ('<div class="col">%s</div><div class="col">%s%s</div><div class="col">%s%s</div>'
            % (ser(BY['legal']), ser(BY['business']), ser(BY['creative']), ser(BY['design']), ser(BY['research'])))
    index = ('<section class="index sec" id="index" aria-labelledby="h-ix"><div class="sec__h"><p class="lab">Drawing index</p>'
             '<h2 id="h-ix">All %d projects</h2>'
             '<p class="sec__l">Every project, listed by room. Choose any entry to jump straight to its write-up.</p>'
             '<ul class="key"><li><span class="tier tier--flagship">Flagship system</span> <span><b>Flagship system:</b> the full-scale production builds. Every guided route is made of them.</span></li>'
             '<li><span><span class="tier tier--weekend">Weekend build</span><span class="tier tier--study">Study</span></span> <span><b>Weekend build</b> and <b>Study:</b> Focused prototypes, creative sprints and benchmarks.</span></li></ul>'
             '<p class="index__ctl" id="ixctl" hidden><button type="button" class="btn" id="by-room" aria-pressed="true">By room</button>'
             '<button type="button" class="btn" id="by-az" aria-pressed="false">A to Z</button></p></div>'
             '<div class="index__cols" id="byroom">%s</div><ol class="index__az" id="byaz" hidden></ol></section>') % (N_CASES, cols)

    # see-also notes for the three linked pairs (the live site's interchanges)
    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><b>%s.</b> <a href="%s/index.html#%s">%s</a> (%s) and <a href="%s/index.html#%s">%s</a> (%s). %s</li>'
                  % (esc(x['key'][0].upper() + x['key'][1:]), a['room']['slug'], a['id'], a['title'], esc(a['room']['short']),
                     b['room']['slug'], b['id'], b['title'], esc(b['room']['short']), esc(x['why'])))
    cross = ('<section class="cross sec" id="cross" aria-labelledby="h-cross"><div class="sec__h"><p class="lab">Cross-references</p>'
             '<h2 id="h-cross">Projects that share a part</h2></div><ul class="cross__l">%s</ul></section>') % ''.join(xk)

    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="notes sec" id="rules" aria-labelledby="h-rules"><div class="sec__h"><p class="lab">General notes &middot; %s</p>'
                  '<h2 id="h-rules">%s</h2></div><ol class="notes__l">%s</ol></section>') % (
        r_eb, r_t, ''.join('<li><span class="notes__n" aria-hidden="true">%s</span><h3>%s</h3><p>%s</p></li>' % (n, t, p) for n, t, p in rules))

    th = HOME['tools_html']
    t_eb = re.search(r'<p class="eyebrow">(.*?)</p>', th).group(1)
    t_t = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', th, re.S).group(1)
    t_l = re.search(r'<p class="sec-lede">(.*?)</p>', th, re.S).group(1)
    trs = re.findall(r'<article class="trow">(.*?)</article>', th, re.S)
    # the data's summary says "Show all 48 projects", a count that went stale; this says how many rows the disclosure holds
    t_sum = 'Show the other %d projects' % (len(trs) - sum(1 for _ in re.finditer(r'<article class="trow">', th.split('<details')[0])))

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
    first = sum(1 for _ in re.finditer(r'<article class="trow">', th.split('<details')[0]))
    tools_html = ('<section class="sch sec" id="tools" aria-labelledby="h-tools"><div class="sec__h"><p class="lab">Tool schedule &middot; %s</p>'
                  '<h2 id="h-tools">%s</h2><p class="sec__l">%s</p></div>'
                  '<div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div>'
                  '<details class="sch__more"><summary>%s</summary><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div></details></section>'
                  ) % (t_eb, t_t, t_l, head, ''.join(trow(x) for x in trs[:first]), t_sum, head, ''.join(trow(x) for x in trs[first:]))

    notice = ('<section class="rev sec" id="archive" aria-labelledby="h-rev"><p class="lab" id="h-rev">Revisions</p>'
              '<p class="rev__p"><b>Style archive.</b> You&rsquo;re looking at: %s. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a href="../styles/index.html">See every version &rarr;</a></p></section>') % (NAME, N_CASES)

    inner = '<main id="main">\n' + '\n'.join([cover, routes_html(), index, cross, rules_html, tools_html, notice]) + '\n</main>\n' + footer_html(0)
    redirect = '<script>(function(){var M = %s;\nvar h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    data = '<script type="application/json" id="now-data">%s</script>\n<script src="hero.js" defer></script>\n' % json.dumps(S).replace('</', '<\\/')
    desc = 'Myles Parslow: %d builds with AI, from law-firm software to novels and games, each shown with the work behind it, set out as a set of working drawings.' % N_CASES
    return page('Myles Parslow', desc, 0, 'pg-home', inner, 'home', redirect, data)


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


def dwg(r, it):
    kick = tier_tag(it) + ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    see = ''
    for o, x in XOF.get(it['id'], []):
        oc = CASE[o]
        see += ('<p class="xref"><span class="lab">See also</span> <a href="../%s/index.html#%s">%s</a> in %s. %s</p>'
                % (oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    plate = ''
    if it['thumb']:
        pw, ph = img_size(os.path.join(ROOT, it['thumb'].replace('../', '', 1)))
        if not pw or not ph:
            pw, ph = 1120, 700
        plate = ('<figure class="plate%s" data-ink style="--ar:%d/%d"><img src="%s" alt="" width="%d" height="%d" loading="lazy" decoding="async">'
                 '<canvas aria-hidden="true"></canvas></figure>') % (' plate--tall' if pw / ph < 1.05 else '', pw, ph, qa('../' + it['thumb']), pw, ph)
    return ('<article class="dwg%s" id="%s" aria-labelledby="t-%s">'
            '<header class="dwg__h"><p class="dwg__meta"><span class="code">%s</span><span class="cnt">%s</span>%s</p>'
            '%s<h2 class="dwg__t" id="t-%s">%s</h2><p class="dwg__sub">%s</p></header>'
            '<div class="dwg__top">%s<div class="dwg__intro"><p class="dwg__lede">%s</p>%s</div></div>'
            '<div class="cbody">%s</div>%s</article>') % (
        '' if plate else ' dwg--bare', it['id'], it['id'], it['code'], it['count'], kick, alias_html(r['slug'], it['id']), it['id'], it['title'], it['sub'],
        plate, it['lede'], see, fix_body(it['body_html'], r['slug']), ask_html(r, it))


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
            parts.append(dwg(r, it))
            lst.append('<li%s><a href="#%s"><span class="code">%s</span> %s</a></li>'
                       % (' class="f"' if it.get('tier') == 'flagship' else '', it['id'], it['code'], it['title']))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="next" href="../%s/index.html"><span class="lab">Next sheet</span>'
                  '<span class="next__t"><b class="bal" aria-hidden="true">%s</b>%s &rarr;</span></a>') % (nxt['slug'], nxt['letter'], nxt['title'])
    else:
        change = ('<a class="next" href="../index.html"><span class="lab">End of the set</span>'
                  '<span class="next__t">Back to the cover sheet (Home) &rarr;</span></a>')
    groups = sum(1 for it in r['items'] if it['kind'] == 'group')
    glance = ''
    if r['slug'] == 'legal':
        glance = ('<p class="rhead__note">%d tools in %d groups, flagships first, then by practice area. <span class="tier tier--flagship">Flagship system</span> marks the largest builds.</p>') % (r['n'], groups)
    head = ('<header class="rhead" id="top"><span class="rhead__mark" aria-hidden="true">%s</span>' % r['letter'] + alias_html(r['slug'], 'top') + '<p class="lab"><b class="bal" aria-hidden="true">%s</b>%s &middot; %s</p>'
            '<h1 class="rhead__t"><a href="../index.html" title="Back to the cover sheet">%s</a></h1>'
            '<p class="rhead__lede">%s</p>%s</header>') % (r['letter'], r['eyebrow'], '%d projects' % r['n'], r['title'], r['lede'], glance)
    listnav = ('<nav class="list" id="list" aria-label="%s projects"><details class="list__d" open><summary><span class="lab">Drawing list &middot; %d</span></summary>'
               '<ol>%s</ol></details></nav>') % (esc(r['short']), r['n'], ''.join(lst))
    inner = (head + '\n<div class="room">' + listnav + '\n<main id="main" class="sheet">\n%s\n%s\n</main></div>' % ('\n'.join(parts), change)
             + '\n' + footer_html(1))
    return page('%s — Myles Parslow' % r['plain'], plain(r['lede']), 1, 'pg-room room-%s' % r['slug'], inner, r['slug'])


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, 'index.html'), home())
    for r in ROOMS:
        write(os.path.join(OUT, r['slug'], 'index.html'), room(r))
    for name in ('j.css', 'j.js', 'hero.js'):
        shutil.copyfile(os.path.join(SRC, name), os.path.join(OUT, name))
    dst = os.path.join(OUT, 'fonts')
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(SRC, 'fonts'), dst)
    assert sum(r['n'] for r in ROOMS) == N_CASES
    import importlib.util
    spec = importlib.util.spec_from_file_location('add_switcher', os.path.join(ROOT, 'themed', 'add_switcher.py'))
    sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw); sw.run('j')
    print('mockup-j: cover sheet + %d rooms, %d projects, %d now-showing slides' % (len(ROOMS), N_CASES, len(slides())))


if __name__ == '__main__':
    main()
