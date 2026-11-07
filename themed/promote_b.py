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

Drift guard: every file this script writes is fingerprinted in themed/.promoted.json.
If a live file no longer matches its fingerprint (someone edited index.html,
an area page or assets/site/* directly), the script stops and lists them, so
their work isn't overwritten. Port those edits into mockup-b/ or themed/source/
first, then run with --force. Without a fingerprint file it compares against
what it is about to write and stops on any difference.
"""
import hashlib, json, re, shutil, subprocess, sys
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

FORCE = '--force' in sys.argv
MANIFEST = THEMED / '.promoted.json'
LIVE = [ROOT / 'index.html'] + [ROOT / a / 'index.html' for a in AREAS] + [ROOT / 'assets' / 'site' / f for f in SHARED]
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
if MANIFEST.exists() and not FORCE:
    known = json.loads(MANIFEST.read_text())
    drift = [str(p.relative_to(ROOT)) for p in LIVE if known.get(str(p.relative_to(ROOT))) not in (None, digest(p))]
    if drift:
        sys.exit('refusing: these live files were edited since the last promote:\n  ' + '\n  '.join(drift)
                 + '\nPort the edits into mockup-b/ or themed/source/, then re-run with --force.')

# 2. regenerate B from the frozen sources
for script in ['extract_cases.py', 'render_b.py']:
    subprocess.run([sys.executable, '-I', str(THEMED / script)], check=True, cwd=ROOT)

# 3. lay B over the site root: build every output in memory, check drift, then write
def demos(t, prefix):
    return t.replace('https://mylesparslow.com/demos/', prefix + 'demos/')

outputs = {}
for f in SHARED:
    outputs[ROOT / 'assets' / 'site' / f] = (MB / f).read_text()

h = (MB / 'index.html').read_text()
h = h.replace('"../assets/', '"assets/').replace("'../assets/", "'assets/")
h = h.replace('href="b.css"', 'href="assets/site/b.css"').replace('src="b.js"', 'src="assets/site/b.js"')
outputs[ROOT / 'index.html'] = demos(h, '')

for a in AREAS:
    t = (MB / a / 'index.html').read_text()
    t = t.replace('"../../assets/', '"../assets/').replace("'../../assets/", "'../assets/")
    for f in SHARED:
        kind = 'href' if f.endswith('.css') else 'src'
        t = t.replace(f'{kind}="../{f}"', f'{kind}="../assets/site/{f}"')
    outputs[ROOT / a / 'index.html'] = demos(t, '../')

if not MANIFEST.exists() and not FORCE:
    # no fingerprints yet: any live file that differs from what we'd write may hold edits made elsewhere
    differ = [str(q.relative_to(ROOT)) for q, t in outputs.items() if q.exists() and q.read_text() != t]
    if differ:
        sys.exit('refusing: no .promoted.json fingerprints, and these live files differ from what this run would write:\n  '
                 + '\n  '.join(differ) + '\nCheck they hold no edits made directly on the live site (git log -- <file>), '
                 'port any into mockup-b/ or themed/source/, then re-run with --force.')

(ROOT / 'assets' / 'site').mkdir(parents=True, exist_ok=True)
for q, t in outputs.items():
    q.write_text(t)
MANIFEST.write_text(json.dumps({str(q.relative_to(ROOT)): digest(q) for q in LIVE}, indent=1))

# sanity: nothing should still point at mockup-only paths
bad = []
for q in [ROOT / 'index.html'] + [ROOT / a / 'index.html' for a in AREAS]:
    t = q.read_text()
    bad += [f'{q.relative_to(ROOT)}: {m}' for m in re.findall(r'(?:href|src)="(?:\.\./)*(?:b|rooms)\.(?:css|js)"', t)]
    bad += [f'{q.relative_to(ROOT)}: ../../assets' for _ in re.findall(r'\.\./\.\./assets', t)]
    bad += [f'{q.relative_to(ROOT)}: mockup' for _ in re.findall(r'mockup-[ab]/', t)]
print('promoted B; fingerprints saved to themed/.promoted.json; leftover mockup paths:', bad or 'none')
