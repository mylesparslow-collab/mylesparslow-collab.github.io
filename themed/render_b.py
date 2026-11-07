#!/usr/bin/env python3
"""Generate the in-theme room pages for mockup B.

    python3 themed/render_b.py

Reads themed/cases.json (made by extract_cases.py from the live area pages) and the
homepage mockup-b/index.html (for the shared menu, chrome and script tags), and writes
mockup-b/<slug>/index.html for legal, business, creative, design and research.
Stdlib only. Safe to re-run; it only writes those five files.

Path rules (pages live at mockup-b/<slug>/):
  assets/...            -> ../../assets/...           (media from the repo root)
  demos/...             -> https://mylesparslow.com/demos/... in a new tab (separate apps)
  legal/#x etc.         -> ../legal/#x                (cross-room links stay in the theme)
  other http(s) links   -> unchanged, new tab
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'mockup-b')
CASES = os.path.join(ROOT, 'themed', 'cases.json')

ROOMS = [  # slug, name, short, letter
    ('legal', 'Legal', 'Legal', 'L'),
    ('business', 'Business', 'Business', 'B'),
    ('creative', 'Creative &amp; games', 'Creative', 'C'),
    ('design', 'Design &amp; 3D', 'Design', 'D'),
    ('research', 'AI &amp; research', 'Research', 'R'),
]
SLUGS = [r[0] for r in ROOMS]

# Projects without a screenshot get a typographic tile: the name in italic Fraunces on the room colour.
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


# ---------------------------------------------------------------- shared pieces from the homepage
home = open(os.path.join(B, 'index.html'), encoding='utf-8').read()
SCRIPTS = '\n'.join(re.findall(r'<script src="https://[^\n]*</script>', home))
assert SCRIPTS.count('<script') == 3, 'expected gsap, ScrollTrigger and lenis script tags on the homepage'
FONTS = re.search(r'<link rel="preconnect" href="https://fonts.googleapis.com">.*?display=swap">', home, re.S).group(0)
MARK = re.search(r'<svg class="mark".*?</svg>', home, re.S).group(0)
# the homepage rows carry each project's own short tagline (cases.json 'sub' is the live page's group label)
TAGS = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
    r'<a class="row" href="[a-z]+/#([^"]+)"[^>]*><span class="row__t"><span class="row__n">(.*?)</span><span class="row__s">(.*?)</span>', home)}
MENU_HOME = re.search(r'<nav class="menu".*?</nav>', home, re.S).group(0)


def menu_for(slug):
    m = MENU_HOME
    m = re.sub(r'href="(#(?:rooms|rules|tools|room-[a-z]+))"', r'href="../index.html\1"', m)
    m = re.sub(r'href="(%s)/"' % '|'.join(SLUGS), r'href="../\1/"', m)
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


# ---------------------------------------------------------------- thumbnails
def thumb(cid, letter):
    if cid in TILES:
        lines = TILES[cid]
        fs = min(0.17, 0.84 / (max(len(x) for x in lines) * 0.5))
        return '<span class="th th--t" aria-hidden="true"><i>%s</i><b style="--fs:%.3f">%s</b></span>' % (letter, fs, '<br>'.join(esc(x) for x in lines))
    return '<span class="th" aria-hidden="true"><img src="../../assets/thumbs-hd/%s.jpg" alt="" width="560" height="350" loading="lazy" decoding="async"></span>' % cid


# ---------------------------------------------------------------- body rewriting
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
    t = re.sub(r'\ssrc="(assets/[^"]+)"', r' src="../../\1"', t)
    if 'loading=' not in t:
        t = t.replace('<img', '<img loading="lazy"', 1)
    if 'decoding=' not in t:
        t = t.replace('<img', '<img decoding="async"', 1)
    if portrait(t):
        t = add_class(t, 'portrait')
    return t


def fix_video(m):
    t = m.group(0)
    t = re.sub(r'\s(src|poster)="(assets/[^"]+)"', r' \1="../../\2"', t)
    t = re.sub(r'\spreload="[^"]*"', '', t)
    t = t.replace('<video', '<video preload="metadata"', 1)
    for need in ('controls', 'playsinline'):
        if not re.search(r'\s%s[\s>=]' % need, t):
            t = t.replace('<video', '<video ' + need, 1)
    if portrait(t):
        t = add_class(t, 'portrait')
    return t


def fix_a(m, slug):
    t = m.group(0)
    h = attr(t, 'href')
    if h is None:
        return t
    new, ext = h, False
    if h.startswith('demos/'):
        new, ext = 'https://mylesparslow.com/' + h, True
    elif h.startswith('assets/'):
        new, ext = '../../' + h, True
    elif re.match(r'^(%s)/' % '|'.join(SLUGS), h):
        if h.startswith(slug + '/'):
            new = h[len(slug) + 1:] or '#top'
            if new == '':
                new = '#index'
        else:
            new = '../' + h
    elif re.match(r'^https?://', h):
        ext = True
    t = t.replace('href="%s"' % h, 'href="%s"' % new, 1)
    if ext and 'target=' not in t:
        t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
    return t


def fix_body(b, slug):
    b = re.sub(r'<img\b[^>]*>', fix_img, b)
    b = re.sub(r'<video\b[^>]*>', fix_video, b)
    b = re.sub(r'<a\b[^>]*>', lambda m: fix_a(m, slug), b)

    def cmp_div(m):
        w, h = int(m.group(2)), int(m.group(3))
        return m.group(0) if w >= h * 0.87 else m.group(0).replace('class="compare"', 'class="compare portrait"', 1)
    b = re.sub(r'<div class="compare"( style="aspect-ratio:\s*(\d+)\s*/\s*(\d+)[^"]*")', cmp_div, b)
    return b


# ---------------------------------------------------------------- page
def page(area, idx, data):
    slug, name, short, letter = area
    cases = data['cases']
    n = len(cases)
    prev = ROOMS[(idx - 1) % 5]
    nxt = ROOMS[(idx + 1) % 5]
    lede = esc(data['lede'])
    rows = []
    for i, c in enumerate(cases, 1):
        rows.append(
            '<li><a class="row" href="#%s"><span class="row__i" aria-hidden="true">%s</span><span class="row__t"><span class="row__n">%s</span><span class="row__s">%s</span></span>%s</a></li>'
            % (c['id'], pad2(i), TAGS.get(c['id'], (esc(c['title']), esc(c['sub'])))[0], TAGS.get(c['id'], (esc(c['title']), esc(c['sub'])))[1], thumb(c['id'], letter)))
    chaps = []
    for i, c in enumerate(cases, 1):
        kind = re.sub(r'^(Companion to )?[Cc]ase study( \d+)?\s*·?\s*', '', c['eyebrow']).strip(' ·')
        chaps.append("""<article class="chap" id="%(id)s" data-chrome="%(name)s" data-short="%(short)s" aria-labelledby="t-%(id)s">
  <div class="chap__top">
    <p class="chap__n"><span class="chap__c">%(i)s / %(n)s</span><span class="chap__k">%(kind)s</span><span class="chap__k">%(group)s</span></p>
    <h2 class="chap__t" id="t-%(id)s" data-words>%(title)s</h2>
    <p class="chap__sub">%(tag)s</p>
    <p class="chap__lede" data-fade>%(sum)s</p>
  </div>
  <div class="cbody">
%(body)s
  </div>
  <p class="chap__end"><a href="#index">Back to the index <span aria-hidden="true">&uarr;</span></a></p>
</article>""" % dict(id=c['id'], name=name, short=short, i=pad2(i), n=pad2(n), kind=esc(kind), title=esc(c['title']),
                     group=esc(c['sub']), tag=TAGS.get(c['id'], ('', esc(c['sub'])))[1], sum=esc(c['sum']), body=fix_body(c['body_html'], slug).strip()))
    # group dividers (ids g-...) go before the first chapter of each group; extras close the room
    byid = {}
    for c, ch in zip(cases, chaps):
        byid[c['id']] = ch
    seq = []
    for g in data['groups']:
        if g['title']:
            seq.append('<div class="gdiv" id="%s" data-chrome="%s" data-short="%s"><h2 class="gdiv__t">%s</h2>%s</div>' % (
                g['id'], name, short, esc(g['title']), '<p class="gdiv__p">%s</p>' % esc(g['intro']) if g['intro'] else ''))
        else:
            seq.append('<span class="gdiv-anchor" id="%s"></span>' % g['id'])
        seq.extend(byid[i] for i in g['cases'])
    assert len(seq) - len(data['groups']) == len(chaps)
    chaps = seq
    extras = ''.join(
        '<section class="xsec" id="more-%s" data-chrome="%s" data-short="%s" aria-labelledby="t-more-%s"><div class="xsec__h"><p class="eyebrow">%s</p><h2 class="xsec__t" id="t-more-%s">%s</h2></div>'
        '<div class="xsec__list">%s</div></section>' % (
            x['group'], name, short, x['group'], esc(x['eyebrow']), x['group'], esc(x['title']),
            ''.join('<div><h3>%s</h3><p>%s</p></div>' % (esc(i['title']), i['html']) for i in x['items']))
        for x in data['extras'])
    pn = []
    for label, r in (('Previous room', prev), ('Next room', nxt)):
        pn.append('<a class="pn__a %s" href="../%s/" style="--room:var(--r-%s)"><span class="eyebrow">%s%s</span><span class="pn__l" aria-hidden="true">%s</span><span class="pn__t">%s</span></a>'
                  % ('prev' if label.startswith('Prev') else 'next', r[0], r[0],
                     '&larr; ' if label.startswith('Prev') else '', label + (' &rarr;' if label.startswith('Next') else ''), r[3], r[1]))
    desc = esc(data['lede'])
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
    <p class="eyebrow">Room %(num)d of 5</p>
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
""" % dict(desc=desc, plain=esc(name), head=HEAD_SCRIPT, fonts=FONTS, slug=slug, chrome=CHROME.replace('%(slug)s', slug).replace('%MARK%', MARK), menu=menu_for(slug),
           name=name, short=short, letter=letter, num=idx + 1, n=n, lede=lede, rows=''.join(rows), chaps='\n\n'.join(chaps), extras=extras,
           pn='\n  '.join(pn), scripts=SCRIPTS)


def main():
    data = json.load(open(CASES, encoding='utf-8'))
    by = {a['slug']: a for a in data['areas']}
    total = 0
    for idx, area in enumerate(ROOMS):
        d = by[area[0]]
        out = os.path.join(B, area[0])
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(page(area, idx, d))
        total += len(d['cases'])
        print('wrote mockup-b/%s/index.html (%d case studies)' % (area[0], len(d['cases'])))
    print('%d case studies in 5 rooms' % total)


if __name__ == '__main__':
    main()
