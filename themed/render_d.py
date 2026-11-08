#!/usr/bin/env python3
"""Build mockup D, "MPWP 5.1": the portfolio as a 1991 word processor for DOS.

    python3 -I themed/render_d.py

Reads themed/live.json and writes mockup-d/index.html, mockup-d/<room>/index.html,
mockup-d/d.css and mockup-d/d.js. Stdlib only. Safe to re-run.

Path rules: body markup is written for a room page at the site root, so from
mockup-d/<room>/ every "../" gains one more "../" (assets and demos live at the repo root).
"""
import datetime
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-d')
LIVE = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME = LIVE['home']
ROOMS = LIVE['rooms']
SLUGS = [r['slug'] for r in ROOMS]
MAIL = 'mzpprojects1@gmail.com'
unesc = html.unescape
esc = lambda t: html.escape(t, quote=True)

# ------------------------------------------------------------------ helpers


def dosname(text, used):
    """8.3 name: letters and digits only, interior vowels dropped from the right until it fits."""
    s = re.sub(r'[^A-Z0-9]', '', text.upper())
    if len(s) > 8:
        ch = list(s)
        i = len(ch) - 2
        while len(ch) > 8 and i > 0:
            if ch[i] in 'AEIOU':
                del ch[i]
            i -= 1
        s = ''.join(ch)[:8]
    base, n = s, 1
    while s in used:
        suf = '~%d' % n
        s = base[:8 - len(suf)] + suf
        n += 1
    used.add(s)
    return s + '.DOC'


def box(lines, width):
    """Double-line box of exactly `width` columns."""
    inner = width - 2
    out = ['╔' + '═' * inner + '╗']
    for l in lines:
        out.append('║' + (' ' + l).ljust(inner) + '║')
    out.append('╚' + '═' * inner + '╝')
    return '\n'.join(out)


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


def body_links(b):
    return [(unesc(re.sub(r'<[^>]+>', '', m.group(2))).strip(), m.group(1))
            for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.search(r'<p class="links">.*?</p>', b, re.S).group(0) if re.search(r'<p class="links">.*?</p>', b, re.S) else '', re.S)]


# ------------------------------------------------------------------ data model
used_by_room = {}
DATE0 = datetime.date(2026, 11, 7)
n_files = 0
for r in ROOMS:
    used = set()
    r['dir'] = r['slug'].upper()
    r['plain'] = unesc(r['title'])
    r['nproj'] = sum(1 for i in r['items'] if i['kind'] == 'case')
    for it in r['items']:
        if it['kind'] == 'case':
            it['file'] = dosname(it['id'], used)
            it['date'] = (DATE0 - datetime.timedelta(days=n_files)).strftime('%m-%d-%y')
            n_files += 1
        elif it['kind'] == 'extra':
            t = re.search(r'xsec__t"[^>]*>(.*?)</h2>', it['html'], re.S).group(1)
            it['title'] = t
            it['file'] = dosname(unesc(t), used)
RATIO = 8

# ------------------------------------------------------------------ shared chrome
BOOT_BOX = box(['MPWP 5.1 · Myles Parslow', 'makes things with AI'], 34)

BOOT = """<div id="boot" aria-hidden="true">
<pre class="b b1">MPWP BIOS 5.1 · (C) none reserved</pre>
<pre class="b b2">Memory test: 640K OK</pre>
<pre class="b b3">Keyboard . . . OK    Fixed disk C: . . . OK</pre>
<pre class="b b4">C:\\&gt; MPWP</pre>
<p class="b b5 vt">MPWP 5.1</p>
<pre class="b b6">@@BOX@@</pre>
<pre class="b b7">Press any key to continue_</pre>
</div>""".replace('@@BOX@@', BOOT_BOX)


def head_script(home):
    s = ("<script>(function(){var d=document.documentElement,t;d.classList.add('js');"
         "try{t=localStorage.getItem('mpwp-theme')}catch(e){}"
         "d.setAttribute('data-theme',t==='print'?'print':'dos');")
    if home:
        s += ("var M=@@MAP@@,h=location.hash.slice(1);"
              "if(h&&M[h]){location.replace(M[h]+'/index.html'+(h==='g-'+M[h]?'':'#'+h));return}"
              "try{if(!matchMedia('(prefers-reduced-motion: reduce)').matches&&!sessionStorage.getItem('mpwp-boot'))d.classList.add('booting')}catch(e){}")
    s += "})()</script>"
    if home:
        s = s.replace('@@MAP@@', HOME['redirect_map'])
    return s


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=VT323&display=swap">')


def bars(depth, file=""):
    up = '../' * depth
    return """<footer class="bars" id="bars">
<nav class="fkeys" aria-label="Function keys">
<a class="fk" id="k-home" href="@@UP@@index.html"><kbd>H</kbd>Home</a>
<a class="fk" id="k-list" href="@@UP@@index.html#files"><kbd>L</kbd>List Files</a>
<a class="fk" id="k-rooms" href="@@UP@@index.html#files"><kbd>O</kbd>Rooms</a>
<button class="fk needs-js" id="k-codes" type="button" aria-pressed="false" aria-controls="codes"><kbd>R</kbd>Reveal Codes</button>
<button class="fk needs-js" id="k-print" type="button" aria-pressed="false"><kbd>P</kbd>Print Preview</button>
<button class="fk needs-js" id="k-help" type="button"><kbd>?</kbd>Help</button>
<a class="fk" id="k-exit" href="@@UP@@index.html#contact"><kbd>X</kbd>Exit</a>
</nav>
<p class="status"><span class="st-l" id="st-file">@@FILE@@</span><span class="st-r">Doc 1 <span class="sp"></span>Pg <b id="st-pg">1</b> <span class="sp"></span>Ln <b id="st-ln">1&quot;</b> <span class="sp"></span>Pos 1&quot;</span></p>
</footer>""".replace('@@UP@@', '' if depth == 0 else up).replace('@@FILE@@', esc(file))


def panels(depth):
    pre = '' if depth == 0 else '../'
    rows = ''.join(
        '<li><a class="lf-row" href="%s%s/index.html"><span class="n">%s</span><span class="t">&lt;DIR&gt;</span><span class="s">%s · %d projects</span></a></li>'
        % (pre, r['slug'], r['dir'], r['title'], r['nproj']) for r in ROOMS)
    return """<aside class="codes" id="codes" aria-label="Reveal Codes" hidden>
<p class="codes__bar" aria-hidden="true"><span>Reveal Codes</span><span class="ruler"></span><span>R or Esc closes</span></p>
<div id="codes-body"></div>
</aside>
<section class="panel" id="p-rooms" role="dialog" aria-label="Rooms" hidden>
<h2 class="panel__t">Rooms · C:\\PORTFOLIO\\*.*</h2>
<ul class="plist">@@ROWS@@</ul>
<p class="panel__f"><button type="button" class="pclose">Esc Close</button></p>
</section>
<section class="panel" id="p-help" role="dialog" aria-label="Help" hidden>
<h2 class="panel__t">Help · MPWP 5.1</h2>
<dl class="keys"><dt>H</dt><dd>Home: back to the homepage (Esc does the same on a room page)</dd>
<dt>L</dt><dd>List Files: the project directory on the home page</dd>
<dt>O</dt><dd>Rooms: the five rooms as directories</dd>
<dt>R</dt><dd>Reveal Codes: the current case study as WordPerfect-style codes</dd>
<dt>P</dt><dd>Print Preview: switch between the blue screen and a paper sheet</dd>
<dt>X</dt><dd>Exit: the contact screen</dd>
<dt>Esc</dt><dd>Close whatever is open</dd>
<dt>&uarr; &darr;</dt><dd>In List Files, move the highlight bar. Enter opens, Tab jumps to the next directory.</dd></dl>
<p class="panel__f">A tribute to the look of a 1991 word processor. Not affiliated with any software company. <button type="button" class="pclose">Esc Close</button></p>
</section>""".replace('@@ROWS@@', rows)


def page_shell(title, desc, depth, body_cls, page, inner, extra_head='', codes=None, file=''):
    css = '../' * depth + 'd.css'
    js = '../' * depth + 'd.js'
    cd = json.dumps(codes or {}, ensure_ascii=False).replace('<', '\\u003c')
    return """<!doctype html>
<html lang="en" data-theme="dos">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="@@DESC@@">
<meta name="theme-color" content="#0a1a96">
<title>@@TITLE@@</title>
<link rel="icon" href="data:,">
@@HEAD@@
@@FONTS@@
<link rel="stylesheet" href="@@CSS@@">
</head>
<body class="@@CLS@@" data-page="@@PAGE@@">
<a class="skip" href="#main">Skip to the content</a>
@@INNER@@
@@BARS@@
@@PANELS@@
<script type="application/json" id="codes-data">@@CD@@</script>
<script src="@@JS@@" defer></script>
</body>
</html>
""".replace('@@DESC@@', esc(desc)).replace('@@TITLE@@', title).replace('@@HEAD@@', head_script(page == 'home')) \
        .replace('@@FONTS@@', FONTS).replace('@@CSS@@', css).replace('@@CLS@@', body_cls).replace('@@PAGE@@', page) \
        .replace('@@INNER@@', inner).replace('@@BARS@@', bars(depth, file)).replace('@@PANELS@@', panels(depth)) \
        .replace('@@CD@@', cd).replace('@@JS@@', js)


def code_entry(it, links):
    return {'t': unesc(it['title']), 'k': [unesc(k) for k in it['kickers']], 's': unesc(it['sub']),
            'id': it['id'], 'n': it['count'], 'l': [l[0] for l in links]}


ARCH = '''<section class="scr" id="archive" data-file="C:\\PORTFOLIO\\ARCHIVE.DOC" data-pg="4" aria-labelledby="h-arch"><p class="docbar">ARCHIVE.DOC</p>
<h2 id="h-arch" class="arch-t">Style archive.</h2>
<p>This site is also a running design experiment. Each version renders the same 53 case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. <a href="../styles/index.html"><b>See every version &rarr;</b></a></p>
<p class="arch-here">You&rsquo;re looking at: MPWP 5.1</p></section>'''


# ------------------------------------------------------------------ home
def home_page():
    h = HOME['hero_html']
    lede = re.search(r'<p class="lede">.*?</p>', h, re.S).group(0)
    stats = re.search(r'<dl class="stats">.*?</dl>', h, re.S).group(0)
    h1 = unesc(re.sub(r'<[^>]+>', '', re.search(r'aria-label="([^"]+)"', h).group(1)))
    codes, rows = {}, []
    d = 0
    for r in ROOMS:
        rows.append('<li><a class="lf-row is-dir" href="%s/index.html" data-path="C:\\PORTFOLIO\\%s\\*.*"><span class="n">%s</span><span class="t">&lt;DIR&gt;</span><span class="s">%s · %d projects</span><span class="d">%s</span></a></li>'
                    % (r['slug'], r['dir'], r['dir'], r['title'], r['nproj'], (DATE0 - datetime.timedelta(days=60 + d)).strftime('%m-%d-%y')))
        d += 1
        for it in r['items']:
            if it['kind'] != 'case':
                continue
            bl = body_links(it['body_html'])
            codes[it['id']] = code_entry(it, bl)
            rows.append('<li><a class="lf-row" href="%s/index.html#%s" data-id="%s" data-path="C:\\PORTFOLIO\\%s\\%s"><span class="n">%s</span><span class="t">%s</span><span class="s">%s</span><span class="d">%s</span></a></li>'
                        % (r['slug'], it['id'], it['id'], r['dir'], it['file'], it['file'], esc(unesc(it['title'])), esc(unesc(it['sub'])), it['date']))
    rules = HOME['rules_html']
    tools = HOME['tools_html'].replace('<details class="more">', '<details class="more">')
    foot = """<section class="scr exit" id="contact" data-file="C:\\PORTFOLIO\\EXIT" data-pg="5" aria-labelledby="h-exit">
<p class="docbar">EXIT</p>
<div class="wbox"><h2 class="wbox__t" id="h-exit">Say hello.</h2>
<p class="exit-q">Save document? <a class="yn" href="mailto:@@M@@" aria-label="Yes, email Myles">Yes</a> (<a class="yn" href="#top" aria-label="No, back to the top">No</a>)</p>
<p class="mailrow">Mail: <a class="mail" href="mailto:@@M@@">@@M@@</a></p>
<p class="foot__row"><a href="https://github.com/mylesparslow-collab" target="_blank" rel="noopener">GitHub</a> <a href="https://mylesparslow.com/legal-portfolio/" target="_blank" rel="noopener">Legal portfolio</a> <a href="#top">Back to top &uarr;</a> <span>Myles Parslow &middot; Made with AI</span></p>
</div></section>""".replace('@@M@@', MAIL)
    inner = """@@BOOT@@
<main id="main" class="sheet"><div id="top"></div>
<section class="scr" id="files" data-file="C:\\PORTFOLIO\\*.*" data-pg="1" aria-labelledby="h-files">
<div class="lf-top"><span>11-07-26 9:15a</span><h2 id="h-files">Directory C:\\PORTFOLIO\\*.*</h2></div>
<div class="wbox docsum"><h2 class="wbox__t">Document Summary</h2>
<h1 class="vt">@@H1@@</h1>
@@LEDE@@
@@STATS@@
</div>
<nav class="lf" aria-label="Portfolio files, 5 rooms and @@N@@ projects">
<p class="lf-cols" aria-hidden="true"><span>Name</span><span>Title</span><span>Description</span><span>Date</span></p>
<ul class="lf-list">@@ROWS@@</ul>
</nav>
<p class="lf-keys"><span><b>&uarr;&darr;</b> Move bar</span> <span><b>Enter</b> Open</span> <span><b>Tab</b> Next directory</span> <span><b>R</b> Reveal Codes</span> <span><b>P</b> Print Preview</span></p>
</section>
<section class="scr" data-file="C:\\PORTFOLIO\\RULES.DOC" data-pg="2"><p class="docbar">RULES.DOC</p>@@RULES@@</section>
<section class="scr" data-file="C:\\PORTFOLIO\\TOOLS.DOC" data-pg="3"><p class="docbar">TOOLS.DOC</p>@@TOOLS@@</section>
@@ARCH@@
@@FOOT@@
</main>""".replace('@@BOOT@@', BOOT).replace('@@H1@@', esc(h1)).replace('@@LEDE@@', lede).replace('@@STATS@@', stats) \
        .replace('@@N@@', str(n_files)).replace('@@ROWS@@', ''.join(rows)).replace('@@RULES@@', rules).replace('@@TOOLS@@', tools).replace('@@ARCH@@', ARCH).replace('@@FOOT@@', foot)
    return page_shell('MPWP 5.1 · Myles Parslow Portfolio', 'Myles Parslow makes things with AI: software for law firms and businesses, novels, games and reference works.',
                      0, 'home', 'home', inner, codes=codes, file='C:\\PORTFOLIO\\*.*')


# ------------------------------------------------------------------ room pages
def room_page(idx, r):
    slug, dirn = r['slug'], r['dir']
    cases = [i for i in r['items'] if i['kind'] == 'case']
    nxt = ROOMS[idx + 1] if idx + 1 < len(ROOMS) else None
    codes, parts = {}, []
    toc = ''.join('<li><a href="#%s"><span class="tn">%s</span> %s</a></li>' % (c['id'], c['count'].split(' / ')[0], esc(unesc(c['title']))) for c in cases)
    first_file = '%s.DOC' % dirn
    parts.append("""<header class="scr rtitle" id="top" data-file="C:\\PORTFOLIO\\@@D@@\\@@F@@" data-pg="1">
<p class="crumb"><a href="../index.html#files">C:\\PORTFOLIO</a>\\@@D@@\\</p>
<p class="eyebrow">@@EY@@</p>
<h1 class="vt"><a class="homelink" href="../index.html" title="Back to the homepage">@@T@@</a></h1>
<p class="rcount">@@CT@@</p>
<p class="rlede">@@L@@</p>
<nav class="toc" aria-label="Pages in this room"><ol>@@TOC@@</ol></nav>
</header>""".replace('@@D@@', dirn).replace('@@F@@', first_file).replace('@@EY@@', r['eyebrow']).replace('@@T@@', r['title'])
        .replace('@@CT@@', r['count']).replace('@@L@@', r['lede']).replace('@@TOC@@', toc))
    pg = 0
    skip_break = False
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            parts.append('<div class="pb" aria-hidden="true"></div>')
            parts.append(it['html'])
            skip_break = True
        elif k == 'case':
            pg += 1
            bl = body_links(it['body_html'])
            codes[it['id']] = code_entry(it, bl)
            kick = ''.join('<span>%s</span>' % kk for kk in it['kickers'])
            if not skip_break:
                parts.append('<div class="pb" aria-hidden="true"></div>')
            skip_break = False
            parts.append("""<article class="page scr" id="@@ID@@" data-id="@@ID@@" data-file="C:\\PORTFOLIO\\@@D@@\\@@F@@" data-pg="@@PG@@" aria-labelledby="t-@@ID@@">
<header class="chead"><p class="ckick"><span class="cn">@@CN@@</span>@@K@@</p>
<h2 class="ctitle" id="t-@@ID@@">@@T@@</h2>
<p class="csub">@@S@@</p>
<p class="clede">@@L@@</p></header>
<div class="cbody">
@@B@@
</div>
</article>""".replace('@@ID@@', it['id']).replace('@@D@@', dirn).replace('@@F@@', it['file']).replace('@@PG@@', str(pg + 0))
                         .replace('@@CN@@', it['count']).replace('@@K@@', kick).replace('@@T@@', it['title']).replace('@@S@@', it['sub'])
                         .replace('@@L@@', it['lede']).replace('@@B@@', fix_body(it['body_html']).strip()))
        elif k == 'extra':
            pg += 1
            parts.append('<div class="pb" aria-hidden="true"></div>')
            x = it['html'].replace('<section class="xsec"', '<section class="xsec page scr" data-file="C:\\PORTFOLIO\\%s\\%s" data-pg="%d"' % (dirn, it['file'], pg), 1)
            parts.append(x)
    nav = ('<a class="pgdn" href="../%s/index.html">[PgDn] Next room: %s</a>' % (nxt['slug'], nxt['dir']) if nxt
           else '<a class="pgdn" href="../index.html#files">[PgDn] That was the last room. Back to List Files</a>')
    parts.append('<div class="pb" aria-hidden="true"></div>')
    parts.append("""<nav class="pn" aria-label="Next room">@@N@@ <a href="../index.html#files">[Home] List Files</a></nav>
<footer class="rfoot"><p>Mail: <a class="mail" href="mailto:@@M@@">@@M@@</a> &middot; <a href="https://github.com/mylesparslow-collab" target="_blank" rel="noopener">GitHub</a> &middot; <a href="https://mylesparslow.com/legal-portfolio/" target="_blank" rel="noopener">Legal portfolio</a> &middot; <a href="#top">Back to top &uarr;</a></p>
<p>Myles Parslow &middot; Made with AI</p></footer>""".replace('@@N@@', nav).replace('@@M@@', MAIL))
    inner = '<main id="main" class="sheet doc">\n%s\n</main>' % '\n'.join(parts)
    return page_shell('%s · MPWP 5.1 · Myles Parslow Portfolio' % esc(r['plain']), unesc(re.sub(r'<[^>]+>', '', r['lede'])), 1, 'room', 'room', inner, codes=codes, file='C:\\PORTFOLIO\\%s\\%s.DOC' % (dirn, dirn))


# ------------------------------------------------------------------ css + js
CSS = r'''/* MPWP 5.1: a tribute to a 1991 word processor for DOS. Original UI, no trademarks. */
:root{--blue:#0a1a96;--desk:var(--blue);--paper:var(--blue);--fg:#d8d8d8;--bright:#fff;--hi:#ffff55;--link:#55ffff;--selbg:#55ffff;--selfg:#0a1a96;--mute:#a9b4ff;--frame:#fff;--shadow:none;--barbg:#aaa;--barfg:#000;--bars:5rem;--codes-h:0px;--pad:clamp(1rem,3vw,2.5rem);color-scheme:dark}
:root[data-theme=print]{--desk:#8a8a8a;--paper:#f6f4ee;--fg:#151515;--bright:#000;--hi:#151515;--link:#0b2a8f;--selbg:#151515;--selfg:#f6f4ee;--mute:#4d4d4d;--frame:#151515;--shadow:0 2px 6px rgba(0,0,0,.25),0 18px 50px rgba(0,0,0,.28);color-scheme:light}
*{box-sizing:border-box}
html{font-size:16px;scroll-padding-bottom:calc(var(--bars) + var(--codes-h) + 1rem);-webkit-text-size-adjust:100%}
body{margin:0;background:var(--desk);color:var(--fg);font:400 1rem/1.5 "IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;padding-bottom:calc(var(--bars) + var(--codes-h));overflow-wrap:break-word}
[data-theme=print] body{padding-top:1.5rem}
@media(max-width:700px){html{font-size:15px}[data-theme=print] body{padding-top:0}}
::selection{background:var(--selbg);color:var(--selfg)}
[id]{scroll-margin-top:1rem}
a{color:var(--link);text-underline-offset:.2em}
a:hover{background:var(--selbg);color:var(--selfg);text-decoration:none}
:focus-visible{outline:2px solid var(--link);outline-offset:2px}
[data-theme=print] :focus-visible{outline-color:#0b2a8f}
b,strong{font-weight:600;color:var(--bright)}
.vt{font-family:VT323,"IBM Plex Mono",monospace;font-weight:400;line-height:.95;margin:0;letter-spacing:0}
.skip{position:absolute;left:-999px;top:0;background:var(--selbg);color:var(--selfg);padding:.5rem 1ch;z-index:200}
.skip:focus{left:0}
.needs-js{display:none}.js .needs-js{display:inline-flex}

/* the sheet: full-bleed blue on the DOS screen, a paper page on the grey desk in Print Preview */
.sheet{width:min(100%,136ch);margin:0 auto;padding:1rem var(--pad) 2rem;background:var(--paper);--w:78ch}
[data-theme=print] .sheet{margin:0 auto 2rem;padding:clamp(1.5rem,5vw,4.5rem) clamp(1.25rem,6vw,5.5rem);box-shadow:var(--shadow);min-height:60vh}
@media(max-width:700px){[data-theme=print] .sheet{margin-bottom:0;padding:1.25rem 1rem 2rem}}
.sheet p,.sheet li{max-width:var(--w)}
.sheet .stats p,.sheet .sheet p.lede{max-width:none}

/* bars */
.bars{position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--barbg);color:var(--barfg);font-size:.875rem;line-height:1.2}
.fkeys{display:flex;overflow-x:auto;white-space:nowrap;scrollbar-width:none;border-top:1px solid #000}
.fkeys::-webkit-scrollbar{display:none}
.fk{flex:none;font:inherit;color:var(--barfg);background:none;border:0;border-right:1px solid #777;margin:0;padding:0 1.4ch;min-height:2.1rem;display:inline-flex;align-items:center;gap:1ch;text-decoration:none;cursor:pointer}
.fk kbd{font:600 .8125rem/1 inherit;font-family:inherit;background:#000;color:#aaa;padding:.2rem .6ch}
.fk:hover,.fk:focus-visible,.fk[aria-pressed=true]{background:#000;color:#aaa}
.fk:hover kbd,.fk:focus-visible kbd,.fk[aria-pressed=true] kbd{background:#aaa;color:#000}
.fk:focus-visible{outline:2px solid #fff;outline-offset:-4px}
@media(pointer:coarse){.fk{min-height:44px}}
.status{margin:0;display:flex;justify-content:space-between;gap:2ch;padding:.15rem 1ch;border-top:1px solid #000;font-size:.875rem;line-height:1.3;max-width:none}
.st-l{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}.st-r{white-space:nowrap}
.status b{color:#000;font-weight:600}.sp{display:inline-block;width:1.5ch}
@media(max-width:700px){.dp{display:none}.status .sp,.st-r{letter-spacing:0}.st-r{font-size:.8125rem}.st-l{font-size:.8125rem}}

/* reveal codes + panels */
.codes{position:fixed;left:0;right:0;bottom:var(--bars);z-index:45;max-height:36vh;overflow:auto;background:var(--blue);color:#d8d8d8;border-top:4px double #fff;font-size:.9375rem}
[data-theme=print] .codes{background:#f6f4ee;color:#151515;border-top-color:#151515}
.codes[hidden],.panel[hidden]{display:none}
.codes__bar{display:flex;gap:1ch;margin:0;padding:0 1ch;background:#aaa;color:#000;font-size:.8125rem;position:sticky;top:0}
.codes__bar .ruler{flex:1;overflow:hidden;white-space:nowrap}
.codes__bar .ruler::before{content:"▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────▲────────"}
#codes-body{padding:.4rem 1ch .6rem}
#codes-body div{max-width:none;margin:.1rem 0}
.cd{background:#aaa;color:#000;padding:0 .4ch;margin:0 .2ch;font-weight:600;white-space:nowrap}
.cd-t{color:var(--bright);font-weight:600}
.panel{position:fixed;z-index:60;left:50%;bottom:calc(var(--bars) + 1rem);transform:translateX(-50%);width:min(92vw,72ch);max-height:calc(100vh - var(--bars) - 2rem);overflow:auto;background:var(--blue);color:#d8d8d8;border:4px double #fff;padding:.25rem 2ch 1rem}
[data-theme=print] .panel{background:#f6f4ee;color:#151515;border-color:#151515;box-shadow:var(--shadow)}
.panel__t{font:600 1rem/1.5 inherit;font-family:inherit;color:var(--hi);margin:.25rem 0 .5rem;text-transform:uppercase}
.panel__f{margin:1rem 0 0;font-size:.875rem;max-width:none}
.pclose{font:inherit;background:var(--selbg);color:var(--selfg);border:0;padding:.1rem 1ch;cursor:pointer;margin-left:1ch}
.plist{list-style:none;margin:0;padding:0}.plist li{max-width:none}
.keys{display:grid;grid-template-columns:max-content 1fr;gap:.35rem 2ch;margin:0}
.keys dt{color:var(--bright);font-weight:600}.keys dd{margin:0}

/* boot */
#boot{display:none}
html.booting #boot{display:flex;flex-direction:column;position:fixed;inset:0;z-index:100;background:#000;color:#aaa;padding:1.25rem 2ch;overflow:hidden;cursor:pointer}
#boot pre{margin:0;font:inherit;line-height:1.35}
#boot .b{opacity:0;animation:bshow 0s forwards}
#boot .vt{font-size:clamp(3.5rem,14vw,6.5rem);color:var(--hi);margin:.6rem 0 .1rem}
#boot .b6{color:#ffff55}
#boot .b7{color:#fff}
.b1{animation-delay:.05s!important}.b2{animation-delay:.2s!important}.b3{animation-delay:.35s!important}.b4{animation-delay:.55s!important}.b5{animation-delay:.7s!important}.b6{animation-delay:.8s!important}.b7{animation-delay:.95s!important}
@keyframes bshow{to{opacity:1}}

/* generic document furniture */
.scr{position:relative}
.docbar{display:flex;gap:1ch;align-items:center;margin:2.5rem 0 1rem;color:var(--bright);font-weight:600;max-width:none!important;overflow:hidden;white-space:nowrap}
.docbar::after{content:"════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════";color:var(--fg);font-weight:400;overflow:hidden}
.wbox{position:relative;border:3px double var(--frame);padding:1.5rem 2ch 1.25rem;margin:1.75rem 0 1.25rem}
.wbox__t{position:absolute;top:-.85rem;left:2ch;margin:0;padding:0 1ch;background:var(--paper);color:var(--hi);font:600 1rem/1.5 inherit;font-family:inherit;text-transform:uppercase}
.eyebrow{margin:0;color:var(--mute)}
.eyebrow::before{content:"[ "}.eyebrow::after{content:" ]"}
h2,h3{font-size:1rem}

/* home: list files */
.lf-top{display:flex;justify-content:space-between;gap:2ch;margin:.5rem 0 0;max-width:none!important;color:var(--bright)}
.lf-top h2{margin:0;font:600 1rem/1.5 inherit;font-family:inherit;color:var(--bright)}
.docsum h1{font-size:clamp(2.75rem,6.5vw,5rem);color:var(--hi);margin:0 0 .75rem}
.docsum .lede{margin:.5rem 0 1rem;max-width:72ch}
.hero__count{display:block;color:var(--bright);font-weight:600;margin-bottom:.25rem}
.lf{margin-top:1.25rem}
.lf-cols,.lf-row{display:grid;grid-template-columns:14ch minmax(18ch,26ch) minmax(0,1fr) 9ch;column-gap:2ch;padding:0 1ch;max-width:none!important}
.lf-cols{margin:0;border-bottom:1px solid var(--fg);color:var(--mute)}
.lf-list{list-style:none;margin:0;padding:0}
.lf-list li{max-width:none}
.lf-row{text-decoration:none;color:var(--fg);align-items:start}
.lf-row .n{color:var(--bright);font-weight:600}
.lf-row .t{color:var(--bright)}
.lf-row.is-dir .n,.lf-row.is-dir .t{color:var(--hi)}
.lf-row.is-dir{margin-top:.75rem}
.lf-list li:first-child .lf-row.is-dir{margin-top:.25rem}
.lf-row .d{text-align:right;color:var(--mute)}
.lf-row:hover,.lf-row:focus,.lf-row[aria-current=true]{background:var(--selbg);color:var(--selfg);outline:none}
.lf-row:hover *,.lf-row:focus *,.lf-row[aria-current=true] *{color:var(--selfg)!important}
.lf-keys{margin:1.25rem 0 0;display:flex;flex-wrap:wrap;gap:.25rem 3ch;color:var(--mute);font-size:.875rem;max-width:none!important}
.lf-keys b{color:var(--bright)}
.panel .lf-row{grid-template-columns:12ch 7ch 1fr}
@media(max-width:700px){
.lf-cols{display:none}
.lf-row{grid-template-columns:minmax(0,1fr) 9ch;grid-template-areas:"n d" "t t" "s s";padding:.5rem 1ch;border-bottom:1px solid rgba(169,180,255,.25)}
.lf-row .n{grid-area:n}.lf-row .d{grid-area:d}.lf-row .t{grid-area:t}.lf-row .s{grid-area:s;color:var(--mute)}
.lf-row.is-dir{margin-top:1rem}
.panel .lf-row{grid-template-columns:auto 1fr;grid-template-areas:"n t" "s s"}
}

/* home: rules + tools */
.rules .sec-title,.tools .sec-title{font:600 1.375rem/1.3 inherit;font-family:inherit;color:var(--hi);margin:.25rem 0 1rem}
.rules .eyebrow,.tools .eyebrow{margin-bottom:.25rem}
.rules__list{list-style:none;margin:0;padding:0;display:grid;gap:1.25rem}
.rule{display:grid;grid-template-columns:5ch 1fr;column-gap:1ch}
.rule__n{color:var(--mute);grid-row:1/3}
.rule h3{margin:0;color:var(--hi);font-weight:600}
.rule p{margin:.2rem 0 0}
.tools .sec-lede{margin:0 0 1.25rem;max-width:72ch}
.trows{display:block}
.trow{display:grid;grid-template-columns:20ch minmax(0,1fr) minmax(0,1fr);column-gap:2ch;padding:.6rem 0;border-top:1px dotted var(--mute)}
.trow h3{margin:0;color:var(--hi);font-weight:600}
.trow .tcol p{margin:0}
.trow .lab{display:block;color:var(--mute);font-size:.8125rem;text-transform:uppercase;letter-spacing:.04em}
.trow .tcol:nth-of-type(1):last-child{grid-column:2/4}
.tools summary{list-style:none;cursor:pointer;margin:1.25rem 0 .5rem;color:var(--link);display:inline-block}
.tools summary::-webkit-details-marker{display:none}
.tools summary::before{content:"["}.tools summary::after{content:"]"}
.tools summary:hover{background:var(--selbg);color:var(--selfg)}
.tools details[open]>summary{margin-bottom:.5rem}
@media(max-width:900px){
.trow{display:block}.trow h3{margin-bottom:.3rem}.trow .tcol{margin:.35rem 0 0}
}
.arch-t{font:600 1.375rem/1.3 inherit;font-family:inherit;color:var(--hi);margin:.25rem 0 .5rem}.arch-here{color:var(--bright);font-weight:600}
.homelink{color:inherit;text-decoration:none}.homelink:hover{background:none;color:inherit;text-decoration:underline}
.room .st-l{cursor:pointer}.room .st-l:hover{text-decoration:underline}
.exit-q{font-size:1.25rem;color:var(--bright)}
.yn{font-weight:600}
.mail{font-weight:600;user-select:all}
.foot__row{display:flex;flex-wrap:wrap;gap:.25rem 3ch;max-width:none!important}

/* room title block, pages */
.crumb{margin:.5rem 0 1.5rem;color:var(--mute)}
.rtitle h1{font-size:clamp(3.5rem,11vw,7.5rem);color:var(--hi);margin:.25rem 0 .5rem}
.rcount{margin:0 0 1rem;color:var(--bright);font-weight:600}
.rlede{font-size:1.0625rem;max-width:68ch}
.toc{margin:1.75rem 0 0}
.toc ol{list-style:none;margin:0;padding:0;columns:3 26ch;column-gap:3ch}
.toc li{break-inside:avoid;max-width:none}
.toc a{display:block;padding:0 .5ch;text-decoration:none}
.tn{color:var(--mute)}
.toc a:hover .tn{color:var(--selfg)}
.pb{margin:2.5rem calc(-1*var(--pad)) 2rem;overflow:hidden;white-space:nowrap;line-height:1;color:var(--fg)}
[data-theme=print] .pb{margin-inline:calc(-1*clamp(1.25rem,6vw,5.5rem))}
.pb::before{content:"════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════"}
.chead{margin-bottom:1.5rem}
.ckick{margin:0 0 .25rem;display:flex;flex-wrap:wrap;gap:0 2ch;color:var(--mute);font-size:.875rem}
.ckick span+span::before{content:"· ";}
.cn{color:var(--bright);font-weight:600}
.ctitle{font:600 clamp(1.5rem,3.2vw,2.25rem)/1.2 inherit;font-family:inherit;color:var(--hi);margin:.25rem 0}
.csub{margin:0;color:var(--bright);font-weight:600}
.clede{margin:.75rem 0 0;font-size:1.0625rem;max-width:72ch}
.doc{counter-reset:fig grp}
.gdiv{counter-increment:grp;margin:0 0 1.75rem}
.gdiv__t{font:600 clamp(1.25rem,2.4vw,1.625rem)/1.25 inherit;font-family:inherit;color:var(--hi);text-transform:uppercase;margin:0 0 .5rem}
.gdiv__t::before{content:counter(grp,upper-roman) ". "}
.gdiv__p{margin:0;max-width:72ch}
.xsec .eyebrow{margin-bottom:.25rem}
.xsec__t{font:600 clamp(1.5rem,3.2vw,2.25rem)/1.2 inherit;font-family:inherit;color:var(--hi);margin:.25rem 0 1rem}
.xsec__list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.25rem 4ch}
.xsec__list>div{border-top:1px dotted var(--mute);padding-top:.5rem}
.xsec__list h3{margin:0;color:var(--hi)}.xsec__list p{margin:.25rem 0 0}
@media(max-width:800px){.xsec__list{grid-template-columns:1fr}}
.pn{display:flex;flex-wrap:wrap;gap:.5rem 4ch;font-size:1.0625rem;font-weight:600;margin:0 0 1.5rem;max-width:none!important}
.pgdn{display:inline-block}
.rfoot{color:var(--mute);font-size:.9375rem}.rfoot p{margin:.25rem 0;max-width:none}

/* case body, restyled as a document */
.cbody{display:grid;gap:1.75rem;counter-reset:none}
.cbody>*{min-width:0}
.cbody p{margin:0 0 .75rem}.cbody p:last-child{margin-bottom:0}
.cbody h3{margin:0 0 .5rem;color:var(--hi);font-weight:600;font-size:1.0625rem}
.cbody h4{margin:0 0 .25rem;color:var(--bright);font-weight:600;font-size:1rem}
.cbody ul,.cbody ol{margin:0 0 .75rem;padding:0;list-style:none;display:grid;gap:.4rem}
.cbody ul>li{padding-left:2ch;position:relative}
.cbody ul>li::before{content:"*";position:absolute;left:0;color:var(--hi)}
.cbody ol{counter-reset:li}
.cbody ol>li{counter-increment:li;padding-left:3ch;position:relative}
.cbody ol>li::before{content:counter(li) ".";position:absolute;left:0;color:var(--hi)}
.cbody code{color:var(--bright)}
.cbody dl{margin:0}.cbody dt{color:var(--bright);font-weight:600}.cbody dd{margin:0 0 .5rem}
.cbody .cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.75rem 5ch}
.cbody .block{min-width:0}
.cbody .block ul,.cbody .block ol{margin-bottom:0}
.cbody .block ul+p,.cbody .block ol+p{margin-top:.75rem}
.cbody .links{display:flex;flex-wrap:wrap;gap:.25rem 2ch;max-width:none}
.cbody .links a{text-decoration:none;font-weight:600}
.cbody .links a::before{content:"["}.cbody .links a::after{content:"]"}
.cbody .links a:hover{text-decoration:none}
.cbody .links span{color:var(--mute)}
.cbody .made{border-left:4px double var(--frame);padding:.1rem 0 .1rem 2ch;max-width:var(--w)}
.cbody .made b{display:block;color:var(--hi);text-transform:uppercase;font-size:.875rem;letter-spacing:.04em}
.cbody .note,.cbody span.note{color:var(--mute)}
.cbody .kind{color:var(--mute);font-size:.875rem;text-transform:uppercase}
.cbody .count{color:var(--bright);font-weight:600}
.cbody .logline{color:var(--bright)}

/* figure boxes */
.cbody figure{margin:0;display:flex;flex-direction:column;border:3px double var(--frame);background:var(--paper);min-width:0}
.cbody figure img,.cbody figure video{display:block;width:100%;height:auto;max-width:100%;background:#000;padding:.5rem;cursor:zoom-in}
.cbody figure video,.cbody figure a img{cursor:pointer}
.cbody figure video{cursor:auto}
.cbody figure>a{display:block}
.cbody figcaption{border-top:1px solid var(--frame);padding:.4rem 1.2ch .5rem;font-size:.875rem;line-height:1.45;color:var(--fg);max-width:none}
.cbody figcaption::before{content:"Figure " counter(fig) ": ";counter-increment:fig;color:var(--bright);font-weight:600}
.cbody figure:has(img.portrait),.cbody figure:has(video.portrait){width:fit-content;max-width:min(100%,400px)}
.cbody .shots,.cbody .grid3,.cbody .gallery,.cbody .reels,.cbody .books,.cbody .piece{display:grid;gap:1.5rem 2.5ch;align-items:start}
.cbody .shots{grid-template-columns:repeat(2,minmax(0,1fr))}
.cbody .grid3{grid-template-columns:repeat(3,minmax(0,1fr))}
.cbody .grid3>div{border-top:1px dotted var(--mute);padding-top:.5rem}
.cbody .gallery{grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem 1.5ch}
.cbody .gallery figcaption,.cbody .reels figcaption{font-size:.8125rem}
.cbody .reels{grid-template-columns:repeat(6,minmax(0,1fr));gap:1rem 1.5ch}
.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr));max-width:760px}
.cbody .reels video{aspect-ratio:9/16;object-fit:cover}
.cbody .books{grid-template-columns:repeat(2,minmax(0,1fr))}
.cbody .book{display:grid;gap:.5rem;align-content:start;border:3px double var(--frame);padding:1rem 2ch;min-width:0}
.cbody .book.lead{grid-column:1/-1;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:1.5rem 3ch}
.cbody .book .cover{width:100%;max-width:240px;height:auto;background:#000;padding:.4rem}
.cbody .lead-text{display:grid;gap:.5rem;min-width:0;align-content:start}
.cbody .piece{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)}
.cbody .piece-text{display:grid;gap:.75rem;min-width:0;align-content:start}
.cbody .piece.flip>figure{order:2}
.cbody .flow{counter-reset:step;grid-template-columns:repeat(5,minmax(0,1fr));gap:1rem 2ch}
.cbody .flow>li{counter-increment:step;padding-left:0;border-top:1px solid var(--frame);padding-top:.5rem;display:grid;gap:.25rem;align-content:start}
.cbody .flow>li::before{content:counter(step,decimal-leading-zero);position:static;color:var(--hi)}
.cbody .flow b{color:var(--hi)}
.cbody .flow span{color:var(--fg)}
.cbody .tags{display:flex;flex-wrap:wrap;gap:.25rem 1.5ch}
.cbody .tag{color:var(--mute);font-size:.875rem;text-transform:uppercase}
.cbody .tag::before{content:"[ "}.cbody .tag::after{content:" ]"}
.cbody .tag.hot{color:var(--selfg);background:var(--selbg)}
.cbody .tag.hot::before,.cbody .tag.hot::after{content:" "}
.cbody .facts{display:flex;flex-wrap:wrap;gap:.25rem 3ch;color:var(--fg)}
.cbody .facts strong{color:var(--hi)}
.cbody .sub-case{display:grid;gap:1.5rem;border-top:4px double var(--frame);padding-top:1.5rem}
.cbody .sub-case>h3{font-size:clamp(1.25rem,2.4vw,1.625rem);text-transform:uppercase}
.cbody .more{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.25rem 4ch}
.cbody .more>div{border-top:1px dotted var(--mute);padding-top:.5rem}

/* stats: a small boxed table */
.stats{display:grid;grid-template-columns:minmax(0,1fr) max-content;border:3px double var(--frame);margin:0 0 .75rem;max-width:72ch;padding:0}
.stats>div{display:contents}
.stats dt,.stats dd{margin:0;padding:.3rem 1.2ch;border-top:1px dotted var(--mute)}
.stats>div:first-child>*{border-top:0}
.stats dt{color:var(--fg)}
.stats dd{color:var(--bright);font-weight:600;text-align:right;border-left:1px dotted var(--mute)}

/* before/after slider, ported from the live pages */
.cbody .compare{position:relative;overflow:hidden;margin:.5rem;background:#000;--pos:50%;touch-action:pan-y;width:auto;max-width:100%}
.cbody .compare.portrait{max-width:360px}
.cbody .compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;max-width:none;padding:0;cursor:ew-resize}
.cbody .compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cbody .cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:3px;margin-left:-1px;background:#fff;pointer-events:none;box-shadow:0 0 0 1px #000}
.cbody .cmp-line::after{content:"\2194";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:2.5rem;height:2.5rem;background:#fff;color:#000;display:grid;place-items:center;font-weight:600}
.cbody .cmp-tag{position:absolute;top:.5rem;background:#ffff55;color:#000;padding:.1rem 1ch;font-size:.8125rem;font-weight:600;pointer-events:none}
.cbody .cmp-tag.l{left:.5rem}.cbody .cmp-tag.r{right:.5rem}
.cbody .compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.cbody .compare:focus-within{outline:3px solid var(--link);outline-offset:2px}

/* cursor + lightbox */
.has-cur::after{content:"\2588";margin-left:.5ch;font-weight:400;color:var(--bright)}
@media(prefers-reduced-motion:no-preference){.has-cur::after{animation:blink 1.06s steps(1) infinite}#boot .b7{animation:bshow 0s .95s forwards,blink 1s 1.2s steps(1) infinite}}
@keyframes blink{50%{opacity:0}}
.lb{position:fixed;inset:0;z-index:90;background:rgba(0,0,0,.88);display:grid;place-items:center;padding:1rem;cursor:zoom-out}
.lb img{max-width:96vw;max-height:calc(100vh - var(--bars) - 2rem);width:auto;height:auto;border:3px double #fff;background:#000}

/* responsive */
@media(max-width:1000px){.cbody .grid3{grid-template-columns:repeat(2,minmax(0,1fr))}.cbody .reels{grid-template-columns:repeat(3,minmax(0,1fr))}.cbody .flow{grid-template-columns:repeat(2,minmax(0,1fr))}.cbody .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:900px){.cbody .cols,.cbody .piece,.cbody .more{grid-template-columns:minmax(0,1fr)}.toc ol{columns:2 20ch}}
@media(max-width:700px){
.cbody .shots,.cbody .grid3,.cbody .books,.cbody .book.lead,.cbody .flow{grid-template-columns:minmax(0,1fr)}
.cbody .reels,.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr))}
.toc ol{columns:1}
.stats{grid-template-columns:minmax(0,1fr) max-content}
}
@media(forced-colors:active){.lf-row:focus,.lf-row[aria-current=true]{outline:2px solid Highlight}}
@media print{.bars,.codes,.panel,#boot{display:none!important}body{padding:0}}
'''

JS = r'''/* MPWP 5.1: keyboard shortcuts, List Files bar, status line, Reveal Codes, Print Preview. Plain JS. */
(function () {
  'use strict';
  var D = document, H = D.documentElement, B = D.body;
  var $ = function (s, r) { return (r || D).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || D).querySelectorAll(s)); };
  var home = B.getAttribute('data-page') === 'home';
  var store = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* boot: a 1.2 s overlay, skipped by any key or click */
  if (H.classList.contains('booting')) {
    var done = false, t;
    var end = function () {
      if (done) return; done = true; clearTimeout(t);
      H.classList.remove('booting');
      try { sessionStorage.setItem('mpwp-boot', '1'); } catch (e) {}
      D.removeEventListener('keydown', skip, true); D.removeEventListener('pointerdown', skip, true);
    };
    var skip = function (e) { e.preventDefault(); e.stopPropagation(); end(); };
    D.addEventListener('keydown', skip, true); D.addEventListener('pointerdown', skip, true);
    t = setTimeout(end, 1250);
  }

  /* bar height -> CSS var */
  var bars = $('#bars');
  var size = function () { H.style.setProperty('--bars', bars.offsetHeight + 'px'); };
  size(); addEventListener('resize', size);
  if (window.ResizeObserver) new ResizeObserver(size).observe(bars);

  /* theme: blue screen by default, Print Preview on request */
  var pbtn = $('#k-print');
  var setTheme = function (t, save) {
    H.setAttribute('data-theme', t);
    if (save) store('mpwp-theme', t);
    if (pbtn) pbtn.setAttribute('aria-pressed', t === 'print' ? 'true' : 'false');
    var m = $('meta[name="theme-color"]'); if (m) m.setAttribute('content', t === 'print' ? '#8a8a8a' : '#0a1a96');
  };
  setTheme(H.getAttribute('data-theme') === 'print' ? 'print' : 'dos', false);
  pbtn.addEventListener('click', function () { setTheme(H.getAttribute('data-theme') === 'print' ? 'dos' : 'print', true); });

  /* panels + reveal codes */
  var CD = {}; try { CD = JSON.parse($('#codes-data').textContent || '{}'); } catch (e) {}
  var cur = null, openPanel = null, lastFocus = null;
  var codes = $('#codes'), kc = $('#k-codes');
  var code = function (t) { var s = D.createElement('span'); s.className = 'cd'; s.textContent = '[' + t + ']'; return s; };
  var line = function (parts) {
    var d = D.createElement('div');
    parts.forEach(function (p) { d.appendChild(typeof p === 'string' ? D.createTextNode(p) : p); });
    $('#codes-body').appendChild(d);
  };
  var renderCodes = function () {
    var b = $('#codes-body'); b.textContent = '';
    var c = cur && CD[cur];
    if (!c) { line([code('Open Style:Directory'), ' Move the bar over a file, or scroll to a case, to see its codes ', code('HRt')]); return; }
    var t = D.createElement('span'); t.className = 'cd-t'; t.textContent = c.t;
    line([code('Open Style:Case'), code('Bold'), t, code('bold'), code('HRt')]);
    line(c.k.map(function (k) { return code('Kicker:' + k); }).concat([code('HRt')]));
    line([code('Sub:' + c.s), code('HRt')]);
    line([code('Id:' + c.id), code('Count:' + c.n), code('HRt')]);
    if (c.l.length) line(c.l.map(function (l) { return code('Link:' + l); }).concat([code('HRt')]));
  };
  var setCodes = function (on) {
    codes.hidden = !on; kc.setAttribute('aria-pressed', on ? 'true' : 'false');
    if (on) renderCodes();
    H.style.setProperty('--codes-h', on ? codes.offsetHeight + 'px' : '0px');
  };
  kc.addEventListener('click', function () { setCodes(codes.hidden); });
  var setCur = function (id) { if (id === cur) return; cur = id; if (!codes.hidden) { renderCodes(); H.style.setProperty('--codes-h', codes.offsetHeight + 'px'); } };
  var showPanel = function (id) {
    closePanel(); var p = $('#' + id); if (!p) return;
    lastFocus = D.activeElement; p.hidden = false; openPanel = p;
    var f = $('a,button', p); if (f) f.focus();
  };
  var closePanel = function () {
    if (!openPanel) return false;
    openPanel.hidden = true; openPanel = null;
    if (lastFocus && lastFocus.focus) lastFocus.focus(); return true;
  };
  $$('.pclose').forEach(function (b) { b.addEventListener('click', closePanel); });
  $('#k-help').addEventListener('click', function () { showPanel('p-help'); });
  $('#k-rooms').addEventListener('click', function (e) { e.preventDefault(); showPanel('p-rooms'); });

  /* lightbox for figures */
  var lb = null;
  var closeLb = function () { if (!lb) return false; lb.remove(); lb = null; return true; };
  D.addEventListener('click', function (e) {
    var i = e.target;
    if (i.tagName !== 'IMG' || !i.closest('.cbody') || i.closest('.compare') || i.closest('a')) return;
    lb = D.createElement('div'); lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-label', 'Enlarged figure');
    var im = D.createElement('img'); im.src = i.currentSrc || i.src; im.alt = i.alt; lb.appendChild(im);
    lb.addEventListener('click', closeLb); B.appendChild(lb);
  });

  /* before/after sliders */
  $$('.compare').forEach(function (c) {
    var r = $('input', c); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* status line + cursor */
  var secs = $$('[data-file]'), heads = $$('main h1, main h2, main h3'), curHead = null, rowFile = null;
  var stFile = $('#st-file'), stPg = $('#st-pg'), stLn = $('#st-ln'), tick = false;
  var update = function () {
    tick = false;
    var y = innerHeight * 0.35, s = secs[0], i;
    for (i = 0; i < secs.length; i++) { if (secs[i].getBoundingClientRect().top <= y) s = secs[i]; else break; }
    if (!s) return;
    var file = s.getAttribute('data-file');
    if (home && s.id === 'files' && rowFile) file = rowFile;
    var cut = file.lastIndexOf('\\') + 1; stFile.textContent = ''; var dp = D.createElement('span'); dp.className = 'dp'; dp.textContent = file.slice(0, cut); stFile.appendChild(dp); stFile.appendChild(D.createTextNode(file.slice(cut))); stPg.textContent = s.getAttribute('data-pg');
    stLn.textContent = (1 + Math.max(0, y - s.getBoundingClientRect().top) / 96).toFixed(2) + '"';
    if (!home && s.getAttribute('data-id')) setCur(s.getAttribute('data-id'));
    else if (!home) setCur(null);
    var h = heads[0], lim = innerHeight * 0.45;
    for (i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top <= lim) h = heads[i]; else break; }
    if (h !== curHead) { if (curHead) curHead.classList.remove('has-cur'); curHead = h; if (h) h.classList.add('has-cur'); }
  };
  var req = function () { if (!tick) { tick = true; requestAnimationFrame(update); } };
  addEventListener('scroll', req, { passive: true }); addEventListener('resize', req); update();

  /* home: List Files bar (roving tabindex, aria-current follows focus) */
  var rows = home ? $$('.lf-list .lf-row') : [], idx = 0, touched = false;
  var go = function (n, focus) {
    if (!rows.length) return;
    n = Math.max(0, Math.min(rows.length - 1, n));
    rows.forEach(function (r, k) { r.tabIndex = k === n ? 0 : -1; if (k === n) r.setAttribute('aria-current', 'true'); else r.removeAttribute('aria-current'); });
    idx = n; if (touched) rowFile = rows[n].getAttribute('data-path'); setCur(rows[n].getAttribute('data-id'));
    if (focus) rows[n].focus();
    req();
  };
  if (rows.length) {
    go(0, false);
    var nextDir = function (from, dir) { for (var k = from + dir; k >= 0 && k < rows.length; k += dir) if (rows[k].classList.contains('is-dir')) return k; return -1; };
    $('.lf-list').addEventListener('focusin', function (e) { var k = rows.indexOf(e.target.closest('.lf-row')); touched = true; if (k >= 0) go(k, false); });
    $('.lf-list').addEventListener('mouseover', function (e) {
      var r = e.target.closest('.lf-row'); if (!r || !matchMedia('(hover:hover)').matches) return;
      var k = rows.indexOf(r); touched = true; if (k >= 0 && k !== idx) { go(k, false); r.focus({ preventScroll: true }); }
    });
    $('.lf-list').addEventListener('keydown', function (e) {
      var k = e.key, n = null;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (k === 'ArrowDown') n = idx + 1; else if (k === 'ArrowUp') n = idx - 1;
      else if (k === 'Home') n = 0; else if (k === 'End') n = rows.length - 1;
      else if (k === 'PageDown') n = idx + 8; else if (k === 'PageUp') n = idx - 8;
      else if (k === 'Tab') { var d = nextDir(idx, e.shiftKey ? -1 : 1); if (d < 0) return; n = d; }
      if (n === null) return;
      e.preventDefault(); go(n, true);
    });
  }

  if (!home) { stFile.title = 'Back to the homepage'; stFile.addEventListener('click', function () { location.href = $('#k-home').href; }); }

  /* shortcuts: letters only, never while typing, no F-keys */
  D.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return;
    var t = e.target;
    if (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) return;
    var k = e.key;
    if (k === 'Escape') { if (closeLb() || closePanel()) return; if (!codes.hidden) { setCodes(false); return; } if (!home) location.href = $('#k-home').href; return; }
    if (k === '?') { showPanel('p-help'); e.preventDefault(); return; }
    switch (k.toLowerCase()) {
      case 'l':
        if (home) { $('#files').scrollIntoView(); if (rows.length) rows[idx].focus({ preventScroll: true }); } else location.href = $('#k-list').href;
        break;
      case 'o': showPanel('p-rooms'); break;
      case 'r': setCodes(codes.hidden); break;
      case 'p': pbtn.click(); break;
      case 'h': location.href = $('#k-home').href; break;
      case 'x': location.href = $('#k-exit').href; break;
    }
  });
  addEventListener('resize', function () { if (!codes.hidden) H.style.setProperty('--codes-h', codes.offsetHeight + 'px'); });
})();
'''


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'd.css'), 'w', encoding='utf-8').write(CSS)
    open(os.path.join(OUT, 'd.js'), 'w', encoding='utf-8').write(JS)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(home_page())
    for idx, r in enumerate(ROOMS):
        os.makedirs(os.path.join(OUT, r['slug']), exist_ok=True)
        open(os.path.join(OUT, r['slug'], 'index.html'), 'w', encoding='utf-8').write(room_page(idx, r))
    print('wrote mockup-d: home + %d rooms, %d case files' % (len(ROOMS), n_files))


if __name__ == '__main__':
    main()


# style switcher (see add_switcher.py)
import runpy as _rp
import os as _os; _rp.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "add_switcher.py"), run_name="__main__")
