#!/usr/bin/env python3 -I
"""Mockup F, "Plain Web": rebuild mockup-f/ from themed/live.json (stdlib only).

Writes mockup-f/index.html, mockup-f/<room>/index.html, mockup-f/f.css, mockup-f/f.js.
Run: python3 -I themed/render_f.py
"""
import datetime
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-f')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
REPO = 'https://github.com/mylesparslow-collab/mylesparslow-collab.github.io'
UPDATED = datetime.date.today()
UPDATED_S = '%d %s %d' % (UPDATED.day, UPDATED.strftime('%b'), UPDATED.year)
unesc = html.unescape


def esc(s):
    return html.escape(s, quote=False)


# ------------------------------------------------------------------ helpers
def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b):
    """Deepen relative paths one level (rooms sit in mockup-f/<room>/), open outbound links in a new tab,
   ."""
    b = re.sub(r'((?:src|href|poster)=")\.\./', r'\1../../', b)

    def a(m):
        t = m.group(0)
        h = attr(t, 'href') or ''
        if (re.match(r'https?://', h) or h.startswith('../../demos/') or h.startswith('../../assets/')) and 'target=' not in t:
            t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
        elif 'target="_blank"' in t and 'rel=' not in t:
            t = t.replace('<a ', '<a rel="noopener" ', 1)
        return t
    b = re.sub(r'<a\b[^>]*>', a, b)
    return b


def first_demo(b):
    m = re.search(r'<p class="links">(.*?)</p>', b, re.S)
    if not m:
        return None
    for l in re.finditer(r'<a\b[^>]*href="([^"]*)"', m.group(1)):
        h = l.group(1)
        if h.startswith('../demos/') or h.startswith('http'):
            return h
    return None


def kicker(it):
    return '<span>%s</span>' % it['count'] + ''.join('<span>%s</span>' % k for k in it['kickers'] if k)


for r in ROOMS:
    r['n'] = sum(1 for i in r['items'] if i['kind'] == 'case')
N_CASES = sum(r['n'] for r in ROOMS)

# ------------------------------------------------------------------ shell
CSS_ONLY_HEAD = '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark">'


def shell(title, desc, depth, inner, body_attr='', head_extra=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n' + CSS_ONLY_HEAD +
            '\n<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%sfavicon.svg" type="image/svg+xml">\n'
            '<link rel="stylesheet" href="%s%sf.css">\n%s</head>\n<body%s>\n'
            '<a class="skip" href="#main">Skip to content</a>\n<main id="main">\n%s\n</main>\n'
            '<script src="%s%sf.js"></script>\n</body>\n</html>\n') % (
        html.escape(title), html.escape(desc, quote=True), up + '../' if depth == 0 else up + '../',
        '', ('../' * depth), head_extra, body_attr, inner, '', '../' * depth)


# ------------------------------------------------------------------ home
def tools_table():
    rows = re.findall(r'<article class="trow">(.*?)</article>', HOME['tools_html'], re.S)
    out = []
    for row in rows:
        name = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        cells = ''.join('<p><b>%s:</b> %s</p>' % (lab, p) for lab, p in
                        re.findall(r'<span class="lab">(.*?)</span>\s*<p>(.*?)</p>', row, re.S))
        out.append('<tr><th scope="row">%s</th><td>%s</td></tr>' % (name, cells))
    head = '<thead><tr><th scope="col">Project</th><th scope="col">Which AI, and for what</th></tr></thead>'
    first = '<table>%s<tbody>%s</tbody></table>' % (head, ''.join(out[:10]))
    rest = ('<details><summary>Show the other %d rows</summary><table>%s<tbody>%s</tbody></table></details>'
            % (len(out) - 10, head, ''.join(out[10:])))
    return first + '\n' + rest


def home_page():
    h = HOME['hero_html']
    count = re.search(r'hero__count">(.*?)</span>', h).group(1)
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', h, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', h, re.S)
    rule_title = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', HOME['rules_html'], re.S).group(1)
    rules = re.findall(r'<h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', HOME['rules_html'], re.S)
    tl_title = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', HOME['tools_html'], re.S).group(1)
    tl_lede = re.search(r'<p class="sec-lede">(.*?)</p>', HOME['tools_html'], re.S).group(1)
    jump = ' &middot; '.join('<a href="#%s">%s (%d)</a>' % (r['slug'], r['short'], r['n']) for r in ROOMS)

    idx = []
    for r in ROOMS:
        items = []
        for it in r['items']:
            if it['kind'] != 'case':
                continue
            demo = first_demo(it['body_html'])
            d = (' <a class="d" target="_blank" rel="noopener" href="%s">[demo]</a>' % demo) if demo else ''
            items.append('<li><a href="%s/index.html#%s">%s</a><span class="u">%s</span>%s</li>' % (r['slug'], it['id'], it['title'], it['sub'], d))
        idx.append('<h2 id="%s"><a href="%s/index.html">%s (%d)</a></h2>\n<p class="m">%s</p>\n<ol>\n%s\n</ol>'
                   % (r['slug'], r['slug'], r['title'], r['n'], r['lede'], '\n'.join(items)))

    foot = HOME['foot_html']
    mail = re.search(r'href="mailto:([^"]+)"', foot).group(1)
    gh = re.search(r'<a href="(https://github.com/[^"]*)">GitHub</a>', foot).group(1)
    lp = re.search(r'<a href="([^"]*)">Legal portfolio</a>', foot).group(1)
    sign = re.search(r'<span>(.*?)</span>\s*</div>', foot, re.S).group(1)
    foot_title = 'Say hello.'

    inner = f'''<header id="top">
<h1>Myles Parslow</h1>
<p>makes things with AI.</p>
<p>{lede}</p>
<p class="m">{count.replace('52', str(N_CASES))}</p>
<ul class="stats">
{chr(10).join('<li><b>%s</b> &mdash; %s</li>' % (dd, dt) for dt, dd in stats)}
</ul>
</header>
<nav aria-label="Rooms"><p>{jump}</p></nav>
<hr>
<section aria-label="Index">
{chr(10).join(idx)}
</section>
<hr>
<section id="rules">
<h2>How I work</h2>
<p class="m">{rule_title}</p>
<ol>
{chr(10).join('<li><b>%s.</b> %s</li>' % (t, p) for t, p in rules)}
</ol>
</section>
<hr>
<section id="tools">
<h2>Which AI for what</h2>
<p class="m">{tl_title}</p>
<p>{tl_lede}</p>
{tools_table()}
</section>
<hr>
<section id="archive">
<p><b>Style archive.</b> You&rsquo;re looking at: Plain Web. This site is also a running design experiment. Each version renders the same {N_CASES} case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. <a href="../styles/index.html"><b>See every version &rarr;</b></a></p>
</section>
<hr>
<footer id="contact">
<h2>{foot_title}</h2>
<p><a href="mailto:{mail}">{mail}</a></p>
<p><a href="{gh}" target="_blank" rel="noopener">GitHub</a> &middot; <a href="{lp}" target="_blank" rel="noopener">Legal portfolio</a> &middot; <a href="#top">Back to top &uarr;</a></p>
<p class="m">{sign}</p>
<p class="m" id="weight" data-u="{UPDATED_S}">This page: under 60 KB &middot; 0 trackers &middot; 0 frameworks &middot; last updated {UPDATED_S}.<br><a href="{REPO}" target="_blank" rel="noopener">source on GitHub</a></p>
</footer>'''
    # the weight line: JS replaces only the number; keep the "source on GitHub" link
    redirect = '<script>(function(){var M=%s,h=location.hash.slice(1);if(M.hasOwnProperty(h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    desc = 'Myles Parslow makes things with AI: %d case studies in five rooms, as a plain web page.' % N_CASES
    return shell('Myles Parslow', desc, 0, inner, '', redirect).replace('<link rel="icon" href="../favicon.svg"', '<link rel="icon" href="../favicon.svg"')


# ------------------------------------------------------------------ rooms
def room_page(i, r):
    others = ' &middot; '.join('<a href="../%s/index.html">%s</a>' % (o['slug'], o['short']) for o in ROOMS if o is not r)
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    nxt_html = ('<a href="../%s/index.html">Next: %s &rarr;</a>' % (nxt['slug'], nxt['short'])) if nxt else '<a href="../index.html">Next: Home &rarr;</a>'
    cases = [it for it in r['items'] if it['kind'] == 'case']
    toc = '\n'.join('<li><a href="#%s">%s</a></li>' % (c['id'], c['title']) for c in cases)
    parts, prev = [], None
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            parts.append('<hr>\n' + fix_body(it['html']))
        elif k == 'extra':
            parts.append('<hr>\n' + fix_body(it['html']) + '\n<p class="t"><a href="#top">&uarr; top</a></p>')
        else:
            pre = '' if prev == 'group' else '<hr>\n'
            parts.append('''%s<article id="%s">
<h2>%s <a class="pl" href="#%s" aria-label="Link to %s">#</a></h2>
<p class="s"><em>%s</em></p>
<p class="m k">%s</p>
<p>%s</p>
%s
<p class="t"><a href="#top">&uarr; top</a></p>
</article>''' % (pre, it['id'], it['title'], it['id'], html.escape(unesc(it['title'])), it['sub'], kicker(it), it['lede'], fix_body(it['body_html'])))
        prev = k
    inner = f'''<nav id="top" aria-label="Breadcrumbs"><p><a href="../index.html">Home</a> / <a href="../index.html" aria-current="page">{r['short']}</a> &nbsp;&nbsp; {others}</p></nav>
<h1>{r['title']}</h1>
<p class="m">{r['eyebrow']} &middot; {r['count']}</p>
<p>{r['lede']}</p>
<nav aria-label="Contents"><ol class="toc">
{toc}
</ol></nav>
{chr(10).join(parts)}
<hr>
<p>{nxt_html}</p>'''
    desc = unesc(re.sub(r'<[^>]+>', '', r['lede']))
    return shell('%s — Myles Parslow' % unesc(r['title']), desc, 1, inner, ' data-home="../index.html"')


# ------------------------------------------------------------------ static files
CSS = r'''@charset "utf-8";
:root{--bg:#fff;--fg:#111;--m:#555;--rule:#ddd;--bd:#999;--a:#00e;--v:#551a8b;--h:#e00;color-scheme:light dark}
@media(prefers-color-scheme:dark){:root{--bg:#121212;--fg:#e8e8e8;--m:#a3a3a3;--rule:#333;--bd:#666;--a:#8ab4ff;--v:#c58af9;--h:#ff7b7b}}
html{scroll-padding-top:1em}
body{margin:0;border-top:4px solid #f60;background:var(--bg);color:var(--fg);font:17px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Verdana,sans-serif;overflow-wrap:break-word}
main{max-width:70ch;margin:0 auto;padding:1.5em 1em 3em}
a{color:var(--a);text-decoration:underline;text-underline-offset:.15em}
a:visited{color:var(--v)}a:hover,a:active{color:var(--h)}
a:focus-visible,summary:focus-visible,input:focus-visible+*{outline:2px solid currentColor;outline-offset:2px}
.skip{position:absolute;left:-99em}.skip:focus{left:1em;top:.5em;background:var(--bg);padding:.25em .5em}
h1,h2,h3,h4{font-size:inherit;font-weight:700;margin:1.5em 0 .5em}
h1{margin-top:0;font-size:34px;line-height:1.2}
h2{margin-top:0}
h1+p{margin-top:0}
h1+p.m{margin-top:-.5em}
p,ul,ol,dl,table,figure,details{margin:0 0 1em}
ul,ol{padding-left:2.5em}
li{margin:0 0 .5em}
li::marker{font-variant-numeric:tabular-nums;color:var(--m)}
.toc{columns:2;column-gap:2em}.toc li{margin:0;break-inside:avoid}
hr{border:0;border-top:1px solid var(--rule);margin:2em 0}
.m,figcaption,.d,.d:visited,.kind,.count,.eyebrow,.note,.lab{color:var(--m)}
.d:hover{color:var(--h)}
.u::before{content:" — "}
.s{margin:-.5em 0 .5em}
.k span+span::before{content:", "}.k span:first-child::after{content:" · "}.k span:nth-child(2)::before{content:none}
.pl{text-decoration:none;color:var(--m);font-weight:400;margin-left:.25em}
.pl:hover{text-decoration:underline}
.t{margin:1em 0 0}
.stats{list-style:none;padding:0}.stats li{margin:0}
dl.stats{list-style:none}dl.stats div{display:flex;justify-content:space-between;gap:1em;border-bottom:1px solid var(--rule);padding:.25em 0}
dl.stats dt{margin:0}dl.stats dd{margin:0;font-weight:700;font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse}
th,td{border:1px solid var(--bd);padding:6px 10px;text-align:left;vertical-align:top}
td p{margin:0 0 .5em}td p:last-child{margin:0}
thead th{border-bottom-width:2px}
summary{cursor:pointer;margin:1em 0 .5em}
figure{margin:1em 0}
img,video{display:block;max-width:100%;height:auto;border:1px solid var(--rule)}
figure>img,figure>a>img,figure>video{width:100%}
.portrait,figure>img.portrait,figure>video.portrait{width:auto;max-width:min(100%,20em)}
figcaption{margin-top:.5em}
.block{margin:0 0 1em}
.block>:last-child{margin-bottom:0}
.block>:first-child{margin-top:0}
.links a+a::before{content:" · ";display:inline-block;color:var(--fg);white-space:pre}.links span{color:var(--m)}.links a+span::before{content:" — "}
.made,.note,.sub-case{border-left:2px solid var(--rule);padding-left:1em;margin:1em 0}
.made b{display:block}.made p{margin:0}
.logline,.s{font-style:italic}
h4{font-style:italic}
.facts{display:flex;flex-wrap:wrap;gap:0 1.5em}
.tags{margin:0 0 .5em}.tag::before{content:"["}.tag::after{content:"] "}.tag{color:var(--m)}.hot{font-weight:700}
.flow b{display:block}.flow span{display:block}
.xsec__list>div,.more>div{margin:0 0 1em}
.eyebrow{margin:0 0 .5em}
.book{margin:0 0 1.5em}.book .cover{width:12em;max-width:100%}
.compare{position:relative;overflow:hidden;max-width:100%;--pos:50%;border:1px solid var(--rule)}
.compare.portrait{max-width:20em}
.compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border:0;max-width:none}
.compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:2px;margin-left:-1px;background:var(--bg);pointer-events:none}
.cmp-tag{position:absolute;top:.5em;background:var(--fg);color:var(--bg);padding:0 .5em;pointer-events:none}
.cmp-tag.l{left:.5em}.cmp-tag.r{right:.5em}
.compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.compare:focus-within{outline:2px solid currentColor;outline-offset:2px}
@media(min-width:46em){
.shots,.grid3,.gallery,.reels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 1em;align-items:start}
.reels figure,.shots figure,.grid3 figure,.gallery figure{margin:0 0 1em}
}
@media(max-width:600px){
.toc{columns:1}
thead{display:none}
tr,th,td{display:block}
th,td{border-width:0 0 0 0;padding:6px 10px}
tr{border:1px solid var(--bd);margin:0 0 .5em}
}
'''

JS = r'''(function(){
  var b=document.body;
  document.addEventListener('keydown',function(e){
    var t=e.target;
    if(e.key==='Escape'&&b.dataset.home&&!(t.closest&&t.closest('input,textarea,select,video')))location.href=b.dataset.home;
  });
  Array.prototype.forEach.call(document.querySelectorAll('.compare'),function(c){
    var r=c.querySelector('input');if(!r)return;
    var s=function(){c.style.setProperty('--pos',r.value+'%')};
    r.addEventListener('input',s);s();
  });
  var w=document.getElementById('weight');
  if(w){
    var t=0,g=function(e){return e.transferSize||e.encodedBodySize||0};
    performance.getEntriesByType('resource').forEach(function(e){t+=g(e)});
    var n=performance.getEntriesByType('navigation')[0];if(n)t+=g(n);
    var k=t>0?Math.max(1,Math.round(t/1024))+' KB':'under 60 KB';
    w.firstChild.nodeValue='This page: '+k+' · 0 trackers · 0 frameworks · last updated '+w.dataset.u+'.';
  }
})();
'''


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    write(os.path.join(OUT, 'f.css'), CSS)
    write(os.path.join(OUT, 'f.js'), JS)
    write(os.path.join(OUT, 'index.html'), home_page())
    for i, r in enumerate(ROOMS):
        write(os.path.join(OUT, r['slug'], 'index.html'), room_page(i, r))
    print('mockup-f: %d rooms, %d cases, css %d B, js %d B' % (len(ROOMS), N_CASES, len(CSS.encode()), len(JS.encode())))


if __name__ == '__main__':
    main()
