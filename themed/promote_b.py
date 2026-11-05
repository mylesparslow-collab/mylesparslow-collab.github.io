"""Promote mockup B to the live site layout.

1. Freeze the pre-redesign area pages as themed/source/<area>.html (first run only).
   extract_cases.py reads from there, so the case content survives the swap.
2. Re-run extract_cases.py and render_b.py so mockup-b/ is current.
3. Write the site:
   index.html                 <- mockup-b/index.html
   <area>/index.html          <- mockup-b/<area>/index.html
   assets/site/{b,rooms}.{css,js}
   with paths rewritten for the root layout, and demo links pointed at the
   site's own demos/ instead of the absolute mylesparslow.com URLs.
Re-runnable: edit render_b.py / b.css / b.js in mockup-b, then run this again.
"""
import re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMED = ROOT / 'themed'
SRC = THEMED / 'source'
MB = ROOT / 'mockup-b'
AREAS = ['legal', 'business', 'creative', 'design', 'research']
SHARED = ['b.css', 'b.js', 'rooms.css', 'rooms.js']

# 1. freeze the original area pages once
SRC.mkdir(exist_ok=True)
for a in AREAS:
    dst = SRC / f'{a}.html'
    if not dst.exists():
        page = (ROOT / a / 'index.html').read_text()
        if 'class="case"' not in page or 'details' not in page:
            sys.exit(f'{a}/index.html does not look like an original area page; refusing to freeze it')
        dst.write_text(page)
        print('froze', dst.relative_to(ROOT))

# 2. regenerate B from the frozen sources
for script in ['extract_cases.py', 'render_b.py']:
    subprocess.run([sys.executable, '-I', str(THEMED / script)], check=True, cwd=ROOT)

# 3. lay B over the site root
site = ROOT / 'assets' / 'site'
site.mkdir(parents=True, exist_ok=True)
for f in SHARED:
    shutil.copy(MB / f, site / f)

def demos(t, prefix):
    return t.replace('https://mylesparslow.com/demos/', prefix + 'demos/')

h = (MB / 'index.html').read_text()
h = h.replace('"../assets/', '"assets/').replace("'../assets/", "'assets/")
h = h.replace('href="b.css"', 'href="assets/site/b.css"').replace('src="b.js"', 'src="assets/site/b.js"')
h = demos(h, '')
(ROOT / 'index.html').write_text(h)

for a in AREAS:
    t = (MB / a / 'index.html').read_text()
    t = t.replace('"../../assets/', '"../assets/').replace("'../../assets/", "'../assets/")
    for f in SHARED:
        kind = 'href' if f.endswith('.css') else 'src'
        t = t.replace(f'{kind}="../{f}"', f'{kind}="../assets/site/{f}"')
    t = demos(t, '../')
    (ROOT / a / 'index.html').write_text(t)

# sanity: nothing should still point at mockup-only paths
bad = []
for p in [ROOT / 'index.html'] + [ROOT / a / 'index.html' for a in AREAS]:
    t = p.read_text()
    bad += [f'{p.relative_to(ROOT)}: {m}' for m in re.findall(r'(?:href|src)="(?:\.\./)*(?:b|rooms)\.(?:css|js)"', t)]
    bad += [f'{p.relative_to(ROOT)}: ../../assets' for _ in re.findall(r'\.\./\.\./assets', t)]
    bad += [f'{p.relative_to(ROOT)}: mockup' for _ in re.findall(r'mockup-[ab]/', t)]
print('promoted B; leftover mockup paths:', bad or 'none')
