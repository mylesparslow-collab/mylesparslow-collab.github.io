#!/usr/bin/env python3
"""Render mockup M, "Redline": the portfolio as a draft in review.

    python3 -I themed/render_m.py

Reads themed/live.json and writes everything under mockup-m/: index.html (the document), <room>/index.html
(one Article per room), plus m.css, m.js and fonts/ copied from themed/m/. Stdlib only. Safe to re-run.
It never touches the live site.

Concept: one document page with a margin of comment balloons. Every project's "How it was built" note is split
into sentences here, in Python, and each sentence is attributed to an author only when its grammatical subject is
clearly "I" (Myles) or a named tool (Claude, ChatGPT, Codex, Gemini, Suno, a local model). Everything else stays
neutral. The result is plain markup (spans with author classes), so it works with no JavaScript; m.js only drives the
view switch (All markup / No markup) and the reviewer filter.

Paths: room pages live at mockup-m/<room>/, so the live bodies' ../assets/ and ../demos/ gain one more ../.
Room-to-room links stay in the theme.
"""
import html
import json
import os
import random
import re
import shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'themed', 'm')
OUT = os.path.join(ROOT, 'mockup-m')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape
NAME = 'Redline'


def esc(s):
    return html.escape(s, quote=False)


def qa(s):
    return html.escape(s, quote=True)


def plain(t):
    return re.sub(r'\s+', ' ', unesc(re.sub(r'<[^>]+>', '', t))).strip()


for i, r in enumerate(ROOMS):
    r['i'] = i
    r['plain'] = unesc(r['title'])
    r['cases'] = [it for it in r['items'] if it['kind'] == 'case']
    r['n'] = len(r['cases'])
    for k, it in enumerate(r['cases']):
        for key in ('links_html', 'thumb', 'sub', 'lede', 'body_html', 'title'):
            it.setdefault(key, '')
        it.setdefault('kickers', [])
        it['k'] = k
        it['code'] = '%d.%d' % (i + 1, k + 1)          # the section number: article.section
        it['pcode'] = '%s-%02d' % (r['letter'], k + 1)  # the project code the old pages and links use (L-01)
        it['count'] = '%02d / %02d' % (k + 1, r['n'])
        it['room'] = r
BY = {r['slug']: r for r in ROOMS}
CASE = {it['id']: it for r in ROOMS for it in r['cases']}
# live.json carries three lead images on the wrong project (fieldwork.jpg on rsctiktok, northfield.jpg on money,
# aftercare.jpg on mecfs) while the projects those files are named after have none: the old extractor ran on from an
# image-less index row into the next row. When a thumb is named after another project that has no thumb, give it back.
for _it in list(CASE.values()):
    _stem = os.path.splitext(os.path.basename(_it['thumb']))[0]
    if _stem and _stem != _it['id'] and _stem in CASE and not CASE[_stem]['thumb']:
        CASE[_stem]['thumb'], _it['thumb'] = _it['thumb'], ''
N_CASES = len(CASE)
SLUGS = [r['slug'] for r in ROOMS]
ID_ROOM = {}
for r in ROOMS:
    for it in r['items']:
        if it.get('id'):
            ID_ROOM[it['id']] = r['slug']
REDIRECT = json.loads(HOME['redirect_map'])
# Old #hashes whose target id no longer exists on the room page (true on the live site too): land them on the
# case that now holds that content, or on the room heading. Rendered as empty anchors.
ALIAS_TO = {'hollowhours': 'ascii', 'auroralake': 'ascii', 'prismtrip': 'ascii', 'notredame': 'ascii', 'empirestate': 'ascii',
            'skippy3d': 'ascii', 'livingprocesses': 'ascii', 'writing': 'noearcuttwice'}
ALIASES = {}
for _old, _room in REDIRECT.items():
    if _old not in ID_ROOM:
        ALIASES.setdefault((_room, ALIAS_TO.get(_old, 'top')), []).append(_old)


def alias_html(slug, target):
    return ''.join('<span class="alias" id="%s"></span>' % a for a in ALIASES.get((slug, target), []))


# Real links stated in the case text: the same pairs the live site shows as interchanges.
XCH = [
    dict(a='rscads', b='clayexplainers', key='same Blender clay kit',
         why='One Blender claymation kit powers both the client video ads and the explainer shorts.'),
    dict(a='citationgate', b='citationaudit', key='both check citations',
         why='The same check of whether a cited source backs up the claim, applied to court opinions in one build and clinical guidelines in the other.'),
    dict(a='skippy', b='atlas', key='Atlas finds the files',
         why='Skippy searches the private legal files on the Mac through Atlas’s index before a single word of the answer is written.'),
]
XOF = {}
for x in XCH:
    XOF.setdefault(x['a'], []).append((x['b'], x))
    XOF.setdefault(x['b'], []).append((x['a'], x))

TIERS = {'flagship': 'Flagship system', 'weekend': 'Weekend build', 'study': 'Study'}


def tier_tag(it):
    t = it.get('tier')
    return '<span class="tier tier--%s">%s</span>' % (t, TIERS[t]) if t else ''


# ------------------------------------------------------------------ body markup
def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b, slug):
    """Deepen relative paths by one level, keep room-to-room links in the theme, open outbound and demo links in a new tab."""
    b = re.sub(r'((?:src|href|poster)=")\.\./', r'\1../../', b)

    def a(m):
        t = m.group(0)
        hr = attr(t, 'href') or ''
        new = hr
        m2 = re.match(r'(?:https://mylesparslow\.com)?/(%s)/(?:index\.html)?(#[\w-]+)?$' % '|'.join(SLUGS), hr)
        m3 = re.match(r'\.\./\.\./(%s)/(?:index\.html)?(#[\w-]+)?$' % '|'.join(SLUGS), hr)
        if m2 or m3:
            g = m2 or m3
            new = ('' if g.group(1) == slug else '../%s/index.html' % g.group(1)) + (g.group(2) or '')
            if not new:
                new = '#top'
        elif hr.startswith('#') and hr[1:] in ID_ROOM and ID_ROOM[hr[1:]] != slug:
            new = '../%s/index.html%s' % (ID_ROOM[hr[1:]], hr)
        elif hr in ('/', 'https://mylesparslow.com/', '../../', '../../index.html'):
            new = '../index.html'
        if new != hr:
            t = t.replace('href="%s"' % hr, 'href="%s"' % new, 1)
            if new.startswith(('#', '../')) and not new.startswith('../../'):
                t = re.sub(r'\s(?:target|rel)="[^"]*"', '', t)
                return t
        if (re.match(r'https?://', new) or new.startswith('../../demos/') or new.startswith('../../assets/')) and 'target=' not in t:
            t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
        elif 'target="_blank"' in t and 'rel=' not in t:
            t = t.replace('<a ', '<a rel="noopener" ', 1)
        return t
    return re.sub(r'<a\b[^>]*>', a, b)


def img_size(path):
    """Pixel size of a JPEG or PNG on disk (the width/height attributes in the bodies are display sizes, not file sizes)."""
    try:
        with open(path, 'rb') as f:
            b = f.read()
    except OSError:
        return 0, 0
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return int.from_bytes(b[16:20], 'big'), int.from_bytes(b[20:24], 'big')
    i = 2
    while i + 9 < len(b) and b[i] == 0xFF:
        m, n = b[i + 1], int.from_bytes(b[i + 2:i + 4], 'big')
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(b[i + 7:i + 9], 'big'), int.from_bytes(b[i + 5:i + 7], 'big')
        i += 2 + n
    return 0, 0


# ------------------------------------------------------------------ attribution (the signature)
# Each "How it was built" note is cut into sentences, and sentences into clauses where a new grammatical subject
# starts (after a semicolon, a colon, a comma, or "and"). A clause is attributed to an author only when its subject is
# clearly "I" (Myles) or a named tool; the Claude model names (Opus, Sonnet, Haiku, Fable) count as Claude. A clause whose
# subject is anything else ("Built with Claude Code.", "The Lua runs in the browser", "a script recorded the run")
# stays neutral. Nothing is inferred from the meaning of the sentence, only from how it starts.
AUTHORS = [('myles', 'Myles', 'M'), ('claude', 'Claude', 'Cl'), ('chatgpt', 'ChatGPT', 'GP'), ('codex', 'Codex', 'Cx'),
           ('gemini', 'Gemini', 'Ge'), ('suno', 'Suno', 'Su'), ('local', 'Local models', 'Lm')]
ANAME = {k: n for k, n, _ in AUTHORS}
AINI = {k: i for k, _, i in AUTHORS}
LABELS = ('How it was built', 'How it was made', 'My role')      # the notes that are attributed

_VERBS = ('wrote|built|ran|did|made|took|found|kept|chose|set|read|drew|gave|had|led|caught|put|began|came|went|sent|held|said|asked|'
          'can|may|will|would|could|should|does|is|was|has|have')
_VERB = r'(?:(?:also|then|first|later|next|only|never|mostly)\s+)*(?:re-)?(?:[a-z]+ed|%s)\b' % _VERBS
_CL = (r'(?:Claude(?:\s+Code)?(?:\s+(?:Opus|Sonnet|Haiku|Fable))?(?:\s+\d[\d.]*)?(?:\s+\([^)]*\))?'
       r'|(?:[Aa]n?\s+)?(?:Opus|Sonnet|Haiku|Fable)(?:\s+\d[\d.]*)?(?:\s+(?:builders?|checker|reviewer))?)')
_SUBJ = [('myles', r'I'), ('claude', _CL), ('chatgpt', r'ChatGPT'), ('codex', r'Codex'),
         ('gemini', r'(?:Google\s+)?Gemini'), ('suno', r'Suno'),
         ('local', r'(?:[Aa]n?\s+(?:optional\s+)?)?(?:local\s+models?|Ollama|Qwen|Llama|Whisper)')]
_LEAD = r'(?:(?:And|But|Then|From there|Along the way|Later|First|Next|Also|Finally|After that)\s*,?\s+)?'
_AND = r'(?:(?:and|but)\s+)?'
_INTER = r'(?:\s*,[^,.;:]{1,48},)?'
WHO = [(a, re.compile(r'^\s*' + _AND + _LEAD + r'(?:%s)%s\s+%s' % (s, _INTER, _VERB))) for a, s in _SUBJ]
_DET = re.compile(r'^\s*(?:and\s+)?(?:a|an|the|it|each)\s+(?:\w+\s+){0,3}?(?:[a-z]+ed|wrote|ran|did|was|were|is|are|does|kept)\b')
_ABBR = re.compile(r'(?:\b[A-Z]|U\.S|e\.g|i\.e|vs|etc|No|Dr|Mr|Mrs|St)\.$')


def who(piece):
    t = unesc(re.sub(r'<[^>]+>', '', piece))
    for a, rx in WHO:
        if rx.match(t):
            return a
    return None


def _in_tag(s, p):
    return s.rfind('<', 0, p) > s.rfind('>', 0, p)


def _balanced(h):
    return h.count('<a ') == h.count('</a>') and h.count('<em>') == h.count('</em>') and h.count('<b>') == h.count('</b>')


def pieces(s):
    cuts = set()
    for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z]|&[lr]dquo;|<(?:a|em)\b)', s):
        if not _ABBR.search(s[:m.start()]) and not _in_tag(s, m.start()):
            cuts.add(m.start())
    for m in re.finditer(r'[;:,]\s+|\s+(?=(?:and|but)\s)', s):
        cut = m.start() + 1 if s[m.start()] in ';:,' else m.start()
        if _in_tag(s, cut):
            continue
        rest = unesc(re.sub(r'<[^>]+>', '', s[cut:cut + 260]))
        if any(rx.match(rest) for _, rx in WHO) or (s[m.start()] in ';,' and _DET.match(rest)):
            cuts.add(cut)
    cs = sorted(cuts)
    out, prev = [], 0
    for c in cs + [len(s)]:
        if c > prev:
            out.append(s[prev:c])
        prev = c
    # never leave a tag open across a cut: fold the piece into its neighbour
    merged = []
    for p in out:
        if merged and not _balanced(merged[-1]):
            merged[-1] += p
        else:
            merged.append(p)
    return merged


def attribute(inner):
    """-> (html with author spans, list of (author or None, plain-text length))."""
    ps = pieces(inner)
    groups = []                                    # [author, html]
    for p in ps:
        a = who(p)
        if groups and groups[-1][0] == a:
            groups[-1][1] += p
        else:
            groups.append([a, p])
    out, stats = [], []
    for a, h in groups:
        stats.append((a, len(plain(h))))
        if a is None:
            out.append(h)
            continue
        if a == 'myles':                                   # keep a lone "I" with the word after it, so the badge never strands it at a line end
            h = re.sub(r'^(\s*(?:and\s+)?(?:[A-Z][a-z]+(?: there| the way)?,?\s+)?)I\s+(?=[a-z])', r'\1I&nbsp;', h)
        m = re.match(r'^(\s*)(.*?)([;:,]?\s*)$', h, re.S)
        out.append('%s<span class="a a--%s" data-by="%s">%s</span>%s' % (m.group(1), a, a, m.group(2), m.group(3)))
    return ''.join(out), stats


NOTE = {}            # case id -> dict(n={author: statements}, ch={author|None: characters}, total=int, any=bool)


def note_stats(cid, stats):
    d = NOTE.setdefault(cid, dict(n={}, ch={}, total=0))
    for a, n in stats:
        d['ch'][a] = d['ch'].get(a, 0) + n
        d['total'] += n
        if a:
            d['n'][a] = d['n'].get(a, 0) + 1


def split_top_level(b, label_ok):
    """Pull the depth-0 <div class="made"> blocks whose label is in label_ok out of a body. -> (body, [block html])."""
    depth, starts, spans = 0, None, []
    for m in re.finditer(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>', b):
        tag, close, selfc = m.group(2).lower(), m.group(1), m.group(3)
        if tag in ('img', 'br', 'input', 'source', 'hr', 'meta', 'link') or selfc:
            continue
        if close:
            depth -= 1
            if starts is not None and depth == starts[0]:
                spans.append((starts[1], m.end()))
                starts = None
        else:
            if depth == 0 and tag == 'div' and 'class="made"' in m.group(0) and starts is None:
                starts = (0, m.start())
            depth += 1
    out, take = [], []
    for s, e in spans:
        blk = b[s:e]
        lab = re.search(r'<b>(.*?)</b>', blk)
        if lab and lab.group(1) in label_ok:
            take.append((s, e))
            out.append(blk)
    for s, e in reversed(take):
        b = b[:s] + b[e:]
    return b, out


def ab_html(cid, cls=''):
    """The small author bar: share of the note's text attributed to each author, from the same split as the underlines."""
    d = NOTE.get(cid)
    if not d or not d['total']:
        return '<span class="ab ab--none%s" role="img" aria-label="No build note to attribute"></span>' % cls
    segs, lab = [], []
    for a, name, _ in AUTHORS:
        c = d['ch'].get(a, 0)
        if c:
            pct = 100.0 * c / d['total']
            segs.append('<i style="flex:%.1f;background:var(--c-%s)"></i>' % (pct, a))
            lab.append('%s %d%%' % (name, round(pct)))
    nn = d['ch'].get(None, 0)
    lab.append('not attributed %d%%' % round(100.0 * nn / d['total']))
    return '<span class="ab%s" role="img" aria-label="Share of the build note: %s">%s<i class="ab__rest" style="flex:%.1f"></i></span>' % (
        cls, ', '.join(lab), ''.join(segs), 100.0 * nn / d['total'])


def who_badges(cid):
    au = authors_of(cid)
    if not au:
        return ''
    return '<span class="ix__who" aria-hidden="true">%s</span>' % ''.join('<span class="ini ini--%s">%s</span>' % (a, AINI[a]) for a in au)


def authors_of(cid):
    d = NOTE.get(cid)
    return [a for a, _, _ in AUTHORS if d and d['n'].get(a)]


def tally_text(cid):
    d = NOTE.get(cid)
    if not d:
        return ''
    bits = []
    for a, name, _ in AUTHORS:
        n = d['n'].get(a, 0)
        if n:
            bits.append('%d by %s' % (n, name if a != 'local' else 'a local model'))
    tot = sum(d['n'].values())
    if not tot:
        return 'No statement in this note starts with an author, so none is attributed.'
    return 'Attributed in this note: %s.' % ', '.join(bits)


def change_bar(cid):
    d = NOTE.get(cid)
    if not d or not d['n']:
        return ''
    tot = sum(d['n'].values())
    stops, at = [], 0.0
    for a, _, _ in AUTHORS:
        n = d['n'].get(a, 0)
        if n:
            nxt = at + 100.0 * n / tot
            stops.append('var(--c-%s) %.1f%% %.1f%%' % (a, at, nxt))
            at = nxt
    return '<span class="cb" aria-hidden="true" style="background:linear-gradient(to bottom,%s)"></span>' % ','.join(stops)


def dominant(cid):
    d = NOTE.get(cid)
    if not d or not d['n']:
        return 'var(--hair)'
    a = max((a for a, _, _ in AUTHORS if d['n'].get(a)), key=lambda a: d['n'][a])
    return 'var(--c-%s)' % a


# Attribute every note up front so the counts exist before any page is written.
def prep_notes():
    for r in ROOMS:
        for it in r['cases']:
            def f(m):
                inner, stats = attribute(m.group(3))
                note_stats(it['id'], stats)
                return m.group(1) + inner + m.group(4)
            it['body_a'] = re.sub(r'(<div class="made"><b>(%s)</b><p>)(.*?)(</p></div>)' % '|'.join(LABELS), f, it['body_html'], flags=re.S)


prep_notes()
ALL_STM = {a: 0 for a, _, _ in AUTHORS}
ALL_TOUCH = {a: 0 for a, _, _ in AUTHORS}
N_NOTES = len(NOTE)
STM_NEUTRAL = 0
for _cid, _d in NOTE.items():
    for _a, _n in _d['n'].items():
        ALL_STM[_a] += _n
        ALL_TOUCH[_a] += 1
STM_TOTAL = sum(ALL_STM.values())
CH_ATTR = sum(sum(v for a, v in d['ch'].items() if a) for d in NOTE.values())
CH_ALL = sum(d['total'] for d in NOTE.values())
ROOM_STM = {r['slug']: {a: sum(NOTE.get(it['id'], {}).get('n', {}).get(a, 0) for it in r['cases']) for a, _, _ in AUTHORS} for r in ROOMS}
ROOM_NOTES = {r['slug']: sum(1 for it in r['cases'] if it['id'] in NOTE) for r in ROOMS}


def print_summary():
    print('attribution: %d build notes in %d projects; %d attributed statements' % (sum(1 for _ in NOTE), N_CASES, STM_TOTAL))
    for a, name, _ in AUTHORS:
        print('  %-13s %3d statements in %2d projects' % (name, ALL_STM[a], ALL_TOUCH[a]))
    print('  %.0f%% of the note text sits in an attributed clause, %.0f%% is neutral' % (100.0 * CH_ATTR / CH_ALL, 100.0 - 100.0 * CH_ATTR / CH_ALL))


def sample_attributed(n=15, seed=7):
    rows = []
    for r in ROOMS:
        for it in r['cases']:
            for m in re.finditer(r'<span class="a a--(\w+)" data-by="\w+">(.*?)</span>', it['body_a'], re.S):
                rows.append((it['id'], m.group(1), plain(m.group(2))))
    random.Random(seed).shuffle(rows)
    return rows[:n]


# ------------------------------------------------------------------ chrome
THEME_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')

HEAD_SCRIPT = """<script>
(function(){var d=document.documentElement,t,v;d.className+=' js';
try{t=localStorage.getItem('mpm-theme');v=localStorage.getItem('mpm-view')}catch(e){}
if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
d.setAttribute('data-theme',t);d.setAttribute('data-view',v==='clean'?'clean':'all');})();
</script>"""


def chips():
    lis = ['<button type="button" class="chip" data-rev="all" aria-pressed="true"><span class="chip__t">Everyone</span></button>']
    for a, name, _ in AUTHORS:
        n = ALL_TOUCH[a]
        lis.append('<button type="button" class="chip" data-rev="%s" aria-pressed="false"%s><span class="sw sw--%s" aria-hidden="true"></span>'
                   '<span class="chip__t">%s</span><span class="chip__n">%d<span class="vh"> projects</span></span></button>'
                   % (a, '' if n else ' disabled', a, name, n))
    return ''.join(lis)


def review_bar(depth, cur):
    up = '../' * depth
    arts = []
    for r in ROOMS:
        arts.append('<li><a href="%s%s/index.html"%s><b aria-hidden="true">%d</b><span>%s</span><i>%d<span class="vh"> projects</span></i></a></li>'
                    % (up, r['slug'], ' aria-current="page"' if r['slug'] == cur else '', r['i'] + 1, esc(r['short']), r['n']))
    return ('<header class="rb" id="rb"><nav class="rb__bar" aria-label="Site">'
            '<a class="rb__home" href="%sindex.html"%s>Myles Parslow<span class="vh"> (home)</span></a>'
            '<div class="rb__view js-only" role="group" aria-label="Markup view"><button type="button" id="v-all" data-view="all" aria-pressed="true">All markup</button>'
            '<button type="button" id="v-clean" data-view="clean" aria-pressed="false">No markup</button></div>'
            '<button type="button" class="rb__menu js-only" id="menu" aria-expanded="false" aria-controls="rb-more">Review</button>'
            '<ul class="rb__arts" aria-label="Articles">%s</ul>'
            '<div class="rb__more" id="rb-more">'
            '<div class="rb__rev js-only"><button type="button" class="rb__revbtn" id="rev-btn" aria-expanded="false" aria-controls="rev-pop">Show changes by <b id="rev-cur">everyone</b></button>'
            '<div class="rb__pop" id="rev-pop" role="group" aria-label="Show changes by"><p class="rb__lab">Show changes by</p>%s<p class="rb__note">Attributed from each project’s How it was built note. The number is how many projects a reviewer appears in.</p></div></div>'
            '<button type="button" class="rb__theme js-only" id="theme" aria-label="Switch between light and dark">%s</button>'
            '</div></nav><p class="vh" id="rev-status" role="status" aria-live="polite"></p></header>'
            ) % (up, ' aria-current="page"' if cur == 'home' else '', ''.join(arts), chips(), THEME_ICON)


def page(title, desc, depth, cls, inner, cur, head_extra='', tail=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en" data-view="all">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n'
            '<link rel="preload" href="%sfonts/Tinos-Regular.woff2" as="font" type="font/woff2" crossorigin>\n'
            '<link rel="preload" href="%sfonts/AtkinsonNext.woff2" as="font" type="font/woff2" crossorigin>\n'
            '%s\n%s<link rel="stylesheet" href="%sm.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="%s">%s</a>\n%s\n<div class="desk">\n%s\n</div>\n'
            '<script src="%sm.js" defer></script>\n%s</body>\n</html>\n') % (
        esc(title), qa(desc), up, up, up, HEAD_SCRIPT, head_extra, up, cls,
        '#index' if depth == 0 else '#main', 'Skip to the rooms' if depth == 0 else 'Skip to the projects', review_bar(depth, cur), inner, up, tail)


def contact_mail():
    return re.search(r'href="mailto:([^"]+)"', HOME['foot_html']).group(1)


def footer_html(depth):
    foot = HOME['foot_html']
    mail = contact_mail()
    gh = re.search(r'<a href="(https://github.com/[^"]*)">GitHub</a>', foot).group(1)
    lp = re.search(r'<a href="([^"]*)">Legal portfolio</a>', foot).group(1)
    sign = re.search(r'<span>([^<]*)</span>\s*</div>', foot).group(1)
    up = '../' * depth
    extra = '' if depth == 0 else '<a href="../index.html#tools">Which AI for what by project &rarr;</a>'
    extra += '<a href="%s../pets/index.html">Meet the cats</a>' % up
    return ('<footer class="row foot" id="contact" aria-labelledby="h-foot"><div class="c2">'
            '<p class="lab">Contact</p><h2 id="h-foot" class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><a href="mailto:%s">%s</a> <button type="button" class="btn js-only" id="copy" data-copy="%s">Copy address</button> <span id="copystat" class="foot__st" aria-live="polite"></span></p>'
            '<p class="foot__row" style="--n:%d"><a href="%s" target="_blank" rel="noopener">GitHub</a><a href="%s" target="_blank" rel="noopener">Legal portfolio</a><a href="#top">Back to top &uarr;</a>%s</p>'
            '<p class="foot__mlp"><b>Want this for your business?</b> Through MLP Consulting I build fast websites, automated follow-up and private, human-approved AI tools for owner-run businesses and legal teams. <a class="nw" href="https://mlpconsults.com/" target="_blank" rel="noopener">Visit MLPConsults.com &rarr;</a></p>'
            '<p class="foot__sign"><span>%s</span></p></div></footer>') % (mail, mail, mail, 4 if depth == 0 else 3, gh, lp, extra, sign)


# ------------------------------------------------------------------ balloons
def key_balloon(scope=None):
    """The reviewer key. scope None = the whole document, or a room slug."""
    rows = []
    for a, name, ini in AUTHORS:
        n = ALL_STM[a] if scope is None else ROOM_STM[scope][a]
        if not n:
            continue
        t = ALL_TOUCH[a] if scope is None else sum(1 for it in BY[scope]['cases'] if NOTE.get(it['id'], {}).get('n', {}).get(a))
        rows.append('<li><span class="a a--%s" data-by="%s">%s</span> <span class="key__n">%d statement%s in %d project%s</span></li>'
                    % (a, a, name, n, '' if n == 1 else 's', t, '' if t == 1 else 's'))
    what = 'in this document' if scope is None else 'in this article'
    return ('<details class="bal bal--key" open><summary class="bal__h"><b>Key to the markup</b></summary>'
            '<p>Each project’s How it was built note is split into sentences, and a sentence is attributed to its grammatical subject when that is “I” (Myles) or a named tool. '
            'Every other sentence stays neutral. Counts %s, attributed from each project’s How it was built note:</p>'
            '<ul class="key">%s</ul></details>') % (what, ''.join(rows))


# ------------------------------------------------------------------ home
def routes_html():
    cards = []
    for k, rt in enumerate(HOME.get('routes', [])):
        ln = BY[rt['line']]
        stops = []
        for cid, why in rt['stops']:
            it = CASE[cid]
            stops.append('<li><a href="%s/index.html#%s"><span class="code">%s</span> <span class="t">%s</span></a><span class="why">%s</span></li>'
                         % (it['room']['slug'], cid, it['pcode'], it['title'], why))
        cards.append('<li class="row term" id="route-%s"><div class="c2"><span class="term__no" aria-hidden="true">%d.</span><p class="lab">Route %d</p><h3>%s</h3><p class="term__p">%s</p>'
                     '<ol class="term__stops">%s</ol><p class="term__more"><a class="more" href="%s/index.html">Explore all %d %s builds &rarr;</a></p></div></li>'
                     % (rt['key'], k + 1, k + 1, rt['who'], rt['pitch'], ''.join(stops), ln['slug'], ln['n'], esc(ln['short'])))
    if not cards:
        return ''
    return ('<section class="start" id="start" aria-labelledby="h-start"><div class="row hd"><div class="c2"><p class="lab">Summary of terms</p>'
            '<h2 id="h-start" class="art__t">Three routes, one for each kind of visitor</h2>'
            '<p class="art__l">%d projects is a lot to explore cold. Start with the route built for what you care about, or go straight to the full index below.</p></div></div>'
            '<ol class="terms">%s</ol>'
            '<div class="row"><div class="c2"><p class="start__alt"><span>Just browsing?</span> <button type="button" class="btn js-only" id="surprise">Take me somewhere random</button> '
            '<a href="#index">Open the full index &darr;</a></p></div></div></section>') % (N_CASES, ''.join(cards))


def status_line():
    ns = N_CASES
    return ('%d sections in %d articles. %d of them have a How it was built note, which holds %d attributed statements: %d by Myles and %d by AI tools. '
            'Everything else in the notes is neutral.') % (ns, len(ROOMS), N_NOTES, STM_TOTAL, ALL_STM['myles'], STM_TOTAL - ALL_STM['myles'])


def home():
    hhtml = HOME['hero_html']
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    tb = ('<header class="row tb" id="top"><div class="c2"><p class="tb__k"><b>Draft for review</b> <span aria-hidden="true">&middot;</span> %d projects in %d articles</p>'
          '<h1 class="tb__t">Myles Parslow makes things with AI.</h1></div>'
          '<aside class="mg" aria-label="Key"><div class="mg__top">%s</div></aside></header>') % (N_CASES, len(ROOMS), key_balloon())
    rec = ''.join('<li class="row rec"><span class="rec__no" aria-hidden="true">%s</span><div class="c2 rec__b"><p class="rec__fig">%s</p><p class="rec__t">%s</p></div></li>'
                  % (chr(66 + k), dd, dt) for k, (dt, dd) in enumerate(stats))
    recit = ('<section class="recitals" aria-labelledby="h-rec"><div class="row"><div class="c2"><h2 id="h-rec" class="lab">Recitals</h2></div></div><ol class="recs">'
             '<li class="row rec rec--lede"><span class="rec__no" aria-hidden="true">A</span><div class="c2 rec__b"><p class="rec__lede">%s</p></div>'
             '<aside class="mg" aria-label="Review status"><div class="mg__top"><div class="bal bal--ref"><p class="bal__h"><b>Review status</b></p><p>%s</p></div></div></aside></li>%s</ol></section>') % (lede, status_line(), rec)

    def ser(r):
        rows = []
        for it in r['cases']:
            see = ''.join('<span class="see">See also <a href="%s/index.html#%s">%s</a> in %s</span>'
                          % (CASE[o]['room']['slug'], o, CASE[o]['title'], esc(CASE[o]['room']['short'])) for o, _ in XOF.get(it['id'], []))
            rows.append('<li data-authors="%s"><div class="ix__l"><a class="ix__a" href="%s/index.html#%s"><span class="n">%s</span><span class="code">%s</span> <span class="t">%s</span></a> '
                        '<span class="s">%s</span></div>%s<div class="ix__m">%s%s</div>%s</li>'
                        % (' '.join(authors_of(it['id'])), r['slug'], it['id'], it['code'], it['pcode'], it['title'], it['sub'], ab_html(it['id']), tier_tag(it), see, who_badges(it['id'])))
        st = ROOM_STM[r['slug']]
        tot = sum(st.values())
        bits = ', '.join('%d by %s' % (st[a], 'a local model' if a == 'local' else n) for a, n, _ in AUTHORS if st[a])
        return ('<section class="art" id="ser-%s" aria-labelledby="hs-%s"><div class="row hd"><div class="c2"><h3 id="hs-%s" class="art__t"><a href="%s/index.html"><span class="art__no">Article %d</span> %s</a> '
                '<span class="art__n">%d projects</span></h3><p class="art__l">%s</p></div>'
                '<aside class="mg" aria-label="Notes on Article %d"><div class="mg__top"><div class="bal bal--ref"><p class="bal__h"><b>Article %d</b></p>'
                '<p>%d of %d projects carry a build note. %s</p></div></div></aside></div>'
                '<ol class="ix">%s</ol></section>') % (
            r['slug'], r['slug'], r['slug'], r['slug'], r['i'] + 1, r['title'], r['n'], r['lede'], r['i'] + 1, r['i'] + 1,
            ROOM_NOTES[r['slug']], r['n'], ('Attributed statements: %s.' % bits) if tot else 'No statement is attributed.', ''.join(rows))
    arts = ''.join(ser(BY[s]) for s in SLUGS)
    index = ('<section class="index" id="index" aria-labelledby="h-ix"><div class="row hd"><div class="c2"><p class="lab">Index of sections</p>'
             '<h2 id="h-ix" class="art__t">All %d projects</h2>'
             '<p class="art__l">Every project, listed by room. Choose any entry to jump straight to its write-up.</p>'
             '<ul class="tierkey"><li><span class="tier tier--flagship">Flagship system</span> <span><b>Flagship system:</b> the full-scale production builds. Every guided route is made of them.</span></li>'
             '<li><span><span class="tier tier--weekend">Weekend build</span> <span class="tier tier--study">Study</span></span> <span><b>Weekend build</b> and <b>Study:</b> Focused prototypes, creative sprints and benchmarks.</span></li></ul>'
             '<p class="ix__how">The bar at the end of each line is the share of that project’s How it was built note attributed to each author. Colours as in the key at the top. A dashed bar means the project has no build note.</p>'
             '</div></div>%s</section>') % (N_CASES, arts)

    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><b>%s.</b> <a href="%s/index.html#%s">%s</a> (%s) and <a href="%s/index.html#%s">%s</a> (%s). %s</li>'
                  % (esc(x['key'][0].upper() + x['key'][1:]), a['room']['slug'], a['id'], a['title'], esc(a['room']['short']),
                     b['room']['slug'], b['id'], b['title'], esc(b['room']['short']), esc(x['why'])))
    cross = ('<section class="cross" id="cross" aria-labelledby="h-cross"><div class="row hd"><div class="c2"><p class="lab">Related sections</p>'
             '<h2 id="h-cross" class="art__t">Projects that share a part</h2></div></div>'
             '<div class="row"><div class="c23"><ul class="cross__l">%s</ul></div></div></section>') % ''.join(xk)

    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="notes" id="rules" aria-labelledby="h-rules"><div class="row hd"><div class="c2"><p class="lab">General provisions &middot; %s</p>'
                  '<h2 id="h-rules" class="art__t">%s</h2></div></div><div class="row"><div class="c23"><ol class="notes__l">%s</ol></div></div></section>') % (
        r_eb, r_t, ''.join('<li><span class="gp__n" aria-hidden="true">%d.</span><h3>%s</h3><p>%s</p></li>' % (int(n), t, p) for n, t, p in rules))

    th = HOME['tools_html']
    t_eb = re.search(r'<p class="eyebrow">(.*?)</p>', th).group(1)
    t_t = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', th, re.S).group(1)
    t_l = re.search(r'<p class="sec-lede">(.*?)</p>', th, re.S).group(1)
    trs = re.findall(r'<article class="trow">(.*?)</article>', th, re.S)
    first = sum(1 for _ in re.finditer(r'<article class="trow">', th.split('<details')[0]))
    # the data's summary says "Show all 48 projects", a count that went stale; this says how many rows the disclosure holds
    t_sum = 'Show the other %d projects' % (len(trs) - first)

    def trow(row):
        name = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        cells = re.findall(r'<span class="lab">(.*?)</span>\s*<p>(.*?)</p>', row, re.S)
        assert 1 <= len(cells) <= 2, name
        std = ('Built with', 'Runs on')

        def cell(k):
            if k >= len(cells):
                return '<span class="sch__none">&mdash;</span>'
            lab, p = cells[k]
            return '<span class="sch__l%s">%s</span>%s' % ('' if lab == std[k] else ' sch__lx', lab, p)
        return '<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (name, cell(0), cell(1))
    head = '<thead><tr><th scope="col">Project</th><th scope="col">Built with</th><th scope="col">Runs on</th></tr></thead>'
    tools_html = ('<section class="sch" id="tools" aria-labelledby="h-tools"><div class="row hd"><div class="c2"><p class="lab">Schedule 1 &middot; %s</p>'
                  '<h2 id="h-tools" class="art__t">%s</h2><p class="art__l">%s</p></div></div>'
                  '<div class="row"><div class="c23"><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div>'
                  '<details class="sch__more"><summary>%s</summary><div class="sch__w"><table class="sch__t">%s<tbody>%s</tbody></table></div></details></div></div></section>'
                  ) % (t_eb, t_t, t_l, head, ''.join(trow(x) for x in trs[:first]), t_sum, head, ''.join(trow(x) for x in trs[first:]))

    notice = ('<aside class="row fn" id="archive" aria-labelledby="h-rev"><div class="c2"><p class="lab" id="h-rev">Footnote</p>'
              '<p class="fn__p"><b>Style archive.</b> You&rsquo;re looking at: %s. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a href="../styles/index.html">See every version &rarr;</a></p></div></aside>') % (NAME, N_CASES)

    inner = '<main id="main" class="page">\n' + '\n'.join([tb, recit, routes_html(), index, cross, rules_html, tools_html, notice]) + '\n' + footer_html(0) + '\n</main>'
    redirect = '<script>(function(){var M = %s;\nvar h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    desc = 'Myles Parslow: %d builds with AI, from law-firm software to novels and games, set out as a draft in review, with each write-up marked up to show what he did and what the AI did.' % N_CASES
    return page('Myles Parslow', desc, 0, 'pg-home', inner, 'home', redirect)


# ------------------------------------------------------------------ rooms
def ask_html(r, it):
    """A low-friction way to reach out from the case itself: a prefilled email, no form. Written as Myles's closing comment."""
    name = unesc(plain(it['title']))
    if r['slug'] in ('legal', 'business') or it.get('tier') == 'flagship':
        subj, lead, body, cta = ('Walkthrough: ' + name, 'Want to see %s running?' % it['title'],
                                 'I can walk you through it on a short screen share and answer questions about how it was built and what it would take for your team.',
                                 'Book a walkthrough')
    else:
        subj, lead, body, cta = ('About ' + name, 'Questions about %s?' % it['title'],
                                 'Happy to talk through how it was made and which AI did which part.', 'Email me')
    href = 'mailto:%s?subject=%s' % (contact_mail(), quote(subj))
    return ('<aside class="bal bal--me ask" aria-label="Contact about %s"><p class="bal__h"><span class="ini ini--myles" aria-hidden="true">M</span><b>Comment from Myles</b></p>'
            '<p class="ask__t"><b>%s</b> %s</p>'
            '<a class="btn" href="%s">%s &rarr;</a></aside>') % (qa(name), lead, body, qa(href), cta)


def section(r, it):
    cid = it['id']
    body = fix_body(it['body_a'], r['slug'])
    body, notes = split_top_level(body, LABELS)
    kick = tier_tag(it) + ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    refs = ''
    for o, x in XOF.get(cid, []):
        oc = CASE[o]
        refs += ('<div class="bal bal--ref"><p class="bal__h"><b>Related section</b></p><p class="xref">See also <a href="../%s/index.html#%s">%s</a> in %s. %s</p></div>'
                 % (oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    note_html = ''
    for nb in notes:
        inner = nb[len('<div class="made">'):-len('</div>')]
        note_html += ('<aside class="bal bal--note made" id="n-%s" style="--ac:%s">%s<p class="bal__tally">%s</p>%s</aside>'
                      % (cid, dominant(cid), inner, esc(tally_text(cid)), ab_html(cid)))
    plate = ''
    if it['thumb']:
        src = it['thumb']
        pw, ph = img_size(os.path.join(ROOT, src.replace('../', '', 1)))
        if pw and pw < 1100:                      # some "hd" thumbs are only 560 px wide: use the case's own larger shot when it has a similar one
            for t in re.findall(r'<img\b[^>]*>', it['body_html']):
                rel = attr(t, 'src') or ''
                if not rel.startswith('../assets/') or 'class="after' in t:
                    continue
                iw, ih = img_size(os.path.join(ROOT, rel[3:]))
                if iw >= 1100 and ih and abs(iw / ih - pw / ph) < 0.25:
                    src, pw, ph = rel, iw, ih
                    break
        if re.search(r'<img\b[^>]*src="%s"' % re.escape(src), it['body_html']):
            src = None                              # the same image is already a figure in the body: show it once
        if not pw or not ph:
            pw, ph = 1120, 700
        cap = ' style="max-width:%dpx"' % pw if pw < 1100 else ''      # never stretch a small file past its own width
        plate = '' if not src else ('<figure class="plate%s"><img src="%s" alt="" width="%d" height="%d" loading="lazy" decoding="async"%s></figure>'
                 % (' plate--tall' if pw / ph < 1.05 else '', qa('../' + src), pw, ph, cap))
    desc = ' aria-describedby="n-%s"' % cid if notes else ''
    return ('<article class="row sec" id="%s" aria-labelledby="t-%s"%s data-authors="%s" style="--sn:\'%s\';--ac:%s">%s'
            '<div class="c2 sec__m"><header class="sec__h"><h2 class="sec__t" id="t-%s"><span class="n">%s</span>%s<span class="sec__tt">%s</span></h2>'
            '<p class="sec__sub">%s</p><p class="sec__meta">%s<span class="cnt">%s</span></p></header>'
            '<div class="sec__lede"><p>%s</p></div>%s<div class="cbody">%s</div><div class="sec__ask">%s</div></div>'
            '<aside class="mg" aria-label="Comments on section %s"><div class="mg__top">%s%s</div></aside></article>') % (
        cid, cid, desc, ' '.join(authors_of(cid)), it['code'], dominant(cid), change_bar(cid),
        cid, it['code'], alias_html(r['slug'], cid), it['title'], it['sub'], kick, it['count'], it['lede'], plate, body,
        ask_html(r, it), it['code'], note_html, refs)


def room(r):
    i = r['i']
    parts, lst, g = [], [], 0
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            g += 1
            gh = fix_body(it['html'], r['slug']).replace('<h2 class="gdiv__t">', '<p class="lab">Part %s</p><h2 class="gdiv__t">' % chr(64 + g), 1)
            parts.append('<div class="row grp"><div class="c2">%s</div></div>' % gh)
            t = re.search(r'gdiv__t">(.*?)</h2>', it['html'], re.S).group(1)
            lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t))
        elif k == 'extra':
            parts.append('<div class="row extra"><div class="c2">%s</div></div>' % fix_body(it['html'], r['slug']))
            t = re.search(r'<h2[^>]*>(.*?)</h2>', it['html'], re.S)
            if t and it.get('id'):
                lst.append('<li class="g"><a href="#%s">%s</a></li>' % (it['id'], t.group(1)))
        else:
            parts.append(section(r, it))
            lst.append('<li><a href="#%s"><span class="n">%s</span><span class="tl"><span class="code">%s</span> %s</span></a></li>' % (it['id'], it['code'], it['pcode'], it['title']))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="next" href="../%s/index.html"><span class="lab">Next article</span>'
                  '<span class="next__t"><span class="art__no">Article %d</span> %s &rarr;</span></a>') % (nxt['slug'], nxt['i'] + 1, nxt['title'])
    else:
        change = ('<a class="next" href="../index.html"><span class="lab">End of the document</span>'
                  '<span class="next__t">Back to the start (Home) &rarr;</span></a>')
    groups = sum(1 for it in r['items'] if it['kind'] == 'group')
    glance = ''
    if r['slug'] == 'legal':
        glance = ('<p class="rhead__note">%d tools in %d groups, flagships first, then by practice area. <span class="tier tier--flagship">Flagship system</span> marks the largest builds.</p>') % (r['n'], groups)
    head = ('<header class="row tb tb--room" id="top"><div class="c2">' + alias_html(r['slug'], 'top') +
            '<p class="tb__k"><b>Article %d</b> <span aria-hidden="true">&middot;</span> %s &middot; %s</p>'
            '<h1 class="tb__t tb__t--room"><a href="../index.html" title="Back to the start">%s</a></h1>'
            '<p class="rhead__lede">%s</p>%s</div>'
            '<aside class="mg" aria-label="Key"><div class="mg__top">%s</div></aside></header>') % (
        i + 1, r['eyebrow'], '%d projects' % r['n'], r['title'], r['lede'], glance, key_balloon(r['slug']))
    toc = ('<nav class="row toc" id="list" aria-label="%s projects"><div class="c2"><details class="toc__d" open><summary><span class="lab">Contents &middot; %d projects</span></summary>'
           '<ol>%s</ol></details></div></nav>') % (esc(r['short']), r['n'], ''.join(lst))
    inner = (head + '\n' + toc + '\n<main id="main" class="sheet">\n%s\n</main>' % '\n'.join(parts) +
             '\n<div class="row"><div class="c2">' + change + '</div></div>\n' + footer_html(1))
    return page('%s — Myles Parslow' % r['plain'], plain(r['lede']), 1, 'pg-room room-%s' % r['slug'],
                '<div class="page">\n' + inner + '\n</div>', r['slug'])


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, 'index.html'), home())
    for r in ROOMS:
        write(os.path.join(OUT, r['slug'], 'index.html'), room(r))
    for name in ('m.css', 'm.js'):
        shutil.copyfile(os.path.join(SRC, name), os.path.join(OUT, name))
    dst = os.path.join(OUT, 'fonts')
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(SRC, 'fonts'), dst)
    assert sum(r['n'] for r in ROOMS) == N_CASES
    import importlib.util
    spec = importlib.util.spec_from_file_location('add_switcher', os.path.join(ROOT, 'themed', 'add_switcher.py'))
    sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw); sw.run('m')
    print('mockup-m: document + %d rooms, %d projects' % (len(ROOMS), N_CASES))
    print_summary()


if __name__ == '__main__':
    main()
    import sys
    if '--sample' in sys.argv:
        for cid, a, t in sample_attributed():
            print('  [%-7s] %-16s %s' % (a, cid, t))
