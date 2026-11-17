#!/usr/bin/env python3
"""Rebuild every version of the site from themed/live.json, in one command.

    python3 -I themed/build.py

1. normalize_live.py  renumber cases and rooms from their order in live.json
2. render_i.py        the Transit Map (the live site) into mockup-i/
3. promote_i.py       copy it to the site root (index.html, <room>/index.html, assets/site/i.*)
4. render_all.py      every other style in the Style dropdown, the styles/ archive page,
                      the style switcher and the shared features (flagship stars, Start-here
                      routes; see add_shared.py)

The GitHub workflow .github/workflows/render-site.yml runs this on every pull request and
push to main that touches themed/, and commits whatever it changes, so all styles stay in
step even if a step is forgotten locally. Pass extra flags (e.g. --force) on to promote_i.py.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [['normalize_live.py'], ['render_i.py'], ['promote_i.py'] + sys.argv[1:], ['render_all.py']]


def main():
    for step in STEPS:
        print('==>', ' '.join(step), flush=True)
        r = subprocess.run([sys.executable, '-I', str(HERE / step[0])] + step[1:], cwd=str(HERE.parent))
        if r.returncode:
            print('!! %s failed (exit %d); stopping' % (step[0], r.returncode), flush=True)
            return r.returncode
    print('all versions rebuilt from live.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
