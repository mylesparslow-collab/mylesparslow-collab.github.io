#!/usr/bin/env python3
"""Checks for mockup K ("Liner Notes"). Stdlib only. Run from anywhere: python3 -I themed/check_k.py

1. Parity: every text block (p, h1-h4, li, dt, dd, th, td, figcaption, summary) of the live pages (root index.html
   and the five room pages) must appear in the matching mockup-k page, whitespace-normalised. Blocks that are only
   the Transit Map theme's own wording (stations, lines, zones, its headings) are listed in THEME and re-worded here.
2. Links: every local href/src in mockup-k resolves to a file, every #anchor exists on its target page, and every
   old-#hash in the homepage redirect map lands on an existing id.
Exits non-zero on any failure.
"""
import html, json, os, re, sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = os.path.join(ROOT, 'mockup-k')
PAGES = ['index.html'] + ['%s/index.html' % r for r in ('legal', 'business', 'creative', 'design', 'research')]
BLOCK = {'p', 'h1', 'h2', 'h3', 'h4', 'li', 'dt', 'dd', 'th', 'td', 'figcaption', 'summary'}
# Transit Map wording and deliberate re-wordings (each still said in this theme's own words)
THEME = [r'Map square', r'[0-9]+ stations', r'Change (here )?for', r'^Zone [0-9]', r'^Interchange: ', r'^System map',
         r'^Myles Parslow [0-9]+ builds with AI, shown in full$', r'^Pick your line\.$', r'or go straight to the full map below\.$',
         r'^Open the full map', r'^The full network$', r'^Select a line to filter the map', r'^Central hub: ', r'^Weekend build Study',
         r'^Every project indexed by station', r'^Rules of travel$', r'^How I work with AI · ', r'^Which AI for what · ',
         r'^Style archive\. You’re looking at: Transit Map\.', r'^Hover or tab across stations', r'^This line at a glance$',
         r'^[0-9]+ tools in [0-9]+ groups, flagships first', r'Flagship system marks the production systems',
         r'^Show all [0-9]+ projects$', r'Flagship system$', r'^Flagship system', r'^Explore all [0-9]+ ', r'^Just browsing\?',
         r'^Route [0-9]', r'^Where to start', r'projects is a lot to explore cold',
         # Transit Map station codes (L-01 ...) and its line chrome; this theme numbers tracks A1, B2 ... instead
         r'^[LBCDR]-[0-9]{2}', r'You are here', r'^[LBCDR](Legal|Business|Creative|Design|Research)', r'^iService information$', r'^(Lines|Interchanges|Timetable|Service|!Service notice)$']


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.blocks, self.all, self.skip = [], [], [], 0

    def handle_starttag(self, t, a):
        if t in ('script', 'style'):
            self.skip += 1
        elif t in BLOCK:
            self.stack.append([])

    def handle_endtag(self, t):
        if t in ('script', 'style'):
            self.skip -= 1
        elif t in BLOCK and self.stack:
            s = ' '.join(''.join(self.stack.pop()).split())
            if s:
                self.blocks.append(s)

    def handle_data(self, x):
        if self.skip:
            return
        self.all.append(x)
        for s in self.stack:
            s.append(x)


def norm(s):
    return re.sub(r'\s+', '', s).replace(' ', '')


def parity():
    miss = []
    for p in PAGES:
        old, new = Text(), Text()
        old.feed(open(os.path.join(ROOT, p), encoding='utf-8').read())
        new.feed(open(os.path.join(K, p), encoding='utf-8').read())
        hay = norm(''.join(new.all))
        for b in dict.fromkeys(old.blocks):
            if any(re.search(rx, b) for rx in THEME):
                continue
            if norm(b) not in hay:
                miss.append((p, b))
    for p, b in miss:
        print('  missing in mockup-k/%s: %s' % (p, b[:160]))
    print('parity: %d missing' % len(miss))
    return not miss


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids = [], set()

    def handle_starttag(self, t, a):
        a = dict(a)
        if a.get('id'):
            self.ids.add(a['id'])
        for k in ('href', 'src', 'poster'):
            if a.get(k):
                self.refs.append(a[k])


def links():
    parsed, bad = {}, []

    def get(path):
        if path not in parsed:
            L = Links()
            L.feed(open(path, encoding='utf-8').read())
            parsed[path] = L
        return parsed[path]
    for p in PAGES:
        src = os.path.join(K, p)
        for ref in get(src).refs:
            u = urlsplit(html.unescape(ref))
            if u.scheme or ref.startswith('//'):
                continue
            path = unquote(u.path)
            if path.startswith('/'):
                tgt = os.path.join(ROOT, path.lstrip('/'))
            elif path:
                tgt = os.path.normpath(os.path.join(os.path.dirname(src), path))
            else:
                tgt = src
            if os.path.isdir(tgt):
                tgt = os.path.join(tgt, 'index.html')
            if not os.path.exists(tgt):
                bad.append('%s -> %s (no file)' % (p, ref))
                continue
            if u.fragment and tgt.endswith('.html') and tgt.startswith(K):
                if u.fragment not in get(tgt).ids and u.fragment != 'top':
                    bad.append('%s -> %s (no #%s)' % (p, ref, u.fragment))
    m = re.search(r'var M = (\{.*?\});', open(os.path.join(K, 'index.html'), encoding='utf-8').read(), re.S)
    red = json.loads(m.group(1))
    for h, room in red.items():
        if h not in get(os.path.join(K, room, 'index.html')).ids:
            bad.append('redirect #%s -> %s (no id)' % (h, room))
    for b in bad:
        print('  ' + b)
    print('links: %d refs on %d pages, %d redirects, %d broken' % (sum(len(get(os.path.join(K, p)).refs) for p in PAGES), len(PAGES), len(red), len(bad)))
    return not bad


if __name__ == '__main__':
    ok = parity()
    ok = links() and ok
    sys.exit(0 if ok else 1)
