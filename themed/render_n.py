#!/usr/bin/env python3
"""Render mockup N, "Flipbook": the portfolio as a stop-motion film.

    python3 -I themed/render_n.py

Reads themed/live.json and writes everything under mockup-n/: index.html (the exposure sheet),
<room>/index.html (one scene per room), plus n.css, n.js, flip.js, strip.jpg and fonts/ copied from
themed/n/. Stdlib only. Safe to re-run. It never touches the live site.

Concept: every project is one numbered frame of one short film, in room order (frame 001 to 087).
The exposure sheet lists the frames; a sticky light-box viewer (canvas 2D, flip.js) holds the frame
that is on the reading line, with the previous and next frames ghosted in green and pink (onion skin).
Play runs the frames at 12 a second; the film strip under the viewer is a scrubber.

strip.jpg (the film strip's thumbnails) is made by themed/n/make_strip.mjs from themed/n/frames.json,
which this script writes. Run the generator, then the script, then the generator again after the
frame list changes.

Paths: room pages live at mockup-n/<room>/, so the live bodies' ../assets/ and ../demos/ gain
one more ../ (the repo root holds assets/ and demos/). Room-to-room links stay in the theme.
"""
import html
import json
import os
import re
import shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'themed', 'n')
OUT = os.path.join(ROOT, 'mockup-n')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape
NAME = 'Flipbook'
FPS = 12
CELL = 64   # width of one film-strip thumbnail, in CSS pixels (the height is 40)


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

# The film: every project is one frame, numbered in room order.
FRAMES = []
for r in ROOMS:
    for it in r['cases']:
        FRAMES.append(it)
        it['g'] = len(FRAMES)
        it['fno'] = '%03d' % it['g']
for r in ROOMS:
    r['g0'], r['g1'] = r['cases'][0]['g'], r['cases'][-1]['g']
    r['range'] = '%03d–%03d' % (r['g0'], r['g1'])


def timecode(n):
    """Frames as seconds+frames at FPS: the way an exposure sheet counts."""
    return '%d+%02d' % (n // FPS, n % FPS)


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
# Three sheets of paper, the front one in ink and the two behind it in the onion-skin colours.
MARK = ('<svg class="mark" viewBox="0 0 28 22" width="26" height="20" aria-hidden="true" focusable="false">'
        '<rect x="9" y="1.5" width="17" height="13" fill="none" stroke="var(--next)" stroke-width="2"/>'
        '<rect x="2" y="7.5" width="17" height="13" fill="none" stroke="var(--prev)" stroke-width="2"/>'
        '<rect x="5.5" y="4.5" width="17" height="13" fill="var(--box)" stroke="currentColor" stroke-width="2"/></svg>')
THEME_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.8"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')
ICON_PLAY = '<svg class="i i--play" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M3.5 2l10 6-10 6z" fill="currentColor"/></svg>'
ICON_PAUSE = '<svg class="i i--pause" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M3 2h3.5v12H3zM9.5 2H13v12H9.5z" fill="currentColor"/></svg>'
ICON_PREV = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M11 2L4 8l7 6zM3 2h1.6v12H3z" fill="currentColor"/></svg>'
ICON_NEXT = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M5 2l7 6-7 6zM11.4 2H13v12h-1.6z" fill="currentColor"/></svg>'

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t;d.className+=' js';
try{t=localStorage.getItem('mpn-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);})();
</script>"""


def bar(depth, cur, local=False):
    """The transport bar: home, step back, play, step forward, the frame counter, the scenes menu and the theme switch.
    The transport buttons and the counter are shown by flip.js; the scenes are a plain list of links without JavaScript."""
    up = '../' * depth
    lis = []
    for r in ROOMS:
        on = r['slug'] == cur
        lis.append('<li><a href="%s%s/index.html"%s><b aria-hidden="true">%s</b><span class="nm">%s</span><i>%s</i></a></li>'
                   % (up, r['slug'], ' aria-current="page"' if on else '', r['letter'], esc(r['short']), r['range']))
    return ('<nav class="bar" id="nav" aria-label="Site">'
            '<a class="bar__home" href="%sindex.html"%s>%s<span>Myles Parslow</span><span class="vh"> (home)</span></a>'
            '<div class="bar__tx" id="bar-tx" role="group" aria-label="Playback" hidden>'
            '<button type="button" class="bar__b" id="v-prev" aria-label="Previous frame">%s</button>'
            '<button type="button" class="bar__b bar__play" id="v-play" aria-pressed="false" data-label="%s">%s%s<span class="btn__t">%s</span></button>'
            '<button type="button" class="bar__b" id="v-next" aria-label="Next frame">%s</button></div>'
            '<p class="bar__fr" id="bar-fr" hidden><span>Frame</span> <b id="bar-n">001</b><span class="bar__of"> / %03d</span></p>'
            '<div class="bar__sc"><button type="button" class="bar__menu" id="menu" aria-expanded="false" aria-controls="scenes">Scenes</button>'
            '<ul class="bar__scenes" id="scenes">%s</ul></div>'
            '<button type="button" class="bar__theme" id="theme" aria-label="Switch between light and dark">%s</button>'
            '</nav>') % (up, ' aria-current="page"' if cur == 'home' else '', MARK, ICON_PREV,
                         'Play scene' if local else 'Play film', ICON_PLAY, ICON_PAUSE, 'Play scene' if local else 'Play film',
                         ICON_NEXT, N_CASES, ''.join(lis), THEME_ICON)


def page(title, desc, depth, cls, inner, cur, head_extra='', tail='', local=False):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n'
            '<link rel="preload" href="%sfonts/SofiaSansCondensed.woff2" as="font" type="font/woff2" crossorigin>\n'
            '<link rel="preload" href="%sfonts/SofiaSans.woff2" as="font" type="font/woff2" crossorigin>\n'
            '%s\n%s<link rel="stylesheet" href="%sn.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="%s">%s</a>\n%s\n%s\n'
            '<script src="%sn.js" defer></script>\n%s</body>\n</html>\n') % (
        esc(title), qa(desc), up, up, up, HEAD_SCRIPT, head_extra, up, cls,
        '#index' if depth == 0 else '#main', 'Skip to the rooms' if depth == 0 else 'Skip to the projects', inner, bar(depth, cur, local), up, tail)


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


# ------------------------------------------------------------------ the viewer
def frames_json(frames, depth, local):
    """The frame list for flip.js. Home links go to the room page; a room page links to the case on the same page."""
    out = []
    for it in frames:
        r = it['room']
        out.append(dict(g=it['g'], id=it['id'], n=unesc(plain(it['title'])), s=unesc(plain(it['sub'])),
                        h=('#%s' % it['id']) if local else '%s/index.html#%s' % (r['slug'], it['id']),
                        src=('../' * (depth + 1) + it['thumb'].replace('../', '', 1)) if it['thumb'] else '',
                        L=r['letter'], sc=r['short'], t=TIERS.get(it.get('tier'), '')))
    return json.dumps(out, ensure_ascii=False).replace('</', '<\\/')


def viewer(frames, depth, local, start=0, hero=False):
    """The light box: counter, frame, caption, onion-skin switch and the film strip (the play and step buttons are in the
    transport bar). On the homepage it is the hero and opens on frame `start`; without JavaScript it is a still of that frame."""
    f0 = frames[start]
    r0 = f0['room']
    n = len(frames)
    cells = []
    prev_room = None
    for it in frames:
        mark = '<b>%s</b>' % it['room']['letter'] if it['room'] is not prev_room and not local else ''
        prev_room = it['room']
        cells.append('<i class="cell" style="--k:%d">%s</i>' % (it['g'] - 1, mark))
    img = ('<img id="v-img" src="%s" alt="Lead screenshot of %s" width="1120" height="720" decoding="async" fetchpriority="high">'
           % (qa('../' * (depth + 1) + f0['thumb'].replace('../', '', 1)), qa(plain(f0['title'])))) if f0['thumb'] else \
        '<span class="v__nopic" id="v-img">%s</span>' % esc(plain(f0['title']))
    href = ('#%s' % f0['id']) if local else '%s/index.html#%s' % (r0['slug'], f0['id'])
    return ('<aside class="vwr%s" id="vwr" aria-label="Flipbook viewer" data-fps="%d" data-total="%d" data-start="%d"><div class="vwr__box">'
            '<p class="vwr__count"><span class="vwr__c1">Frame</span> <b class="vwr__n" id="v-n" data-p="%s" data-n="%s">%s</b> <span class="vwr__of" id="v-of">/ %03d</span> <span class="vwr__sc" id="v-sc">Scene %s</span></p>'
            '<a class="vwr__stage" id="v-link" href="%s">%s<canvas id="v-cv" aria-hidden="true"></canvas></a>'
            '<div class="vwr__cap"><p class="vwr__t" id="v-t">%s</p><p class="vwr__s" id="v-s">%s</p>'
            '<a class="vwr__open" id="v-open" href="%s">%s</a></div>'
            '<div class="vwr__ctl" id="v-ctl" hidden>'
            '<button type="button" class="btn btn--onion" id="v-onion" aria-pressed="true"><span class="dots" aria-hidden="true"><i class="g"></i><i class="p"></i></span><span class="btn__t">Onion skin</span></button>'
            '<span class="vwr__time" id="v-time" title="Seconds plus frames, at %d frames a second">0+00 / %s</span></div>'
            '<div class="strip" id="v-strip" role="slider" tabindex="0" aria-label="Film strip: drag or use the arrow keys to move between frames" aria-valuemin="1" aria-valuemax="%d" aria-valuenow="%d" hidden>'
            '<div class="strip__track" id="v-track" aria-hidden="true">%s</div><span class="strip__head" aria-hidden="true"></span></div>'
            '<p class="vh" id="v-live" aria-live="polite"></p></div></aside>') % (
        ' vwr--hero' if hero else '', FPS, N_CASES, start,
        frames[start - 1]['fno'] if start > 0 else '', frames[start + 1]['fno'] if start + 1 < n else '', f0['fno'], N_CASES, r0['letter'],
        qa(href), img, f0['title'], f0['sub'], qa(href), 'Open project &rarr;',
        FPS, timecode(n), n, start + 1, ''.join(cells))


# ------------------------------------------------------------------ home
def xrow(it, href):
    sec = '<span class="xr__sm" aria-hidden="true">%d s</span>' % (it['g'] // FPS) if it['g'] % FPS == 0 else ''
    return ('<li class="xr%s%s"><a class="xr__a" href="%s" data-g="%d"><span class="xr__n">%s%s</span>'
            '<span class="xr__act"><span class="xr__c">%s</span> %s</span><span class="xr__dia">%s</span><span class="xr__t">%s</span></a></li>'
            % (' xr--s' if sec else '', ' xr--t' if it.get('tier') else '', href, it['g'], it['fno'], sec, it['code'], it['title'], it['sub'], tier_tag(it)))


def routes_html():
    cards = []
    for k, rt in enumerate(HOME.get('routes', [])):
        ln = BY[rt['line']]
        stops = []
        for cid, why in rt['stops']:
            it = CASE[cid]
            stops.append('<li><span class="fn" aria-hidden="true">%s</span><a href="%s/index.html#%s"><span class="code">%s</span> <span class="t">%s</span></a><span class="why">%s</span></li>'
                         % (it['fno'], it['room']['slug'], cid, it['code'], it['title'], why))
        cards.append('<li class="set" id="route-%s"><div class="set__h"><p class="lab">Route %d</p><h3>%s</h3><p class="set__p">%s</p>'
                     '<a class="more" href="%s/index.html">Explore all %d %s builds &rarr;</a></div><ol>%s</ol></li>'
                     % (rt['key'], k + 1, rt['who'], rt['pitch'], ln['slug'], ln['n'], esc(ln['short']), ''.join(stops)))
    if not cards:
        return ''
    return ('<section class="start sec panel" id="start" aria-labelledby="h-start"><div class="sec__h"><p class="lab">Where to start &middot; Three ways through the film</p>'
            '<h2 id="h-start">Three routes, one for each kind of visitor</h2>'
            '<p class="sec__l">%d projects is a lot to explore cold. Start with the route built for what you care about, or go straight to the full index below.</p></div>'
            '<ol class="sets">%s</ol>'
            '<p class="start__alt"><span>Just browsing?</span> <button type="button" class="btn" id="surprise">Take me somewhere random</button> '
            '<a href="#index">Open the full index &darr;</a></p></section>') % (N_CASES, ''.join(cards))


def home():
    hhtml = HOME['hero_html']
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    # the slate: a ruled strip of labelled cells, the running time first, then the two statistics (labels kept word for word)
    notes = '<div class="slate__c slate__c--t"><dt>Running time, in seconds plus frames</dt><dd>%s <span>&middot; %d fps</span></dd></div>' % (timecode(N_CASES), FPS)
    notes += ''.join('<div class="slate__c"><dt>%s</dt><dd>%s</dd></div>' % (dt, dd) for dt, dd in stats)
    title = ('<header class="title panel" id="top">'
             '<p class="lab title__lab">%s &middot; %d frames &middot; %d scenes</p>'
             '<h1>Myles Parslow makes things with AI.</h1>'
             '<p class="title__lede">%s</p>'
             '<div class="title__n"><p class="lab">Production notes</p><dl class="slate">%s</dl></div></header>'
             ) % (NAME, N_CASES, len(ROOMS), lede, notes)

    # the exposure sheet: every project by room, one scene band per room
    def scene(r):
        rows = ''.join(xrow(it, '%s/index.html#%s' % (r['slug'], it['id'])) for it in r['cases'])
        return ('<section class="xs__sc" id="ser-%s" aria-labelledby="hs-%s"><h3 id="hs-%s" class="band"><a href="%s/index.html">'
                '<b class="band__l" aria-hidden="true">%s</b><span class="band__t">%s</span>'
                '<span class="band__n">%d projects &middot; frames %s</span></a></h3><p class="band__p">%s</p><ol>%s</ol></section>'
                ) % (r['slug'], r['slug'], r['slug'], r['slug'], r['letter'], r['title'], r['n'], r['range'], r['lede'], rows)
    sheet = ('<section class="xs panel" id="index" aria-labelledby="h-ix"><div class="xs__h"><p class="lab">Exposure sheet</p>'
             '<h2 id="h-ix">All %d projects</h2>'
             '<p class="sec__l">Every project, listed by room. Choose any entry to jump straight to its write-up.</p>'
             '<ul class="key"><li><span class="tier tier--flagship">Flagship system</span> <span><b>Flagship system:</b> the full-scale production builds. Every guided route is made of them.</span></li>'
             '<li><span class="key__two"><span class="tier tier--weekend">Weekend build</span><span class="tier tier--study">Study</span></span> <span><b>Weekend build</b> and <b>Study:</b> Focused prototypes, creative sprints and benchmarks.</span></li></ul></div>'
             '<div class="xs__cols" aria-hidden="true"><span>Frame</span><span>Action</span><span>Dialogue</span></div>%s</section>'
             ) % (N_CASES, ''.join(scene(r) for r in ROOMS))

    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><b>%s.</b> <a href="%s/index.html#%s">%s</a> (%s) and <a href="%s/index.html#%s">%s</a> (%s). %s</li>'
                  % (esc(x['key'][0].upper() + x['key'][1:]), a['room']['slug'], a['id'], a['title'], esc(a['room']['short']),
                     b['room']['slug'], b['id'], b['title'], esc(b['room']['short']), esc(x['why'])))
    cross = ('<section class="cross sec panel" id="cross" aria-labelledby="h-cross"><div class="sec__h"><p class="lab">Cross-references</p>'
             '<h2 id="h-cross">Projects that share a part</h2></div><ul class="cross__l">%s</ul></section>') % ''.join(xk)

    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="notes2 sec panel" id="rules" aria-labelledby="h-rules"><div class="sec__h"><p class="lab">%s</p>'
                  '<h2 id="h-rules">%s</h2></div><ol class="notes2__l">%s</ol></section>') % (
        r_eb, r_t, ''.join('<li><span class="notes2__n" aria-hidden="true">%s</span><h3>%s</h3><p>%s</p></li>' % (n, t, p) for n, t, p in rules))

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
    tools_html = ('<section class="sch sec panel" id="tools" aria-labelledby="h-tools"><div class="sec__h"><p class="lab">%s</p>'
                  '<h2 id="h-tools">%s</h2><p class="sec__l">%s</p></div>'
                  '<div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div>'
                  '<details class="sch__more"><summary>%s</summary><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div></details></section>'
                  ) % (t_eb, t_t, t_l, head, ''.join(trow(x) for x in trs[:first]), t_sum, head, ''.join(trow(x) for x in trs[first:]))

    notice = ('<section class="rev sec panel" id="archive" aria-labelledby="h-rev"><p class="lab" id="h-rev">Revisions</p>'
              '<p class="rev__p"><b>Style archive.</b> You&rsquo;re looking at: %s. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a href="../styles/index.html">See every version &rarr;</a></p></section>') % (NAME, N_CASES)

    # the film opens on the first Creative frame, where the stop-motion work starts; frame order is still room order
    start = BY['creative']['g0'] - 1
    work = ('<div class="work work--home" id="work">\n<div class="hero" id="hero"><div class="hero__slot" id="v-slot">%s</div>\n%s</div>\n%s\n</div>'
            % (viewer(FRAMES, 0, False, start, True), title, sheet))
    inner = '<main id="main">\n' + work + '\n' + '\n'.join([routes_html(), cross, rules_html, tools_html, notice]) + '\n</main>\n' + footer_html(0)
    redirect = '<script>(function(){var M = %s;\nvar h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    data = ('<script type="application/json" id="fr-data" data-scope="all">%s</script>\n<script src="flip.js" defer></script>\n'
            % frames_json(FRAMES, 0, False))
    desc = ('Myles Parslow: %d builds with AI, from law-firm software to novels and games, each shown with the work behind it, '
            'set out as the frames of a short stop-motion film.') % N_CASES
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


def nb(r, it, d):
    """Frame number of the neighbour inside the same scene, for the onion-skin echo behind a case's number."""
    k = it['k'] + d
    return r['cases'][k]['fno'] if 0 <= k < r['n'] else ''


def case(r, it):
    kick = tier_tag(it) + ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    see = ''
    for o, x in XOF.get(it['id'], []):
        oc = CASE[o]
        see += ('<p class="xref"><span class="lab">See also</span> <a href="../%s/index.html#%s">%s</a> in %s. %s</p>'
                % (oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    return ('<article class="case" id="%s" data-g="%d" aria-labelledby="t-%s">'
            '<header class="case__h"><span class="case__no" aria-hidden="true" data-p="%s" data-n="%s">%s</span><div class="case__id">'
            '<p class="case__meta"><span class="code">%s</span><span class="cnt">%s</span>%s</p>'
            '%s<h2 class="case__t" id="t-%s">%s</h2><p class="case__sub">%s</p></div></header>'
            '<div class="case__intro"><p class="case__lede">%s</p>%s</div>'
            '<div class="cbody">%s</div>%s</article>') % (
        it['id'], it['g'], it['id'], nb(r, it, -1), nb(r, it, 1), it['fno'], it['code'], it['count'], kick, alias_html(r['slug'], it['id']), it['id'], it['title'], it['sub'],
        it['lede'], see, fix_body(it['body_html'], r['slug']), ask_html(r, it))


def room(r):
    i = r['i']
    parts, g = [], 0
    nxt_case = None
    for k, it in enumerate(r['items']):
        kind = it['kind']
        if kind == 'group':
            g += 1
            nxt = next((c for c in r['items'][k + 1:] if c['kind'] == 'case'), None)
            gh = fix_body(it['html'], r['slug']).replace('<h2 class="gdiv__t">', '<p class="lab">Group %d</p><h2 class="gdiv__t">' % g, 1)
            parts.append('<div class="grp"%s>%s</div>' % (' data-g="%d"' % nxt['g'] if nxt else '', gh))
        elif kind == 'extra':
            parts.append('<div class="extra">%s</div>' % fix_body(it['html'], r['slug']))
        else:
            parts.append(case(r, it))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="next" href="../%s/index.html"><span class="lab">Next scene</span>'
                  '<span class="next__t"><b class="band__l" aria-hidden="true">%s</b>%s &rarr;</span></a>') % (nxt['slug'], nxt['letter'], nxt['title'])
    else:
        change = ('<a class="next" href="../index.html"><span class="lab">End of the film</span>'
                  '<span class="next__t">Back to the cover sheet (Home) &rarr;</span></a>')
    groups = sum(1 for it in r['items'] if it['kind'] == 'group')
    glance = ''
    if r['slug'] == 'legal':
        glance = ('<p class="rhead__note">%d tools in %d groups, flagships first, then by practice area. <span class="tier tier--flagship">Flagship system</span> marks the largest builds.</p>') % (r['n'], groups)
    head = ('<header class="rhead panel" id="top">' + alias_html(r['slug'], 'top') +
            '<p class="lab"><b class="band__l band__l--s" aria-hidden="true">%s</b>Scene %s &middot; %s &middot; %s &middot; frames %s</p>'
            '<h1 class="rhead__t"><a href="../index.html" title="Back to the cover sheet">%s</a></h1>'
            '<p class="rhead__lede">%s</p>%s</header>') % (r['letter'], r['letter'], r['eyebrow'], '%d projects' % r['n'], r['range'], r['title'], r['lede'], glance)
    sheet = ('<details class="scsheet"><summary><span>Scene sheet: all %d frames</span></summary><ol>%s</ol></details>'
             % (r['n'], ''.join(xrow(it, '#%s' % it['id']) for it in r['cases'])))
    body = '<div class="cases panel">\n%s\n%s\n%s\n</div>' % (sheet, '\n'.join(parts), change)
    work = '<div class="work work--room" id="work">\n%s\n%s\n%s\n</div>' % (head, viewer(r['cases'], 1, True), body)
    inner = '<main id="main">\n' + work + '\n</main>\n' + footer_html(1)
    data = ('<script type="application/json" id="fr-data" data-scope="room">%s</script>\n<script src="../flip.js" defer></script>\n'
            % frames_json(r['cases'], 1, True))
    return page('%s — Myles Parslow' % r['plain'], plain(r['lede']), 1, 'pg-room room-%s' % r['slug'], inner, r['slug'], '', data, True)


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, 'index.html'), home())
    for r in ROOMS:
        write(os.path.join(OUT, r['slug'], 'index.html'), room(r))
    # the frame list the strip-sprite script reads
    manifest = [dict(g=it['g'], title=unesc(plain(it['title'])), sub=unesc(plain(it['sub'])), L=it['room']['letter'],
                     src=it['thumb'].replace('../', '', 1) if it['thumb'] else '') for it in FRAMES]
    write(os.path.join(SRC, 'frames.json'), json.dumps(manifest, ensure_ascii=False, indent=1))
    for name in ('n.css', 'n.js', 'flip.js', 'strip.jpg'):
        if os.path.exists(os.path.join(SRC, name)):
            shutil.copyfile(os.path.join(SRC, name), os.path.join(OUT, name))
        else:
            print('missing', name, '(run themed/n/make_strip.mjs for strip.jpg)')
    dst = os.path.join(OUT, 'fonts')
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(SRC, 'fonts'), dst)
    assert sum(r['n'] for r in ROOMS) == N_CASES == len(FRAMES)
    print('mockup-n: exposure sheet + %d scenes, %d frames' % (len(ROOMS), N_CASES))



def _switcher():
    import importlib.util
    spec = importlib.util.spec_from_file_location('add_switcher', os.path.join(ROOT, 'themed', 'add_switcher.py'))
    sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw); sw.run('n')

if __name__ == '__main__':
    main()
    _switcher()
