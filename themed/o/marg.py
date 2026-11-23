"""Manuscript furniture for mockup O: illuminated initials, the vine bar, line-fillers and the margin drawings.

Every piece is drawn new here as SVG; nothing is traced from the reference scans. The initials are painted
objects, so they keep fixed colours in both themes (lapis, rose, gold, vellum); the pen drawings use the theme
ink and two washes, so they follow light and dark.
"""
import math

LAPIS, ROSE, GOLD, GOLDD, VELL, INK, VERM = '#1f3f86', '#a54a5c', '#b08a2e', '#7d6120', '#f5f0e4', '#2b231c', '#b8321c'


def f(v):
    v = round(v, 1)
    return str(int(v)) if v == int(v) else '%.1f' % v


LEAF = [(0, 0), (-4, -1), (-8, -6), (-5, -10), (-3, -12), (-1, -11), (0, -9), (1, -11), (3, -12), (5, -10), (8, -6), (4, -1), (0, 0)]


def leaf_d(x, y, a, s=1.0):
    """An ivy leaf: stem at (x, y), pointing along angle a."""
    c, sn = math.cos(a), math.sin(a)
    P = [(x + s * (c * px - sn * py), y + s * (sn * px + c * py)) for px, py in LEAF]
    d = 'M%s,%s' % (f(P[0][0]), f(P[0][1]))
    for i in range(1, 13, 3):
        d += 'C%s,%s %s,%s %s,%s' % tuple(f(v) for p in P[i:i + 3] for v in p)
    return d + 'Z'


# ------------------------------------------------------------------ illuminated initials
def _ground(v, uid):
    """The white pen pattern on the ground of the initial, inside 8..92."""
    out, v = [], v % 4
    if v == 0:      # diaper of fine diagonal lines with a dot in each lozenge
        d = ''
        for k in range(-80, 100, 11):
            d += 'M%s,8L%s,92' % (f(8 + k), f(8 + k + 84))
            d += 'M%s,8L%s,92' % (f(92 - k), f(92 - k - 84))
        out.append('<path d="%s" stroke="%s" stroke-width=".7" fill="none" clip-path="url(#%s)"/>' % (d, VELL, uid))
        dots = ''
        for i in range(8):
            for j in range(8):
                x, y = 8 + 5.5 + i * 11, 8 + j * 11
                if 10 < x < 90 and 10 < y < 90:
                    dots += 'M%s,%sh0' % (f(x), f(y))
        out.append('<path d="%s" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (dots, VELL))
    elif v == 1:    # scrolling white tendrils
        d = ''
        for (cx, cy, s) in ((24, 24, 1), (76, 24, -1), (24, 76, -1), (76, 76, 1), (50, 50, 1)):
            d += 'M%s,%sc%s,-8 %s,-10 %s,-4c%s,4 %s,8 %s,4' % (f(cx - 10), f(cy + 4), f(4 * s), f(14 * s), f(16 * s), f(2 * s), f(-2 * s), f(-6 * s))
            d += 'M%s,%sc%s,6 %s,10 %s,6' % (f(cx - 4), f(cy - 8), f(-3 * s), f(5 * s), f(10 * s))
        out.append('<path d="%s" stroke="%s" stroke-width=".9" fill="none" stroke-linecap="round" clip-path="url(#%s)"/>' % (d, VELL, uid))
        dots = ''.join('M%s,%sh0' % (f(x), f(y)) for x, y in ((14, 50), (86, 50), (50, 14), (50, 86), (36, 36), (64, 64), (64, 36), (36, 64)))
        out.append('<path d="%s" stroke="%s" stroke-width="2.2" stroke-linecap="round"/>' % (dots, VELL))
    elif v == 2:    # trefoils of three dots
        dots = ''
        for i in range(5):
            for j in range(5):
                x, y = 16 + i * 17 + (j % 2) * 8.5, 16 + j * 17
                if x > 88:
                    continue
                dots += 'M%s,%sh0M%s,%sh0M%s,%sh0' % (f(x), f(y - 2.2), f(x - 2), f(y + 1.3), f(x + 2), f(y + 1.3))
        out.append('<path d="%s" stroke="%s" stroke-width="1.7" stroke-linecap="round"/>' % (dots, VELL))
    else:           # a lattice of small crosses
        d = ''
        for i in range(6):
            for j in range(6):
                x, y = 15 + i * 14, 15 + j * 14
                d += 'M%s,%sh5M%s,%sv5' % (f(x - 2.5), f(y), f(x), f(y - 2.5))
        out.append('<path d="%s" stroke="%s" stroke-width=".9" fill="none"/>' % (d, VELL))
    return ''.join(out)


# ground colour, letter fill, letter outline
INI = [(LAPIS, GOLD, INK), (ROSE, VELL, INK), (LAPIS, VELL, INK), (ROSE, LAPIS, VELL)]


def initial(ch, v, uid='ic'):
    g, lf, lo = INI[v % 4]
    pearl = ''.join('M%s,%sh0' % (f(p), f(q)) for k in range(1, 12) for (p, q) in ((k * 8.33, 3), (k * 8.33, 97), (3, k * 8.33), (97, k * 8.33)))
    return ('<svg class="ini" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
            '<defs><clipPath id="%s"><rect x="8" y="8" width="84" height="84"/></clipPath></defs>'
            '<rect x=".6" y=".6" width="98.8" height="98.8" fill="%s" stroke="%s" stroke-width="1.2"/>'
            '<path d="%s" stroke="%s" stroke-width="1.6" stroke-linecap="round"/>'
            '<rect x="7" y="7" width="86" height="86" fill="%s" stroke="%s" stroke-width="1"/>%s'
            '<text x="50" y="77" text-anchor="middle" font-family="Uncial Antiqua,serif" font-size="74" fill="%s" stroke="%s" stroke-width="2.2" '
            'paint-order="stroke" stroke-linejoin="round">%s</text></svg>') % (uid, GOLD, INK, pearl, VELL, g, INK, _ground(v, uid), lf, lo, ch)


def vine(v):
    """The bar that runs down the inner margin from the initial, ending at both ends in ivy curls."""
    a, b = (LAPIS, ROSE) if v % 2 == 0 else (ROSE, LAPIS)
    seg = ''
    y = 46.0
    k = 0
    while y < 372:
        seg += '<rect x="19" y="%s" width="6" height="%s" fill="%s"/>' % (f(y), f(min(34, 372 - y)), a if k % 2 == 0 else b)
        y += 34
        k += 1
    knots = ''.join('<rect x="18" y="%s" width="8" height="4" fill="%s" stroke="%s" stroke-width=".7"/>' % (f(46 + 34 * i - 2), GOLD, INK, ) for i in range(1, 10))

    def leaf(x, y, ang, fill):
        return '<path d="%s" fill="%s" stroke="%s" stroke-width=".8"/>' % (leaf_d(x, y, ang + math.pi / 2), fill, INK)

    curls = ('<path d="M22,46C22,30 10,26 6,34C3,40 9,44 13,40" fill="none" stroke="%s" stroke-width="1.4"/>'
             '<path d="M22,372C22,388 34,394 39,386C42,380 36,376 32,380" fill="none" stroke="%s" stroke-width="1.4"/>'
             '<path d="M25,96H48" stroke="%s" stroke-width="3"/>') % (INK, INK, GOLD)
    leaves = leaf(13, 40, -0.4, GOLD) + leaf(8, 26, -1.6, b) + leaf(30, 388, 2.6, GOLD) + leaf(40, 380, 1.2, a)
    edge = '<rect x="19" y="46" width="6" height="326" fill="none" stroke="%s" stroke-width=".9"/>' % INK
    return '<svg class="vine" viewBox="0 0 50 400" aria-hidden="true" focusable="false">%s%s%s%s%s</svg>' % (seg, edge, knots, curls, leaves)


# ------------------------------------------------------------------ line-fillers (dividers between leaves)
def filler(v):
    out = []
    if v % 3 == 0:
        out.append('<rect x="60" y="6" width="520" height="8" fill="%s" stroke="%s" stroke-width=".8"/>' % (LAPIS, INK))
        z = 'M62,12' + ''.join('L%s,%s' % (f(62 + i * 8), '8' if i % 2 else '12') for i in range(1, 65))
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1"/>' % (z, VELL))
    elif v % 3 == 1:
        out.append('<rect x="60" y="6" width="520" height="8" fill="%s" stroke="%s" stroke-width=".8"/>' % (VERM, INK))
        out.append('<path d="%s" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (''.join('M%s,10h0' % f(66 + i * 9) for i in range(57)), VELL))
    else:
        out.append('<rect x="60" y="6" width="260" height="8" fill="%s" stroke="%s" stroke-width=".8"/>' % (VERM, INK))
        out.append('<rect x="320" y="6" width="260" height="8" fill="%s" stroke="%s" stroke-width=".8"/>' % (LAPIS, INK))
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width=".9"/>' % (''.join('M%s,7.5l4,2.5l-4,2.5' % f(64 + i * 10) for i in range(51)), VELL))
    # knots and pen flourishes at both ends
    for x, s in ((60, -1), (580, 1)):
        out.append('<circle cx="%s" cy="10" r="5" fill="%s" stroke="%s" stroke-width=".8"/><circle cx="%s" cy="10" r="1.6" fill="%s"/>' % (x, GOLD, INK, x, INK))
        out.append('<path d="M%s,10c%s,-8 %s,-8 %s,0s%s,8 %s,0" fill="none" stroke="%s" stroke-width="1"/>' % (
            x + 5 * s, f(8 * s), f(16 * s), f(22 * s), f(14 * s), f(22 * s), VERM))
    out.append('<rect x="318" y="7" width="4" height="6" fill="%s"/>' % GOLD if v % 3 == 2 else '')
    return '<svg class="fill" viewBox="0 0 640 20" aria-hidden="true" focusable="false">%s</svg>' % ''.join(out)


# ------------------------------------------------------------------ margin drawings (pen line + flat wash)
def _owl():
    body = 'M45,20C64,20 74,40 72,62C70,84 60,96 45,96C30,96 20,84 18,62C16,40 26,20 45,20Z'
    chev = ''.join('M%s,%sl2.4,2.4l2.4,-2.4' % (f(x), f(y)) for (x, y) in ((34, 62), (42, 62), (50, 62), (30, 70), (38, 70), (46, 70), (54, 70),
                                                                          (34, 78), (42, 78), (50, 78), (40, 86), (46, 86)))
    return ('<path class="pf" d="M2,101C30,98 60,103 88,99M70,100C74,96 78,94 84,94"/><path class="pn wg" d="%s"/>' % (leaf_d(80, 95, -1.1, 0.9))
            + '<path class="pn" d="M28,27L22,10L37,22ZM62,27L68,10L53,22Z"/>'
            + '<path class="pn wo" d="%s"/>' % body
            + '<path class="pn" d="M35,30C42,30 45,36 45,41C45,47 41,51 35,51C29,51 25,46 25,40C25,35 29,30 35,30Z'
            'M55,30C61,30 65,35 65,40C65,46 61,51 55,51C49,51 45,47 45,41C45,36 48,30 55,30Z"/>'
            + '<circle class="pk" cx="35.5" cy="41" r="3.2"/><circle class="pk" cx="54.5" cy="41" r="3.2"/>'
            + '<path class="ph" d="M28,34C30,32 33,31 35,31M62,34C60,32 57,31 55,31"/>'
            + '<path class="pn wr" d="M45,45l-3,5l3,4l3,-4Z"/>'
            + '<path class="pf" d="M22,52C20,70 26,86 36,93M68,52C70,70 64,86 54,93"/><path class="ph" d="%s"/>' % chev
            + '<path class="pf" d="M37,96l-2,5M40,96l0,5M43,96l2,5M48,96l-2,5M51,96l0,5M54,96l2,5"/>'), (0, 4, 90, 102)


def _manicule():
    hand = ('M22,15C30,12 40,11 48,13L104,15C112,15 114,25 106,26L62,27C68,28 70,34 63,35C68,36 68,42 61,42'
            'C64,43 63,48 56,48C48,49 40,47 33,45L22,42Z')
    return ('<path class="pn wr" d="M4,12H22V45H4Z"/>'
            '<path class="pf" d="M9,12V45M22,12q4,2.75 0,5.5q4,2.75 0,5.5q4,2.75 0,5.5q4,2.75 0,5.5q4,2.75 0,5.5q4,2.75 0,5.5"/>'
            '<path class="pn" d="%s"/>' % hand
            + '<path class="pf" d="M100,17C104,17 106,19 106,22M76,16v5M82,16v5M54,27C57,28 59,31 58,33M52,35C55,36 57,39 55,41M48,42C51,43 52,45 51,47"/>'
            + '<path class="ph" d="M28,18C34,17 40,18 46,20M28,38C33,39 36,40 38,41"/>'), (0, 4, 116, 48)


def _heron():
    body = 'M30,70C30,56 44,50 56,54C68,58 76,70 78,84L86,97C76,95 62,91 52,91C40,91 30,82 30,70Z'
    neck = ('M32,64C26,56 34,46 32,38C30,32 24,30 24,24L21,23L2,24.5L20,19C20,17 22,14 26,12C30,10 36,12 36,18'
            'C36,22 36,26 40,30C46,36 50,44 44,54')
    return ('<path class="pf" d="M14,140C16,120 12,104 18,88M16,118C8,112 6,104 4,98M74,140C72,122 76,112 80,100M80,140C82,128 86,120 88,114"/>'
            + '<path class="pf" d="M56,90L58,112L56,136M56,136l-10,2M56,136l10,1M56,136l1,4M63,90L71,105L61,111"/>'
            + '<path class="pn wg" d="%s"/><path class="pn wg" d="%s"/>' % (body, neck)
            + '<path class="pf" d="M44,62C56,64 66,72 74,86M50,70C58,74 64,80 68,88M34,13C42,10 50,12 57,8M35,15C43,14 49,16 55,14"/>'
            + '<circle class="pk" cx="28" cy="16.5" r="1.3"/>'
            + '<path class="ph" d="M36,62C40,66 44,70 48,74M38,56C41,60 43,64 46,68M4,140C30,138 60,142 88,139M10,146h14M40,147h18M66,145h12"/>'), (0, 4, 92, 146)


def _goose():
    body = 'M34,58C34,46 50,40 66,44C82,48 98,54 104,62C97,62 99,66 93,70C87,80 70,84 56,84C42,84 34,72 34,58Z'
    neck = ('M40,48C34,42 30,34 30,26C30,18 24,14 18,16C14,17 12,20 12,22L2,25L3,27L13,28C16,30 18,34 20,40'
            'C22,50 30,56 36,62')
    quill = 'M14,27C18,18 24,10 32,4C30,12 24,20 17,29Z'
    return ('<path class="pn wr" d="%s"/>' % quill
            + '<path class="pf" d="M58,84L56,99M56,99l-8,4l3,-1l3,1M56,99l7,3M71,82L73,99M73,99l-8,4M73,99l7,3"/>'
            + '<path class="pn" d="%s"/><path class="pn" d="%s"/>' % (body, neck)
            + '<path class="pn wo" d="M12,22L2,25L3,27L13,28Z"/><path class="pf" d="M12,25.5l-9,0.5"/>'
            + '<path class="pf" d="M6,36L31,5"/>'
            + '<path class="ph" d="M19,25l4,-4M21,22l4,-5M24,18l4,-5M26,14l3,-5"/>'
            + '<path class="pf" d="M52,56C64,54 80,58 92,66M60,62C70,62 78,66 86,70M64,70C72,72 80,74 86,74"/>'
            + '<circle class="pk" cx="19" cy="20" r="1.3"/>'
            + '<path class="ph" d="M40,100C56,102 76,100 96,102"/>'), (0, 0, 108, 106)


def _hare():
    body = ('M50,100C46,86 48,70 56,60C54,52 52,46 50,40C44,40 40,36 38,32C36,28 38,22 42,19C46,16 52,15 56,17'
            'C61,20 64,26 64,32C74,40 90,52 96,70C100,84 98,96 88,102L50,102Z')
    ear1 = 'M52,18C55,6 64,0 71,1C71,8 63,15 58,21Z'
    ear2 = 'M57,19C63,9 74,5 81,7C79,13 69,19 62,25Z'
    book = 'M22,62L40,57L41,73L23,78ZM40,57L56,61L56,77L41,73Z'
    return ('<path class="pn wo" d="%s"/><path class="pn wo" d="%s"/><path class="pn wo" d="%s"/>' % (ear2, body, ear1)
            + '<path class="pf" d="M60,103C70,105 84,105 92,103M58,14C62,9 66,6 69,4"/><circle class="pn" cx="98" cy="92" r="5"/>'
            + '<path class="pn" d="%s"/><path class="pn wr" d="M23,78L41,73L56,77L41,76Z"/>' % book
            + '<path class="ph" d="M26,64l11,-3M26,67l11,-3M27,70l11,-3M27,73l11,-3M43,61l10,2.6M43,64l10,2.6M43,67l10,2.6M43,70l10,2.6"/>'
            + '<path class="pn" d="M38,76C38,81 44,82 46,77M48,77C49,82 55,82 55,78"/>'
            + '<circle class="pk" cx="47" cy="25" r="1.4"/><path class="ph" d="M39,31l-9,-3M39,32l-9,2M60,40C66,52 70,66 70,80M74,78C80,84 84,92 84,100"/>'), (0, -2, 106, 108)


def _cat_lute():
    head = 'M54,20C52,30 58,40 66,40C76,40 82,32 80,22C78,16 72,14 66,14C60,14 56,16 54,20Z'
    body = 'M58,40C46,48 42,70 46,92C48,104 56,110 66,110C78,110 86,104 88,92C92,72 86,52 76,40Z'
    lute = 'M38,92C30,84 34,70 46,66C56,62 66,66 66,74C66,84 58,94 48,96C44,97 41,95 38,92Z'
    neck = 'M60,68L90,48L93,52L64,74Z'
    return ('<path class="pf" d="M86,104C100,104 106,94 100,86C96,82 92,86 96,88"/>'
            '<path class="pn" d="M54,22L56,6L64,15ZM71,14L80,6L79,22Z"/><path class="pn" d="%s"/><path class="pn" d="%s"/>' % (body, head)
            + '<path class="pf" d="M60,26q3,-2 6,0M70,26q3,-2 6,0M74,32l12,-2M74,34l12,1M62,32l-12,-2M62,34l-12,1"/><path class="pk" d="M68.5,30.5l-1.6,2h3.2Z"/>'
            + '<path class="pn wo" d="%s"/>' % lute
            + '<path class="pn wo" d="%s"/>' % neck
            + '<path class="pn" d="M90,48L99,53L97,57L92,52Z"/><path class="pf" d="M94,50l-2,-3M96,51.5l-2,-3M98,53l-2,-3"/>'
            + '<circle class="pn" cx="50" cy="80" r="4.5"/><circle class="ph" cx="50" cy="80" r="2.6"/>'
            + '<path class="ph" d="M41,88L91,50M42,90L92,51.5"/><path class="pf" d="M40,90l6,-4"/>'
            + '<path class="pn" d="M80,52C83,49 88,50 87,54C86,57 81,57 80,55ZM54,76C57,72 62,73 61,77C60,80 56,80 54,78Z"/>'
            + '<path class="ph" d="M60,104C62,108 66,110 70,110M52,46C50,54 48,62 48,70"/>'), (28, 2, 82, 110)


DRAWINGS = {'heron': _heron, 'hare': _hare, 'cat': _cat_lute, 'owl': _owl, 'goose': _goose, 'manicule': _manicule}
SET = ['heron', 'hare', 'cat', 'owl', 'goose']


def drawing(name, cls='marg'):
    body, (x, y, w, h) = DRAWINGS[name]()
    return '<svg class="%s marg--%s" viewBox="%s %s %s %s" aria-hidden="true" focusable="false">%s</svg>' % (cls, name, x, y, w, h, body)
