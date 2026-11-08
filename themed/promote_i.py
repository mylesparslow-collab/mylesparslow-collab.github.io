"""Promote mockup I ("Transit Map") to the live site.

Content source from now on is themed/live.json (extract_live.py only understands the
old design B markup, so do NOT re-run it against the live pages after this promote).
To add or edit a case study: edit themed/live.json, then
    python3 -I themed/render_i.py && python3 -I themed/promote_i.py

Writes:
  index.html, <room>/index.html, assets/site/i.css, assets/site/i.js
Drift guard: hashes of everything written go to themed/.promoted-i.json. If a live file
was edited by hand since (another session, a quick fix), the run stops and lists it.
Port the edit into live.json or render_i.py first, then re-run with --force.
First run (no manifest): refuses if any target has uncommitted changes in git.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MI = ROOT / 'mockup-i'
AREAS = ['legal', 'business', 'creative', 'design', 'research']
MANIFEST = ROOT / 'themed' / '.promoted-i.json'
FORCE = '--force' in sys.argv

HEAD_ICONS = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
              '<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">\n'
              '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def icons(t, rel):
    t = re.sub(r'<link rel="icon" href="' + re.escape(rel) + r'favicon\.svg"[^>]*>', HEAD_ICONS, t)
    assert '/favicon.svg' in t, 'favicon link not found'
    return t


# 1. fresh render
subprocess.run([sys.executable, '-I', str(ROOT / 'themed' / 'render_i.py')], check=True, cwd=ROOT)

# 2. build every output in memory
out = {}
out[ROOT / 'assets/site/i.css'] = (MI / 'i.css').read_text()
out[ROOT / 'assets/site/i.js'] = (MI / 'i.js').read_text()

h = (MI / 'index.html').read_text()
h = h.replace('"../assets/', '"assets/').replace("'../assets/", "'assets/")
h = h.replace('"../demos/', '"demos/')
h = h.replace('href="i.css"', 'href="assets/site/i.css"').replace('src="i.js"', 'src="assets/site/i.js"')
h = h.replace('href="../styles/index.html"', 'href="styles/index.html"')
out[ROOT / 'index.html'] = icons(h, '../')

for a in AREAS:
    t = (MI / a / 'index.html').read_text()
    t = t.replace('"../../assets/', '"../assets/').replace("'../../assets/", "'../assets/")
    t = t.replace('"../../demos/', '"../demos/')
    t = t.replace('href="../i.css"', 'href="../assets/site/i.css"').replace('src="../i.js"', 'src="../assets/site/i.js"')
    out[ROOT / a / 'index.html'] = icons(t, '../../')

# 3. drift guard
rel = lambda p: str(p.relative_to(ROOT))
if not FORCE:
    if MANIFEST.exists():
        known = json.loads(MANIFEST.read_text())
        drift = [rel(p) for p in out if known.get(rel(p)) not in (None, digest(p))]
        if drift:
            sys.exit('refusing: edited since the last promote:\n  ' + '\n  '.join(drift)
                     + '\nPort those edits into themed/live.json or render_i.py, then re-run with --force.')
    else:
        dirty = subprocess.run(['git', 'status', '--porcelain', '--'] + [rel(p) for p in out],
                               capture_output=True, text=True, cwd=ROOT).stdout.strip()
        dirty = [l for l in dirty.splitlines() if not l.startswith('??')]
        if dirty:
            sys.exit('refusing: uncommitted changes in live files:\n  ' + '\n  '.join(dirty))

# 4. write + record
for p, t in out.items():
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t)
MANIFEST.write_text(json.dumps({rel(p): digest(p) for p in out}, indent=1))

# 5. sanity: no mockup-relative paths left
bad = []
for p in out:
    if p.suffix != '.html':
        continue
    t = p.read_text()
    bad += [f'{rel(p)}: {m}' for m in re.findall(r'(?:href|src)="(?:\.\./)*i\.(?:css|js)"', t)]
    bad += [f'{rel(p)}: mockup path' for _ in re.findall(r'mockup-[a-z]/', t)]
    if p.parent == ROOT:
        bad += [f'{rel(p)}: ../ path' for _ in re.findall(r'(?:href|src)="\.\./(?!styles)', t)]
    else:
        bad += [f'{rel(p)}: ../../ path' for _ in re.findall(r'(?:href|src)="\.\./\.\./', t)]
print('promoted I; fingerprints in themed/.promoted-i.json; leftovers:', bad or 'none')
