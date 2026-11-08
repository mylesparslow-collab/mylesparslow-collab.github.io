#!/usr/bin/env python3 -I
"""Mockup H, "Orbit": rebuild mockup-h/ from themed/live.json (stdlib only).

The homepage is a slowly turning dot globe ringed by five tilted orbits, one per room;
every project is a satellite. Writes mockup-h/index.html, mockup-h/<room>/index.html,
mockup-h/h.css and mockup-h/h.js. Run: python3 -I themed/render_h.py

The land mask (144 x 60 cells, 2.5 deg x 3 deg, rasterised from Natural Earth 1:110m land,
public domain) is bit-packed inline below; nothing is fetched at runtime.
"""
import html
import json
import os
import random
import re
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-h')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape

RING = {'legal': '#7aa2ff', 'business': '#5fd7a6', 'creative': '#ff8a5b', 'design': '#ffd166', 'research': '#c792ff'}

# 144 x 60 land mask, row 0 = 90N, col 0 = 180W; 1 bit per cell, MSB first
MASK = ('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH+B/4AAAAAAAAAAAAAAAAAADvj//+AD0AAAAcAAAAA'
        'AAABiL8P//8AAAAAMAD4AAAAAAADxLaAP/8AAAACAP/7YIAAAOAAHm/4P/wAAHAAG/////8Aw///9/5cH+AAA/8f+///////'
        'If////58HwHAD73////////+A////+BgDgAAPn////////64AEB//+B+AAACLn///////4CAAQAf//x/AAACHP///////gOA'
        'AAAH//5/wAALv////////4IAAAAH///6QAAA/////////0AAAAAD///+AAAB//X3/////gAAAAAD///wAAAF6+Dv/////EAA'
        'AAAD///AAAAPEu/3////cIAAAAAB//+AAAAPBB/z////kQAAAAAA//+AAAAH8AP/////BgAAAAAAX/4AAAAP/Ov/////iAAA'
        'AAAAP8EAAAAf///v////gAAAAAAAH4EAAAA///36////AAAAAAAAA4MAAAB///7/D/f8AAAAAAAAA4gQAAB///7+B8fAAAAA'
        'AAAAAPgAAAB///94B4PggAAAAAAAAA4AAAB////gAwHwQAAAAAAAAAI/AAA////wAwEgQAAAAAAAAAB/gAAf///wAIAAIAAA'
        'AAAAAAB/4AAAP//gAAKCAAAAAAAAAAD/8AAAD//AAADOAAAAAAAAAAD//AAAD/+AAADOhAAAAAAAAAH//4AAB/8AAABAA8AA'
        'AAAAAAD//8AAB/8AAAAYAeAAAAAAAAB//4AAB/8AAAAAAAAAAAAAAAB//wAAB/8QAAAADAAAAAAAAAAf/wAAB/8wAAAAfsAA'
        'AAAAAAAP/wAAB/wwAAAA/+AAAAAAAAAP/gAAA/xgAAAH//AAAAAAAAAP+AAAA/gAAAAD//gAAAAAAAAf8AAAAfgAAAAD//gA'
        'AAAAAAAf4AAAAfAAAAAD9/gAAAAAAAAfwAAAAAAAAAADAfAAAAAAAAAfgAAAAAAAAAAAAPAAAAAAAAA+AAAAAAAAAAAAAAAC'
        'AAAAAAAcAAAAAAAAAAAAACAIAAAAAAA4AAAAAAAAAAAAAAAQAAAAAAA4AAAAAAAAEAAAAAAAAAAAAAAwAAAAAAAAAAAAAAAA'
        'AAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAA'
        'AAAAAAAEAAAAAAAfAH///8AAAAAAAAAeAAAAN7//5/////+AAAAFAbyfAAA////////////wAAf////wAAf///////////+A'
        'AQ////+ADg////////////+AAB//////P//////////////A//f/////////////////////////////////////////////')


def esc(s):
    return html.escape(s, quote=True)


def text(s):
    return unesc(re.sub(r'<[^>]+>', '', s)).strip()


def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b):
    """Deepen relative paths one level (rooms sit in mockup-h/<room>/); open outbound links in a new tab."""
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


def code(r, it):
    n = int(it['count'].split('/')[0])
    return '%s-%02d' % (r['letter'], n)


for r in ROOMS:
    r['cases'] = [i for i in r['items'] if i['kind'] == 'case']
    r['n'] = len(r['cases'])
N_CASES = sum(r['n'] for r in ROOMS)

# ------------------------------------------------------------------ chrome
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&amp;family=Space+Mono&amp;display=swap">')
HOUSE = ('<svg class="ico" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">'
         '<path d="M2 7.2 8 2l6 5.2M3.6 6v7.5h3.2V9.6h2.4v3.9h3.2V6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/></svg>')


def topbar(up, current=None, home=False):
    chips = []
    for r in ROOMS:
        cur = r['slug'] == current
        href = (up + 'index.html') if cur else (up + r['slug'] + '/index.html')
        extra = ' aria-current="page" title="Back to Home"' if cur else ''
        chips.append('<a class="rc%s" style="--c:%s" href="%s"%s><i aria-hidden="true"></i><span class="rc__f">%s</span><span class="rc__a" aria-hidden="true">%s</span></a>'
                     % (' is-cur' if cur else '', RING[r['slug']], href, extra, r['short'], r['letter']))
    hc = ' aria-current="page"' if home else ''
    return ('<header class="bar"><nav class="bar__in" aria-label="Site">'
            '<a class="homebtn" href="%sindex.html"%s>%s<span>Home</span></a>'
            '<div class="bar__rooms">%s</div></nav></header>') % (up, hc, HOUSE, ''.join(chips))


def stars_bg():
    rnd = random.Random(1991)
    w, h = 1400, 1000
    dots = []
    for _ in range(44):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        o = rnd.choice([0.18, 0.25, 0.32, 0.45, 0.6])
        dots.append('<rect x="%.0f" y="%.0f" width="1" height="1" fill="#dfe6f2" fill-opacity="%.2f"/>' % (x, y, o))
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">%s</svg>' % (w, h, ''.join(dots))
    return 'url("data:image/svg+xml,%s")' % urllib.parse.quote(svg, safe=' =:/"-.,')


def shell(title, desc, up, inner, body_attr='', head_extra=''):
    return ('<!doctype html>\n<html lang="en" class="nojs">\n<head>\n<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark">'
            '<meta name="theme-color" content="#060a18">\n<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n%s\n<link rel="stylesheet" href="%sh.css">\n'
            '<script>document.documentElement.className="js"</script>\n%s</head>\n<body%s>\n'
            '<a class="skip" href="#main">Skip to content</a>\n%s\n<script src="%sh.js"></script>\n</body>\n</html>\n') % (
        esc(title), esc(desc), up, FONTS, up, head_extra, body_attr, inner, up)


# ------------------------------------------------------------------ home
def tools_section():
    t = HOME['tools_html']
    eyebrow = re.search(r'<p class="eyebrow">(.*?)</p>', t).group(1)
    title = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', t, re.S).group(1)
    lede = re.search(r'<p class="sec-lede">(.*?)</p>', t, re.S).group(1)
    rows = re.findall(r'<article class="trow">(.*?)</article>', t, re.S)
    trs = []
    for row in rows:
        name = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        cells = re.findall(r'<span class="lab">(.*?)</span>\s*<p>(.*?)</p>', row, re.S)
        tds = ''.join('<td><span class="lab">%s</span>%s</td>' % (lab, p) for lab, p in cells[:2])
        if len(cells) < 2:
            tds += '<td></td>'
        trs.append('<tr><th scope="row">%s</th>%s</tr>' % (name, tds))
    head = '<thead><tr><th scope="col">Project</th><th scope="col">Built with</th><th scope="col">Runs on</th></tr></thead>'
    cut = 12
    return ('''<section class="sec tools" id="tools" aria-labelledby="h-tools">
<p class="eyebrow">%s</p>
<h2 id="h-tools" class="sec__t">%s</h2>
<p class="sec__lede">%s</p>
<div class="tbl"><table>%s<tbody>%s</tbody></table></div>
<details class="more"><summary>Show the other %d projects</summary><div class="tbl"><table>%s<tbody>%s</tbody></table></div></details>
</section>''' % (eyebrow, title, lede, head, ''.join(trs[:cut]), len(trs) - cut, head, ''.join(trs[cut:])))


def rules_section():
    t = HOME['rules_html']
    eyebrow = re.search(r'<p class="eyebrow">(.*?)</p>', t).group(1)
    title = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', t, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', t, re.S)
    lis = ''.join('<li><span class="mono">%s</span><h3>%s</h3><p>%s</p></li>' % r for r in rules)
    return ('<section class="sec rules" id="rules" aria-labelledby="h-rules"><p class="eyebrow">%s</p>'
            '<h2 id="h-rules" class="sec__t">%s</h2><ol class="rules__l">%s</ol></section>') % (eyebrow, title, lis)


def mission_log():
    out = []
    for r in ROOMS:
        lis = []
        for it in r['cases']:
            lis.append('<li><a href="%s/index.html#%s" data-sat="%s" data-room="%s"><span class="lc mono">%s</span>'
                       '<span class="lt">%s</span><span class="ls">%s</span></a></li>'
                       % (r['slug'], it['id'], it['id'], r['slug'], code(r, it), it['title'], it['sub']))
        out.append('''<section class="lg" id="log-%s" style="--c:%s" aria-labelledby="lh-%s">
<div class="lg__h"><h3 id="lh-%s"><a href="%s/index.html"><i aria-hidden="true"></i>%s</a></h3><p class="lg__n">%s &middot; %s</p></div>
<p class="lg__lede">%s</p>
<ol class="lg__l">%s</ol>
</section>''' % (r['slug'], RING[r['slug']], r['slug'], r['slug'], r['slug'], r['title'], r['eyebrow'], r['count'], r['lede'], ''.join(lis)))
    return '\n'.join(out)


def home_page():
    h = HOME['hero_html']
    count = re.search(r'hero__count">(.*?)</span>', h).group(1)
    count = re.sub(r'^\d+', str(N_CASES), count)
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', h, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', h, re.S)
    foot = HOME['foot_html']
    mail = re.search(r'href="mailto:([^"]+)"', foot).group(1)
    gh = re.search(r'<a href="(https://github.com/[^"]*)">GitHub</a>', foot).group(1)
    lp = re.search(r'<a href="([^"]*)">Legal portfolio</a>', foot).group(1)
    sign = re.search(r'<span>([^<]*Made with AI)</span>', foot).group(1)
    labels = ''.join('<button type="button" class="olab" data-room="%s" style="--c:%s" aria-expanded="false" aria-controls="opanel" '
                     'aria-label="%s orbit, %d projects: focus it"><i aria-hidden="true"></i>%s <span class="mono">%d</span></button>'
                     % (r['slug'], RING[r['slug']], esc(r['short']), r['n'], r['short'], r['n']) for r in ROOMS)
    readouts = ''.join('<div><dd data-fit="shrink"><span>%s</span></dd><dt>%s</dt></div>' % (dd, dt) for dt, dd in stats)
    inner = f'''{topbar('', home=True)}
<main id="main">
<div class="sys" id="top">
<div class="sys__text">
<header class="hero">
<h1><span class="hero__name">Myles Parslow</span> <span class="hero__tag">makes things with AI.</span></h1>
<p class="hero__count mono">{count}</p>
<p class="hero__lede">{lede}</p>
<dl class="readouts">{readouts}</dl>
</header>
<section class="log" id="log" aria-labelledby="h-log">
<div class="log__h"><h2 id="h-log" class="sec__t">Mission log</h2><p>All {N_CASES} satellites, orbit by orbit. Each one opens its file in that room.</p></div>
{mission_log()}
</section>
</div>
<div class="sys__stage">
<div class="stage" id="stage">
<div class="sky">
<canvas aria-hidden="true"></canvas>
<div class="olabs">{labels}</div>
<div class="tip" id="tip" aria-hidden="true" hidden><b></b><span></span><em class="mono"></em></div>
<p class="stage__hint mono" aria-hidden="true">drag to turn &middot; click a ring&rsquo;s name</p>
</div>
<aside class="opanel" id="opanel" hidden aria-labelledby="op-t">
<button type="button" class="opanel__x" aria-label="Close and show all orbits">&times;</button>
<p class="opanel__m mono"></p>
<h2 id="op-t" class="opanel__t"></h2>
<ol class="opanel__l"></ol>
<a class="opanel__go" href="#">Enter room &rarr;</a>
</aside>
</div>
</div>
</div>
{rules_section()}
{tools_section()}
<section class="sec archive" id="archive" aria-label="Style archive">
<p class="archive__now mono">You&rsquo;re looking at: Orbit</p>
<p><b>Style archive.</b> This site is also a running design experiment. Each version renders the same {N_CASES} case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. <a href="../styles/index.html"><b>See every version &rarr;</b></a></p>
</section>
<footer class="sec foot" id="contact">
<h2 class="sec__t">Say hello.</h2>
<p class="foot__mail"><a href="mailto:{mail}">{mail}</a> <button type="button" class="copy" data-copy="{mail}">Copy</button></p>
<p class="foot__row"><a href="{gh}" target="_blank" rel="noopener">GitHub</a><a href="{lp}" target="_blank" rel="noopener">Legal portfolio</a><a href="#top">Back to top &uarr;</a><span>{sign}</span></p>
</footer>
</main>'''
    redirect = '<script>(function(){var M=%s,h=location.hash.slice(1);if(M.hasOwnProperty(h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    desc = 'Myles Parslow makes things with AI: %d case studies in five rooms, drawn as a small planetary system.' % N_CASES
    return shell('Myles Parslow', desc, '', inner, ' class="home"', redirect)


# ------------------------------------------------------------------ rooms
def room_page(i, r):
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    nxt_html = (('<a class="next" href="../%s/index.html" style="--c:%s"><span class="mono">Next orbit &rarr;</span><b>%s</b></a>' % (nxt['slug'], RING[nxt['slug']], nxt['title']))
                if nxt else '<a class="next" href="../index.html"><span class="mono">Next orbit &rarr;</span><b>Home</b></a>')
    chips = ''.join('<a href="#%s" data-sat="%s"><span class="mono">%s</span>%s</a>' % (c['id'], c['id'], code(r, c), c['title']) for c in r['cases'])
    parts = []
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            parts.append('<div class="divider">%s</div>' % fix_body(it['html']))
        elif k == 'extra':
            parts.append(fix_body(it['html']))
        else:
            ks = ''.join('<li>%s</li>' % k for k in it['kickers'] if k)
            parts.append('''<article class="sat" id="%s" aria-labelledby="t-%s">
<div class="sat__h">
<p class="sat__c"><span class="mono">%s</span><span class="sat__ct">%s</span></p>
<h2 id="t-%s">%s</h2>
<p class="sat__sub">%s</p>
<ul class="sat__k">%s</ul>
<p class="sat__lede">%s</p>
</div>
<div class="cbody">
%s
</div>
</article>''' % (it['id'], it['id'], code(r, it), it['count'], it['id'], it['title'], it['sub'], ks, it['lede'], fix_body(it['body_html'])))
    inner = f'''{topbar('../', current=r['slug'])}
<main id="main">
<header class="rhead" id="top">
<p class="rhead__m">{r['eyebrow']} &middot; {r['count']}</p>
<div class="mini" id="mini" aria-hidden="true"><canvas></canvas></div>
<h1 class="rname" data-fit="fill" data-max="248" data-min="24"><span>{r['title']}</span></h1>
<p class="rhead__lede">{r['lede']}</p>
<nav class="chips" aria-label="Satellites in this room">{chips}</nav>
</header>
{chr(10).join(parts)}
<nav class="nextnav" aria-label="Next room">{nxt_html}</nav>
</main>'''
    desc = text(r['lede'])
    return shell('%s · Myles Parslow' % unesc(r['title']), desc, '../', inner,
                 ' class="room" data-room="%s" data-home="../index.html" style="--ring:%s"' % (r['slug'], RING[r['slug']]))


# ------------------------------------------------------------------ static files
CSS = r'''@charset "utf-8";
:root{--bg:#060a18;--fg:#dfe6f2;--mut:#98a4bd;--dim:#6f7b95;--line:#24304d;--panel:#0a1124;--ring:#dfe6f2;
--legal:#7aa2ff;--business:#5fd7a6;--creative:#ff8a5b;--design:#ffd166;--research:#c792ff;
--sans:"Space Grotesk",ui-sans-serif,system-ui,sans-serif;--mono:"Space Mono",ui-monospace,Menlo,monospace;--bar:56px;--gut:clamp(16px,3.4vw,56px);color-scheme:dark}
*,*::before,*::after{box-sizing:border-box}
html{background:var(--bg);color:var(--fg);-webkit-text-size-adjust:100%;scroll-padding-top:calc(var(--bar) + 20px)}
body{margin:0;background:var(--bg) %STARS% repeat;color:var(--fg);font:400 17px/1.6 var(--sans);overflow-x:hidden;overflow-wrap:break-word}
a{color:inherit}
h1,h2,h3,h4,p,ol,ul,dl,dd,figure{margin:0}
.mono{font-family:var(--mono);font-size:.78em;letter-spacing:0}
:focus-visible{outline:2px solid #fff;outline-offset:3px;border-radius:4px}
.skip{position:absolute;left:-999px;top:8px;z-index:50;background:var(--fg);color:var(--bg);padding:8px 12px;border-radius:6px}
.skip:focus{left:12px}
::selection{background:#2e4aa8;color:#fff}

/* bar */
.bar{position:fixed;top:0;left:0;right:0;z-index:20;height:var(--bar);background:#060a18;border-bottom:1px solid var(--line)}
.bar__in{height:100%;display:flex;align-items:center;gap:10px;padding:0 var(--gut);max-width:1840px;margin:0 auto}
.homebtn{display:inline-flex;align-items:center;gap:7px;height:34px;padding:0 13px 0 11px;border:1px solid var(--line);border-radius:99px;text-decoration:none;font-weight:500;font-size:15px;flex:none}
.homebtn:hover,.homebtn[aria-current]{border-color:var(--fg)}
.ico{display:block}
.bar__rooms{display:flex;gap:6px;margin-left:auto;min-width:0}
.rc{display:inline-flex;align-items:center;gap:7px;height:34px;padding:0 12px;border:1px solid color-mix(in srgb,var(--c) 55%,transparent);border-radius:99px;text-decoration:none;font-size:14px;font-weight:500;color:var(--fg);white-space:nowrap}
.rc i{width:7px;height:7px;border-radius:50%;background:var(--c);flex:none}
.rc:hover{border-color:var(--c)}
.rc.is-cur{background:var(--c);border-color:var(--c);color:#060a18}
.rc.is-cur i{background:#060a18}
.rc__a{display:none}
@media(max-width:700px){.rc__f{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}.rc__a{display:inline}.rc{padding:0 10px;gap:6px}.bar__rooms{gap:5px}}
@media(max-width:360px){.rc i{display:none}.rc{padding:0 9px}}
main{padding-top:var(--bar)}

/* home: system */
.sys{display:grid;grid-template-columns:minmax(0,1fr);max-width:1840px;margin:0 auto}
.sys__stage{order:-1;padding:12px var(--gut) 0}
.stage{position:relative;width:100%;user-select:none;-webkit-user-select:none}
.sky{position:relative;width:100%;height:min(86vw,640px);touch-action:pan-y}
.stage canvas{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:grab}
.stage.is-drag canvas{cursor:grabbing}.stage.is-hot canvas{cursor:pointer}
.nojs .stage{display:none}
.olabs{position:absolute;inset:0;pointer-events:none}
.olab{position:absolute;left:0;top:0;pointer-events:auto;display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 10px;border-radius:99px;border:1px solid color-mix(in srgb,var(--c) 60%,transparent);background:#070c1e;color:var(--fg);font:500 13px/1 var(--sans);white-space:nowrap;cursor:pointer;transition:opacity .3s,border-color .2s;will-change:transform}
.olab i{width:7px;height:7px;border-radius:50%;background:var(--c)}
.olab .mono{color:var(--mut);font-size:11px}
.olab:hover,.olab[aria-expanded=true]{border-color:var(--c)}
.olab[aria-expanded=true]{background:var(--c);color:#060a18}.olab[aria-expanded=true] .mono{color:#060a18}.olab[aria-expanded=true] i{background:#060a18}
.stage.is-focus .olab[aria-expanded=false]{opacity:.55}
.tip{position:absolute;left:0;top:0;z-index:3;pointer-events:none;max-width:240px;padding:8px 11px;border:1px solid var(--c,var(--line));border-radius:8px;background:#070c1e;display:grid;gap:1px;font-size:14px;line-height:1.3}
.tip[hidden]{display:none}
.tip b{font-weight:700}.tip span{color:var(--mut)}.tip em{font-style:normal;color:var(--c);font-size:11px;margin-top:3px}
.stage__hint{position:absolute;left:0;bottom:4px;color:var(--dim);font-size:11px;background:var(--bg);padding:2px 6px 2px 0}
.nojs .stage__hint{display:none}
.opanel{position:relative;z-index:4;margin:8px 0 0;padding:18px 18px 16px;border:1px solid var(--c,var(--line));border-radius:12px;background:var(--panel);display:grid;gap:8px}
.opanel[hidden]{display:none}
.stage.is-wide .opanel{position:absolute;left:0;top:16px;max-height:calc(100% - 56px);margin:0;width:var(--pw,300px);grid-template-rows:auto auto auto minmax(0,1fr) auto}
.opanel__x{position:absolute;top:8px;right:8px;width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:transparent;color:var(--fg);font-size:20px;line-height:1;cursor:pointer}
.opanel__x:hover{border-color:var(--fg)}
.opanel__m{color:var(--c);font-size:11px}
.opanel__t{font-size:28px;line-height:1.05;font-weight:700;padding-right:36px}
.opanel__l{list-style:none;padding:0;overflow:auto;display:grid;align-content:start;gap:0;margin:4px -6px 0}
.opanel__l a{display:grid;grid-template-columns:44px minmax(0,1fr);column-gap:8px;padding:6px;border-radius:6px;text-decoration:none;line-height:1.25}
.opanel__l a:hover,.opanel__l a:focus-visible{background:#111a36}
.opanel__l .lc{color:var(--c);font-size:11px;padding-top:3px}.opanel__l .lt{font-weight:500}.opanel__l .ls{grid-column:2;color:var(--mut);font-size:13px}
.opanel__go{justify-self:start;display:inline-flex;align-items:center;height:38px;padding:0 16px;border-radius:99px;background:var(--c);color:#060a18;font-weight:700;text-decoration:none}

/* hero */
.sys__text{padding:0 var(--gut);min-width:0}
.hero{padding:28px 0 56px;display:grid;gap:18px;max-width:720px}
.hero h1{display:grid;gap:10px;font-weight:700}
.hero__name{font-size:clamp(52px,7.4vw,128px);line-height:.94;letter-spacing:-.035em}
.hero__tag{font-size:clamp(22px,2.3vw,36px);line-height:1.15;font-weight:400;color:var(--mut);letter-spacing:-.01em}
.hero__count{color:var(--mut);margin-top:6px}
.hero__lede{font-size:clamp(17px,1.25vw,20px);max-width:36em}
.readouts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:8px}
.readouts div{display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--line);padding-top:12px;min-width:0}
.readouts dd{font-size:clamp(28px,3vw,44px);font-weight:500;line-height:1;letter-spacing:-.02em;white-space:nowrap;font-variant-numeric:tabular-nums}
.readouts dt{color:var(--mut);font-size:14px;line-height:1.35}
[data-fit]{white-space:nowrap;overflow:hidden}
[data-fit]>span{display:inline-block}

/* mission log */
.log{padding:8px 0 72px;display:grid;gap:44px}
.log__h{display:grid;gap:6px}.log__h p{color:var(--mut)}
.sec__t{font-size:clamp(30px,3.2vw,48px);line-height:1.05;font-weight:700;letter-spacing:-.02em}
.lg{display:grid;gap:10px}
.lg__h{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:4px 16px;border-bottom:1px solid var(--c);padding-bottom:8px}
.lg__h h3{font-size:24px;font-weight:700;line-height:1.1}
.lg__h a{text-decoration:none;display:inline-flex;align-items:center;gap:10px}
.lg__h a:hover{color:var(--c)}
.lg__h i{width:10px;height:10px;border-radius:50%;background:var(--c);box-shadow:0 0 0 4px color-mix(in srgb,var(--c) 22%,transparent)}
.lg__n{color:var(--mut);font-size:14px}
.lg__lede{color:var(--mut);font-size:15px;max-width:44em}
.lg__l{list-style:none;padding:0;display:grid}
.lg__l a{display:grid;grid-template-columns:52px minmax(0,auto) minmax(0,1fr);column-gap:12px;align-items:baseline;padding:9px 8px;margin:0 -8px;border-radius:6px;text-decoration:none;border-bottom:1px solid #121a33}
.lg__l a:hover,.lg__l a:focus-visible,.lg__l a.is-hl{background:#0d1530}
.lg__l .lc{color:var(--c);font-size:11.5px}
.lg__l .lt{font-weight:500}
.lg__l .ls{color:var(--mut);font-size:14px}
@media(max-width:560px){.lg__l a{grid-template-columns:48px minmax(0,1fr)}.lg__l .ls{grid-column:2}}

/* sections */
.sec{max-width:1840px;margin:0 auto;padding:72px var(--gut) 0}
.eyebrow{color:var(--mut);font-size:15px;margin-bottom:8px}
.sec__lede{color:var(--mut);max-width:44em;margin-top:12px}
.rules__l{list-style:none;padding:0;margin-top:28px;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}
.rules__l li{border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:10px;align-content:start;background:rgba(10,17,36,.7)}
.rules__l .mono{color:var(--legal)}
.rules__l li:nth-child(2) .mono{color:var(--business)}.rules__l li:nth-child(3) .mono{color:var(--creative)}
.rules__l h3{font-size:21px;line-height:1.2;font-weight:700}
.rules__l p{color:var(--mut)}
.tbl{margin-top:28px;overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:rgba(10,17,36,.7)}
table{width:100%;border-collapse:collapse;font-size:15px;line-height:1.5}
th,td{text-align:left;vertical-align:top;padding:12px 16px;border-bottom:1px solid var(--line)}
tbody tr:last-child>*{border-bottom:0}
thead th{font-weight:500;color:var(--mut);font-size:13px}
tbody th{font-weight:700;width:22%}
td{width:39%}
td .lab{display:none}
.more{margin-top:14px}
.more summary{cursor:pointer;display:inline-flex;align-items:center;height:38px;padding:0 16px;border:1px solid var(--line);border-radius:99px;font-weight:500}
.more summary:hover{border-color:var(--fg)}
.more[open] summary{margin-bottom:0}
@media(max-width:700px){thead{display:none}table,tbody,tr,th,td{display:block;width:auto}tr{padding:12px 16px;border-bottom:1px solid var(--line)}th,td{padding:0;border:0}tbody th{margin-bottom:6px}td{margin-top:6px}td .lab{display:block;color:var(--mut);font-size:12px}}
.archive{display:grid;gap:8px}
.archive p{max-width:46em;font-size:18px}
.archive__now{color:var(--design);font-family:var(--sans);font-size:15px;font-weight:500}
.archive a{color:var(--design)}
.foot{padding-bottom:64px;display:grid;gap:16px}
.foot__mail{display:flex;flex-wrap:wrap;align-items:center;gap:12px;font-size:clamp(22px,3vw,40px);font-weight:500;user-select:text}
.foot__mail a{text-decoration-thickness:1px;text-underline-offset:.18em;overflow-wrap:anywhere}
.copy{height:34px;padding:0 14px;border:1px solid var(--line);border-radius:99px;background:transparent;color:var(--fg);font:500 14px/1 var(--sans);cursor:pointer}
.copy:hover{border-color:var(--fg)}
.foot__row{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--mut)}
.foot__row a{color:var(--fg)}

@media(min-width:1024px){
.sys{grid-template-columns:minmax(0,5fr) minmax(0,6fr)}
.sys__stage{order:0;padding:0 var(--gut) 0 0}
.stage{position:sticky;top:calc(var(--bar) + 8px);height:calc(100vh - var(--bar) - 16px);min-height:560px}
.sky{height:100%}
.hero{padding-top:clamp(40px,8vh,96px);min-height:calc(100vh - var(--bar));align-content:center}
}

/* room pages */
.room{--c:var(--ring)}
.rhead{max-width:1840px;margin:0 auto;padding:24px var(--gut) 40px;display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:clamp(16px,3vw,48px);row-gap:16px;align-items:end;border-bottom:1px solid var(--line)}
.rhead>*{grid-column:1/-1}
.rhead__m{grid-column:1;grid-row:1;color:var(--mut);align-self:center}
.mini{grid-column:2;grid-row:1;width:clamp(120px,15vw,240px);aspect-ratio:1;position:relative}
@media(min-width:700px){.rhead .rname{grid-column:1;grid-row:2}.mini{grid-row:1/3;align-self:end}.rhead__m{align-self:start;padding-top:12px}}
.mini canvas{position:absolute;inset:0;width:100%;height:100%}
.rname{font-size:120px;line-height:1.1;font-weight:700;letter-spacing:-.04em;padding:.09em 0 .06em}
.rhead__lede{max-width:44em;font-size:clamp(17px,1.4vw,21px)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.chips a{display:inline-flex;align-items:center;gap:8px;min-height:34px;padding:4px 13px;border:1px solid color-mix(in srgb,var(--ring) 45%,transparent);border-radius:99px;text-decoration:none;font-size:14px;font-weight:500;line-height:1.2}
.chips a:hover{border-color:var(--ring)}
.chips .mono{color:var(--ring);font-size:11px;white-space:nowrap}
.sat,.divider,.xsec,.nextnav{max-width:1840px;margin:0 auto;padding-left:var(--gut);padding-right:var(--gut)}
.sat{padding-top:72px;padding-bottom:16px;scroll-margin-top:calc(var(--bar) + 12px)}
.sat>*{position:relative;border-left:1px solid color-mix(in srgb,var(--ring) 70%,transparent);padding-left:clamp(18px,2.6vw,40px)}
.sat__h{display:grid;gap:8px;padding-bottom:28px}
.sat__h::before{content:"";position:absolute;left:-5px;top:4px;width:9px;height:9px;border-radius:50%;background:var(--ring);box-shadow:0 0 0 5px color-mix(in srgb,var(--ring) 18%,transparent)}
.sat__c{display:flex;gap:12px;align-items:baseline;color:var(--ring);line-height:1}
.sat__ct{color:var(--dim);font-size:13px}
.sat h2{font-size:clamp(34px,4.6vw,72px);line-height:1;font-weight:700;letter-spacing:-.03em}
.sat__sub{font-size:clamp(18px,1.6vw,24px);color:var(--mut)}
.sat__k{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.sat__k li{font-size:13px;padding:3px 10px;border:1px solid var(--line);border-radius:99px;color:var(--mut)}
.sat__lede{font-size:clamp(18px,1.5vw,22px);max-width:40em;margin-top:6px}
.cbody{display:grid;gap:28px;padding-bottom:28px;min-width:0}
.cbody>*{min-width:0}
.cbody p,.cbody li{max-width:44em}
.cbody h3{font-size:22px;line-height:1.2;font-weight:700;margin-bottom:8px}
.cbody h4{font-size:17px;font-weight:700;margin-bottom:4px}
.cbody p+p,.cbody p+ul,.cbody ul+p,.cbody p+ol{margin-top:10px}
.cbody ul,.cbody ol{padding-left:1.2em}
.cbody li+li{margin-top:4px}
.cbody .block{display:block}
.cbody *+h3,.cbody *+h4{margin-top:22px}
.cbody figure>figcaption{margin-top:0}
.cbody .cols{display:grid;grid-template-columns:minmax(0,1fr);gap:28px;align-items:start}
@media(min-width:900px){.cbody .cols{grid-template-columns:repeat(2,minmax(0,1fr));gap:28px 48px}}
.cbody .made{border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:rgba(10,17,36,.75);max-width:52em}
.cbody .made b{display:block;color:var(--ring);font-weight:500;font-size:14px;margin-bottom:4px}
.cbody .note{color:var(--mut);font-size:15px}
.cbody .links{display:flex;flex-wrap:wrap;gap:8px;max-width:none}
.cbody .links a{display:inline-flex;align-items:center;min-height:38px;padding:6px 16px;border:1px solid var(--ring);border-radius:99px;color:var(--ring);text-decoration:none;font-weight:500;font-size:15px;line-height:1.2}
.cbody .links a:hover{background:color-mix(in srgb,var(--ring) 14%,transparent)}
.cbody .links span{color:var(--mut);align-self:center;font-size:14px}
.cbody figure{display:grid;gap:8px;align-content:start;min-width:0}
.cbody img,.cbody video{display:block;max-width:100%;height:auto;border:1px solid #24304d;border-radius:8px;background:#0a1124}
.cbody figure>img,.cbody figure>a>img,.cbody figure>video{width:100%}
.cbody figure>a{display:block;border-radius:8px}
.cbody .portrait,.cbody figure>img.portrait,.cbody figure>video.portrait{width:auto;max-width:min(100%,360px)}
.cbody figcaption{color:var(--mut);font-size:14px;line-height:1.45;max-width:44em}
.cbody .wide{max-width:1280px}
.cbody .shots,.cbody .grid3,.cbody .gallery,.cbody .reels{display:grid;gap:20px;align-items:start;grid-template-columns:minmax(0,1fr)}
@media(min-width:700px){.cbody .shots,.cbody .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}.cbody .grid3{grid-template-columns:repeat(2,minmax(0,1fr))}.cbody .reels{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(min-width:1100px){.cbody .grid3{grid-template-columns:repeat(3,minmax(0,1fr))}.cbody .gallery{grid-template-columns:repeat(4,minmax(0,1fr))}.cbody .reels{grid-template-columns:repeat(6,minmax(0,1fr))}.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr));max-width:760px}}
.cbody .grid3>div{border-top:1px solid var(--line);padding-top:12px}
.cbody .reels video,.cbody .reels figure>video.portrait{width:100%;max-width:100%;aspect-ratio:9/16;object-fit:cover}
.cbody .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;max-width:1280px}
.cbody .stats>div{border:1px solid var(--line);border-radius:10px;background:rgba(10,17,36,.75);padding:16px;display:flex;flex-direction:column;gap:8px;min-width:0}
.cbody .stats dd{order:-1;font-size:clamp(26px,2.6vw,38px);line-height:1;font-weight:500;letter-spacing:-.02em;font-variant-numeric:tabular-nums;color:var(--fg)}
.cbody .stats dt{color:var(--mut);font-size:14px;line-height:1.35}
.cbody .flow{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;counter-reset:st;max-width:none}
.cbody .flow li{counter-increment:st;display:grid;gap:6px;align-content:start;border-top:1px solid var(--ring);padding-top:10px;margin:0}
.cbody .flow b::before{content:counter(st,decimal-leading-zero) "  ";font-family:var(--mono);font-size:11px;color:var(--ring)}
.cbody .flow span{color:var(--mut);font-size:15px}
.cbody .tags{display:flex;flex-wrap:wrap;gap:6px}
.cbody .tag{font-size:13px;padding:3px 10px;border:1px solid var(--line);border-radius:99px;color:var(--mut)}
.cbody .tag.hot{border-color:var(--ring);color:var(--ring)}
.cbody .facts{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--mut)}
.cbody .facts strong{color:var(--fg);font-size:22px;font-weight:500;margin-right:4px;white-space:nowrap}
.cbody .piece{display:grid;gap:20px;grid-template-columns:minmax(0,1fr)}
.cbody .piece-text{display:grid;gap:12px;align-content:start}
@media(min-width:900px){.cbody .piece{grid-template-columns:minmax(0,1.2fr) minmax(0,1fr)}}
.cbody .books{display:grid;gap:20px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.cbody .book{border:1px solid var(--line);border-radius:10px;padding:16px;display:grid;gap:8px;align-content:start}
.cbody .book.lead{grid-column:1/-1;grid-template-columns:minmax(0,1fr)}
@media(min-width:700px){.cbody .book.lead{grid-template-columns:200px minmax(0,1fr);gap:24px}}
.cbody .book .cover{width:100%;max-width:200px}
.cbody .lead-text{display:grid;gap:8px;align-content:start}
.cbody .kind{color:var(--ring);font-size:13px}
.cbody .book .count{color:var(--dim);font-size:13px}
.cbody .logline{font-style:italic;font-size:18px}
.cbody .sub-case{border:1px solid var(--line);border-radius:12px;padding:20px;display:grid;gap:12px}
.cbody .eyebrow{color:var(--ring)}
.cbody .compare-fig{max-width:1280px}
.cbody .compare{position:relative;overflow:hidden;width:100%;max-width:100%;border-radius:8px;border:1px solid #24304d;--pos:50%;touch-action:pan-y;background:#0a1124}
.cbody .compare.portrait{max-width:360px}
.cbody .compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border:0;border-radius:0;max-width:none}
.cbody .compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cbody .cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:2px;margin-left:-1px;background:#dfe6f2;pointer-events:none}
.cbody .cmp-line::after{content:"\2194";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:38px;height:38px;border-radius:50%;background:#dfe6f2;color:#060a18;display:grid;place-items:center;font:700 17px/1 var(--sans)}
.cbody .cmp-tag{position:absolute;top:10px;font:500 12px/1 var(--sans);background:#060a18;color:#dfe6f2;padding:6px 9px;border-radius:99px;pointer-events:none}
.cbody .cmp-tag.l{left:10px}.cbody .cmp-tag.r{right:10px}
.cbody .compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.cbody .compare:focus-within{outline:2px solid #fff;outline-offset:3px}
.divider{padding-top:96px;scroll-margin-top:var(--bar)}
.divider .gdiv{border-top:1px solid var(--ring);padding-top:20px;display:grid;gap:8px;scroll-margin-top:calc(var(--bar) + 12px)}
.divider .gdiv__t{font-size:clamp(28px,3.4vw,52px);line-height:1.05;font-weight:700;letter-spacing:-.02em}
.divider .gdiv__p{color:var(--mut);max-width:44em;font-size:18px}
.divider+.sat{padding-top:48px}
.xsec{padding-top:96px;padding-bottom:24px;scroll-margin-top:calc(var(--bar) + 12px)}
.xsec__h{border-top:1px solid var(--ring);padding-top:20px;display:grid;gap:4px;margin-bottom:24px}
.xsec .eyebrow{color:var(--ring)}
.xsec__t{font-size:clamp(28px,3.4vw,52px);line-height:1.05;font-weight:700;letter-spacing:-.02em}
.xsec__list{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.xsec__list>div{border:1px solid var(--line);border-radius:10px;padding:16px;display:grid;gap:6px;align-content:start}
.xsec__list h3{font-size:19px;font-weight:700;line-height:1.2}
.xsec__list p{color:var(--mut);font-size:15px}
.nextnav{padding-top:96px;padding-bottom:80px}
.next{display:grid;gap:6px;text-decoration:none;border-top:1px solid var(--c,var(--fg));padding-top:20px}
.next .mono{color:var(--c,var(--fg));font-size:13px}
.next b{font-size:clamp(36px,6vw,96px);line-height:1;letter-spacing:-.03em}
.next:hover b{color:var(--c,var(--fg))}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
'''

JS = r'''/* Mockup H "Orbit": fitted type, compare sliders, Esc to Home, and the orbit system (canvas 2D). */
(function () {
  'use strict';
  var D = document, B = D.body, W = window;
  var RM = W.matchMedia && W.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ROOMS = ['legal', 'business', 'creative', 'design', 'research'];
  var COL = { legal: [122, 162, 255], business: [95, 215, 166], creative: [255, 138, 91], design: [255, 209, 102], research: [199, 146, 255] };
  var LET = { legal: 'Legal', business: 'Business', creative: 'Creative', design: 'Design', research: 'Research' };

  /* ---------- fitted type: one line, never wraps, never overflows */
  function fit(el) {
    var s = el.firstElementChild;
    if (!s || s.tagName !== 'SPAN') { s = D.createElement('span'); while (el.firstChild) s.appendChild(el.firstChild); el.appendChild(s); }
    el.style.fontSize = '';
    var w = el.clientWidth; if (!w) return;
    var base = parseFloat(getComputedStyle(el).fontSize), cur = base;
    var max = +el.getAttribute('data-max') || base, min = +el.getAttribute('data-min') || 10, fill = el.getAttribute('data-fit') === 'fill';
    for (var i = 0; i < 4; i++) {
      var sw = s.getBoundingClientRect().width; if (!sw) return;
      var nx = cur * (w - 2) / sw;
      if (!fill) nx = Math.min(nx, base);
      nx = Math.max(min, Math.min(fill ? max : base, nx));
      if (Math.abs(nx - cur) < 0.25 && sw <= w) break;
      cur = Math.floor(nx * 4) / 4; el.style.fontSize = cur + 'px';
    }
  }
  var fits = [];
  function fitAll() { fits = D.querySelectorAll('[data-fit]'); for (var i = 0; i < fits.length; i++) fit(fits[i]); }
  Array.prototype.forEach.call(D.querySelectorAll('.cbody .stats dd'), function (d) { d.setAttribute('data-fit', 'shrink'); d.setAttribute('data-min', '14'); });
  fitAll();
  if (D.fonts && D.fonts.ready) D.fonts.ready.then(fitAll);
  var rz = 0; W.addEventListener('resize', function () { cancelAnimationFrame(rz); rz = requestAnimationFrame(fitAll); });

  /* ---------- before / after sliders */
  Array.prototype.forEach.call(D.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input'); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* ---------- copy email */
  Array.prototype.forEach.call(D.querySelectorAll('.copy'), function (b) {
    b.addEventListener('click', function () {
      var v = b.getAttribute('data-copy');
      var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(v).then(done, function () {});
    });
  });

  /* ---------- Esc on room pages returns Home */
  if (B.getAttribute('data-home')) D.addEventListener('keydown', function (e) {
    var t = e.target;
    if (e.key === 'Escape' && !(t.closest && t.closest('input,textarea,select,video'))) location.href = B.getAttribute('data-home');
  });

  /* ---------- land mask */
  var MW = 144, MH = 60, GRID = (function () {
    var s = atob('%MASK%'), g = new Uint8Array(MW * MH);
    for (var i = 0; i < MW * MH; i++) g[i] = (s.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1;
    return g;
  })();
  function land(lon, lat) {
    var fx = ((((lon + 180) / 2.5) % MW) + MW) % MW - 0.5, fy = (90 - lat) / 3 - 0.5;
    var x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0;
    function g(x, y) { y = y < 0 ? 0 : y > MH - 1 ? MH - 1 : y; return GRID[y * MW + (((x % MW) + MW) % MW)]; }
    return (g(x0, y0) * (1 - tx) + g(x0 + 1, y0) * tx) * (1 - ty) + (g(x0, y0 + 1) * (1 - tx) + g(x0 + 1, y0 + 1) * tx) * ty;
  }

  /* ---------- 3x3 helpers (row-major) */
  function mul(a, b) {
    var o = new Array(9);
    for (var r = 0; r < 3; r++) for (var c = 0; c < 3; c++) o[r * 3 + c] = a[r * 3] * b[c] + a[r * 3 + 1] * b[3 + c] + a[r * 3 + 2] * b[6 + c];
    return o;
  }
  function view(yaw, pitch) {
    var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    return [cy, 0, sy, sp * sy, cp, -sp * cy, -cp * sy, sp, cp * cy];
  }
  function rotY(a) { var c = Math.cos(a), s = Math.sin(a); return [c, 0, s, 0, 1, 0, -s, 0, c]; }
  function rotZ(a) { var c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; }
  function wrapPi(a) { a = (a + Math.PI) % (2 * Math.PI); if (a < 0) a += 2 * Math.PI; return a - Math.PI; }

  /* five orbits: radius (globe radii), inclination, ascending node, phase */
  var RINGS = [
    { room: 'legal', r: 1.24, inc: -0.66, node: 0.50, ph: 0.2 },
    { room: 'business', r: 1.35, inc: 0.53, node: 2.05, ph: 1.4 },
    { room: 'creative', r: 1.46, inc: 0.85, node: 5.76, ph: 2.6 },
    { room: 'design', r: 1.57, inc: 1.01, node: 1.71, ph: 0.9 },
    { room: 'research', r: 1.68, inc: 0.46, node: 5.21, ph: 3.7 }
  ];
  var RMAX = 1.68;
  RINGS.forEach(function (g) {
    var ci = Math.cos(g.inc), si = Math.sin(g.inc), cn = Math.cos(g.node), sn = Math.sin(g.node);
    g.u = [cn, 0, -sn]; g.v = [ci * sn, -si, ci * cn]; g.n = [si * sn, ci, si * cn];
    g.w = 0.045 * Math.pow(1.24 / g.r, 1.5);
    g.c = COL[g.room]; g.sats = [];
  });
  var RBY = {}; RINGS.forEach(function (g) { RBY[g.room] = g; });

  function Orbit(stage, opt) {
    var sky = stage.querySelector('.sky') || stage, cv = stage.querySelector('canvas'), ctx = cv.getContext('2d');
    var mini = !!opt.mini, only = opt.only || null;
    var lowTier = Math.min(screen.width, screen.height) < 700 || (navigator.hardwareConcurrency || 8) <= 4;
    var DPR = Math.min(W.devicePixelRatio || 1, lowTier ? 1.5 : 2);
    var NF = mini ? 5000 : (lowTier ? 9000 : 18000);
    /* globe points: x,y,z,type (0 ocean,1 land,2 coast,3 graticule) */
    var pts = [], i, ga = Math.PI * (3 - Math.sqrt(5));
    for (i = 0; i < NF; i++) {
      var y = 1 - 2 * (i + 0.5) / NF, rr = Math.sqrt(1 - y * y), ph = i * ga;
      var x = Math.cos(ph) * rr, z = Math.sin(ph) * rr;
      var L = land(Math.atan2(x, z) * 180 / Math.PI, Math.asin(y) * 180 / Math.PI);
      if (L >= 0.5) pts.push(x, y, z, L < 0.86 ? 2 : 1);
      else if (((Math.imul(i, 2654435761) >>> 0) % 997) < 250) pts.push(x, y, z, 0);
    }
    if (!mini) {
      for (var la = -60; la <= 60; la += 30) for (var lo = 0; lo < 360; lo += 2.4) {
        var a1 = la * Math.PI / 180, b1 = lo * Math.PI / 180;
        pts.push(Math.cos(a1) * Math.sin(b1), Math.sin(a1), Math.cos(a1) * Math.cos(b1), 3);
      }
    }
    var P = new Float32Array(pts), NP = P.length / 4;
    var LB = 9, buckets = [], bc = new Int32Array(4 * LB);
    for (i = 0; i < 4 * LB; i++) buckets.push(new Float32Array(NP * 2));
    var TA = [0.42, 1.0, 1.0, 0.24], TS = [1.1, 1.8, 2.1, 1.0];

    var Wd = 0, Ht = 0, R = 0, R0 = 0, cx = 0, cy = 0, cxT = 0, RT = 0, wide = false, PW = 0;
    var yaw = mini ? 0.6 : -0.5, pitch = 0.34, P0 = 0.34, vYaw = 0, target = null;
    var spin = 0.9, t = 0, focus = only, hl = null, hover = null;
    var rim = null, disc = null, spR = 1;
    var labels = {}, labW = {}, labPos = {};
    var tip = stage.querySelector('.tip'), panel = stage.querySelector('.opanel');
    var sats = [];
    (opt.sats || []).forEach(function (s) {
      var g = RBY[s.room]; if (!g) return; g.sats.push(s); s.g = g; sats.push(s);
    });
    RINGS.forEach(function (g) { g.sats.forEach(function (s, k) { s.th = g.ph + 2 * Math.PI * k / g.sats.length; s.sx = -99; s.sy = -99; s.vis = false; }); });
    if (!mini) Array.prototype.forEach.call(stage.querySelectorAll('.olab'), function (b) { labels[b.getAttribute('data-room')] = b; });

    function sprites() {
      var R = R0; spR = R; var s = Math.ceil(R * 1.36 * 2 * DPR) + 2, c = s / 2;
      rim = D.createElement('canvas'); rim.width = rim.height = s;
      var x = rim.getContext('2d'), g = x.createRadialGradient(c, c, R * 0.92 * DPR, c, c, R * 1.34 * DPR);
      g.addColorStop(0, 'rgba(120,150,255,0)'); g.addColorStop(0.17, 'rgba(140,168,255,0.20)'); g.addColorStop(0.32, 'rgba(110,140,240,0.08)'); g.addColorStop(1, 'rgba(90,120,230,0)');
      x.fillStyle = g; x.fillRect(0, 0, s, s);
      disc = D.createElement('canvas'); disc.width = disc.height = s; x = disc.getContext('2d');
      g = x.createRadialGradient(c - R * 0.38 * DPR, c - R * 0.42 * DPR, R * 0.1 * DPR, c, c, R * DPR);
      g.addColorStop(0, '#111c40'); g.addColorStop(0.7, '#0a1230'); g.addColorStop(1, '#070c20');
      x.fillStyle = g; x.beginPath(); x.arc(c, c, R * DPR, 0, Math.PI * 2); x.fill();
      x.strokeStyle = 'rgba(200,214,255,0.16)'; x.lineWidth = DPR; x.beginPath(); x.arc(c, c, R * DPR - DPR * 0.5, 0, Math.PI * 2); x.stroke();
    }
    function layout() {
      var b = sky.getBoundingClientRect();
      Wd = b.width; Ht = b.height; if (!Wd || !Ht) return;
      cv.width = Math.round(Wd * DPR); cv.height = Math.round(Ht * DPR);
      wide = !mini && Wd >= 560; stage.classList.toggle('is-wide', wide);
      R0 = Math.min(Wd, Ht) / (2 * RMAX + (mini ? 0.12 : 0.34));
      PW = Math.min(310, Math.round(Wd * 0.38)); stage.style.setProperty('--pw', PW + 'px');
      for (var k in labels) labW[k] = [labels[k].offsetWidth, labels[k].offsetHeight];
      aim(true);
      R = RT; cx = cxT; cy = Ht / 2 - (mini ? 0 : 8);
      sprites(); dirty = true;
    }
    function aim(snap) {
      if (focus && wide && !mini) {
        var g = RBY[focus];
        RT = Math.min(R0, (Wd - PW - 24) / (g.r + 1), (Ht / 2 - 36) / g.r);
        cxT = Wd - 8 - g.r * RT;
      } else { RT = R0; cxT = Wd / 2; }
      if (snap || RM) { R = RT; cx = cxT; }
    }
    /* orient so ring g faces the viewer, tipped back by 0.5 rad */
    function faceRing(g) {
      var best = null;
      [1, -1].forEach(function (sg) {
        var nx = g.n[0] * sg, ny = g.n[1] * sg, nz = g.n[2] * sg;
        var yw = Math.atan2(-nx, nz), h = Math.sqrt(nx * nx + nz * nz), phi = Math.atan2(ny, h), pt = phi - 0.5;
        if (Math.abs(pt) > 1.35) return;
        var c = { yaw: yaw + wrapPi(yw - yaw), pitch: pt };
        var cost = Math.abs(c.yaw - yaw) + Math.abs(pt - P0) * 1.5;
        if (!best || cost < best.cost) { c.cost = cost; best = c; }
      });
      return best;
    }
    function setFocus(room) {
      if (mini) return;
      focus = room || null; vYaw = 0;
      if (focus) { target = faceRing(RBY[focus]); } else { target = { yaw: yaw, pitch: P0 }; }
      for (var k in labels) labels[k].setAttribute('aria-expanded', k === focus ? 'true' : 'false');
      stage.classList.toggle('is-focus', !!focus);
      if (panel) {
        if (focus) {
          var g = RBY[focus], c = 'rgb(' + g.c.join(',') + ')';
          panel.style.setProperty('--c', c);
          panel.querySelector('.opanel__m').textContent = 'Orbit ' + (ROOMS.indexOf(focus) + 1) + ' of 5 · ' + g.sats.length + ' satellites';
          var src = D.getElementById('lh-' + focus);
          panel.querySelector('.opanel__t').textContent = src ? src.textContent : LET[focus];
          var ol = panel.querySelector('.opanel__l'); ol.innerHTML = '';
          var log = D.querySelector('#log-' + focus + ' .lg__l');
          if (log) Array.prototype.forEach.call(log.children, function (li) { var n = li.cloneNode(true); n.querySelector('a').classList.remove('is-hl'); ol.appendChild(n); });
          panel.querySelector('.opanel__go').setAttribute('href', focus + '/index.html');
          panel.hidden = false;
        } else panel.hidden = true;
      }
      aim(false); if (RM && target) { yaw = target.yaw; pitch = target.pitch; target = null; }
      dirty = true; kick();
    }
    this.setFocus = setFocus;
    this.focus = function () { return focus; };
    this.highlight = function (id) { hl = id; dirty = true; kick(); };
    function bucketPush(ty, a, x, y) {
      var b = (a * LB) | 0; if (b >= LB) b = LB - 1; if (b < 1) return;
      var k = ty * LB + b, n = bc[k]; buckets[k][n] = x; buckets[k][n + 1] = y; bc[k] = n + 2;
    }
    function ringPath(g, V, front, alpha, lw, dash) {
      var N = 220, open = false, apex = null;
      ctx.beginPath();
      for (var j = 0; j <= N; j++) {
        var th = j / N * Math.PI * 2, c = Math.cos(th), s = Math.sin(th);
        var wx = g.r * (g.u[0] * c + g.v[0] * s), wy = g.r * (g.u[1] * c + g.v[1] * s), wz = g.r * (g.u[2] * c + g.v[2] * s);
        var X = V[0] * wx + V[1] * wy + V[2] * wz, Y = V[3] * wx + V[4] * wy + V[5] * wz, Z = V[6] * wx + V[7] * wy + V[8] * wz;
        var sx = (cx + X * R) * DPR, sy = (cy - Y * R) * DPR;
        if (!apex || Y > apex[2]) apex = [cx + X * R, cy - Y * R, Y];
        if ((Z >= 0) === front) { if (open) ctx.lineTo(sx, sy); else { ctx.moveTo(sx, sy); open = true; } }
        else open = false;
      }
      ctx.strokeStyle = 'rgba(' + g.c.join(',') + ',' + alpha + ')'; ctx.lineWidth = lw * DPR;
      ctx.setLineDash(dash ? [2 * DPR, 4 * DPR] : []); ctx.stroke();
      return apex;
    }
    function satPos(s, V) {
      var g = s.g, c = Math.cos(s.th), sn = Math.sin(s.th);
      var wx = g.r * (g.u[0] * c + g.v[0] * sn), wy = g.r * (g.u[1] * c + g.v[1] * sn), wz = g.r * (g.u[2] * c + g.v[2] * sn);
      var X = V[0] * wx + V[1] * wy + V[2] * wz, Y = V[3] * wx + V[4] * wy + V[5] * wz, Z = V[6] * wx + V[7] * wy + V[8] * wz;
      s.sx = cx + X * R; s.sy = cy - Y * R; s.z = Z;
      var dx = X, dy = Y; s.vis = Z >= 0 || dx * dx + dy * dy > 1;
    }
    function ringAlpha(g, front) {
      if (mini) return g.room === only ? (front ? 0.95 : 0.55) : (front ? 0.13 : 0.07);
      if (focus) return g.room === focus ? (front ? 0.95 : 0.6) : (front ? 0.12 : 0.06);
      return front ? 0.62 : 0.3;
    }
    function drawSats(V, front) {
      for (var k = 0; k < sats.length; k++) {
        var s = sats[k]; if ((s.z >= 0) !== front) continue;
        var g = s.g, dimmed = (focus && g.room !== focus) || (mini && g.room !== only);
        var a = (front ? 1 : 0.5) * (dimmed ? 0.22 : 1), r = mini ? 1.8 : 2.6;
        ctx.fillStyle = 'rgba(' + g.c.join(',') + ',' + a + ')';
        ctx.beginPath(); ctx.arc(s.sx * DPR, s.sy * DPR, r * DPR, 0, 6.2832); ctx.fill();
        if (!mini && front && !dimmed) {
          ctx.strokeStyle = 'rgba(' + g.c.join(',') + ',0.35)'; ctx.lineWidth = DPR;
          ctx.beginPath(); ctx.arc(s.sx * DPR, s.sy * DPR, 5.5 * DPR, 0, 6.2832); ctx.stroke();
        }
      }
    }
    function draw() {
      var V = view(yaw, pitch), G = mul(V, mul(rotZ(0.41), rotY(spin)));
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
      for (var k = 0; k < sats.length; k++) satPos(sats[k], V);
      /* back half */
      for (k = 0; k < RINGS.length; k++) ringPath(RINGS[k], V, false, ringAlpha(RINGS[k], false), 1, true);
      drawSats(V, false);
      /* globe */
      var sz = Math.max(0.75, Math.min(1.35, R / 210));
      var sd = rim.width * R / spR, sx0 = cx * DPR - sd / 2, sy0 = cy * DPR - sd / 2;
      ctx.drawImage(rim, sx0, sy0, sd, sd); ctx.drawImage(disc, sx0, sy0, sd, sd);
      bc.fill(0);
      var g0 = G[0], g1 = G[1], g2 = G[2], g3 = G[3], g4 = G[4], g5 = G[5], g6 = G[6], g7 = G[7], g8 = G[8];
      var lx = -0.42, ly = 0.52, lz = 0.74, RD = R * DPR, CX = cx * DPR, CY = cy * DPR;
      for (var j = 0, o = 0; j < NP; j++, o += 4) {
        var x = P[o], y = P[o + 1], z = P[o + 2];
        var Z = g6 * x + g7 * y + g8 * z; if (Z <= 0.02) continue;
        var X = g0 * x + g1 * y + g2 * z, Y = g3 * x + g4 * y + g5 * z, ty = P[o + 3];
        var d = X * lx + Y * ly + Z * lz, sh = 0.3 + 0.7 * (d > 0 ? d : 0);
        var a = TA[ty] * sh * (0.3 + 0.7 * Math.sqrt(Z)) * 1.12;
        bucketPush(ty, a, CX + X * RD, CY - Y * RD);
      }
      ctx.fillStyle = '#dfe6f2';
      for (var ty2 = 0; ty2 < 4; ty2++) {
        var s = TS[ty2] * sz * DPR, h = s / 2;
        for (var b = 1; b < LB; b++) {
          var kk = ty2 * LB + b, n = bc[kk]; if (!n) continue;
          var arr = buckets[kk];
          ctx.globalAlpha = (b + 0.5) / LB; ctx.beginPath();
          if (ty2 === 1 || ty2 === 2) for (var q = 0; q < n; q += 2) { ctx.moveTo(arr[q] + h, arr[q + 1]); ctx.arc(arr[q], arr[q + 1], h, 0, 6.2832); }
          else for (q = 0; q < n; q += 2) ctx.rect(arr[q] - h, arr[q + 1] - h, s, s);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
      /* front half */
      var apex = {};
      for (k = 0; k < RINGS.length; k++) {
        var gg = RINGS[k], on = (focus && gg.room === focus) || (mini && gg.room === only);
        apex[gg.room] = ringPath(gg, V, true, ringAlpha(gg, true), on ? 1.5 : 1.1, false);
      }
      drawSats(V, true);
      /* highlight */
      var hs = hover || findSat(hl);
      if (hs && !mini) {
        var c = 'rgb(' + hs.g.c.join(',') + ')';
        ctx.strokeStyle = c; ctx.lineWidth = 1.5 * DPR; ctx.globalAlpha = hs.vis ? 1 : 0.6;
        ctx.beginPath(); ctx.arc(hs.sx * DPR, hs.sy * DPR, 10 * DPR, 0, 6.2832); ctx.stroke();
        ctx.fillStyle = c; ctx.beginPath(); ctx.arc(hs.sx * DPR, hs.sy * DPR, 3.6 * DPR, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
      }
      if (!mini) { placeLabels(apex); placeTip(hs); }
    }
    function findSat(id) { if (!id) return null; for (var k = 0; k < sats.length; k++) if (sats[k].id === id) return sats[k]; return null; }
    function placeLabels(apex) {
      var L = [], left = (focus && wide) ? PW + 30 : 6;
      for (var k in labels) {
        var a = apex[k], w = labW[k][0], h = labW[k][1];
        L.push({ k: k, x: a[0] - w / 2, y: a[1] - h - 10, w: w, h: h });
      }
      function clampL(p) { p.x = Math.max(left, Math.min(Wd - p.w - 6, p.x)); p.y = Math.max(4, Math.min(Ht - p.h - 28, p.y)); }
      function hit(p, placed) { for (var m = 0; m < placed.length; m++) { var q = placed[m]; if (p.x < q.x + q.w + 6 && q.x < p.x + p.w + 6 && p.y < q.y + q.h + 4 && q.y < p.y + p.h + 4) return true; } return false; }
      L.sort(function (p, q) { return (q.k === focus) - (p.k === focus) || p.y - q.y; });
      var placed = [];
      L.forEach(function (p) {
        var x0 = p.x, y0 = p.y, dy = p.h + 6, dx = p.w * 0.6 + 8, ok = false;
        var C = [[0, 0], [0, -dy], [0, dy], [dx, 0], [-dx, 0], [dx, -dy], [-dx, -dy], [dx, dy], [-dx, dy], [0, -2 * dy], [0, 2 * dy], [2 * dx, 0], [-2 * dx, 0], [0, -3 * dy], [0, 3 * dy]];
        for (var c = 0; c < C.length; c++) { p.x = x0 + C[c][0]; p.y = y0 + C[c][1]; clampL(p); if (!hit(p, placed)) { ok = true; break; } }
        if (!ok) { p.x = x0; p.y = y0; clampL(p); }
        placed.push(p);
      });
      L.forEach(function (p) {
        var o = labPos[p.k];
        if (!o || RM || jump) o = labPos[p.k] = { x: p.x, y: p.y };
        else if (Math.abs(p.x - o.x) + Math.abs(p.y - o.y) > 40) { o.x = p.x; o.y = p.y; }
        else { o.x += (p.x - o.x) * 0.5; o.y += (p.y - o.y) * 0.5; }
        labels[p.k].style.transform = 'translate(' + o.x.toFixed(1) + 'px,' + o.y.toFixed(1) + 'px)';
      });
      jump = false;
    }
    var jump = true;
    function placeTip(s) {
      if (!tip) return;
      if (!s) { tip.hidden = true; return; }
      if (tip.getAttribute('data-id') !== s.id) {
        tip.setAttribute('data-id', s.id);
        tip.querySelector('b').textContent = s.title; tip.querySelector('span').textContent = s.sub;
        tip.querySelector('em').textContent = s.code + ' · ' + LET[s.room];
        tip.style.setProperty('--c', 'rgb(' + s.g.c.join(',') + ')');
        tip.hidden = false; tip._w = tip.offsetWidth; tip._h = tip.offsetHeight;
      }
      tip.hidden = false;
      var left = (focus && wide) ? PW + 30 : 4;
      var x = s.sx + 16, y = s.sy - tip._h - 12;
      if (x + tip._w > Wd - 4) x = s.sx - tip._w - 16;
      if (x < left) x = left;
      if (y < 4) y = s.sy + 16;
      tip.style.transform = 'translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
    }

    /* ---------- loop */
    var raf = 0, last = 0, running = false, visible = true, dirty = true, stats = W.__orbit = W.__orbit || { dts: [], draw: [] };
    function animating() { return !RM || target || Math.abs(vYaw) > 1e-4 || Math.abs(R - RT) > 0.3 || Math.abs(cx - cxT) > 0.3; }
    function frame(now) {
      raf = 0;
      var dt = last ? Math.min(0.05, (now - last) / 1000) : 0.016; last = now;
      if (!mini) { stats.dts.push(dt * 1000); if (stats.dts.length > 600) stats.dts.shift(); }
      if (!RM) {
        t += dt; spin += dt * (mini ? 0.1 : 0.07);
        for (var k = 0; k < sats.length; k++) sats[k].th += dt * sats[k].g.w;
        if (!drag && Math.abs(vYaw) > 1e-4) { yaw += vYaw * dt; vYaw *= Math.exp(-dt * 2.4); }
      }
      if (target) {
        var e = RM ? 1 : 1 - Math.exp(-dt * 3.4);
        yaw += (target.yaw - yaw) * e; pitch += (target.pitch - pitch) * e;
        if (Math.abs(target.yaw - yaw) < 1e-3 && Math.abs(target.pitch - pitch) < 1e-3) { yaw = target.yaw; pitch = target.pitch; target = null; }
      }
      var e2 = RM ? 1 : 1 - Math.exp(-dt * 4);
      R += (RT - R) * e2; cx += (cxT - cx) * e2;
      var t0 = performance.now(); draw(); dirty = false;
      if (!mini) { stats.draw.push(performance.now() - t0); if (stats.draw.length > 600) stats.draw.shift(); }
      if (running && (animating() || dirty)) raf = requestAnimationFrame(frame);
      else last = 0;
    }
    function kick() { if (running && !raf) { raf = requestAnimationFrame(frame); } }
    function setRun() {
      running = visible && !D.hidden;
      if (running) { dirty = true; kick(); } else if (raf) { cancelAnimationFrame(raf); raf = 0; last = 0; }
    }
    D.addEventListener('visibilitychange', setRun);
    if ('IntersectionObserver' in W) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; setRun(); }, { rootMargin: '40px' }).observe(sky);
    if ('ResizeObserver' in W) new ResizeObserver(function () { layout(); jump = true; kick(); }).observe(sky);
    else W.addEventListener('resize', function () { layout(); kick(); });
    layout(); setRun();

    /* ---------- pointer: drag with inertia, hover, click */
    var drag = null;
    if (mini) return;
    function pick(px, py, rad) {
      var best = null, bd = rad * rad;
      for (var k = 0; k < sats.length; k++) {
        var s = sats[k]; if (!s.vis) continue;
        if (focus && s.g.room !== focus) continue;
        var dx = s.sx - px, dy = s.sy - py, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = s; }
      }
      return best;
    }
    function local(e) { var b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; }
    cv.addEventListener('pointerdown', function (e) {
      var p = local(e);
      drag = { x: p[0], y: p[1], lx: p[0], ly: p[1], t: performance.now(), moved: false, id: e.pointerId, type: e.pointerType, v: 0 };
      vYaw = 0;
    });
    cv.addEventListener('pointermove', function (e) {
      var p = local(e);
      if (drag && drag.id === e.pointerId) {
        var dx = p[0] - drag.lx, dy = p[1] - drag.ly, now = performance.now(), dt = Math.max(1, now - drag.t);
        if (!drag.moved && Math.abs(p[0] - drag.x) + Math.abs(p[1] - drag.y) > 5) {
          drag.moved = true; stage.classList.add('is-drag'); target = null;
          try { cv.setPointerCapture(e.pointerId); } catch (_) {}
        }
        if (drag.moved) {
          var k = 2.6 / Math.max(260, R * 2);
          yaw += dx * k; if (drag.type === 'mouse') pitch = Math.max(-1.2, Math.min(1.25, pitch + dy * k));
          drag.v = drag.v * 0.6 + (dx * k / (dt / 1000)) * 0.4;
          hover = null;
        }
        drag.lx = p[0]; drag.ly = p[1]; drag.t = now; dirty = true; kick();
        return;
      }
      if (e.pointerType === 'mouse') {
        var s = pick(p[0], p[1], 14);
        if (s !== hover) { hover = s; stage.classList.toggle('is-hot', !!s); dirty = true; kick(); }
      }
    });
    function end(e) {
      if (!drag || drag.id !== e.pointerId) return;
      var d = drag; drag = null; stage.classList.remove('is-drag');
      if (d.moved) { if (!RM && performance.now() - d.t < 90) vYaw = Math.max(-3, Math.min(3, d.v)); kick(); return; }
      if (e.type === 'pointercancel') return;
      var p = local(e), s = pick(p[0], p[1], d.type === 'mouse' ? 14 : 22);
      if (s) {
        if (d.type !== 'mouse' && hover !== s) { hover = s; dirty = true; kick(); return; }
        location.href = s.href; return;
      }
      hover = null; stage.classList.remove('is-hot');
      if (focus) setFocus(null); else { dirty = true; kick(); }
    }
    cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
    cv.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse' && hover && !drag) { hover = null; stage.classList.remove('is-hot'); dirty = true; kick(); } });
  }

  /* ---------- homepage system */
  var stage = D.getElementById('stage');
  if (stage) {
    var sats = Array.prototype.map.call(D.querySelectorAll('#log a[data-sat]'), function (a) {
      return { id: a.getAttribute('data-sat'), room: a.getAttribute('data-room'), href: a.getAttribute('href'),
        title: a.querySelector('.lt').textContent, sub: a.querySelector('.ls').textContent, code: a.querySelector('.lc').textContent };
    });
    var orb = new Orbit(stage, { sats: sats });
    Array.prototype.forEach.call(stage.querySelectorAll('.olab'), function (b) {
      b.addEventListener('click', function (e) { e.stopPropagation(); var r = b.getAttribute('data-room'); orb.setFocus(orb.focus() === r ? null : r); });
    });
    var panel = D.getElementById('opanel');
    panel.querySelector('.opanel__x').addEventListener('click', function () { var f = orb.focus(); orb.setFocus(null); var l = stage.querySelector('.olab[data-room="' + f + '"]'); if (l) l.focus(); });
    D.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && orb.focus()) { var f = orb.focus(); orb.setFocus(null); var l = stage.querySelector('.olab[data-room="' + f + '"]'); if (l && (panel.contains(D.activeElement) || D.activeElement === l)) l.focus(); }
    });
    D.addEventListener('click', function (e) {
      if (orb.focus() && !stage.contains(e.target)) orb.setFocus(null);
    });
    function hlFrom(e) { var a = e.target.closest && e.target.closest('a[data-sat]'); return a ? a.getAttribute('data-sat') : null; }
    var cur = null;
    function setHL(id) {
      if (id === cur) return; cur = id; orb.highlight(id);
      Array.prototype.forEach.call(D.querySelectorAll('#log a.is-hl'), function (a) { a.classList.remove('is-hl'); });
      if (id) { var a = D.querySelector('#log a[data-sat="' + id + '"]'); if (a) a.classList.add('is-hl'); }
    }
    [D.getElementById('log'), panel].forEach(function (root) {
      root.addEventListener('focusin', function (e) { setHL(hlFrom(e)); });
      root.addEventListener('focusout', function () { setHL(null); });
      root.addEventListener('mouseover', function (e) { var id = hlFrom(e); if (id) setHL(id); });
      root.addEventListener('mouseleave', function () { setHL(null); });
    });
  }

  /* ---------- room page: small globe with only this room's ring lit */
  var mini = D.getElementById('mini');
  if (mini) {
    var room = B.getAttribute('data-room');
    var ms = Array.prototype.map.call(D.querySelectorAll('.chips a[data-sat]'), function (a) { return { id: a.getAttribute('data-sat'), room: room }; });
    new Orbit(mini, { mini: true, only: room, sats: ms });
  }
})();
'''


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    write(os.path.join(OUT, 'h.css'), CSS.replace('%STARS%', stars_bg()))
    write(os.path.join(OUT, 'h.js'), JS.replace('%MASK%', MASK))
    write(os.path.join(OUT, 'index.html'), home_page())
    for i, r in enumerate(ROOMS):
        write(os.path.join(OUT, r['slug'], 'index.html'), room_page(i, r))
    print('mockup-h: %d rooms, %d cases, css %d B, js %d B' % (len(ROOMS), N_CASES, len(CSS), len(JS)))


if __name__ == '__main__':
    main()
