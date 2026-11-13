#!/usr/bin/env python3
"""Generate the whole "Five Rooms" version (mockup-b) from the live site's data.

    python3 -I themed/render_b.py

Reads themed/live.json (made by extract_live.py from the deployed site) and writes
mockup-b/index.html (homepage) plus mockup-b/<room>/index.html for every room in the data.
Nothing here is counted by hand: project totals, room counts, thumbnails, rows, groups and
extra sections all come from live.json. Stdlib only. Safe to re-run.

The page shell (head script, loader, menu, chrome, script tags) is embedded below as
HOME_HEAD / HOME_TAIL; the hero, rules, tools and footer come from live.json's `home` block.

Path rules (live.json body paths are written for a room page at the site root, ../assets/):
  pages here live at mockup-b/<room>/, one level deeper, so
  ../assets/...      -> ../../assets/...           (media from the repo root)
  ../demos/...       -> https://mylesparslow.com/demos/... in a new tab (separate apps)
  /<room>/#x         -> ../<room>/#x               (cross-room links stay in the theme)
  other /paths       -> https://mylesparslow.com/... in a new tab
  other http(s)      -> unchanged, new tab
"""
import html
import json
import os
import re
import runpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'mockup-b')
LIVE = os.path.join(ROOT, 'themed', 'live.json')
SITE = 'https://mylesparslow.com'

# Optional overrides for the typographic tile (projects with no image): the name in italic Fraunces on the
# room colour. Any id not listed gets a tile made from its title, split over two lines.
TILES = {
    'marketingstudio': ['Marketing', 'Studio'],
    'rsctiktok': ['TikTok on', 'autopilot'],
    'money': ['Money', 'Desk'],
    'mecfs': ['ME/CFS', 'evidence map'],
    'citationaudit': ['Guideline', 'citation audit'],
}

esc = lambda t: html.escape(html.unescape(t), quote=True)


def pad2(n):
    return '%02d' % n


def plain(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', h or ''))).strip()


def blurb(h, limit=240):
    """Plain-text summary for hover/about text: whole sentences up to ~limit characters."""
    t = plain(h)
    if len(t) <= limit:
        return t
    out = ''
    for s in re.split(r'(?<=[.!?])\s+', t):
        if out and len(out) + len(s) + 1 > limit:
            break
        out = (out + ' ' + s).strip()
    return out if len(out) <= limit + 60 else t[:limit].rsplit(' ', 1)[0] + '…'


HOME_HEAD = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Products, writing and playful builds Myles Parslow made with AI tools including Claude, ChatGPT, Codex, Suno and local models, and how they were made.">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ebe5da">
<title>Myles Parslow Portfolio</title>
<script>
(function(){var d=document.documentElement,t,go;d.classList.add('js');
try{t=localStorage.getItem('mpb-theme')}catch(e){}
if(t!=='light'&&t!=='dark'&&t!=='red')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);
var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute('content',{light:'#ebe5da',dark:'#141312',red:'#bf2400'}[t]);
if(!matchMedia('(prefers-reduced-motion: reduce)').matches){d.classList.add('anim');
var n=performance.getEntriesByType&&performance.getEntriesByType('navigation')[0],skip=n&&n.type==='back_forward';
try{go=sessionStorage.getItem('mpb-go');sessionStorage.removeItem('mpb-go');skip=skip||sessionStorage.getItem('mpb-seen')}catch(e){}
if(go&&!(n&&n.type==='back_forward'))d.classList.add('arriving');
if(!skip&&!go)d.classList.add('loading');
setTimeout(function(){if(!window.__mpbDone){d.classList.remove('anim','loading','arriving');var l=document.querySelector('.loader');if(l)l.style.display='none';var h=document.getElementById('hero');if(h)h.style.clipPath='none';}},10000);}
})();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..700,0..100,0..1;1,9..144,300..700,0..100,0..1&amp;family=Hanken+Grotesk:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="b.css">
<script>
/* Projects used to live on this page. Old links like /#conflara forward to the project's area page. */
(function () {
  var map = %%MAP%%;
  var id = decodeURIComponent(location.hash.slice(1));
  if (id && map[id]) location.replace(map[id] + '/' + location.hash);
})();
</script>
</head>
<body>
<a class="skipl" href="#rooms">Skip to the rooms</a>

<div class="loader" aria-hidden="true">
  <svg class="loader__svg" width="100%" height="100%" focusable="false"><polygon id="mRed" points="-.08,0 .24,0 .5,.66 .76,0 1.08,0 1.08,.1 .98,.1 .98,.9 1.08,.9 1.08,1 .72,1 .72,.9 .8,.9 .8,.32 .56,.86 .44,.86 .2,.32 .2,.9 .28,.9 .28,1 -.08,1 -.08,.9 .02,.9 .02,.1 -.08,.1" fill="#f23c0d"/></svg>
  <span class="loader__n">000</span>
</div>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs><clipPath id="mClip" clipPathUnits="userSpaceOnUse"><polygon id="mPoly" points="-.08,0 .24,0 .5,.66 .76,0 1.08,0 1.08,.1 .98,.1 .98,.9 1.08,.9 1.08,1 .72,1 .72,.9 .8,.9 .8,.32 .56,.86 .44,.86 .2,.32 .2,.9 .28,.9 .28,1 -.08,1 -.08,.9 .02,.9 .02,.1 -.08,.1"/><rect id="mRect" x="0" y="0" width="0" height="0"/></clipPath></defs></svg>

<div class="chrome" id="chrome">
  <a class="c tl" href="#top" aria-label="Myles Parslow, back to top" data-scramble><svg class="mark" viewBox="-.1 -.04 1.2 1.08" aria-hidden="true" focusable="false"><polygon points="-.08,0 .24,0 .5,.66 .76,0 1.08,0 1.08,.1 .98,.1 .98,.9 1.08,.9 1.08,1 .72,1 .72,.9 .8,.9 .8,.32 .56,.86 .44,.86 .2,.32 .2,.9 .28,.9 .28,1 -.08,1 -.08,.9 .02,.9 .02,.1 -.08,.1"/></svg><span class="sct" aria-hidden="true">Myles Parslow</span><span class="ctx" aria-hidden="true" hidden><span class="ctx__f"></span><span class="ctx__s"></span></span></a>
  <div class="c tr">
    <button class="theme" type="button" aria-label="In light theme. Switch to dark."><i class="sw" aria-hidden="true"></i><span class="sct">In light</span></button>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" aria-label="Menu" data-scramble><span class="sct" aria-hidden="true">Menu</span></button>
  </div>
</div>

<nav class="menu" data-lenis-prevent id="menu" aria-label="Menu" aria-hidden="true">
  <button class="menu__close" type="button" aria-label="Close menu"><span class="sct" aria-hidden="true">Close</span></button>
  <ol class="menu__list"><li><a class="mi" href="#rooms"><span class="mi__n">01</span><span class="mi__l">Rooms</span></a><ul class="menu__sub" aria-label="Rooms on this page"><li><a href="#room-legal">Legal</a></li><li><a href="#room-business">Business</a></li><li><a href="#room-creative">Creative &amp; games</a></li><li><a href="#room-design">Design &amp; 3D</a></li><li><a href="#room-research">AI &amp; research</a></li></ul></li><li><a class="mi" href="#rules"><span class="mi__n">02</span><span class="mi__l">Rules</span></a></li><li><a class="mi" href="#tools"><span class="mi__n">03</span><span class="mi__l">Tools</span></a></li><li><a class="mi" href="legal/"><span class="mi__n">04</span><span class="mi__l">Legal</span></a></li><li><a class="mi" href="business/"><span class="mi__n">05</span><span class="mi__l">Business</span></a></li><li><a class="mi" href="creative/"><span class="mi__n">06</span><span class="mi__l">Creative &amp; games</span></a></li><li><a class="mi" href="design/"><span class="mi__n">07</span><span class="mi__l">Design &amp; 3D</span></a></li><li><a class="mi" href="research/"><span class="mi__n">08</span><span class="mi__l">AI &amp; research</span></a></li></ol>
  <p class="menu__foot"><a href="mailto:mzpprojects1@gmail.com">mzpprojects1@gmail.com</a><a href="https://github.com/mylesparslow-collab">GitHub</a><a href="https://mylesparslow.com/legal-portfolio/">Legal portfolio</a></p>
</nav>

<div id="page">
<main id="top">
'''
HOME_TAIL = r'''
%%ARCHIVE%%
</main>

%%FOOT%%
</div>

<div class="toast" role="status" aria-live="polite"></div>
<svg class="curtain" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path id="cur" d="M0 -20 L100 -20 L100 130 L0 130Z"/></svg>

<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" integrity="sha384-g4NTh/Iv5PPU4xPyhEWqPcwtNXOvdaDI8LLnyYfyNZOjKJeYQyjzQ9X5275eBjpt" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" integrity="sha384-Z3REaz79l2IaAZqJsSABtTbhjgOUYyV3p90XNnAPCSHg3EMTz1fouunq9WZRtj3d" crossorigin="anonymous"></script>
<script src="https://unpkg.com/lenis@1.1.13/dist/lenis.min.js" integrity="sha384-B2WBjDzEjJpYvhmi2UyEn7rektqkf5suS6sNoyyrf0EBAwBHdkiXxIlU0V5Ru2ed" crossorigin="anonymous"></script>
<script src="b.js"></script>
</body>
</html>
'''


# ---------------------------------------------------------------- shared pieces from the shell
_shell = HOME_HEAD + HOME_TAIL
SCRIPTS = '\n'.join(re.findall(r'<script src="https://[^\n]*</script>', _shell))
assert SCRIPTS.count('<script') == 3, 'expected gsap, ScrollTrigger and lenis script tags in the shell'
FONTS = re.search(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?display=swap">', _shell, re.S).group(0)
MARK = re.search(r'<svg class="mark".*?</svg>', _shell, re.S).group(0)
MENU_HOME = re.search(r'<nav class="menu".*?</nav>', _shell, re.S).group(0)


def menu_for(slug, slugs):
    m = MENU_HOME
    m = re.sub(r'href="(#(?:rooms|rules|tools|room-[a-z]+))"', r'href="../index.html\1"', m)
    m = re.sub(r'href="(%s)/"' % '|'.join(slugs), r'href="../\1/"', m)
    m = m.replace('<nav class="menu"', '<nav class="menu" data-lenis-prevent', 1)
    m = m.replace('aria-label="Rooms on this page"', 'aria-label="Rooms on the homepage"')
    m = re.sub(r'(<a class="mi" href="\.\./%s/")' % slug, r'\1 aria-current="page"', m)
    return m


HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t,go;d.classList.add('js');
try{t=localStorage.getItem('mpb-theme')}catch(e){}
if(t!=='light'&&t!=='dark'&&t!=='red')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);
var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute('content',{light:'#ebe5da',dark:'#141312',red:'#bf2400'}[t]);
if(!matchMedia('(prefers-reduced-motion: reduce)').matches){d.classList.add('anim');
var n=performance.getEntriesByType&&performance.getEntriesByType('navigation')[0];
try{go=sessionStorage.getItem('mpb-go');sessionStorage.removeItem('mpb-go')}catch(e){}
if(go&&!(n&&n.type==='back_forward'))d.classList.add('arriving');
setTimeout(function(){d.classList.remove('arriving')},6000);}
})();
</script>"""

CHROME = """<div class="chrome" id="chrome" style="--cbg:var(--r-%(slug)s);--cfg:var(--rfg);--cacc:var(--racc)">
  <a class="c tl" href="../index.html" aria-label="Myles Parslow, home" data-scramble>%MARK%<span class="sct" aria-hidden="true">Myles Parslow</span><span class="ctx" aria-hidden="true" hidden><span class="ctx__f"></span><span class="ctx__s"></span></span></a>
  <div class="c tr">
    <button class="theme" type="button" aria-label="In light theme. Switch to dark."><i class="sw" aria-hidden="true"></i><span class="sct">In light</span></button>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" aria-label="Menu" data-scramble><span class="sct" aria-hidden="true">Menu</span></button>
  </div>
</div>"""


# ---------------------------------------------------------------- paths
def norm_media(v, up):
    """src/poster value -> path for a page `up` levels below mockup-b/ (0 = homepage)."""
    m = re.match(r'^(?:\.\./|\./|/)*(assets/.*)$', v)
    return '../' * (up + 1) + m.group(1) if m else v


def fix_urls(s, up):
    s = re.sub(r'\s(src|poster|data-[a-z-]+)="([^"]*)"',
               lambda m: ' %s="%s"' % (m.group(1), norm_media(m.group(2), up)) if m.group(2) else m.group(0), s)
    return re.sub(r'url\((["\']?)(?:\.\./|\./|/)*assets/', lambda m: 'url(%s%sassets/' % (m.group(1), '../' * (up + 1)), s)


# ---------------------------------------------------------------- thumbnails
def first_img(body):
    m = re.search(r'<img\b[^>]*\ssrc="([^"]+)"', body or '')
    return m.group(1) if m else ''


def thumb_path(c):
    """Repo-root path (assets/...) of the project's image, or '' when it has none on disk."""
    for cand in (c.get('thumb', ''), first_img(c.get('body_html', ''))):
        m = re.match(r'^(?:\.\./|\./|/)*(assets/.*)$', cand or '')
        if m and os.path.exists(os.path.join(ROOT, m.group(1))):
            return m.group(1)
    return ''


def tile_lines(c):
    if c['id'] in TILES:
        return TILES[c['id']]
    words = plain(c['title']).split()
    if len(words) < 2:
        return words or ['']
    best = min(range(1, len(words)), key=lambda i: abs(len(' '.join(words[:i])) - len(' '.join(words[i:]))))
    return [' '.join(words[:best]), ' '.join(words[best:])]


def thumb(c, letter, up):
    p = thumb_path(c)
    if p:
        return '<span class="th" aria-hidden="true"><img src="%s%s" alt="" width="560" height="350" loading="lazy" decoding="async"></span>' % ('../' * (up + 1), p)
    lines = tile_lines(c)
    fs = min(0.17, 0.84 / (max(len(x) for x in lines) * 0.5))
    return '<span class="th th--t" aria-hidden="true"><i>%s</i><b style="--fs:%.3f">%s</b></span>' % (letter, fs, '<br>'.join(esc(x) for x in lines))


def tile_width(n):
    rows = (n + 1) // 2
    if rows <= 3:
        return 'clamp(96px,11vw,176px)'
    if rows <= 5:
        return 'clamp(84px,8.5vw,140px)'
    return 'clamp(72px,6.5vw,112px)'


# ---------------------------------------------------------------- body rewriting (room pages, up=1)
def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def add_class(tag, cls):
    m = re.search(r'\sclass="([^"]*)"', tag)
    if m:
        if cls in m.group(1).split():
            return tag
        return tag[:m.start()] + ' class="%s %s"' % (m.group(1), cls) + tag[m.end():]
    return tag.replace('>', ' class="%s">' % cls, 1) if not tag.endswith('/>') else tag[:-2] + ' class="%s"/>' % cls


def portrait(tag):
    w, h = attr(tag, 'width'), attr(tag, 'height')
    try:
        return int(h) > int(w) * 1.15
    except (TypeError, ValueError):
        return False


def fix_img(m):
    t = m.group(0)
    if 'loading=' not in t:
        t = t.replace('<img', '<img loading="lazy"', 1)
    if 'decoding=' not in t:
        t = t.replace('<img', '<img decoding="async"', 1)
    if portrait(t):
        t = add_class(t, 'portrait')
    return t


def fix_video(m):
    t = m.group(0)
    t = re.sub(r'\spreload="[^"]*"', '', t)
    t = t.replace('<video', '<video preload="metadata"', 1)
    for need in ('controls', 'playsinline'):
        if not re.search(r'\s%s[\s>=]' % need, t):
            t = t.replace('<video', '<video ' + need, 1)
    if portrait(t):
        t = add_class(t, 'portrait')
    return t


def fix_a(m, slug, slugs):
    t = m.group(0)
    h = attr(t, 'href')
    if h is None:
        return t
    new, ext = h, False
    room = '|'.join(slugs)
    mm = re.match(r'^(?:\.\./|/)?(?:%s)/' % room, h) if h else None
    if re.match(r'^(?:\.\./|\./|/)*assets/', h):
        new, ext = norm_media(h, 1), True
    elif re.match(r'^(?:\.\./|\./|/)*demos/', h):
        new, ext = SITE + '/' + re.sub(r'^(?:\.\./|\./|/)*', '', h), True
    elif mm and not h.startswith('./'):
        rest = re.sub(r'^(?:\.\./|/)', '', h)
        if rest.startswith(slug + '/'):
            new = rest[len(slug) + 1:] or '#top'
            if new == '':
                new = '#top'
        else:
            new = '../' + rest
    elif re.match(r'^/[^/]', h):
        new, ext = SITE + h, True
    elif re.match(r'^https?://', h):
        ext = True
    if new != h:
        t = t.replace('href="%s"' % h, 'href="%s"' % new, 1)
    if ext and 'target=' not in t:
        t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
    return t


def fix_body(b, slug, slugs):
    b = fix_urls(b, 1)
    b = re.sub(r'<img\b[^>]*>', fix_img, b)
    b = re.sub(r'<video\b[^>]*>', fix_video, b)
    b = re.sub(r'<a\b[^>]*>', lambda m: fix_a(m, slug, slugs), b)

    def cmp_div(m):
        w, h = int(m.group(2)), int(m.group(3))
        return m.group(0) if w >= h * 0.87 else m.group(0).replace('class="compare"', 'class="compare portrait"', 1)
    b = re.sub(r'<div class="compare"( style="aspect-ratio:\s*(\d+)\s*/\s*(\d+)[^"]*")', cmp_div, b)
    return b


# ---------------------------------------------------------------- room page
def page(r, idx, rooms):
    slug, name, short, letter = r['slug'], r['title'], r['short'], r['letter']
    slugs = [x['slug'] for x in rooms]
    items = r['items']
    cases = [i for i in items if i['kind'] == 'case']
    n = len(cases)
    prev = rooms[(idx - 1) % len(rooms)]
    nxt = rooms[(idx + 1) % len(rooms)]
    fb = lambda h: fix_body(h, slug, slugs)
    rows = ''.join(
        '<li><a class="row" href="#%s"><span class="row__i" aria-hidden="true">%s</span><span class="row__t"><span class="row__n">%s</span><span class="row__s">%s</span></span>%s</a></li>'
        % (c['id'], pad2(i), esc(c['title']), esc(c.get('sub', '')), thumb(c, letter, 1)) for i, c in enumerate(cases, 1))

    def chap(c):
        kick = ''.join('<span class="chap__k">%s</span>' % esc(k) for k in c.get('kickers', []) if k)
        links = c.get('links_html', '')
        return """<article class="chap" id="%(id)s" data-chrome="%(name)s" data-short="%(short)s" aria-labelledby="t-%(id)s">
  <div class="chap__top">
    <p class="chap__n"><span class="chap__c">%(count)s</span>%(kick)s</p>
    <h2 class="chap__t" id="t-%(id)s" data-words>%(title)s</h2>
    <p class="chap__sub">%(sub)s</p>
    <p class="chap__lede" data-fade>%(lede)s</p>
  </div>
  <div class="cbody">
%(body)s%(links)s
  </div>
  <p class="chap__end"><a href="#index">Back to the index <span aria-hidden="true">&uarr;</span></a></p>
</article>""" % dict(id=c['id'], name=name, short=short, count=esc(c.get('count', '')), kick=kick, title=esc(c['title']),
                     sub=esc(c.get('sub', '')), lede=fb(c.get('lede', '')), body=fb(c.get('body_html', '')).strip(),
                     links=('\n' + fb(links).strip()) if links else '')

    last_case = max(i for i, x in enumerate(items) if x['kind'] == 'case')
    inner, tail = [], []
    for i, x in enumerate(items):
        s = chap(x) if x['kind'] == 'case' else fb(x['html']).strip()
        (tail if (x['kind'] == 'extra' and i > last_case) else inner).append(s)
    pn = []
    for label, o in (('Previous room', prev), ('Next room', nxt)):
        isprev = label.startswith('Prev')
        pn.append('<a class="pn__a %s" href="../%s/" style="--room:var(--r-%s)"><span class="eyebrow">%s%s</span><span class="pn__l" aria-hidden="true">%s</span><span class="pn__t">%s</span></a>'
                  % ('prev' if isprev else 'next', o['slug'], o['slug'], '&larr; ' if isprev else '', label + ('' if isprev else ' &rarr;'), o['letter'], o['title']))
    desc = esc(blurb(r['lede'], 300))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="%(desc)s">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ebe5da">
<title>%(plain)s &middot; Myles Parslow Portfolio</title>
%(head)s
%(fonts)s
<link rel="stylesheet" href="../b.css">
<link rel="stylesheet" href="../rooms.css">
</head>
<body class="roompage" data-room="%(slug)s">
<a class="skipl" href="#index">Skip to the projects</a>

%(chrome)s

%(menu)s

<div id="page">
<main id="top">
<header class="rhead" id="rhead" data-chrome="%(name)s" data-short="%(short)s" data-ground="%(slug)s" style="--room:var(--r-%(slug)s)" aria-labelledby="h-room">
  <span class="rhead__letter" aria-hidden="true">%(letter)s</span>
  <div class="rhead__main">
    <p class="eyebrow">Room %(num)d of %(nr)d</p>
    <h1 class="rhead__t" id="h-room">%(name)s</h1>
    <p class="rhead__count">%(n)d projects</p>
    <p class="rhead__lede">%(lede)s</p>
  </div>
  <nav class="rindex" id="index" aria-label="%(plain)s projects">
    <ol class="rindex__list">%(rows)s</ol>
  </nav>
</header>

<div class="chapters">
%(chaps)s
</div>
%(extras)s

<nav class="pn" aria-label="Other rooms">
  %(pn)s
</nav>
</main>

<footer class="foot foot--room" id="contact">
  <a class="back" href="../index.html#rooms"><span class="sct">Back to the rooms</span> <span aria-hidden="true">&uarr;</span></a>
  <p class="toolslink"><a href="../index.html#tools">Which AI for what <span>by project</span> <i aria-hidden="true">&rarr;</i></a></p>
  <a class="mail" href="mailto:mzpprojects1@gmail.com" data-copy="mzpprojects1@gmail.com" aria-label="Copy email address mzpprojects1@gmail.com" data-scramble><span class="sct" aria-hidden="true">mzpprojects1@gmail.com</span></a>
  <div class="foot__row">
    <a href="https://github.com/mylesparslow-collab" target="_blank" rel="noopener">GitHub</a>
    <a href="https://mylesparslow.com/legal-portfolio/" target="_blank" rel="noopener">Legal portfolio</a>
    <a href="#top">Back to top &uarr;</a>
    <span>Myles Parslow &middot; Made with AI</span>
  </div>
</footer>
</div>

<div class="toast" role="status" aria-live="polite"></div>
<svg class="curtain" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path id="cur" d="M0 -20 L100 -20 L100 130 L0 130Z"/></svg>

%(scripts)s
<script src="../b.js"></script>
<script src="../rooms.js"></script>
</body>
</html>
""" % dict(desc=desc, plain=esc(name), head=HEAD_SCRIPT, fonts=FONTS, slug=slug,
           chrome=CHROME.replace('%(slug)s', slug).replace('%MARK%', MARK), menu=menu_for(slug, slugs),
           name=name, short=short, letter=letter, num=idx + 1, nr=len(rooms), n=n, lede=fb(r['lede']), rows=rows,
           chaps='\n\n'.join(inner), extras='\n'.join(tail), pn='\n  '.join(pn), scripts=SCRIPTS)


# ---------------------------------------------------------------- homepage
def home_rooms(rooms):
    out = ['<div class="rooms" id="rooms">']
    for idx, r in enumerate(rooms, 1):
        slug, letter = r['slug'], r['letter']
        cases = [i for i in r['items'] if i['kind'] == 'case']
        about = blurb(r['lede'], 200)
        rows = ''.join(
            '<li><a class="row" href="%s/#%s" data-about="%s"><span class="row__t"><span class="row__n">%s</span><span class="row__s">%s</span></span>%s</a></li>'
            % (slug, c['id'], esc(blurb(c.get('lede', ''))), esc(c['title']), esc(c.get('sub', '')), thumb(c, letter, 0)) for c in cases)
        out.append("""<div class="slot" aria-hidden="true"></div>
<section class="room" id="room-%(slug)s" data-room="%(i)d" data-chrome="%(name)s" data-short="%(short)s" data-ground="%(slug)s" style="--room:var(--r-%(slug)s);--rows:%(rows)d;--tw:%(tw)s" aria-labelledby="h-%(slug)s">
<span class="room__shade" aria-hidden="true"></span>
<div class="room__side"><span class="room__letter" aria-hidden="true">%(letter)s</span>
<div class="room__head"><h2 id="h-%(slug)s" class="room__title">%(name)s</h2><p class="room__count">%(n)d projects</p></div>
<p class="room__about" data-default="%(about)s">%(about)s</p>
<a class="room__open" href="%(slug)s/"><span class="sct">Open room</span> <i aria-hidden="true">&rarr;</i></a></div>
<ul class="room__list" aria-label="%(name)s projects">%(list)s</ul>
</section>""" % dict(slug=slug, i=idx, name=r['title'], short=r['short'], rows=(len(cases) + 1) // 2, tw=tile_width(len(cases)),
                     letter=letter, n=len(cases), about=esc(about), list=rows))
    out.append('</div>')
    return '\n'.join(out)


def home_hero(h, rooms, total, ids):
    h = fix_urls(h, 0)
    # keep only frame slides whose target project exists in the data
    def keep(m):
        t = re.search(r'data-h="[^"#]*/#([^"]+)"', m.group(0))
        return m.group(0) if (not t or t.group(1) in ids) else ''
    h = re.sub(r'<img\b[^>]*data-h="[^"]*"[^>]*>', keep, h)
    h = re.sub(r'(<span class="hero__count">)[^<]*(</span>)', r'\g<1>%d projects &middot; %d rooms\g<2>' % (total, len(rooms)), h)
    n = len(re.findall(r'<img\b', re.search(r'<div class="frame".*?</div>', h, re.S).group(0)))
    h = re.sub(r'(<span class="ctl__n"[^>]*>)[^<]*(</span>)', r'\g<1>01 / %s\g<2>' % pad2(n), h)
    return h


def redirect_map(live, rooms):
    """Old homepage #id -> room slug. The live map first, then every id this version renders."""
    try:
        m = json.loads(live['home'].get('redirect_map') or '{}')
    except ValueError:
        m = {}
    for r in rooms:
        for i in r['items']:
            if i.get('id'):
                m.setdefault(i['id'], r['slug'])
    return json.dumps(m, separators=(',', ':'))


def archive(total):
    return ('<section class="archive" id="archive" aria-labelledby="h-archive"><p class="eyebrow" id="h-archive">Style archive</p>'
            '<p class="archive__t">You&rsquo;re looking at: Five Rooms. This site is also a running design experiment. Each version renders the same %d case studies '
            'in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
            '<a class="archive__a" href="../styles/index.html">See every version <span aria-hidden="true">&rarr;</span></a></p></section>' % total)


def home_page(live, rooms):
    total = sum(1 for r in rooms for i in r['items'] if i['kind'] == 'case')
    ids = {i['id'] for r in rooms for i in r['items'] if i.get('id')}
    hm = live['home']
    foot = fix_urls(hm['foot_html'], 0)
    page_ = (HOME_HEAD.replace('%%MAP%%', redirect_map(live, rooms)) + home_hero(hm['hero_html'], rooms, total, ids)
             + '\n\n' + home_rooms(rooms) + '\n\n' + fix_urls(hm['rules_html'], 0) + '\n\n' + fix_urls(hm['tools_html'], 0)
             + HOME_TAIL.replace('%%FOOT%%', foot))
    return page_.replace('%%ARCHIVE%%', archive(total))


def main():
    live = json.load(open(LIVE, encoding='utf-8'))
    rooms = live['rooms']
    for r in rooms:
        r['_n'] = sum(1 for i in r['items'] if i['kind'] == 'case')
    with open(os.path.join(B, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(home_page(live, rooms))
    total = 0
    for idx, r in enumerate(rooms):
        out = os.path.join(B, r['slug'])
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(page(r, idx, rooms))
        total += r['_n']
        print('wrote mockup-b/%s/index.html (%d case studies)' % (r['slug'], r['_n']))
    print('wrote mockup-b/index.html; %d case studies in %d rooms' % (total, len(rooms)))


if __name__ == '__main__':
    main()


# style switcher (see add_switcher.py): adds the Style dropdown script tag to all six pages of this version
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'add_switcher.py'), run_name='__main__')
