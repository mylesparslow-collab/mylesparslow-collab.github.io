#!/usr/bin/env python3
"""Render mockup C, "The Museum": a lobby with a floor plan and five gallery rooms.

    python3 -I themed/render_c.py

Reads themed/live.json (made by extract_live.py) and writes everything under mockup-c/:
index.html, <room>/index.html, c.css and c.js. Stdlib only. Safe to re-run.

Paths: room pages live at mockup-c/<room>/, so the live bodies' ../assets/ and ../demos/
gain one more ../ (the repo root holds assets/ and demos/). Room-to-room links stay in
the theme (../legal/index.html#id). Demos and external links open in a new tab.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-c')
DATA = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))


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
_fill_cases(DATA)
HOME = DATA['home']
ROOMS = DATA['rooms']
SLUGS = [r['slug'] for r in ROOMS]
REDIRECT = json.loads(HOME['redirect_map'])

esc = lambda t: html.escape(html.unescape(t), quote=True)
plain = lambda t: html.unescape(re.sub(r'<[^>]+>', '', t))

# short chip names, the lines the giant word is set in, and the fitted size (vw) for the widest line
SHORT = {'legal': 'Legal', 'business': 'Business', 'creative': 'Creative', 'design': 'Design', 'research': 'Research'}
LINES = {'legal': ['Legal'], 'business': ['Business'], 'creative': ['Creative', '&amp; games'],
         'design': ['Design', '&amp; 3D'], 'research': ['AI &amp;', 'research']}
RATIO = {'legal': 2.31, 'business': 3.54, 'creative': 3.52, 'design': 2.69, 'research': 3.86}  # word width / font-size
FIT = {k: min(30.0, round(90.0 / v, 1)) for k, v in RATIO.items()}  # CSS fallback (vw); c.js fits exactly
LETTER = {r['slug']: r['letter'] for r in ROOMS}
COUNT = {r['slug']: sum(1 for i in r['items'] if i['kind'] == 'case') for r in ROOMS}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&amp;display=swap">')

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t;
try{t=localStorage.getItem('mpc-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';
d.setAttribute('data-theme',t);})();
</script>"""


# ------------------------------------------------------------------ floor plan geometry
PW, PH = 1120.0, 430.0          # room field inside the walls
PX, PY = 40.0, 40.0
_tot = sum(COUNT.values())
_unit = PW * PH / _tot
def _rects():
    """Treemap: Legal as a full-height column, then Business over Creative, Design over Research."""
    c = COUNT
    out = {}
    x = PX
    w1 = c['legal'] * _unit / PH
    out['legal'] = (x, PY, w1, PH)
    x += w1
    pair = c['business'] + c['creative']
    w2 = pair * _unit / PH
    h = PH * c['business'] / pair
    out['business'] = (x, PY, w2, h)
    out['creative'] = (x, PY + h, w2, PH - h)
    x += w2
    pair = c['design'] + c['research']
    w3 = PW - w1 - w2
    h = PH * c['design'] / pair
    out['design'] = (x, PY, w3, h)
    out['research'] = (x, PY + h, w3, PH - h)
    return out
RECTS = _rects()


def plan_svg(current=None, mini=False, hrefs=None):
    """Inline SVG floor plan. Every room is a real focusable link."""
    gap = 3
    parts = []
    for i, r in enumerate(ROOMS, 1):
        s = r['slug']
        x, y, w, h = RECTS[s]
        x, y, w, h = x + gap, y + gap, w - 2 * gap, h - 2 * gap
        label = 'Room %d · %s · %d projects' % (i, SHORT[s], COUNT[s])
        href = (hrefs or {}).get(s, '%s/index.html' % s)
        cur = ' aria-current="page"' if s == current else ''
        if mini:
            body = ('<text class="pr-l" x="%.1f" y="%.1f">%s</text>' % (x + 14, y + 38, LETTER[s]))
            if s == current:
                body += '<circle class="pr-here" cx="%.1f" cy="%.1f" r="9"/>' % (x + w - 22, y + 24)
        else:
            body = ('<text class="pr-n" x="%.1f" y="%.1f" text-anchor="end">%d</text>' % (x + w - 18, y + 52, i)
                    + '<text class="pr-name" x="%.1f" y="%.1f">%s</text>' % (x + 18, y + h - 52, SHORT[s].upper())
                    + '<text class="pr-l" x="%.1f" y="%.1f">%s</text>' % (x + 18, y + h - 22, label))
        parts.append('<a class="pr" data-room="%s" href="%s" aria-label="%s"%s style="--room:var(--%s)">'
                     '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>%s</a>'
                     % (s, href, label, cur, s, x, y, w, h, body))
    walls = '<path class="wall" d="M560 490H20V20H1180V490H640"/>'
    door = ('<path class="arrow" d="M600 522V498M590 508L600 497L610 508"/>'
            '<text class="pr-ent" x="600" y="552" text-anchor="middle">Entrance</text>')
    cls = 'plan plan--mini' if mini else 'plan'
    ttl = 'Floor plan of the portfolio: five rooms, drawn in proportion to their number of projects'
    return ('<svg class="%s" viewBox="0 0 1200 570" role="group" aria-label="%s">%s%s%s</svg>'
            % (cls, ttl, walls, ''.join(parts), door))


# ------------------------------------------------------------------ body rewriting
def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_a(m, slug, own_ids, id_room):
    t = m.group(0)
    h = attr(t, 'href')
    if h is None:
        return t
    new, ext = h, False
    if h.startswith('../demos/') or h.startswith('../assets/'):
        new, ext = '../' + h, True
    elif h.startswith('#'):
        i = h[1:]
        if i and i not in own_ids and i in id_room:
            new = '../%s/index.html#%s' % (id_room[i], i)
    elif re.match(r'^https?://', h):
        ext = True
    if new != h:
        t = t.replace('href="%s"' % h, 'href="%s"' % new, 1)
    if ext:
        if 'target=' not in t:
            t = t.replace('<a ', '<a target="_blank" ', 1)
        if 'rel=' not in t:
            t = t.replace('<a ', '<a rel="noopener" ', 1)
        elif 'noopener' not in attr(t, 'rel'):
            t = t.replace('rel="%s"' % attr(t, 'rel'), 'rel="%s noopener"' % attr(t, 'rel'), 1)
    return t


def portrait(tag):
    try:
        return int(attr(tag, 'height')) > int(attr(tag, 'width')) * 1.15
    except (TypeError, ValueError):
        return False


def fix_media(m):
    t = m.group(0)
    t = re.sub(r'\s(src|poster)="\.\./(assets/[^"]+)"', r' \1="../../\2"', t)
    t = re.sub(r'\s(src|poster)="\.\./(demos/[^"]+)"', r' \1="../../\2"', t)
    if t.startswith('<video'):
        if not re.search(r'\scontrols[\s>=]', t):
            t = t.replace('<video', '<video controls', 1)
        if not re.search(r'\splaysinline[\s>=]', t):
            t = t.replace('<video', '<video playsinline', 1)
    return t


def fix_body(b, slug, own_ids, id_room):
    b = re.sub(r'<(?:img|video|source)\b[^>]*>', fix_media, b)
    b = re.sub(r'<a\b[^>]*>', lambda m: fix_a(m, slug, own_ids, id_room), b)
    return b.strip()


def first_img(body):
    m = re.search(r'<img\b[^>]*\ssrc="\.\./(assets/[^"]+)"', body)
    return '../' + m.group(1) if m else ''


# ------------------------------------------------------------------ shared chrome
def bar(current=None):
    """The slim fixed wayfinding bar: floor plan, five room chips, theme toggle."""
    if current:
        plan = ('<a class="wf-home" href="../index.html">%s<span>Home</span></a>'
                '<a class="wf-plan" href="../index.html#plan">%s<span>Floor plan</span></a>' % (HOME_ICON, PLAN_ICON))
    else:
        plan = ('<a class="wf-home" href="#lobby" aria-current="page">%s<span>Home</span></a>'
                '<a class="wf-plan" href="#plan">%s<span>Floor plan</span></a>' % (HOME_ICON, PLAN_ICON))
    base = '../' if current else ''
    chips = []
    for i, r in enumerate(ROOMS, 1):
        s = r['slug']
        cur = ' aria-current="page" title="Close this room and return to the floor plan"' if s == current else ''
        href = '../index.html#plan' if s == current else '%s%s/index.html' % (base, s)
        chips.append('<li><a class="chip" data-room="%s" href="%s"%s style="--room:var(--%s)"><span class="chip__n" aria-hidden="true">%d</span>%s</a></li>'
                     % (s, href, cur, s, i, SHORT[s]))
    toggle = ('<button class="theme" type="button" aria-label="Theme: dark. Switch to light."><i aria-hidden="true"></i><span>Dark</span></button>')
    return ('<div class="wf" id="wayfinding"><nav class="wf__in" aria-label="Wayfinding">%s<ul class="chips">%s</ul>%s</nav></div>'
            % (plan, ''.join(chips), toggle))


HOME_ICON = ('<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">'
             '<path d="M2.5 9.5L10 3l7.5 6.5M4.5 8.5V17h4v-5h3v5h4V8.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>')
PLAN_ICON = ('<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">'
             '<path d="M2 2h7v9H2zM11 2h7v5h-7zM11 9h7v9h-7zM2 13h7v5H2z" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>')


def page(title, desc, body_class, data_room, rel, inner, script_extra=''):
    return """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="%(desc)s">
<meta name="color-scheme" content="dark light">
<title>%(title)s</title>
%(head)s
%(fonts)s
<link rel="stylesheet" href="%(rel)sc.css">
%(extra)s</head>
<body class="%(bc)s"%(dr)s>
<a class="skip" href="#main">Skip to the content</a>
%(inner)s
<script src="%(rel)sc.js"></script>
</body>
</html>
""" % dict(title=title, desc=esc(desc), head=HEAD_SCRIPT, fonts=FONTS, rel=rel, extra=script_extra, bc=body_class,
           dr=' data-room="%s"' % data_room if data_room else '', inner=inner)


# ------------------------------------------------------------------ homepage
def parse_hero():
    h = HOME['hero_html']
    count = re.search(r'<span class="hero__count">(.*?)</span>', h).group(1)
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', h, re.S).group(1)
    stats = re.findall(r'<div><dt>(.*?)</dt><dd>(.*?)</dd></div>', h)
    src = re.search(r'<img src="(assets/[^"]+)"[^>]*data-n="([^"]*)" data-s="([^"]*)" data-h="([^"]*)"', h)
    return count, lede, stats, src.group(1), src.group(2), src.group(3), src.group(4)


def tools_table():
    t = HOME['tools_html']
    eyebrow = re.search(r'<p class="eyebrow">(.*?)</p>', t).group(1)
    sec = re.search(r'<h2[^>]*>(.*?)</h2>', t).group(1)
    lede = re.search(r'<p class="sec-lede">(.*?)</p>', t).group(1)
    summary = re.search(r'<summary><span class="sct">(.*?)</span></summary>', t).group(1)
    head, _, tail = t.partition('<details')
    def rows(s):
        out = []
        for m in re.finditer(r'<article class="trow"><h3>(.*?)</h3>(.*?)</article>', s, re.S):
            cols = re.findall(r'<div class="tcol"><span class="lab">(.*?)</span><p>(.*?)</p></div>', m.group(2), re.S)
            dl = ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % c for c in cols)
            out.append('<tr><th scope="row">%s</th><td><dl>%s</dl></td></tr>' % (m.group(1), dl))
        return ''.join(out)
    def table(r, cap):
        return ('<table class="guide"><caption class="sr">%s</caption><thead><tr><th scope="col">Project</th>'
                '<th scope="col">Which AI did what</th></tr></thead><tbody>%s</tbody></table>' % (cap, r))
    first, rest = rows(head), rows(tail)
    return eyebrow, sec, lede, summary, table(first, 'Which AI built and runs each project'), table(rest, 'The remaining projects')


def build_home():
    count, lede, stats, himg, hn, hs, hh = parse_hero()
    hh_link = hh.replace('/#', '/index.html#')
    plaques = ''.join('<div class="plaque"><dd>%s</dd><dt>%s</dt></div>' % (v, k) for k, v in stats)
    # directory
    cols = []
    for i, r in enumerate(ROOMS, 1):
        s, L = r['slug'], r['letter']
        items = []
        for it in r['items']:
            if it['kind'] != 'case':
                continue
            n = it['count'].split('/')[0].strip()
            items.append('<li><a class="d-item" href="%s/index.html#%s"><span class="d-n">%s%s</span>'
                         '<span class="d-t"><b>%s</b><span>%s</span></span></a></li>' % (s, it['id'], L, n, it['title'], it['sub']))
        cols.append('<section class="dircol" data-room="%s" style="--room:var(--%s);--room-t:var(--%s-t)" aria-labelledby="dh-%s">'
                    '<h3 id="dh-%s"><a href="%s/index.html"><span class="dh-n">%s</span><span class="dh-t">%s</span></a></h3>'
                    '<p class="dh-c">%s</p><ol>%s</ol></section>'
                    % (s, s, s, s, s, s, r['eyebrow'].replace('Room ', '').split(' of')[0], r['title'], r['count'], ''.join(items)))
    # house rules
    rules = re.findall(r'<li class="rule"><span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p></li>', HOME['rules_html'])
    r_eye = re.search(r'<p class="eyebrow">(.*?)</p>', HOME['rules_html']).group(1)
    r_h2 = re.search(r'<h2[^>]*>(.*?)</h2>', HOME['rules_html']).group(1)
    plq = ''.join('<li class="rule"><span class="rule__n" aria-hidden="true">%s</span><h4>%s</h4><p>%s</p></li>' % r for r in rules)
    t_eye, t_h2, t_lede, t_sum, t1, t2 = tools_table()
    foot = HOME['foot_html']
    say = re.search(r'aria-label="(Say hello\.)"', foot).group(1)
    email = re.search(r'data-copy="([^"]+)"', foot).group(1)
    links = re.findall(r'<a href="(https://[^"]+)">(.*?)</a>', foot)
    mid = re.search(r'<span>(Myles Parslow[^<]*)</span>', foot).group(1)
    flinks = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % l for l in links)
    ids = {}
    inner = """%(bar)s
<main id="main">
<header class="lobby-head" id="lobby">
  <p class="lh-k">Welcome to the portfolio. %(count)s</p>
  <h1 class="sign" aria-label="Myles Parslow makes things with AI."><span class="sign__a" aria-hidden="true">Myles</span> <span class="sign__b" aria-hidden="true">Parslow</span></h1>
  <p class="sign-sub" aria-hidden="true">makes things with AI</p>
  <figure class="plate plate--lobby">
    <a href="%(hh)s"><img src="../%(himg)s" alt="" width="560" height="350" decoding="async"></a>
    <figcaption><span>Now showing:</span> <b>%(hn)s</b> &mdash; <span>%(hs)s</span></figcaption>
  </figure>
  <div class="lh-text">
    <p class="lh-lede">%(lede)s</p>
    <dl class="plaques">%(plaques)s</dl>
    <a class="go" href="#plan"><span>Start at the floor plan</span><i aria-hidden="true">&darr;</i></a>
  </div>
</header>

<section class="sec plan-sec" id="plan" aria-labelledby="h-plan">
  <h2 class="disp" id="h-plan">Floor plan</h2>
  <p class="sec-note">Five rooms. Each room&rsquo;s floor area follows its number of projects. Select a room to go in.</p>
  <div class="plan-wrap">
    %(ghosts)s%(plan)s
    <ol class="bands" aria-label="Rooms">%(bands)s</ol>
  </div>
</section>

<section class="sec dir-sec" id="directory" aria-labelledby="h-dir">
  <h2 class="disp" id="h-dir">Directory</h2>
  <p class="sec-note">Every project, by room. The letter and number are the exhibit number on its wall label.</p>
  <div class="dir">%(cols)s</div>
</section>

<section class="sec rules-sec" id="rules" aria-labelledby="h-rules">
  <p class="eyebrow">%(r_eye)s</p>
  <h2 class="disp" id="h-rules">House rules</h2>
  <p class="sec-note">%(r_h2)s</p>
  <ol class="plaque-row">%(plq)s</ol>
</section>

<section class="sec tools-sec" id="tools" aria-labelledby="h-tools">
  <p class="eyebrow">%(t_eye)s</p>
  <h2 class="disp" id="h-tools">Visitor guide: which AI for what</h2>
  <h3 class="sub">%(t_h2)s</h3>
  <p class="sec-note">%(t_lede)s</p>
  %(t1)s
  <details class="more"><summary>%(t_sum)s</summary>%(t2)s</details>
</section>

<section class="sec archive" id="archive" aria-labelledby="h-archive">
  <div class="archive__in">
    <h2 class="sub" id="h-archive">Style archive</h2>
    <p>This site is also a running design experiment. Each version renders the same %(ncases)d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. <a href="../styles/index.html">See every version <span aria-hidden="true">&rarr;</span></a></p>
    <p class="archive__now">You&rsquo;re looking at: The Museum.</p>
  </div>
</section>
</main>

<footer class="desk" id="contact" aria-labelledby="h-desk">
  <h2 class="disp" id="h-desk">Information desk</h2>
  <p class="desk__say">%(say)s</p>
  <p class="desk__mail"><span class="lab">Email</span> <span class="addr">%(email)s</span> <a class="mailto" href="mailto:%(email)s">Write to this address</a></p>
  <ul class="desk__links">%(flinks)s<li><a href="#lobby">Back to top <span aria-hidden="true">&uarr;</span></a></li></ul>
  <p class="desk__line">%(mid)s</p>
</footer>
""" % dict(ncases=sum(COUNT.values()), bar=bar(), count=esc(count), hh=hh_link, himg=himg, hn=hn, hs=hs, lede=lede, plaques=plaques,
           ghosts=''.join('<i class="vtg" data-room="%s" aria-hidden="true" style="left:%.3f%%;top:%.3f%%;width:%.3f%%;height:%.3f%%;--room:var(--%s)"></i>'
                          % ((s,) + tuple(v * 100 for v in ((RECTS[s][0] + 3) / 1200, (RECTS[s][1] + 3) / 570, (RECTS[s][2] - 6) / 1200, (RECTS[s][3] - 6) / 570)) + (s,))
                          for s in SLUGS),
           plan=plan_svg(), bands=''.join(
               '<li><a class="band" data-room="%s" href="%s/index.html" style="--room:var(--%s);--n:%d"><span class="band__n" aria-hidden="true">%d</span>'
               '<span class="band__t">%s</span><span class="band__l">Room %d · %s · %d projects</span></a></li>'
               % (r['slug'], r['slug'], r['slug'], COUNT[r['slug']], i, SHORT[r['slug']], i, SHORT[r['slug']], COUNT[r['slug']])
               for i, r in enumerate(ROOMS, 1)),
           cols=''.join(cols), r_eye=r_eye, r_h2=r_h2, plq=plq, t_eye=t_eye, t_h2=t_h2, t_lede=t_lede, t1=t1, t2=t2,
           t_sum=t_sum, say=say, email=email, flinks=flinks, mid=mid)
    redirect = ('<script>(function(){var m=%s,h=location.hash.slice(1);'
                'if(h&&Object.prototype.hasOwnProperty.call(m,h))location.replace(m[h]+"/index.html#"+h);})();</script>\n'
                % HOME['redirect_map'].strip())
    return page('Myles Parslow · The Museum of things made with AI',
                'Myles Parslow makes things with AI. Five rooms, fifty-odd exhibits: legal software, business, creative work, design and research.',
                'lobby', None, '', inner, redirect)


# ------------------------------------------------------------------ room pages
def build_room(idx, r, id_room):
    slug, L = r['slug'], r['letter']
    name = r['title']
    cases = [i for i in r['items'] if i['kind'] == 'case']
    own_ids = {i['id'] for i in r['items']}
    first = cases[0]
    th = first['thumb'] or first_img(first['body_html'])
    th = ('../' + th) if th.startswith('../assets') else th
    lines = '<span class="giant__l">%s</span>' % SHORT[slug]
    index = ''.join('<li><a href="#%s"><span>%s%s</span>%s</a></li>' % (c['id'], L, c['count'].split('/')[0].strip(), c['title']) for c in cases)
    out = []
    for it in r['items']:
        if it['kind'] == 'group':
            m = re.search(r'<h2 class="gdiv__t">(.*?)</h2>(?:<p class="gdiv__p">(.*?)</p>)?', it['html'], re.S)
            out.append('<div class="gdiv" id="%s"><p class="gdiv__k">Gallery</p><h2 class="gdiv__t">%s</h2>%s</div>'
                       % (it['id'], m.group(1), '<p class="gdiv__p">%s</p>' % m.group(2) if m.group(2) else ''))
        elif it['kind'] == 'extra':
            out.append(it['html'])
        else:
            n = it['count'].split('/')[0].strip()
            kick = ' · '.join(k for k in it['kickers'] if k.strip())
            out.append("""<article class="exhibit" id="%(id)s" aria-labelledby="t-%(id)s">
  <aside class="label">
    <p class="label__no"><span class="label__acc">%(L)s%(n)s</span><span class="label__of">Exhibit %(count)s</span></p>
    <h2 class="label__t" id="t-%(id)s">%(title)s</h2>
    <p class="label__sub">%(sub)s</p>
    <dl class="label__meta"><div><dt>Medium:</dt><dd>%(kick)s</dd></div></dl>
    <p class="label__lede">%(lede)s</p>
  </aside>
  <div class="cbody">
%(body)s
%(links)s
  </div>
</article>""" % dict(id=it['id'], L=L, n=n, count=it['count'], title=it['title'], sub=it['sub'], kick=kick, lede=it['lede'],
                     body=fix_body(it['body_html'], slug, own_ids, id_room),
                     links=('<div class="links links--end">%s</div>' % fix_body(it['links_html'], slug, own_ids, id_room)) if it['links_html'].strip() else ''))
    # exit: next-room door and floor-plan strip
    if idx < 4:
        nr = ROOMS[idx + 1]
        door = ('<a class="door" href="../%s/index.html" style="--room:var(--%s)"><span class="door__room">Room %d · %s</span>'
                '<span class="door__go">Next room <i aria-hidden="true">&rarr;</i></span></a>' % (nr['slug'], nr['slug'], idx + 2, SHORT[nr['slug']]))
    else:
        door = ('<a class="door door--lobby" href="../index.html"><span class="door__room">The lobby</span>'
                '<span class="door__go">Back to the lobby <i aria-hidden="true">&rarr;</i></span></a>')
    strip = plan_svg(current=slug, mini=True, hrefs={s: '../%s/index.html' % s for s in SLUGS})
    inner = """%(bar)s
<div class="backdrop" id="backdrop"><div class="sheet" id="sheet">
<div class="sheet__top"><a class="close" href="../index.html#plan"><span aria-hidden="true">&times;</span> Close room</a></div>
<main id="main">
<header class="rhead" id="top" style="--fit:%(fit)svw" aria-labelledby="h-room">
  <div class="rhead__top">
  <h1 class="giant" id="h-room">%(lines)s</h1>
  <figure class="plate plate--hero">
    <img src="%(th)s" alt="" width="560" height="350" decoding="async">
  </figure>
  </div>
  <div class="rhead__meta">
    <p class="rhead__k">%(eyebrow)s</p>
    <p class="rhead__c">%(count)s</p>
    <p class="rhead__lede">%(lede)s</p>
    <nav class="rindex" aria-label="Exhibits in this room"><ol>%(index)s</ol></nav>
  </div>
</header>
<div class="hall">
%(out)s
</div>
<nav class="exit" aria-label="Leaving this room">
  %(door)s
  <div class="strip"><p class="strip__k">Floor plan</p>%(strip)s</div>
</nav>
</main>
<footer class="slim"><a href="../index.html#contact">Information desk</a><span><a href="../index.html">Myles Parslow</a> &middot; Made with AI</span></footer>
</div></div>
""" % dict(bar=bar(slug), fit=FIT[slug], lines=lines, th=th, eyebrow=r['eyebrow'], count=r['count'], lede=r['lede'],
           index=index, out='\n\n'.join(out), door=door, strip=strip)
    return page('%s · Myles Parslow Portfolio' % esc(name), plain(r['lede']), 'room', slug, '../', inner)


# ------------------------------------------------------------------ css / js
def main():
    id_room = {}
    for r in ROOMS:
        for it in r['items']:
            id_room[it['id']] = r['slug']
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(build_home())
    for i, r in enumerate(ROOMS):
        os.makedirs(os.path.join(OUT, r['slug']), exist_ok=True)
        with open(os.path.join(OUT, r['slug'], 'index.html'), 'w', encoding='utf-8') as f:
            f.write(build_room(i, r, id_room))
    with open(os.path.join(OUT, 'c.css'), 'w', encoding='utf-8') as f:
        f.write(CSS_TEXT.replace('/*VT*/', ''.join(
            '.vtg[data-room="%(s)s"],.band[data-room="%(s)s"],body[data-room="%(s)s"] .sheet{view-transition-name:room-%(s)s}\n' % {'s': s} for s in SLUGS)))
    with open(os.path.join(OUT, 'c.js'), 'w', encoding='utf-8') as f:
        f.write(JS_TEXT)
    print('wrote mockup-c: home + %d rooms, %d exhibits' % (len(ROOMS), sum(COUNT.values())))


CSS_TEXT = r"""/* Mockup C: The Museum. One family (Archivo, variable wdth + wght), five room colours, wall labels and passe-partout mats. */
:root{
  --char:#16181b;--cream:#f3ecdd;--ver:#ff5b2e;--ink:#1b1416;
  --legal:#4a0f1c;--business:#12372a;--creative:#5a3a12;--design:#1a2f8f;--research:#2f1838;
  --legal-t:#f4e6e6;--business-t:#e4efe9;--creative-t:#f3ead9;--design-t:#e5e9f7;--research-t:#eee4f1;
  --bar-h:56px;--gut:clamp(16px,4vw,64px);--max:1800px;
  --e:cubic-bezier(.2,.7,.2,1);
  color-scheme:dark;
}
body[data-room=legal]{--room:var(--legal);--room-t:var(--legal-t)}
body[data-room=business]{--room:var(--business);--room-t:var(--business-t)}
body[data-room=creative]{--room:var(--creative);--room-t:var(--creative-t)}
body[data-room=design]{--room:var(--design);--room-t:var(--design-t)}
body[data-room=research]{--room:var(--research);--room-t:var(--research-t)}

/* dark (default) */
body{--bg:var(--room,var(--char));--fg:var(--cream);--hd:var(--cream);--mute:rgba(243,236,221,.8);
  --mat:#efe7d6;--mat-ink:#1b1416;--mat-mute:rgba(27,20,22,.74);--rule:rgba(243,236,221,.3);--soft:rgba(243,236,221,.08);
  --bar:#16181b;--bar-fg:#f3ecdd;--btn:#f3ecdd;--btn-fg:#1b1416;--focus:var(--ver);--chip-edge:rgba(243,236,221,.38)}
:root[data-theme=light]{color-scheme:light}
:root[data-theme=light] body{--bg:var(--room-t,#f4efe4);--fg:var(--ink);--hd:var(--room,var(--ink));--mute:rgba(27,20,22,.78);
  --mat:#fff;--mat-ink:#1b1416;--mat-mute:rgba(27,20,22,.74);--rule:rgba(27,20,22,.28);--soft:rgba(27,20,22,.06);
  --bar:#f4efe4;--bar-fg:#1b1416;--btn:var(--room,#16181b);--btn-fg:#fff;--focus:#c7330a;--chip-edge:rgba(27,20,22,.38)}

*,*::before,*::after{box-sizing:border-box}
html{background:#16181b;scroll-padding-top:calc(var(--bar-h) + 16px);-webkit-text-size-adjust:100%}
:root[data-theme=light]{background:#f4efe4}
body{margin:0;background:var(--bg);color:var(--fg);
  font-family:"Archivo",system-ui,-apple-system,"Segoe UI",sans-serif;font-weight:400;font-stretch:100%;
  font-variation-settings:"wdth" 100,"wght" 400;font-size:18px;line-height:1.55;overflow-wrap:break-word}
img,video,svg{max-width:100%}
img{display:block;height:auto}
a{color:inherit}
h1,h2,h3,h4,p,ol,ul,dl,dd,figure{margin:0}
ol,ul{padding:0;list-style:none}
:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:fixed;left:12px;top:-80px;z-index:100;background:var(--ver);color:#16181b;padding:10px 16px;font-variation-settings:"wdth" 112,"wght" 600;font-size:15px;text-decoration:none}
.skip:focus{top:calc(var(--bar-h) + 8px)}

/* type roles */
.disp,.sign,.giant,.gdiv__t,.label__t,.dh-t,.pr-name{text-transform:uppercase;font-variation-settings:"wdth" 62,"wght" 800;font-weight:800;line-height:.86;letter-spacing:0}
.disp{font-size:clamp(56px,11vw,180px);color:var(--hd)}
.eyebrow,.lab,.label__meta dt,.label__of,.gdiv__k,.rhead__k,.rhead__c,.strip__k,.d-n,.chip,.wf-plan,.wf-home,.theme,.caption,figcaption,.dh-c,.band__l,.go,.sec-note.small{
  font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;line-height:1.4;letter-spacing:0;text-transform:none}
.sub{font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:clamp(22px,2.4vw,34px);line-height:1;margin:18px 0 8px}
.sec-note{max-width:66ch;color:var(--mute);margin-top:18px}
.sec{padding:clamp(56px,9vw,132px) var(--gut) 0;max-width:var(--max);margin:0 auto}
.eyebrow{color:var(--mute);margin-bottom:10px}

/* wayfinding bar (fixed) */
.wf{position:fixed;inset:0 0 auto 0;z-index:50;background:var(--bar);color:var(--bar-fg);border-bottom:1px solid var(--rule)}
.wf__in{height:var(--bar-h);display:flex;align-items:center;gap:14px;padding:0 var(--gut);max-width:var(--max);margin:0 auto}
.wf-home,.wf-plan{display:inline-flex;align-items:center;gap:8px;text-decoration:none;font-size:14px;padding:8px 2px;white-space:nowrap}
.wf-home svg,.wf-plan svg{color:var(--ver)}
:root[data-theme=light] .wf-home svg,:root[data-theme=light] .wf-plan svg{color:#c7330a}
.wf-home span{font-variation-settings:"wdth" 112,"wght" 700}
.wf-home:hover span,.wf-plan:hover span{text-decoration:underline;text-underline-offset:4px}
.wf-home[aria-current]{text-decoration:underline;text-underline-offset:5px;text-decoration-color:var(--ver);text-decoration-thickness:2px}
.chips{display:flex;gap:6px;margin:0 auto;flex-wrap:nowrap}
.chip{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border-radius:99px;text-decoration:none;white-space:nowrap;
  box-shadow:inset 0 0 0 1.5px color-mix(in srgb,var(--room) 55%,var(--chip-edge));position:relative;transition:background-color .2s}
.chip__n{width:8px;height:8px;border-radius:50%;background:var(--room);box-shadow:0 0 0 1px var(--chip-edge);font-size:0}
:root[data-theme=light] .chip__n{box-shadow:none}
.chip:hover{background:color-mix(in srgb,var(--room) 60%,transparent)}
.chip[aria-current=page]{background:var(--room);color:#f3ecdd;box-shadow:inset 0 0 0 1.5px #f3ecdd}
.chip[aria-current=page]::after{content:"";position:absolute;left:50%;bottom:-9px;width:34px;height:4px;margin-left:-17px;background:var(--ver)}
.chip[aria-current=page] .chip__n{background:var(--ver);box-shadow:none}
.theme{appearance:none;font:inherit;display:inline-flex;align-items:center;gap:8px;background:none;color:inherit;border:0;
  box-shadow:inset 0 0 0 1.5px var(--chip-edge);border-radius:99px;padding:7px 13px;cursor:pointer;font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;white-space:nowrap}
.theme i{width:14px;height:14px;border-radius:50%;background:linear-gradient(90deg,currentColor 50%,transparent 50%);box-shadow:inset 0 0 0 1.5px currentColor}
.theme:hover{background:var(--soft)}

/* shared: mats, plates */
.plate,.cbody figure{background:var(--mat);color:var(--mat-ink);padding:clamp(14px,1.4vw,20px);
  box-shadow:0 1px 0 rgba(0,0,0,.25),0 18px 36px -18px rgba(0,0,0,.55)}
.plate img,.cbody figure img,.cbody figure video{width:100%;display:block}
.plate figcaption,.cbody figcaption{color:var(--mat-mute);font-size:13.5px;line-height:1.45;padding-top:10px;max-width:none}
:root[data-theme=light] .plate,:root[data-theme=light] .cbody figure{box-shadow:0 0 0 1px rgba(27,20,22,.14),0 16px 30px -20px rgba(27,20,22,.4)}

/* ============ LOBBY ============ */
.lobby{--bg:var(--char)}
:root[data-theme=light] .lobby{--bg:#f4efe4;--hd:#16181b}
.lobby-head{position:relative;padding:calc(var(--bar-h) + clamp(28px,5vw,64px)) var(--gut) clamp(40px,7vw,96px);max-width:var(--max);margin:0 auto;
  display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-areas:"k k" "sign sign" "sub sub" "text plate";gap:0 clamp(24px,4vw,64px);align-items:start}
.lh-k{grid-area:k;font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;color:var(--mute);margin-bottom:clamp(8px,2vw,24px)}
.sign{grid-area:sign;font-size:clamp(70px,14.9vw,300px);line-height:.8;color:var(--cream);white-space:nowrap;letter-spacing:-.005em}
:root[data-theme=light] .sign{color:#16181b}
.sign__a,.sign__b{display:inline}
.sign-sub{grid-area:sub;justify-self:start;max-width:46%;font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:clamp(26px,3.6vw,64px);line-height:1;margin:clamp(14px,2vw,28px) 0 0;color:var(--ver)}
:root[data-theme=light] .sign-sub{color:#c7330a}
.plate--lobby{grid-area:plate;margin-top:clamp(-90px,-6vw,-30px);position:relative;z-index:2;justify-self:end;width:min(100%,560px);transform-origin:top right}
.plate--lobby a{display:block}
.plate--lobby figcaption b{font-variation-settings:"wdth" 112,"wght" 700}
.lh-text{grid-area:text;margin-top:clamp(28px,4vw,56px);max-width:66ch}
.lh-lede{font-size:clamp(18px,1.5vw,22px);line-height:1.5}
.plaques{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}
.plaque{display:flex;flex-direction:column;background:var(--mat);color:var(--mat-ink);padding:14px 18px 16px;min-width:180px;flex:1 1 220px;max-width:340px;box-shadow:inset 0 0 0 4px var(--mat),inset 0 0 0 5px rgba(27,20,22,.4)}
.plaque dd{order:1;font-variation-settings:"wdth" 75,"wght" 800;font-size:clamp(28px,3vw,42px);line-height:1;text-transform:uppercase;margin-bottom:8px;font-variant-numeric:tabular-nums}
.plaque dt{order:2;font-variation-settings:"wdth" 112,"wght" 500;font-size:13.5px;line-height:1.4;color:var(--mat-mute)}
.go{display:inline-flex;gap:10px;align-items:center;margin-top:32px;text-decoration:none;font-size:15px;padding:12px 18px;background:var(--ver);color:#16181b;font-variation-settings:"wdth" 112,"wght" 700}
.go i{font-style:normal;font-size:20px;transition:transform .2s var(--e)}
.go:hover i{transform:translateY(4px)}

/* floor plan */
.plan-wrap{margin-top:clamp(28px,4vw,56px)}
.plan{width:100%;height:auto;display:block;overflow:visible}
.plan .wall{fill:none;stroke:var(--cream);stroke-width:6;stroke-linecap:square}
:root[data-theme=light] .plan .wall{stroke:#16181b}
.plan .arrow{fill:none;stroke:var(--ver);stroke-width:4;stroke-linecap:square}
.plan .pr-ent{fill:var(--mute);font:500 17px "Archivo",sans-serif;font-variation-settings:"wdth" 112,"wght" 500}
.pr{cursor:pointer;outline:none;transition:transform .28s var(--e)}
.pr rect{fill:var(--room);stroke:rgba(243,236,221,.28);stroke-width:1.5;transition:stroke .2s}
.pr text{fill:#f3ecdd}
.pr .pr-n{font:800 54px "Archivo",sans-serif;font-variation-settings:"wdth" 62,"wght" 800;opacity:.55}
.pr .pr-name{font:800 66px "Archivo",sans-serif;font-variation-settings:"wdth" 62,"wght" 800;letter-spacing:0}
.pr .pr-l{font:500 17px "Archivo",sans-serif;font-variation-settings:"wdth" 112,"wght" 500}
.pr:hover,.pr:focus-visible,.pr.is-hot{transform:translateY(-9px);filter:drop-shadow(0 14px 14px rgba(0,0,0,.45))}
.pr:hover rect,.pr:focus-visible rect,.pr.is-hot rect{stroke:var(--ver);stroke-width:4}
.plan--mini .pr:hover,.plan--mini .pr:focus-visible{transform:translateY(-5px)}
.plan--mini .pr .pr-l{font-size:40px;font-variation-settings:"wdth" 62,"wght" 800;opacity:.9}
.plan--mini .pr[aria-current=page] rect{stroke:var(--ver);stroke-width:5}
.plan--mini .pr-here{fill:var(--ver)}
.bands{display:none}
.band{display:grid;gap:2px;align-content:end;text-decoration:none;background:var(--room);color:#f3ecdd;padding:16px 18px;min-height:calc(var(--n) * 8px + 78px);position:relative;border-bottom:3px solid var(--char);transition:padding .2s var(--e)}
:root[data-theme=light] .band{border-bottom-color:#f4efe4}
.band__n{position:absolute;top:10px;right:16px;font-variation-settings:"wdth" 62,"wght" 800;font-size:54px;line-height:1;opacity:.5}
.band__t{font-variation-settings:"wdth" 62,"wght" 800;text-transform:uppercase;font-size:clamp(44px,15vw,72px);line-height:.86}
.band:hover,.band:focus-visible{outline-offset:-3px;padding-left:30px}
.band:focus-visible{outline:3px solid var(--ver)}

/* directory */
.dir{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:clamp(28px,4vw,56px)}
.dircol{background:var(--room);color:#f3ecdd;padding:20px 18px 24px;display:flex;flex-direction:column;gap:14px;border-top:6px solid var(--room);transition:transform .25s var(--e),border-color .2s,box-shadow .25s;box-shadow:inset 0 0 0 1px rgba(243,236,221,.14)}
:root[data-theme=light] .dircol{background:var(--room-t);color:var(--ink);box-shadow:inset 0 0 0 1px rgba(27,20,22,.12);border-top-color:var(--room)}
.dircol h3 a{display:flex;flex-direction:column;gap:6px;text-decoration:none}
.dh-n{font-variation-settings:"wdth" 62,"wght" 800;font-size:15px;opacity:.7;display:none}
.dh-t{font-size:clamp(34px,3.6vw,56px);line-height:.88;color:inherit}
:root[data-theme=light] .dh-t{color:var(--room)}
.dh-c{opacity:.85}
.dircol ol{display:grid;gap:2px;border-top:1px solid currentColor;padding-top:6px}
.dircol ol{border-top-color:rgba(243,236,221,.4)}
:root[data-theme=light] .dircol ol{border-top-color:rgba(27,20,22,.35)}
.d-item{display:grid;grid-template-columns:42px minmax(0,1fr);gap:8px;text-decoration:none;padding:8px 6px 8px 0;border-bottom:1px solid rgba(243,236,221,.14)}
:root[data-theme=light] .d-item{border-bottom-color:rgba(27,20,22,.12)}
.d-n{opacity:.72;font-size:13px;padding-top:3px;font-variant-numeric:tabular-nums}
.d-t{display:flex;flex-direction:column;min-width:0}
.d-t b{font-variation-settings:"wdth" 100,"wght" 650;font-weight:650;font-size:17px;line-height:1.2}
.d-t span{font-size:14px;line-height:1.35;opacity:.82}
.d-item:hover b{text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px}
.d-item:focus-visible{outline-offset:-2px;background:rgba(255,91,46,.18)}
.dircol.is-hot{transform:translateY(-8px);border-top-color:var(--ver);box-shadow:0 18px 30px -14px rgba(0,0,0,.6),inset 0 0 0 1px rgba(243,236,221,.3)}
.dircol:focus-within{border-top-color:var(--ver)}

/* house rules */
.plaque-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(12px,2vw,28px);margin-top:clamp(28px,4vw,56px);counter-reset:r}
.rule{background:var(--mat);color:var(--mat-ink);padding:clamp(22px,2.4vw,36px);display:grid;gap:14px;align-content:start;box-shadow:inset 0 0 0 7px var(--mat),inset 0 0 0 8px rgba(27,20,22,.45)}
.rule__n{font-variation-settings:"wdth" 62,"wght" 800;font-size:clamp(64px,7vw,110px);line-height:.8;color:var(--ink)}
.rule h4{font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:clamp(24px,2.2vw,34px);line-height:1}
.rule p{color:var(--mat-mute)}

/* visitor guide table */
.guide{width:100%;border-collapse:collapse;margin-top:clamp(20px,3vw,36px)}
.guide thead th{text-align:left;font-variation-settings:"wdth" 112,"wght" 600;font-size:14px;padding:10px 12px;border-bottom:3px solid var(--fg)}
.guide tbody th,.guide tbody td{vertical-align:top;border-bottom:1px solid var(--rule);padding:18px 12px;text-align:left}
.guide tbody th{width:26%;font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:clamp(20px,1.8vw,26px);line-height:1.05}
.guide dl{display:grid;gap:10px}
.guide dl>div{display:grid;grid-template-columns:110px minmax(0,1fr);gap:14px}
.guide dt{font-variation-settings:"wdth" 112,"wght" 600;font-size:14px;color:var(--mute);padding-top:3px}
.guide dd{max-width:66ch}
.guide tbody tr:hover{background:var(--soft)}
.more>summary{cursor:pointer;margin-top:24px;display:inline-block;padding:12px 18px;background:var(--btn);color:var(--btn-fg);font-variation-settings:"wdth" 112,"wght" 600;font-size:15px}
.more[open]>summary{margin-bottom:8px}
.more>summary:hover{background:var(--ver);color:#16181b}

/* information desk */
.desk{max-width:var(--max);margin:clamp(72px,10vw,150px) auto 0;padding:clamp(40px,6vw,80px) var(--gut) clamp(40px,6vw,72px);border-top:6px solid var(--ver);display:grid;gap:18px;grid-template-columns:minmax(0,1fr)}
.desk__say{font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:clamp(28px,4vw,56px);line-height:1}
.desk__mail{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline}
.desk__mail .lab{color:var(--mute)}
.addr{font-variation-settings:"wdth" 100,"wght" 650;font-size:clamp(22px,3vw,40px);user-select:all;-webkit-user-select:all;overflow-wrap:anywhere}
.mailto{font-size:14px;font-variation-settings:"wdth" 112,"wght" 500}
.desk__links{display:flex;flex-wrap:wrap;gap:8px 28px}
.desk__links a{font-variation-settings:"wdth" 112,"wght" 600;font-size:16px;text-underline-offset:4px}
.desk__line{color:var(--mute);font-variation-settings:"wdth" 112,"wght" 500;font-size:14px}

/* ============ ROOM ============ */
body.room{--back:#16181b;--edge:clamp(20px,2vw,28px);background:var(--back)}
:root[data-theme=light] body.room{--back:#e3dccb}
.backdrop{padding:var(--bar-h) var(--edge) var(--edge);cursor:zoom-out;min-height:100svh}
.sheet{cursor:auto;background:var(--bg);position:relative;overflow:clip;border-radius:0 0 14px 14px;min-height:calc(100svh - var(--bar-h) - var(--edge));box-shadow:0 0 0 1px rgba(243,236,221,.14),0 30px 60px -30px rgba(0,0,0,.7)}
:root[data-theme=light] .sheet{box-shadow:0 0 0 1px rgba(27,20,22,.2),0 30px 60px -30px rgba(27,20,22,.35)}
.sheet__top{display:flex;justify-content:flex-end;padding:14px var(--gut) 0;position:relative;z-index:5}
.close{display:inline-flex;gap:8px;align-items:center;padding:8px 14px;text-decoration:none;box-shadow:inset 0 0 0 1.5px currentColor;font-variation-settings:"wdth" 112,"wght" 600;font-size:14px;line-height:1.3}
.close span{font-size:20px;line-height:1}
.close:hover{background:var(--ver);color:#16181b;box-shadow:none}
.vtg{position:absolute;pointer-events:none;background:var(--room);display:block}
.plan-wrap{position:relative}
.wf{view-transition-name:wf}
@view-transition{navigation:auto}
::view-transition-group(*){animation-duration:.5s;animation-timing-function:cubic-bezier(.2,.7,.2,1)}
::view-transition-old(wf),::view-transition-new(wf){animation:none}
/*VT*/
.archive{padding-bottom:0}
.archive__in{background:var(--mat);color:var(--mat-ink);padding:clamp(22px,3vw,40px);display:grid;gap:12px;max-width:80ch;box-shadow:inset 0 0 0 7px var(--mat),inset 0 0 0 8px rgba(27,20,22,.45)}
.archive__in .sub{margin:0;color:var(--ink)}
.archive__in a{font-variation-settings:"wdth" 100,"wght" 650}
.archive__now{font-variation-settings:"wdth" 112,"wght" 600;font-size:15px}
.rhead{position:relative;padding:0 0 clamp(32px,5vw,72px);overflow:hidden}
.rhead__top{position:relative;padding-bottom:var(--hang,0px)}
.giant{font-size:var(--fit);line-height:.78;color:var(--hd);padding:0 var(--gut);white-space:nowrap;display:block}
.giant__l{display:inline-block;padding-top:.06em;white-space:nowrap}
.plate--hero{position:absolute;right:var(--gut);bottom:0;width:var(--plate-w,clamp(180px,20vw,380px));z-index:3}
.rhead__meta{position:relative;z-index:2;padding:clamp(28px,4vw,56px) var(--gut) 0;max-width:var(--max);margin:0 auto;display:grid;grid-template-columns:minmax(150px,220px) minmax(0,1fr);gap:8px clamp(20px,3vw,48px)}
.rhead__k{grid-column:1;color:var(--mute)}
.rhead__c{grid-column:1;color:var(--mute);margin-top:-6px}
.rhead__k{font-size:15px;color:var(--fg)}
.rhead__lede{grid-column:2;grid-row:1/span 2;font-size:clamp(19px,1.7vw,24px);line-height:1.5;max-width:66ch}
.rindex{grid-column:2;margin-top:28px}
.rindex ol{columns:2;column-gap:32px}
.rindex a{display:grid;grid-template-columns:48px minmax(0,1fr);gap:8px;padding:6px 0;border-top:1px solid var(--rule);text-decoration:none;font-variation-settings:"wdth" 100,"wght" 550;font-size:16px;break-inside:avoid}
.rindex a span{font-variation-settings:"wdth" 112,"wght" 500;font-size:13px;color:var(--mute);padding-top:2px}
.rindex a:hover{text-decoration:underline;text-underline-offset:3px}

.hall{max-width:var(--max);margin:0 auto;padding:clamp(24px,4vw,56px) var(--gut) 0}
.gdiv{margin:clamp(56px,9vw,130px) 0 clamp(24px,4vw,48px);padding-top:18px;border-top:6px solid var(--fg);scroll-margin-top:calc(var(--bar-h) + 16px)}
.gdiv:first-child{margin-top:0}
.gdiv__k{color:var(--mute);margin-bottom:12px}
.gdiv__t{font-size:clamp(48px,9vw,150px);color:var(--hd)}
.gdiv__p{max-width:66ch;margin-top:20px;color:var(--mute)}

.exhibit{display:grid;grid-template-columns:minmax(0,1fr);gap:24px;padding:clamp(28px,4vw,56px) 0 clamp(40px,6vw,90px);border-top:1px solid var(--rule);scroll-margin-top:calc(var(--bar-h) + 16px)}
.gdiv+.exhibit{border-top:0}
.label{background:var(--mat);color:var(--mat-ink);padding:clamp(18px,2vw,28px);display:grid;gap:14px;align-content:start;box-shadow:inset 0 0 0 6px var(--mat),inset 0 0 0 7px rgba(27,20,22,.4),0 18px 34px -20px rgba(0,0,0,.55)}
:root[data-theme=light] .label{box-shadow:inset 0 0 0 6px var(--mat),inset 0 0 0 7px rgba(27,20,22,.35),0 0 0 1px rgba(27,20,22,.14)}
.label__no{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:0 6px}
.label__acc{font-variation-settings:"wdth" 62,"wght" 800;font-size:26px;line-height:1;background:var(--room);color:#f3ecdd;padding:6px 10px 5px}
:root[data-theme=light] .label__acc{background:var(--room);color:#fff}
.label__of{color:var(--mat-mute)}
.label__t{font-variation-settings:"wdth" 75,"wght" 700;font-weight:700;font-size:clamp(32px,5vw,72px);line-height:.92;color:var(--room);padding:0 6px;overflow-wrap:break-word;hyphens:auto}
.label__sub{padding:0 6px;font-variation-settings:"wdth" 100,"wght" 600;font-size:18px;line-height:1.3}
.label__meta{padding:0 6px;border-top:1px solid rgba(27,20,22,.35);padding-top:12px}
.label__meta>div{display:flex;flex-wrap:wrap;gap:2px 8px}
.label__meta dt{font-size:14px;font-variation-settings:"wdth" 112,"wght" 700}
.label__meta dd{font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;line-height:1.4}
.label__lede{padding:0 6px 4px;font-size:16.5px;line-height:1.5;color:var(--mat-ink);max-width:66ch}

/* ---- exhibit body ---- */
.cbody{display:grid;gap:clamp(28px,4vw,52px);min-width:0;align-content:start}
.cbody>*{min-width:0}
.cbody p,.cbody li,.cbody dd{max-width:66ch}
.cbody p{line-height:1.55}
.cbody strong{font-variation-settings:"wdth" 100,"wght" 650}
.cbody a{text-underline-offset:3px;text-decoration-thickness:1px}
.cbody a:hover{text-decoration-thickness:2px}
.cbody h3,.cbody h4{font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;line-height:1;color:var(--hd);margin:0}
.cbody h3{font-size:clamp(24px,2.3vw,34px)}
.cbody h4{font-size:19px}
.cbody ul,.cbody ol{display:grid;gap:.55em;padding-left:1.15em;list-style:disc}
.cbody ol{list-style:decimal}
.cbody li::marker{color:var(--mute)}
.cbody code{font:inherit;font-variation-settings:"wdth" 112,"wght" 600;background:var(--soft);padding:.05em .35em}
.cbody .block{display:grid;gap:14px;align-content:start;border-top:3px solid var(--fg);padding-top:14px;min-width:0}
.cbody .block .block{border-top:1px solid var(--rule)}
.cbody .cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(24px,3.4vw,52px);align-items:start}
.cbody .shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2vw,28px);align-items:start}
.cbody .grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(16px,2vw,28px);align-items:start}
.cbody .grid3>div{display:grid;gap:8px;align-content:start;border-top:3px solid var(--fg);padding-top:12px}
.cbody .gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(14px,1.6vw,22px);align-items:start}
.cbody .more,.cbody .more>div{min-width:0}
.cbody .more{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px clamp(24px,3.4vw,52px)}
.cbody .more>div{display:grid;gap:8px;align-content:start;border-top:3px solid var(--fg);padding-top:12px}
.cbody figure{display:grid;align-content:start;min-width:0}
.cbody figure:has(img.portrait){max-width:430px}
.cbody img.portrait,.cbody video.portrait{max-width:100%}
.cbody .reels{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(12px,1.4vw,20px);align-items:start}
.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr));max-width:620px}
.cbody .reels video{aspect-ratio:9/16;object-fit:cover;background:#000}
.cbody video{background:#000}

/* made: a small plaque */
.cbody .made{display:grid;gap:6px;background:var(--soft);border-left:6px solid var(--fg);padding:14px 18px 16px;max-width:66ch}
.cbody .made b{font-variation-settings:"wdth" 112,"wght" 700;font-size:14px;line-height:1.35}
.cbody .made p{color:var(--fg)}
.cbody .note{font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;color:var(--mute)}
.cbody .logline{font-variation-settings:"wdth" 100,"wght" 500;font-size:clamp(19px,1.6vw,23px);line-height:1.35}
.cbody .kind{font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;color:var(--mute)}
.cbody .count{font-variation-settings:"wdth" 75,"wght" 800;text-transform:uppercase;font-size:24px;line-height:1}

/* stats: small plaques */
.cbody .stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.cbody .stats>div{display:flex;flex-direction:column;background:var(--mat);color:var(--mat-ink);padding:12px 14px 14px;box-shadow:inset 0 0 0 3px var(--mat),inset 0 0 0 4px rgba(27,20,22,.4)}
.cbody .stats dd{order:1;font-variation-settings:"wdth" 75,"wght" 800;text-transform:uppercase;font-size:clamp(24px,2.4vw,34px);line-height:1;margin-bottom:6px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.cbody .stats dt{order:2;font-variation-settings:"wdth" 112,"wght" 500;font-size:13px;line-height:1.35;color:var(--mat-mute)}

/* link buttons */
.cbody .links{display:flex;flex-wrap:wrap;gap:10px;align-items:center;max-width:none}
.cbody .links a,.cbody .piece-text>p>a:only-child{display:inline-flex;align-items:center;gap:.6em;padding:12px 18px;background:var(--btn);color:var(--btn-fg);text-decoration:none;font-variation-settings:"wdth" 112,"wght" 650;font-size:15px;line-height:1.2;transition:background-color .15s,color .15s}
.cbody .links a:hover,.cbody .piece-text>p>a:only-child:hover{background:var(--ver);color:#16181b}
.cbody .links a[target=_blank]::after{content:"\2197";font-size:1.15em;line-height:1}
.cbody .links span{font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;color:var(--mute)}
.cbody .links a:focus-visible{outline-color:var(--fg)}

/* compare slider */
.cbody .compare{position:relative;overflow:hidden;width:100%;--pos:50%;touch-action:pan-y;background:#000}
.cbody .compare.portrait{max-width:360px;margin-inline:auto}
.cbody .compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;max-width:none}
.cbody .compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cbody .cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:3px;margin-left:-1.5px;background:var(--ver);pointer-events:none}
.cbody .cmp-line::after{content:"\2194";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:42px;height:42px;border-radius:50%;background:var(--ver);color:#16181b;display:grid;place-items:center;font:700 18px/1 "Archivo",sans-serif}
.cbody .cmp-tag{position:absolute;top:10px;font-variation-settings:"wdth" 112,"wght" 650;font-size:12px;line-height:1;background:#16181b;color:#f3ecdd;padding:6px 9px;pointer-events:none}
.cbody .cmp-tag.l{left:10px}.cbody .cmp-tag.r{right:10px}
.cbody .compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.cbody .compare:focus-within{outline:3px solid var(--ver);outline-offset:3px}

/* flow, piece, tags, facts, books */
.cbody .flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;padding:0;list-style:none;counter-reset:step}
.cbody .flow li{counter-increment:step;display:grid;gap:6px;align-content:start;border-top:3px solid var(--fg);padding-top:10px}
.cbody .flow b{font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:20px;line-height:1}
.cbody .flow b::before{content:counter(step,decimal-leading-zero) " ";font-variation-settings:"wdth" 112,"wght" 500;font-size:13px;display:block;margin-bottom:4px;color:var(--mute)}
.cbody .flow span{font-size:15.5px;line-height:1.45;color:var(--mute)}
.cbody .piece{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:clamp(20px,3vw,40px);align-items:start}
.cbody .piece.flip>figure{order:2}
.cbody .piece-text{display:grid;gap:14px;align-content:start;min-width:0}
.cbody .tags{display:flex;flex-wrap:wrap;gap:6px}
.cbody .tag{font-variation-settings:"wdth" 112,"wght" 500;font-size:13px;line-height:1;padding:7px 10px;box-shadow:inset 0 0 0 1.5px var(--fg)}
.cbody .tag.hot{background:var(--fg);color:var(--bg);box-shadow:none}
.cbody .facts{display:flex;flex-wrap:wrap;gap:6px 22px;font-variation-settings:"wdth" 112,"wght" 500;font-size:14px;color:var(--mute)}
.cbody .facts strong{font-variation-settings:"wdth" 75,"wght" 800;font-size:26px;line-height:1;color:var(--fg);margin-right:.2em}
.cbody .books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(16px,2vw,28px);align-items:start}
.cbody .book{display:grid;gap:12px;align-content:start;min-width:0;padding:clamp(16px,1.8vw,26px);background:var(--soft);box-shadow:inset 0 0 0 1px var(--rule)}
.cbody .book.lead{grid-column:1/-1;grid-template-columns:minmax(0,13rem) minmax(0,1fr);gap:clamp(18px,2.4vw,32px)}
.cbody .lead-text{display:grid;gap:12px;min-width:0}
.cbody img.cover{max-width:240px;background:var(--mat);padding:clamp(10px,1vw,14px)}
.cbody .sub-case{display:grid;gap:clamp(20px,3vw,32px);border-top:6px solid var(--fg);padding-top:clamp(24px,3vw,40px)}
.cbody .sub-case>h3{font-size:clamp(32px,4vw,60px)}

/* extras */
.xsec{max-width:var(--max);margin:clamp(56px,8vw,120px) auto 0;padding:18px var(--gut) 0;border-top:6px solid var(--fg);scroll-margin-top:calc(var(--bar-h) + 16px)}
.xsec__h{display:grid;gap:6px}
.xsec__t{font-size:clamp(48px,8vw,130px);color:var(--hd);text-transform:uppercase;font-variation-settings:"wdth" 62,"wght" 800;line-height:.86}
.xsec__list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px clamp(24px,3.4vw,52px);margin-top:28px}
.xsec__list>div{border-top:3px solid var(--fg);padding-top:12px;display:grid;gap:8px;align-content:start}
.xsec__list h3{font-variation-settings:"wdth" 75,"wght" 700;text-transform:uppercase;font-size:clamp(22px,2vw,30px);line-height:1;color:var(--hd)}
.xsec__list p{max-width:66ch}

/* exit: door + strip */
.exit{max-width:var(--max);margin:clamp(64px,10vw,150px) auto 0;padding:0 var(--gut);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:clamp(24px,4vw,64px);align-items:end}
.door{position:relative;display:grid;align-content:space-between;gap:24px;min-height:clamp(300px,34vw,440px);width:min(100%,460px);padding:clamp(28px,3vw,44px) clamp(20px,2.4vw,32px) 28px;background:var(--room);color:#f3ecdd;text-decoration:none;
  border-radius:999px 999px 0 0;box-shadow:inset 0 0 0 1px rgba(243,236,221,.3),0 0 0 6px var(--bg),0 0 0 7px rgba(243,236,221,.5);justify-items:center;text-align:center;transition:transform .3s var(--e)}
:root[data-theme=light] .door{box-shadow:0 0 0 6px var(--bg),0 0 0 7px rgba(27,20,22,.5)}
.door::before{content:"";position:absolute;right:22px;top:62%;width:12px;height:12px;border-radius:50%;background:var(--ver)}
.door--lobby{--room:var(--char)}
.door__room{font-variation-settings:"wdth" 62,"wght" 800;text-transform:uppercase;font-size:clamp(40px,5vw,72px);line-height:.88;padding-top:clamp(40px,6vw,90px)}
.door__go{font-variation-settings:"wdth" 112,"wght" 650;font-size:18px;display:inline-flex;gap:10px;align-items:center}
.door__go i{font-style:normal;color:var(--ver);font-size:26px;transition:transform .2s var(--e)}
.door:hover,.door:focus-visible{transform:translateY(-8px)}
.door:hover .door__go i{transform:translateX(6px)}
.strip{display:grid;gap:10px}
.strip__k{color:var(--mute)}
.strip .plan{max-width:560px}
.strip .wall{stroke-width:8}
.slim{max-width:var(--max);margin:clamp(48px,7vw,96px) auto 0;padding:24px var(--gut) 36px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;border-top:1px solid var(--rule);font-variation-settings:"wdth" 112,"wght" 500;font-size:14px}
.slim span{color:var(--mute)}

/* ============ responsive ============ */
@media (min-width:1000px){
  .exhibit{grid-template-columns:minmax(320px,32%) minmax(0,1fr);gap:clamp(28px,4vw,64px);align-items:start}
  .label{position:sticky;top:calc(var(--bar-h) + 20px);max-height:calc(100svh - var(--bar-h) - 40px);overflow:auto}
}
@media (max-width:1280px){
  .cbody .flow{grid-template-columns:repeat(3,minmax(0,1fr))}
  .dir{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media (max-width:1100px){
  .plate--hero{position:relative;right:auto;bottom:auto;transform:none;width:min(72%,340px);margin:20px var(--gut) 0 auto}
}
@media (max-width:999px){
  .cbody .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}
  .plaque-row{grid-template-columns:minmax(0,1fr)}
  .dir{grid-template-columns:repeat(2,minmax(0,1fr))}
  .exit{grid-template-columns:minmax(0,1fr)}
  .lobby-head{grid-template-columns:minmax(0,1fr);grid-template-areas:"k" "sign" "sub" "plate" "text"}
  .plate--lobby{margin-top:28px;justify-self:start}
  .sign-sub{max-width:none}
}
@media (max-width:760px){
  :root{--bar-h:92px}
  .wf__in{flex-wrap:wrap;height:auto;min-height:var(--bar-h);align-content:center;gap:4px 10px;padding-top:6px;padding-bottom:8px}
  .wf-home{order:0}.wf-plan{order:1}.theme{order:2;margin-left:auto}
  .chips{order:3;flex:1 0 100%;margin:0;justify-content:space-between;gap:3px}
  .chip{padding:6px 7px;gap:0;font-size:12.5px}
  .chip__n{display:none}
  .chip[aria-current=page]::after{bottom:-7px}
  .plan:not(.plan--mini),.vtg{display:none}
  :root{--edge:8px}
  .bands{display:block}
  .dir{grid-template-columns:minmax(0,1fr)}
  .guide thead{display:none}
  .guide,.guide tbody,.guide tr,.guide tbody th,.guide tbody td{display:block;width:100%}
  .guide tbody th{padding:16px 0 4px;border-bottom:0}
  .guide tbody td{padding:0 0 16px}
  .guide dl>div{grid-template-columns:minmax(0,1fr);gap:2px}
  .cbody .cols,.cbody .shots,.cbody .grid3,.cbody .more,.cbody .piece,.cbody .books,.cbody .book.lead,.xsec__list{grid-template-columns:minmax(0,1fr)}
  .cbody .piece.flip>figure{order:0}
  .cbody .flow{grid-template-columns:minmax(0,1fr)}
  .cbody .reels{grid-template-columns:repeat(2,minmax(0,1fr))}
  .rhead__meta{grid-template-columns:minmax(0,1fr)}
  .rhead__lede,.rindex{grid-column:1;grid-row:auto}
  .rindex ol{columns:1}
  .rhead__k,.rhead__c{grid-column:1}
  .exit{align-items:start}
  .door{width:100%}
  .sign{white-space:normal;font-size:22.5vw}
  .sign__a,.sign__b{display:block}
  .plaque{flex-basis:100%;max-width:none}
}
@media (max-width:480px){.cbody .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}}

/* ============ motion (CSS only) ============ */
@media (prefers-reduced-motion:no-preference){
  @supports (animation-timeline:scroll()){
    @keyframes drift{from{transform:translateX(0)}to{transform:translateX(-7vw)}}
    @keyframes settle{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:none}}
    .giant{animation:drift linear both;animation-timeline:scroll(root);animation-range:0 90vh}
    .sign{animation:drift linear both;animation-timeline:scroll(root);animation-range:0 80vh}
    .exhibit .label,.exhibit .cbody>:first-child{animation:settle linear both;animation-timeline:view();animation-range:entry 0% entry 220px}
  }
}
@media (prefers-reduced-motion:reduce){
  @view-transition{navigation:none}
  *,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important}
  .pr:hover,.pr:focus-visible,.pr.is-hot,.dircol.is-hot,.door:hover,.door:focus-visible{transform:none}
}
"""
JS_TEXT = r"""/* Mockup C: theme toggle, floor-plan <-> directory sync, before/after sliders. No libraries. */
(function () {
  'use strict';
  var d = document.documentElement;

  /* theme toggle (the head script already set data-theme, so there is no flash) */
  var btn = document.querySelector('.theme');
  function paint() {
    if (!btn) return;
    var t = d.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    var other = t === 'light' ? 'dark' : 'light';
    btn.setAttribute('aria-label', 'Theme: ' + t + '. Switch to ' + other + '.');
    btn.querySelector('span').textContent = t === 'light' ? 'Light' : 'Dark';
  }
  paint();
  if (btn) btn.addEventListener('click', function () {
    var t = d.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    d.setAttribute('data-theme', t);
    try { localStorage.setItem('mpc-theme', t); } catch (e) {}
    paint();
  });

  /* lobby: hovering or focusing a room on the plan lights its directory column, and the other way round */
  var lobby = document.querySelector('body.lobby');
  if (lobby) {
    var scope = document.querySelectorAll('#plan [data-room], #directory [data-room]');
    var set = function (room, on) {
      Array.prototype.forEach.call(scope, function (el) {
        if (el.getAttribute('data-room') === room) el.classList.toggle('is-hot', on);
      });
    };
    Array.prototype.forEach.call(scope, function (el) {
      var r = el.getAttribute('data-room');
      el.addEventListener('mouseenter', function () { set(r, true); });
      el.addEventListener('mouseleave', function () { set(r, false); });
      el.addEventListener('focusin', function () { set(r, true); });
      el.addEventListener('focusout', function () { set(r, false); });
    });
  }

  /* room pages: fit the giant room word to one line and size the plate to the word */
  function fit() {
    var g = document.querySelector('.giant');
    if (!g) return;
    var l = g.firstElementChild, top = g.parentNode, cs = getComputedStyle(g);
    var avail = g.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    g.style.fontSize = '100px';
    var w = l.getBoundingClientRect().width;
    if (!w || !avail) return;
    g.style.fontSize = Math.min(100 * avail / w * 0.995, innerWidth * 0.30) + 'px';
    var p = top.querySelector('.plate');
    if (!p) return;
    if (innerWidth > 1100) {
      p.style.setProperty('--plate-w', Math.max(160, Math.min(380, innerWidth * 0.2)) + 'px');
      top.style.setProperty('--hang', Math.round(p.getBoundingClientRect().height * 0.5) + 'px');
    } else { p.style.removeProperty('--plate-w'); top.style.removeProperty('--hang'); }
  }
  if (document.querySelector('.giant')) {
    fit();
    window.addEventListener('resize', fit);
    window.addEventListener('load', fit);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  }

  /* room = a sheet opened out of the floor plan: backdrop click, Esc or the close button go back to the plan */
  if (document.getElementById('sheet')) {
    var plan = '../index.html#plan';
    document.addEventListener('click', function (e) {
      if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var t = e.target;
      if (!t.closest || t.closest('.sheet') || t.closest('.wf')) return;
      location.href = plan;
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || e.defaultPrevented || document.fullscreenElement) return;
      if (e.target.closest && e.target.closest('input,textarea,select')) return;
      location.href = plan;
    });
  }

  /* before / after sliders: a range input drives --pos */
  Array.prototype.forEach.call(document.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var upd = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', upd); upd();
  });
})();
"""

if __name__ == '__main__':
    main()


# style switcher (see add_switcher.py)
import runpy as _rp
import os as _os; _rp.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "add_switcher.py"), run_name="__main__")
