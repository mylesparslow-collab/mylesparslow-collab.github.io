#!/usr/bin/env python3 -I
"""Mockup I, "Transit Map": rebuild mockup-i/ from themed/live.json (stdlib only).

The five rooms are five lines, each project a station. The network map is inline SVG laid out here:
routes are octilinear waypoint lists, stations are spaced evenly between pinned stations, and labels
are placed by a greedy solver with a box/segment collision check. The render fails if any label
still collides.

Writes mockup-i/index.html, mockup-i/<room>/index.html, mockup-i/i.css, mockup-i/i.js.
Run: python3 -I themed/render_i.py
"""
import html
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'mockup-i')
D = json.load(open(os.path.join(ROOT, 'themed', 'live.json'), encoding='utf-8'))
HOME, ROOMS = D['home'], D['rooms']
unesc = html.unescape


def esc(s):
    return html.escape(s, quote=False)


def qa(s):
    return html.escape(s, quote=True)


def plain(t):
    return re.sub(r'\s+', ' ', unesc(re.sub(r'<[^>]+>', '', t))).strip()


# ------------------------------------------------------------------ lines
LINE = {
    'legal':    dict(c='#0019a8', fg='#ffffff'),
    'business': dict(c='#00843d', fg='#ffffff'),
    'creative': dict(c='#e32017', fg='#ffffff'),
    'design':   dict(c='#ffd300', fg='#16161a'),
    'research': dict(c='#9b0058', fg='#ffffff'),
}
for i, r in enumerate(ROOMS):
    r['i'] = i
    r['plain'] = unesc(r['title'])
    r.update(LINE[r['slug']])
    r['cases'] = [it for it in r['items'] if it['kind'] == 'case']
    r['n'] = len(r['cases'])
    zone, zname = 1, ''
    seen_group = False
    for it in r['items']:
        if it['kind'] == 'group':
            if seen_group:
                zone += 1
            seen_group = True
            zname = plain(re.search(r'gdiv__t">(.*?)</h2>', it['html'], re.S).group(1))
            it['zone'] = zone
        elif it['kind'] == 'case':
            it['zone'], it['zname'] = zone, zname
    for k, it in enumerate(r['cases']):
        it['k'] = k
        it['code'] = '%s-%02d' % (r['letter'], k + 1)
        it['room'] = r
BY = {r['slug']: r for r in ROOMS}
CASE = {it['id']: it for r in ROOMS for it in r['cases']}
N_CASES = len(CASE)

# Interchanges: real links stated in the case text (see the legend copy for each).
XCH = [
    dict(a='rscads', b='clayexplainers', key='same Blender clay kit',
         why='The clay explainers are made with the same Blender clay kit as the business ads.'),
    dict(a='citationgate', b='citationaudit', key='both check citations',
         why='Both check whether a cited source says what it is cited for: court opinions in one, medical papers in the other.'),
]
XOF = {}
for x in XCH:
    XOF.setdefault(x['a'], []).append((x['b'], x))
    XOF.setdefault(x['b'], []).append((x['a'], x))

# ------------------------------------------------------------------ geometry helpers
S2 = math.sqrt(0.5)
DIRV = {'N': (0, -1), 'NE': (S2, -S2), 'E': (1, 0), 'SE': (S2, S2), 'S': (0, 1), 'SW': (-S2, S2), 'W': (-1, 0), 'NW': (-S2, -S2)}


def seglen(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def octi_ok(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    return abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6


def at(pts, d):
    """Point and unit direction at distance d along a polyline."""
    for i in range(len(pts) - 1):
        L = seglen(pts[i], pts[i + 1])
        if d <= L + 1e-9 or i == len(pts) - 2:
            t = 0 if L == 0 else d / L
            a, b = pts[i], pts[i + 1]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        d -= L
    raise ValueError


def dist_of(pts, p):
    """Distance along the polyline of a point that lies on it."""
    acc = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = seglen(a, b)
        if L and abs((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / L < 0.6:
            t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (L * L)
            if -1e-6 <= t <= 1 + 1e-6:
                return acc + t * L
        acc += L
    raise ValueError('pin %r is not on the route' % (p,))


def plen(pts):
    return sum(seglen(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ------------------------------------------------------------------ the network (design input)
# Hub at (CX, CY). Paired lines run 14px apart; each interchange is a capsule across a pair.
CX, CY = 700, 450
G = 14  # lane pitch
h = G / 2
o = round(h * S2, 3)


def P(x, y):
    return (round(x, 3), round(y, 3))


def along(p, dname, L):
    v = DIRV[dname]
    return P(p[0] + v[0] * L, p[1] + v[1] * L)


# lanes leaving the hub
HUB_NE = P(CX + o, CY - o)   # NE side of a NW-SE pair
HUB_SW = P(CX - o, CY + o)   # SW side of a NW-SE pair
# Legal + Research run as a NW pair out of the hub (Legal on the NE side), meeting at L09/R09.
PAIR = 330
L_bend = along(HUB_NE, 'NW', PAIR)
R_end = along(HUB_SW, 'NW', PAIR - 30)
# Business over Creative run east out of the hub, meeting at B03/C03.
B0, C0 = P(CX, CY - h), P(CX, CY + h)
BC_x = CX + 330
# Design + Research run as a SE pair out of the hub (Design on the NE side), meeting at D06/R02.
DR = 140  # distance from hub to the D06/R02 capsule along SE

ROUTE = {}
PINS = {}
SIDES = {}
WRAPW = {'legal': 176, 'research': 290, 'business': 150, 'creative': 128, 'design': 124}

# Legal: hub -> NW (pair with Research) -> N column
ROUTE['legal'] = [HUB_NE, L_bend, P(L_bend[0], 34)]
PINS['legal'] = {0: along(HUB_NE, 'NW', 52), 8: along(HUB_NE, 'NW', PAIR - 30), 9: P(L_bend[0], L_bend[1] - 27), 19: P(L_bend[0], 34)}
SIDES['legal'] = ['NE'] * 9 + ['E'] * 11

# Research: R01 (stub end) -> R02 -> hub -> NW (pair with Legal) -> R09
r_stub = along(HUB_SW, 'SE', DR + 50)
ROUTE['research'] = [P(r_stub[0], r_stub[1] + 60), r_stub, HUB_SW, R_end]
PINS['research'] = {0: P(r_stub[0], r_stub[1] + 60), 1: along(HUB_SW, 'SE', DR), 2: along(HUB_SW, 'NW', 84), 9: R_end}
SIDES['research'] = ['W', 'SW'] + ['SW'] * 7 + ['W']

# Business: hub -> E (over Creative) -> NE -> N column
b_turn = P(BC_x + 50, B0[1])
b_up = along(b_turn, 'NE', 60)
ROUTE['business'] = [B0, b_turn, b_up, P(b_up[0], 40)]
PINS['business'] = {0: P(CX + 90, B0[1]), 2: P(BC_x, B0[1]), 3: P(b_up[0], b_up[1] - 40), 5: P(b_up[0], 280), 12: P(b_up[0], 40)}
SIDES['business'] = ['N'] * 3 + ['E'] * 10

# Creative: hub -> E (under Business) -> SE -> E (over Design) -> end
c_turn = P(BC_x + 50, C0[1])
D_low = 590
c_y = D_low - G
c_down = along(c_turn, 'SE', (c_y - C0[1]) / S2)
CD_x = c_down[0] + 120
ROUTE['creative'] = [C0, c_turn, c_down, P(CD_x + 420, c_y)]
PINS['creative'] = {0: P(CX + 150, C0[1]), 2: P(BC_x, C0[1]), 4: P(CD_x, c_y), 8: P(CD_x + 420, c_y)}
SIDES['creative'] = ['S', 'S', 'S', 'NE', 'N', 'N', 'N', 'N', 'N']

# Design: D01..D05 on a W then SW arm, hub, D06 on the SE pair, then E under Creative
d_w = P(470, CY)
d_end = along(d_w, 'SW', 200)
d_bend = along(HUB_NE, 'SE', (D_low - HUB_NE[1]) / S2)
ROUTE['design'] = [d_end, d_w, P(CX, CY)]
PINS['design'] = {0: d_end, 3: P(CX - 150, CY)}
SIDES['design'] = ['SE', 'SE', 'SE', 'S']

# The one geographic flourish: a river through the empty middle, never under a label.
RIVER_W = 15
RIVER = [P(650, -40), P(650, 146), P(804, 300.5), P(1300, 300.5), P(1360, 240.5), P(1800, 240.5)]

DEBUG = '--debug' in sys.argv
ORDER = ['legal', 'business', 'creative', 'design', 'research']

# ------------------------------------------------------------------ text metrics (Overpass 600, em units)
CW = {}
for ch in 'iljI.,:;\'!|': CW[ch] = 0.26
for ch in 'frt': CW[ch] = 0.36
for ch in 'mw': CW[ch] = 0.82
for ch in 'MW': CW[ch] = 0.88
for ch in '0123456789': CW[ch] = 0.58
CW.update({' ': 0.25, '-': 0.36, '/': 0.40, '&': 0.68, '+': 0.58, '’': 0.26, ',': 0.26, '(': 0.32, ')': 0.32})
FS = 14.0
LH = 16.5
WRAP = 128


def tw(s, fs=FS):
    w = 0.0
    for ch in s:
        if ch in CW:
            w += CW[ch]
        elif ch.isupper():
            w += 0.66
        else:
            w += 0.555
    return w * fs


def wrap(s, maxw=WRAP):
    words, lines, cur = s.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if cur and tw(t) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


# ------------------------------------------------------------------ collision geometry
def rect_hits_seg(r, a, b, pad):
    x0, y0, x1, y1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


def rr(a, b, pad=0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


# ------------------------------------------------------------------ layout
def layout():
    segs = []     # (a, b, pad, owner)
    stations = []
    for slug in ORDER:
        pts = ROUTE[slug]
        for i in range(len(pts) - 1):
            if not octi_ok(pts[i], pts[i + 1]):
                raise SystemExit('route %s segment %d is not octilinear: %r -> %r' % (slug, i, pts[i], pts[i + 1]))
            segs.append((pts[i], pts[i + 1], 6.5, slug))
        r = BY[slug]
        pins = sorted((k, dist_of(pts, p)) for k, p in PINS[slug].items())
        if pins[0][0] != 0 or pins[-1][0] != r['n'] - 1:
            raise SystemExit('pins for %s must include the first and last station' % slug)
        ds = {}
        for (k0, a), (k1, b) in zip(pins, pins[1:]):
            for k in range(k0, k1 + 1):
                ds[k] = a + (b - a) * (k - k0) / (k1 - k0)
        for k, it in enumerate(r['cases']):
            p, v = at(pts, ds[k])
            stations.append(dict(it=it, slug=slug, p=p, v=v, side=SIDES[slug][k], d=ds[k]))
    sid = {s['it']['id']: s for s in stations}
    caps = []
    for x in XCH:
        a, b = sid[x['a']], sid[x['b']]
        gap = seglen(a['p'], b['p'])
        if gap > G + 1.5:
            raise SystemExit('interchange %s/%s stations are %.1fpx apart (want %d)' % (x['a'], x['b'], gap, G))
        a['x'] = b['x'] = True
        caps.append((a['p'], b['p'], x))
    obst = []  # rects
    for s in stations:
        p = s['p']
        if s.get('x'):
            obst.append((p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8))
        else:
            n = DIRV[s['side']]
            segs.append((p, (p[0] + n[0] * 9, p[1] + n[1] * 9), 3.5, s['slug']))
    for a, b, x in caps:
        segs.append((a, b, 9, 'cap'))
    hub_r = 30
    hub_box = (CX - hub_r - 3, CY - hub_r - 3, CX + hub_r + 3, CY + hub_r + 3)
    obst.append(hub_box)

    placed = []

    def free(box, own=None):
        for q in placed:
            if rr(box, q, 3):
                return False
        for q in obst:
            if rr(box, q, 2):
                return False
        for a, b, pad, ow in segs:
            if rect_hits_seg(box, a, b, pad):
                return False
        return True

    def box_for(anchor, n, w, hh):
        ax, ay = anchor
        if n[0] > 0.3:
            x0 = ax
        elif n[0] < -0.3:
            x0 = ax - w
        else:
            x0 = ax - w / 2
        if n[1] > 0.3:
            y0 = ay
        elif n[1] < -0.3:
            y0 = ay - hh
        else:
            y0 = ay - hh / 2
        return (x0, y0, x0 + w, y0 + hh)

    # hub label first
    hub_lines = ['Myles Parslow']
    hw, hh = tw('Myles Parslow', 15) + 4, 34
    hub_lab = None
    for dx, dy in ((0, 46), (0, -46), (0, 60), (-60, 50), (60, 50), (-80, 44), (90, 40)):
        bx = (CX + dx - hw / 2, CY + dy - (0 if dy > 0 else hh), CX + dx + hw / 2, CY + dy + (hh if dy > 0 else 0))
        if free(bx):
            hub_lab = bx
            break
    if not hub_lab:
        raise SystemExit('no room for the hub label')
    placed.append(hub_lab)

    opp = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E', 'NE': 'SW', 'SW': 'NE', 'NW': 'SE', 'SE': 'NW'}
    fails = []
    for s in stations:
        lines = wrap(unesc(s['it']['title']), WRAPW[s['slug']])
        w = max(tw(l) for l in lines) * 1.04 + 2
        hh = LH * len(lines)
        s['lines'] = lines
        gap = 13 if s.get('x') else 13
        done = False
        for side in (s['side'], opp[s['side']]):
            n = DIRV[side]
            for shift in (0, 5, -5, 10, -10, 16, -16, 22, -22):
                ax = s['p'][0] + n[0] * gap + s['v'][0] * shift
                ay = s['p'][1] + n[1] * gap + s['v'][1] * shift
                b = box_for((ax, ay), n, w, hh)
                if free(b):
                    s['box'], s['n'], s['used'] = b, n, side
                    placed.append(b)
                    done = True
                    break
            if done:
                break
        if not done:
            fails.append(s['it']['id'])
            n = DIRV[s['side']]
            s['box'] = box_for((s['p'][0] + n[0] * gap, s['p'][1] + n[1] * gap), n, w, hh)
            s['n'], s['used'] = n, s['side']
    # final pairwise audit (independent of the greedy order)
    boxes = [(s['it']['id'], s['box']) for s in stations] + [('hub', hub_lab)]
    over = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if rr(boxes[i][1], boxes[j][1], 0):
                over.append((boxes[i][0], boxes[j][0]))
    for s in stations:
        for a, b, pad, ow in segs:
            if rect_hits_seg(s['box'], a, b, 2):
                over.append((s['it']['id'], 'line:' + ow))
    if fails or over:
        print('LABEL COLLISIONS. unplaced: %s; overlaps: %s' % (fails, over[:20]), file=sys.stderr)
        if not DEBUG:
            raise SystemExit(1)
    for s in stations:
        for i in range(len(RIVER) - 1):
            if rect_hits_seg(s['box'], RIVER[i], RIVER[i + 1], RIVER_W / 2 + 2):
                over.append((s['it']['id'], 'river'))
    for i in range(len(RIVER) - 1):
        if rect_hits_seg(hub_lab, RIVER[i], RIVER[i + 1], RIVER_W / 2 + 2):
            over.append(('hub', 'river'))
    if over and not fails:
        print('RIVER/LABEL CONFLICT: %s' % over, file=sys.stderr)
        if not DEBUG:
            raise SystemExit(1)
    # bounds
    xs, ys = [], []
    for slug in ORDER:
        for p in ROUTE[slug]:
            xs.append(p[0]); ys.append(p[1])
    for s in stations:
        xs += [s['box'][0], s['box'][2]]; ys += [s['box'][1], s['box'][3]]
    xs += [hub_lab[0], hub_lab[2]]; ys += [hub_lab[1], hub_lab[3]]
    bb = (min(xs), min(ys), max(xs), max(ys))
    return dict(stations=stations, caps=caps, hub_lab=hub_lab, hub_r=hub_r, bb=bb, segs=segs)


# ------------------------------------------------------------------ SVG
def pathd(pts):
    return 'M' + ' L'.join('%.1f %.1f' % p for p in pts)


def map_svg(L):
    st = L['stations']
    x0, y0, x1, y1 = L['bb']
    m = 34
    vx, vy, vw, vh = x0 - m, y0 - m, (x1 - x0) + 2 * m, (y1 - y0) + 2 * m
    # map grid squares (letters across, numbers down), for the station index
    cols, rows = 10, 6
    gw, gh = vw / cols, vh / rows
    for s in st:
        cx_ = min(cols - 1, int((s['p'][0] - vx) / gw))
        cy_ = min(rows - 1, int((s['p'][1] - vy) / gh))
        s['sq'] = '%s%d' % ('ABCDEFGHIJ'[cx_], cy_ + 1)
    L['vb'] = (vx, vy, vw, vh)
    out = ['<svg class="net" id="net" data-hub="%d %d" viewBox="%.1f %.1f %.1f %.1f" preserveAspectRatio="xMidYMid meet" role="group" aria-labelledby="net-t" data-vb="%.1f %.1f %.1f %.1f">'
           % (CX, CY, vx, vy, vw, vh, vx, vy, vw, vh)]
    out.append('<title id="net-t">Network map: five lines, %d stations, meeting at the Myles Parslow interchange</title>' % N_CASES)
    out.append('<rect class="bg" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (vx - 2000, vy - 2000, vw + 4000, vh + 4000))
    # grid ticks along the frame edge (outside all content)
    g = ['<g class="grid" aria-hidden="true">']
    for i in range(cols):
        gx = vx + gw * (i + .5)
        g.append('<text x="%.1f" y="%.1f">%s</text>' % (gx, vy + 14, 'ABCDEFGHIJ'[i]))
        if i:
            g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (vx + gw * i, vy, vx + gw * i, vy + 8))
    for j in range(rows):
        gy = vy + gh * (j + .5)
        g.append('<text x="%.1f" y="%.1f">%d</text>' % (vx + 9, gy + 4, j + 1))
        if j:
            g.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (vx, vy + gh * j, vx + 8, vy + gh * j))
    g.append('</g>')
    out += g
    out.append('<path class="river" aria-hidden="true" d="%s"/>' % pathd(RIVER))
    # lines
    out.append('<g class="tracks">')
    for i, slug in enumerate(ORDER):
        pts = ROUTE[slug]
        ln = plen(pts)
        lst = [s for s in st if s['slug'] == slug]
        xs = [p[0] for p in pts] + [s['box'][0] for s in lst] + [s['box'][2] for s in lst]
        ys = [p[1] for p in pts] + [s['box'][1] for s in lst] + [s['box'][3] for s in lst]
        bb = '%.0f %.0f %.0f %.0f' % (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        cas = '<path class="cas" d="%s" style="--len:%.0f;--d:%.2fs"/>' % (pathd(pts), ln, i * .19) if slug == 'design' else ''
        out.append('<g class="ln" data-line="%s" data-bb="%s">%s<path class="trk" d="%s" stroke="%s" style="--len:%.0f;--d:%.2fs"/></g>'
                   % (slug, bb, cas, pathd(pts), LINE[slug]['c'], ln, i * .19))
    out.append('</g>')
    # ticks (not interactive; the station link carries its own hit area)
    out.append('<g class="ticks" aria-hidden="true">')
    for s in st:
        if s.get('x'):
            continue
        p, n = s['p'], DIRV[s['side']]
        cls = ' class="tk"'
        if s['slug'] == 'design':
            out.append('<line class="tk tkc" data-line="design" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (p[0], p[1], p[0] + n[0] * 10.5, p[1] + n[1] * 10.5))
            cls = ' class="tk tky"'
        out.append('<line%s data-line="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s"/>'
                   % (cls, s['slug'], p[0], p[1], p[0] + n[0] * 9, p[1] + n[1] * 9, LINE[s['slug']]['c']))
    out.append('</g>')
    # interchange capsules
    out.append('<g class="caps" aria-hidden="true">')
    for a, b, x in L['caps']:
        out.append('<g class="cap" data-lines="%s %s"><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="cap-o"/><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="cap-i"/></g>'
                   % (CASE[x['a']]['room']['slug'], CASE[x['b']]['room']['slug'], a[0], a[1], b[0], b[1], a[0], a[1], b[0], b[1]))
    out.append('</g>')
    # hub
    hl = L['hub_lab']
    out.append('<g class="hub" aria-hidden="true"><circle cx="%d" cy="%d" r="%d"/><circle class="hub-i" cx="%d" cy="%d" r="%d"/>'
               '<text class="hub-t" x="%.1f" y="%.1f">Myles Parslow</text><text class="hub-s" x="%.1f" y="%.1f">You are here</text></g>'
               % (CX, CY, L['hub_r'], CX, CY, L['hub_r'] - 9, (hl[0] + hl[2]) / 2, hl[1] + 14, (hl[0] + hl[2]) / 2, hl[1] + 30))
    # stations: real links, in line order
    out.append('<g class="stations">')
    for slug in ORDER:
        r = BY[slug]
        out.append('<g class="sts" data-line="%s">' % slug)
        for s in [q for q in st if q['slug'] == slug]:
            it = s['it']
            b = s['box']
            n = s['n']
            anchor = 'start' if n[0] > 0.3 else ('end' if n[0] < -0.3 else 'middle')
            tx = b[0] + 1 if anchor == 'start' else (b[2] - 1 if anchor == 'end' else (b[0] + b[2]) / 2)
            tsp = ''.join('<tspan x="%.1f" y="%.1f">%s</tspan>' % (tx, b[1] + 12.5 + LH * k, esc(l)) for k, l in enumerate(s['lines']))
            p = s['p']
            xl = ''
            if it['id'] in XOF:
                xl = ', interchange with ' + ', '.join(unesc(CASE[o]['title']) for o, _ in XOF[it['id']])
            lab = '%s, %s line, %s%s' % (unesc(it['title']), r['short'], unesc(it['sub']), xl)
            out.append('<a class="st%s" href="%s/index.html#%s" data-line="%s" data-id="%s" data-code="%s" data-t="%s" data-s="%s" aria-label="%s">'
                       '<rect class="hit" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/><rect class="hit" x="%.1f" y="%.1f" width="12" height="12"/>'
                       '<circle class="dot" cx="%.1f" cy="%.1f" r="5"/>'
                       '<text text-anchor="%s">%s</text></a>'
                       % (' is-x' if s.get('x') else '', slug, it['id'], slug, it['id'], it['code'], qa(unesc(it['title'])), qa(unesc(it['sub'])), qa(lab),
                          b[0] - 1, b[1] - 1, b[2] - b[0] + 2, b[3] - b[1] + 2, p[0] - 6, p[1] - 6, p[0], p[1], anchor, tsp))
        out.append('</g>')
    if DEBUG:
        for s in st:
            b = s['box']
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#f0f" stroke-width=".6"/>' % (b[0], b[1], b[2]-b[0], b[3]-b[1]))
    out.append('</g></svg>')
    return '\n'.join(out)


# ------------------------------------------------------------------ body markup
def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % name, tag)
    return m.group(1) if m else None


def fix_body(b):
    """Deepen relative paths by one level and open outbound/demo links in a new tab."""
    b = re.sub(r'((?:src|href|poster)=")\.\./', r'\1../../', b)

    def a(m):
        t = m.group(0)
        hr = attr(t, 'href') or ''
        if (re.match(r'https?://', hr) or hr.startswith('../../demos/') or hr.startswith('../../assets/')) and 'target=' not in t:
            t = t.replace('<a ', '<a target="_blank" rel="noopener" ', 1)
        elif 'target="_blank"' in t and 'rel=' not in t:
            t = t.replace('<a ', '<a rel="noopener" ', 1)
        return t
    return re.sub(r'<a\b[^>]*>', a, b)


# ------------------------------------------------------------------ chrome
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800&display=swap">')
HOUSE = ('<svg class="ico" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
         '<path d="M3 11.5 12 4l9 7.5M5.5 10v10h13V10M10 20v-6h4v6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def chip(r, href, cur=False, extra=''):
    return ('<a class="chip%s" href="%s" style="--c:%s;--f:%s"%s><b aria-hidden="true">%s</b><span>%s</span></a>'
            % (' is-cur' if cur else '', href, r['c'], r['fg'], (' aria-current="page" title="Back to Home"' if cur else '') + extra, r['letter'], r['short']))


def topbar(depth, cur):
    up = '../' * depth
    chips = []
    for r in ROOMS:
        if depth == 0:
            href = '%s/index.html' % r['slug']
        elif r['slug'] == cur:
            href = '../index.html'
        else:
            href = '../%s/index.html' % r['slug']
        chips.append('<li>%s</li>' % chip(r, href, r['slug'] == cur))
    here = ''
    if depth:
        here = '<p class="yah" id="yah" aria-live="off"><span class="yah__l">You are here</span> <a id="yah-a" href="#top">%s</a></p>' % esc(BY[cur]['short'] + ' line')
    return ('<header class="bar" id="bar"><nav class="bar__in" aria-label="Lines">'
            '<a class="home%s" href="%sindex.html"%s>%s<span>Home</span></a>'
            '<ul class="chips">%s</ul>%s</nav></header>') % (
        ' is-cur' if cur == 'home' else '', up, ' aria-current="page"' if cur == 'home' else '', HOUSE, ''.join(chips), here)


def page(title, desc, depth, cls, inner, head_extra=''):
    up = '../' * depth
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light">\n<meta name="theme-color" content="#fbfaf7">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="icon" href="%s../favicon.svg" type="image/svg+xml">\n%s\n'
            '<script>document.documentElement.className+=" js"</script>\n%s'
            '<link rel="stylesheet" href="%si.css">\n</head>\n<body class="%s">\n'
            '<a class="skip" href="#main">%s</a>\n%s\n'
            '<script src="%si.js"></script>\n</body>\n</html>\n') % (
        esc(title), qa(desc), up, FONTS, head_extra, up, cls, 'Skip to the rooms' if depth == 0 else 'Skip to the projects', inner, up)


# ------------------------------------------------------------------ footer
def footer_html(depth):
    foot = HOME['foot_html']
    mail = re.search(r'href="mailto:([^"]+)"', foot).group(1)
    gh = re.search(r'<a href="(https://github.com/[^"]*)">GitHub</a>', foot).group(1)
    lp = re.search(r'<a href="([^"]*)">Legal portfolio</a>', foot).group(1)
    sign = re.search(r'<span>([^<]*)</span>\s*</div>', foot).group(1)
    extra = '' if depth == 0 else ' <a href="../index.html#tools">Which AI for what by project &rarr;</a>'
    return ('<footer class="foot" id="contact" aria-labelledby="h-foot"><h2 id="h-foot" class="foot__t">Say hello.</h2>'
            '<p class="foot__mail"><a href="mailto:%s">%s</a> <button type="button" class="tbtn" id="copy" data-copy="%s">Copy address</button> <span id="copystat" class="foot__st" aria-live="polite"></span></p>'
            '<p class="foot__row"><a href="%s" target="_blank" rel="noopener">GitHub</a> <a href="%s" target="_blank" rel="noopener">Legal portfolio</a> <a href="#top">Back to top &uarr;</a>%s</p>'
            '<p class="foot__sign">%s</p></footer>') % (mail, mail, mail, gh, lp, extra, sign)


# ------------------------------------------------------------------ home
def badge(r, txt=None):
    return '<span class="lbadge" style="--c:%s;--f:%s"><b>%s</b>%s</span>' % (r['c'], r['fg'], r['letter'], esc(txt if txt is not None else r['short']))


def home():
    L = layout()
    hhtml = HOME['hero_html']
    count = re.search(r'hero__count">(.*?)</span>', hhtml).group(1).replace('52', str(N_CASES))
    lede = re.search(r'<p class="lede"><span class="hero__count">.*?</span>(.*?)</p>', hhtml, re.S).group(1)
    stats = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', hhtml, re.S)
    st_rows = ''.join('<tr><th scope="row">%s</th><td><span class="num">%s</span></td></tr>' % (dt, dd) for dt, dd in stats)

    title = ('<section class="sheet" id="top" aria-labelledby="h-name">'
             '<div class="sheet__name"><p class="sheet__kicker">Network map &middot; November 2026</p>'
             '<h1 id="h-name"><span class="fit nm" data-cap="168">Myles Parslow</span> <span class="ttl">makes things with AI</span></h1></div>'
             '<aside class="svc" aria-labelledby="h-svc"><h2 id="h-svc" class="svc__h"><span class="svc__i" aria-hidden="true">i</span>Service information</h2>'
             '<p class="svc__count">%s</p><p class="svc__lede">%s</p>'
             '<table class="svc__t"><tbody>%s</tbody></table></aside></section>') % (count, lede, st_rows)

    # legend
    lb = []
    for r in ROOMS:
        lb.append('<li><button class="lb" type="button" data-line="%s" aria-pressed="false" style="--c:%s;--f:%s">'
                  '<b aria-hidden="true">%s</b><span class="lb__n">%s line</span><span class="lb__c">%d stations</span></button></li>'
                  % (r['slug'], r['c'], r['fg'], r['letter'], esc(r['short']), r['n']))
    xk = []
    for x in XCH:
        a, b = CASE[x['a']], CASE[x['b']]
        xk.append('<li><span class="xk__sym" aria-hidden="true"><i style="--c:%s"></i><i style="--c:%s"></i></span>'
                  '<span class="xk__t"><b>Interchange: %s.</b> <a href="%s/index.html#%s">%s</a> (%s) &harr; <a href="%s/index.html#%s">%s</a> (%s). %s</span></li>'
                  % (a['room']['c'], b['room']['c'], esc(x['key']), a['room']['slug'], a['id'], a['title'], esc(a['room']['short']),
                     b['room']['slug'], b['id'], b['title'], esc(b['room']['short']), esc(x['why'])))
    legend = ('<div class="legend"><div class="legend__lines"><h3 class="legend__h">Lines</h3><ul class="lbs">%s</ul>'
              '<p class="legend__tip">Choose a line to isolate it. Choose it again, press Esc or click the empty map to show the whole network.</p></div>'
              '<div class="legend__x"><h3 class="legend__h">Interchanges</h3><ul class="xk">%s</ul>'
              '<p class="xk__hub"><span class="hubsym" aria-hidden="true"></span><span><b>You are here:</b> the Myles Parslow interchange, where all five lines meet.</span></p></div></div>'
              ) % (''.join(lb), ''.join(xk))

    # list view (vertical line diagrams)
    lv = []
    for r in ROOMS:
        items = []
        for it in r['cases']:
            ch = ''
            if it['id'] in XOF:
                ch = ''.join('<span class="lv__x">Change for <a href="%s/index.html#%s">%s</a> &middot; %s line</span>'
                             % (CASE[o]['room']['slug'], o, CASE[o]['title'], esc(CASE[o]['room']['short'])) for o, _ in XOF[it['id']])
            items.append('<li class="%s"><a href="%s/index.html#%s"><span class="lv__c">%s</span> %s</a><span class="lv__s">%s</span>%s</li>'
                         % ('is-x' if ch else '', r['slug'], it['id'], it['code'], it['title'], it['sub'], ch))
        lv.append('<section class="lv" style="--c:%s;--f:%s" aria-labelledby="lv-%s"><h3 id="lv-%s"><a href="%s/index.html">%s</a> <span class="lv__n">%d stations</span></h3><ol>%s</ol></section>'
                  % (r['c'], r['fg'], r['slug'], r['slug'], r['slug'], badge(r, r['short'] + ' line'), r['n'], ''.join(items)))

    net = ('<section class="netsec" id="map" aria-labelledby="h-map">'
           '<div class="netsec__h"><h2 id="h-map" class="sec-h">The network</h2>'
           '<div class="ctl" role="group" aria-label="Map view">'
           '<button type="button" class="tbtn" id="view" aria-pressed="false">List view</button>'
           '<span class="zoom"><button type="button" class="tbtn sq" id="zin" aria-label="Zoom in">+</button>'
           '<button type="button" class="tbtn sq" id="zout" aria-label="Zoom out">&minus;</button>'
           '<button type="button" class="tbtn" id="zfit">Whole map</button></span></div></div>'
           '<div class="board" id="board" aria-live="polite"><span class="board__d">Hover or tab to a station. Choose a line in the key to ride it.</span></div>'
           '<div class="frame" id="frame" style="--ar:%.0f/%.0f">%s</div>'
           '<div class="lview" id="lview" hidden>%s</div>'
           '%s</section>') % ((lambda svg: (L['vb'][2], L['vb'][3], svg))(map_svg(L)) + (''.join(lv), legend))

    # station index (alphabetical, like a real map's gazetteer)
    sq = {s['it']['id']: s['sq'] for s in L['stations']}
    rows = []
    for it in sorted(CASE.values(), key=lambda c: plain(c['title']).lower()):
        r = it['room']
        rows.append('<li><a href="%s/index.html#%s">%s</a><span class="ix__s">%s</span>'
                    '<span class="ix__m"><span class="ldot" style="--c:%s;--f:%s" title="%s line"><span aria-hidden="true">%s</span><span class="vh">%s line</span></span>'
                    '<span class="ix__z">Zone %d</span><span class="ix__sq"><span class="vh">Map square </span>%s</span></span></li>'
                    % (r['slug'], it['id'], it['title'], it['sub'], r['c'], r['fg'], esc(r['short']), r['letter'], esc(r['short']), it['zone'], sq[it['id']]))
    index = ('<section class="ix" id="index" aria-labelledby="h-ix"><h2 id="h-ix" class="sec-h">Station index</h2>'
             '<p class="sec-l">All %d stations, A to Z: station &middot; line &middot; zone &middot; map square. Each one opens on its line.</p>'
             '<ol class="ixl">%s</ol></section>' % (N_CASES, ''.join(rows)))

    # rules of travel
    rh = HOME['rules_html']
    r_eb = re.search(r'<p class="eyebrow">(.*?)</p>', rh).group(1)
    r_t = re.search(r'id="h-rules"[^>]*>(.*?)</h2>', rh, re.S).group(1)
    rules = re.findall(r'<span class="rule__n">(.*?)</span><h3[^>]*>(.*?)</h3><p[^>]*>(.*?)</p>', rh, re.S)
    rules_html = ('<section class="rules" id="rules" aria-labelledby="h-rules"><h2 id="h-rules" class="sec-h">Rules of travel</h2>'
                  '<p class="sec-k">%s &middot; %s</p><ol class="rl">%s</ol></section>') % (
        r_eb, r_t, ''.join('<li><span class="rl__n" aria-hidden="true">%s</span><div><h3>%s</h3><p>%s</p></div></li>' % (n, t, p) for n, t, p in rules))

    # timetable
    th = HOME['tools_html']
    t_eb = re.search(r'<p class="eyebrow">(.*?)</p>', th).group(1)
    t_t = re.search(r'id="h-tools"[^>]*>(.*?)</h2>', th, re.S).group(1)
    t_l = re.search(r'<p class="sec-lede">(.*?)</p>', th, re.S).group(1)
    t_sum = re.search(r'<summary><span class="sct">(.*?)</span></summary>', th).group(1)
    trs = re.findall(r'<article class="trow">(.*?)</article>', th, re.S)

    def trow(row):
        name = re.search(r'<h3>(.*?)</h3>', row, re.S).group(1)
        cells = re.findall(r'<span class="lab">(.*?)</span>\s*<p>(.*?)</p>', row, re.S)
        assert 1 <= len(cells) <= 2, name
        std = ('Built with', 'Runs on')

        def cell(k):
            if k >= len(cells):
                return '<span class="tt__none">&mdash;</span>'
            lab, p = cells[k]
            return '<span class="tt__l%s">%s</span>%s' % ('' if lab == std[k] else ' tt__lx', lab, p)
        return '<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (name, cell(0), cell(1))
    head = '<thead><tr><th scope="col">Service</th><th scope="col">Built with</th><th scope="col">Runs on</th></tr></thead>'
    first = sum(1 for _ in re.finditer(r'<article class="trow">', th.split('<details')[0]))
    tools_html = ('<section class="tt" id="tools" aria-labelledby="h-tools"><h2 id="h-tools" class="sec-h">Timetable</h2>'
                  '<p class="sec-k">%s &middot; %s</p><p class="sec-l">%s</p>'
                  '<div class="tt__w"><table class="ttt">%s<tbody>%s</tbody></table></div>'
                  '<details class="tt__more"><summary>%s</summary><div class="tt__w"><table class="ttt">%s<tbody>%s</tbody></table></div></details></section>'
                  ) % (t_eb, t_t, t_l, head, ''.join(trow(x) for x in trs[:first]), t_sum, head, ''.join(trow(x) for x in trs[first:]))

    notice = ('<section class="notice" id="archive" aria-labelledby="h-notice"><h2 id="h-notice" class="notice__h"><span class="notice__i" aria-hidden="true">!</span>Service notice</h2>'
              '<p><b>Style archive.</b> You&rsquo;re looking at: Transit Map. This site is also a running design experiment. Each version renders the same %d case studies in a completely different style, from a museum floor plan to a 1991 law-firm word processor. '
              '<a class="notice__a" href="../styles/index.html"><b>See every version &rarr;</b></a></p></section>') % N_CASES

    footer = footer_html(0)

    inner = topbar(0, 'home') + '\n<main id="main">\n' + '\n'.join([title, net, index, rules_html, tools_html, notice]) + '\n</main>\n' + footer
    redirect = '<script>(function(){var M=%s,h=location.hash.slice(1);if(h&&Object.prototype.hasOwnProperty.call(M,h))location.replace(M[h]+"/index.html#"+h)})()</script>\n' % HOME['redirect_map']
    desc = 'Myles Parslow makes things with AI: %d case studies on five lines, drawn as a transit map.' % N_CASES
    return page('Myles Parslow', desc, 0, 'pg-home', inner, redirect), L


# ------------------------------------------------------------------ rooms
def strip(r):
    lis = []
    for it in r['cases']:
        x = it['id'] in XOF
        xo = ''
        if x:
            xo = ''.join('<i class="sx" style="--c:%s" title="Change for %s"></i>' % (CASE[o]['room']['c'], qa(CASE[o]['room']['short'])) for o, _ in XOF[it['id']])
        mw = max(76, int(max(tw(wd, 12.5) for wd in plain(it['title']).split()) * 1.06) + 14)
        lis.append('<li class="%s" data-id="%s"%s><a href="#%s"><span class="sn">%s</span><span class="sm" aria-hidden="true">%s</span><span class="sy">You are here</span></a></li>'
                   % ('is-x' if x else '', it['id'], (' style="min-width:%dpx"' % mw) if mw > 76 else '', it['id'], it['title'], xo))
    return ('<nav class="strip" id="strip" aria-label="%s line stations" style="--c:%s;--f:%s"><div class="strip__sc" id="strip-sc"><ol class="strip__ol">%s</ol></div></nav>'
            % (esc(r['short']), r['c'], r['fg'], ''.join(lis)))


def stop(r, it):
    kick = ''.join('<span class="kk">%s</span>' % k for k in it['kickers'] if k)
    chg = ''
    for o, x in XOF.get(it['id'], []):
        oc = CASE[o]
        chg += ('<p class="chg"><span class="chg__sym" aria-hidden="true"><i style="--c:%s"></i><i style="--c:%s"></i></span>'
                '<span>Change here for <a href="../%s/index.html#%s">%s</a> on the %s line. %s</span></p>'
                % (r['c'], oc['room']['c'], oc['room']['slug'], o, oc['title'], esc(oc['room']['short']), esc(x['why'])))
    return ('<article class="stop" id="%s" aria-labelledby="t-%s">'
            '<header class="stop__h"><span class="stop__mk%s" aria-hidden="true"></span>'
            '<p class="stop__code"><span class="code">%s</span> <span class="cnt">%s</span>%s</p>'
            '<h2 class="stop__t" id="t-%s">%s</h2><p class="stop__sub">%s</p>'
            '%s<p class="stop__lede">%s</p></header>'
            '<div class="cbody">%s</div></article>') % (
        it['id'], it['id'], ' is-x' if it['id'] in XOF else '', it['code'], it['count'], kick, it['id'], it['title'], it['sub'], chg, it['lede'], fix_body(it['body_html']))


def room(r):
    i = r['i']
    parts = []
    for it in r['items']:
        k = it['kind']
        if k == 'group':
            g = fix_body(it['html']).replace('<h2 class="gdiv__t">', '<p class="zn"><span>Zone %d</span></p><h2 class="gdiv__t">' % it['zone'], 1)
            parts.append('<div class="zone">%s</div>' % g)
        elif k == 'extra':
            parts.append('<div class="extra">%s</div>' % fix_body(it['html']))
        else:
            parts.append(stop(r, it))
    nxt = ROOMS[i + 1] if i + 1 < len(ROOMS) else None
    if nxt:
        change = ('<a class="change" href="../%s/index.html" style="--c:%s;--f:%s"><span class="change__k">Change here for</span>'
                  '<span class="change__t">%s line &rarr;</span></a>') % (nxt['slug'], nxt['c'], nxt['fg'], esc(nxt['short']))
    else:
        change = ('<a class="change home-change" href="../index.html"><span class="change__k">End of the line. Change here for</span>'
                  '<span class="change__t">The network map (Home) &rarr;</span></a>')
    head = ('<header class="rhead" id="top" style="--c:%s;--f:%s"><div class="rhead__band" aria-hidden="true"></div>'
            '<div class="rhead__in"><p class="rhead__meta">%s <span>Line %d of 5 &middot; %d stations</span> <span class="rhead__old">%s &middot; %s</span></p>'
            '<h1 class="rhead__t"><a class="fit" data-cap="210" href="../index.html" title="Back to the network map">%s</a></h1>'
            '<p class="rhead__lede">%s</p></div></header>') % (
        r['c'], r['fg'], badge(r, r['short'] + ' line'), i + 1, r['n'], r['eyebrow'], r['count'], r['title'], r['lede'])
    inner = (topbar(1, r['slug']) + '\n' + head + '\n' + strip(r) + '\n<main id="main" class="line" style="--c:%s;--f:%s">\n%s\n%s\n</main>'
             % (r['c'], r['fg'], '\n'.join(parts), change)) + '\n' + footer_html(1)
    desc = plain(r['lede'])
    return page('%s line — Myles Parslow' % r['plain'], desc, 1, 'room room-%s' % r['slug'], inner)


# ------------------------------------------------------------------ static
CSS = r'''/* Mockup I, "Transit Map". Generated by themed/render_i.py. Light only: a transit map is white. */
:root{--paper:#fbfaf7;--white:#ffffff;--ink:#16161a;--mute:#56565e;--rule:#d8d4cb;--soft:#efece4;--water:#cfe3f2;
  --ff:"Overpass",system-ui,-apple-system,"Segoe UI",sans-serif;--barh:58px;--striph:84px;--gut:clamp(16px,4vw,56px);--max:1600px;color-scheme:light}
*,*::before,*::after{box-sizing:border-box}
[hidden]{display:none!important}
html{background:var(--paper);color:var(--ink);scroll-padding-top:calc(var(--barh) + 16px);-webkit-text-size-adjust:100%}
.room{scroll-padding-top:calc(var(--barh) + var(--striph) + 12px)}
html:has(body.room){scroll-padding-top:calc(var(--barh) + var(--striph) + 12px)}
body{margin:0;background:var(--paper);color:var(--ink);font:400 17px/1.55 var(--ff);overflow-x:clip}
img,video{max-width:100%}
a{color:inherit}
h1,h2,h3,h4,p,ol,ul,dl,figure,table{margin:0}
:focus-visible{outline:3px solid var(--ink);outline-offset:3px;border-radius:2px}
.skip{position:absolute;left:-9999px;top:8px;z-index:100;background:var(--ink);color:var(--white);padding:10px 16px;font-weight:800;text-decoration:none}
.skip:focus{left:12px}

/* ---------- top bar ---------- */
.bar{position:sticky;top:0;z-index:60;background:var(--paper);border-bottom:2px solid var(--ink)}
.bar__in{display:flex;align-items:center;gap:14px;min-height:var(--barh);padding:8px var(--gut);max-width:var(--max);margin:0 auto}
.home{display:inline-flex;align-items:center;gap:8px;flex:none;padding:7px 15px 6px 12px;border:2px solid var(--ink);border-radius:999px;font-weight:800;font-size:15px;line-height:1;text-decoration:none;background:var(--white);color:var(--ink)}
.home .ico{flex:none;margin-top:-2px}
.home:hover{background:var(--ink);color:var(--white)}
.home.is-cur{background:var(--ink);color:var(--white)}
.chips{list-style:none;padding:0;display:flex;gap:6px;flex-wrap:nowrap;min-width:0}
.chip{display:inline-flex;align-items:center;gap:7px;padding:4px 12px 4px 4px;border:2px solid var(--c);border-radius:999px;background:var(--white);color:var(--ink);font-weight:600;font-size:15px;line-height:1;text-decoration:none;white-space:nowrap}
.chip b{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--c);color:var(--f);font-weight:800;font-size:13px;line-height:1;padding-top:2px}
.chip span{padding-top:2px}
.chip:hover{background:var(--c);color:var(--f)}
.chip:hover b{background:var(--white);color:var(--ink)}
.chip.is-cur{background:var(--c);color:var(--f)}
.chip.is-cur b{background:var(--white);color:var(--ink)}
.chip[style*="#ffd300"]{border-color:var(--ink)}
.chip[style*="#ffd300"] b{box-shadow:0 0 0 1.5px var(--ink)}
.yah{margin-left:auto;min-width:0;font-size:14px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.yah__l{color:var(--mute);font-weight:600}
.yah a{font-weight:800;text-decoration:none;border-bottom:3px solid var(--c, var(--ink))}

/* ---------- shared section heads ---------- */
.sec-h{font-weight:800;font-size:clamp(28px,3vw,44px);line-height:1.05}
.sec-k{margin-top:6px;color:var(--mute);font-weight:600}
.sec-l{margin-top:8px;max-width:46em;font-size:18px}
.tbtn{font:600 15px/1 var(--ff);color:var(--ink);background:var(--white);border:2px solid var(--ink);border-radius:999px;padding:9px 14px 7px;cursor:pointer}
.tbtn:hover{background:var(--ink);color:var(--white)}
.tbtn.sq{width:38px;padding:7px 0 5px;font-size:19px;font-weight:800;text-align:center}
.tbtn[aria-pressed="true"]{background:var(--ink);color:var(--white)}
.lbadge{display:inline-flex;align-items:center;gap:7px;padding:3px 11px 2px 3px;border-radius:999px;background:var(--c);color:var(--f);font-weight:800;font-size:14px;line-height:1.1;white-space:nowrap}
.lbadge b{display:grid;place-items:center;width:21px;height:21px;border-radius:50%;background:var(--white);color:var(--ink);font-size:12px;padding-top:2px}
.lbadge[style*="#ffd300"]{box-shadow:inset 0 0 0 1.5px var(--ink)}
.lbadge[style*="#ffd300"] b{box-shadow:0 0 0 1.5px var(--ink)}

/* ---------- home: the map sheet title block ---------- */
.sheet{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(0,1fr);gap:clamp(20px,3vw,44px);align-items:stretch;max-width:var(--max);margin:0 auto;padding:clamp(24px,4vw,52px) var(--gut) clamp(24px,3vw,40px);scroll-margin-top:var(--barh)}
.sheet__name{border:3px solid var(--ink);background:var(--white);padding:clamp(18px,2.4vw,32px);display:flex;flex-direction:column;justify-content:flex-end;min-width:0}
.sheet__kicker{font-weight:600;font-size:15px;color:var(--mute);margin-bottom:auto;padding-bottom:18px}
.sheet h1{display:block;min-width:0}
.sheet .nm{display:block;width:max-content;max-width:none;font-weight:800;line-height:.95;letter-spacing:-.01em;white-space:nowrap;font-size:96px}
.sheet .ttl{display:block;margin-top:10px;font-weight:600;font-size:clamp(22px,2.4vw,36px);line-height:1.1}
.svc{border:3px solid var(--ink);background:var(--white);display:flex;flex-direction:column;min-width:0}
.svc__h{display:flex;align-items:center;gap:10px;background:var(--ink);color:var(--white);font-weight:800;font-size:18px;padding:10px 14px 8px}
.svc__i{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--white);color:var(--ink);font-size:15px;font-weight:800;padding-top:2px}
.svc__count{padding:14px 16px 0;font-weight:800;font-size:15px}
.svc__lede{padding:6px 16px 14px;font-size:16px;line-height:1.5}
.svc__t{width:100%;border-collapse:collapse;margin-top:auto;border-top:2px solid var(--ink)}
.svc__t th{text-align:left;font-weight:400;font-size:14px;line-height:1.35;padding:10px 12px 8px 16px;border-bottom:1px solid var(--rule);vertical-align:middle}
.svc__t td{text-align:right;padding:10px 16px 8px 8px;border-bottom:1px solid var(--rule);white-space:nowrap;vertical-align:middle}
.svc__t tr:last-child>*{border-bottom:0}
.num{display:inline-block;font-weight:800;font-size:clamp(20px,2vw,30px);line-height:1;font-variant-numeric:tabular-nums;white-space:nowrap}

/* ---------- home: the network map ---------- */
.netsec{max-width:var(--max);margin:0 auto;padding:clamp(12px,2vw,24px) var(--gut) clamp(40px,5vw,64px);scroll-margin-top:var(--barh)}
.netsec__h{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px 20px;margin-bottom:14px}
.ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.zoom{display:inline-flex;gap:6px}
.board{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;min-height:54px;padding:9px 14px 7px;background:var(--ink);color:var(--white);border:3px solid var(--ink);border-bottom:0;font-weight:600;font-size:16px;line-height:1.3}
.board__d{color:#d6d3cc}
.board__c{font-weight:800;font-variant-numeric:tabular-nums}
.board__t{font-weight:800;font-size:18px}
.board__s{color:#d6d3cc}
.board a{color:var(--white);font-weight:800}
.board .ride{margin-left:auto;display:inline-flex;align-items:center;gap:8px;padding:7px 14px 5px;border-radius:999px;background:var(--c);color:var(--f);text-decoration:none;box-shadow:0 0 0 2px var(--white)}
.board .tbtn{border-color:var(--white);background:var(--ink);color:var(--white);padding:7px 12px 5px}
.board .tbtn:hover{background:var(--white);color:var(--ink)}
.frame{position:relative;border:3px solid var(--ink);background:var(--paper);aspect-ratio:var(--ar);max-height:calc(100vh - var(--barh) - 40px);overflow:hidden;touch-action:none;width:100%}
.frame.is-drag{cursor:grabbing}
.net{display:block;width:100%;height:100%;user-select:none;-webkit-user-select:none;cursor:grab}
.net .bg{fill:var(--paper)}
.net .river{fill:none;stroke:var(--water);stroke-width:15;stroke-linejoin:round;stroke-linecap:butt}
.net .grid text{font:600 11px var(--ff);fill:#8b877e;text-anchor:middle}
.net .grid line{stroke:#bdb8ad;stroke-width:1}
.net .trk{fill:none;stroke-width:8;stroke-linejoin:round;stroke-linecap:round}
.net .cas{fill:none;stroke:var(--ink);stroke-width:11.5;stroke-linejoin:round;stroke-linecap:round}
.net .tk{stroke-width:5;stroke-linecap:butt}
.net .tkc{stroke:var(--ink);stroke-width:8}
.net .tky{stroke-width:4.5}
.net .cap-o{stroke:var(--ink);stroke-width:19;stroke-linecap:round}
.net .cap-i{stroke:var(--white);stroke-width:12;stroke-linecap:round}
.net .hub circle{fill:var(--white);stroke:var(--ink);stroke-width:5}
.net .hub .hub-i{fill:var(--ink);stroke:none}
.net .hub-t{font:800 15px var(--ff);text-anchor:middle;fill:var(--ink)}
.net .hub-s{font:600 12px var(--ff);text-anchor:middle;fill:var(--mute)}
.net .st{cursor:pointer;outline:none}
.net .st text{font:600 14px var(--ff);fill:var(--ink)}
.net .st .hit{fill:transparent;stroke:none}
.net .st .dot{fill:none;stroke:none}
.net .st.on .dot,.net .st:hover .dot,.net .st:focus-visible .dot{fill:var(--white);stroke:var(--ink);stroke-width:3}
.net .st.on text,.net .st:hover text,.net .st:focus-visible text{font-weight:800;text-decoration:underline;text-decoration-thickness:1.5px}
.net .st:focus-visible .hit{stroke:var(--ink);stroke-width:2;stroke-dasharray:4 3}
.net .ln,.net .tk,.net .sts,.net .cap,.net .st{transition:opacity .2s}
.net .dim{opacity:.15}
.net .sts .st.dim{opacity:.25}
@media (prefers-reduced-motion:no-preference){
  .js .net.anim .trk,.js .net.anim .cas{stroke-dasharray:var(--len) var(--len);stroke-dashoffset:var(--len);animation:draw .42s cubic-bezier(.45,0,.2,1) var(--d) forwards}
}
@keyframes draw{to{stroke-dashoffset:0}}
.lview{border:3px solid var(--ink);background:var(--white);padding:18px clamp(14px,2vw,24px);display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:24px 28px}
.lview[hidden]{display:none}
.lv h3{font-size:16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.lv h3 a{text-decoration:none}
.lv__n{font-weight:600;color:var(--mute);font-size:14px}
.lv ol{list-style:none;padding:6px 0 0 0;margin:8px 0 0 9px;border-left:8px solid var(--c)}
.lv[style*="#ffd300"] ol{box-shadow:-1.5px 0 0 var(--ink),inset 1.5px 0 0 var(--ink);border-left-color:var(--c)}
.lv li{position:relative;padding:5px 0 7px 18px}
.lv li::before{content:"";position:absolute;left:0;top:12px;width:10px;height:5px;background:var(--c)}
.lv li.is-x::before{left:-12px;top:6px;width:16px;height:16px;border-radius:50%;background:var(--white);border:3px solid var(--ink)}
.lv a{font-weight:800;text-decoration:none}
.lv a:hover{text-decoration:underline}
.lv__c{font-weight:600;color:var(--mute);font-size:13px;margin-right:2px;font-variant-numeric:tabular-nums}
.lv__s{display:block;font-size:14px;color:var(--mute)}
.lv__x{display:block;font-size:14px}
.lv__x a{font-weight:600;text-decoration:underline}
.legend{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:clamp(20px,3vw,48px);margin-top:22px}
.legend__h{font-weight:800;font-size:18px;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
.lbs{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(225px,1fr));gap:8px}
.lb{display:flex;align-items:center;gap:10px;width:100%;text-align:left;font:600 15px/1.2 var(--ff);color:var(--ink);background:var(--white);border:2px solid var(--c);border-radius:999px;padding:4px 14px 4px 4px;cursor:pointer}
.lb b{display:grid;place-items:center;flex:none;width:32px;height:32px;border-radius:50%;background:var(--c);color:var(--f);font-weight:800;font-size:15px;padding-top:2px}
.lb__n{font-weight:800}
.lb__c{margin-left:auto;color:var(--mute);font-size:14px;white-space:nowrap}
.lb:hover,.lb[aria-pressed="true"]{background:var(--c);color:var(--f)}
.lb:hover .lb__c,.lb[aria-pressed="true"] .lb__c{color:inherit}
.lb:hover b,.lb[aria-pressed="true"] b{background:var(--white);color:var(--ink)}
.lb[style*="#ffd300"]{border-color:var(--ink)}
.lb[style*="#ffd300"] b{box-shadow:0 0 0 1.5px var(--ink)}
.legend__tip{margin-top:10px;font-size:14px;color:var(--mute)}
.xk{list-style:none;padding:0;display:grid;gap:10px}
.xk li{display:flex;gap:12px;align-items:flex-start;font-size:15px;line-height:1.45}
.xk__sym,.chg__sym{position:relative;flex:none;display:inline-flex;flex-direction:column;gap:6px;width:38px;padding:5px 0;margin-top:1px}
.xk__sym i,.chg__sym i{display:block;height:8px;background:var(--c);border-radius:2px}
.xk__sym::after,.chg__sym::after{content:"";position:absolute;left:50%;top:50%;width:16px;height:30px;margin:-15px 0 0 -8px;border-radius:9px;background:var(--white);border:3px solid var(--ink)}
.xk a{font-weight:800}
.xk__hub{display:flex;gap:12px;align-items:center;margin-top:14px;font-size:15px}
.hubsym{flex:none;width:30px;height:30px;border-radius:50%;background:var(--white);border:5px solid var(--ink);position:relative}
.hubsym::after{content:"";position:absolute;inset:6px;border-radius:50%;background:var(--ink)}

/* ---------- home: station index ---------- */
.ix,.rules,.tt,.notice{max-width:var(--max);margin:0 auto;padding:clamp(36px,5vw,64px) var(--gut) 0;scroll-margin-top:var(--barh)}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap}
.ixl{list-style:none;padding:0;margin-top:20px;columns:3 300px;column-gap:36px;border-top:3px solid var(--ink);padding-top:6px}
.ixl li{break-inside:avoid;display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:10px;padding:7px 0 6px;border-bottom:1px solid var(--rule)}
.ixl a{grid-column:1;font-weight:800;font-size:15.5px;line-height:1.25;text-decoration:none}
.ixl a:hover{text-decoration:underline}
.ix__s{grid-column:1;font-size:13.5px;line-height:1.3;color:var(--mute)}
.ix__m{grid-column:2;grid-row:1/span 2;display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;white-space:nowrap}
.ldot{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--c);color:var(--f);font-weight:800;font-size:12px;padding-top:2px}
.ldot[style*="#ffd300"]{box-shadow:inset 0 0 0 1.5px var(--ink)}
.ix__z{color:var(--mute)}
.ix__sq{font-weight:800;min-width:2.2em;text-align:right;font-variant-numeric:tabular-nums}

/* ---------- rules of travel ---------- */
.rl{list-style:none;padding:0;margin-top:22px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.rl li{display:flex;gap:14px;align-items:flex-start;background:var(--white);border:3px solid var(--ink);padding:16px 18px}
.rl__n{flex:none;display:grid;place-items:center;width:40px;height:40px;border-radius:50%;background:var(--ink);color:var(--white);font-weight:800;font-size:16px;padding-top:2px}
.rl h3{font-weight:800;font-size:20px;line-height:1.2;margin-bottom:6px}
.rl p{font-size:16px}

/* ---------- timetable ---------- */
.tt__w{margin-top:20px;overflow-x:auto}
.ttt{width:100%;border-collapse:collapse;font-size:15px;line-height:1.45;border:3px solid var(--ink);background:var(--white)}
.ttt thead th{background:var(--ink);color:var(--white);text-align:left;font-weight:800;padding:10px 12px 8px}
.ttt tbody th{text-align:left;font-weight:800;width:18%;min-width:9em}
.ttt tbody th,.ttt td{vertical-align:top;padding:10px 12px 8px;border-bottom:1px solid var(--rule)}
.ttt td{width:41%}
.ttt tbody tr:nth-child(even)>*{background:var(--soft)}
.tt__l{display:none}
.tt__l.tt__lx{display:block;font-size:12.5px;font-weight:800;color:var(--mute)}
.tt__none{color:var(--mute)}
.tt__more{margin-top:14px}
.tt__more summary{display:inline-block;cursor:pointer;font-weight:800;border:2px solid var(--ink);border-radius:999px;padding:8px 16px 6px;background:var(--white)}
.tt__more summary:hover{background:var(--ink);color:var(--white)}
.tt__more[open] summary{margin-bottom:0}

/* ---------- service notice ---------- */
.notice{padding-bottom:clamp(40px,6vw,72px)}
.notice>*{max-width:960px}
.notice__h{display:flex;align-items:center;gap:12px;font-weight:800;font-size:20px;background:#ffd300;color:var(--ink);border:3px solid var(--ink);border-bottom:0;padding:10px 16px 8px}
.notice__i{display:grid;place-items:center;width:26px;height:26px;border-radius:50%;background:var(--ink);color:#ffd300;font-weight:800;padding-top:2px}
.notice p{border:3px solid var(--ink);background:var(--white);padding:16px 18px;font-size:17px}
.notice__a{white-space:nowrap}

/* ---------- footer ---------- */
.foot{background:var(--ink);color:var(--white);padding:clamp(36px,5vw,64px) var(--gut) 40px}
.foot>*{max-width:var(--max);margin-left:auto;margin-right:auto}
.foot__t{font-weight:800;font-size:clamp(34px,4vw,60px);line-height:1}
.foot__mail{margin-top:16px;display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center}
.foot__mail a{font-weight:800;font-size:clamp(20px,2.4vw,32px);color:var(--white);text-underline-offset:4px;user-select:text;-webkit-user-select:text;overflow-wrap:anywhere}
.foot .tbtn{background:var(--ink);color:var(--white);border-color:var(--white)}
.foot .tbtn:hover{background:var(--white);color:var(--ink)}
.foot__st{font-size:14px;color:#d6d3cc}
.foot__row{margin-top:22px;display:flex;flex-wrap:wrap;gap:10px 22px;font-weight:600}
.foot__row a{color:var(--white)}
.foot__sign{margin-top:18px;color:#bdb9b0;font-size:14px}
.foot :focus-visible{outline-color:var(--white)}

/* ---------- room header ---------- */
.rhead{background:var(--paper)}
.rhead__band{height:30px;background:var(--c)}
.room-design .rhead__band{border-bottom:2px solid var(--ink)}
.rhead__in{max-width:var(--max);margin:0 auto;padding:clamp(22px,3.5vw,44px) var(--gut) clamp(16px,2vw,26px)}
.rhead__meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px;font-weight:600;font-size:16px}
.rhead__old{color:var(--mute);font-weight:400;font-size:14px}
.rhead__t{margin:clamp(10px,1.6vw,20px) 0 clamp(10px,1.4vw,18px);line-height:.9;min-width:0}
.rhead__t .fit{display:inline-block;width:max-content;font-weight:800;letter-spacing:-.015em;white-space:nowrap;text-decoration:none;color:var(--ink);font-size:120px}
.rhead__t .fit:hover{text-decoration:underline;text-decoration-thickness:4px;text-underline-offset:8px}
.rhead__lede{max-width:44em;font-size:clamp(18px,1.4vw,21px);line-height:1.5}

/* ---------- strip map (sticky) ---------- */
.strip{position:sticky;top:var(--barh);z-index:50;background:var(--paper);border-top:1px solid var(--rule);border-bottom:2px solid var(--ink)}
.strip__sc{overflow-x:auto;overflow-y:hidden;overscroll-behavior-x:contain;scrollbar-width:thin;max-width:var(--max);margin:0 auto}
.strip__ol{list-style:none;display:flex;padding:6px 16px 4px;margin:0;min-width:min-content}
.strip__ol li{flex:1 0 76px;max-width:200px;min-width:76px}
.strip__ol a{position:relative;display:grid;grid-template-rows:34px 22px 16px;justify-items:center;align-items:center;text-decoration:none;color:var(--ink);padding:0 4px;height:var(--striph-in,74px)}
.strip__ol a::before{content:"";position:absolute;left:0;right:0;top:41px;height:8px;background:var(--c)}
.room-design .strip__ol a::before{box-shadow:0 1.5px 0 var(--ink),0 -1.5px 0 var(--ink)}
.strip__ol li:first-child a::before{left:50%;border-radius:4px 0 0 4px}
.strip__ol li:last-child a::before{right:50%;border-radius:0 4px 4px 0}
.sn{align-self:end;font-size:12.5px;font-weight:600;line-height:1.15;text-align:center;max-width:100%;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:3px}
.sm{position:relative;z-index:1;width:5px;height:15px;margin-top:-13px;background:var(--c)}
.room-design .sm{box-shadow:0 0 0 1.5px var(--ink)}
.is-x .sm{width:18px;height:18px;margin-top:0;border-radius:50%;background:var(--white);border:3px solid var(--ink);box-shadow:none}
.sx{position:absolute;right:-9px;top:-7px;width:9px;height:9px;border-radius:50%;background:var(--c);box-shadow:0 0 0 1.5px var(--white)}
.sy{visibility:hidden;font-size:11px;font-weight:800;line-height:1;background:var(--ink);color:var(--white);border-radius:999px;padding:3px 7px 2px;white-space:nowrap}
.strip__ol a:hover .sn{text-decoration:underline}
.strip__ol .here .sn{font-weight:800}
.strip__ol .here .sm{width:24px;height:24px;margin-top:0;border-radius:50%;background:var(--ink);border:4px solid var(--white);box-shadow:0 0 0 2.5px var(--ink)}
.strip__ol .here .sy{visibility:visible}

/* ---------- stops along the line ---------- */
.line{position:relative;max-width:var(--max);margin:0 auto;padding:0 var(--gut) 72px;--rail:18px;--ind:72px}
.line::before{content:"";position:absolute;left:calc(var(--gut) + var(--rail));top:0;bottom:120px;width:8px;margin-left:-4px;background:var(--c)}
.room-design .line::before{box-shadow:1.5px 0 0 var(--ink),-1.5px 0 0 var(--ink)}
.stop,.zone,.extra,.change{position:relative;margin-left:var(--ind);min-width:0}
.stop{padding-top:clamp(52px,8vh,104px)}
.stop__h{position:relative;max-width:62em}
.stop__mk{position:absolute;left:calc(var(--rail) - var(--ind));top:14px;width:20px;height:6px;background:var(--c)}
.room-design .stop__mk{box-shadow:0 0 0 1.5px var(--ink)}
.stop__mk.is-x{width:24px;height:24px;margin:-9px 0 0 -12px;border-radius:50%;background:var(--white);border:4px solid var(--ink);box-shadow:none}
.stop__code{display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;font-weight:600;font-size:15px}
.stop__code .code{background:var(--c);color:var(--f);font-weight:800;padding:4px 9px 2px;border-radius:5px;font-variant-numeric:tabular-nums}
.room-design .stop__code .code{box-shadow:inset 0 0 0 1.5px var(--ink)}
.cnt{color:var(--mute);font-variant-numeric:tabular-nums}
.stop__t{margin-top:12px;font-weight:800;font-size:clamp(32px,4vw,60px);line-height:1;letter-spacing:-.01em;overflow-wrap:break-word}
.stop__sub{margin-top:8px;font-weight:600;font-size:clamp(18px,1.6vw,22px);color:var(--mute)}
.stop__code .kk{border:1.5px solid var(--ink);border-radius:999px;padding:3px 11px 1px;font-size:13px;font-weight:600;background:var(--white)}
.stop__code .cnt{margin-right:4px}
.chg{margin-top:16px;display:flex;gap:12px;align-items:flex-start;max-width:46em;border:2px solid var(--ink);border-radius:12px;background:var(--white);padding:11px 14px 9px;font-size:15px;line-height:1.45}
.chg a{font-weight:800}
.stop__lede{margin-top:18px;max-width:40em;font-size:clamp(19px,1.5vw,23px);line-height:1.45}

.zone{padding-top:clamp(60px,9vh,112px);scroll-margin-top:calc(var(--barh) + var(--striph))}
.zone .gdiv{position:relative;border-top:3px solid var(--ink);padding-top:16px;max-width:62em;scroll-margin-top:calc(var(--barh) + var(--striph) + 12px)}
.zone .gdiv::before{content:"";position:absolute;top:-3px;left:calc(-1 * var(--ind));width:var(--ind);height:3px;background:var(--ink)}
.zn{margin-bottom:10px}
.zn span{display:inline-block;background:var(--ink);color:var(--white);font-weight:800;font-size:14px;padding:5px 12px 3px;border-radius:999px}
.gdiv__t{font-weight:800;font-size:clamp(24px,2.4vw,34px);line-height:1.1}
.gdiv__p{margin-top:8px;max-width:44em;color:var(--mute);font-size:18px}
.extra{padding-top:clamp(60px,9vh,112px)}
.xsec{border:3px solid var(--ink);background:var(--white);padding:clamp(18px,2.4vw,30px);scroll-margin-top:calc(var(--barh) + var(--striph) + 12px)}
.xsec .eyebrow{font-weight:600;color:var(--mute);font-size:15px}
.xsec__t{font-weight:800;font-size:clamp(24px,2.4vw,34px);line-height:1.1;margin:4px 0 16px}
.xsec__list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 32px}
.xsec__list>div{border-top:2px solid var(--ink);padding-top:10px}
.xsec__list h3{font-weight:800;font-size:19px;line-height:1.25;margin-bottom:4px}
.xsec__list p{font-size:16px}
.change{display:flex;flex-direction:column;gap:4px;margin-top:clamp(64px,10vh,120px);padding:18px 22px 16px;border:3px solid var(--ink);border-radius:14px;background:var(--c, var(--white));color:var(--f, var(--ink));text-decoration:none;max-width:38em}
.home-change{background:var(--white);color:var(--ink)}
.change__k{font-weight:600;font-size:15px}
.change__t{font-weight:800;font-size:clamp(26px,3vw,42px);line-height:1.05}
.change:hover .change__t{text-decoration:underline}

/* ---------- case body: the live markup, restyled on white ---------- */
.cbody{display:grid;grid-template-columns:minmax(0,1fr);gap:clamp(28px,4vh,48px);margin-top:clamp(26px,3vw,40px);max-width:1240px;min-width:0}
.cbody>*{min-width:0}
.cbody p,.cbody li,.cbody dd,.cbody figcaption{overflow-wrap:break-word}
.cbody p{max-width:44em}
.cbody a{text-decoration:underline;text-decoration-thickness:1.5px;text-underline-offset:3px}
.cbody strong{font-weight:800}
.cbody code{font-family:var(--ff);font-weight:600;font-size:.92em;background:var(--soft);padding:.05em .35em;border-radius:3px}
.cbody h3{font-weight:800;font-size:clamp(22px,2vw,30px);line-height:1.15}
.cbody h4{font-weight:800;font-size:17px;line-height:1.3}
.cbody ul,.cbody ol{padding-left:1.25em;display:grid;gap:.55em}
.cbody li::marker{color:var(--mute)}
.cbody figure{display:grid;grid-template-columns:minmax(0,1fr);gap:10px;align-content:start;min-width:0}
.cbody img{display:block;width:100%;height:auto;border:1px solid var(--ink);background:var(--white)}
.cbody img.portrait,.cbody video.portrait{max-width:min(100%,360px)}
.cbody figcaption{font-size:14.5px;line-height:1.45;color:var(--mute);max-width:44em}
.cbody .wide:has(img.portrait){max-width:360px}
.cbody .links{display:flex;flex-wrap:wrap;align-items:center;gap:10px;max-width:none}
.cbody .links a{display:inline-flex;align-items:center;gap:9px;padding:10px 17px 8px;border-radius:999px;background:var(--c);color:var(--f);font-weight:800;font-size:15px;line-height:1.2;text-decoration:none;border:2px solid var(--c)}
.room-design .cbody .links a{border-color:var(--ink)}
.cbody .links a::after{content:"\2192";font-weight:800}
.cbody .links a:hover{background:var(--ink);color:var(--white);border-color:var(--ink)}
.cbody .links span{font-size:15px;color:var(--mute);font-weight:600}
.cbody .cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(28px,4vw,64px);align-items:start}
.cbody .block{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;align-content:start;min-width:0}
.cbody .grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px clamp(20px,3vw,40px)}
.cbody .grid3>div,.cbody .more>div{display:grid;gap:6px;align-content:start;border-top:2px solid var(--ink);padding-top:10px}
.cbody .grid3 p,.cbody .more p{font-size:16px}
.cbody .shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(20px,3vw,40px);align-items:start}
.cbody .gallery{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(14px,2vw,24px);align-items:start}
.cbody .gallery figcaption{font-size:13px}
.cbody .more{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px clamp(28px,4vw,56px)}
.cbody .made{display:grid;gap:4px;border-left:8px solid var(--c);background:var(--white);padding:12px 16px 10px;max-width:52em}
.room-design .cbody .made{box-shadow:inset 1.5px 0 0 var(--ink)}
.cbody .made b{font-weight:800;font-size:15px}
.cbody .note{border-left:3px solid var(--ink);padding-left:14px;color:var(--mute)}
.cbody .sub-case{border-top:2px solid var(--ink);padding-top:14px}
.cbody .stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,280px),1fr));column-gap:28px;border-top:3px solid var(--ink);margin:0;max-width:1100px}
.cbody .stats>div{display:flex;align-items:baseline;justify-content:space-between;gap:16px;padding:10px 2px 8px;border-bottom:1px solid var(--rule);min-width:0}
.cbody .stats dt{font-size:15px;line-height:1.35;min-width:0}
.cbody .stats dd{margin:0;flex:none;font-weight:800;font-size:22px;line-height:1.1;font-variant-numeric:tabular-nums;white-space:nowrap}
.cbody .compare{position:relative;overflow:hidden;width:100%;max-width:100%;border:1px solid var(--ink);background:var(--soft);--pos:50%;touch-action:pan-y}
.cbody .compare.portrait{max-width:360px}
.cbody .compare img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border:0;max-width:none}
.cbody .compare img.after{clip-path:inset(0 0 0 var(--pos))}
.cbody .cmp-line{position:absolute;top:0;bottom:0;left:var(--pos);width:3px;margin-left:-1.5px;background:var(--white);pointer-events:none;box-shadow:0 0 0 1px var(--ink)}
.cbody .cmp-line::after{content:"\2194";position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:40px;height:40px;border-radius:50%;background:var(--ink);color:var(--white);display:grid;place-items:center;font-weight:800;font-size:18px}
.cbody .cmp-tag{position:absolute;top:10px;font-weight:800;font-size:12px;line-height:1;background:var(--ink);color:var(--white);padding:6px 9px 4px;border-radius:999px;pointer-events:none}
.cbody .cmp-tag.l{left:10px}.cbody .cmp-tag.r{right:10px}
.cbody .compare input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize}
.cbody .compare:focus-within{outline:3px solid var(--ink);outline-offset:3px}
.cbody video{display:block;width:100%;height:auto;background:#000;border:1px solid var(--ink)}
.cbody .reels{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:clamp(10px,1.4vw,18px);align-items:start}
.cbody .reels.two{grid-template-columns:repeat(2,minmax(0,1fr));max-width:760px}
.cbody .reels video{aspect-ratio:9/16;object-fit:cover}
.cbody .reels figcaption{font-size:13px}
.cbody .flow{list-style:none;padding:0;counter-reset:step;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px}
.cbody .flow li{counter-increment:step;display:grid;gap:6px;align-content:start;border-top:8px solid var(--c);padding-top:10px}
.cbody .flow b{font-weight:800;font-size:19px}
.cbody .flow b::before{content:counter(step,decimal-leading-zero) "  ";color:var(--mute);font-size:14px}
.cbody .flow span{font-size:15.5px}
.cbody .piece{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(22px,4vw,52px);align-items:start}
.cbody .piece.flip>figure{order:2}
.cbody .piece-text{display:grid;gap:14px;min-width:0;align-content:start}
.cbody .tags{display:flex;flex-wrap:wrap;gap:8px}
.cbody .tag{font-weight:600;font-size:13px;padding:4px 10px 2px;border-radius:999px;border:1.5px solid var(--ink)}
.cbody .tag.hot{background:var(--ink);color:var(--white)}
.cbody .facts{display:flex;flex-wrap:wrap;gap:6px 24px;font-size:15px;color:var(--mute)}
.cbody .facts strong{color:var(--ink);font-size:20px;margin-right:.2em}
.cbody .books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(18px,2.4vw,32px);align-items:start}
.cbody .book{display:grid;gap:12px;align-content:start;min-width:0;padding:clamp(16px,2vw,26px);border:2px solid var(--ink);background:var(--white)}
.cbody .book.lead{grid-column:1/-1;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:clamp(18px,3vw,36px)}
.cbody .book .cover{width:100%;max-width:240px;height:auto}
.cbody .lead-text{display:grid;gap:12px;min-width:0}
.cbody .kind{font-weight:600;font-size:14px;color:var(--mute)}
.cbody .count{font-weight:800;font-size:20px;font-variant-numeric:tabular-nums}
.cbody .logline{font-size:19px;font-weight:600}

/* ---------- responsive ---------- */
@media (max-width:1100px){
  .chip span{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .chip{padding:4px}
  .cbody .flow{grid-template-columns:repeat(3,minmax(0,1fr))}
  .cbody .gallery{grid-template-columns:repeat(3,minmax(0,1fr))}
  .cbody .reels{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media (max-width:900px){
  .sheet{grid-template-columns:minmax(0,1fr)}
  .legend{grid-template-columns:minmax(0,1fr)}
  .rl{grid-template-columns:minmax(0,1fr)}
  .cbody .grid3{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody .piece,.cbody .book.lead{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:767px){
  :root{--barh:54px;--striph:80px}
  body{font-size:16.5px}
  .bar__in{gap:8px;padding-left:12px;padding-right:12px}
  .home{padding:7px 11px 6px 9px}
  .chips{gap:4px}
  .chip b{width:26px;height:26px}
  .yah{display:none}
  .frame{aspect-ratio:auto;height:min(72vh,560px);max-height:none}
  .line{--rail:10px;--ind:34px}
  .stop__mk{width:14px}
  .cbody .cols,.cbody .shots,.cbody .more,.cbody .books,.xsec__list{grid-template-columns:minmax(0,1fr)}
  .cbody .gallery,.cbody .grid3,.cbody .reels{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cbody .flow{grid-template-columns:minmax(0,1fr)}
  .ttt,.ttt tbody,.ttt tr,.ttt th,.ttt td{display:block;width:auto}
  .ttt thead{display:none}
  .ttt tr{border-bottom:2px solid var(--ink)}
  .ttt tbody th{border-bottom:0;padding-bottom:2px;min-width:0}
  .ttt td{border-bottom:0;padding-top:2px}
  .ttt tbody tr:nth-child(even)>*{background:none}
  .tt__l{display:block;font-size:12.5px;font-weight:800;color:var(--mute)}
  .tt__none{display:none}
  .board{font-size:15px}
}
@media (max-width:420px){
  .home{padding:6px 9px}
  .chip b{width:24px;height:24px;font-size:12px}
  .cbody .gallery,.cbody .grid3{grid-template-columns:minmax(0,1fr)}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{transition:none!important;animation:none!important}
}
'''

JS = r'''/* Mockup I, "Transit Map". Generated by themed/render_i.py. */
(function () {
  'use strict';
  var d = document;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function qsa(s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); }

  /* ---------- fit big words to one line, shrink big numbers that would overflow ---------- */
  function fit() {
    qsa('.fit').forEach(function (el) {
      var box = el.parentNode, cs = getComputedStyle(box);
      var avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var cap = +el.getAttribute('data-cap') || 200;
      el.style.fontSize = '100px';
      var w = el.getBoundingClientRect().width;
      if (!w) return;
      el.style.fontSize = Math.max(12, Math.min(cap, Math.floor(1000 * avail / w * 0.995) / 10)) + 'px';
    });
    qsa('.cbody .stats dd, .svc .num').forEach(function (el) {
      el.style.fontSize = '';
      var row = el.closest('div, td');
      if (!row) return;
      var s = parseFloat(getComputedStyle(el).fontSize), guard = 0;
      var over = function () { return row.scrollWidth > row.clientWidth + 1 || el.getBoundingClientRect().right > row.getBoundingClientRect().right + 1; };
      while (over() && s > 12 && guard++ < 40) { s -= 1; el.style.fontSize = s + 'px'; }
    });
  }
  var fr = 0;
  function sched() { cancelAnimationFrame(fr); fr = requestAnimationFrame(fit); }
  fit();
  addEventListener('resize', sched);
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(fit);
  addEventListener('load', fit);

  /* ---------- before / after sliders ---------- */
  qsa('.compare').forEach(function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* ---------- copy the email ---------- */
  var cb = d.getElementById('copy');
  if (cb) cb.addEventListener('click', function () {
    var t = cb.getAttribute('data-copy'), st = d.getElementById('copystat');
    function ok(m) { if (st) { st.textContent = m; setTimeout(function () { st.textContent = ''; }, 2400); } }
    function fallback() {
      var ta = d.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px;top:0';
      d.body.appendChild(ta); ta.select();
      var good = false; try { good = d.execCommand('copy'); } catch (e) {}
      d.body.removeChild(ta); ok(good ? 'Copied.' : 'Select the address and copy it.');
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { ok('Copied.'); }, fallback);
    else fallback();
  });

  /* ---------- the network map ---------- */
  var svg = d.getElementById('net');
  if (svg) netmap(svg);

  function netmap(svg) {
    var frame = d.getElementById('frame'), board = d.getElementById('board');
    var boardDefault = board.innerHTML;
    var v0 = svg.getAttribute('data-vb').split(' ').map(Number);
    var V0 = { x: v0[0], y: v0[1], w: v0[2], h: v0[3] };
    function ar() { return (frame.clientWidth && frame.clientHeight) ? frame.clientWidth / frame.clientHeight : V0.w / V0.h; }
    var hub = svg.getAttribute('data-hub').split(' ').map(Number);
    var vb = { x: V0.x, y: V0.y, w: V0.w, h: V0.h };
    var iso = null, tween = 0;
    var COL = {};
    qsa('.lb').forEach(function (b) { COL[b.getAttribute('data-line')] = { c: b.style.getPropertyValue('--c'), f: b.style.getPropertyValue('--f'), n: b.querySelector('.lb__n').textContent, k: b.querySelector('.lb__c').textContent, l: b.querySelector('b').textContent }; });

    if (!reduce) { svg.classList.add('anim'); setTimeout(function () { svg.classList.remove('anim'); }, 1400); }

    function setVB(v) { vb = v; svg.setAttribute('viewBox', v.x.toFixed(1) + ' ' + v.y.toFixed(1) + ' ' + v.w.toFixed(1) + ' ' + v.h.toFixed(1)); }
    function clamp(v) {
      var A = ar(), maxW = Math.max(V0.w, V0.h * A);
      var w = Math.min(maxW, Math.max(V0.w / 6, v.w)), h = w / A;
      var cx = v.x + v.w / 2, cy = v.y + v.h / 2;
      cx = Math.min(V0.x + V0.w, Math.max(V0.x, cx)); cy = Math.min(V0.y + V0.h, Math.max(V0.y, cy));
      if (w >= maxW - 0.5) { cx = V0.x + V0.w / 2; cy = V0.y + V0.h / 2; }
      return { x: cx - w / 2, y: cy - h / 2, w: w, h: h };
    }
    function go(t, ms) {
      t = clamp(t); cancelAnimationFrame(tween);
      if (reduce || !ms) { setVB(t); return; }
      var f = { x: vb.x, y: vb.y, w: vb.w, h: vb.h }, t0 = performance.now();
      (function step(now) {
        var k = Math.min(1, (now - t0) / ms), e = k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        setVB({ x: f.x + (t.x - f.x) * e, y: f.y + (t.y - f.y) * e, w: f.w + (t.w - f.w) * e, h: f.h + (t.h - f.h) * e });
        if (k < 1) tween = requestAnimationFrame(step);
      })(t0);
    }
    function fitBox(x, y, w, h, pad) {
      x -= pad; y -= pad; w += 2 * pad; h += 2 * pad;
      var A = ar();
      if (w / h > A) { var nh = w / A; y -= (nh - h) / 2; h = nh; } else { var nw = h * A; x -= (nw - w) / 2; w = nw; }
      return { x: x, y: y, w: w, h: h };
    }
    function zoomAt(f, px, py) {
      var w = vb.w / f, h = vb.h / f;
      go({ x: px - (px - vb.x) / f, y: py - (py - vb.y) / f, w: w, h: h }, 0);
    }
    function upp() { var m = svg.getScreenCTM(); return m ? 1 / m.a : 1; }
    function toSvg(cx, cy) { var m = svg.getScreenCTM(); if (!m) return { x: 0, y: 0 }; var p = svg.createSVGPoint(); p.x = cx; p.y = cy; p = p.matrixTransform(m.inverse()); return { x: p.x, y: p.y }; }
    function home() {
      var full = fitBox(V0.x, V0.y, V0.w, V0.h, 0);
      var sc = frame.clientWidth / full.w;
      if (sc < 0.74 && frame.clientWidth) { var w = frame.clientWidth / 0.74; full = { x: hub[0] - w / 2, y: hub[1] - w / ar() / 2, w: w, h: w / ar() }; }
      return full;
    }

    /* dimming */
    function dim(line) {
      qsa('.ln, .tk, .sts', svg).forEach(function (e) { e.classList.toggle('dim', !!line && e.getAttribute('data-line') !== line); });
      qsa('.cap', svg).forEach(function (e) { e.classList.toggle('dim', !!line && e.getAttribute('data-lines').split(' ').indexOf(line) < 0); });
    }
    function badge(l) { var c = COL[l]; return '<span class="lbadge" style="--c:' + c.c + ';--f:' + c.f + '"><b>' + c.l + '</b>' + c.n + '</span>'; }
    function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
    function isoBoard(l) {
      var c = COL[l], short = c.n.replace(/ line$/, '');
      board.innerHTML = badge(l) + ' <span class="board__s">' + esc(c.k) + '</span>' +
        '<a class="ride" style="--c:' + c.c + ';--f:' + c.f + '" href="' + l + '/index.html">Ride the ' + esc(short) + ' line &rarr;</a>' +
        '<button type="button" class="tbtn" id="unisolate">Whole map</button>';
      d.getElementById('unisolate').addEventListener('click', restore);
    }
    function restBoard() { if (iso) isoBoard(iso); else board.innerHTML = boardDefault; }

    var cur = null;
    function hl(st) {
      if (cur) cur.classList.remove('on');
      cur = st; st.classList.add('on');
      var l = st.getAttribute('data-line');
      dim(l);
      board.innerHTML = badge(l) + ' <span class="board__c">' + esc(st.getAttribute('data-code')) + '</span> <span class="board__t">' + esc(st.getAttribute('data-t')) +
        '</span> <span class="board__s">' + esc(st.getAttribute('data-s')) + '</span> <span class="board__s">&middot; open on the line &rarr;</span>';
    }
    function unhl(st) {
      if (cur !== st) return;
      st.classList.remove('on'); cur = null;
      dim(iso); restBoard();
    }
    qsa('a.st', svg).forEach(function (st) {
      st.addEventListener('mouseenter', function () { hl(st); });
      st.addEventListener('mouseleave', function () { unhl(st); });
      st.addEventListener('focus', function () {
        hl(st);
        var c = st.querySelector('.dot'), x = +c.getAttribute('cx'), y = +c.getAttribute('cy');
        if (x < vb.x + 20 || x > vb.x + vb.w - 20 || y < vb.y + 20 || y > vb.y + vb.h - 20) go({ x: x - vb.w / 2, y: y - vb.h / 2, w: vb.w, h: vb.h }, 300);
      });
      st.addEventListener('blur', function () { unhl(st); });
    });

    /* isolate a line */
    function isolate(l) {
      iso = l; dim(l);
      qsa('.lb').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-line') === l ? 'true' : 'false'); });
      var bb = svg.querySelector('.ln[data-line="' + l + '"]').getAttribute('data-bb').split(' ').map(Number);
      go(fitBox(bb[0], bb[1], bb[2], bb[3], 36), 520);
      isoBoard(l);
    }
    function restore() {
      if (!iso) return;
      iso = null; dim(null);
      qsa('.lb').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      go(home(), 520); restBoard();
    }
    qsa('.lb').forEach(function (b) {
      b.addEventListener('click', function () {
        var l = b.getAttribute('data-line');
        if (iso === l) restore(); else { if (lview && !lview.hidden) setView(false); isolate(l); }
      });
    });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && iso) { restore(); } });

    /* pan, pinch, wheel (with ctrl/cmd or a trackpad pinch), buttons */
    var ptr = {}, start = null, dragged = false;
    function pts() { return Object.keys(ptr).map(function (k) { return ptr[k]; }); }
    frame.addEventListener('pointerdown', function (e) {
      if (e.button > 0) return;
      ptr[e.pointerId] = { x: e.clientX, y: e.clientY };
      var p = pts();
      dragged = false;
      if (p.length === 1) start = { x: e.clientX, y: e.clientY, vb: { x: vb.x, y: vb.y, w: vb.w, h: vb.h }, u: upp() };
      else if (p.length === 2) {
        var m = toSvg((p[0].x + p[1].x) / 2, (p[0].y + p[1].y) / 2);
        start = { pinch: Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y), vb: { x: vb.x, y: vb.y, w: vb.w, h: vb.h }, m: m };
        dragged = true;
      }
    });
    frame.addEventListener('pointermove', function (e) {
      if (!ptr[e.pointerId] || !start) return;
      ptr[e.pointerId] = { x: e.clientX, y: e.clientY };
      var p = pts();
      if (p.length === 1 && !start.pinch) {
        var dx = e.clientX - start.x, dy = e.clientY - start.y;
        if (!dragged && Math.hypot(dx, dy) < 5) return;
        if (!dragged) { dragged = true; frame.classList.add('is-drag'); try { frame.setPointerCapture(e.pointerId); } catch (x) {} }
        cancelAnimationFrame(tween);
        setVB(clamp({ x: start.vb.x - dx * start.u, y: start.vb.y - dy * start.u, w: start.vb.w, h: start.vb.h }));
      } else if (p.length === 2 && start.pinch) {
        var dist = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y), f = dist / start.pinch;
        var w = start.vb.w / f, h = start.vb.h / f, m = start.m;
        setVB(clamp({ x: m.x - (m.x - start.vb.x) / f, y: m.y - (m.y - start.vb.y) / f, w: w, h: h }));
      }
      e.preventDefault();
    });
    function up(e) {
      delete ptr[e.pointerId];
      if (!pts().length) { frame.classList.remove('is-drag'); start = null; }
      else if (pts().length === 1) { var q = pts()[0]; start = { x: q.x, y: q.y, vb: { x: vb.x, y: vb.y, w: vb.w, h: vb.h }, u: upp() }; }
    }
    frame.addEventListener('pointerup', up);
    frame.addEventListener('pointercancel', up);
    svg.addEventListener('click', function (e) {
      if (dragged) { e.preventDefault(); e.stopPropagation(); dragged = false; return; }
      if (!e.target.closest('a.st') && iso) restore();
    }, true);
    frame.addEventListener('wheel', function (e) {
      if (!(e.ctrlKey || e.metaKey)) return;
      e.preventDefault();
      var p = toSvg(e.clientX, e.clientY);
      zoomAt(Math.exp(-e.deltaY * 0.01), p.x, p.y);
    }, { passive: false });
    function center() { return { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2 }; }
    d.getElementById('zin').addEventListener('click', function () { var c = center(); var t = { w: vb.w / 1.4 }; go({ x: c.x - t.w / 2, y: c.y - t.w / ar() / 2, w: t.w, h: t.w / ar() }, 240); });
    d.getElementById('zout').addEventListener('click', function () { var c = center(); var w = vb.w * 1.4; go({ x: c.x - w / 2, y: c.y - w / ar() / 2, w: w, h: w / ar() }, 240); });
    d.getElementById('zfit').addEventListener('click', function () { if (iso) restore(); else go(fitBox(V0.x, V0.y, V0.w, V0.h, 0), 360); });

    /* map view or list view; list by default on phones */
    var vbtn = d.getElementById('view'), lview = d.getElementById('lview'), zoomCtl = d.querySelector('.zoom');
    function setView(list) {
      lview.hidden = !list; frame.hidden = list; board.hidden = list; zoomCtl.hidden = list;
      vbtn.setAttribute('aria-pressed', list ? 'true' : 'false');
      vbtn.textContent = list ? 'Map view' : 'List view';
      if (!list) setVB(clamp(home()));
    }
    vbtn.addEventListener('click', function () { setView(lview.hidden); });
    if (innerWidth < 768) setView(true); else setVB(clamp(home()));
    var lastW = innerWidth;
    addEventListener('resize', function () { if (Math.abs(innerWidth - lastW) > 40 && !iso) { lastW = innerWidth; if (!frame.hidden) setVB(clamp(home())); } });
  }

  /* ---------- room pages: you-are-here strip, Esc goes Home ---------- */
  if (d.body.classList.contains('room')) {
    addEventListener('keydown', function (e) {
      var t = d.activeElement || {};
      if (e.key === 'Escape' && !e.defaultPrevented && !/^(INPUT|TEXTAREA|SELECT|VIDEO)$/.test(t.tagName || '')) location.href = '../index.html';
    });
    var stops = qsa('.stop'), sc = d.getElementById('strip-sc'), yah = d.getElementById('yah-a');
    var items = {}; qsa('.strip__ol li').forEach(function (li) { items[li.getAttribute('data-id')] = li; });
    var yahDefault = yah ? yah.textContent : '';
    var now = null, raf = 0;
    function mark() {
      raf = 0;
      var st = d.getElementById('strip'), lim = (st ? st.getBoundingClientRect().bottom : 0) + 48, hit = stops[0] || null;
      // measure the stop block itself: a deep link (#id) scrolls the block's top, not its title, to just under the strip
      for (var i = 0; i < stops.length; i++) { if (stops[i].getBoundingClientRect().top <= lim) hit = stops[i]; else break; }
      if (stops.length && innerHeight + scrollY >= d.documentElement.scrollHeight - 2) {
        var last = stops[stops.length - 1]; if (last.getBoundingClientRect().top < innerHeight) hit = last;
      }
      var id = hit ? hit.id : null;
      if (id === now) return;
      if (now && items[now]) { items[now].classList.remove('here'); items[now].querySelector('a').removeAttribute('aria-current'); }
      now = id;
      if (yah) { yah.textContent = id ? hit.querySelector('.code').textContent + ' ' + hit.querySelector('.stop__t').textContent : yahDefault; yah.setAttribute('href', id ? '#' + id : '#top'); }
      if (!id || !items[id]) return;
      var li = items[id];
      li.classList.add('here'); li.querySelector('a').setAttribute('aria-current', 'location');
      if (sc && sc.scrollWidth > sc.clientWidth) {
        var left = li.offsetLeft - sc.clientWidth / 2 + li.offsetWidth / 2;
        try { sc.scrollTo({ left: left, behavior: reduce ? 'auto' : 'smooth' }); } catch (x) { sc.scrollLeft = left; }
      }
    }
    addEventListener('scroll', function () { if (!raf) raf = requestAnimationFrame(mark); }, { passive: true });
    addEventListener('resize', function () { if (!raf) raf = requestAnimationFrame(mark); });
    addEventListener('hashchange', function () { requestAnimationFrame(mark); });
    addEventListener('load', mark);
    mark();
  }
})();
'''


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)


def main():
    hp, L = home()
    write(os.path.join(OUT, 'index.html'), hp)
    for r in ROOMS:
        write(os.path.join(OUT, r['slug'], 'index.html'), room(r))
    write(os.path.join(OUT, 'i.css'), CSS)
    write(os.path.join(OUT, 'i.js'), JS)
    print('mockup-i: %d rooms, %d stations, %d interchanges, map %s' % (len(ROOMS), N_CASES, len(XCH), ' '.join('%.0f' % v for v in L['bb'])))


if __name__ == '__main__':
    main()


# style switcher (see add_switcher.py)
import runpy as _rp
import os as _os; _rp.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "add_switcher.py"), run_name="__main__")
