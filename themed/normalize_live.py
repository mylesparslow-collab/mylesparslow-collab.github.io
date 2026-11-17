"""Recompute the numbering stored in themed/live.json from the order of the items (idempotent).

Every case carries `count` ("07 / 29") and every room `count` ("29 projects") and
`eyebrow` ("Room 1 of 5"). Several styles print these as they are, so after a project is
added, removed or moved they must be renumbered. build.py runs this first.
Run by hand: python3 -I themed/normalize_live.py
"""
import json
import re
from pathlib import Path

LIVE = Path(__file__).resolve().parent / 'live.json'


def run():
    raw = LIVE.read_text(encoding='utf-8')
    d = json.loads(raw)
    rooms = d['rooms']
    for ri, r in enumerate(rooms):
        cases = [it for it in r['items'] if it['kind'] == 'case']
        for k, it in enumerate(cases):
            it['count'] = '%02d / %02d' % (k + 1, len(cases))
        r['count'] = re.sub(r'^\d+', str(len(cases)), r['count'])
        r['eyebrow'] = re.sub(r'Room \d+ of \d+', 'Room %d of %d' % (ri + 1, len(rooms)), r['eyebrow'])
    out = json.dumps(d, ensure_ascii=False, indent=1)
    changed = out != raw
    if changed:
        LIVE.write_text(out, encoding='utf-8')
    return changed


if __name__ == '__main__':
    print('live.json renumbered' if run() else 'live.json numbering already current')
