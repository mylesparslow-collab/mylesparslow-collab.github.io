"""Extract every case study from the five area pages into themed/cases.json.

Both homepage mockups render their in-theme area pages from this one file, so
the content stays identical to the live site while the design changes.
Media paths become root-relative ("assets/...", "demos/..."): each renderer
prefixes them for its own folder depth.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AREAS = [
    ('legal', 'Legal software', 'L'),
    ('business', 'Business', 'B'),
    ('creative', 'Creative & games', 'C'),
    ('design', 'Design, 3D & generative', 'D'),
    ('research', 'AI tools & research', 'R'),
]

def clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()

def norm_paths(html):
    # ../assets/x -> assets/x ; ../demos/x -> demos/x ; ../legal/#id -> legal/#id
    return re.sub(r'(src|href|poster)="\.\./', r'\1="', html)

out = {'areas': []}
for slug, name, letter in AREAS:
    frozen = Path(__file__).parent / 'source' / f'{slug}.html'
    h = (frozen if frozen.exists() else ROOT / slug / 'index.html').read_text()
    intro = re.search(r'<header class="intro area-intro">(.*?)</header>', h, re.S)
    intro_h = intro.group(1) if intro else ''
    lede = re.search(r'<p class="lede">(.*?)</p>', intro_h, re.S)
    cases = []
    for m in re.finditer(r'<details class="case" id="([^"]+)"([^>]*)>(.*?)</details>', h, re.S):
        cid, attrs, inner = m.groups()
        sub_attr = re.search(r'data-sub="([^"]*)"', attrs)
        summ = re.search(r'<summary class="case-sum">(.*?)</summary>', inner, re.S).group(1)
        eyebrow = re.search(r'<span class="eyebrow">(.*?)</span>', summ, re.S)
        title = re.search(r'<h2>(.*?)</h2>', summ, re.S)
        sum_p = re.search(r'<p class="sum">(.*?)</p>', summ, re.S) or re.search(r'<p>(.*?)</p>', summ, re.S)
        body = re.search(r'<div class="case-body">(.*)</div>\s*$', inner, re.S)
        body_html = norm_paths(body.group(1).strip()) if body else ''
        cases.append({
            'id': cid,
            'eyebrow': clean(eyebrow.group(1)) if eyebrow else '',
            'title': clean(title.group(1)) if title else cid,
            'sub': sub_attr.group(1) if sub_attr else '',
            'sum': clean(sum_p.group(1)) if sum_p else '',
            'body_html': body_html,
            'media': sorted(set(re.findall(r'(?:src|poster)="(assets/[^"]+)"', body_html))),
            'demo_links': re.findall(r'href="(demos/[^"]+)"', body_html),
        })
    # Everything that sits outside the case blocks: group headings + intros (with their ids, so old
    # /#g-... links resolve) and extra non-case sections ("shelf", e.g. Business "Smaller pieces").
    groups, extras = [], []
    gstarts = list(re.finditer(r'<section class="group" id="([^"]+)">', h))
    wf = h.find('<div class="wayfind">')
    for gi, gm in enumerate(gstarts):
        end = gstarts[gi + 1].start() if gi + 1 < len(gstarts) else (wf if wf > 0 else len(h))
        chunk = h[gm.end():end]
        head = re.search(r'<div class="group-head">\s*<h2>(.*?)</h2>\s*(?:<p>(.*?)</p>)?\s*</div>', chunk, re.S)
        gcases = re.findall(r'<details class="case" id="([^"]+)"', chunk)
        groups.append({'id': gm.group(1),
                       'title': clean(head.group(1)) if head else '',
                       'intro': clean(head.group(2) or '') if head else '',
                       'cases': gcases})
        for sm in re.finditer(r'<section class="shelf">(.*?)</section>', chunk, re.S):
            sh = sm.group(1)
            eb = re.search(r'<span class="eyebrow">(.*?)</span>', sh, re.S)
            ti = re.search(r'<h2>(.*?)</h2>', sh, re.S)
            items = [{'title': clean(t), 'html': norm_paths(p_.strip())}
                     for t, p_ in re.findall(r'<div><h3>(.*?)</h3><p>(.*?)</p></div>', sh, re.S)]
            extras.append({'group': gm.group(1), 'eyebrow': clean(eb.group(1)) if eb else '',
                           'title': clean(ti.group(1)) if ti else '', 'items': items})
    assert sum(len(g['cases']) for g in groups) == len(cases), slug
    out['areas'].append({'slug': slug, 'name': name, 'letter': letter,
                         'lede': clean(lede.group(1)) if lede else '', 'cases': cases,
                         'groups': groups, 'extras': extras})
    print(slug, len(cases), 'cases')

(Path(__file__).parent / 'cases.json').write_text(json.dumps(out, indent=1))
print('total', sum(len(a['cases']) for a in out['areas']))
