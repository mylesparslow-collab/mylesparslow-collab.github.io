"""Add the style-switcher script tag to every page of every portfolio version (idempotent).
Each render_*.py runs this at its end, and so does promote_i.py (via render_i.py).
Run by hand: python3 -I themed/add_switcher.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ['index.html'] + [f'{r}/index.html' for r in ['legal', 'business', 'creative', 'design', 'research']]
DIRS = {k: ROOT / f'mockup-{k}' for k in 'bcdefghi'}


def tag(k):
    return f'<script src="/assets/site/styles.js" data-v="{k}" defer></script>'


def run(keys=None):
    n = 0
    for k, d in DIRS.items():
        if keys and k not in keys:
            continue
        for p in PAGES:
            f = d / p
            if not f.exists():
                continue
            t = f.read_text()
            if 'assets/site/styles.js' in t:
                continue
            assert '</head>' in t, f'no </head> in {f}'
            f.write_text(t.replace('</head>', tag(k) + '\n</head>', 1))
            n += 1
    return n


if __name__ == '__main__':
    print('style switcher added to', run(), 'pages')
