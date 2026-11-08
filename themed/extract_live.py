"""Extract the LIVE site (root index.html + the five room pages) into themed/live.json.

Unlike extract_cases.py (which reads the frozen pre-redesign pages in themed/source/),
this reads what is actually deployed, so edits made directly on the live site
(PRs #34-#38: consultancy cases, AgentForge Rust, Northfield refresh...) are kept.

Output shape:
  home:  {hero_html, rules_html, tools_html, foot_html, redirect_map}
  rooms: [{slug, title, short, letter, eyebrow, count, lede,
           items: [{kind:'case', id, count, kickers, title, sub, lede, body_html, links_html}
                   | {kind:'group', id, html} | {kind:'extra', id, html}]}]
Paths stay as written on the live pages (rooms use ../assets/, home uses assets/).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AREAS = ['legal', 'business', 'creative', 'design', 'research']
VOID = {'img', 'br', 'hr', 'input', 'source', 'meta', 'link', 'wbr', 'track', 'area', 'col', 'embed', 'param'}


def element_end(t, start):
    """Index just past the element whose start tag begins at `start` (balanced by tag name)."""
    name = re.match(r'<([a-zA-Z0-9]+)', t[start:]).group(1).lower()
    depth = 0
    for m in re.compile(r'<(/?)([a-zA-Z0-9]+)\b[^>]*?(/?)>').finditer(t, start):
        if m.group(2).lower() != name:
            continue
        if m.group(1):
            depth -= 1
            if depth == 0:
                return m.end()
        elif not m.group(3) and name not in VOID:
            depth += 1
    raise ValueError(f'unbalanced <{name}> at {start}')


def inner(el):
    return el[el.find('>') + 1: el.rfind('<')]


def grab(t, pattern, start=0):
    m = re.compile(pattern).search(t, start)
    if not m:
        return None, -1
    e = element_end(t, m.start())
    return t[m.start():e], e


def text(el):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', el or '')).strip()


def room(slug):
    t = (ROOT / slug / 'index.html').read_text()
    head, _ = grab(t, r'<header class="rhead"')
    r = {
        'slug': slug,
        'title': text(grab(head, r'<h1')[0]),
        'short': re.search(r'data-short="([^"]*)"', head).group(1),
        'letter': text(grab(head, r'<span class="rhead__letter"')[0]),
        'eyebrow': text(grab(head, r'<p class="eyebrow"')[0]),
        'count': text(grab(head, r'<p class="rhead__count"')[0]),
        'lede': inner(grab(head, r'<p class="rhead__lede"')[0]).strip(),
        'items': [],
    }
    thumbs = dict(re.findall(r'<a class="row" href="#([^"]+)">.*?<img src="([^"]+)"', grab(t, r'<nav class="rindex"')[0], re.S))
    chapters, _ = grab(t, r'<div class="chapters"')
    body = inner(chapters)
    pos = 0
    pat = re.compile(r'<(article class="chap"|div class="gdiv"|section class="xsec"|p class="links")')
    while True:
        m = pat.search(body, pos)
        if not m:
            break
        e = element_end(body, m.start())
        el = body[m.start():e]
        kind = m.group(1)
        if kind.startswith('article'):
            top, te = grab(el, r'<div class="chap__top"')
            cb, _ = grab(el, r'<div class="cbody"', te)
            n, _ = grab(top, r'<p class="chap__n"')
            sub, _ = grab(top, r'<p class="chap__sub"')
            lede, _ = grab(top, r'<p class="chap__lede"')
            r['items'].append({
                'kind': 'case',
                'id': re.search(r'id="([^"]+)"', el).group(1),
                'count': text(grab(n, r'<span class="chap__c"')[0]),
                'kickers': [text(k) for k in re.findall(r'<span class="chap__k">(.*?)</span>', n)],
                'title': text(grab(top, r'<h2')[0]),
                'sub': text(sub) if sub else '',
                'lede': inner(lede).strip() if lede else '',
                'body_html': inner(cb).strip(),
                'links_html': '',
                'thumb': '',
            })
        elif kind.startswith('p class="links"'):
            # a links paragraph that follows an article belongs to that article
            if r['items'] and r['items'][-1]['kind'] == 'case' and not r['items'][-1]['links_html']:
                r['items'][-1]['links_html'] = el
            else:
                r['items'].append({'kind': 'extra', 'id': '', 'html': el})
        else:
            r['items'].append({'kind': 'group' if 'gdiv' in kind else 'extra',
                               'id': re.search(r'id="([^"]+)"', el).group(1), 'html': el})
        pos = e
    for i in r['items']:
        if i['kind'] == 'case':
            th = thumbs.get(i['id'], '')
            # prefer the sharp 2x set when it has this image
            hd = th.replace('thumbs-sm/', 'thumbs-hd/')
            i['thumb'] = hd if hd != th and (ROOT / slug / hd).resolve().exists() else th
    # extra sections after the chapters (e.g. business "Smaller pieces")
    _, ce = grab(t, r'<div class="chapters"')
    pos = ce
    while True:
        el, pos = grab(t, r'<section class="xsec"', pos)
        if not el:
            break
        r['items'].append({'kind': 'extra', 'id': re.search(r'id="([^"]+)"', el).group(1), 'html': el})
    return r


def home():
    t = (ROOT / 'index.html').read_text()
    out = {}
    for key, p in [('hero_html', r'<header class="hero"'), ('rules_html', r'<section class="rules"'),
                   ('tools_html', r'<section class="tools"'), ('foot_html', r'<footer class="foot"')]:
        out[key] = grab(t, p)[0]
    m = re.search(r'var map\s*=\s*(\{.*?\});', t, re.S) or re.search(r'map\s*=\s*(\{[^;]*?\})', t, re.S)
    out['redirect_map'] = m.group(1) if m else None
    return out


if __name__ == '__main__':
    data = {'home': home(), 'rooms': [room(a) for a in AREAS]}
    n = sum(1 for r in data['rooms'] for i in r['items'] if i['kind'] == 'case')
    for r in data['rooms']:
        cases = [i for i in r['items'] if i['kind'] == 'case']
        declared = int(re.match(r'\d+', r['count']).group())
        assert len(cases) == declared, f"{r['slug']}: {len(cases)} cases but header says {r['count']}"
    (ROOT / 'themed' / 'live.json').write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f'{n} case studies across {len(data["rooms"])} rooms;',
          'redirect map', 'found' if data['home']['redirect_map'] else 'MISSING')
