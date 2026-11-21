#!/usr/bin/env python3
"""Render mockup K, "Liner Notes": the portfolio as a record label's catalogue.

    python3 -I themed/render_k.py

Reads themed/live.json and writes everything under mockup-k/: index.html (the label's catalogue,
opening on a crate of five sleeves), <room>/index.html (one LP per room, every project a track),
plus k.css and k.js copied from themed/k/. Stdlib only. Safe to re-run. Never touches the live site.

Grammar: rooms are records (EP, LP or double LP by track count), projects are tracks numbered by
side (A1..A8, B1..), "How it was built" is the credits, the projects that share a part are samples,
"Which AI for what" is the personnel list and the rules are the liner notes.

Paths: room pages live at mockup-k/<room>/, so the live bodies' ../assets/ and ../demos/ gain
one more ../ (the repo root holds assets/ and demos/). Room-to-room links stay in the theme.
"""
import html
import json
import os
import re
import shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'themed', 'k')
OUT = os.path.join(ROOT, 'mockup-k')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape
NAME = 'Liner Notes'


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


# ------------------------------------------------------------------ the label's grammar
SIDE = 8                                     # tracks per side, as on a real LP side of about 20 minutes


def track_no(k):
    return '%s%d' % ('ABCDEFGH'[k // SIDE], k % SIDE + 1)


def fmt(n):
    return 'EP' if n <= SIDE else ('LP' if n <= 2 * SIDE else '2&times;LP')


for r in ROOMS:
    r['cat'] = 'MPK-%03d' % (r['i'] + 1)
    r['fmt'] = fmt(r['n'])
    r['sides'] = (r['n'] + SIDE - 1) // SIDE
    for it in r['cases']:
        it['trk'] = track_no(it['k'])


def sleeve_art(r, n=4):
    """The sleeve: a grid of the room's own screenshots, flagships first. Never filtered or tinted."""
    pics = [c for c in r['cases'] if c['thumb'] and c.get('tier') == 'flagship'] + [c for c in r['cases'] if c['thumb'] and c.get('tier') != 'flagship']
    return pics[:n]


# ------------------------------------------------------------------ chrome
THEME_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')
DISC = ('<svg class="mk" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="11" fill="currentColor"/>'
        '<circle cx="12" cy="12" r="4.4" fill="var(--lab, #ff4d2e)"/><circle cx="12" cy="12" r="1.1" fill="currentColor"/></svg>')

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t;d.className+=' js';
try{t=localStorage.getItem('mpk-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);})();
</script>"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anybody:wdth,wght@50..150,300..900&amp;family=Instrument+Sans:wdth,wght@75..100,400..700&amp;display=swap">\n')


def top_nav(depth, cur):
    up = '../' * depth
    lis = []
    for r in ROOMS:
        on = r['slug'] == cur
        lis.append('<li class="lab-%s"><a href="%s%s/index.html"%s><i class="dot" aria-hidden="true"></i><span>%s</span><b>%d<span class="vh"> tracks</span></b></a></li>'
                   % (r['slug'], up, r['slug'], ' aria-current="page"' if on else '', esc(r['short']), r['n']))
    return ('<nav class="top" id="nav" aria-label="Site"><div class="top__in">'
            '<a class="top__home" href="%sindex.html"%s>%s<span>Myles Parslow</span><span class="vh"> (home)</span></a>'
            '<button type="button" class="top__menu" id="menu" aria-expanded="false" aria-controls="records">Records</button>'
            '<ul class="top__rooms" id="records">%s</ul>'
            '<button type="button" class="top__theme" id="theme" aria-label="Switch between light and dark">%s</button>'
            '</div></nav>') % (up, ' aria-current="page"' if cur == 'home' else '', DISC, ''.join(lis), THEME_ICON)


def page(title, desc, depth, cls, inner, cur, head_extra='', tail=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n'
            '%s%s\n%s<link rel="stylesheet" href="%sk.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="%s">%s</a>\n%s\n%s\n'
            '<script src="%sk.js" defer></script>\n%s</body>\n</html>\n') % (
        esc(title), qa(desc), up, FONTS, HEAD_SCRIPT, head_extra, up, cls,
        '#catalogue' if depth == 0 else '#main', 'Skip to the catalogue' if depth == 0 else 'Skip to the tracks',
        top_nav(depth, cur), inner, up, tail)


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
    return ('<footer class="foot" id="contact" aria-labelledby="h-foot"><div class="foot__in">'
            '<div class="foot__l"><p class="eb">Bookings &amp; contact</p><h2 id="h-foot" class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><a href="mailto:%s">%s</a></p><p class="foot__cp"><button type="button" class="btn" id="copy" data-copy="%s">Copy address</button> <span id="copystat" class="foot__st" aria-live="polite"></span></p></div>'
            '<div class="foot__r"><p class="foot__row"><a href="%s" target="_blank" rel="noopener">GitHub</a><a href="%s" target="_blank" rel="noopener">Legal portfolio</a><a href="#top">Back to top &uarr;</a>%s</p>'
            '<p class="foot__mlp"><b>Want this for your business?</b> Through MLP Consulting I build fast websites, automated follow-up and private, human-approved AI tools for owner-run businesses and legal teams. <a href="https://mlpconsults.com/" target="_blank" rel="noopener">Visit MLPConsults.com &rarr;</a></p>'
            '<p class="foot__sign">%s</p></div></div></footer>') % (mail, mail, mail, gh, lp, extra, sign)


def img_size(path):
    """Pixel size of a JPEG or PNG on disk."""
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


def label_disc(r, cls='disc', spin=False):
    """A record: grooves in CSS, the centre label in the room's colour, printed with its catalogue number."""
    return ('<span class="%s lab-%s%s" aria-hidden="true"><span class="disc__l"><b>%s</b><i>%s &middot; 33&#8531;</i></span></span>'
            % (cls, r['slug'], ' is-spin' if spin else '', esc(r['short']), r['cat']))


# ------------------------------------------------------------------ home
def tref(it, cls='tr'):
    """A track reference: record + track number + title, linking to the write-up."""
    return ('<a class="%s lab-%s" href="%s/index.html#%s"><span class="tr__n"><i class="dot" aria-hidden="true"></i>%s</span> <span class="tr__t">%s</span></a>'
            % (cls, it['room']['slug'], it['room']['slug'], it['id'], it['trk'], it['title']))


def crate():
    sleeves = []
    for r in ROOMS:
        pics = sleeve_art(r)
        grid = ''.join('<img src="%s" alt="" width="560" height="350" loading="%s" decoding="async">'
                       % (qa(c['thumb']), 'eager' if r['i'] < 2 else 'lazy') for c in pics)
        sleeves.append(
            '<li class="sl lab-%s" data-i="%d">'
            '<a class="sl__a" href="%s/index.html">'
            '<span class="sl__sleeve"><span class="sl__band"><span class="sl__cat">%s &middot; %s</span><span class="sl__t">%s</span></span>'
            '<span class="sl__grid g%d" aria-hidden="true">%s</span>'
            '<span class="sl__foot"><span>%d tracks</span><span>%d side%s</span></span></span>'
            '%s<span class="vh">: %d tracks. Open the record.</span></a></li>'
            % (r['slug'], r['i'], r['slug'], r['cat'], r['fmt'], r['title'], len(pics), grid,
               r['n'], r['sides'], '' if r['sides'] == 1 else 's', label_disc(r, 'disc sl__disc'), r['n']))
    return ('<div class="crate" id="crate" role="group" aria-roledescription="record crate" aria-label="The five records">'
            '<ol class="crate__bin" id="bin">%s</ol><div class="crate__wall" aria-hidden="true"><span>MPK &middot; %d tracks on %d records</span></div>'
            '<div class="crate__ctl" id="crate-ctl" hidden>'
            '<button type="button" class="btn sq" data-d="-1" aria-label="Previous record">&larr;</button>'
            '<p class="crate__now" id="crate-now" aria-live="polite"></p>'
            '<button type="button" class="btn sq" data-d="1" aria-label="Next record">&rarr;</button></div>'
            '<p class="crate__hint" id="crate-hint" hidden>Flip through the crate: scroll over it, drag, or use the arrow keys.</p></div>'
            ) % (''.join(sleeves), N_CASES, len(ROOMS))


def routes_html():
    cards = []
    for k, rt in enumerate(HOME.get('routes', [])):
        ln = BY[rt['line']]
        stops = []
        for cid, why in rt['stops']:
            it = CASE[cid]
            stops.append('<li>%s<span class="why">%s</span></li>' % (tref(it), why))
        cards.append('<li class="mix lab-%s" id="route-%s"><div class="mix__h"><p class="eb"><i class="dot" aria-hidden="true"></i>Compilation %d &middot; for</p><h3>%s</h3><p class="mix__p">%s</p></div>'
                     '<ol class="mix__l">%s</ol><a class="more" href="%s/index.html">Play all %d %s tracks &rarr;</a></li>'
                     % (ln['slug'], rt['key'], k + 1, rt['who'], rt['pitch'], ''.join(stops), ln['slug'], ln['n'], esc(ln['short'])))
    if not cards:
        return ''
    return ('<section class="mixes sec" id="start" aria-labelledby="h-start"><div class="sec__h"><p class="eb">Where to start</p>'
            '<h2 id="h-start">Three compilations, one for each kind of listener</h2>'
            '<p class="sec__l">%d tracks is a lot to take in cold. Start with the compilation made for what you care about, or go straight to the full catalogue below.</p></div>'
            '<ol class="mixes__l">%s</ol>'
            '<p class="mixes__alt"><span>Just browsing?</span> <button type="button" class="btn" id="surprise">Drop the needle anywhere</button> '
            '<a href="#catalogue">Open the full catalogue &darr;</a></p></section>') % (N_CASES, ''.join(cards))


def home():
    hhtml = HOME['hero_html']
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    dims = ''.join('<div><dd>%s</dd><dt>%s</dt></div>' % (dd, dt) for dt, dd in stats)
    hero = ('<header class="hero" id="top"><div class="hero__in">'
            '<div class="hero__l"><p class="eb hero__eb">The catalogue &middot; %d tracks on %d records</p>'
            '<h1 class="hero__t"><span class="w1">Myles Parslow</span> <span class="w2">makes things</span> <span class="w3">with <em>AI.</em></span></h1>'
            '<p class="hero__lede">%s</p><dl class="hero__dims">%s</dl></div>'
            '<div class="hero__r">%s</div></div></header>') % (N_CASES, len(ROOMS), lede, dims, crate())

    # the catalogue: every track, by record
    def rec(r):
        rows = []
        for it in r['cases']:
            see = ''.join('<span class="see">Samples <a href="%s/index.html#%s">%s</a> (%s)</span>'
                          % (CASE[o]['room']['slug'], o, CASE[o]['title'], esc(CASE[o]['room']['short'])) for o, _ in XOF.get(it['id'], []))
            rows.append('<li data-t="%s"><a href="%s/index.html#%s"><span class="n">%s</span><span class="t">%s</span></a><span class="s">%s</span>%s%s</li>'
                        % (qa(plain(it['title']).lower()), r['slug'], it['id'], it['trk'], it['title'], it['sub'], tier_tag(it), see))
        return ('<section class="rec lab-%s" id="rec-%s" aria-labelledby="hr-%s"><div class="rec__h">%s<h3 id="hr-%s"><a href="%s/index.html">'
                '<span class="rec__cat">%s &middot; %s &middot; %d tracks</span><span class="rec__t">%s</span></a></h3><p class="rec__l">%s</p></div><ol class="rec__l2">%s</ol></section>'
                ) % (r['slug'], r['slug'], r['slug'], label_disc(r, 'disc rec__disc'), r['slug'], r['slug'], r['cat'], r['fmt'], r['n'], r['title'], r['lede'], ''.join(rows))
    cat = ('<section class="cat sec" id="catalogue" aria-labelledby="h-cat"><div class="sec__h"><p class="eb">Catalogue</p>'
           '<h2 id="h-cat">All %d tracks</h2>'
           '<p class="sec__l">Every project, by record. Choose any track to jump straight to its write-up.</p>'
           '<ul class="key"><li><span class="tier tier--flagship">Flagship system</span> <span><b>Flagship system:</b> the full-scale production builds. Every compilation is made of them.</span></li>'
           '<li><span><span class="tier tier--weekend">Weekend build</span> <span class="tier tier--study">Study</span></span> <span><b>Weekend build</b> and <b>Study:</b> Focused prototypes, creative sprints and benchmarks.</span></li></ul>'
           '<p class="cat__ctl" id="catctl" hidden><button type="button" class="btn" id="by-room" aria-pressed="true">By record</button>'
           '<button type="button" class="btn" id="by-az" aria-pressed="false">A to Z</button></p></div>'
           '<div class="cat__recs" id="byroom">%s</div><ol class="cat__az" id="byaz" hidden></ol></section>') % (N_CASES, ''.join(rec(r) for r in ROOMS))

    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><p class="smp__k">%s</p><p class="smp__pair">%s <span class="smp__x" aria-hidden="true">&times;</span> %s</p><p class="smp__why">%s</p>'
                  '<p class="vh">%s (%s) and %s (%s).</p></li>'
                  % (esc(x['key'][0].upper() + x['key'][1:]) + '.', tref(a), tref(b), esc(x['why']),
                     a['title'], esc(a['room']['short']), b['title'], esc(b['room']['short'])))
    samples = ('<section class="smp sec" id="cross" aria-labelledby="h-cross"><div class="sec__h"><p class="eb">Samples</p>'
               '<h2 id="h-cross">Projects that share a part</h2><p class="sec__l">Three places where one track lifts a part from another, across records.</p></div><ul class="smp__l">%s</ul></section>') % ''.join(xk)

    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="notes sec" id="rules" aria-labelledby="h-rules"><div class="sec__h"><p class="eb">Liner notes &middot; %s</p>'
                  '<h2 id="h-rules">%s</h2></div><ol class="notes__l">%s</ol></section>') % (
        r_eb, r_t, ''.join('<li><span class="notes__n" aria-hidden="true">%s</span><div><h3>%s</h3><p>%s</p></div></li>' % (n, t, p) for n, t, p in rules))

    th = HOME['tools_html']
    t_eb = re.search(r'<p class="eyebrow">(.*?)</p>', th).group(1)
    t_t = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', th, re.S).group(1)
    t_l = re.search(r'<p class="sec-lede">(.*?)</p>', th, re.S).group(1)
    trs = re.findall(r'<article class="trow">(.*?)</article>', th, re.S)
    first = sum(1 for _ in re.finditer(r'<article class="trow">', th.split('<details')[0]))
    t_sum = 'Show the other %d credits' % (len(trs) - first)

    def trow(row):
        name = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        cells = re.findall(r'<span class="lab">(.*?)</span>\s*<p>(.*?)</p>', row, re.S)
        assert 1 <= len(cells) <= 2, name
        std = ('Built with', 'Runs on')

        def cell(k):
            if k >= len(cells):
                return '<span class="pers__none">&mdash;</span>'
            lab, p = cells[k]
            return '<span class="pers__l%s">%s</span>%s' % ('' if lab == std[k] else ' pers__lx', lab, p)
        return '<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (name, cell(0), cell(1))
    head = '<thead><tr><th scope="col">Project</th><th scope="col">Built with</th><th scope="col">Runs on</th></tr></thead>'
    tools_html = ('<section class="pers sec" id="tools" aria-labelledby="h-tools"><div class="sec__h"><p class="eb">Personnel &middot; %s</p>'
                  '<h2 id="h-tools">%s</h2><p class="sec__l">%s</p></div>'
                  '<div class="pers__w"><table class="pers__t">%s<tbody>%s</tbody></table></div>'
                  '<details class="pers__more"><summary>%s</summary><div class="pers__w"><table class="pers__t">%s<tbody>%s</tbody></table></div></details></section>'
                  ) % (t_eb, t_t, t_l, head, ''.join(trow(x) for x in trs[:first]), t_sum, head, ''.join(trow(x) for x in trs[first:]))

    notice = ('<section class="arch sec" id="archive" aria-labelledby="h-arch"><p class="eb" id="h-arch">Other pressings</p>'
              '<p class="arch__p"><b>Style archive.</b> You&rsquo;re looking at: %s. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a href="../styles/index.html">See every version &rarr;</a></p></section>') % (NAME, N_CASES)

    inner = '<main id="main">\n' + '\n'.join([hero, routes_html(), cat, samples, rules_html, tools_html, notice]) + '\n</main>\n' + footer_html(0)
    redirect = '<script>(function(){var M = %s;\nvar h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    desc = 'Myles Parslow: %d builds with AI, from law-firm software to novels and games, each shown with the work behind it, pressed as five records.' % N_CASES
    return page('Myles Parslow', desc, 0, 'pg-home', inner, 'home', redirect)


# ------------------------------------------------------------------ rooms
def ask_html(r, it):
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


def track(r, it):
    kick = tier_tag(it) + ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    see = ''
    for o, x in XOF.get(it['id'], []):
        oc = CASE[o]
        see += ('<p class="xref"><span class="eb">Samples</span> <a href="../%s/index.html#%s">%s</a> in %s. %s</p>'
                % (oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    plate = ''
    if it['thumb']:
        pw, ph = img_size(os.path.join(ROOT, it['thumb'].replace('../', '', 1)))
        if not pw or not ph:
            pw, ph = 1120, 700
        plate = ('<figure class="plate%s"><img src="%s" alt="" width="%d" height="%d" loading="lazy" decoding="async"></figure>'
                 ) % (' plate--tall' if pw / ph < 1.05 else '', qa('../' + it['thumb']), pw, ph)
    side_start = it['k'] % SIDE == 0
    side = ''
    if side_start and r['sides'] > 1:
        s = it['k'] // SIDE
        side = '<p class="side" aria-hidden="true"><span>Side %s</span><i>Tracks %d&ndash;%d</i></p>' % ('ABCDEFGH'[s], s * SIDE + 1, min(r['n'], (s + 1) * SIDE))
    return ('%s<article class="trk%s" id="%s" aria-labelledby="t-%s" data-trk="%s">'
            '<header class="trk__h"><p class="trk__n" aria-hidden="true">%s</p>'
            '<div class="trk__hd"><p class="trk__meta"><span class="vh">Track %s, </span><span class="cnt">%s</span>%s</p>'
            '%s<h2 class="trk__t" id="t-%s">%s</h2><p class="trk__sub">%s</p></div></header>'
            '<div class="trk__top">%s<div class="trk__intro"><p class="trk__lede">%s</p>%s</div></div>'
            '<div class="cbody">%s</div>%s</article>') % (
        side, '' if plate else ' trk--bare', it['id'], it['id'], it['trk'], it['trk'], it['trk'], it['count'], kick,
        alias_html(r['slug'], it['id']), it['id'], it['title'], it['sub'],
        plate, it['lede'], see, fix_body(it['body_html'], r['slug']).replace('<div class="made"><b>How it was built</b>', '<div class="made made--cr"><b>How it was built</b>'), ask_html(r, it))


def room(r):
    i = r['i']
    parts, lst, g = [], [], 0
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            g += 1
            gh = fix_body(it['html'], r['slug']).replace('<h2 class="gdiv__t">', '<p class="eb">Movement %d</p><h2 class="gdiv__t">' % g, 1)
            parts.append('<div class="grp">%s</div>' % gh)
            t = re.search(r'gdiv__t">(.*?)</h2>', it['html'], re.S).group(1)
            lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t))
        elif k == 'extra':
            parts.append('<div class="extra">%s</div>' % fix_body(it['html'], r['slug']))
            t = re.search(r'<h2[^>]*>(.*?)</h2>', it['html'], re.S)
            if t and it.get('id'):
                lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t.group(1)))
        else:
            t_html = track(r, it)
            if it['k'] % SIDE == 0 and r['sides'] > 1:
                # a side starts here: put its marker above any movement heading that leads into this track
                side_html, t_html = t_html.split('<article', 1)
                t_html = '<article' + t_html
                at, lat = len(parts), len(lst)
                while at and parts[at - 1].startswith('<div class="grp">'):
                    at -= 1
                    lat -= 1
                parts.insert(at, side_html)
                lst.insert(lat, '<li class="sd" aria-hidden="true">Side %s</li>' % 'ABCDEFGH'[it['k'] // SIDE])
            parts.append(t_html)
            lst.append('<li%s><a href="#%s"><span class="n">%s</span><span class="t">%s</span></a></li>'
                       % (' class="f"' if it.get('tier') == 'flagship' else '', it['id'], it['trk'], it['title']))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="next lab-%s" href="../%s/index.html">%s<span class="eb">Next record &middot; %s</span>'
                  '<span class="next__t">%s &rarr;</span></a>') % (nxt['slug'], nxt['slug'], label_disc(nxt, 'disc next__disc'), nxt['cat'], nxt['title'])
    else:
        change = ('<a class="next" href="../index.html"><span class="eb">End of the catalogue</span>'
                  '<span class="next__t">Back to the crate (Home) &rarr;</span></a>')
    groups = sum(1 for it in r['items'] if it['kind'] == 'group')
    glance = ''
    if r['slug'] == 'legal':
        glance = ('<p class="rhead__note">%d tools in %d movements, flagships first, then by practice area. <span class="tier tier--flagship">Flagship system</span> marks the largest builds.</p>') % (r['n'], groups)
    pics = sleeve_art(r, 4)
    grid = ''.join('<img src="%s" alt="" width="560" height="350" decoding="async"%s>' % (qa('../' + c['thumb']), '' if n < 2 else ' loading="lazy"') for n, c in enumerate(pics))
    head = ('<header class="rhead lab-%s" id="top"><div class="rhead__in">' % r['slug'] + alias_html(r['slug'], 'top') +
            '<div class="rhead__txt"><p class="eb"><i class="dot" aria-hidden="true"></i>%s &middot; %s &middot; %s &middot; %d tracks</p>'
            '<h1 class="rhead__t"><a href="../index.html" title="Back to the catalogue">%s</a></h1>'
            '<p class="rhead__lede">%s</p>%s<p class="rhead__go"><a class="btn" href="#%s">Play from %s &darr;</a></p></div>'
            '<div class="rhead__rec" aria-hidden="true"><span class="sl__sleeve rhead__sleeve"><span class="sl__band"><span class="sl__cat">%s &middot; %s</span><span class="sl__t">%s</span></span>'
            '<span class="sl__grid g%d">%s</span><span class="sl__foot"><span>%d tracks</span><span>%s</span></span></span>%s</div>'
            '</div></header>') % (r['cat'], r['fmt'], r['eyebrow'], r['n'], r['title'], r['lede'], glance, r['cases'][0]['id'], r['cases'][0]['trk'],
                                  r['cat'], r['fmt'], r['title'], len(pics), grid, r['n'], esc(r['short']), label_disc(r, 'disc rhead__disc'))
    listnav = ('<nav class="list" id="list" aria-label="%s tracklist"><details class="list__d" open><summary><span class="eb">Tracklist &middot; %d</span></summary>'
               '<ol>%s</ol></details></nav>') % (esc(r['short']), r['n'], ''.join(lst))
    deck = ('<a class="deck lab-%s" id="deck" href="#list" aria-label="Now playing. Open the tracklist">'
            '<span class="deck__plat" aria-hidden="true"><span class="deck__rec" id="deck-rec"><span class="disc__l"></span></span><span class="deck__arm" id="deck-arm"></span></span>'
            '<span class="deck__txt"><span class="eb">Now playing</span><span class="deck__now" id="deck-now">%s %s</span></span></a>'
            ) % (r['slug'], r['cases'][0]['trk'], r['cases'][0]['title'])
    inner = (head + '\n<div class="room lab-%s">' % r['slug'] + listnav + '\n<main id="main" class="tracks">\n%s\n%s\n</main></div>' % ('\n'.join(parts), change)
             + '\n' + deck + '\n' + footer_html(1))
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
    for name in ('k.css', 'k.js'):
        shutil.copyfile(os.path.join(SRC, name), os.path.join(OUT, name))
    assert sum(r['n'] for r in ROOMS) == N_CASES
    import importlib.util
    spec = importlib.util.spec_from_file_location('add_switcher', os.path.join(ROOT, 'themed', 'add_switcher.py'))
    sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw); sw.run('k')
    print('mockup-k: catalogue + %d records, %d tracks' % (len(ROOMS), N_CASES))


if __name__ == '__main__':
    main()
