"""Civitas: the city map for mockup O, drawn by code.

    import citymap; svg, meta = citymap.build(links)

A walled city in the manner of a 16th-century bird's-eye town view: a tilted ground plan (depth squashed
to 0.6 and skewed a little to the right so the right-hand walls of buildings show), every building drawn
as an elevation standing on its footprint, a dense fabric of small houses along the streets with gardens
in the block interiors, and the important buildings drawn by hand-written functions several times larger.
Everything is seeded, so the map is the same on every run. Stdlib only.

Classes (styled in o.css): p paper fill + ink line, sh shaded wall, rr/rg/ro washed roofs (vermilion,
verdigris, ochre), k ink fill, n line only, h fine hatch, st street wash, wt water, gd garden ground.
"""
import html
import json
import re
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
WID = json.load(open(os.path.join(HERE, 'widths.json'), encoding='utf-8'))
W, H = 1600, 1000
DX, DY = 0.42, 0.6          # a step back in depth moves 0.42 right and 0.6 up


def tw(s, font, size):
    return sum(WID[font].get(c, 0.5) for c in s) * size


PREC = [1]          # decimals written; ground hatching drops to whole units


def f(v):
    if PREC[0] == 0:
        return str(int(round(v)))
    v = round(v, 1)
    if v == int(v):
        return str(int(v))
    return '%.1f' % v


def pts(ps):
    return ' '.join(f(x) + ',' + f(y) for x, y in ps)


def Mz(ps):
    return 'M' + pts(ps) + 'Z'


def Ml(ps):
    return 'M' + pts(ps)


def path(d, c):
    return '<path class="%s" d="%s"/>' % (c, d)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def ell(cx, cy, rx, ry, a0, a1, n=12):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def circ(cx, cy, r):
    return 'M%s,%sa%s,%s 0 1 0 %s,0a%s,%s 0 1 0 -%s,0' % (f(cx - r), f(cy), f(r), f(r), f(2 * r), f(r), f(r), f(2 * r))


def spline(P, closed=False, step=9.0):
    n, out = len(P), []
    for i in (range(n) if closed else range(n - 1)):
        p0 = P[(i - 1) % n] if closed else P[max(i - 1, 0)]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed else P[min(i + 2, n - 1)]
        k = max(2, int(math.dist(p1, p2) / step))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


def wob(ps, rnd, amp=0.55):
    """A pen's slight unsteadiness: smoothed noise, never more than about half a pixel."""
    out, nx, ny = [], 0.0, 0.0
    for x, y in ps:
        nx = nx * 0.72 + rnd.uniform(-amp, amp) * 0.28 * 2
        ny = ny * 0.72 + rnd.uniform(-amp, amp) * 0.28 * 2
        out.append((x + nx, y + ny))
    return out


def dseg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def pip(x, y, poly):
    c, n = False, len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def offset(ring, dist):
    """Move every point of a closed ring toward its centroid side by dist (a convex ring is assumed)."""
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    n, out = len(ring), []
    for i in range(n):
        a, b = ring[i - 1], ring[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        x, y = ring[i]
        if (cx - x) * nx + (cy - y) * ny < 0:
            nx, ny = -nx, -ny
        out.append((x + nx * dist, y + ny * dist))
    return out


def clip_line(p, q, poly):
    """Clip segment p-q to a convex polygon (Cyrus-Beck). Returns None or the clipped pair."""
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1 if area > 0 else -1
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        nx, ny = s * (a[1] - b[1]), s * (b[0] - a[0])      # inward normal
        num = nx * (p[0] - a[0]) + ny * (p[1] - a[1])
        den = nx * dx + ny * dy
        if abs(den) < 1e-9:
            if num < 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (p[0] + dx * t0, p[1] + dy * t0), (p[0] + dx * t1, p[1] + dy * t1)


# ------------------------------------------------------------------ a drawing in 3D (u along, d back, z up)
class O:
    def __init__(s, x, y):
        s.x, s.y, s.o = x, y, []

    def p(s, u, d=0, z=0):
        return (s.x + u + DX * d, s.y - DY * d - z)

    def P(s, q):
        return [s.p(*a) for a in q]

    def poly(s, q, c='p'):
        s.o.append(path(Mz(s.P(q)), c))

    def polys(s, qs, c='p'):
        s.o.append(path(''.join(Mz(s.P(q)) for q in qs), c))

    def line(s, q, c='n'):
        s.o.append(path(Ml(s.P(q)), c))

    def lines(s, qs, c='n'):
        if qs:
            s.o.append(path(''.join(Ml(s.P(q)) for q in qs), c))

    def raw(s, t):
        s.o.append(t)

    def svg(s):
        return ''.join(s.o)


def hatch3(a0, a1, b0, b1, n, t0=0.12, t1=0.88):
    """n lines from edge a (a0..a1) to edge b (b0..b1), in 3D tuples."""
    out = []
    for i in range(n):
        t = t0 + (t1 - t0) * (i / (n - 1) if n > 1 else 0.5)
        A = tuple(a0[k] + (a1[k] - a0[k]) * t for k in range(3))
        B = tuple(b0[k] + (b1[k] - b0[k]) * t for k in range(3))
        out.append([A, B])
    return out


def box(o, u0, u1, d0, d1, h, z0=0, cf='p', cr='sh'):
    o.poly([(u1, d0, z0), (u1, d1, z0), (u1, d1, z0 + h), (u1, d0, z0 + h)], cr)
    o.poly([(u0, d0, z0), (u1, d0, z0), (u1, d0, z0 + h), (u0, d0, z0 + h)], cf)


def roof_u(o, u0, u1, d0, d1, h, r, c='rr', hip=0, n=0, gable='sh'):
    """Ridge along u. Front slope with optional hatching; right end a hip or a gable."""
    dm = (d0 + d1) / 2
    if hip:
        o.poly([(u1, d0, h), (u1, d1, h), (u1 - hip, dm, h + r)], c)
    else:
        o.poly([(u1, d0, h), (u1, d1, h), (u1, dm, h + r)], gable)
    o.poly([(u0, d0, h), (u1, d0, h), (u1 - hip, dm, h + r), (u0 + hip, dm, h + r)], c)
    if n:
        o.lines([[(u0 + hip * 0 + (u1 - u0) * t, d0, h), (u0 + hip + (u1 - u0 - 2 * hip) * t, dm, h + r)]
                 for t in [(i + 0.5) / n for i in range(n)]], 'h')


def roof_d(o, u0, u1, d0, d1, h, r, c='rr', n=0):
    """Ridge along d (a gable facing the viewer). Both slopes, hatching on the right one."""
    um = (u0 + u1) / 2
    o.poly([(u0, d0, h), (um, d0, h + r), (um, d1, h + r), (u0, d1, h)], c)
    o.poly([(u1, d0, h), (u1, d1, h), (um, d1, h + r), (um, d0, h + r)], c)
    if n:
        o.lines(hatch3((um, d0, h + r), (um, d1, h + r), (u1, d0, h), (u1, d1, h), n), 'h')


def gable_front(o, u0, u1, d, h, r, c='p'):
    um = (u0 + u1) / 2
    o.poly([(u0, d, 0), (u1, d, 0), (u1, d, h), (um, d, h + r), (u0, d, h)], c)


def parch(o, u, d, z, w, hh, c='k'):
    """A pointed arch opening on a front plane: left foot at (u, d, z), width w, total height hh."""
    x, y = o.p(u, d, z)
    s = hh - w * 0.75
    o.raw(path('M%s,%sv-%sC%s,%s %s,%s %s,%sC%s,%s %s,%s %s,%sv%sZ' % (
        f(x), f(y), f(s), f(x), f(y - s - w * 0.4), f(x + w * 0.28), f(y - s - w * 0.68), f(x + w / 2), f(y - hh),
        f(x + w * 0.72), f(y - s - w * 0.68), f(x + w), f(y - s - w * 0.4), f(x + w), f(y - s), f(s)), c))


def rarch(o, u, d, z, w, hh, c='k'):
    """A round-headed opening."""
    x, y = o.p(u, d, z)
    s = max(0.1, hh - w / 2)
    o.raw(path('M%s,%sv-%sa%s,%s 0 0 1 %s,0v%sZ' % (f(x), f(y), f(s), f(w / 2), f(w / 2), f(w), f(s)), c))


def rect_k(o, u, d, z, w, hh, c='k'):
    x, y = o.p(u, d, z)
    o.raw(path('M%s,%sh%sv-%sh-%sZ' % (f(x), f(y), f(w), f(hh), f(w)), c))


def cyl(o, u, d, z0, r, h, top='cone', rh=14, rc='rr', shade=True, cren=True):
    """A round tower: body, shaded right side, crenellated top or a conical roof."""
    cx, cy = o.p(u, d, z0)
    ry = r * 0.5
    near = ell(cx, cy, r, ry, math.pi, 0, 10)                       # left to right along the near side
    body = [(cx - r, cy - h)] + near + [(cx + r, cy - h)] + [(x, y - h) for x, y in near[::-1]]
    o.raw(path(Mz(body), 'p'))
    if shade:
        o.raw(path(''.join(Ml([(cx + r * k, cy + ry * math.sqrt(1 - k * k) - 0.4), (cx + r * k, cy - h + ry * math.sqrt(1 - k * k))])
                           for k in (0.45, 0.68, 0.86)), 'h'))
    if top == 'cone':
        base = ell(cx, cy - h, r + 1.2, ry + 0.6, math.pi, 0, 8)
        o.raw(path(Mz(base + [(cx, cy - h - rh)]), rc))
        o.raw(path('M%s,%sv-3' % (f(cx), f(cy - h - rh)), 'n'))
    else:
        o.raw(path(Mz(ell(cx, cy - h, r, ry, 0, 2 * math.pi, 16)), 'p'))
        if top == 'cren' and cren:
            m = ''
            for x, y in ell(cx, cy - h, r, ry, math.pi * 0.92, math.pi * 0.08, 5):
                m += 'M%s,%sh2.2v-2.6h-2.2Z' % (f(x - 1.1), f(y))
            o.raw(path(m, 'p'))


def merlons(o, u0, u1, d, z, step=4.4, mw=2.4, mh=2.6):
    x0, y0 = o.p(u0, d, z)
    x1, _ = o.p(u1, d, z)
    m, x = '', x0
    while x + mw <= x1 + 0.01:
        m += 'M%s,%sh%sv-%sh-%sZ' % (f(x), f(y0), f(mw), f(mh), f(mw))
        x += step
    o.raw(path(m, 'p'))


# ------------------------------------------------------------------ banderole (ribbon scroll with a name)
def banderole(cx, cy, text, fs=15.0, sub=''):
    w = tw(text, 'CR', fs) * 1.1 + 24          # Cardo bold, a touch wider than the regular widths
    x0, x1 = cx - w / 2, cx + w / 2
    h = fs * 0.62
    out = []
    # tails behind the band, swallow-tailed, dropping a little
    for side in (-1, 1):
        xe = x0 if side < 0 else x1
        tail = [(xe - side * 4, cy - h * 0.25), (xe + side * 16, cy - h * 0.05), (xe + side * 10, cy + h * 0.55),
                (xe + side * 17, cy + h * 1.2), (xe - side * 4, cy + h * 1.15)]
        out.append(path(Mz(tail), 'p bt0'))
        out.append(path(Mz([(xe, cy + h), (xe - side * 4, cy + h * 1.15), (xe - side * 4, cy + h * 0.7)]), 'k bt1'))
    band = ('M%s,%sQ%s,%s %s,%sL%s,%sQ%s,%s %s,%sZ' % (
        f(x0), f(cy - h), f(cx), f(cy - h - 3.2), f(x1), f(cy - h), f(x1), f(cy + h), f(cx), f(cy + h - 3.2), f(x0), f(cy + h)))
    out.append(path(band, 'p bb'))
    sub_t = ' <tspan class="bs" x="%s" y="%s">%s</tspan>' % (f(cx), f(cy + h + 19), html.escape(sub, quote=False)) if sub else ''
    if sub:                                   # a solid paper plate behind the count so map lines never cross it
        sw = tw(sub, 'CR', 16) * 1.02 + 14
        out.append('<rect class="bsp" x="%s" y="%s" width="%s" height="20" rx="3"/>' % (f(cx - sw / 2), f(cy + h + 4), f(sw)))
    out.append('<text class="bn" x="%s" y="%s" font-size="%s">%s%s</text>' % (f(cx), f(cy + fs * 0.3), f(fs), html.escape(text, quote=False), sub_t))
    return ''.join(out), (x0 - 18, cy - h - 4, w + 36, 2 * h + (24 if sub else 8))


# ------------------------------------------------------------------ houses
INLINE = {'p': '', 'r0': '', 'sh': ' fill="var(--shade)"', 'rr': ' fill="var(--w-red)"', 'k': ' fill="var(--ink)" stroke="none"',
          'h': ' fill="none" stroke-width=".4"', 'n': ' fill="none"'}


def inline(svg):
    """Drawings reused through <use> take fill and stroke from the use element (document classes do not reach
    inside a use element's copy), so only the departures from paper-and-ink are written out."""
    return re.sub(r' class="([a-z0-9]+)"', lambda m: INLINE[m.group(1)], svg)


def house(x, y, w, dd, h, r, kind, rc, rnd):
    o = O(x, y)
    if kind == 'eave':
        dm = dd / 2
        o.poly([(w, 0, 0), (w, dd, 0), (w, dd, h), (w, dm, h + r), (w, 0, h)], 'sh')
        q = [(0, 0, h), (w, 0, h), (w, dm, h + r), (0, dm, h + r)]
        hs = ''.join(Ml(o.P([(u, 0, h), (u, dm, h + r)])) for u in [w * (i + 0.5) / int(w / 3.2) for i in range(int(w / 3.2))])
        o.raw(path(Mz(o.P(q)) + hs, rc))
        o.poly([(0, 0, 0), (w, 0, 0), (w, 0, h), (0, 0, h)], 'p')
        if rnd.random() < 0.5:
            cx = w * rnd.uniform(0.2, 0.7)
            o.poly([(cx, dm * 0.5, h + r * 0.5), (cx + 2.4, dm * 0.5, h + r * 0.5), (cx + 2.4, dm * 0.5, h + r + 3), (cx, dm * 0.5, h + r + 3)], 'p')
    else:
        um = w / 2
        o.poly([(w, 0, 0), (w, dd, 0), (w, dd, h), (w, 0, h)], 'sh')
        L = [(0, 0, h), (um, 0, h + r), (um, dd, h + r), (0, dd, h)]
        R = [(w, 0, h), (w, dd, h), (um, dd, h + r), (um, 0, h + r)]
        nh = 3 if dd < 17 else 4
        hs = ''.join(Ml(o.P(q)) for q in hatch3((um, 0, h + r), (um, dd, h + r), (w, 0, h), (w, dd, h), nh, 0.2, 0.85))
        o.raw(path(Mz(o.P(L)) + Mz(o.P(R)) + hs, rc))
        if kind == 'step':
            s1, s2 = r * 0.36, r * 0.7
            a1, a2 = w * 0.17, w * 0.33
            q = [(0, 0, 0), (w, 0, 0), (w, 0, h), (w, 0, h + s1 * 0.6), (w - a1, 0, h + s1 * 0.6), (w - a1, 0, h + s2), (w - a2, 0, h + s2),
                 (w - a2, 0, h + r + 1), (a2, 0, h + r + 1), (a2, 0, h + s2), (a1, 0, h + s2), (a1, 0, h + s1 * 0.6), (0, 0, h + s1 * 0.6)]
            o.poly(q, 'p')
        else:
            gable_front(o, 0, w, 0, h, r)
            if rnd.random() < 0.45:        # a timber-framed upper floor
                o.lines([[(0, 0, h * 0.55), (w, 0, h * 0.55)], [(um, 0, h * 0.55), (um, 0, h + r * 0.6)]], 'h')
    m = ''
    dx0 = x + w * rnd.uniform(0.25, 0.55)
    dh = min(5.2, h * 0.45)
    m += 'M%s,%sv-%sa1.2,1.2 0 0 1 2.4,0v%sZ' % (f(dx0), f(y), f(dh - 1.2), f(dh - 1.2))
    if h >= 10:
        n = max(1, int(w / 6.5))
        for i in range(n):
            wx = x + w * (i + 0.5) / n - 0.8
            m += 'M%s,%sh1.6v-2.4h-1.6Z' % (f(wx), f(y - h + 3.8))
    if kind != 'eave' and r > 7:
        m += 'M%s,%sh1.4v-2h-1.4Z' % (f(x + w / 2 - 0.7), f(y - h - r * 0.35))
    o.raw(path(m, 'k'))
    return o.svg()


def tree(x, y, r, rnd):
    t = 'M%s,%sv-%s' % (f(x), f(y), f(r * 0.9))
    c = circ(x, y - r * 0.9 - r, r)
    sh = 'M%s,%sv%s' % (f(x + r * 0.45), f(y - r * 2.4), f(r * 1.0))
    return path(t, 'n') + path(c, 'p') + path(sh, 'h')


# ------------------------------------------------------------------ the important buildings
def cathedral(x, y):
    """Side view from the north: apse at left (east), the two west towers at right. The near (north-west)
    tower stands unfinished; the far one carries the openwork spire."""
    o = O(x, y)
    # far (south-west) tower first: it stands behind everything else
    u0, u1 = 176, 210
    box(o, u0, u1, 30, 62, 176)
    for z in (40, 92, 140):
        parch(o, u0 + 9, 30, z, 6, 22)
        parch(o, u0 + 19, 30, z, 6, 22)
    o.lines([[(u0, 30, z), (u1, 30, z)] for z in (34, 86, 134, 172)], 'n')
    # octagonal belfry and openwork spire
    cx, cy = o.p((u0 + u1) / 2, 46, 176)
    o.raw(path(Mz([(cx - 15, cy), (cx - 15, cy - 26), (cx - 9, cy - 30), (cx + 9, cy - 30), (cx + 15, cy - 26), (cx + 15, cy)]), 'p'))
    o.raw(path('M%s,%sv-22M%s,%sv-22M%s,%sv-22' % (f(cx - 9), f(cy - 2), f(cx), f(cy - 2), f(cx + 9), f(cy - 2)), 'n'))
    sx = [(cx - 11, cy - 30), (cx, cy - 104), (cx + 11, cy - 30)]
    o.raw(path(Mz(sx), 'rg'))
    o.raw(path(''.join(Ml([(cx - 11 + 11 * t, cy - 30 - 74 * t), (cx + 11 - 11 * t, cy - 30 - 74 * t)]) for t in (0.18, 0.36, 0.54, 0.72)), 'h'))
    o.raw(path(Ml([(cx, cy - 30), (cx, cy - 104)]), 'n'))
    cr = ''
    for t in (0.12, 0.27, 0.42, 0.57, 0.72, 0.85):
        for s in (-1, 1):
            px, py = cx + s * 11 * (1 - t), cy - 30 - 74 * t
            cr += 'M%s,%sl%s,-2.4' % (f(px), f(py), f(s * 2.4))
    o.raw(path(cr, 'n'))
    o.raw(path('M%s,%sv-9M%s,%sh7' % (f(cx), f(cy - 104), f(cx - 3.5), f(cy - 110)), 'n'))
    # choir and apse (east end, left)
    h, r = 50, 44
    ap = [(30 + 22 * math.cos(a), 22 + 22 * math.sin(a)) for a in [math.pi * (0.5 + i / 4) for i in range(5)]]  # (30,44)->(30,0)
    faces = list(zip(ap[:-1], ap[1:]))
    for (a, b) in faces[1:]:
        o.poly([(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], h), (a[0], a[1], h)], 'p' if b[1] < 8 else 'sh')
    for (a, b) in faces[2:]:
        mu, md = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        parch(o, mu - 3, md, 16, 6, 24)
    o.polys([[(a[0], a[1], h), (b[0], b[1], h), (30, 22, h + r)] for a, b in faces[1:]], 'rg')
    # north aisle (lean-to) with buttresses and flyers, then the nave wall and roof above it
    A0, A1 = 30, 176
    o.poly([(A0, 0, h), (A1, 0, h), (A1, 22, h + r), (A0, 22, h + r)], 'rg')
    o.lines([[(u, 0, h), (u, 22, h + r)] for u in range(A0 + 6, A1, 7)], 'h')
    o.line([(A0, 22, h + r), (A1, 22, h + r)], 'n')
    o.poly([(A0, 0, 32), (A1, 0, 32), (A1, 0, h), (A0, 0, h)], 'p')
    for u in range(A0 + 8, A1 - 6, 14):
        parch(o, u + 2, 0, 35, 5, 13)
    o.poly([(A0, -18, 26), (A1, -18, 26), (A1, 0, 34), (A0, 0, 34)], 'rg')
    o.poly([(A0, -18, 0), (A1, -18, 0), (A1, -18, 26), (A0, -18, 26)], 'p')
    o.poly([(A1, -18, 0), (A1, 0, 0), (A1, 0, 34), (A1, -18, 26)], 'sh')
    bays = list(range(A0 + 7, A1, 14))
    for u in bays[:-1]:
        parch(o, u + 3, -18, 5, 6, 16)
    for u in bays:
        # buttress, pinnacle and flyer
        o.poly([(u - 2, -24, 0), (u + 2, -24, 0), (u + 2, -24, 30), (u - 2, -24, 30)], 'p')
        o.poly([(u + 2, -24, 0), (u + 2, -18, 0), (u + 2, -18, 30), (u + 2, -24, 30)], 'sh')
        bx, by = o.p(u, -24, 30)
        o.raw(path('M%s,%sL%s,%sL%s,%s' % (f(bx - 2), f(by), f(bx), f(by - 10), f(bx + 2), f(by)), 'p'))
        fx, fy = o.p(u, -22, 28)
        tx, ty = o.p(u, 0, 46)
        o.raw(path('M%s,%sQ%s,%s %s,%s' % (f(fx), f(fy), f((fx + tx) / 2 - 1), f(min(fy, ty) - 6), f(tx), f(ty)), 'n'))
    # north transept with its rose window, standing out toward the viewer
    T0, T1 = 92, 128
    tm = (T0 + T1) / 2
    o.poly([(T0, -34, h), (tm, -34, h + 30), (tm, 18, h + 30), (T0, 18, h)], 'rg')
    o.poly([(T1, -34, h), (T1, 18, h), (tm, 18, h + 30), (tm, -34, h + 30)], 'rg')
    o.lines(hatch3((tm, -34, h + 30), (tm, 18, h + 30), (T1, -34, h), (T1, 18, h), 4, 0.25, 0.75), 'h')
    o.poly([(T1, -34, 0), (T1, -18, 0), (T1, -18, h), (T1, -34, h)], 'sh')
    gable_front(o, T0, T1, -34, h, 30)
    rx, ry = o.p(tm, -34, 44)
    rose = circ(rx, ry, 11) + circ(rx, ry, 4)
    for i in range(12):
        a = i * math.pi / 6
        rose += 'M%s,%sL%s,%s' % (f(rx + 4 * math.cos(a)), f(ry + 4 * math.sin(a)), f(rx + 11 * math.cos(a)), f(ry + 11 * math.sin(a)))
    o.raw(path(rose, 'p'))
    parch(o, tm - 6, -34, 0, 12, 22)
    o.raw(path(Ml([o.p(tm - 9, -34, 0), o.p(tm - 9, -34, 24)]) + Ml([o.p(tm + 9, -34, 0), o.p(tm + 9, -34, 24)]), 'n'))
    # crossing fleche
    fx, fy = o.p(tm, 22, h + r)
    o.raw(path(Mz([(fx - 4, fy), (fx - 4, fy - 12), (fx + 4, fy - 12), (fx + 4, fy)]), 'p'))
    o.raw(path(Mz([(fx - 4.5, fy - 12), (fx, fy - 50), (fx + 4.5, fy - 12)]), 'rg'))
    o.raw(path('M%s,%sv-6M%s,%sh5' % (f(fx), f(fy - 50), f(fx - 2.5), f(fy - 53)), 'n'))
    # the near (north-west) tower: unfinished, with a broken top
    u0, u1 = 176, 210
    o.poly([(u1, -18, 0), (u1, 20, 0), (u1, 20, 116), (u1, -18, 116)], 'sh')
    o.poly([(u0, -18, 128), (u1, -18, 116), (u1, 20, 116), (u0, 20, 128)], 'p')
    top = [(u0, -18, 130), (u0 + 5, -18, 130), (u0 + 5, -18, 126), (u0 + 13, -18, 126), (u0 + 13, -18, 121), (u0 + 22, -18, 121),
           (u0 + 22, -18, 117), (u1, -18, 117)]
    o.poly([(u0, -18, 0), (u1, -18, 0)] + top[::-1], 'p')
    o.lines([[(u0, -18, z), (u1, -18, z)] for z in (34, 82)], 'n')
    parch(o, u0 + 9, -18, 44, 6, 26)
    parch(o, u0 + 19, -18, 44, 6, 26)
    parch(o, u0 + 12, -18, 90, 10, 22)
    # the west portal in the tower's west face
    px0, py0 = o.p(u1, -6, 0)
    px1, py1 = o.p(u1, 10, 0)
    o.raw(path('M%s,%sL%s,%sL%s,%sQ%s,%s %s,%sZ' % (f(px0), f(py0), f(px1), f(py1), f(px1), f(py1 - 22), f((px0 + px1) / 2 + 2), f(py1 - 36),
                                                   f(px0), f(py0 - 22)), 'k'))
    return o.svg(), o


def lodge(x, y, tower_xy):
    """The masons' lodge: a timber-framed shed, a wheel crane and stone blocks in the yard, and scaffolding
    and the great crane on the cathedral's unfinished tower (tower_xy: that tower's near face, left foot)."""
    o = O(x, y)
    # scaffolding against the tower (drawn here so it sits in front of the cathedral)
    tx, ty = tower_xy
    t = O(tx, ty)
    sc = ''
    for u in (-2, 12, 24, 36):
        sc += Ml(t.P([(u, -20, 60), (u, -20, 132)]))
    for z in (70, 86, 102, 118):
        sc += Ml(t.P([(-3, -20, z), (37, -20, z)]))
    sc += Ml(t.P([(-2, -20, 70), (12, -20, 86)])) + Ml(t.P([(24, -20, 102), (36, -20, 118)]))
    o.raw(path(sc, 'n'))
    # the great crane on the tower top: a small housed treadwheel and a slanting jib
    cx0, cy0 = t.p(8, 0, 122)
    o.raw(path(Mz([(cx0, cy0), (cx0 + 14, cy0), (cx0 + 14, cy0 - 12), (cx0 + 7, cy0 - 18), (cx0, cy0 - 12)]), 'p'))
    o.raw(path('M%s,%sh14' % (f(cx0), f(cy0 - 5)), 'h'))
    o.raw(path('M%s,%sL%s,%sM%s,%sv14' % (f(cx0 + 7), f(cy0 - 14), f(cx0 - 26), f(cy0 - 34), f(cx0 - 26), f(cy0 - 34)), 'n'))
    o.raw(path('M%s,%sh4v3h-4Z' % (f(cx0 - 28), f(cy0 - 20)), 'k'))
    # the lodge itself: half-timbered, roof along u
    L0, L1, D1 = 0, 46, 22
    box(o, L0, L1, 0, D1, 18)
    roof_u(o, L0, L1, 0, D1, 18, 14, 'rr', n=7)
    tim = ''
    for u in (0, 11.5, 23, 34.5, 46):
        tim += Ml(o.P([(u, 0, 0), (u, 0, 18)]))
    tim += Ml(o.P([(0, 0, 9), (46, 0, 9)]))
    for u in (0, 23):
        tim += Ml(o.P([(u, 0, 9), (u + 11.5, 0, 18)])) + Ml(o.P([(u + 23, 0, 9), (u + 11.5, 0, 18)]))
    o.raw(path(tim, 'n'))
    rarch(o, 14, 0, 0, 7, 7.5)
    rarch(o, 26, 0, 0, 7, 7.5)
    # a timber yard crane: mast, jib, rope and a block in the sling
    m = O(x + 62, y + 4)
    m.lines([[(0, 0, 0), (0, 0, 40)], [(0, 0, 38), (-16, 0, 26)], [(0, 0, 40), (22, 0, 48)], [(22, 0, 48), (22, 0, 30)], [(-5, 0, 0), (0, 0, 12)],
             [(5, 0, 0), (0, 0, 12)]], 'n')
    m.poly([(19, 0, 24), (25, 0, 24), (25, 0, 29), (19, 0, 29)], 'p')
    # a stack of cut stone
    s = O(x + 50, y + 14)
    for (u, d, z) in ((0, 0, 0), (9, 0, 0), (4, 0, 5), (18, 2, 0)):
        box(s, u, u + 8, d, d + 6, 5, z)
        s.poly([(u, d, z + 5), (u + 8, d, z + 5), (u + 8, d + 6, z + 5), (u, d + 6, z + 5)], 'p')
    return o.svg() + m.svg() + s.svg()


def guildhall(x, y):
    o = O(x, y)
    U, D, h, r = 150, 40, 56, 46
    # right end: a stepped gable
    st = [(U, 0, 0), (U, D, 0), (U, D, h)]
    steps = 5
    for i in range(steps):
        d0 = D - D / 2 * i / steps
        d1 = D - D / 2 * (i + 1) / steps
        z0 = h + r * i / steps
        z1 = h + r * (i + 1) / steps
        st += [(U, d0, z1 + 3), (U, d1, z1 + 3)]
    for i in range(steps - 1, -1, -1):
        d0 = D / 2 * i / steps
        d1 = D / 2 * (i + 1) / steps
        z1 = h + r * (i + 1) / steps
        st += [(U, d1, z1 + 3), (U, d0, z1 + 3)]
    st += [(U, 0, h)]
    o.poly(st, 'sh')
    roof_u(o, 0, U, 0, D, h, r, 'rr', n=0, gable='sh')
    o.lines([[(u, 0, h), (u, D / 2, h + r)] for u in range(6, U, 6)], 'h')
    # dormers
    for u in (28, 68, 108):
        dz = h + 12
        o.poly([(u, 4, dz - 6), (u + 12, 4, dz - 6), (u + 12, 4, dz + 6), (u + 6, 4, dz + 13), (u, 4, dz + 6)], 'p')
        rect_k(o, u + 4, 4, dz - 4, 4, 6)
    # front: arcade below, windows above
    o.poly([(0, 0, 0), (U, 0, 0), (U, 0, h), (0, 0, h)], 'p')
    o.lines([[(0, 0, 28), (U, 0, 28)], [(0, 0, h - 3), (U, 0, h - 3)]], 'n')
    for i in range(6):
        u = 7 + i * 23.2
        rarch(o, u, 0, 0, 16, 22, 'sh')
        rect_k(o, u + 4.5, 0, 33, 7, 16, 'k')
        o.raw(path(Ml(o.P([(u + 8, 0, 33), (u + 8, 0, 49)])) + Ml(o.P([(u + 4.5, 0, 42), (u + 11.5, 0, 42)])), 'wl'))
    # clock turret on the ridge
    c = O(*o.p(U / 2 - 9, D / 2 - 6, h + r - 6))
    box(c, 0, 18, 0, 12, 30)
    cx, cy = c.p(9, 0, 18)
    cl = circ(cx, cy, 6.5)
    for i in range(12):
        a = i * math.pi / 6
        cl += 'M%s,%sL%s,%s' % (f(cx + 5 * math.cos(a)), f(cy + 5 * math.sin(a)), f(cx + 6.5 * math.cos(a)), f(cy + 6.5 * math.sin(a)))
    o.raw(c.svg() + path(cl, 'p') + path('M%s,%sl0,-4.2M%s,%sl3,1.6' % (f(cx), f(cy), f(cx), f(cy)), 'n'))
    lx, ly = c.p(9, 6, 30)
    o.raw(path(Mz([(lx - 8, ly), (lx - 8, ly - 12), (lx + 8, ly - 12), (lx + 8, ly)]), 'p'))
    o.raw(path('M%s,%sv-9M%s,%sv-9M%s,%sv-9' % (f(lx - 3.5), f(ly - 1), f(lx), f(ly - 1), f(lx + 3.5), f(ly - 1)), 'n'))
    o.raw(path(Mz([(lx - 9.5, ly - 12), (lx, ly - 40), (lx + 9.5, ly - 12)]), 'rg'))
    o.raw(path('M%s,%sv-8l7,2.4l-7,2.4' % (f(lx), f(ly - 40)), 'n'))
    return o.svg()


def market_cross(x, y):
    o = []
    for i, (rx, hh) in enumerate(((17, 4), (12.5, 4), (8, 4))):
        cy = y - 4 * i
        ry = rx * 0.45
        near = ell(x, cy, rx, ry, math.pi, 0, 10)
        o.append(path(Mz([(px, py - hh) for px, py in near[::-1]] + near), 'sh'))
        o.append(path(Mz(ell(x, cy - hh, rx, ry, 0, 2 * math.pi, 16)), 'p'))
    top = y - 12
    o.append(path(Mz([(x - 1.8, top), (x - 1.8, top - 40), (x + 1.8, top - 40), (x + 1.8, top)]), 'p'))
    t = top - 40
    o.append(path(Mz([(x - 5, t), (x - 5, t - 8), (x + 5, t - 8), (x + 5, t)]), 'p'))
    o.append(path(Mz([(x - 6, t - 8), (x, t - 16), (x + 6, t - 8)]), 'rr'))
    o.append(path('M%s,%sv-9M%s,%sh7' % (f(x), f(t - 16), f(x - 3.5), f(t - 22)), 'n'))
    o.append(path('M%s,%sv-5h2v5Z' % (f(x - 1), f(t - 1)), 'k'))
    return ''.join(o)


def stall(x, y, rnd):
    o = O(x, y)
    box(o, 0, 14, 0, 8, 5)
    o.lines([[(0, 0, 5), (0, 0, 10)], [(14, 0, 5), (14, 0, 10)]], 'n')
    q = [(-1.5, -2, 9), (15.5, -2, 9), (15.5, 9, 13), (-1.5, 9, 13)]
    o.poly(q, 'p')
    st = ''
    for i in range(0, 6, 2):
        a = -1.5 + 17 * i / 6
        b = -1.5 + 17 * (i + 1) / 6
        st += Mz(o.P([(a, -2, 9), (b, -2, 9), (b, 9, 13), (a, 9, 13)]))
    o.raw(path(st, 'rr'))
    return o.svg()


def castle(x, y, rnd):
    """The castle on its hill: hachured slope, curtain wall with round towers, the keep and the great hall
    where the assize sits."""
    o = O(x, y)
    hz = 30          # hill height
    cx = x + 120
    rcx, rcy, rrx, rry = cx + 6, y + 2 - hz, 112, 34
    rimf = ell(rcx, rcy, rrx, rry, math.pi, 2 * math.pi, 24)          # far rim, left to right over the top
    rimn = ell(rcx, rcy, rrx, rry, 0, math.pi, 24)                    # near rim, right to left
    near = ell(cx, y + 6, 150, 40, 0, math.pi, 30)                    # foot of the hill, right to left
    o.raw(path(Mz(rimf + near), 'p hill'))
    o.raw(path(Ml(rimf), 'n') + path(Ml(rimn), 'n'))
    rnd2 = random.Random(7)
    ha = ''
    for i in range(1, 64):
        t = i / 64
        a = math.pi * t
        px, py = rcx + rrx * math.cos(a), rcy + rry * math.sin(a)
        bx, by_ = cx + 150 * math.cos(a), y + 6 + 40 * math.sin(a)
        L = rnd2.uniform(0.3, 0.75) if 0.2 < t < 0.8 else rnd2.uniform(0.55, 0.95)
        ha += 'M%s,%sL%s,%s' % (f(px), f(py + 1), f(px + (bx - px) * L), f(py + (by_ - py) * L))
    for side in (-1, 1):
        for k in range(5):
            t = k / 5
            px, py = rcx + side * rrx * (1 - 0.02 * k), rcy - 4 + 8 * t
            ha += 'M%s,%sl%s,%s' % (f(px), f(py), f(side * rnd2.uniform(10, 22)), f(rnd2.uniform(8, 14)))
    o.raw(path(ha, 'h'))
    o.raw(path(Ml(near), 'n'))
    # the ramp road up to the gate
    o.raw(path(Mz([(cx - 20, y + 2), (cx - 6, y + 2), (cx + 14, y + 46), (cx - 4, y + 46)]), 'st0'))
    p0 = O(rcx, rcy)
    N = 40
    ring = [(92 * math.cos(2 * math.pi * i / N), 44 * math.sin(2 * math.pi * i / N)) for i in range(N + 1)]   # i in 0..20 far, 20..40 near
    hw = 20

    def wall(i0, i1):
        for i in range(i0, i1):
            (ua, da), (ub, db) = ring[i], ring[i + 1]
            p0.poly([(ua, da, 0), (ub, db, 0), (ub, db, hw), (ua, da, hw)], 'sh' if (i0 == 0) else 'p')
            mx, my = p0.p((ua + ub) / 2, (da + db) / 2, hw)
            p0.raw(path('M%s,%sh2.4v-2.6h-2.4Z' % (f(mx - 1.2), f(my)), 'p'))

    wall(0, 20)
    for i in (6, 14):
        u, d = ring[i]
        cyl(p0, u, d, 0, 8, 30, 'cone', 16)
    o.raw(p0.svg())
    p0.o = []
    # the keep
    k = O(*p0.p(-62, -6, 0))
    box(k, 0, 38, 0, 34, 112)
    k.lines([[(0, 0, z), (38, 0, z)] for z in (36, 74)], 'n')
    for z in (14, 48, 84):
        rarch(k, 9, 0, z, 4, 9)
        rarch(k, 24, 0, z, 4, 9)
    k.poly([(0, 0, 112), (38, 0, 112), (38, 34, 112), (0, 34, 112)], 'p')
    merlons(k, 0, 38, 0, 112)
    for (u, d) in ((0, 34), (38, 34), (0, 0), (38, 0)):
        cyl(k, u, d, 108, 4.6, 12, 'cone', 12)
    fx, fy = k.p(19, 17, 112)
    k.raw(path('M%s,%sv-26' % (f(fx), f(fy)), 'n'))
    k.raw(path('M%s,%sq9,2 17,-1q-8,5 -17,7Z' % (f(fx), f(fy - 26)), 'rr'))
    o.raw(k.svg())
    # the great hall (assize hall): tall windows, steep roof, a louvre
    g = O(*p0.p(-12, 4, 0))
    box(g, 0, 80, 0, 28, 36)
    roof_u(g, 0, 80, 0, 28, 36, 34, 'rr', n=12)
    for u in (8, 24, 40, 56):
        parch(g, u, 0, 9, 7, 22)
    lx, ly = g.p(40, 14, 70)
    g.raw(path(Mz([(lx - 4, ly), (lx - 4, ly - 7), (lx, ly - 12), (lx + 4, ly - 7), (lx + 4, ly)]), 'p'))
    rarch(g, 68, 0, 0, 6, 10)
    o.raw(g.svg())
    # near half of the curtain wall, its towers and the gatehouse
    wall(20, 40)
    for i in (25, 35):
        u, d = ring[i]
        cyl(p0, u, d, 0, 9, 32, 'cren', 0)
    o.raw(p0.svg())
    p0.o = []
    gu, gd = ring[30]
    gh = O(*p0.p(gu - 12, gd - 2, 0))
    box(gh, 0, 24, 0, 12, 30)
    merlons(gh, 0, 24, 0, 30)
    rarch(gh, 7, 0, 0, 10, 15)
    o.raw(gh.svg())
    return o.svg()


def college(x, y):
    """Scriptorium and college: four ranges round a cloister garth, with the library tower."""
    o = O(x, y)
    U, D = 120, 86
    # back range (the scriptorium, its windows facing the garth)
    box(o, 0, U, D - 20, D, 30)
    roof_u(o, 0, U, D - 20, D, 30, 22, 'rr', n=14)
    for u in range(8, U - 6, 13):
        rarch(o, u, D - 20, 14, 3.4, 9)
        rarch(o, u + 4.4, D - 20, 14, 3.4, 9)
    arc = ''
    for u in range(22, 100, 7):
        x0, y0 = o.p(u, D - 20, 0)
        arc += 'M%s,%sv-5a2.6,2.6 0 0 1 5.2,0v5' % (f(x0), f(y0))
    o.raw(path(arc, 'n'))
    # bell-cote on the back range
    bx, by = o.p(30, D - 10, 52)
    o.raw(path(Mz([(bx - 4, by + 2), (bx - 4, by - 10), (bx, by - 15), (bx + 4, by - 10), (bx + 4, by + 2)]), 'p') + path('M%s,%sv-3.4a1.6,1.6 0 0 1 3.2,0v3.4Z' % (f(bx - 1.6), f(by - 3)), 'k'))
    # left range: its right face looks onto the garth
    o.poly([(20, 0, 0), (20, D - 20, 0), (20, D - 20, 26), (20, 0, 26)], 'sh')
    o.poly([(0, 0, 26), (10, 0, 44), (10, D - 20, 44), (0, D - 20, 26)], 'rr')
    o.poly([(20, 0, 26), (20, D - 20, 26), (10, D - 20, 44), (10, 0, 44)], 'rr')
    o.lines(hatch3((10, 0, 44), (10, D - 20, 44), (20, 0, 26), (20, D - 20, 26), 5, 0.12, 0.88), 'h')
    # garth
    o.poly([(20, 14, 0), (100, 14, 0), (100, D - 20, 0), (20, D - 20, 0)], 'gd')
    wx, wy = o.p(60, 40, 0)
    o.raw(tree(wx, wy, 5, None))
    # right range
    o.poly([(U, 0, 0), (U, D - 20, 0), (U, D - 20, 26), (U, 0, 26)], 'sh')
    o.poly([(100, 0, 26), (110, 0, 44), (110, D - 20, 44), (100, D - 20, 26)], 'rr')
    o.poly([(U, 0, 26), (U, D - 20, 26), (110, D - 20, 44), (110, 0, 44)], 'rr')
    o.lines(hatch3((110, 0, 44), (110, D - 20, 44), (U, 0, 26), (U, D - 20, 26), 5, 0.12, 0.88), 'h')
    o.poly([(100, 0, 0), (100, 0, 26), (100, 14, 26), (100, 14, 0)], 'p')
    # front range: a low cloister walk with an open arcade
    box(o, 0, U, 0, 14, 16)
    o.poly([(0, 0, 16), (U, 0, 16), (U, 14, 24), (0, 14, 24)], 'rr')
    o.lines([[(u, 0, 16), (u, 14, 24)] for u in range(4, U, 5)], 'h')
    arc = ''
    for u in range(6, U - 4, 9):
        x0, y0 = o.p(u, 0, 0)
        arc += 'M%s,%sv-7a3.4,3.4 0 0 1 6.8,0v7Z' % (f(x0), f(y0))
    o.raw(path(arc, 'k'))
    # the library tower at the front right corner
    t = O(*o.p(U - 6, -10, 0))
    box(t, 0, 30, 0, 28, 104)
    t.lines([[(0, 0, z), (30, 0, z)] for z in (26, 52, 78)], 'n')
    for z in (8, 32, 58, 84):
        for u in (5, 13, 21):
            rect_k(t, u, 0, z, 3.6, 9)
    px, py = t.p(15, 14, 104)
    t.raw(path(Mz([t.p(0, 0, 104), t.p(30, 0, 104), (px, py - 40)]), 'rr'))
    t.raw(path(Mz([t.p(30, 0, 104), t.p(30, 28, 104), (px, py - 40)]), 'sh'))
    t.raw(path(''.join(Ml([lerp(t.p(30 * k, 0, 104), (px, py - 40), 0.0), (px, py - 40)]) for k in (0.25, 0.5, 0.75)), 'h'))
    t.raw(path('M%s,%sv-8m-3,2.4h6' % (f(px), f(py - 40)), 'n'))
    o.raw(t.svg())
    return o.svg()


def mint(x, y):
    o = O(x, y)
    # a lean-to workshop on the right
    box(o, 52, 70, 0, 22, 16)
    o.poly([(52, 0, 16), (70, 0, 16), (70, 22, 24), (52, 22, 24)], 'rr')
    box(o, 0, 52, 0, 28, 28)
    roof_u(o, 0, 52, 0, 28, 28, 22, 'rr', n=8)
    # chimney stack and smoke
    c = O(*o.p(38, 10, 36))
    box(c, 0, 8, 0, 6, 42)
    c.poly([(0, 0, 42), (8, 0, 42), (8, 6, 42), (0, 6, 42)], 'p')
    sx, sy = c.p(4, 3, 42)
    sm = ''
    for i, (a, b) in enumerate(((0, 0), (6, -8), (14, -12))):
        sm += 'M%s,%sc4,-4 -3,-7 1,-12c3,-4 9,-2 8,-8' % (f(sx + a), f(sy + b - 3))
    o.raw(c.svg() + path(sm, 'n'))
    rarch(o, 20, 0, 0, 10, 15)
    rect_k(o, 6, 0, 16, 5, 6)
    rect_k(o, 38, 0, 16, 5, 6)
    # the sign: a bracket and a struck coin
    bx, by = o.p(0, 0, 22)
    o.raw(path('M%s,%sh-12M%s,%sv3' % (f(bx), f(by), f(bx - 9), f(by)), 'n'))
    o.raw(path(circ(bx - 9, by + 9, 6), 'ro') + path(circ(bx - 9, by + 9, 4) + 'M%s,%sv6M%s,%sh6' % (f(bx - 9), f(by + 6), f(bx - 12), f(by + 9)), 'n'))
    # anvil on its block by the door
    ax, ay = o.p(34, -6, 0)
    o.raw(path('M%s,%sh6v-5h-6Z' % (f(ax), f(ay)), 'p') + path('M%s,%sh12l-3,-2.6h-9l-1,1.4Z' % (f(ax - 3), f(ay - 5)), 'k'))
    return o.svg()


def harbour(x, y):
    """The quay on the river with the treadwheel crane, the harbour master's house and a ship at anchor."""
    o = O(x, y)
    # quay wall along the bank
    o.poly([(0, 0, 0), (170, 0, 0), (170, 0, 9), (0, 0, 9)], 'sh')
    o.poly([(0, 0, 9), (170, 0, 9), (170, 18, 9), (0, 18, 9)], 'p')
    o.lines([[(u, 0, 0), (u, 0, 9)] for u in range(10, 170, 12)], 'h')
    po = ''
    for u in (20, 60, 100, 140):
        px, py = o.p(u, 2, 9)
        po += 'M%s,%sv-5' % (f(px), f(py))
    o.raw(path(po, 'n'))
    # the harbour master's house
    hm = O(*o.p(110, 8, 9))
    box(hm, 0, 30, 0, 18, 18)
    roof_u(hm, 0, 30, 0, 18, 18, 14, 'rr', n=5)
    rarch(hm, 12, 0, 0, 5, 7)
    rect_k(hm, 4, 0, 10, 3, 4)
    rect_k(hm, 22, 0, 10, 3, 4)
    lx, ly = hm.p(30, 0, 14)
    hm.raw(path('M%s,%sh5v3' % (f(lx), f(ly)), 'n') + path('M%s,%sh3v4h-3Z' % (f(lx + 3.5), f(ly + 7)), 'ro'))
    o.raw(hm.svg())
    # the treadwheel crane
    cr = O(*o.p(36, 6, 9))
    box(cr, 0, 22, 0, 18, 16)
    cr.poly([(0, 0, 16), (22, 0, 16), (11, 9, 30)], 'rr')
    cr.poly([(22, 0, 16), (22, 18, 16), (11, 9, 30)], 'sh')
    cx, cy = cr.p(11, 9, 30)
    wx, wy = cr.p(11, 0, 8)
    cr.raw(path(circ(wx, wy, 6) + 'M%s,%sh12M%s,%sv12' % (f(wx - 6), f(wy), f(wx), f(wy - 6)), 'n'))
    cr.raw(path('M%s,%sL%s,%sv18' % (f(cx), f(cy), f(cx - 34), f(cy - 16)), 'n'))
    cr.raw(path('M%s,%sh5v5h-5Z' % (f(cx - 36.5), f(cy + 2)), 'k'))
    o.raw(cr.svg())
    return o.svg()


def ship(x, y):
    """A cog at anchor: clinker hull, castles fore and aft, one mast with a striped square sail."""
    o = []
    hull = 'M%s,%sQ%s,%s %s,%sL%s,%sQ%s,%s %s,%sZ' % (
        f(x - 34), f(y - 14), f(x - 30), f(y + 2), f(x - 14), f(y + 4), f(x + 18), f(y + 4), f(x + 34), f(y + 2), f(x + 38), f(y - 16))
    o.append(path(hull, 'p'))
    o.append(path('M%s,%sQ%s,%s %s,%sM%s,%sQ%s,%s %s,%s' % (f(x - 32), f(y - 8), f(x + 2), f(y - 2), f(x + 36), f(y - 9),
                                                         f(x - 31), f(y - 3), f(x + 2), f(y + 2), f(x + 35), f(y - 4)), 'h'))
    o.append(path(Mz([(x + 18, y - 9), (x + 38, y - 16), (x + 38, y - 26), (x + 18, y - 22)]), 'p'))
    o.append(path(Mz([(x - 34, y - 14), (x - 22, y - 11), (x - 22, y - 20), (x - 33, y - 22)]), 'p'))
    o.append(path('M%s,%sv-56' % (f(x + 2), f(y - 6)), 'n'))
    sail = [(x - 13, y - 52), (x + 17, y - 52), (x + 19, y - 22), (x - 15, y - 22)]
    o.append(path(Mz(sail), 'p'))
    st = ''
    for i in (0, 2, 4):
        a, b = i / 6, (i + 1) / 6
        st += Mz([lerp(sail[0], sail[1], a), lerp(sail[0], sail[1], b), lerp(sail[3], sail[2], b), lerp(sail[3], sail[2], a)])
    o.append(path(st, 'rr'))
    o.append(path('M%s,%sL%s,%sM%s,%sL%s,%s' % (f(x + 2), f(y - 62), f(x - 34), f(y - 20), f(x + 2), f(y - 62), f(x + 38), f(y - 24)), 'h'))
    o.append(path('M%s,%sl12,3l-12,3' % (f(x + 2), f(y - 62)), 'rr'))
    return ''.join(o)


def boat(x, y, s=1.0):
    return (path('M%s,%sq%s,%s %s,0l%s,-%sZ' % (f(x - 9 * s), f(y - 3 * s), f(3 * s), f(5 * s), f(16 * s), f(3 * s), f(3 * s)), 'p')
            + path('M%s,%sv-%s' % (f(x), f(y - 2 * s), f(12 * s)), 'n') + path(Mz([(x + 0.6 * s, y - 13 * s), (x + 7 * s, y - 5 * s), (x + 0.6 * s, y - 4 * s)]), 'p'))


def gatehouse(x, y):
    o = O(x - 17, y)
    cyl(o, -4, 12, 0, 10, 46, 'cone', 20)
    box(o, 0, 34, 0, 22, 38)
    o.poly([(0, 0, 38), (34, 0, 38), (34, 22, 38), (0, 22, 38)], 'p')
    merlons(o, 0, 34, 0, 38)
    rarch(o, 9, 0, 0, 16, 24)
    x0, y0 = o.p(9, 0, 0)
    o.raw(path('M%s,%sv-15M%s,%sv-19M%s,%sv-15M%s,%sh16M%s,%sh16' % (f(x0 + 4), f(y0), f(x0 + 8), f(y0), f(x0 + 12), f(y0), f(x0), f(y0 - 8),
                                                                    f(x0), f(y0 - 14)), 'wl'))
    rect_k(o, 15, 0, 28, 4, 5)
    o.lines([[(0, 0, 30), (34, 0, 30)]], 'h')
    cyl(o, 38, 12, 0, 10, 46, 'cone', 20)
    return o.svg()


def bridge(x0, y0, length, rnd):
    """A stone bridge running back across the river; its right-hand face shows the arches and cutwaters."""
    o = O(x0, y0)
    L, Wd, z = length, 15, 14
    n = 5
    # cutwaters standing out from the face, under the deck
    cw = ''
    for i in range(1, n):
        d = L * i / n
        cw += Mz(o.P([(Wd, d - 3, 0), (Wd + 7, d, 0), (Wd, d + 3, 0), (Wd, d + 3, z - 4), (Wd + 5, d, z - 3), (Wd, d - 3, z - 4)]))
    o.poly([(Wd, 0, 0), (Wd, L, 0), (Wd, L, z), (Wd, 0, z)], 'sh')
    ar = ''
    for i in range(n):
        d0 = L * (i + 0.14) / n
        d1 = L * (i + 0.86) / n
        q = [(Wd, d0 + (d1 - d0) * t, 9.5 * math.sin(math.pi * t) ** 0.8) for t in [k / 10 for k in range(11)]]
        ar += Mz(o.P(q))
    o.raw(path(ar, 'ka'))
    o.raw(path(cw, 'p'))
    o.poly([(0, 0, z), (Wd, 0, z), (Wd, L, z), (0, L, z)], 'p')
    o.lines([[(0, 0, z + 3), (0, L, z + 3)], [(Wd, 0, z + 3), (Wd, L, z + 3)], [(0, 0, z), (0, 0, z + 3)], [(Wd, 0, z), (Wd, 0, z + 3)]], 'n')
    o.lines([[(Wd * 0.5, d, z), (Wd * 0.5, d + 6, z)] for d in range(8, int(L) - 8, 14)], 'h')
    # a small chapel at mid-span
    t = O(*o.p(0, L * 0.5 - 6, z))
    box(t, 0, 12, 0, 10, 14)
    t.poly([(0, 0, 14), (12, 0, 14), (6, 5, 26)], 'rr')
    t.poly([(12, 0, 14), (12, 10, 14), (6, 5, 26)], 'sh')
    rarch(t, 4, 0, 0, 4, 6)
    o.raw(t.svg())
    return o.svg()


def old_town(x, y, rnd):
    """The earlier wall line, ruined: its foundations as a broken dashed line in the grass, a few lengths of
    wall still standing, a fallen tower with its stones lying about, and the old gate arch on its own."""
    o = []
    seg = [(-26, 262), (-12, 196), (8, 136), (38, 84), (80, 42), (130, 14), (190, 0)]
    pl = [(x + a, y + b) for a, b in spline(seg, False, 4)]
    inner = [(px + 7, py + 5) for px, py in pl]
    o.append(path(Ml(pl), 'dash') + path(Ml(inner), 'dash'))
    n = len(pl)

    def wall_piece(i0, i1, hmax):
        seg_ = pl[i0:i1 + 1]
        hs = [hmax * (0.55 + 0.45 * abs(math.sin(k * 1.9 + i0))) for k in range(len(seg_))]
        hs[0] *= 0.5
        hs[-1] *= 0.45
        face = seg_ + [(px, py - hh) for (px, py), hh in zip(seg_[::-1], hs[::-1])]
        top = [(px, py - hh) for (px, py), hh in zip(seg_, hs)] + [(px + DX * 8, py - hh - DY * 8) for (px, py), hh in zip(seg_[::-1], hs[::-1])]
        o.append(path(Mz(top), 'p') + path(Mz(face), 'sh'))
        o.append(path(''.join(Ml([(px, py - 1), (px, py - hh + 1.5)]) for (px, py), hh in list(zip(seg_, hs))[1:-1:2]), 'h'))

    wall_piece(int(n * 0.06), int(n * 0.16), 15)
    wall_piece(int(n * 0.44), int(n * 0.55), 17)
    wall_piece(int(n * 0.80), int(n * 0.93), 14)

    def stump(tx, ty, r, hh):
        jag = [(tx + r, ty - hh * 0.62), (tx + r * 0.55, ty - hh * 0.8), (tx + r * 0.2, ty - hh * 0.58), (tx - r * 0.15, ty - hh),
               (tx - r * 0.55, ty - hh * 0.74), (tx - r, ty - hh * 0.88)]
        o.append(path(Mz(ell(tx, ty, r, r * 0.5, math.pi, 0, 10) + jag), 'p'))
        o.append(path(''.join(Ml([(tx + r * k, ty + r * 0.5 * math.sqrt(1 - k * k) - 0.5), (tx + r * k, ty - hh * (0.6 - 0.1 * k))]) for k in (0.4, 0.62, 0.82)), 'h'))
        o.append(path(Mz([(tx - 2.5, ty - hh * 0.5), (tx + 1.5, ty - hh * 0.5), (tx + 1.5, ty - hh * 0.34), (tx - 2.5, ty - hh * 0.34)]), 'k'))
        bl = ''
        for (bx, by, a) in ((r + 7, 5, 0.3), (r + 15, 10, -0.4), (r + 3, 12, 0.9), (r + 22, 4, 0.2)):
            c, s_ = math.cos(a), math.sin(a)
            bl += Mz([(tx + bx + c * u - s_ * v, ty + by + s_ * u + c * v) for u, v in ((-4.5, -2.6), (4.5, -2.6), (4.5, 2.6), (-4.5, 2.6))])
        o.append(path(bl, 'p'))

    p1, p2 = pl[int(n * 0.3)], pl[int(n * 0.68)]
    stump(p1[0] + 3, p1[1] + 3, 14, 38)
    stump(p2[0] + 3, p2[1] + 3, 11, 28)
    # the old gate: an arch standing on its own, its wall gone
    g = O(x + 92, y + 120)
    g.poly([(36, 0, 0), (36, 14, 0), (36, 14, 30), (36, 0, 34)], 'sh')
    g.poly([(0, 0, 0), (36, 0, 0), (36, 0, 34), (30, 0, 38), (24, 0, 35), (15, 0, 41), (8, 0, 37), (0, 0, 39)], 'p')
    rarch(g, 9, 0, 0, 18, 26, 'k')
    g.lines([[(0, 0, 12), (9, 0, 12)], [(27, 0, 12), (36, 0, 12)], [(0, 0, 25), (36, 0, 25)]], 'h')
    o.append(g.svg())
    # a roofless house
    hh = O(x + 150, y + 70)
    hh.poly([(20, 0, 0), (20, 12, 0), (20, 12, 9), (20, 0, 11)], 'sh')
    hh.poly([(0, 0, 0), (20, 0, 0), (20, 0, 11), (14, 0, 17), (10, 0, 14), (6, 0, 19), (0, 0, 12)], 'p')
    rarch(hh, 7, 0, 4, 5, 7, 'k')
    o.append(hh.svg())
    tufts = ''
    for (a, b) in ((10, 96), (60, 108), (110, 64), (-6, 176), (70, 30), (140, 34), (30, 214), (160, 110), (44, 150), (120, 170), (180, 60), (90, 200)):
        tufts += 'M%s,%sl-2,-4M%s,%sl0,-5M%s,%sl2,-4' % (f(x + a), f(y + b), f(x + a + 2), f(y + b), f(x + a + 4), f(y + b))
    o.append(path(tufts, 'h'))
    return ''.join(o)


def wind_rose(cx, cy, R):
    o = []
    o.append(path(circ(cx, cy, R * 0.9) + circ(cx, cy, R * 0.84), 'n'))
    tk = ''
    for i in range(32):
        a = i * math.pi / 16
        r0 = R * (0.84 if i % 2 else 0.8)
        tk += 'M%s,%sL%s,%s' % (f(cx + r0 * math.cos(a)), f(cy + r0 * math.sin(a)), f(cx + R * 0.9 * math.cos(a)), f(cy + R * 0.9 * math.sin(a)))
    o.append(path(tk, 'h'))
    for ring, Ln, wdt, off in ((1, R * 0.62, R * 0.08, math.pi / 8), (0, R * 0.78, R * 0.12, math.pi / 4), (0, R, R * 0.14, 0)):
        for i in range(8 if ring else 4 if off == 0 else 4):
            a = off + i * (math.pi / 4 if ring else math.pi / 2)
            tip = (cx + Ln * math.cos(a), cy + Ln * math.sin(a))
            l = (cx + wdt * math.cos(a - math.pi / 2), cy + wdt * math.sin(a - math.pi / 2))
            r = (cx + wdt * math.cos(a + math.pi / 2), cy + wdt * math.sin(a + math.pi / 2))
            o.append(path(Mz([(cx, cy), l, tip]), 'p'))
            o.append(path(Mz([(cx, cy), r, tip]), 'k'))
    o.append(path(circ(cx, cy, R * 0.07), 'p'))
    return ''.join(o)


def fleur(x, y, s):
    """A small fleur-de-lis pointing down (the rose marks Septentrio at the foot of the map)."""
    d = ('M{x},{y}c-1.5,4 -1.5,8 0,12c1.5,-4 1.5,-8 0,-12z'
         'M{x},{y2}c-3,-1 -6,1 -6.5,4c-.3,2 1.5,3 2.5,2c-1,-1 -.6,-2.6 .8,-3c1.5,-.4 2.6,.6 3.2,1.6'
         'M{x},{y2}c3,-1 6,1 6.5,4c.3,2 -1.5,3 -2.5,2c1,-1 .6,-2.6 -.8,-3c-1.5,-.4 -2.6,.6 -3.2,1.6'
         'M{a},{y3}h7').format(x=f(x), y=f(y), y2=f(y + 4), y3=f(y + 3), a=f(x - 3.5))
    return path(d, 'n fl')


# ------------------------------------------------------------------ the map
def build(links, seed=1575):
    """links: key -> dict(href, label, name, sub). Returns (svg, meta) where meta lists each building's
    key, centre and box in map units, in the order of the phone walk."""
    rnd = random.Random(seed)
    ground, sorted_items, labels, defs = [], [], [], []

    PREC[0] = 0
    # ---- river along the top (Meridies), city bank below
    def ybank(x):
        return 232 + 7 * math.sin(x / 210.0) + 4 * math.sin(x / 77.0)

    def yfar(x):
        return 98 + 16 * math.sin(x / 330.0 + 1.1) + 5 * math.sin(x / 120.0)

    xs = list(range(0, W + 1, 10))
    bank = [(x, ybank(x)) for x in xs]
    far = [(x, yfar(x)) for x in xs]
    ground.append(path(Mz(far + bank[::-1]), 'wt'))
    ground.append(path(Ml(wob(far, rnd, 0.4)), 'n') + path(Ml(wob(bank, rnd, 0.4)), 'n'))
    rip = ''
    for i in range(260):
        x = rnd.uniform(20, W - 20)
        yt, yb = yfar(x) + 6, ybank(x) - 6
        y = rnd.uniform(yt, yb)
        L = rnd.uniform(5, 16)
        rip += 'M%s,%sh%s' % (f(x), f(y), f(L))
    ground.append(path(rip, 'rp'))

    # ---- the wall ring (D-shaped, flat side along the river)
    ctrl = [(352, 244), (560, 246), (800, 247), (1040, 246), (1260, 244), (1448, 250),
            (1488, 340), (1480, 480), (1430, 630), (1330, 770), (1180, 868), (990, 918), (810, 928), (650, 905),
            (510, 838), (420, 728), (366, 588), (346, 440), (344, 320)]
    ring = spline(ctrl, True, 7)
    for i, (x, y) in enumerate(ring):
        if y < 262:
            ring[i] = (x, ybank(x) + 12)
    n = len(ring)
    arc = [0.0]
    for i in range(1, n + 1):
        arc.append(arc[-1] + math.dist(ring[i - 1], ring[i % n]))
    total = arc[-1]

    def nearest(pt):
        return min(range(n), key=lambda i: math.dist(ring[i], pt))

    gates = {'gate-l': nearest((346, 430)), 'gate-s': nearest((820, 928)), 'gate-r': nearest((1474, 540))}
    inner = offset(ring, 30)
    lane = offset(ring, 17)

    # ---- streets (centre lines in screen space) and the market square
    G = {k: ring[i] for k, i in gates.items()}
    sq = [(722, 714), (952, 710), (968, 790), (712, 794)]
    streets = [
        (spline([(404, 664), (450, 664), (530, 676), (630, 696), (716, 746)]), 9),
        (spline([(964, 752), (1060, 734), (1190, 708), (1320, 640), G['gate-r']]), 9),
        (spline([G['gate-s'], (818, 864), (828, 820), (838, 792)]), 9),
        (spline([(952, 712), (985, 612), (1000, 520), (1012, 380), (1020, 262)]), 7),
        (spline([(722, 714), (706, 640), (716, 560), (706, 500)]), 6),
        (spline([(706, 500), (600, 452), (480, 440), G['gate-l']]), 7),
        (spline([(630, 696), (618, 780), (610, 880)]), 6),
        (spline([(530, 676), (488, 740), (470, 830)]), 5),
        (spline([(1060, 734), (1090, 800), (1080, 880)]), 6),
        (spline([(1190, 708), (1262, 776), (1250, 840)]), 5),
        (spline([(1000, 520), (1120, 504), (1250, 474), (1380, 424), (1452, 384)]), 6),
        (spline([(1012, 380), (1140, 340), (1300, 312), (1430, 300)]), 5),
        (spline([(828, 820), (720, 842), (640, 832)]), 5),
        (spline([(840, 794), (960, 826), (1060, 846)]), 5),
        (spline([(1120, 504), (1128, 600), (1150, 706)]), 5),
        (spline([(870, 486), (880, 380), (860, 262)]), 5),
        (lane + lane[:1], 6),
    ]
    for pl, w in streets:
        ground.append('<path class="st" stroke-width="%s" d="%s"/>' % (w, Ml(pl)))
    ground.append(path(Mz(sq), 'sq'))

    # ---- roads outside the gates
    roads = [
        spline([G['gate-l'], (290, 440), (230, 444), (194, 437), (120, 452), (14, 472)]),
        spline([G['gate-s'], (822, 960), (830, 1000)]),
        spline([G['gate-r'], (1530, 548), (1600, 560)]),
        spline([(0, 60), (300, 70), (650, 64), (900, 58), (1200, 66), (1600, 56)]),
    ]
    for rd in roads:
        ground.append('<path class="st" stroke-width="8" d="%s"/>' % Ml(rd))

    PREC[0] = 1
    # ---- placement grid
    CS = 4
    GW, GH = W // CS + 1, H // CS + 1
    INF = 999.0
    clear = [[INF] * GW for _ in range(GH)]
    for pl, w in streets + [(sq + sq[:1], 2)]:
        for (ax, ay), (bx, by) in zip(pl[:-1], pl[1:]):
            R = w / 2 + 40
            for gy in range(max(0, int((min(ay, by) - R) / CS)), min(GH, int((max(ay, by) + R) / CS) + 1)):
                row = clear[gy]
                py = gy * CS + 2
                for gx in range(max(0, int((min(ax, bx) - R) / CS)), min(GW, int((max(ax, bx) + R) / CS) + 1)):
                    dd = dseg(gx * CS + 2, py, ax, ay, bx, by) - w / 2
                    if dd < row[gx]:
                        row[gx] = dd
    # the square is open ground
    inside = [[False] * GW for _ in range(GH)]
    for gy in range(GH):
        py = gy * CS + 2
        xs_ = []
        m = len(inner)
        for i in range(m):
            (x1, y1), (x2, y2) = inner[i], inner[(i + 1) % m]
            if (y1 > py) != (y2 > py):
                xs_.append(x1 + (py - y1) * (x2 - x1) / (y2 - y1))
        xs_.sort()
        for a, b in zip(xs_[0::2], xs_[1::2]):
            for gx in range(max(0, int(a / CS) + 1), min(GW, int(b / CS))):
                inside[gy][gx] = True
    for gy in range(GH):
        for gx in range(GW):
            if pip(gx * CS + 2, gy * CS + 2, sq):
                clear[gy][gx] = -1
    reserved = [[False] * GW for _ in range(GH)]

    def reserve(x0, y0, x1, y1):
        for gy in range(max(0, int(y0 / CS)), min(GH, int(y1 / CS) + 1)):
            for gx in range(max(0, int(x0 / CS)), min(GW, int(x1 / CS) + 1)):
                reserved[gy][gx] = True

    # ---- the important buildings: positions (base points) and reserved ground
    B = {}
    CATH = (600, 470)
    B['castle'] = (392, 534)
    B['lodge'] = (840, 484)
    B['guild'] = (772, 708)
    B['cross'] = (866, 770)
    B['college'] = (1170, 600)
    B['mint'] = (516, 812)
    reserve(570, 380, 905, 500)       # cathedral close and its plaza
    reserve(830, 440, 960, 504)       # lodge yard
    reserve(350, 470, 690, 590)       # castle hill
    reserve(760, 650, 945, 714)       # guildhall
    reserve(1160, 530, 1340, 606)     # college
    reserve(488, 772, 600, 818)       # mint
    for k, i in gates.items():
        gx, gy = ring[i]
        reserve(gx - 36, gy - 30, gx + 36, gy + 14)

    # ---- houses: terraces along the streets, drawn from a set of variants
    occ = [[False] * GW for _ in range(GH)]
    houses, variants = [], {}
    vr = random.Random(seed + 1)
    y = 266.0
    while y < 925:
        x = 330.0 + rnd.uniform(0, 8)
        while x < 1500:
            w = rnd.choice((14, 17, 17, 20, 20, 23))
            dd = rnd.choice((15, 19))
            x1 = x + w + DX * dd
            y0 = y - DY * dd
            gx0, gx1 = int((x + 1) / CS), int((x1 - 1) / CS)
            gy0, gy1 = int((y0 + 1) / CS), int((y - 1) / CS)
            ok, near = True, False
            for gy in range(gy0, gy1 + 1):
                for gx in range(gx0, gx1 + 1):
                    if not inside[gy][gx] or reserved[gy][gx] or clear[gy][gx] < 0.5:
                        ok = False
                        break
                    if clear[gy][gx] < 30:
                        near = True
                if not ok:
                    break
            if ok and near:
                for gy in range(gy0, gy1 + 1):
                    for gx in range(gx0, gx1 + 1):
                        occ[gy][gx] = True
                kind = rnd.choices(('gable', 'eave', 'step'), (0.52, 0.34, 0.14))[0]
                rc = 'rr' if rnd.random() < 0.26 else 'r0'
                h = rnd.choice((10, 13))
                r = rnd.choice((8, 11)) if kind != 'eave' else rnd.choice((6, 8))
                key = (kind, w, dd, h, r, rc)
                if key not in variants:
                    vid = 'v%d' % len(variants)
                    variants[key] = (vid, '<g id="%s">%s</g>' % (vid, inline(house(0, 0, w, dd, h, r, kind, rc, vr))))
                yy = round(y + rnd.choice((0, 0, 1, -1)))
                houses.append((yy, '<use href="#%s" x="%d" y="%d"/>' % (variants[key][0], round(x), yy)))
                x = x + w + rnd.choice((0, 0, 0, 0, 0.8, 2.5))
            else:
                x += 2.5
        y += rnd.uniform(9.2, 11)
    sorted_items += [(yy, s_, None) for yy, s_ in houses]
    defs.extend(v[1] for v in variants.values())

    PREC[0] = 0
    # ---- gardens in the block interiors: rows of small garden trees
    gard, gtr = '', ''
    for gy in range(int(270 / CS), int(920 / CS), 2):
        for gx in range(int(340 / CS), int(1490 / CS), 3):
            if inside[gy][gx] and not reserved[gy][gx] and not occ[gy][gx] and clear[gy][gx] > 30:
                if all(not occ[gy + a_][gx + b_] for a_ in (-2, -1, 0, 1) for b_ in (-1, 0, 1)) and rnd.random() < 0.5:
                    px, py = gx * CS + (gy % 4) * 1.5 + rnd.uniform(-1.2, 1.2), gy * CS + rnd.uniform(-0.8, 0.8)
                    gtr += circ(px, py - 3, 2)
                    gard += 'M%s,%sv-1.4' % (f(px), f(py))
    ground.append(path(gard, 'n'))
    ground.append(path(gtr, 'p'))

    PREC[0] = 1
    # ---- the wall: chunks between towers, towers, gates
    gate_idx = set(gates.values())
    gate_arc = [arc[i] for i in gate_idx]

    def near_gate(a, r=26):
        return any(min(abs(a - g), total - abs(a - g)) < r for g in gate_arc)

    tower_at = []
    a = 18.0
    while a < total:
        if not near_gate(a, 36):
            tower_at.append(a)
        a += 54
    ti = [min(range(n), key=lambda i: abs(arc[i] - t)) for t in tower_at]
    hw = 12
    i = 0
    while i < n:
        j = min(i + 4, n)
        if near_gate(arc[i], 16) and near_gate(arc[min(j, n - 1)], 16):
            i = j
            continue
        seg = [ring[k % n] for k in range(i, j + 1)]
        face = seg + [(x, yy - hw) for x, yy in seg[::-1]]
        top = [(x, yy - hw) for x, yy in seg] + [(x + DX * 11, yy - hw - DY * 11) for x, yy in seg[::-1]]
        s = path(Mz(top), 'p') + path(Mz(face), 'sh') + path(Ml([(x, yy - hw - 1.2) for x, yy in seg]), 'mer')
        sorted_items.append((max(p[1] for p in seg) + 0.5, s, None))
        i = j
    for k in ti:
        x, yy = ring[k]
        o = O(x, yy)
        cyl(o, 0, 0, 0, 7.5, 22, 'cone' if (k // 7) % 2 else 'cren', 13)
        sorted_items.append((yy + 2, o.svg(), None))

    # ---- trees outside the walls and along the roads
    trees = []
    for rd in roads[:3]:
        for k in range(4, len(rd) - 2, 5):
            x, yy = rd[k]
            for side in (-1, 1):
                if rnd.random() < 0.6:
                    trees.append((x + side * rnd.uniform(9, 14), yy + rnd.uniform(-3, 4)))

    # ---- fields outside the walls: hedged parcels with hatching, some orchards, some blank
    cart = (26, 548, 336, 428)          # cartouche box (x, y, w, h)
    rose = (1478, 846, 84)               # wind rose (cx, cy, R)
    excl_boxes = [(cart[0] - 8, cart[1] - 8, cart[0] + cart[2] + 8, cart[1] + cart[3] + 8),
                  (rose[0] - rose[2] - 14, rose[1] - rose[2] - 14, W, H),
                  (30, 250, 270, 590),       # the old town
                  ]
    ring_out = offset(ring, -16)

    def free_pt(x, yy, far_ok=False):
        if pip(x, yy, ring_out):
            return False
        if yfar(x) - 3 < yy < ybank(x) + 6:
            return False
        for (a0, b0, a1, b1) in excl_boxes:
            if a0 <= x <= a1 and b0 <= yy <= b1:
                return False
        for rd in roads:
            if min(math.dist((x, yy), p) for p in rd) < 7:
                return False
        return True

    PREC[0] = 0
    fields, fh, orch = '', '', ''
    for yy in range(12, H - 10, 46):
        for xx in range(0, W, 92):
            q = [(xx + rnd.uniform(-8, 8), yy + rnd.uniform(-6, 6)), (xx + 92 + rnd.uniform(-8, 8), yy + rnd.uniform(-6, 6)),
                 (xx + 92 + rnd.uniform(-8, 8), yy + 46 + rnd.uniform(-6, 6)), (xx + rnd.uniform(-8, 8), yy + 46 + rnd.uniform(-6, 6))]
            k = rnd.choice((2, 3, 3, 4, 5))
            vert = rnd.random() < 0.5
            for i in range(k):
                t0, t1 = i / k, (i + 1) / k
                if vert:
                    sq_ = [lerp(q[0], q[1], t0), lerp(q[0], q[1], t1), lerp(q[3], q[2], t1), lerp(q[3], q[2], t0)]
                else:
                    sq_ = [lerp(q[0], q[3], t0), lerp(q[1], q[2], t0), lerp(q[1], q[2], t1), lerp(q[0], q[3], t1)]
                cx_, cy_ = sum(p[0] for p in sq_) / 4, sum(p[1] for p in sq_) / 4
                if not all(free_pt(px, py) for px, py in sq_ + [(cx_, cy_)]):
                    continue
                fields += Mz(sq_)
                kind = rnd.random()
                if kind < 0.86:
                    a0, a1 = (sq_[0], sq_[3]) if vert else (sq_[0], sq_[1])
                    b0, b1 = (sq_[1], sq_[2]) if vert else (sq_[3], sq_[2])
                    L = math.dist(a0, b0)
                    nl = max(2, int(L / rnd.uniform(3.2, 4.4)))
                    for j in range(1, nl):
                        t = j / nl
                        p0, p1 = lerp(a0, b0, t), lerp(a1, b1, t)
                        p0, p1 = lerp(p0, p1, 0.04), lerp(p1, p0, 0.04)
                        fh += 'M%s,%sL%s,%s' % (f(p0[0]), f(p0[1]), f(p1[0]), f(p1[1]))
                elif kind < 0.93:
                    for j in range(6):
                        px, py = lerp(lerp(sq_[0], sq_[1], rnd.uniform(0.15, 0.85)), lerp(sq_[3], sq_[2], rnd.uniform(0.15, 0.85)), rnd.uniform(0.25, 0.85))
                        orch += circ(px, py - 2, 1.8)
    ground.append(path(fields, 'n fe'))
    ground.append(path(fh, 'h fh'))
    ground.append(path(orch, 'p'))
    PREC[0] = 1

    for x, yy in trees:
        if free_pt(x, yy) or yy > 930 or x < 330:
            sorted_items.append((yy, tree(x, yy, rnd.uniform(3.2, 4.6), rnd), None))

    # ---- the far bank: a small suburb with its church
    sub = []
    xx = 430.0
    for k in range(22):
        if 610 < xx < 700:
            xx = 700
        yy = yfar(xx) - 4 + rnd.uniform(-2, 1)
        w = rnd.choice((14, 16, 18))
        sub.append((yy, house(xx, yy, w, 14, 9, 7, rnd.choice(('gable', 'eave')), 'r0', rnd)))
        xx += w + 3 + rnd.uniform(0, 2)
        if k == 10:
            xx += 40
    ch = O(640, yfar(640) - 6)
    box(ch, 0, 40, 0, 16, 18)
    roof_u(ch, 0, 40, 0, 16, 18, 13, 'rg', n=6)
    box(ch, 40, 52, 0, 12, 40)
    tx, ty = ch.p(46, 6, 40)
    ch.raw(path(Mz([ch.p(40, 0, 40), ch.p(52, 0, 40), (tx, ty - 24)]), 'rg'))
    ch.raw(path('M%s,%sv-6' % (f(tx), f(ty - 24)), 'n'))
    sub.append((yfar(640) - 6, ch.svg()))
    for yy, s in sorted(sub):
        ground.append(s)

    # ---- links: the buildings that are doors
    def link(key, body, bx, by_, bw, bh, ban):
        L = links[key]
        ban_svg, bb = ban
        x0 = min(bx, bb[0])
        y0 = min(by_, bb[1])
        x1 = max(bx + bw, bb[0] + bb[2])
        y1 = max(by_ + bh, bb[1] + bb[3])
        hit = '<rect class="hit" x="%s" y="%s" width="%s" height="%s" rx="6"/>' % (f(bx), f(by_), f(bw), f(bh))
        meta.append(dict(key=key, x=(bx + bw / 2), y=(by_ + bh / 2), box=(x0, y0, x1 - x0, y1 - y0), name=L['name'], sub=L['sub'], href=L['href']))
        e = lambda v: html.escape(v, quote=True)
        # the accessible name starts with what the banderole shows, then says what the building holds
        shown = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'<text class="bn".*?</text>', ban_svg).group(0)))
        aria = shown + ('. ' + L['label'] if L.get('label') else '')
        return ('<a class="b" id="cv-%s" href="%s" aria-label="%s" data-n="%s" data-s="%s" style="--bw:var(--w-%s)">%s<g class="bd">%s</g><g class="bl">%s</g></a>'
                % (key, e(L['href']), e(aria), e(L['name']), e(L['sub']), L.get('wash', 'red'), hit, body, ban_svg))

    meta = []

    # cathedral + lodge
    cath_svg, cath_o = cathedral(*CATH)
    ban_c = banderole(CATH[0] + 150, CATH[1] - 200, 'The Cathedral', 18, links['cathedral']['sub'])
    sorted_items.append((CATH[1], link('cathedral', cath_svg, CATH[0] - 4, CATH[1] - 250 + 40, 216, 230, ban_c), 'cathedral'))
    lx, ly = B['lodge']
    tf = cath_o.p(176, -18, 0)
    ban_l = banderole(lx + 70, ly - 118, 'Masons’ Lodge', 17, links['lodge']['sub'])
    sorted_items.append((ly + 20, link('lodge', lodge(lx, ly, tf), lx - 50, ly - 140, 140, 168, ban_l), 'lodge'))
    # castle
    cx, cy = B['castle']
    ban_k = banderole(cx + 92, cy - 196, 'Castle & Assize Hall', 17, links['castle']['sub'])
    sorted_items.append((cy - 30, link('castle', castle(cx, cy, rnd), cx - 34, cy - 186, 300, 236, ban_k), 'castle'))
    # guildhall, stalls, market cross
    gx, gy = B['guild']
    ban_g = banderole(gx + 84, gy - 196, 'The Guildhall', 18, links['guild']['sub'])
    sorted_items.append((gy, link('guild', guildhall(gx, gy), gx - 4, gy - 180, 178, 184, ban_g), 'guild'))
    for (sx, sy) in ((736, 744), (760, 778), (928, 740), (904, 782), (948, 776)):
        sorted_items.append((sy, stall(sx, sy, rnd), None))
    mx, my = B['cross']
    ban_x = banderole(mx - 74, my - 14, 'Market Cross', 14)
    sorted_items.append((my, link('cross', market_cross(mx, my), mx - 22, my - 72, 44, 80, ban_x), 'cross'))
    # college
    kx, ky = B['college']
    ban_s = banderole(kx + 92, ky - 200, 'Scriptorium & College', 17, links['college']['sub'])
    sorted_items.append((ky, link('college', college(kx, ky), kx - 4, ky - 186, 190, 196, ban_s), 'college'))
    # mint
    nx, ny = B['mint']
    ban_m = banderole(nx + 34, ny - 112, 'The Mint', 15)
    sorted_items.append((ny, link('mint', mint(nx, ny), nx - 26, ny - 104, 116, 120, ban_m), 'mint'))
    # gates
    gpos = {'gate-l': (-30, -86), 'gate-s': (0, -84), 'gate-r': (30, -84)}
    for k, i in gates.items():
        x, yy = ring[i]
        ox, oy = gpos[k]
        ban = banderole(x + ox, yy + oy, links[k]['short'], 14)
        sorted_items.append((yy + 3, link(k, gatehouse(x, yy), x - 36, yy - 74, 76, 80, ban), k))
    # harbour and ship
    hx = 1270
    hy = ybank(hx) + 2
    hb = harbour(hx, hy) + ship(1196, 196)
    ban_h = banderole(1300, 118, 'The Harbour', 15)
    sorted_items.append((hy - 0.5, link('harbour', hb, 1150, 118, 306, hy - 118 + 6, ban_h), 'harbour'))
    # bridges (one link holding both)
    br = ''
    bxs = []
    for bx0 in (700, 1086):
        y1 = ybank(bx0) + 4
        Ld = (y1 - yfar(bx0 + 60) + 8) / DY
        br += bridge(bx0, y1, Ld, rnd)
        bxs.append((bx0, y1, Ld))
    ban_b = banderole(900, 150, 'The Bridges', 15)
    sorted_items.append((min(b[1] for b in bxs) - 1, link('bridges', br, 690, 70, 470, 180, ban_b), 'bridges'))
    # the old town outside the walls
    ban_o = banderole(150, 266, 'The Old Town', 15)
    sorted_items.append((420, link('oldtown', old_town(84, 316, rnd), 40, 282, 260, 300, ban_o), 'oldtown'))
    # small boats on the river
    for (bx, by) in ((300, 170), (520, 150), (1500, 188), (960, 196), (1010, 150)):
        sorted_items.append((by - 200, boat(bx, by, 1.0), None))

    # ---- assemble the painter's list: decorative runs wrapped and hidden, links as they are
    sorted_items.sort(key=lambda t: t[0])
    body, run = [], []
    for _, s, key in sorted_items:
        if key is None:
            run.append(s)
        else:
            if run:
                body.append('<g aria-hidden="true">%s</g>' % ''.join(run))
                run = []
            body.append(s)
    if run:
        body.append('<g aria-hidden="true">%s</g>' % ''.join(run))

    # ---- lettering, cartouche, rose and scale
    lab = []
    defs.append('<path id="cv-p1" d="%s"/>' % Ml([(80, (yfar(80) + ybank(80)) / 2 + 6), (420, (yfar(420) + ybank(420)) / 2 + 8)]))
    defs.append('<path id="cv-p2" d="%s"/>' % Ml([(1160, (yfar(1160) + ybank(1160)) / 2 + 22), (1300, (yfar(1300) + ybank(1300)) / 2 + 22)]))
    defs.append('<path id="cv-p3" d="%s"/>' % Ml(spline([(1196, 660), (1300, 618)])))
    defs.append('<path id="cv-p4" d="%s"/>' % Ml(spline([(450, 589), (600, 625)])))
    defs.append('<path id="cv-p5" d="%s"/>' % Ml([(831, 900), (836, 820)]))
    lab.append('<text class="rv"><textPath href="#cv-p1">Flumen Magnum</textPath></text>')
    lab.append('<text class="sn"><textPath href="#cv-p3">Via Regia</textPath></text>')
    lab.append('<text class="sn"><textPath href="#cv-p4">Via Regia</textPath></text>')
    lab.append('<text class="sn"><textPath href="#cv-p5">Via Australis</textPath></text>')
    lab.append('<text class="sn" x="480" y="44">Suburbium</text>')
    for txt, x, y, rot in (('Meridies', W / 2, 30, 0), ('Septentrio', W / 2, H - 20, 0), ('Oriens', 30, H / 2, -90), ('Occidens', W - 30, H / 2, 90)):
        tl = tw(txt.upper(), 'CR', 13) + 9 * 1.6
        if rot:
            lab.append('<g transform="rotate(%d %s %s)"><rect class="pp" x="%s" y="%s" width="%s" height="20"/><text class="cw" x="%s" y="%s">%s</text></g>'
                       % (rot, f(x), f(y), f(x - tl / 2 - 8), f(y - 14), f(tl + 16), f(x), f(y + 1), txt.upper()))
        else:
            lab.append('<rect class="pp" x="%s" y="%s" width="%s" height="20"/><text class="cw" x="%s" y="%s">%s</text>'
                       % (f(x - tl / 2 - 8), f(y - 14), f(tl + 16), f(x), f(y + 1), txt.upper()))
    # wind rose with a fleur-de-lis at Septentrio (pointing down) and a cross at Oriens (left)
    rx_, ry_, R = rose
    lab.append(wind_rose(rx_, ry_, R))
    lab.append(fleur(rx_, ry_ + R + 2, 1))
    lab.append(path('M%s,%sh-9M%s,%sv8' % (f(rx_ - R - 2), f(ry_), f(rx_ - R - 7), f(ry_ - 4)), 'n'))
    # scale of paces under the cartouche's neighbour: bottom centre-left
    sx0, sy0 = 1110, 960
    lab.append(path(Mz([(sx0 - 14, sy0 - 26), (sx0 + 214, sy0 - 26), (sx0 + 214, sy0 + 18), (sx0 - 14, sy0 + 18)]), 'pp'))
    sc = ''
    for i in range(5):
        sc += Mz([(sx0 + i * 40, sy0), (sx0 + (i + 1) * 40, sy0), (sx0 + (i + 1) * 40, sy0 - 5), (sx0 + i * 40, sy0 - 5)])
    lab.append(path(sc, 'p'))
    lab.append(path(''.join(Mz([(sx0 + i * 40, sy0), (sx0 + (i + 1) * 40, sy0), (sx0 + (i + 1) * 40, sy0 - 5), (sx0 + i * 40, sy0 - 5)]) for i in (0, 2, 4)), 'k'))
    for i in range(6):
        lab.append('<text class="sc" x="%s" y="%s">%d</text>' % (f(sx0 + i * 40), f(sy0 + 12), i * 100))
    lab.append('<text class="sn" x="%s" y="%s">Scala passuum</text>' % (f(sx0 + 100), f(sy0 - 10)))
    # the cartouche
    cx0, cy0, cw, chh = cart
    cc = []
    cc.append(path(Mz([(cx0, cy0), (cx0 + cw, cy0), (cx0 + cw, cy0 + chh), (cx0, cy0 + chh)]), 'p ca'))
    cc.append(path(Mz([(cx0 + 7, cy0 + 7), (cx0 + cw - 7, cy0 + 7), (cx0 + cw - 7, cy0 + chh - 7), (cx0 + 7, cy0 + chh - 7)]), 'n'))
    # strapwork: rolled scrolls at the four corners and a strap across the top and bottom
    for (sx, sy, a, b) in ((cx0, cy0, -1, -1), (cx0 + cw, cy0, 1, -1), (cx0, cy0 + chh, -1, 1), (cx0 + cw, cy0 + chh, 1, 1)):
        cc.append(path('M%s,%sc%s,%s %s,%s %s,%sc%s,%s %s,%s %s,%sc%s,%s %s,%s %s,%s' % (
            f(sx - a * 22), f(sy), f(a * 10), f(0), f(a * 22), f(b * 2), f(a * 22), f(b * 12),
            f(0), f(b * 7), f(-a * 8), f(b * 9), f(-a * 11), f(b * 4),
            f(-a * 2), f(-b * 3), f(a * 1), f(-b * 7), f(a * 5), f(-b * 6)), 'n sw'))
        cc.append(path('M%s,%sc%s,%s %s,%s %s,%s' % (f(sx), f(sy - b * 22), f(0), f(b * 10), f(a * 2), f(b * 22), f(a * 12), f(b * 22)), 'n sw'))
    tb, _ = banderole(cx0 + cw / 2, cy0 - 1, 'Civitas Mylesiana', 19)
    cc.append(tb)
    mid = cx0 + cw / 2
    cc.append('<g class="ct"><text class="ct1" x="%s" y="%s">Myles Parslow</text><text class="ct1" x="%s" y="%s">makes things</text>'
              '<text class="ct1" x="%s" y="%s">with AI.</text>' % (f(mid), f(cy0 + 92), f(mid), f(cy0 + 124), f(mid), f(cy0 + 156)))
    cc.append(path('M%s,%sh60M%s,%sh60' % (f(mid - 70), f(cy0 + 186), f(mid + 10), f(cy0 + 186)), 'n'))
    cc.append(path(circ(mid, cy0 + 186, 3), 'k'))
    for i, t in enumerate(('The city of his work, drawn as a map.', 'Each great building is a room of', 'projects; the gates, the bridges, the', 'cross and the mint hold the rest.')):
        cc.append('<text class="ct2" x="%s" y="%s">%s</text>' % (f(mid), f(cy0 + 218 + 22 * i), t))
    cc.append('</g>')
    lab.append('<g class="cart">%s</g>' % ''.join(cc))

    frame = (path(Mz([(4, 4), (W - 4, 4), (W - 4, H - 4), (4, H - 4)]), 'n fr1')
             + path(Mz([(11, 11), (W - 11, 11), (W - 11, H - 11), (11, H - 11)]), 'n fr2'))

    svg = ('<svg class="cv" id="cv" viewBox="0 0 %d %d" role="group" aria-labelledby="cv-t" aria-describedby="cv-d">'
           '<title id="cv-t">Map of the city: Civitas Mylesiana</title>'
           '<desc id="cv-d">A walled city drawn as a bird&#8217;s-eye view. Each important building is a link to a part of the site; '
           'the same links are listed as plain text under the map.</desc>'
           '<defs><clipPath id="cv-clip"><rect x="11" y="11" width="%d" height="%d"/></clipPath>%s</defs>'
           '<rect class="pg" x="0" y="0" width="%d" height="%d"/>'
           '<g clip-path="url(#cv-clip)"><g aria-hidden="true">%s</g>%s<g aria-hidden="true">%s</g></g>'
           '<g aria-hidden="true">%s</g></svg>') % (
        W, H, W - 22, H - 22, ''.join(defs), W, H, ''.join(ground), ''.join(body), ''.join(lab), frame)
    order = ['gate-l', 'castle', 'cathedral', 'lodge', 'bridges', 'harbour', 'college', 'gate-r', 'guild', 'cross', 'gate-s', 'mint', 'oldtown']
    meta.sort(key=lambda m: order.index(m['key']))
    return svg, meta, dict(cart=cart, houses=len(houses))


def building_svg(kind, links=None):
    """One building on its own, for the head of its room's leaf."""
    rnd = random.Random(3)
    if kind == 'castle':
        body, vb = castle(60, 300, rnd), (0, 60, 360, 290)
    elif kind == 'cathedral':
        body, vb = cathedral(20, 330)[0], (0, 60, 300, 300)
    elif kind == 'guild':
        body, vb = guildhall(20, 250), (0, 50, 210, 220)
    elif kind == 'lodge':
        c_svg, c_o = cathedral(-150, 330)
        body, vb = c_svg + lodge(90, 346, c_o.p(176, -18, 0)), (0, 100, 260, 270)
    elif kind == 'college':
        body, vb = college(30, 270), (0, 60, 240, 230)
    else:
        body, vb = '', (0, 0, 10, 10)
    return '<svg class="cv cvb" viewBox="%s" aria-hidden="true" focusable="false">%s</svg>' % (' '.join(str(v) for v in vb), body)


if __name__ == '__main__':
    demo = {k: dict(href='#' + k, label=k, name=k, sub='sub', short=k) for k in
            ('castle', 'cathedral', 'lodge', 'guild', 'cross', 'college', 'mint', 'gate-l', 'gate-s', 'gate-r', 'harbour', 'bridges', 'oldtown')}
    s, m, info = build(demo)
    print(len(s), info)
