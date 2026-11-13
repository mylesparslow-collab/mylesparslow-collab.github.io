#!/usr/bin/env python3
"""Build mockup E, "Case File": the portfolio as a court case file.

    python3 -I themed/render_e.py

Reads themed/live.json and writes mockup-e/index.html, mockup-e/<room>/index.html,
mockup-e/e.css and mockup-e/e.js. Stdlib only. Safe to re-run.

Home: a pleading-style caption, a stack of five manila folders, an exhibit index, stipulations,
Schedule A, a sticky note, proof of service. Rooms: a folder-tab row over a sheet of pleading paper,
every case an exhibit with a sticker and a Bates number.

Path rules: body markup is written for a room page at the site root, so from
mockup-e/<room>/ every "../" gains one more "../".
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-e')
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
YEAR = '2026'
unesc = html.unescape
esc = lambda t: html.escape(t, quote=True)
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

# ------------------------------------------------------------------ helpers


def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b):
    """Deepen relative paths by one level; outbound/demo links open in a new tab."""
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
    return unesc(re.sub(r'<[^>]+>', '', t))


# ------------------------------------------------------------------ data model
total = 0
for ri, r in enumerate(ROOMS, 1):
    r['n'] = ri
    r['plain'] = unesc(r['title'])
    cases = [i for i in r['items'] if i['kind'] == 'case']
    r['ncase'] = len(cases)
    total += len(cases)
    for it in cases:
        ci = int(it['count'].split('/')[0])
        it['ci'] = ci
        it['ex'] = '%s-%02d' % (r['letter'], ci)
        it['bates'] = 'PARSLOW-%04d%02d' % (ri, ci)
TOTAL_CASES = total

ICON_HOUSE = '<svg class="ico" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true" focusable="false"><path d="M2 9.5 10 2.5l8 7M4.5 8.5V17h4v-4.5h3V17h4V8.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"/></svg>'
ICON_THEME = ('<svg class="ico ico-sun" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="3.6" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M10 2v2.2M10 15.8V18M2 10h2.2M15.8 10H18M4.3 4.3l1.5 1.5M14.2 14.2l1.5 1.5M4.3 15.7l1.5-1.5M14.2 5.8l1.5-1.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>'
              '<svg class="ico ico-moon" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true" focusable="false"><path d="M16.5 12.2A7 7 0 0 1 7.8 3.5a7 7 0 1 0 8.7 8.7Z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>')

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&display=swap">')


def head_script(home):
    s = ("<script>(function(){var d=document.documentElement,t;d.classList.add('js');"
         "try{t=localStorage.getItem('cf-theme')}catch(e){}"
         "if(t!=='dark'&&t!=='light')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';"
         "d.setAttribute('data-theme',t);")
    if home:
        s += ("var M=@@MAP@@,h=location.hash.slice(1);"
              "if(h&&M[h]){location.replace(M[h]+'/index.html'+(h==='g-'+M[h]?'':'#'+h));return}")
    s += "})()</script>"
    if home:
        s = s.replace('@@MAP@@', HOME['redirect_map'])
    return s


def tabrow(depth, current):
    """Manila folder-tab row. current: None (home), or the room slug."""
    up = '../' * depth
    tabs = ['<a class="tab tab--home%s" href="%sindex.html"%s>%s<span>Home</span></a>'
            % (' is-cur' if current is None else '', up, ' aria-current="page"' if current is None else '', ICON_HOUSE)]
    for r in ROOMS:
        cur = current == r['slug']
        if cur:
            tabs.append('<a class="tab is-cur" href="%sindex.html" aria-current="page" title="Close this folder (Esc)"><b>%s</b><span class="tab__n"> %s</span><span class="sr"> (current folder; select to return Home)</span></a>'
                        % (up, r['letter'], r['short']))
        else:
            tabs.append('<a class="tab" href="%s%s/index.html"><b>%s</b><span class="tab__n"> %s</span></a>' % (up, r['slug'], r['letter'], r['short']))
    return ('<header class="tabrow"><nav class="tabs" aria-label="Folders">%s</nav>'
            '<button class="themebtn needs-js" type="button" id="themebtn" aria-pressed="false" aria-label="Dark desk">%s<span class="themebtn__t">Desk</span></button></header>'
            % (''.join(tabs), ICON_THEME))


def page_shell(title, desc, depth, page, inner, current):
    up = '../' * depth
    return """<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="@@DESC@@">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#d9cfbf">
<title>@@TITLE@@</title>
<link rel="icon" href="data:,">
@@HEAD@@
@@FONTS@@
<link rel="stylesheet" href="@@UP@@e.css">
</head>
<body class="@@PAGE@@" data-page="@@PAGE@@">
<a class="skip" href="#main">Skip to the content</a>
@@TABS@@
@@INNER@@
<script src="@@UP@@e.js" defer></script>
</body>
</html>
""".replace('@@DESC@@', esc(desc)).replace('@@TITLE@@', title).replace('@@HEAD@@', head_script(page == 'home')) \
        .replace('@@FONTS@@', FONTS).replace('@@UP@@', up).replace('@@PAGE@@', page) \
        .replace('@@TABS@@', tabrow(depth, current)).replace('@@INNER@@', inner)


def stamp(uid, ring_top, ring_bottom, centre, centre_size=38, klass='stamp', tfs=25, tsp=5, bfs=17, bsp=3):
    return """<svg class="@@K@@" viewBox="0 0 200 200" aria-hidden="true" focusable="false">
<defs><filter id="rough-@@U@@" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.2"/></filter>
<path id="top-@@U@@" d="M 28,100 a 72,72 0 0 1 144,0"/><path id="bot-@@U@@" d="M 22,100 a 78,78 0 0 0 156,0"/></defs>
<g filter="url(#rough-@@U@@)" fill="currentColor" stroke="currentColor">
<circle cx="100" cy="100" r="94" fill="none" stroke-width="5"/><circle cx="100" cy="100" r="86" fill="none" stroke-width="1.5"/><circle cx="100" cy="100" r="54" fill="none" stroke-width="1.5"/>
<text font-size="@@TF@@" font-weight="700" letter-spacing="@@TS@@" stroke="none"><textPath href="#top-@@U@@" startOffset="50%" text-anchor="middle">@@T@@</textPath></text>
<text font-size="@@BF@@" font-weight="700" letter-spacing="@@BS@@" stroke="none"><textPath href="#bot-@@U@@" startOffset="50%" text-anchor="middle" dominant-baseline="hanging">@@B@@</textPath></text>
<text x="100" y="@@Y@@" font-size="@@S@@" font-weight="700" text-anchor="middle" stroke="none">@@C@@</text>
<path d="M28 100h14M158 100h14" stroke-width="3"/>
</g></svg>""".replace('@@K@@', klass).replace('@@U@@', uid).replace('@@T@@', ring_top).replace('@@B@@', ring_bottom) \
        .replace('@@TF@@', str(tfs)).replace('@@TS@@', str(tsp)).replace('@@BF@@', str(bfs)).replace('@@BS@@', str(bsp)).replace('@@C@@', centre).replace('@@S@@', str(centre_size)).replace('@@Y@@', str(100 + centre_size * 0.34))


# ------------------------------------------------------------------ home
def tools_table(t):
    """Turn the tools rows into a real table (Schedule A)."""
    def row(m):
        name = re.search(r'<h3>(.*?)</h3>', m.group(0), re.S).group(1)
        cols = re.findall(r'<div class="tcol">(.*?)</div>', m.group(0), re.S)
        return '<tr><th scope="row"><h3>%s</h3></th>%s</tr>' % (name, ''.join('<td><div class="tcol">%s</div></td>' % c for c in cols))
    t = re.sub(r'<article class="trow">.*?</article>', row, t, flags=re.S)
    t = t.replace('<div class="trows">', '<table class="trows"><tbody>')
    # close each table: the </div> that ended the trows wrapper follows the last </tr>
    t = re.sub(r'</tr></div>', '</tr></tbody></table>', t)
    return t


def home_page():
    h = HOME['hero_html']
    lede = re.search(r'<p class="lede">.*?</p>', h, re.S).group(0)
    stats = re.search(r'<dl class="stats">.*?</dl>', h, re.S).group(0)

    # folders
    folders = []
    for r in ROOMS:
        cases = [i for i in r['items'] if i['kind'] == 'case'][:3]
        lines = ''.join('<span class="ix"><i>%s</i><em>%s</em><u></u></span>' % (c['ex'], c['title']) for c in cases)
        folders.append("""<li style="--i:@@I@@"><a class="folder" href="@@S@@/index.html" style="--i:@@I@@" aria-label="Open folder @@N@@: @@T@@, @@C@@ exhibits">
<span class="folder__tab" aria-hidden="true"><b>@@L@@</b> &middot; @@SH@@ &middot; @@C@@</span>
<span class="folder__body"><span class="folder__idx" aria-hidden="true">@@LINES@@</span>
<span class="folder__meta" aria-hidden="true"><span>Folder @@N@@ of 5</span><span>@@CT@@</span><span class="folder__open">Open folder &rarr;</span></span></span></a></li>"""
                       .replace('@@I@@', str(r['n'] - 1)).replace('@@S@@', r['slug']).replace('@@N@@', str(r['n'])).replace('@@T@@', esc(r['plain']))
                       .replace('@@C@@', str(r['ncase'])).replace('@@L@@', r['letter']).replace('@@SH@@', r['short']).replace('@@LINES@@', lines)
                       .replace('@@CT@@', r['count']))

    # exhibit index
    rows = []
    for r in ROOMS:
        rows.append('<tr class="fold"><th scope="colgroup" colspan="3"><a href="%s/index.html">Folder %d &middot; %s &middot; %d exhibits</a></th></tr>'
                    % (r['slug'], r['n'], r['title'], r['ncase']))
        for it in r['items']:
            if it['kind'] != 'case':
                continue
            rows.append('<tr><td class="exno">%s</td><th scope="row"><a href="%s/index.html#%s">%s</a></th><td class="exsub">%s</td></tr>'
                        % (it['ex'], r['slug'], it['id'], it['title'], it['sub']))

    rules = HOME['rules_html']
    tools = tools_table(HOME['tools_html'])
    foot_links = re.findall(r'<a href="(https://[^"]+)">([^<]+)</a>', HOME['foot_html'])
    gh = [l for l in foot_links if 'github' in l[0]][0]
    lp = [l for l in foot_links if 'legal' in l[0]][0]

    inner = """<main id="main"><div class="desk">
<span id="top"></span>
<section class="sheet pleading caption-sheet" aria-labelledby="h-caption">
<div class="nums" aria-hidden="true"></div>
<div class="caption">
<div class="caption__l"><h1 id="h-caption"><span class="c1">In the matter of</span> <span class="c2">Myles Parslow,</span> <span class="c3">who makes things with AI</span></h1></div>
<div class="caption__p" aria-hidden="true">)<br>)<br>)<br>)<br>)</div>
<div class="caption__r"><p class="caseno">Case No. MP-2026-@@NN@@</p><p class="caption__t">Portfolio of Exhibits</p><p class="caption__c">@@N@@ exhibits &middot; 5 folders</p></div>
</div>
<div class="statement">
<div class="statement__t"><h2 class="doc-h">Statement</h2>@@LEDE@@</div>
<div class="findings"><h2 class="doc-h">Findings</h2>@@STATS@@</div>
</div>
<a class="stampbtn" href="#folders" aria-label="Open the file: jump to the five folders">@@STAMPBTN@@</a>
<p class="hand note-start" aria-hidden="true">start here &rarr;</p>
</section>

<section class="stack-sec" id="folders" aria-labelledby="h-folders">
<h2 class="slip" id="h-folders">The file &middot; five folders</h2>
<ol class="stack">@@FOLDERS@@</ol>
<p class="hand note-pick" aria-hidden="true">pick a folder, any folder</p>
</section>

<section class="sheet" id="exhibits" aria-labelledby="h-index">
<h2 class="doc-cap" id="h-index">Index of exhibits</h2>
<table class="extable"><caption class="sr">All @@N@@ exhibits, by folder</caption>
<thead><tr><th scope="col">Exhibit</th><th scope="col">Title</th><th scope="col">Description</th></tr></thead>
<tbody>@@ROWS@@</tbody></table>
</section>

<div class="sheet stip"><h2 class="doc-cap">Stipulations</h2>@@RULES@@</div>

<div class="sheet sched"><h2 class="doc-cap">Schedule A</h2>@@TOOLS@@</div>

<aside class="sticky" aria-label="Style archive">
<p class="sticky__h hand">You&rsquo;re looking at: Case File</p>
<p><strong>Style archive.</strong> This site is also a running design experiment. Each version renders the same @@N@@ case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. <a href="../styles/index.html"><strong>See every version &rarr;</strong></a></p>
</aside>

<footer class="sheet pos" id="contact" aria-labelledby="h-pos">
<h2 class="doc-cap">Proof of service</h2>
<h3 class="pos__h" id="h-pos">Say hello.</h3>
<p>I, Myles Parslow, declare that I can be served by email, which I read, at:</p>
<p class="pos__mail"><a class="mail" href="mailto:@@M@@">@@M@@</a></p>
<p class="pos__row"><a href="@@GH@@" target="_blank" rel="noopener">@@GHT@@</a> <a href="@@LP@@" target="_blank" rel="noopener">@@LPT@@</a> <a href="#top">Back to top &uarr;</a></p>
<p class="pos__sig"><span class="hand sig" aria-hidden="true">Myles Parslow</span><span class="pos__by">Myles Parslow &middot; Made with AI</span></p>
<div class="stamp-wrap" aria-hidden="true">@@RECEIVED@@</div>
</footer>
</div></main>""" \
        .replace('@@NN@@', '%03d' % total).replace('@@N@@', str(total)).replace('@@LEDE@@', lede).replace('@@STATS@@', stats).replace('@@FOLDERS@@', ''.join(folders)) \
        .replace('@@ROWS@@', ''.join(rows)).replace('@@RULES@@', rules).replace('@@TOOLS@@', tools).replace('@@M@@', MAIL) \
        .replace('@@GH@@', gh[0]).replace('@@GHT@@', gh[1]).replace('@@LP@@', lp[0]).replace('@@LPT@@', lp[1]) \
        .replace('@@STAMPBTN@@', stamp('btn', 'OPEN THE FILE', 'PRESS TO BEGIN', '&darr;', 54, 'stamp stamp--btn', 17, 2, 13, 2)) \
        .replace('@@RECEIVED@@', stamp('rec', 'RECEIVED', 'MP-2026-%03d' % total, YEAR, 38, 'stamp stamp--rec'))
    return page_shell('Case File · Myles Parslow Portfolio', 'Myles Parslow makes things with AI: software for law firms and businesses, novels, games and reference works. %d exhibits in five folders.' % total,
                      0, 'home', inner, None)


# ------------------------------------------------------------------ room pages
def group_html(g, n):
    t = re.search(r'gdiv__t">(.*?)</h2>', g['html'], re.S).group(1)
    p = re.search(r'gdiv__p">(.*?)</p>', g['html'], re.S).group(1)
    return ('<div class="gdiv count" id="%s"><p class="count-n">Count %s</p><h2 class="gdiv__t">%s</h2><p class="gdiv__p">%s</p></div>'
            % (g['id'], ROMAN[n], t, p))


def room_page(idx, r):
    nxt = ROOMS[idx + 1] if idx + 1 < len(ROOMS) else None
    cases = [i for i in r['items'] if i['kind'] == 'case']
    docket = ''.join('<li><a href="#%s"><span class="dn">%s</span> %s</a></li>' % (c['id'], c['ex'], c['title']) for c in cases)
    parts = []
    gn = 0
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            parts.append(group_html(it, gn))
            gn += 1
        elif k == 'case':
            kick = '; '.join(x for x in it['kickers'] if x.strip())
            parts.append("""<article class="exhibit" id="@@ID@@" aria-labelledby="t-@@ID@@">
<p class="sticker">Exhibit @@EX@@</p>
<header class="ehead"><p class="ekick"><span class="ecount">@@CN@@</span> Re: @@K@@</p>
<h2 class="etitle" id="t-@@ID@@">@@T@@</h2>
<p class="esub">@@S@@</p>
<p class="elede">@@L@@</p></header>
<div class="cbody">
@@B@@
</div>
<p class="bates" aria-label="Bates number @@BA@@">@@BA@@</p>
</article>""".replace('@@ID@@', it['id']).replace('@@EX@@', it['ex']).replace('@@CN@@', it['count']).replace('@@K@@', kick)
                         .replace('@@T@@', it['title']).replace('@@S@@', it['sub']).replace('@@L@@', it['lede'])
                         .replace('@@B@@', fix_body(it['body_html']).strip()).replace('@@BA@@', it['bates']))
        elif k == 'extra':
            parts.append(it['html'])
    if nxt:
        nav = '<a class="nexttab" href="../%s/index.html"><span>Next folder &rarr;</span> <b>%s</b> %s</a>' % (nxt['slug'], nxt['letter'], nxt['short'])
    else:
        nav = '<a class="nexttab" href="../index.html"><span>Close the file &rarr;</span> Home</a>'
    sheet = """<main id="main"><div class="desk">
<article class="sheet pleading room" id="top" aria-label="@@PL@@ folder">
<div class="nums" aria-hidden="true"></div>
<header class="rcaption">
<h1 class="rcaption__t">In re: <span>@@T@@</span></h1>
<p class="rcaption__n">@@EY@@ &middot; @@NC@@ exhibits</p>
<p class="rlede">@@LEDE@@</p>
<nav class="docket" aria-label="Exhibits in this folder"><p class="docket__h">Docket &middot; @@CT@@</p><ol>@@DOCKET@@</ol></nav>
<p class="hand note-ex" aria-hidden="true">exhibits follow &darr;</p>
</header>
@@PARTS@@
<nav class="nextrow" aria-label="Next folder">@@NAV@@ <a class="backhome" href="../index.html">Back to the stack</a></nav>
<footer class="rfoot"><p>Served by email: <a class="mail" href="mailto:@@M@@">@@M@@</a> &middot; <a href="https://github.com/mylesparslow-collab" target="_blank" rel="noopener">GitHub</a> &middot; <a href="https://mylesparslow.com/legal-portfolio/" target="_blank" rel="noopener">Legal portfolio</a> &middot; <a href="#top">Back to top &uarr;</a></p>
<p>Myles Parslow &middot; Made with AI</p></footer>
</article>
</div></main>""".replace('@@PL@@', esc(r['plain'])).replace('@@T@@', r['title']).replace('@@EY@@', r['eyebrow']).replace('@@NC@@', str(r['ncase'])) \
        .replace('@@LEDE@@', r['lede']).replace('@@CT@@', r['count']).replace('@@DOCKET@@', docket).replace('@@PARTS@@', '\n'.join(parts)) \
        .replace('@@NAV@@', nav).replace('@@M@@', MAIL)
    return page_shell('%s · Case File · Myles Parslow Portfolio' % esc(r['plain']), strip_tags(r['lede']), 1, 'room', sheet, r['slug'])


# ------------------------------------------------------------------ css + js
NUMS = '\\A '.join(str(n) for _ in range(90) for n in range(1, 29))

CSS = r'''/* Case File: the portfolio as a court case file. Original styling; no trademarks. */
:root{--desk:#d9cfbf;--deskink:#2a2118;--deskmute:#5a4d3d;--paper:#fffdf6;--ink:#1d1b18;--inkmute:#5a544a;--manila:#e8d3a1;--manila-edge:#cdb47c;--manila-hi:#f1e1b8;--red:#c8463d;--sticker:#f6d23c;--hl:#fff27a;--stamp:#b8322a;--rule:rgba(70,100,150,.14);
  --fs:18px;--lh:calc(var(--fs)*1.6);--tabh:48px;--serif:"Libre Caslon Text",Georgia,"Times New Roman",serif;--hand:Caveat,"Segoe Script",cursive;
  --ease:cubic-bezier(.2,.8,.2,1);--press:cubic-bezier(.34,1.56,.64,1);--shadow-p:0 1px 0 rgba(0,0,0,.08),0 2px 3px rgba(60,40,20,.18),0 18px 34px -14px rgba(60,40,20,.5);color-scheme:light}
:root[data-theme=dark]{--desk:#2a1e16;--deskink:#eadfcc;--deskmute:#b9a88f;--shadow-p:0 1px 0 rgba(0,0,0,.4),0 3px 6px rgba(0,0,0,.45),0 22px 40px -14px rgba(0,0,0,.8);color-scheme:dark}
@media(prefers-color-scheme:dark){:root:not([data-theme]){--desk:#2a1e16;--deskink:#eadfcc;--deskmute:#b9a88f;--shadow-p:0 1px 0 rgba(0,0,0,.4),0 3px 6px rgba(0,0,0,.45),0 22px 40px -14px rgba(0,0,0,.8)}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-padding-top:calc(var(--tabh) + 24px)}
body{margin:0;background-color:var(--desk);color:var(--deskink);font:400 var(--fs)/1.6 var(--serif);overflow-wrap:break-word;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' seed='7'/%3E%3CfeColorMatrix values='0 0 0 0 .25 0 0 0 0 .17 0 0 0 0 .1 0 0 0 .09 0'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E"),linear-gradient(100deg,rgba(255,255,255,.05),rgba(0,0,0,.05) 50%,rgba(255,255,255,.04))}
:root[data-theme=dark] body{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' seed='7'/%3E%3CfeColorMatrix values='0 0 0 0 .9 0 0 0 0 .7 0 0 0 0 .5 0 0 0 .05 0'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E"),repeating-linear-gradient(92deg,rgba(0,0,0,.18) 0 3px,rgba(255,255,255,.012) 3px 9px,rgba(0,0,0,.1) 9px 11px,transparent 11px 26px)}
::selection{background:var(--hl);color:var(--ink)}
a{color:inherit;text-underline-offset:.18em;text-decoration-thickness:1px}
:focus-visible{outline:3px solid #1f5fbf;outline-offset:3px;border-radius:2px}
:root[data-theme=dark] :focus-visible{outline-color:#ffd96a}
.sheet :focus-visible,.folder:focus-visible{outline-color:#1f5fbf}
img,video{max-width:100%;height:auto}
.sr{position:absolute!important;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0;padding:0}
.skip{position:absolute;left:-999px;top:8px;z-index:200;background:var(--sticker);color:var(--ink);padding:.5rem 1rem;font-weight:700}
.skip:focus{left:8px}
.needs-js{display:none}.js .needs-js{display:inline-flex}
.hand{font-family:var(--hand);font-weight:700;letter-spacing:0}

/* ------------------------------------------------------------ tab row */
.tabrow{position:sticky;top:0;z-index:60;display:flex;align-items:flex-end;justify-content:space-between;gap:12px;height:var(--tabh);padding:0 clamp(8px,2vw,28px);background:var(--desk);border-bottom:4px solid var(--manila-edge);box-shadow:0 6px 12px -8px rgba(0,0,0,.45)}
.tabs{display:flex;align-items:flex-end;min-width:0;overflow-x:auto;scrollbar-width:none;padding:0 6px;margin:0 -6px}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:none;display:inline-flex;align-items:center;gap:.4em;height:34px;margin-right:-4px;padding:0 18px 0 16px;background:var(--manila-edge);color:var(--ink);text-decoration:none;font-weight:700;font-size:13.5px;letter-spacing:.04em;text-transform:uppercase;border-radius:10px 10px 0 0;border:1px solid #b79c64;border-bottom:0;position:relative;z-index:1;transition:transform .25s var(--ease),background-color .25s var(--ease)}
.tab:hover{transform:translateY(-3px);background:#dcc58d}
.tab:focus-visible{outline-offset:-3px;z-index:6}
.tab.is-cur{height:42px;background:var(--manila);z-index:5;margin-bottom:-4px;padding-bottom:4px;box-shadow:inset 0 3px 0 var(--manila-hi)}
.tab.is-cur:hover{transform:none}
.tab b{font-weight:700}
.tab--home{padding-right:16px}
.ico{flex:none}
.themebtn{flex:none;align-items:center;gap:7px;height:30px;margin-bottom:6px;padding:0 12px;border:1.5px solid var(--manila-edge);border-radius:99px;background:transparent;color:var(--deskink);font:700 12.5px/1 var(--serif);letter-spacing:.06em;text-transform:uppercase;cursor:pointer;transition:background-color .2s var(--ease)}
.themebtn:hover{background:rgba(205,180,124,.28)}
.ico-moon{display:none}
:root[data-theme=dark] .ico-sun{display:none}:root[data-theme=dark] .ico-moon{display:inline}
@media(max-width:700px){
  .tab{padding:0 11px;font-size:13px}
  .tab:not(.is-cur):not(.tab--home) .tab__n{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .tab--home span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .themebtn__t{display:none}.themebtn{padding:0 9px}
}

/* ------------------------------------------------------------ desk + sheets */
.desk{max-width:1060px;margin:0 auto;grid-template-columns:minmax(0,1fr);padding:clamp(28px,5vw,64px) clamp(10px,3vw,32px) 90px;display:grid;gap:clamp(36px,6vw,72px)}
.sheet{position:relative;isolation:isolate;background:var(--paper);color:var(--ink);box-shadow:var(--shadow-p);padding:clamp(26px,4.5vw,56px) clamp(18px,5vw,64px) clamp(28px,4.5vw,56px);min-width:0}
.sheet a{color:var(--ink)}
.sheet h1,.sheet h2,.sheet h3,.sheet h4{font-family:var(--serif)}
.doc-cap{margin:0 0 1.2em;text-align:center;font:700 clamp(17px,2vw,20px)/1.3 var(--serif);letter-spacing:.22em;text-transform:uppercase;padding-bottom:.55em;border-bottom:3px double var(--ink)}
.doc-h{margin:0 0 .6em;font:700 15px/1.3 var(--serif);letter-spacing:.14em;text-transform:uppercase;border-bottom:1px solid var(--ink);padding-bottom:.3em}
.slip{justify-self:start;margin:0 0 18px;padding:7px 16px 6px;background:var(--paper);color:var(--ink);font:700 15px/1.3 var(--serif);letter-spacing:.14em;text-transform:uppercase;box-shadow:var(--shadow-p);transform:rotate(-.6deg)}

/* pleading paper: a double red rule on the left, line numbers, faint rules on the line grid */
.pleading{--pt:calc(var(--lh)*2);--lm:clamp(58px,9vw,98px);padding:var(--pt) clamp(18px,5vw,64px) calc(var(--lh)*2) var(--lm);
  isolation:isolate}
.pleading::before{content:"";position:absolute;top:0;bottom:0;left:calc(var(--lm) - 22px);width:6px;border-left:2px solid var(--red);border-right:2px solid var(--red);pointer-events:none}
.pleading::after{content:"";position:absolute;top:0;bottom:0;right:26px;width:0;border-right:1px solid rgba(200,70,61,.55);pointer-events:none}
.nums{position:absolute;z-index:-1;left:0;right:0;top:var(--pt);bottom:0;overflow:hidden;pointer-events:none;user-select:none;-webkit-user-select:none;background-image:linear-gradient(to bottom,transparent calc(var(--lh) - 1px),var(--rule) calc(var(--lh) - 1px));background-size:100% var(--lh)}
.nums::before{content:"@@NUMS@@";position:absolute;left:0;top:0;bottom:0;width:calc(var(--lm) - 30px);overflow:hidden;text-align:right;color:#9a7a76;font:400 13px/var(--lh) var(--serif);font-variant-numeric:tabular-nums;white-space:pre}
@media(max-width:640px){
  :root{--fs:17px}
  .pleading{--lm:50px;padding-right:18px}
  .pleading::after{display:none}
  .nums{font-size:11px}
}

/* settle-in: a 1-2px drop and a tiny rotation, once */
@media(prefers-reduced-motion:no-preference){
  .js .sheet:not(.in){transform:translateY(-2px)}
  .js .sheet:not(.in):not(.room){transform:translateY(-2px) rotate(.25deg)}
  .js .sheet{transition:transform .7s var(--ease)}
  .js .sticker{transform:scale(1.08) rotate(-2deg);opacity:0}
  .js .exhibit.in .sticker,.js .exhibit:target .sticker{animation:press .55s var(--press) both}
  @keyframes press{0%{transform:scale(1.08) rotate(-2deg);opacity:0}30%{opacity:1}100%{transform:scale(1) rotate(-2deg);opacity:1}}
  .js .stamp--rec{transform:scale(1.08) rotate(-12deg);opacity:0}
  .js .pos.in .stamp--rec{animation:press-s .6s var(--press) .15s both}
  @keyframes press-s{0%{transform:scale(1.08) rotate(-12deg);opacity:0}30%{opacity:.9}100%{transform:scale(1) rotate(-12deg);opacity:.9}}
}

/* ------------------------------------------------------------ home: caption */
.caption-sheet{padding-bottom:calc(var(--lh)*5)}
.caption{display:grid;grid-template-columns:minmax(0,1.25fr) 34px minmax(0,1fr);align-items:stretch;border-bottom:2px solid var(--ink);padding-bottom:var(--lh);margin-bottom:var(--lh)}
.caption h1{margin:0;font:700 clamp(21px,3.3vw,31px)/1.3 var(--serif);letter-spacing:.04em;text-transform:uppercase;display:grid;gap:.15em}
.caption h1 .c1{font-size:.62em;letter-spacing:.14em;font-weight:400}
.caption h1 .c3{font-size:.62em;font-style:italic;text-transform:none;letter-spacing:.02em;font-weight:400}
.caption__p{font:400 clamp(26px,3.5vw,36px)/1.15 var(--serif);text-align:center;color:var(--ink)}
.caption__r{display:grid;align-content:start;gap:.25em;padding-left:.3em}
.caption__r p{margin:0;font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:clamp(15px,1.7vw,17px)}
.caption__r .caseno{font-size:.85em;font-weight:400}
.caption__r .caption__t{font-size:clamp(19px,2.6vw,25px);line-height:1.2}
.caption__r .caption__c{font-weight:400;font-size:.85em}
.statement{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:clamp(22px,4vw,56px);align-items:start}
.statement p.lede{margin:0 0 var(--lh);max-width:34em}
.hero__count{display:block;margin-bottom:.4em;font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:.82em}
.findings .doc-h{margin-bottom:.8em}
.note-start{position:absolute;right:clamp(130px,16vw,190px);bottom:48px;margin:0;font-size:28px;color:var(--stamp);transform:rotate(-4deg);white-space:nowrap}
.stampbtn{position:absolute;right:clamp(14px,3vw,40px);bottom:clamp(14px,3vw,34px);width:clamp(96px,12vw,128px);aspect-ratio:1;color:var(--stamp);transform:rotate(-8deg);transition:transform .35s var(--press);display:block}
.stampbtn:hover,.stampbtn:focus-visible{transform:rotate(-4deg) scale(1.06)}
.stamp{width:100%;height:100%;display:block;mix-blend-mode:multiply;font-family:var(--serif);color:var(--stamp)}
.stampbtn .stamp text,.stamp text{fill:currentColor}
@media(max-width:700px){
  .caption{grid-template-columns:minmax(0,1fr) 22px minmax(0,.95fr)}
  .statement{grid-template-columns:minmax(0,1fr)}
  .note-start{display:none}
}
@media(max-width:480px){
  .caption{grid-template-columns:minmax(0,1fr);}
  .caption__p{display:none}
  .caption__r{padding:var(--lh) 0 0;margin-top:var(--lh);border-top:1px solid var(--ink)}
}

/* findings box (home and case bodies) */
.stats{margin:0 0 var(--lh);border:1.5px solid var(--ink);border-top:4px double var(--ink);display:block;background:rgba(255,253,246,.7)}
.findings .stats::before{display:none}
.stats::before{content:"Findings";display:block;padding:.2em .8em;border-bottom:1px solid var(--ink);font:700 12px/1.6 var(--serif);letter-spacing:.16em;text-transform:uppercase;background:var(--manila-hi)}
.stats>div{display:grid;grid-template-columns:minmax(6.2em,max-content) minmax(0,1fr);gap:.2em 1em;align-items:baseline;padding:.45em .8em;border-top:1px solid rgba(29,27,24,.35);max-width:none}
.stats>div:first-of-type{border-top:0}
.stats dd{order:-1;margin:0;font:700 1.25em/1.2 var(--serif);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.stats dt{margin:0;font-size:.82em;line-height:1.4;color:var(--inkmute)}
@media(max-width:420px){.stats>div{grid-template-columns:minmax(0,1fr)}}

/* ------------------------------------------------------------ home: the folder stack */
.stack-sec{position:relative}
.stack{list-style:none;margin:0;padding:0;--step:150px;--fh:calc(var(--step) + 34px);--tab-h:40px;position:relative}
.stack li{position:relative;margin-top:calc(var(--step) - var(--fh));z-index:calc(var(--i) + 1)}
.stack li:first-child{margin-top:0}
.folder{display:block;position:relative;height:var(--fh);text-decoration:none;color:var(--ink);transition:transform .38s var(--ease)}
.folder__tab{position:absolute;top:0;left:calc(var(--i)*20%);width:19%;min-width:150px;height:calc(var(--tab-h) + 2px);z-index:2;display:flex;align-items:center;justify-content:center;gap:.35em;padding:0 10px;background:var(--manila);border:1px solid var(--manila-edge);border-bottom:0;border-radius:11px 11px 0 0;font-size:14px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;white-space:nowrap;box-shadow:0 -3px 5px -3px rgba(60,40,10,.4),inset 0 2px 0 var(--manila-hi)}
.folder__tab::before{content:"";position:absolute;left:8px;right:8px;bottom:0;height:3px;background:var(--manila-edge);opacity:.7}
.folder__body{position:absolute;top:var(--tab-h);left:0;right:0;bottom:0;display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:20px;padding:16px clamp(16px,3vw,32px) 0;background:linear-gradient(180deg,var(--manila-hi),var(--manila) 38px);border:1px solid var(--manila-edge);border-radius:0 8px 0 0;box-shadow:0 -4px 8px -3px rgba(60,40,10,.4),0 1px 0 rgba(255,255,255,.25) inset}
.folder__idx{display:grid;gap:0;align-content:start}
.ix{display:flex;align-items:baseline;gap:.5em;line-height:25px;font-size:15.5px;white-space:nowrap;min-width:0}
.ix i{font-style:normal;font-weight:700;letter-spacing:.04em;flex:none}
.ix u{flex:1;min-width:14px;border-bottom:1px dotted rgba(29,27,24,.55);text-decoration:none;transform:translateY(-4px)}
.ix em{font-style:normal;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:0 1 auto}
.folder__meta{display:grid;align-content:start;justify-items:end;gap:2px;text-align:right;font-size:14px;color:#4a3f2a;line-height:1.5}
.folder__meta span:first-child{font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:12.5px}
.folder__open{margin-top:8px;padding:3px 10px;border:1.5px solid var(--ink);border-radius:99px;font-weight:700;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink);transition:background-color .25s var(--ease),color .25s var(--ease)}
.folder:hover,.folder:focus-visible{transform:translateY(-14px)}
.folder:hover .folder__body,.folder:focus-visible .folder__body{box-shadow:0 -10px 18px -5px rgba(60,40,10,.5),0 1px 0 rgba(255,255,255,.25) inset}
.folder:hover .folder__open,.folder:focus-visible .folder__open{background:var(--ink);color:var(--manila-hi)}
.folder:focus-visible{outline:none}
.folder:focus-visible .folder__tab,.folder:focus-visible .folder__body{box-shadow:0 0 0 3px #1f5fbf}
.note-pick{position:absolute;right:2%;top:-34px;margin:0;font-size:26px;color:var(--deskink);transform:rotate(3deg)}
.stack-sec{padding-top:6px}
@media(max-width:860px){
  .stack{--step:172px}
  .folder__tab{left:calc(var(--i)*7%);width:auto;min-width:0;padding:0 18px}
  .folder__body{grid-template-columns:minmax(0,1fr);gap:0;padding-top:12px}
  .folder__meta{display:none}
  .ix{font-size:15.5px}
  
  .note-pick{display:none}
}
@media(max-width:480px){.stack{--step:150px}.folder__tab{left:calc(var(--i)*5%)}}

/* ------------------------------------------------------------ home: exhibit index */
.extable{width:100%;border-collapse:collapse;font-size:16.5px;line-height:1.4}
.extable thead th{text-align:left;font:700 12.5px/1.4 var(--serif);letter-spacing:.14em;text-transform:uppercase;padding:.4em .6em;border-bottom:2px solid var(--ink)}
.extable td,.extable tbody th{padding:.5em .6em;vertical-align:baseline;border-bottom:1px solid rgba(29,27,24,.18);text-align:left;font-weight:400}
.extable .exno{width:5.4em;font-weight:700;letter-spacing:.04em;font-variant-numeric:tabular-nums;white-space:nowrap}
.extable tbody th a{font-weight:700;text-decoration:none;background-image:linear-gradient(var(--hl),var(--hl));background-repeat:no-repeat;background-size:0 .55em;background-position:0 85%;transition:background-size .3s var(--ease)}
.extable tbody tr:hover th a,.extable tbody th a:focus-visible{background-size:100% .55em}
.extable .exsub{font-style:italic;color:var(--inkmute)}
.extable tr.fold th{padding:1.4em .6em .35em;border-bottom:2px solid var(--manila-edge);font:700 14px/1.4 var(--serif);letter-spacing:.14em;text-transform:uppercase;background:none}
.extable tr.fold:first-child th{padding-top:.6em}
.extable tr.fold a{text-decoration:none;font-weight:700}
.extable tr.fold a:hover{text-decoration:underline}
@media(max-width:640px){
  .extable thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .extable tbody tr:not(.fold){display:grid;grid-template-columns:4.6em minmax(0,1fr);column-gap:.4em;padding:.35em 0;border-bottom:1px solid rgba(29,27,24,.18)}
  .extable td,.extable tbody th{border:0;padding:.1em .3em}
  .extable .exno{width:auto;grid-row:1/span 2}
  .extable .exsub{grid-column:2}
}

/* ------------------------------------------------------------ home: stipulations + schedule A */
.stip .rules__list{list-style:none;margin:0;padding:0;display:grid;gap:var(--lh);counter-reset:s}
.stip .rule{display:grid;grid-template-columns:3.2em minmax(0,1fr);column-gap:.4em;row-gap:.2em}
.stip .rule__n{grid-row:1/span 2;font:700 1.15em/1.4 var(--serif);font-variant-numeric:tabular-nums}
.stip .rule h3{margin:0;font:700 1.05em/1.4 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.stip .rule p{margin:0;max-width:34em}
.stip .eyebrow{margin:0 0 .3em;font-style:italic;color:var(--inkmute)}
.stip .eyebrow::before{content:"Re: "}
.stip .sec-title,.sched .sec-title{margin:0 0 .7em;font:700 clamp(20px,2.6vw,26px)/1.25 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.sched .eyebrow{margin:0 0 .3em;font-style:italic;color:var(--inkmute)}
.sched .eyebrow::before{content:"Re: "}
.sched .sec-lede{max-width:36em;margin:0 0 var(--lh)}
.trows{width:100%;border-collapse:collapse;border-top:2px solid var(--ink);margin:0 0 var(--lh);font-size:16px;line-height:1.5}
.trows tr{border-bottom:1px solid var(--ink)}
.trows th,.trows td{padding:.7em .8em;vertical-align:top;text-align:left;font-weight:400}
.trows th{width:22%;border-right:1px solid var(--ink)}
.trows td+td{border-left:1px dotted rgba(29,27,24,.5)}
.trows h3{margin:0;font:700 1em/1.35 var(--serif)}
.trows p{margin:0}
.trows .lab{display:block;margin-bottom:.15em;font:700 11.5px/1.4 var(--serif);letter-spacing:.14em;text-transform:uppercase;color:var(--inkmute)}
details.more{margin-top:0}
details.more summary{cursor:pointer;display:inline-block;margin:0 0 var(--lh);padding:.45em 1.1em;background:var(--manila);border:1px solid var(--manila-edge);border-radius:8px 8px 0 0;font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:14px;list-style:none;box-shadow:inset 0 2px 0 var(--manila-hi)}
details.more summary::-webkit-details-marker{display:none}
details.more summary::before{content:"+ "}
details.more[open] summary::before{content:"\2212  "}
@media(max-width:700px){
  .trows,.trows tbody{display:block}
  .trows tr{display:block;padding:.5em 0}
  .trows th,.trows td{display:block;width:auto;border:0;padding:.2em .2em}
  .trows td+td{border:0}
}

/* ------------------------------------------------------------ home: sticky note + proof of service */
.sticky{justify-self:center;width:min(100%,430px);padding:20px 22px 22px;background:#f7dc5a;color:var(--ink);box-shadow:var(--shadow-p);transform:rotate(-1.6deg);position:relative;font-size:16.5px;line-height:1.5}
.sticky::before{content:"";position:absolute;top:-10px;left:50%;width:84px;height:22px;margin-left:-42px;background:rgba(255,253,246,.55);transform:rotate(2deg);box-shadow:0 1px 2px rgba(0,0,0,.15)}
.sticky p{margin:0 0 .6em}
.sticky .sticky__h{font-size:34px;line-height:1.05;margin-bottom:.3em}
.sticky a{color:var(--ink)}
.pos{padding-bottom:clamp(40px,6vw,64px);overflow:hidden}
.pos__h{margin:0 0 .5em;font:700 clamp(30px,5vw,46px)/1.1 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.pos p{max-width:34em}
.pos__mail{margin:.4em 0 .8em}
.pos__mail .mail{font-weight:700;font-size:clamp(18px,3.6vw,28px);user-select:all;-webkit-user-select:all;overflow-wrap:anywhere;background-image:linear-gradient(var(--hl),var(--hl));background-repeat:no-repeat;background-size:100% .55em;background-position:0 85%;text-decoration:none}
.pos__row{display:flex;flex-wrap:wrap;gap:6px 24px;margin:0 0 var(--lh)}
.pos__sig{display:grid;gap:2px;margin:var(--lh) 0 0;max-width:15em}
.pos__sig .sig{font-size:40px;line-height:1;border-bottom:1px solid var(--ink);padding-bottom:2px;color:#1f3b78}
.pos__by{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--inkmute)}
.stamp-wrap{position:absolute;right:clamp(14px,5vw,64px);bottom:clamp(30px,5vw,60px);width:clamp(120px,19vw,184px);pointer-events:none}
.stamp--rec{transform:rotate(-12deg);opacity:.9}
@media(max-width:560px){.stamp-wrap{opacity:.75;right:6px;bottom:6px;width:112px}}

/* ------------------------------------------------------------ room page */
.room{--lm:clamp(58px,9vw,98px)}
.rcaption{text-align:center;margin-bottom:calc(var(--lh)*2)}
.rcaption__t{margin:0;font:700 clamp(26px,4.4vw,40px)/1.2 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.rcaption__t span{display:inline}
.rcaption__n{margin:.2em 0 var(--lh);font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:14px;padding-bottom:.6em;border-bottom:3px double var(--ink)}
.rlede{margin:0 auto var(--lh);max-width:34em;font-size:1.05em;text-align:left}
.docket{text-align:left;max-width:44em;margin:0 auto}
.docket__h{margin:0 0 .4em;font:700 12.5px/1.6 var(--serif);letter-spacing:.16em;text-transform:uppercase;border-bottom:1px solid var(--ink)}
.docket ol{list-style:none;margin:0;padding:0;columns:2;column-gap:2em;font-size:15px;line-height:1.5}
.docket li{break-inside:avoid;padding:.12em 0}
.docket a{text-decoration:none}
.docket a:hover{text-decoration:underline}
.docket .dn{font-weight:700;letter-spacing:.04em;margin-right:.4em}
.note-ex{margin:var(--lh) 0 0;font-size:26px;color:var(--stamp);transform:rotate(-2deg)}
@media(max-width:600px){.docket ol{columns:1}}

.exhibit{position:relative;scroll-margin-top:calc(var(--tabh) + 36px);padding-top:calc(var(--lh)*2);margin-top:calc(var(--lh)*1.5);border-top:3px double var(--ink)}
.exhibit:first-of-type{margin-top:0}
.sticker{position:absolute;top:calc(var(--lh)*.5);right:-6px;margin:0;padding:.35em .85em .3em;background:var(--sticker);color:var(--ink);font:700 14px/1.3 var(--serif);letter-spacing:.14em;text-transform:uppercase;border-radius:3px;box-shadow:0 1px 0 rgba(0,0,0,.15),0 3px 6px -1px rgba(60,40,10,.4),inset 0 0 0 1px rgba(0,0,0,.08);transform:rotate(-2deg);z-index:2}
.ehead{margin-bottom:var(--lh);padding-right:min(190px,30%)}
.ekick{margin:0;font-size:14px;line-height:var(--lh);color:var(--inkmute);font-style:italic}
.ecount{font-style:normal;font-weight:700;letter-spacing:.06em;margin-right:.6em;color:var(--ink);font-variant-numeric:tabular-nums}
.etitle{margin:.1em 0 0;font:700 clamp(25px,4vw,38px)/1.18 var(--serif);letter-spacing:.04em;text-transform:uppercase;overflow-wrap:anywhere;scroll-margin-top:calc(var(--tabh) + 36px)}
.exhibit:target .etitle{background-image:linear-gradient(var(--hl),var(--hl));background-repeat:no-repeat;background-size:100% .5em;background-position:0 88%}
.esub{margin:0 0 var(--lh);font-style:italic;font-size:1.1em;color:var(--inkmute)}
.elede{margin:0;max-width:34em}
.bates{margin:var(--lh) 0 0;text-align:right;font-variant:small-caps;font-weight:700;letter-spacing:.14em;font-size:15px;color:var(--inkmute);text-transform:lowercase;font-variant-numeric:tabular-nums}
.bates{text-transform:none;font-variant-caps:all-small-caps}
@media(max-width:560px){.ehead{padding-right:0;padding-top:var(--lh)}.sticker{font-size:12.5px}}

/* count dividers */
.gdiv.count{margin:calc(var(--lh)*2.5) 0 calc(var(--lh)*1.5);text-align:center;scroll-margin-top:calc(var(--tabh) + 36px);padding:var(--lh) 0;border-top:3px double var(--ink);border-bottom:1px solid var(--ink)}
.exhibit:first-of-type{border-top:0}
.count-n{margin:0;font:700 14px/1.5 var(--serif);letter-spacing:.3em;text-transform:uppercase;color:var(--stamp)}
.gdiv__t{margin:.1em 0 .2em;font:700 clamp(22px,3.4vw,30px)/1.25 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.gdiv__p{margin:0 auto;max-width:34em;font-style:italic;color:var(--inkmute)}
.gdiv.count+.exhibit{border-top:0;margin-top:0}

/* extras ("Smaller pieces") */
.xsec{margin-top:calc(var(--lh)*2);padding-top:var(--lh);border-top:3px double var(--ink);scroll-margin-top:calc(var(--tabh) + 36px)}
.xsec__h{margin-bottom:var(--lh)}
.xsec__h .eyebrow{margin:0;font-style:italic;color:var(--inkmute)}
.xsec__t{margin:0;font:700 clamp(22px,3.4vw,30px)/1.25 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.xsec__list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--lh) 2em}
.xsec__list>div{border-top:1px solid var(--ink);padding-top:.5em}
.xsec__list h3{margin:0 0 .2em;font:700 .95em/1.4 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.xsec__list p{margin:0;font-size:.95em}
@media(max-width:700px){.xsec__list{grid-template-columns:1fr}}

/* case body, restyled for paper */
.cbody{display:grid;gap:var(--lh);min-width:0}
.cbody>*{min-width:0;margin:0}
.cbody p{margin:0;max-width:34em}
.cbody p+p{margin-top:var(--lh)}
.cbody a{text-decoration:underline;text-decoration-thickness:1px}
.cbody a:hover{background:var(--hl)}
.cbody strong{font-weight:700}
.cbody code{font:400 .88em/1.2 ui-monospace,Menlo,Consolas,monospace;background:rgba(246,210,60,.28);padding:.05em .3em;border-radius:2px}
.cbody h3,.cbody h4{margin:0;font:700 .95em/1.4 var(--serif);letter-spacing:.04em;text-transform:uppercase}
.cbody h3{border-bottom:1px solid var(--ink);padding-bottom:.15em;margin-bottom:.5em;display:block}
.cbody h4{letter-spacing:.04em;margin-bottom:.2em}
.cbody ul,.cbody ol{margin:0;padding-left:1.4em;display:grid;gap:.5em;max-width:34em}
.cbody li::marker{color:var(--inkmute)}
.cbody .block{display:grid;gap:.6em;align-content:start;min-width:0}
.cbody .block>*{margin:0}
.cbody .block p+p{margin-top:.6em}
.cbody .cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--lh) 2.4em;align-items:start}
.cbody .cols .block{padding-left:0}
.cbody .cols .block+.block{border-left:1px solid rgba(29,27,24,.3);padding-left:1.4em}
.cbody .cols p,.cbody .cols ul,.cbody .cols ol{max-width:none}
.cbody .grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--lh) 1.6em}
.cbody .grid3>div{border-top:2px solid var(--ink);padding-top:.5em;min-width:0}
.cbody .grid3 p{font-size:.92em;max-width:none}
.cbody .made{border-left:4px solid var(--stamp);padding:.2em 0 .2em 1em;background:linear-gradient(90deg,rgba(184,50,42,.06),transparent 70%)}
.cbody .made b{display:block;font:700 12.5px/1.6 var(--serif);letter-spacing:.14em;text-transform:uppercase;color:var(--stamp)}
.cbody .made p{font-size:.95em;max-width:34em}
.cbody .note{font-style:italic;font-size:.9em;color:var(--inkmute)}
.cbody .kind{display:block;font:700 12.5px/1.6 var(--serif);letter-spacing:.14em;text-transform:uppercase;color:var(--inkmute)}
.cbody .count{font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:.04em}
.cbody .logline{font-style:italic;font-size:1.05em}
.cbody .facts{display:flex;flex-wrap:wrap;gap:.3em 1.6em;font-size:.92em;color:var(--inkmute)}
.cbody .facts strong{color:var(--ink);font-size:1.25em;margin-right:.2em}
.cbody .tags{display:flex;flex-wrap:wrap;gap:6px}
.cbody .tag{padding:.2em .7em;border:1px solid var(--ink);font:700 11.5px/1.5 var(--serif);letter-spacing:.12em;text-transform:uppercase;border-radius:2px}
.cbody .tag.hot{background:var(--sticker)}
.cbody .flow{list-style:none;padding:0;max-width:none;counter-reset:st;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:var(--lh) 1.4em}
.cbody .flow li{counter-increment:st;border-top:2px solid var(--ink);padding-top:.4em;display:grid;gap:.2em;align-content:start}
.cbody .flow b::before{content:counter(st) ". ";color:var(--stamp)}
.cbody .flow span{font-size:.92em;color:var(--inkmute)}
.cbody .books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--lh) 1.8em;align-items:start}
.cbody .book{display:grid;gap:.6em;align-content:start;min-width:0;padding:1em 1.1em;border:1px solid var(--ink);box-shadow:3px 3px 0 rgba(29,27,24,.25)}
.cbody .book>*{margin:0}
.cbody .book.lead{grid-column:1/-1;grid-template-columns:minmax(0,13rem) minmax(0,1fr);gap:1.6em}
.cbody .lead-text{display:grid;gap:.6em;min-width:0}
.cbody .lead-text>*{margin:0}
.cbody .book .cover{width:100%;max-width:220px}
.cbody .piece{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:1.6em;align-items:start}
.cbody .piece-text{display:grid;gap:.6em;min-width:0}
.cbody .piece-text>*{margin:0}
.cbody .sub-case{display:grid;gap:var(--lh);border-top:1px solid var(--ink);padding-top:var(--lh)}
.cbody .sub-case>h3{font-size:1.15em}
.cbody .sub-case>*{margin:0}
.cbody .more{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--lh) 2em}
.cbody .more>div{border-top:1px solid var(--ink);padding-top:.5em}
.cbody .more p{font-size:.95em}
.cbody .stats{margin:0;max-width:30em}


/* links: highlighter swipe + underline, with a hand-drawn arrow */
.cbody .links{display:flex;flex-wrap:wrap;align-items:center;gap:.5em 1.4em;max-width:none}
.cbody .links::before{content:"open demo \2192";font:700 26px/1 var(--hand);color:var(--stamp);transform:rotate(-3deg);margin-right:.2em;opacity:0;transition:opacity .3s var(--ease)}
.cbody .links:has(a)::before{opacity:0}
.exhibit:first-of-type .cbody .links:has(a)::before,.cbody .links:hover::before,.cbody .links:focus-within::before{opacity:1}
.cbody .links:not(:has(a))::before{display:none}
.cbody .links a{position:relative;display:inline-block;font-weight:700;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:.2em;padding:0 .3em}
.cbody .links a::before{content:"";position:absolute;left:0;right:0;top:.15em;bottom:-.02em;background:var(--hl);mix-blend-mode:multiply;z-index:-1;transform:rotate(-.6deg);transform-origin:left center}
.cbody .links a:hover{background:none}
.cbody .links a[target=_blank]::after{content:" \2197"}
.cbody .links span{font-style:italic;color:var(--inkmute)}
.cbody .links{isolation:auto}

/* figures: paper-clipped photographs. Never tinted or filtered. */
.cbody figure{position:relative;margin:0;background:#fff;border:9px solid #fff;box-shadow:0 1px 2px rgba(40,30,15,.3),0 7px 16px -6px rgba(40,30,15,.45);display:grid;gap:8px;align-content:start;min-width:0;transform:rotate(var(--r,0deg))}
.cbody figure::before{content:"";position:absolute;z-index:3;top:-22px;left:18px;width:15px;height:38px;border:2.5px solid #8b919b;border-radius:8px 8px 8px 8px;background:transparent;box-shadow:0 1px 1px rgba(0,0,0,.25);pointer-events:none}
.cbody figure::after{content:"";position:absolute;z-index:3;top:-15px;left:23px;width:5px;height:27px;border:2.5px solid #8b919b;border-top:0;border-radius:0 0 5px 5px;pointer-events:none}
.cbody figure img,.cbody figure video{display:block;width:100%;height:auto;border:0;margin:0}
.cbody figure figcaption{margin:0;padding:0 2px 4px;font-size:13.5px;line-height:1.45;font-style:italic;color:#44403a}
.cbody figure.wide,.cbody figure.compare-fig{--r:0deg}
.cbody figure.wide:has(img.portrait){max-width:360px}
.cbody img.portrait,.cbody video.portrait{max-width:min(100%,360px)}
.cbody img.cover{box-shadow:0 1px 3px rgba(0,0,0,.3)}
.cbody .shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:calc(var(--lh)*.9) 1.8em;align-items:start}
.cbody .gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:calc(var(--lh)*.9) 1.4em;align-items:start}
.cbody .shots figure:nth-child(odd),.cbody .gallery figure:nth-child(3n+1),.cbody .reels figure:nth-child(odd){--r:-.5deg}
.cbody .shots figure:nth-child(even),.cbody .gallery figure:nth-child(3n+2),.cbody .reels figure:nth-child(even){--r:.5deg}
.cbody .gallery figure:nth-child(3n){--r:.2deg}
.cbody .reels{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:calc(var(--lh)*.9) 1.2em;align-items:start}
.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr));max-width:560px}
.cbody .reels video{aspect-ratio:9/16;object-fit:cover;background:#000}
.cbody figure.piece,.cbody .piece>figure{--r:-.4deg}
.cbody video{background:#000}
.cbody .piece figure{margin:0}

/* before / after slider */
.cbody .compare{position:relative;overflow:hidden;width:100%;background:#ddd;--pos:50%;touch-action:pan-y}
.cbody .compare.portrait{max-width:360px}
.cbody .compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;max-width:none}
.cbody .compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cbody .cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:2px;margin-left:-1px;background:#fff;pointer-events:none;box-shadow:0 0 0 1px rgba(0,0,0,.35)}
.cbody .cmp-line::after{content:"\2194";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:40px;height:40px;border-radius:50%;background:var(--ink);color:#fff;display:grid;place-items:center;font:700 18px/1 var(--serif)}
.cbody .cmp-tag{position:absolute;top:10px;font:700 11px/1 var(--serif);letter-spacing:.12em;text-transform:uppercase;background:var(--ink);color:#fff;padding:6px 8px;pointer-events:none}
.cbody .cmp-tag.l{left:10px}.cbody .cmp-tag.r{right:10px}
.cbody .compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.cbody .compare:focus-within{outline:3px solid #1f5fbf;outline-offset:3px}

/* end of the room */
.nextrow{margin-top:calc(var(--lh)*3);display:flex;flex-wrap:wrap;align-items:flex-end;gap:14px 28px;border-top:3px double var(--ink);padding-top:var(--lh)}
.nexttab{display:inline-flex;align-items:center;gap:.6em;padding:.7em 1.6em .6em;background:var(--manila);border:1px solid var(--manila-edge);border-radius:12px 12px 0 0;box-shadow:inset 0 3px 0 var(--manila-hi),0 -2px 4px -2px rgba(60,40,10,.4);color:var(--ink);text-decoration:none;font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:15px;transition:transform .35s var(--ease)}
.nexttab:hover,.nexttab:focus-visible{transform:translateY(-6px)}
.nexttab span{font-style:normal}
.backhome{font-size:15px}
.rfoot{margin-top:calc(var(--lh)*2);font-size:14.5px;color:var(--inkmute)}
.rfoot p{margin:0 0 .3em}

@media(max-width:900px){
  .cbody .cols,.cbody .grid3,.cbody .more,.cbody .piece,.cbody .books,.cbody .book.lead,.cbody .shots{grid-template-columns:minmax(0,1fr)}
  .cbody .cols .block+.block{border-left:0;padding-left:0;border-top:1px solid rgba(29,27,24,.3);padding-top:var(--lh)}
  .cbody .book .cover{max-width:180px}
}
@media(max-width:560px){
  .cbody .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody .reels{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody figure{border-width:7px}
}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
}
@media print{.tabrow,.themebtn,.stampbtn{display:none}body{background:#fff}.sheet{box-shadow:none}}
'''.replace('@@NUMS@@', NUMS)

JS = r'''/* Case File: theme toggle, settle-in, compare sliders, Esc to go Home. */
(function () {
  'use strict';
  var root = document.documentElement;
  var btn = document.getElementById('themebtn');
  function paint() {
    var dark = root.getAttribute('data-theme') === 'dark';
    if (btn) { btn.setAttribute('aria-pressed', dark ? 'true' : 'false'); btn.setAttribute('aria-label', dark ? 'Light desk' : 'Dark desk'); }
  }
  if (btn) {
    btn.addEventListener('click', function () {
      var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', t);
      try { localStorage.setItem('cf-theme', t); } catch (e) {}
      paint();
    });
  }
  paint();

  /* papers settle in once, stickers press on once */
  var els = document.querySelectorAll('.sheet, .exhibit');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.02 });
    Array.prototype.forEach.call(els, function (el) { io.observe(el); });
  } else {
    Array.prototype.forEach.call(els, function (el) { el.classList.add('in'); });
  }

  /* before / after sliders */
  Array.prototype.forEach.call(document.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* keep the current tab in view in the scrolling tab row */
  var cur = document.querySelector('.tab.is-cur');
  if (cur && cur.scrollIntoView && cur.parentNode.scrollWidth > cur.parentNode.clientWidth) {
    cur.parentNode.scrollLeft = cur.offsetLeft - 40;
  }

  /* Esc closes the folder and returns Home (rooms only) */
  if (document.body.getAttribute('data-page') === 'room') {
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      var t = e.target, n = t && t.tagName;
      if (n === 'INPUT' || n === 'TEXTAREA' || n === 'SELECT' || (t && t.isContentEditable)) return;
      if (document.fullscreenElement) return;
      var home = document.querySelector('.tab--home');
      if (home) location.href = home.getAttribute('href');
    });
  }
})();
'''


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'e.css'), 'w', encoding='utf-8').write(CSS)
    open(os.path.join(OUT, 'e.js'), 'w', encoding='utf-8').write(JS)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(home_page())
    for i, r in enumerate(ROOMS):
        d = os.path.join(OUT, r['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(room_page(i, r))
    print('mockup-e written:', total, 'exhibits,', len(ROOMS), 'rooms')


if __name__ == '__main__':
    main()


# style switcher (see add_switcher.py)
import runpy as _rp
import os as _os; _rp.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "add_switcher.py"), run_name="__main__")
