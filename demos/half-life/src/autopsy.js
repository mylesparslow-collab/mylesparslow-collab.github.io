const NS = 'http://www.w3.org/2000/svg';
const LAST_YEAR = 2014;

function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const k in attrs || {}) {
    if (k === 'class') e.className = attrs[k];
    else if (k === 'style') e.style.cssText = attrs[k];
    else e.setAttribute(k, attrs[k]);
  }
  for (const c of kids) if (c != null) e.append(c);
  return e;
}
function s(tag, attrs, ...kids) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
  for (const c of kids) if (c != null) e.append(c);
  return e;
}
const fmt = (n) => n.toLocaleString('en-US');

const CSS = `
.au { position: relative; }
.au-search { position: relative; max-width: 420px; margin-bottom: 24px; }
.au-search input { width: 100%; font: 16px var(--font-sans); color: var(--ink); background: var(--bg-2); border: 1px solid var(--line); border-radius: 6px; padding: 10px 12px; }
.au-search input:focus-visible { outline: 2px solid var(--ember); outline-offset: 1px; }
.au-list { list-style: none; margin: 4px 0 0; padding: 0; position: absolute; left: 0; right: 0; z-index: 5; background: var(--bg); border: 1px solid var(--line); border-radius: 6px; max-height: 340px; overflow: auto; }
.au-list:empty { display: none; }
.au-list li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 12px; cursor: pointer; font-size: 15px; border-bottom: 1px solid var(--line); }
.au-list li:last-child { border-bottom: 0; }
.au-list li[aria-selected="true"] { background: var(--bg-2); box-shadow: inset 3px 0 0 var(--ember); }
.au-list li span:last-child { font-family: var(--font-mono); font-size: 12px; color: var(--muted); white-space: nowrap; align-self: center; }
.au-name { font-size: clamp(28px, 6vw, 56px); line-height: 1.05; letter-spacing: -.02em; font-weight: 800; margin: 0 0 8px; overflow-wrap: anywhere; }
.au-sub { font-family: var(--font-mono); color: var(--muted); font-size: 14px; margin: 0 0 24px; }
.au-stats { display: flex; flex-wrap: wrap; gap: 20px 48px; margin: 0 0 40px; }
.au-stat b { display: block; font-family: var(--font-mono); font-weight: 600; font-size: clamp(28px, 6vw, 48px); line-height: 1.1; font-variant-numeric: tabular-nums; }
.au-stat span { font-size: 13px; color: var(--muted); }
.au h3 { font-size: 16px; margin: 0 0 4px; font-weight: 700; }
.au-cap { font-size: 13px; color: var(--muted); margin: 0 0 12px; max-width: 70ch; }
.au-block { margin-bottom: 40px; }
.au-chart svg { display: block; width: 100%; height: auto; overflow: visible; }
.au-chart text, .au-heat text { font-family: var(--font-mono); fill: var(--muted); }
.au-scroll { overflow-x: auto; max-width: 100%; border: 1px solid var(--line); border-radius: 6px; padding: 8px; background: var(--bg); }
.au-scroll svg { display: block; }
.au-none { color: var(--muted); font-size: 15px; }
.au-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 12px; }
.au-tabs button { font: 13px var(--font-mono); color: var(--ink); background: var(--bg-2); border: 1px solid var(--line); border-radius: 6px; padding: 6px 10px; cursor: pointer; }
.au-tabs button[aria-selected="true"] { border-color: var(--accent); box-shadow: inset 0 -2px 0 var(--accent); }
.au-tabs button:focus-visible { outline: 2px solid var(--ember); outline-offset: 1px; }
.au-page { max-width: 65ch; font-family: var(--font-sans); font-size: 16px; line-height: 1.6; white-space: pre-wrap; overflow-wrap: anywhere; background: var(--bg-2); border-left: 3px solid var(--accent); padding: 12px 16px; margin: 0; }
`;

export function mountAutopsy(el, data) {
  if (!document.getElementById('au-css')) {
    const st = document.createElement('style');
    st.id = 'au-css';
    st.textContent = CSS;
    document.head.append(st);
  }
  const rows = data.cases.cases;
  const start = rows.find((r) => r[3] === '384 U.S. 436');
  let cur = start || rows[0];
  let token = 0;
  let lastW = 0;

  const root = h('div', { class: 'au' });
  const input = h('input', {
    type: 'search', placeholder: 'Search a case by name', 'aria-label': 'Search cases by name',
    autocomplete: 'off', role: 'combobox', 'aria-expanded': 'false', 'aria-controls': 'au-results',
    'aria-autocomplete': 'list',
  });
  const list = h('ul', { class: 'au-list', id: 'au-results', role: 'listbox' });
  const search = h('div', { class: 'au-search' }, input, list);
  const body = h('div', { class: 'au-body' });
  root.append(search, body);
  el.append(root);

  /* ---------- search ---------- */
  let results = [];
  let active = -1;
  function paintList() {
    list.replaceChildren();
    results.forEach((r, i) => {
      const li = h('li', { role: 'option', id: `au-opt-${i}`, 'aria-selected': String(i === active) },
        h('span', {}, r[1]), h('span', {}, `${r[2]} · ${fmt(r[4])}`));
      li.addEventListener('mousedown', (e) => { e.preventDefault(); choose(r); });
      list.append(li);
    });
    input.setAttribute('aria-expanded', String(results.length > 0));
    if (active >= 0 && results[active]) input.setAttribute('aria-activedescendant', `au-opt-${active}`);
    else input.removeAttribute('aria-activedescendant');
  }
  function choose(r) {
    results = []; active = -1; paintList();
    input.value = '';
    window.dispatchEvent(new CustomEvent('hl:select', { detail: { id: r[0], from: 'autopsy' } }));
  }
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    results = q
      ? rows.filter((r) => r[1].toLowerCase().includes(q)).sort((a, b) => b[4] - a[4]).slice(0, 8)
      : [];
    active = results.length ? 0 : -1;
    paintList();
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' && results.length) { e.preventDefault(); active = (active + 1) % results.length; paintList(); }
    else if (e.key === 'ArrowUp' && results.length) { e.preventDefault(); active = (active - 1 + results.length) % results.length; paintList(); }
    else if (e.key === 'Enter' && results[active]) { e.preventDefault(); choose(results[active]); }
    else if (e.key === 'Escape') { results = []; active = -1; paintList(); }
  });
  input.addEventListener('blur', () => { results = []; active = -1; paintList(); });

  /* ---------- chart A ---------- */
  function chartA(c) {
    const [, , year, , total, hl, py] = c;
    const box = h('div', { class: 'au-chart' });
    const draw = () => {
      const W = Math.max(280, Math.round(box.clientWidth || el.clientWidth || 600));
      const H = Math.round(Math.min(280, Math.max(190, W * 0.32)));
      const m = { l: 34, r: 8, t: 22, b: 24 };
      const y0 = year, y1 = Math.max(LAST_YEAR, year);
      const n = y1 - y0 + 1;
      const counts = new Array(n).fill(0);
      let max = 1;
      for (let i = 0; i < py.length; i += 2) {
        const k = py[i] - y0;
        if (k >= 0 && k < n) { counts[k] = py[i + 1]; if (py[i + 1] > max) max = py[i + 1]; }
      }
      const iw = W - m.l - m.r, ih = H - m.t - m.b;
      const bw = iw / n;
      const X = (y) => m.l + (y - y0) * bw;
      const Y = (v) => m.t + ih - (v / max) * ih;
      const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `Citations per year for ${c[1]}, ${y0} to ${y1}` });
      svg.append(s('line', { x1: m.l, x2: W - m.r, y1: m.t + ih, y2: m.t + ih, stroke: 'var(--line)' }));
      svg.append(s('text', { x: m.l - 6, y: m.t + 4, 'text-anchor': 'end', 'font-size': 10 }, String(max)));
      svg.append(s('text', { x: m.l - 6, y: m.t + ih, 'text-anchor': 'end', 'font-size': 10 }, '0'));
      counts.forEach((v, i) => {
        if (!v) return;
        const t = s('rect', { x: (m.l + i * bw).toFixed(2), y: Y(v).toFixed(2), width: Math.max(0.6, bw - (bw > 3 ? 0.8 : 0)).toFixed(2), height: (m.t + ih - Y(v)).toFixed(2), fill: 'var(--ember)' });
        t.append(s('title', {}, `${y0 + i}: ${v} citation${v === 1 ? '' : 's'}`));
        svg.append(t);
      });
      const step = W < 480 ? 50 : (y1 - y0 > 120 ? 20 : 10);
      for (let y = Math.ceil(y0 / step) * step; y <= y1; y += step) {
        const x = X(y) + bw / 2;
        svg.append(s('line', { x1: x, x2: x, y1: m.t + ih, y2: m.t + ih + 4, stroke: 'var(--muted)' }));
        svg.append(s('text', { x, y: H - 6, 'text-anchor': 'middle', 'font-size': 10 }, String(y)));
      }
      if (hl != null) {
        const mx = Math.min(W - m.r, X(year + hl) + bw / 2);
        svg.append(s('line', { x1: mx, x2: mx, y1: m.t - 6, y2: m.t + ih, stroke: 'var(--accent)', 'stroke-width': 1.5, 'stroke-dasharray': '4 3' }));
        const right = mx - m.l > W - m.r - mx;
        const lab = s('text', { x: right ? mx - 6 : mx + 6, y: m.t + 4, 'text-anchor': right ? 'end' : 'start', 'font-size': 11, style: 'fill:var(--ink)' });
        const l1 = s('tspan', { x: right ? mx - 6 : mx + 6 }, `${Math.round(year + hl)}`);
        const l2 = s('tspan', { x: right ? mx - 6 : mx + 6, dy: 13 }, 'half of its citations');
        const l3 = s('tspan', { x: right ? mx - 6 : mx + 6, dy: 13 }, 'came before this');
        lab.append(l1, l2, l3);
        svg.append(lab);
      }
      box.replaceChildren(svg);
      lastW = box.clientWidth;
    };
    box._draw = draw;
    return box;
  }

  /* ---------- chart B ---------- */
  function chartB(c, pg) {
    const wrap = h('div', { class: 'au-scroll au-heat' });
    const { first, last, pins } = pg;
    const nRows = Math.max(1, last - first + 1);
    const decs = pins.map((p) => p[1]);
    const dMin = decs.length ? Math.min(...decs) : Math.floor(c[2] / 10) * 10;
    const dMax = 2010;
    const nCols = Math.max(1, (dMax - dMin) / 10 + 1);
    const grid = new Map();
    const rowTot = new Array(nRows).fill(0);
    let max = 1;
    for (const [p, d, n] of pins) {
      const r = p - first;
      if (r < 0 || r >= nRows) continue;
      const k = r + ':' + d;
      const v = (grid.get(k) || 0) + n;
      grid.set(k, v);
      rowTot[r] += n;
      if (v > max) max = v;
    }
    const rh = nRows > 80 ? 3 : Math.max(6, Math.min(18, Math.floor(420 / nRows)));
    const labW = 52, totW = 44, gap = 4, top = 18;
    const avail = (el.clientWidth || 360) - 18;
    const cw = Math.max(30, Math.min(96, Math.floor((avail - labW - totW - 8) / nCols)));
    const W = labW + nCols * cw + totW + 8;
    const H = top + nRows * rh + 2;
    const svg = s('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': `Pin-cite heatmap for ${c[1]}` });
    const mix = (t) => (t < 0.5
      ? `color-mix(in srgb, var(--ember-2) ${Math.round(t * 200)}%, var(--bg-2))`
      : `color-mix(in srgb, var(--ember) ${Math.round((t - 0.5) * 200)}%, var(--ember-2))`);
    for (let j = 0; j < nCols; j++) {
      if (nCols > 9 && j % 2) continue;
      const t = s('text', { x: labW + j * cw + cw / 2, y: 11, 'text-anchor': 'middle', 'font-size': 9 }, String(dMin + j * 10));
      svg.append(t);
    }
    svg.append(s('text', { x: W - 4, y: 11, 'text-anchor': 'end', 'font-size': 9 }, 'total'));
    const every = rh >= 10 ? 1 : (rh >= 6 ? 2 : 5);
    for (let r = 0; r < nRows; r++) {
      const y = top + r * rh;
      const page = first + r;
      if (rh >= 5 ? r % every === 0 : r % 10 === 0) {
        svg.append(s('text', { x: labW - 6, y: y + Math.min(rh, 10) - 1, 'text-anchor': 'end', 'font-size': rh >= 5 ? Math.min(10, rh + 2) : 8 }, `p. ${page}`));
      }
      for (let j = 0; j < nCols; j++) {
        const d = dMin + j * 10;
        const v = grid.get(r + ':' + d) || 0;
        const rect = s('rect', { x: labW + j * cw, y, width: cw - 1, height: Math.max(1, rh - (rh > 4 ? 1 : 0)), fill: v ? mix(Math.sqrt(v / max)) : 'var(--bg-2)' });
        rect.append(s('title', {}, `p. ${page}, ${d}s: ${v} pin cite${v === 1 ? '' : 's'}`));
        svg.append(rect);
      }
      if (rowTot[r] && (rh >= 6 || r % every === 0)) {
        svg.append(s('text', { x: W - 4 - gap + gap, y: y + Math.min(rh, 10) - 1, 'text-anchor': 'end', 'font-size': Math.min(10, rh + 2) }, String(rowTot[r])));
      }
    }
    wrap.append(svg);
    return wrap;
  }

  /* ---------- hottest pages ---------- */
  function textBlock(t) {
    const pages = t && t.pages ? t.pages : null;
    if (!pages) return null;
    const ent = Object.entries(pages).filter(([, v]) => v);
    if (!ent.length) return null;
    return ent;
  }
  function fillText(host, c, t) {
    const ent = textBlock(t);
    if (!ent) { host.hidden = true; return; }
    const pg = data.pages && data.pages[c[0]];
    const cnt = {};
    if (pg) for (const [p, , n] of pg.pins) cnt[p] = (cnt[p] || 0) + n;
    const items = ent.map(([p, v]) => [p, v, cnt[p]]).sort((a, b) => (b[2] || 0) - (a[2] || 0)).slice(0, 3);
    host.hidden = false;
    const tabs = h('div', { class: 'au-tabs', role: 'tablist' });
    const pre = h('p', { class: 'au-page', role: 'tabpanel' });
    const btns = items.map(([p, v, n], i) => {
      const b = h('button', { type: 'button', role: 'tab', 'aria-selected': 'false' }, n ? `p. ${p} · ${fmt(n)} cites` : `p. ${p}`);
      b.addEventListener('click', () => show(i));
      tabs.append(b);
      return b;
    });
    function show(i) {
      btns.forEach((b, k) => b.setAttribute('aria-selected', String(k === i)));
      pre.textContent = items[i][1];
    }
    show(0);
    host.append(h('h3', {}, 'The hottest pages'), h('p', { class: 'au-cap' }, 'Excerpts of the pages later opinions pin-cited most, from scanned volumes (older pages carry OCR errors).'), tabs, pre);
  }

  /* ---------- render ---------- */
  function render(c) {
    cur = c;
    const my = ++token;
    const [, name, year, cite, total, hl, py] = c;
    let last = year;
    for (let i = 0; i < py.length; i += 2) if (py[i] > last) last = py[i];
    body.replaceChildren();
    body.append(
      h('h3', { class: 'au-name', style: 'font-size:clamp(28px,6vw,56px);margin:0 0 8px' }, name),
      h('p', { class: 'au-sub' }, `${cite} · decided ${year}`),
      h('div', { class: 'au-stats' },
        h('div', { class: 'au-stat' }, h('b', {}, fmt(total)), h('span', {}, 'total citations')),
        h('div', { class: 'au-stat' }, h('b', {}, hl == null ? '—' : String(hl)), h('span', {}, 'half-life: median citation age, years')),
        h('div', { class: 'au-stat' }, h('b', {}, String(last)), h('span', {}, 'last year cited'))),
    );
    const a = h('div', { class: 'au-block' }, h('h3', {}, 'Citations per year'),
      h('p', { class: 'au-cap' }, 'How many later U.S. Reports opinions cited this ruling, year by year.'));
    const ca = chartA(c);
    a.append(ca);
    body.append(a);
    ca._draw();

    const pg = data.pages && data.pages[c[0]];
    const b = h('div', { class: 'au-block' }, h('h3', {}, 'Which pages became law'));
    if (pg && !pg.pins.length) {
      b.append(h('p', { class: 'au-none' }, 'No later opinion pin-cited a specific page of this ruling.'));
    } else if (pg) {
      b.append(
        h('p', { class: 'au-cap' }, 'A pin cite points a later opinion at one page of the ruling. Each row is a page, each column a decade; empty rows were never pin-cited.'),
        chartB(c, pg));
    } else {
      b.append(h('p', { class: 'au-none' }, 'Fewer than 25 later citations, so no page map.'));
    }
    body.append(b);

    const tb = h('div', { class: 'au-block' });
    tb.hidden = true;
    body.append(tb);
    Promise.resolve(data.textIds && !data.textIds.has(c[0]) ? null : data.loadText(c[0])).then((t) => {
      if (my === token) fillText(tb, c, t);
    }).catch(() => {});
  }

  window.addEventListener('hl:select', (e) => {
    const id = e.detail && e.detail.id;
    const c = data.byId.get(id) || data.byId.get(Number(id));
    if (!c) return;
    render(c);
    if (!(e.detail && e.detail.from === 'autopsy')) {
      const reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    }
  });

  let rt;
  window.addEventListener('resize', () => {
    clearTimeout(rt);
    rt = setTimeout(() => {
      const ca = body.querySelector('.au-chart');
      if (ca && ca._draw && ca.clientWidth !== lastW) ca._draw();
    }, 100);
  });

  render(cur);
}
