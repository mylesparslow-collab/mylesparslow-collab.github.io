#!/usr/bin/env python3
"""Build mockup G, "Sticker Wall": the portfolio as a wall of chunky, draggable stickers on colour slabs.

    python3 -I themed/render_g.py

Reads themed/live.json and writes mockup-g/index.html, mockup-g/<room>/index.html,
mockup-g/g.css and mockup-g/g.js. Stdlib only. Safe to re-run.

Path rules: body markup is written for a room page at the site root, so from
mockup-g/<room>/ every "../" gains one more "../" (assets and demos live at the repo root).
"""
import html
import json
import os
import re
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-g')
LIVE = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))


def _fill_cases(data):
    """Treat keys that live.json omits on some cases (links_html, thumb, ...) as empty."""
    for room in data['rooms']:
        for it in room['items']:
            if it.get('kind') == 'case':
                for k in ('links_html', 'thumb', 'sub', 'lede', 'body_html', 'count', 'title'):
                    it.setdefault(k, '')
                it.setdefault('kickers', [])
    n = sum(1 for room in data['rooms'] for it in room['items'] if it.get('kind') == 'case')
    h = data['home']
    h['hero_html'] = re.sub(r'(hero__count">)\d+( projects)', lambda m: m.group(1) + str(n) + m.group(2), h['hero_html'])
    return data
_fill_cases(LIVE)
HOME = LIVE['home']
ROOMS = LIVE['rooms']
MAIL = 'mzpprojects1@gmail.com'
unesc = html.unescape
esc = lambda t: html.escape(t, quote=True)

INK, PAPER, WHITE = '#1a1033', '#fff7ea', '#ffffff'
TOMATO, BUTTER, VIOLET, MINT = '#ff4a2b', '#ffd84a', '#5b3df5', '#7ee0b5'

# room -> (fill, text on fill, alt fill (bands, buttons), text on alt, sticker outline on the slab)
RM = {
    'legal':    dict(c=VIOLET, f=WHITE, a=BUTTER, af=INK, so=INK),
    'business': dict(c=MINT,   f=INK,   a=TOMATO, af=INK, so=INK),
    'creative': dict(c=TOMATO, f=INK,   a=BUTTER, af=INK, so=INK),
    'design':   dict(c=BUTTER, f=INK,   a=VIOLET, af=WHITE, so=INK),
    'research': dict(c=INK,    f=MINT,  a=MINT,   af=INK, so=PAPER),
}
# sticker fills (fill, text)
STK = {'tomato': (TOMATO, INK), 'butter': (BUTTER, INK), 'violet': (VIOLET, WHITE), 'mint': (MINT, INK), 'paper': (PAPER, INK)}
SLAB_OF = {'legal': 'violet', 'business': 'mint', 'creative': 'tomato', 'design': 'butter', 'research': 'ink'}
BLOBS = ['999px', '34px 70px 40px 64px / 56px 34px 58px 40px', '60px 36px 64px 30px / 38px 54px 36px 56px',
         '28px', '50px 28px 50px 28px / 40px 40px 40px 40px']

for i, r in enumerate(ROOMS):
    r['i'] = i
    r['plain'] = unesc(r['title'])
    r['nproj'] = sum(1 for it in r['items'] if it['kind'] == 'case')
    r.update(RM[r['slug']])
BY = {r['slug']: r for r in ROOMS}


def seed(s, salt=''):
    return zlib.crc32((s + salt).encode())


def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b):
    """Deepen relative paths by one level and open outbound/demo links in a new tab."""
    b = re.sub(r'((?:src|href|poster)=")\.\./', r'\1../../', b)

    def a(m):
        t = m.group(0)
        h = attr(t, 'href') or ''
        if (re.match(r'https?://', h) or h.startswith('../../demos/') or h.startswith('../../assets/')) and 'target=' not in t:
            t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
        elif 'target="_blank"' in t and 'rel=' not in t:
            t = t.replace('<a ', '<a rel="noopener" ', 1)
        return t
    return re.sub(r'<a\b[^>]*>', a, b)


def strip_tags(t):
    return unesc(re.sub(r'<[^>]+>', '', t)).strip()


# ------------------------------------------------------------------ shared chrome
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&family=Unbounded:wght@800&display=swap">')

HOUSE = ('<svg class="ico" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">'
         '<path d="M3 11.5 12 4l9 7.5M5.5 10v10h13V10M10 20v-6h4v6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def head_script(home):
    s = ("<script>(function(){var d=document.documentElement,t;d.classList.add('js');"
         "try{t=localStorage.getItem('sw-theme')}catch(e){}"
         "if(t!=='dark'&&t!=='light')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';"
         "d.setAttribute('data-theme',t);")
    if home:
        s += ("var M=@@MAP@@,h=location.hash.slice(1);"
              "if(h&&M[h]){location.replace(M[h]+'/index.html'+(h==='g-'+M[h]?'':'#'+h));return}")
    s += "})()</script>"
    return s.replace('@@MAP@@', HOME['redirect_map']) if home else s


def topbar(depth, cur):
    up = '../' * depth
    chips = []
    for r in ROOMS:
        is_cur = r['slug'] == cur
        href = (up + 'index.html') if is_cur else ('%s%s/index.html' % (up, r['slug']) if depth == 0 else '../%s/index.html' % r['slug'])
        if depth == 0:
            href = '%s/index.html' % r['slug']
        chips.append('<li><a class="chip chip-%s%s" href="%s"%s style="--c:%s;--cf:%s"><i class="dot" aria-hidden="true"></i>%s</a></li>' % (
            r['slug'], ' is-cur' if is_cur else '', href, ' aria-current="page" title="Back to Home"' if is_cur else '',
            r['c'], r['f'], r['short']))
    return ('<header class="topbar"><nav class="bar" aria-label="Site">'
            '<a class="home%s" href="%sindex.html"%s>%s<span>Home</span></a>'
            '<ul class="chips">%s</ul>'
            '<button class="theme" id="theme" type="button" aria-pressed="false" aria-label="Dark mode"><span class="theme__i" aria-hidden="true"></span><span class="theme__t">Dark</span></button>'
            '</nav></header>') % (' is-cur' if cur == 'home' else '', up, ' aria-current="page"' if cur == 'home' else '', HOUSE, ''.join(chips))


def page(title, desc, depth, cls, inner, home=False):
    up = '../' * depth
    return """<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="@@DESC@@">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#ff4a2b">
<title>@@TITLE@@</title>
<link rel="icon" href="data:,">
@@HEAD@@
@@FONTS@@
<link rel="stylesheet" href="@@UP@@g.css">
</head>
<body class="@@CLS@@">
<a class="skip" href="#main">@@SKIP@@</a>
@@INNER@@
<script src="@@UP@@g.js" defer></script>
</body>
</html>
""".replace('@@DESC@@', esc(desc)).replace('@@TITLE@@', esc(title)).replace('@@HEAD@@', head_script(home)).replace(
        '@@FONTS@@', FONTS).replace('@@UP@@', up).replace('@@SKIP@@', 'Skip to the rooms' if home else 'Skip to the projects').replace('@@CLS@@', cls).replace('@@INNER@@', inner)


# ------------------------------------------------------------------ homepage
def hero():
    h = HOME['hero_html']
    count = re.search(r'class="hero__count">(.*?)</span>', h, re.S).group(1)
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', h, re.S).group(1)
    stats = re.findall(r'<div><dt>(.*?)</dt><dd>(.*?)</dd></div>', re.search(r'<dl class="stats">.*?</dl>', h, re.S).group(0), re.S)
    badges = ''.join('<div class="badge b%d"><dd>%s</dd><dt>%s</dt></div>' % (i, dd, dt) for i, (dt, dd) in enumerate(stats))
    return """<header class="hero" id="top" data-fitbox>
<span class="deco d1" aria-hidden="true"></span><span class="deco d2" aria-hidden="true"></span>
<h1 class="hero__name" aria-label="Myles Parslow"><span class="fit" data-cap="340">Myles</span><span class="fit" data-cap="340">Parslow</span></h1>
<p class="hero__pill"><span>makes things with AI.</span></p>
<div class="hero__grid">
<div class="hero__txt"><p class="hero__count">@@COUNT@@</p><p class="lede">@@LEDE@@</p><p class="hero__hint">Psst: every sticker below can be picked up and moved. Tap one to open it.</p></div>
<dl class="badges">@@BADGES@@</dl>
</div>
</header>""".replace('@@COUNT@@', count).replace('@@LEDE@@', lede).replace('@@BADGES@@', badges)


def sticker(r, it, k):
    sd = seed(it['id'])
    rot = ((sd % 1201) / 100.0) - 6.0
    slab = SLAB_OF[r['slug']]
    names = [n for n in ('tomato', 'butter', 'violet', 'mint', 'paper') if n != slab]
    nm = names[(sd >> 5) % len(names)]
    if k and (sd >> 9) % 3 == 0:  # nudge neighbours apart in colour
        nm = names[((sd >> 5) + k) % len(names)]
    fill, fg = STK[nm]
    blob = BLOBS[(sd >> 11) % len(BLOBS)]
    mt = (sd >> 14) % 18
    mx = -(((sd >> 18) % 5) + 2)
    return ('<li class="st" style="--mt:%dpx;--mx:%dpx"><a class="sticker" href="%s/index.html#%s" draggable="false" '
            'style="--r:%.2fdeg;--bg:%s;--fg:%s;--rad:%s">'
            '<b class="st__t">%s</b><span class="st__s">%s</span></a></li>') % (
        mt, mx, r['slug'], it['id'], rot, fill, fg, blob, it['title'], it['sub'])


def slab(r):
    stickers = ''.join(sticker(r, it, k) for k, it in enumerate([x for x in r['items'] if x['kind'] == 'case']))
    full = ''
    if r['plain'] != r['short']:
        full = '<span class="pill">%s</span>' % r['title']
    return """<section class="slab slab-@@S@@" id="room-@@S@@" aria-labelledby="h-@@S@@" style="--c:@@C@@;--cf:@@F@@;--so:@@SO@@;--a:@@A@@;--af:@@AF@@" data-fitbox>
<div class="slab__top"><p class="eyebrow">@@EY@@</p><span class="pill">@@CNT@@</span>@@FULL@@</div>
<h2 class="slab__name" id="h-@@S@@"><a class="fit" data-cap="200" data-min="48" href="@@S@@/index.html">@@SHORT@@</a></h2>
<p class="slab__lede">@@LEDE@@</p>
<ul class="wall" aria-label="@@SHORT@@ projects">@@STICKERS@@</ul>
<div class="slab__foot"><button class="tidy" type="button">Tidy up</button><a class="open" href="@@S@@/index.html">Open @@SHORT@@<span aria-hidden="true"> &rarr;</span></a></div>
</section>""".replace('@@S@@', r['slug']).replace('@@C@@', r['c']).replace('@@F@@', r['f']).replace('@@SO@@', r['so']).replace(
        '@@A@@', r['a']).replace('@@AF@@', r['af']).replace('@@EY@@', r['eyebrow']).replace('@@CNT@@', r['count']).replace(
        '@@FULL@@', full).replace('@@SHORT@@', r['short']).replace('@@LEDE@@', r['lede']).replace('@@STICKERS@@', stickers)


def rules():
    h = HOME['rules_html']
    eyebrow = re.search(r'<p class="eyebrow">(.*?)</p>', h, re.S).group(1)
    title = re.search(r'<h2[^>]*>(.*?)</h2>', h, re.S).group(1)
    items = re.findall(r'<li class="rule"><span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p></li>', h, re.S)
    cols = [('violet', VIOLET, WHITE), ('butter', BUTTER, INK), ('mint', MINT, INK)]
    lis = ''.join('<li class="rule rule%d" style="--bg:%s;--fg:%s"><span class="rule__n">%s</span><h3>%s</h3><p>%s</p></li>' % (
        i, cols[i][1], cols[i][2], n, t, p) for i, (n, t, p) in enumerate(items))
    return ('<section class="rules paper" id="rules" aria-labelledby="h-rules"><p class="eyebrow">%s</p>'
            '<h2 class="sec-title" id="h-rules">%s</h2><ol class="rules__list">%s</ol></section>') % (eyebrow, title, lis)


def tools():
    h = HOME['tools_html']
    eyebrow = re.search(r'<p class="eyebrow">(.*?)</p>', h, re.S).group(1)
    title = re.search(r'<h2[^>]*>(.*?)</h2>', h, re.S).group(1)
    lede = re.search(r'<p class="sec-lede">(.*?)</p>', h, re.S).group(1)
    summ = re.search(r'<summary><span class="sct">(.*?)</span></summary>', h, re.S)
    rows = []
    for art in re.findall(r'<article class="trow">(.*?)</article>', h, re.S):
        name = re.search(r'<h3>(.*?)</h3>', art, re.S).group(1)
        tcs = re.findall(r'<span class="lab">(.*?)</span><p>(.*?)</p>', art, re.S)
        cs = []
        for lab, p in tcs:
            cs.append(p if lab in ('Built with', 'Runs on') else '<b class="lab">%s:</b> %s' % (lab, p))
        cs += [''] * (2 - len(cs))
        rows.append('<tr><th scope="row">%s</th><td data-label="%s">%s</td><td data-label="%s">%s</td></tr>' % (
            name, tcs[0][0] if tcs else 'Built with', cs[0], tcs[1][0] if len(tcs) > 1 else 'Runs on', cs[1]))
    return ('<section class="tools paper" id="tools" aria-labelledby="h-tools"><p class="eyebrow">%s</p>'
            '<h2 class="sec-title" id="h-tools">%s</h2><p class="sec-lede">%s</p>'
            '<div class="tscroll"><table class="ttable"><caption>%s</caption><thead><tr><th scope="col">Project</th><th scope="col">Built with</th><th scope="col">Runs on</th></tr></thead>'
            '<tbody>%s</tbody></table></div></section>') % (eyebrow, title, lede, esc(strip_tags(summ.group(1))) if summ else '', ''.join(rows))


def blurb(depth):
    up = '../' * depth
    return ('<section class="blurb" id="archive" data-fitbox><p class="blurb__now">You&rsquo;re looking at: <b>Sticker Wall</b></p>'
            '<p class="blurb__t"><b>Style archive.</b> This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, '
            'from a museum floor plan to a 1991 law-firm word processor. <a class="big-link" href="%sstyles/index.html">See every version <span aria-hidden="true">&rarr;</span></a></p></section>') % (sum(1 for r in ROOMS for i in r['items'] if i['kind'] == 'case'), up)


def footer():
    return ('<footer class="foot" id="contact" data-fitbox><h2 class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><span class="fit mailtxt" id="mailtxt" data-cap="120" data-min="14">%s</span></p>'
            '<div class="foot__btns"><button class="copybtn" id="copy" type="button" data-copy="%s">Copy email</button>'
            '<a class="mailbtn" href="mailto:%s">Open in mail app</a><span class="copystat" id="copystat" role="status" aria-live="polite"></span></div>'
            '<div class="foot__row"><a href="https://github.com/mylesparslow-collab">GitHub</a>'
            '<a href="https://mylesparslow.com/legal-portfolio/">Legal portfolio</a>'
            '<a href="#top">Back to top &uarr;</a><span>Myles Parslow &middot; Made with AI</span></div></footer>') % (MAIL, MAIL, MAIL)


def build_home():
    inner = (topbar(0, 'home') + '<main id="main">' + hero() + ''.join(slab(r) for r in ROOMS) + rules() + tools() + blurb(1) + '</main>' + footer())
    return page('Myles Parslow · Sticker Wall', 'Myles Parslow makes things with AI: %d case studies, from legal software to cat songs and a kart racer, as stickers on a colour wall.' % sum(1 for r in ROOMS for i in r['items'] if i['kind'] == 'case'), 0, 'page-home', inner, home=True)


# ------------------------------------------------------------------ room pages
def case_html(r, it):
    letter = r['letter']
    num = it['count'].split('/')[0].strip()
    kicks = [k for k in it['kickers'] if k.strip()]
    pills = ''.join('<span class="kick k%d">%s</span>' % ((seed(it['id'], k) % 4), k) for k in kicks)
    body = fix_body(it['body_html'])
    return """<article class="case" id="@@ID@@" data-chrome="@@TT@@">
<header class="case__h">
<div class="case__tags"><span class="ctag">@@L@@@@N@@</span><span class="cof">@@CNT@@</span>@@PILLS@@</div>
<h2 class="case__t">@@T@@</h2>
<p class="case__sub"><span class="pill">@@SUB@@</span></p>
<p class="case__lede">@@LEDE@@</p>
</header>
<div class="cbody">@@BODY@@</div>
</article>""".replace('@@ID@@', it['id']).replace('@@TT@@', esc(strip_tags(it['title']))).replace('@@L@@', letter).replace(
        '@@N@@', num).replace('@@CNT@@', it['count']).replace('@@PILLS@@', pills).replace('@@T@@', it['title']).replace(
        '@@SUB@@', it['sub']).replace('@@LEDE@@', it['lede']).replace('@@BODY@@', body)


def room_jump(r):
    out = []
    for it in r['items']:
        if it['kind'] != 'case':
            continue
        sd = seed(it['id'], 'j')
        rot = ((sd % 601) / 100.0) - 3.0
        nm = ('tomato', 'butter', 'violet', 'mint', 'paper')
        names = [n for n in nm if STK[n][0] != r['c']]
        fill, fg = STK[names[(sd >> 4) % len(names)]]
        so = r['so']
        out.append('<li><a class="jump" href="#%s" style="--r:%.1fdeg;--bg:%s;--fg:%s;--so:%s">%s</a></li>' % (it['id'], rot, fill, fg, so, it['title']))
    return '<ul class="jumps" aria-label="Jump to a project">%s</ul>' % ''.join(out)


ROOMFOOT = ('<footer class="foot foot--room"><div class="foot__row"><a href="https://github.com/mylesparslow-collab">GitHub</a>'
            '<a href="https://mylesparslow.com/legal-portfolio/">Legal portfolio</a><a href="#top">Back to top &uarr;</a>'
            '<span>Myles Parslow &middot; Made with AI</span></div></footer>')


def build_room(r):
    s = r['slug']
    parts = []
    for it in r['items']:
        if it['kind'] == 'case':
            parts.append(case_html(r, it))
        else:
            parts.append(fix_body(it['html']))
    head = """<header class="rhead" id="top" style="--c:@@C@@;--cf:@@F@@;--so:@@SO@@" data-fitbox>
<p class="eyebrow">@@EY@@ &middot; @@CNT@@</p>
<h1 class="rhead__name"><span class="fit" data-cap="200" data-min="48">@@SHORT@@</span></h1>
@@FULL@@<p class="rhead__lede">@@LEDE@@</p>
@@JUMPS@@
<p class="rhead__ai"><a class="open" href="../index.html#tools">Which AI for what by project <span aria-hidden="true">&rarr;</span></a></p>
</header>""".replace('@@C@@', r['c']).replace('@@F@@', r['f']).replace('@@SO@@', r['so']).replace('@@EY@@', r['eyebrow']).replace(
        '@@CNT@@', r['count']).replace('@@SHORT@@', r['short']).replace('@@LEDE@@', r['lede']).replace('@@JUMPS@@', room_jump(r)).replace(
        '@@FULL@@', ('<p class="rhead__full"><span class="pill">%s</span></p>' % r['title']) if r['plain'] != r['short'] else '')
    if r['i'] < len(ROOMS) - 1:
        n = ROOMS[r['i'] + 1]
        nxt = ('<a class="next" href="../%s/index.html" style="--c:%s;--cf:%s" data-fitbox><span class="next__l">Next room <span aria-hidden="true">&rarr;</span></span>'
               '<span class="next__n"><span class="fit" data-cap="200" data-min="40">%s</span></span><span class="next__s">%s &middot; %s</span></a>') % (
            n['slug'], n['c'], n['f'], n['short'], n['eyebrow'], n['count'])
    else:
        nxt = ('<a class="next" href="../index.html" style="--c:%s;--cf:%s" data-fitbox><span class="next__l">That was the last room <span aria-hidden="true">&rarr;</span></span>'
               '<span class="next__n"><span class="fit" data-cap="200" data-min="40">Home</span></span><span class="next__s">Back to the sticker wall</span></a>') % (TOMATO, INK)
    main = '<main id="main">' + head + '<div class="cases">' + ''.join(parts) + '</div>' + nxt + '</main>' + ROOMFOOT
    style = '--c:%s;--cf:%s;--a:%s;--af:%s;--so:%s' % (r['c'], r['f'], r['a'], r['af'], r['so'])
    inner = '<div class="roomwrap" style="%s">' % style + topbar(1, s) + main + '</div>'
    return page('%s · Myles Parslow' % r['plain'], strip_tags(r['lede']), 1, 'room room-' + s, inner)


# ------------------------------------------------------------------ css
CSS = r"""
/* Sticker Wall: tokens */
:root{
  --ink:#1a1033;--paper:#fff7ea;--white:#fff;
  --tomato:#ff4a2b;--butter:#ffd84a;--violet:#5b3df5;--mint:#7ee0b5;
  --pop:cubic-bezier(.34,1.56,.64,1);--move:cubic-bezier(.2,.8,.2,1);
  --disp:"Unbounded","Arial Black",system-ui,sans-serif;--body:"DM Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --gut:clamp(16px,4vw,56px);
}
:root,:root[data-theme="light"]{--bg:var(--paper);--fg:var(--ink);--card:#fff;--edge:var(--ink);--zebra:#fff1b8;--made:#fff1b8;--link:var(--violet);--mute:#4a3d6e;color-scheme:light}
:root[data-theme="dark"]{--bg:var(--ink);--fg:var(--paper);--card:#2a1d52;--edge:var(--paper);--zebra:#251a47;--made:#3a2c6b;--link:var(--mint);--mute:#cfc6e8;color-scheme:dark}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:110px}
body{margin:0;background:var(--bg);color:var(--fg);font:400 18px/1.6 var(--body);overflow-x:hidden;-webkit-font-smoothing:antialiased}
h1,h2,h3,h4,p,ul,ol,dl,dd,figure{margin:0}
ul,ol{padding:0;list-style:none}
img,video{max-width:100%}
a{color:inherit}
:focus-visible{outline:4px solid var(--violet);outline-offset:3px;box-shadow:0 0 0 7px var(--white)}
:root[data-theme="dark"] :focus-visible{outline-color:var(--butter);box-shadow:0 0 0 7px var(--ink)}
.slab :focus-visible,.hero :focus-visible,.rhead :focus-visible,.next :focus-visible,.foot :focus-visible,.blurb :focus-visible{outline-color:var(--ink);box-shadow:0 0 0 7px var(--white)}
.slab-research :focus-visible,.foot :focus-visible,.room-research .rhead :focus-visible{outline-color:var(--butter);box-shadow:0 0 0 7px var(--ink)}
.skip{position:absolute;left:12px;top:-80px;background:var(--ink);color:var(--paper);padding:12px 18px;border-radius:99px;font-weight:700;z-index:200;text-decoration:none}
.skip:focus{top:12px}
.eyebrow{font:700 16px/1.3 var(--body)}
.pill{display:inline-block;background:var(--white);color:var(--ink);border:3px solid var(--ink);border-radius:99px;padding:3px 14px;font:700 15px/1.4 var(--body)}

/* ---------- top bar ---------- */
.topbar{position:fixed;z-index:100;top:12px;left:0;right:0;display:flex;justify-content:center;padding:0 12px;pointer-events:none}
.bar{pointer-events:auto;display:flex;align-items:center;gap:8px;max-width:100%;background:var(--white);color:var(--ink);border:3px solid var(--ink);border-radius:99px;padding:6px 8px;box-shadow:5px 5px 0 var(--ink)}
.home,.chip,.theme{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:0 14px;border-radius:99px;font:700 15px/1 var(--body);text-decoration:none;color:var(--ink);border:3px solid transparent;background:transparent;cursor:pointer;transition:transform .3s var(--pop),background-color .25s var(--move)}
.home{border-color:var(--ink)}
.home.is-cur{background:var(--ink);color:var(--paper)}
.chips{display:flex;gap:6px;flex-wrap:nowrap}
.chip{border-color:var(--c);background:var(--white)}
.chip .dot{width:12px;height:12px;border-radius:50%;background:var(--c);border:2px solid var(--ink);flex:none}
.chip.is-cur{background:var(--c);color:var(--cf);border-color:var(--ink)}
.chip.is-cur .dot{background:var(--cf)}
.chip-research{border-color:var(--ink)}
.chip-research.is-cur{background:var(--ink);color:var(--mint)}
.chip-research.is-cur .dot{background:var(--mint)}
.theme{border-color:var(--ink);padding:0 12px 0 10px}
.theme__i{width:18px;height:18px;border-radius:50%;background:var(--butter);border:3px solid var(--ink);position:relative;flex:none;overflow:hidden}
:root[data-theme="dark"] .theme__i{background:var(--ink)}
:root[data-theme="dark"] .theme__i::after{content:"";position:absolute;width:14px;height:14px;border-radius:50%;background:var(--white);left:-6px;top:-5px;box-shadow:0 0 0 0 transparent}
.home:hover,.chip:hover,.theme:hover{animation:wob .45s var(--pop)}
@keyframes wob{0%{transform:rotate(0)}25%{transform:rotate(-2deg) scale(1.04)}60%{transform:rotate(2deg) scale(1.04)}100%{transform:rotate(0)}}

/* ---------- hero ---------- */
.hero{position:relative;overflow:hidden;background:var(--tomato);color:var(--ink);padding:clamp(120px,16vh,168px) var(--gut) clamp(48px,8vh,96px)}
.hero__name{position:relative;z-index:1;font:800 100px/.92 var(--disp);text-transform:uppercase;letter-spacing:-.025em}
.fit{display:block;width:max-content;max-width:none;white-space:nowrap;font-family:var(--disp);font-weight:800;line-height:.95;letter-spacing:-.02em;font-size:clamp(48px,11vw,200px)}
.hero__name .fit{line-height:.9;font-size:clamp(48px,20vw,340px)}
.hero__pill{margin:clamp(10px,2vw,22px) 0 clamp(28px,5vh,56px) clamp(4px,3vw,40px)}
.hero__pill span{display:inline-block;transform:rotate(-3deg);background:var(--butter);color:var(--ink);border:3px solid var(--ink);box-shadow:6px 6px 0 var(--ink);border-radius:99px;padding:.3em 1em;font:800 clamp(18px,3.4vw,44px)/1.2 var(--disp)}
.hero__grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(28px,5vw,72px);align-items:center;position:relative;z-index:1}
.hero__count{display:inline-block;background:var(--ink);color:var(--paper);border-radius:99px;padding:4px 16px;font:700 16px/1.5 var(--body);margin-bottom:14px}
.hero .lede{font-size:clamp(18px,1.7vw,22px);max-width:36em}
.hero__hint{margin-top:18px;font-weight:700}
.badges{display:flex;flex-wrap:wrap;gap:clamp(16px,2vw,28px);justify-content:center}
.badge{width:min(100%,270px);aspect-ratio:1;border-radius:50%;border:3px solid var(--ink);box-shadow:6px 6px 0 var(--ink);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:30px 30px;gap:8px}
.badge dd{order:1;font:800 clamp(19px,1.7vw,24px)/1.15 var(--disp);white-space:nowrap}
.badge dt{order:2;font:700 14px/1.35 var(--body)}
.badge.b0{background:var(--butter);color:var(--ink);transform:rotate(-5deg)}
.badge.b1{background:var(--violet);color:var(--white);transform:rotate(4deg);margin-top:clamp(0px,3vw,36px)}
.deco{position:absolute;pointer-events:none;border:3px solid var(--ink)}
.d1{width:78px;aspect-ratio:1;border-radius:50%;background:var(--violet);right:3vw;top:22px}
.d2{width:58px;aspect-ratio:1;background:var(--mint);right:calc(3vw + 100px);top:26px;clip-path:polygon(50% 0,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);border:0}

/* ---------- slabs: the sticker wall ---------- */
.slab{position:relative;background:var(--c);color:var(--cf);padding:clamp(48px,8vh,96px) var(--gut) clamp(40px,6vh,72px);overflow:hidden}
.slab__top{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:clamp(8px,2vh,20px)}
.slab__top .eyebrow{margin-right:6px}
.slab-research .pill{background:var(--mint)}
.slab__name{font-size:0;line-height:0}
.slab__name a,.rhead__name .fit{text-decoration:none;color:inherit;font-size:clamp(48px,11vw,200px)}
.slab__name a{display:block}
.slab__name a:hover{animation:wob .5s var(--pop)}
.slab__lede{max-width:44em;margin:clamp(10px,2vh,20px) 0 clamp(24px,4vh,44px);font-size:20px}
.wall{display:flex;flex-wrap:wrap;justify-content:center;align-items:flex-start;gap:14px 10px;padding:6px 0 12px;position:relative}
.st{position:relative;margin:var(--mt) var(--mx) 0;max-width:100%}
.sticker{display:block;max-width:min(300px,100%);padding:14px 24px 15px;background:var(--bg);color:var(--fg);border:3px solid var(--so);border-radius:var(--rad);box-shadow:6px 6px 0 var(--so);text-decoration:none;
  transform:translate(var(--dx,0px),var(--dy,0px)) rotate(var(--r)) scale(var(--s,1));touch-action:pan-y;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;cursor:grab;
  transition:transform .45s var(--pop),box-shadow .3s var(--move);will-change:transform}
.st:hover,.st:focus-within{z-index:5}
.st__t{display:block;font:800 clamp(16px,1.5vw,20px)/1.2 var(--disp);overflow-wrap:anywhere}
.st__s{display:block;font:700 14px/1.35 var(--body);margin-top:4px}
.sticker:hover{animation:wob .45s var(--pop)}
.sticker.is-drag{--s:1.06;box-shadow:12px 14px 0 var(--so);transition:none;cursor:grabbing;animation:none;z-index:50}
.st:has(.is-drag){z-index:60}
.slab__foot{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;margin-top:clamp(20px,3vh,36px)}
.tidy,.open,.copybtn,.mailbtn{font:700 17px/1 var(--body);display:inline-flex;align-items:center;min-height:48px;padding:0 24px;border-radius:99px;border:3px solid var(--so,var(--ink));background:var(--white);color:var(--ink);box-shadow:5px 5px 0 var(--so,var(--ink));cursor:pointer;text-decoration:none;transition:transform .3s var(--pop),box-shadow .3s var(--move)}
.tidy:hover,.open:hover,.copybtn:hover,.mailbtn:hover{animation:wob .45s var(--pop)}
.tidy:active,.open:active,.copybtn:active,.mailbtn:active{transform:translate(3px,3px);box-shadow:2px 2px 0 var(--so,var(--ink))}
.open{background:var(--ink);color:var(--paper)}
.slab-research .open{background:var(--mint);color:var(--ink)}
.slab-research .tidy{background:var(--paper)}

/* ---------- paper sections ---------- */
.paper{background:var(--bg);color:var(--fg);padding:clamp(56px,10vh,120px) var(--gut)}
.sec-title{font:800 clamp(30px,5vw,72px)/1.05 var(--disp);letter-spacing:-.02em;margin:10px 0 clamp(28px,5vh,56px);max-width:16em;overflow-wrap:anywhere}
.sec-lede{max-width:44em;margin:-16px 0 32px}
.rules__list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(20px,3vw,40px);counter-reset:r}
.rule{background:var(--bg);color:var(--fg);border:3px solid var(--edge);border-radius:36px;box-shadow:8px 8px 0 var(--edge);padding:clamp(24px,2.6vw,40px);display:flex;flex-direction:column;gap:14px;transition:transform .4s var(--pop)}
.rule0{transform:rotate(-1.5deg)}.rule1{transform:rotate(1.2deg) translateY(12px)}.rule2{transform:rotate(-.8deg)}
.rule:hover{animation:wob .45s var(--pop)}
.rule__n{display:grid;place-items:center;width:72px;height:72px;border-radius:50%;background:var(--ink);color:var(--paper);border:3px solid var(--ink);font:800 26px/1 var(--disp);flex:none}
.rule h3{font:800 clamp(20px,2vw,28px)/1.2 var(--disp);overflow-wrap:anywhere}
.rule p{font-size:18px}

.tscroll{border:3px solid var(--edge);border-radius:28px;box-shadow:8px 8px 0 var(--edge);overflow:hidden;background:var(--card)}
.ttable{width:100%;border-collapse:collapse;font-size:17px;line-height:1.5}
.ttable caption{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.ttable thead th{background:var(--ink);color:var(--paper);font:800 15px/1.3 var(--disp);text-align:left;padding:16px 20px}
.ttable tbody th,.ttable td{padding:16px 20px;vertical-align:top;text-align:left;border-top:3px solid var(--edge)}
.ttable tbody tr:first-child>*{border-top:0}
.ttable tbody th{font:800 16px/1.3 var(--disp);width:19%;overflow-wrap:anywhere}
.ttable tbody tr:nth-child(even){background:var(--zebra)}
.ttable td:empty{background:repeating-linear-gradient(135deg,transparent 0 8px,color-mix(in srgb,var(--fg) 8%,transparent) 8px 10px)}

.blurb{background:var(--mint);color:var(--ink);padding:clamp(48px,9vh,110px) var(--gut)}
.blurb__now{display:inline-block;background:var(--ink);color:var(--paper);border-radius:99px;padding:6px 20px;font:700 17px/1.4 var(--body);transform:rotate(-2deg);margin-bottom:24px}
.blurb__now b{font:800 .95em var(--disp);color:var(--butter)}
.blurb__t{font:700 clamp(20px,2.6vw,36px)/1.35 var(--body);max-width:30em}
.big-link{display:inline-block;background:var(--ink);color:var(--paper);border-radius:99px;padding:.1em .7em .15em;text-decoration:none;white-space:nowrap;transition:transform .3s var(--pop)}
.big-link:hover{animation:wob .45s var(--pop)}

.foot{background:var(--ink);color:var(--paper);padding:clamp(56px,10vh,120px) var(--gut) 40px;overflow:hidden}
.foot__t{font:800 clamp(30px,5vw,72px)/1.05 var(--disp);color:var(--butter);margin-bottom:clamp(18px,3vh,32px)}
.foot__mail{margin-bottom:28px}
.mailtxt{user-select:all;-webkit-user-select:all;color:var(--paper);font-size:clamp(14px,5vw,120px)}
.foot__btns{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-bottom:clamp(36px,6vh,72px)}
.foot .copybtn{background:var(--butter);--so:var(--paper)}
.foot .mailbtn{background:var(--mint);--so:var(--paper)}
.copystat{font-weight:700;color:var(--butter);min-width:6em}
.foot__row{display:flex;flex-wrap:wrap;gap:12px 28px;font-weight:700;border-top:3px solid var(--paper);padding-top:22px}
.foot__row a{text-decoration-thickness:3px;text-underline-offset:5px}
.foot__row a:hover{color:var(--butter)}

/* ---------- room page ---------- */
.rhead{background:var(--c);color:var(--cf);padding:clamp(120px,16vh,170px) var(--gut) clamp(40px,7vh,80px);overflow:hidden}
.rhead .eyebrow{font-size:18px;margin-bottom:6px}
.rhead__name{font-size:0;line-height:0}
.rhead__full{margin-top:12px}
.rhead__ai{margin-top:24px}
.rhead .open{background:var(--ink);color:var(--paper);--so:var(--paper)}
.foot--room{padding-top:32px}
.foot--room .foot__row{border-top:0;padding-top:0}
.ttable .lab{font-weight:700}
.rhead__lede{max-width:40em;font-size:clamp(19px,1.7vw,24px);margin:20px 0 28px}
.jumps{display:flex;flex-wrap:wrap;gap:12px 10px}
.jump{display:block;padding:7px 16px;background:var(--bg);color:var(--fg);border:3px solid var(--so);border-radius:99px;box-shadow:4px 4px 0 var(--so);font:800 13px/1.25 var(--disp);text-decoration:none;transform:rotate(var(--r));transition:transform .35s var(--pop)}
.jump:hover{animation:wob .45s var(--pop)}
.cases{padding:0 0 clamp(40px,8vh,96px)}
.case{width:min(1240px,calc(100% - 2*var(--gut)));margin:clamp(40px,7vh,88px) auto 0;background:var(--card);color:var(--fg);border:3px solid var(--edge);border-radius:24px;box-shadow:10px 10px 0 var(--edge);padding:clamp(20px,3.4vw,52px);scroll-margin-top:110px;min-width:0}
.js .case{opacity:0;transform:scale(.96)}
.js .case.in{animation:popin .45s var(--pop) both}
@keyframes popin{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:scale(1)}}
.case__h{display:grid;gap:14px;margin-bottom:clamp(24px,4vh,44px)}
.case__tags{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ctag{background:var(--c);color:var(--cf);border:3px solid var(--edge);border-radius:99px;padding:3px 14px;font:800 15px/1.4 var(--disp);transform:rotate(-3deg);box-shadow:3px 3px 0 var(--edge)}
.cof{font-weight:700;color:var(--mute);font-size:15px;margin-right:6px}
.kick{border:3px solid var(--ink);border-radius:99px;padding:2px 12px;font:700 14px/1.5 var(--body);color:var(--ink)}
.k0{background:var(--butter)}.k1{background:var(--mint)}.k2{background:var(--tomato)}.k3{background:var(--paper)}
.case__t{font:800 clamp(26px,4.4vw,56px)/1.08 var(--disp);letter-spacing:-.02em;overflow-wrap:anywhere}
.case__sub .pill{background:var(--a);color:var(--af);border-color:var(--edge);transform:rotate(-1deg)}
.case__lede{font-size:20px;max-width:42em}

.cbody{display:grid;gap:clamp(28px,5vh,48px);min-width:0}
.cbody>*{min-width:0}
.cbody p,.cbody li,.cbody dd,.cbody dt,.cbody figcaption{overflow-wrap:break-word}
.cbody p{max-width:46em}
.cbody a{color:var(--link);font-weight:700;text-decoration-thickness:3px;text-underline-offset:4px}
.cbody a:hover{text-decoration-color:var(--tomato)}
.cbody code{font:700 .88em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--made);padding:.1em .4em;border-radius:8px}
.cbody h3{font:800 clamp(19px,2vw,26px)/1.2 var(--disp);overflow-wrap:anywhere}
.cbody h4{font:700 18px/1.4 var(--body)}
.cbody ul,.cbody ol{display:grid;gap:.6em;padding-left:1.4em}
.cbody ul{list-style:none}
.cbody ul>li{position:relative}
.cbody ul>li::before{content:"";position:absolute;left:-1.3em;top:.55em;width:.7em;height:.7em;border-radius:50%;background:var(--c);border:2px solid var(--edge)}
.cbody ol{list-style:decimal}
.cbody ol li::marker{font-weight:700}
.cbody figure{border:3px solid var(--edge);border-radius:16px;box-shadow:6px 6px 0 var(--edge);overflow:hidden;background:var(--card);align-self:start;min-width:0}
.cbody figure img,.cbody figure video{display:block;width:100%;height:auto;background:#000}
.cbody figure img.portrait,.cbody figure video.portrait{max-width:min(100%,380px);margin:0 auto}
.cbody figcaption{padding:12px 16px 14px;font-size:15px;line-height:1.5;border-top:3px solid var(--edge)}
.cbody figure:has(img.portrait){max-width:420px}
.cbody .cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(24px,4vw,56px);align-items:start}
.cbody .block{display:grid;gap:12px;align-content:start}
.cbody .block ul,.cbody .block ol{margin:0}
.cbody .shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(20px,3vw,40px);align-items:start}
.cbody .gallery{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(14px,2vw,26px);align-items:start}
.cbody .gallery figcaption{font-size:13px;padding:8px 10px}
.cbody .grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(16px,2vw,28px)}
.cbody .grid3>div,.cbody .more>div{display:grid;gap:8px;align-content:start;border:3px solid var(--edge);border-radius:20px;padding:18px 20px;background:var(--bg);box-shadow:4px 4px 0 var(--edge)}
.cbody .more{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
.cbody .made{background:var(--made);border:3px dashed var(--edge);border-radius:20px;padding:16px 20px;display:grid;gap:6px}
.cbody .made b{font:800 14px/1.3 var(--disp)}
.cbody .made p{max-width:none}
.cbody .links{display:flex;flex-wrap:wrap;gap:14px;align-items:center;max-width:none}
.cbody .links a{display:inline-flex;align-items:center;gap:.6em;min-height:48px;padding:0 24px;border-radius:99px;border:3px solid var(--edge);background:var(--a);color:var(--af);box-shadow:5px 5px 0 var(--edge);text-decoration:none;font:700 17px/1.2 var(--body);transition:transform .3s var(--pop),box-shadow .3s var(--move)}
.cbody .links a::after{content:"\2192";display:inline-block;font-size:1.2em;transition:transform .35s var(--pop)}
.cbody .links a:hover{animation:wob .45s var(--pop);color:var(--af)}
.cbody .links a:hover::after{transform:translateX(5px)}
.cbody .links a:active{transform:translate(3px,3px);box-shadow:2px 2px 0 var(--edge)}
.cbody .links span{display:inline-block;border:3px dashed var(--edge);border-radius:99px;padding:6px 18px;font-weight:700;font-size:15px}
.cbody .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:clamp(14px,2vw,24px)}
.cbody .stats>div{display:flex;flex-direction:column;justify-content:center;gap:6px;background:var(--c);color:var(--cf);border:3px solid var(--edge);border-radius:60px;box-shadow:6px 6px 0 var(--edge);padding:26px 32px;text-align:center;min-width:0}
.cbody .stats dd{order:1;font:800 clamp(24px,2.8vw,38px)/1.1 var(--disp);white-space:nowrap}
.cbody .stats dt{order:2;font:700 15px/1.35 var(--body)}
.cbody .compare{position:relative;overflow:hidden;width:100%;max-width:100%;border:3px solid var(--edge);border-radius:16px;box-shadow:6px 6px 0 var(--edge);background:var(--card);--pos:50%;touch-action:pan-y}
.cbody .compare.portrait{max-width:380px}
.cbody figure.compare-fig{border:0;box-shadow:none;background:none;overflow:visible}
.cbody figure.compare-fig figcaption{border:3px solid var(--edge);border-radius:14px;margin-top:14px;background:var(--card)}
.cbody .compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;max-width:none}
.cbody .compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cbody .cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:4px;margin-left:-2px;background:var(--white);pointer-events:none;box-shadow:0 0 0 2px var(--ink)}
.cbody .cmp-line::after{content:"\2194";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:46px;height:46px;border-radius:50%;background:var(--butter);color:var(--ink);border:3px solid var(--ink);display:grid;place-items:center;font:800 20px/1 var(--body)}
.cbody .cmp-tag{position:absolute;top:10px;font:700 13px/1 var(--body);background:var(--ink);color:var(--paper);padding:7px 10px;border-radius:99px;pointer-events:none}
.cbody .cmp-tag.l{left:10px}.cbody .cmp-tag.r{right:10px}
.cbody .compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.cbody .compare:focus-within{outline:4px solid var(--violet);outline-offset:4px}
.cbody .reels{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:clamp(10px,1.4vw,18px);align-items:start}
.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr));max-width:760px}
.cbody .reels video{aspect-ratio:9/16;object-fit:cover}
.cbody .reels figcaption{font-size:13px;padding:8px 10px}
.cbody .flow{counter-reset:step;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px;padding:0;list-style:none}
.cbody .flow li{counter-increment:step;display:grid;gap:6px;align-content:start;border:3px solid var(--edge);border-radius:20px;padding:16px;background:var(--bg);box-shadow:4px 4px 0 var(--edge)}
.cbody .flow li::before{content:none}
.cbody .flow b{font:800 16px/1.2 var(--disp)}
.cbody .flow b::before{content:counter(step);display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--c);color:var(--cf);border:3px solid var(--edge);margin-right:8px;font:800 14px/1 var(--disp)}
.cbody .piece{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(24px,4vw,56px);align-items:start}
.cbody .piece.flip>figure{order:2}
.cbody .piece-text{display:grid;gap:14px;align-content:start}
.cbody .tags{display:flex;flex-wrap:wrap;gap:8px;padding:0}
.cbody .tag{border:3px solid var(--edge);border-radius:99px;padding:2px 12px;font:700 14px/1.5 var(--body)}
.cbody .tag.hot{background:var(--tomato);color:var(--ink);border-color:var(--ink)}
.cbody .facts{display:flex;flex-wrap:wrap;gap:6px 22px}
.cbody .facts strong{font:800 20px/1 var(--disp);margin-right:.25em}
.cbody .books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(18px,2.4vw,32px);align-items:start}
.cbody .book{display:grid;gap:12px;align-content:start;padding:clamp(18px,2vw,28px);border:3px solid var(--edge);border-radius:24px;box-shadow:6px 6px 0 var(--edge);background:var(--bg)}
.cbody .book.lead{grid-column:1/-1;grid-template-columns:minmax(0,14rem) minmax(0,1fr);gap:clamp(18px,3vw,36px)}
.cbody .book .cover{width:100%;max-width:230px;height:auto;border:3px solid var(--edge);border-radius:10px}
.cbody .lead-text{display:grid;gap:12px;min-width:0}
.cbody .kind{display:inline-block;justify-self:start;background:var(--butter);color:var(--ink);border:3px solid var(--ink);border-radius:99px;padding:1px 12px;font:700 14px/1.5 var(--body)}
.cbody .count{font:800 20px/1.1 var(--disp)}
.cbody .logline{font:700 clamp(19px,1.6vw,22px)/1.4 var(--body)}
.cbody .note,.cbody span.note{font-size:15px;color:var(--mute)}
.cbody .sub-case{display:grid;gap:clamp(20px,4vh,36px);border-top:3px dashed var(--edge);padding-top:clamp(28px,5vh,48px)}
.cbody .sub-case>h3{font:800 clamp(24px,3.2vw,42px)/1.1 var(--disp)}

.gdiv{margin:clamp(48px,8vh,96px) 0 0;background:var(--a);color:var(--af);border-block:3px solid var(--ink);padding:clamp(14px,2.4vh,24px) var(--gut);scroll-margin-top:110px;display:grid;gap:4px}
.gdiv__t{font:800 clamp(22px,3.4vw,44px)/1.1 var(--disp);overflow-wrap:anywhere}
.gdiv__p{max-width:56em;font-size:17px;font-weight:700}
.gdiv+.case{margin-top:clamp(32px,5vh,56px)}
.xsec{width:min(1240px,calc(100% - 2*var(--gut)));margin:clamp(40px,7vh,88px) auto 0;border:3px solid var(--edge);border-radius:24px;box-shadow:10px 10px 0 var(--edge);background:var(--card);padding:clamp(20px,3.4vw,52px);scroll-margin-top:110px}
.xsec__h{display:grid;gap:8px;margin-bottom:28px}
.xsec__t{font:800 clamp(26px,3.6vw,46px)/1.1 var(--disp)}
.xsec__list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}
.xsec__list>div{display:grid;gap:8px;align-content:start;border:3px solid var(--edge);border-radius:20px;padding:18px 22px;background:var(--bg);box-shadow:4px 4px 0 var(--edge)}
.xsec__list h3{font:800 18px/1.25 var(--disp)}

.next{display:flex;flex-direction:column;gap:6px;background:var(--c);color:var(--cf);text-decoration:none;padding:clamp(48px,9vh,110px) var(--gut) clamp(48px,9vh,110px);overflow:hidden;transition:filter .3s}
.next__l{display:inline-block;align-self:flex-start;background:var(--ink);color:var(--paper);border-radius:99px;padding:6px 20px;font:700 18px/1.4 var(--body);transform:rotate(-2deg);transition:transform .35s var(--pop)}
.next:hover .next__l,.next:focus-visible .next__l{transform:rotate(2deg) translateX(8px)}
.next__n{font-size:0;line-height:0;margin-top:10px}
.next__n .fit{font-size:clamp(40px,11vw,200px)}
.next__s{font:700 20px/1.4 var(--body)}
.next[style*="#1a1033"] .next__l{background:var(--mint);color:var(--ink)}

/* ---------- responsive ---------- */
@media (max-width:1100px){
  .cbody .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody .reels{grid-template-columns:repeat(3,minmax(0,1fr))}
  .cbody .flow{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody .grid3{grid-template-columns:repeat(2,minmax(0,1fr))}
  .ttable thead th,.ttable tbody th,.ttable td{padding:14px}
}
@media (max-width:900px){
  .hero__grid{grid-template-columns:minmax(0,1fr)}
  .rules__list{grid-template-columns:minmax(0,1fr)}
  .rule1{transform:rotate(1.2deg)}
  .cbody .cols,.cbody .shots,.cbody .piece,.cbody .books,.cbody .book.lead,.cbody .more,.xsec__list{grid-template-columns:minmax(0,1fr)}
  .cbody .piece.flip>figure{order:0}
}
@media (max-width:760px){
  body{font-size:17px}
  .topbar{position:absolute;top:10px}
  .bar{flex-wrap:wrap;justify-content:center;border-radius:30px;gap:6px;padding:8px}
  .chips{display:contents}
  .chips li{display:contents}
  .home,.chip,.theme{min-height:38px;padding:0 11px;font-size:14px}
  .theme__t{display:none}
  .deco{display:none}
  .hero,.rhead{padding-top:190px}
  html{scroll-padding-top:20px}
  .case,.xsec,.gdiv{scroll-margin-top:20px}
  .ttable thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .ttable,.ttable tbody,.ttable tr,.ttable th,.ttable td{display:block;width:100%}
  .ttable tbody th{width:100%;border-top:3px solid var(--edge);padding-bottom:6px}
  .ttable tbody tr:first-child>th{border-top:0}
  .ttable td{border-top:0;padding-top:4px}
  .ttable td:empty{display:none}
  .ttable td::before{content:attr(data-label);display:block;font:700 13px/1.3 var(--body);color:var(--mute)}
  .ttable tbody tr{padding-bottom:10px}
  .wall{gap:12px 6px}
  .sticker{padding:12px 18px 13px;max-width:calc(100vw - 2*var(--gut) - 14px)}
  .cbody .stats>div{border-radius:44px}
  .cbody .gallery,.cbody .reels,.cbody .grid3{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody .flow{grid-template-columns:minmax(0,1fr)}
  .badge{width:min(100%,250px);padding:28px}
  .case{box-shadow:6px 6px 0 var(--edge);border-radius:20px}
  .cbody .links a{padding:0 18px}
}
@media (max-width:420px){
  .cbody .gallery,.cbody .grid3{grid-template-columns:minmax(0,1fr)}
  .cbody .reels{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation:none!important;transition:none!important}
  .js .case{opacity:1;transform:none}
}
"""

JS = r"""(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)');

  /* theme toggle: the head script already set data-theme (saved choice, else the system) */
  var tb = d.getElementById('theme');
  function paint() {
    var dark = root.getAttribute('data-theme') === 'dark';
    if (tb) { tb.setAttribute('aria-pressed', dark ? 'true' : 'false'); tb.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode'); tb.querySelector('.theme__t').textContent = dark ? 'Light' : 'Dark'; }
  }
  paint();
  if (tb) tb.addEventListener('click', function () {
    var n = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', n);
    try { localStorage.setItem('sw-theme', n); } catch (e) {}
    paint();
  });
  try {
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      var s = null; try { s = localStorage.getItem('sw-theme'); } catch (x) {}
      if (!s) { root.setAttribute('data-theme', e.matches ? 'dark' : 'light'); paint(); }
    });
  } catch (e) {}

  /* fit big display words to one line */
  function fit() {
    Array.prototype.forEach.call(d.querySelectorAll('.fit'), function (el) {
      var box = el.closest('[data-fitbox]') || el.parentNode;
      var cs = getComputedStyle(box);
      var avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var cap = +el.getAttribute('data-cap') || 200;
      var vw = innerWidth;
      if (el.getAttribute('data-cap') === '200') cap = Math.min(200, Math.max(48, vw * 0.11));
      el.style.fontSize = '100px';
      var w = el.getBoundingClientRect().width;
      if (!w) return;
      var s = Math.min(cap, (100 * avail) / w);
      el.style.fontSize = Math.max(10, Math.floor(s * 10) / 10) + 'px';
    });
  }
  function fitNums() {
    Array.prototype.forEach.call(d.querySelectorAll('.stats dd, .badge dd'), function (el) {
      el.style.fontSize = '';
      var box = el.parentNode, cs = getComputedStyle(box);
      var avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var w = el.scrollWidth;
      if (w > avail) el.style.fontSize = Math.max(11, Math.floor(parseFloat(getComputedStyle(el).fontSize) * avail / w * 10) / 10) + 'px';
    });
  }
  var raf = 0;
  function sched() { cancelAnimationFrame(raf); raf = requestAnimationFrame(function () { fit(); fitNums(); }); }
  fit(); fitNums();
  addEventListener('resize', sched);
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(function () { fit(); fitNums(); });
  addEventListener('load', function () { fit(); fitNums(); });

  /* sticker dragging: pick up, move around the slab, elastic drop. A click still opens the link. */
  var zTop = 100;
  Array.prototype.forEach.call(d.querySelectorAll('.wall'), function (wall) {
    var slab = wall.closest('.slab');
    var all = [];
    Array.prototype.forEach.call(wall.querySelectorAll('.sticker'), function (s) {
      var dx = 0, dy = 0, sx = 0, sy = 0, bx = 0, by = 0, pid = null, moved = false, block = false;
      all.push(function () { dx = 0; dy = 0; s.style.setProperty('--dx', '0px'); s.style.setProperty('--dy', '0px'); });
      s.addEventListener('dragstart', function (e) { e.preventDefault(); });
      s.addEventListener('pointerdown', function (e) {
        if (e.button > 0) return;
        pid = e.pointerId; sx = e.clientX; sy = e.clientY; bx = dx; by = dy; moved = false; block = false;
      });
      s.addEventListener('pointermove', function (e) {
        if (e.pointerId !== pid) return;
        var mx = e.clientX - sx, my = e.clientY - sy;
        if (!moved) {
          if (Math.hypot(mx, my) < 6) return;
          moved = true;
          try { s.setPointerCapture(pid); } catch (x) {}
          s.classList.add('is-drag');
          s.parentNode.style.zIndex = ++zTop;
        }
        dx = bx + mx; dy = by + my;
        s.style.setProperty('--dx', dx + 'px'); s.style.setProperty('--dy', dy + 'px');
        var r = s.getBoundingClientRect(), b = slab.getBoundingClientRect(), fx = 0, fy = 0;
        if (r.left < b.left + 4) fx = b.left + 4 - r.left; else if (r.right > b.right - 4) fx = b.right - 4 - r.right;
        if (r.top < b.top + 4) fy = b.top + 4 - r.top; else if (r.bottom > b.bottom - 4) fy = b.bottom - 4 - r.bottom;
        if (fx || fy) { dx += fx; dy += fy; s.style.setProperty('--dx', dx + 'px'); s.style.setProperty('--dy', dy + 'px'); }
        e.preventDefault();
      });
      function end(e) {
        if (e.pointerId !== pid) return;
        pid = null;
        if (moved) { block = true; s.classList.remove('is-drag'); setTimeout(function () { block = false; }, 60); }
      }
      s.addEventListener('pointerup', end);
      s.addEventListener('pointercancel', end);
      s.addEventListener('click', function (e) { if (block) { e.preventDefault(); e.stopPropagation(); block = false; } });
    });
    var tidy = slab.querySelector('.tidy');
    if (tidy) tidy.addEventListener('click', function () { all.forEach(function (f) { f(); }); });
  });

  /* case cards pop in once */
  var cards = d.querySelectorAll('.case');
  if (cards.length) {
    if (reduce.matches || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(cards, function (c) { c.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
      }, { rootMargin: '0px 0px -8% 0px' });
      Array.prototype.forEach.call(cards, function (c) { io.observe(c); });
      setTimeout(function () { Array.prototype.forEach.call(cards, function (c) { if (!c.classList.contains('in') && c.getBoundingClientRect().top < innerHeight) c.classList.add('in'); }); }, 900);
      /* a deep link must never land on a hidden card */
      addEventListener('hashchange', function () { var t = d.getElementById(location.hash.slice(1)); if (t && t.classList.contains('case')) t.classList.add('in'); });
      var h0 = d.getElementById(location.hash.slice(1)); if (h0 && h0.classList && h0.classList.contains('case')) h0.classList.add('in');
    }
  }

  /* before / after sliders */
  Array.prototype.forEach.call(d.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* copy the email */
  var cb = d.getElementById('copy');
  if (cb) cb.addEventListener('click', function () {
    var t = cb.getAttribute('data-copy'), st = d.getElementById('copystat');
    function ok(m) { if (st) st.textContent = m; setTimeout(function () { if (st) st.textContent = ''; }, 2200); }
    function fallback() {
      var ta = d.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px;top:0';
      d.body.appendChild(ta); ta.select();
      var good = false; try { good = d.execCommand('copy'); } catch (e) {}
      d.body.removeChild(ta); ok(good ? 'Copied!' : 'Select the text and copy it');
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { ok('Copied!'); }, fallback);
    else fallback();
  });

  /* Esc on a room page goes Home */
  if (d.body.classList.contains('room')) addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !e.defaultPrevented && !/^(INPUT|TEXTAREA|SELECT)$/.test((d.activeElement || {}).tagName || '')) location.href = '../index.html';
  });
})();
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    w = lambda p, t: (os.makedirs(os.path.dirname(p), exist_ok=True), open(p, 'w', encoding='utf-8').write(t))
    w(os.path.join(OUT, 'index.html'), build_home())
    for r in ROOMS:
        w(os.path.join(OUT, r['slug'], 'index.html'), build_room(r))
    w(os.path.join(OUT, 'g.css'), CSS.lstrip())
    w(os.path.join(OUT, 'g.js'), JS)
    n = sum(r['nproj'] for r in ROOMS)
    print('mockup-g: %d rooms, %d case studies' % (len(ROOMS), n))


if __name__ == '__main__':
    main()


# style switcher (see add_switcher.py)
import runpy as _rp
import os as _os; _rp.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "add_switcher.py"), run_name="__main__")
