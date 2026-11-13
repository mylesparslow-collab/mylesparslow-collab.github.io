#!/usr/bin/env python3
"""Re-render every alternate style from live.json, then add the style switcher.

    python3 -I themed/render_all.py

Runs render_b, c, d, e, f, g, h and render_styles in order (each as a subprocess), then
add_switcher. Exits non-zero if any step fails. Does NOT run render_i.py or promote_i.py:
those publish the live site (Transit Map) and are run separately.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ['render_b', 'render_c', 'render_d', 'render_e', 'render_f', 'render_g', 'render_h',
         'render_styles', 'add_switcher']


def main():
    failed = []
    for name in STEPS:
        print('==', name, flush=True)
        r = subprocess.run([sys.executable, '-I', str(HERE / (name + '.py'))], cwd=str(HERE.parent))
        if r.returncode:
            print('!! %s failed (exit %d)' % (name, r.returncode), flush=True)
            failed.append(name)
    print()
    print('Reminder: the live site (root + room pages, Transit Map) is NOT rebuilt here.')
    print('For that: python3 -I themed/render_i.py && python3 -I themed/promote_i.py')
    if failed:
        print('FAILED: ' + ', '.join(failed))
        return 1
    print('all %d steps ok' % len(STEPS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
