const NS = 'http://www.w3.org/2000/svg';
const CSS = `
.hl-ledger { display: block; }
.hl-ledger .blk { margin: 0 0 40px; min-width: 0; }
.hl-ledger h3 { font-family: var(--font-sans); font-size: 20px; font-weight: 700; margin: 0 0 4px; letter-spacing: -.01em; }
.hl-ledger .lede { color: var(--muted); font-size: 15px; margin: 0 0 16px; max-width: 62ch; }
.hl-ledger .num { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.hl-ledger svg { display: block; max-width: 100%; }
.hl-ledger svg text { fill: var(--muted); font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.hl-ledger .note { color: var(--muted); font-size: 12px; line-height: 1.5; margin: 12px 0 0; max-width: 80ch; }
.hl-ledger .legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 12px; color: var(--muted); margin: 8px 0 0; }
.hl-ledger .legend i { display: inline-block; width: 10px; height: 10px; margin-right: 6px; vertical-align: -1px; }
.hl-ledger .row { display: grid; align-items: center; gap: 4px 12px; padding: 10px 0; border-top: 1px solid var(--line); cursor: pointer; color: var(--ink); }
.hl-ledger .row:last-child { border-bottom: 1px solid var(--line); }
.hl-ledger .row:focus-visible { outline: 2px solid var(--ember); outline-offset: 2px; }
.hl-ledger .sd { grid-template-columns: minmax(0, 1fr) 120px; }
.hl-ledger .sd .nm, .hl-ledger .im .nm, .hl-ledger .oc .nm { font-size: 14px; font-weight: 500; overflow-wrap: anywhere; }
.hl-ledger .sd .meta { grid-column: 1 / -1; grid-row: 2; font-size: 12px; color: var(--muted); }
.hl-ledger .sd svg { grid-column: 2; grid-row: 1; }
.hl-ledger .im { grid-template-columns: minmax(0, 1fr); gap: 2px; padding: 8px 0; }
.hl-ledger .im .nm { display: flex; justify-content: space-between; gap: 12px; }
.hl-ledger .im .span { color: var(--muted); font-size: 12px; white-space: nowrap; }
.hl-ledger .oc { grid-template-columns: minmax(0, 1fr) auto; }
.hl-ledger .oc .n { font-size: 14px; color: var(--ember); }
@media (min-width: 720px) {
  .hl-ledger .sd { grid-template-columns: minmax(0, 1fr) 220px 120px; }
  .hl-ledger .sd .meta { grid-column: 2; grid-row: 1; text-align: right; }
  .hl-ledger .sd svg { grid-column: 3; }
}
`;

const el_ = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};
const svg_ = (tag, attrs, text) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  return e;
};
const select = (id) => window.dispatchEvent(new CustomEvent('hl:select', { detail: { id } }));
function rowButton(row, id) {
  row.tabIndex = 0;
  row.setAttribute('role', 'button');
  row.addEventListener('click', () => select(id));
  row.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(id); }
  });
}
function block(root, title, lede) {
  const b = el_('div', 'blk');
  b.append(el_('h3', null, title), el_('p', 'lede', lede));
  root.append(b);
  return b;
}
const yearsOf = (row) => {
  const py = row ? row[6] : null;
  return py && py.length ? { first: py[0], last: py[py.length - 2] } : null;
};

function drawDecades(host, rows) {
  host.textContent = '';
  const W = Math.max(280, Math.floor(host.clientWidth || 320));
  const H = 230, top = 12, bot = 48, left = 30;
  const plotH = H - top - bot, plotW = W - left;
  const yMax = Math.ceil(Math.max(...rows.map((r) => r[1])) / 20) * 20;
  const colW = plotW / rows.length;
  const barW = Math.max(6, colW * 0.7);
  const narrow = colW < 26;
  const base = top + plotH;
  const s = svg_('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Median age of citations within 30 years, by decade of decision' });
  for (let v = 0; v <= yMax; v += yMax <= 40 ? 10 : 20) {
    const y = base - (v / yMax) * plotH;
    s.append(svg_('line', { x1: left, x2: W, y1: y, y2: y, stroke: 'var(--line)', 'stroke-width': 1 }));
    s.append(svg_('text', { x: left - 4, y: y + 3, 'text-anchor': 'end', 'font-size': 9 }, v));
  }
  rows.forEach(([dec, med, n], i) => {
    const h = (med / yMax) * plotH;
    const r = svg_('rect', { x: left + i * colW + (colW - barW) / 2, y: base - h, width: barW, height: h, fill: 'var(--ember)' });
    if (n < 30) r.setAttribute('fill-opacity', '.4');
    r.append(svg_('title', {}, `${dec}s: median ${med} years, n=${n}`));
    s.append(r);
    const cx = left + i * colW + colW / 2;
    if (!narrow || i % 2 === 0) s.append(svg_('text', { x: cx, y: base + 12, 'text-anchor': 'middle', 'font-size': 9 }, narrow ? `'${String(dec).slice(2)}` : dec));
    if (narrow) {
      s.append(svg_('text', { x: cx + 3, y: base + 16, 'text-anchor': 'end', 'font-size': 8, transform: `rotate(-90 ${cx + 3} ${base + 16})` }, n));
    } else {
      s.append(svg_('text', { x: cx, y: base + 26, 'text-anchor': 'middle', 'font-size': 8 }, n));
    }
  });
  host.append(s);
}

function drawImmortals(host, rows, byId) {
  host.textContent = '';
  const W = Math.max(280, Math.floor(host.clientWidth || 320));
  const A0 = 1790, A1 = 2014, H = 14, pad = 6;
  const X = (y) => pad + ((y - A0) / (A1 - A0)) * (W - 2 * pad);
  const ax = svg_('svg', { width: W, height: 14, viewBox: `0 0 ${W} 14`, 'aria-hidden': 'true' });
  for (const y of [1800, 1850, 1900, 1950, 2000]) {
    ax.append(svg_('text', { x: X(y), y: 10, 'text-anchor': 'middle', 'font-size': 9 }, y));
  }
  host.append(ax);
  rows.forEach(([id, name, year]) => {
    const yrs = yearsOf(byId.get(id));
    if (!yrs) return;
    const row = el_('div', 'row im');
    const nm = el_('div', 'nm');
    nm.append(el_('span', null, `${name} (${year})`), el_('span', 'span num', `${yrs.first}–${yrs.last} · ${yrs.last - yrs.first} yrs`));
    const s = svg_('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' });
    s.append(svg_('line', { x1: pad, x2: W - pad, y1: H / 2, y2: H / 2, stroke: 'var(--line)', 'stroke-width': 1 }));
    s.append(svg_('rect', { x: X(yrs.first), y: 3, width: Math.max(2, X(yrs.last) - X(yrs.first)), height: H - 6, fill: 'var(--ember)', 'fill-opacity': '.75' }));
    s.append(svg_('circle', { cx: X(year), cy: H / 2, r: 3.5, fill: 'var(--accent)' }));
    row.append(nm, s);
    row.setAttribute('aria-label', `${name}, decided ${year}, cited ${yrs.first} to ${yrs.last}`);
    rowButton(row, id);
    host.append(row);
  });
}

function sparkline(perYear, death) {
  const w = 120, h = 24;
  const y0 = perYear[0], y1 = Math.max(death, perYear[perYear.length - 2]);
  const span = Math.max(1, y1 - y0);
  let mx = 1;
  for (let i = 1; i < perYear.length; i += 2) mx = Math.max(mx, perYear[i]);
  const X = (y) => 3 + ((y - y0) / span) * (w - 6);
  const s = svg_('svg', { width: w, height: h, viewBox: `0 0 ${w} ${h}`, 'aria-hidden': 'true' });
  s.append(svg_('line', { x1: 0, x2: w, y1: h - 1, y2: h - 1, stroke: 'var(--line)', 'stroke-width': 1 }));
  for (let i = 0; i < perYear.length; i += 2) {
    const bh = Math.max(1, (perYear[i + 1] / mx) * (h - 4));
    s.append(svg_('rect', { x: X(perYear[i]) - 0.75, y: h - 1 - bh, width: 1.5, height: bh, fill: 'var(--ember)' }));
  }
  s.append(svg_('line', { x1: X(death), x2: X(death), y1: 0, y2: h, stroke: 'var(--accent)', 'stroke-width': 1, 'stroke-dasharray': '2 2' }));
  s.append(svg_('circle', { cx: X(death), cy: h - 1, r: 2.5, fill: 'var(--accent)' }));
  return s;
}

export function mountLedger(el, data) {
  const { ledger, byId } = data;
  if (!document.getElementById('hl-ledger-style')) {
    const st = el_('style', null, CSS);
    st.id = 'hl-ledger-style';
    document.head.append(st);
  }
  const root = el_('div', 'hl-ledger');
  el.append(root);

  // 1. byDecade
  const b1 = block(root, 'Is precedent dying faster?', 'It did, then stopped. Counting only each ruling\u2019s first 30 years of citations, the Court cited 1860s rulings a median of about 21 years after they came down. By the 1900s that had fallen to about 9, and it has stayed between 7 and 12 since.');
  const chart = el_('div');
  b1.append(chart);
  const lg = el_('div', 'legend');
  const k1 = el_('span');
  const i1 = el_('i');
  i1.style.background = 'var(--ember)';
  k1.append(i1, 'Median age of citations in a ruling\u2019s first 30 years (n = rulings, under each column)');
  const k2 = el_('span');
  const i2 = el_('i');
  i2.style.background = 'var(--ember)';
  i2.style.opacity = '.4';
  k2.append(i2, 'Fewer than 30 rulings that decade');
  lg.append(k1, k2);
  b1.append(lg, el_('p', 'note', ledger.notes));

  // 2. sudden deaths
  const b2 = block(root, 'Sudden deaths', 'Cited steadily, then never again; often a sign the ruling was overruled or overtaken.');
  const list2 = el_('div');
  ledger.suddenDeaths.forEach(([id, name, year, total, last]) => {
    const row = el_('div', 'row sd');
    row.append(el_('div', 'nm', name), el_('div', 'meta num', `${year} · ${total} cites · last ${last}`));
    const c = byId.get(id);
    if (c && c[6] && c[6].length) row.append(sparkline(c[6], last));
    row.setAttribute('aria-label', `${name}, decided ${year}, ${total} citations, last cited ${last}`);
    rowButton(row, id);
    list2.append(row);
  });
  b2.append(list2);

  // 3. immortals
  const b3 = block(root, 'The immortals', 'Rulings still being cited two centuries on. Each bar runs from first to last citing year; the dot is the year it was decided.');
  const host3 = el_('div');
  b3.append(host3);

  // 4. order cites
  const b4 = block(root, 'Cited mostly by one-page orders', 'These rulings are cited in one-page orders, such as routine denials of fee waivers for repeat filers (Martin v. District of Columbia Court of Appeals). Those orders are excluded from every total on this page; the counts below are what was left out.');
  const list4 = el_('div');
  ledger.orderCites.forEach(([id, name, n]) => {
    const row = el_('div', 'row oc');
    row.append(el_('div', 'nm', name), el_('div', 'n num', String(n)));
    row.setAttribute('aria-label', `${name}, ${n} citations from one-page orders`);
    rowButton(row, id);
    list4.append(row);
  });
  b4.append(list4);

  const render = () => {
    drawDecades(chart, ledger.byDecade);
    host3.textContent = '';
    drawImmortals(host3, ledger.immortals.slice(0, 15), byId);
  };
  render();
  let w = chart.clientWidth;
  if (typeof ResizeObserver === 'function') {
    new ResizeObserver(() => {
      const nw = chart.clientWidth;
      if (nw && nw !== w) { w = nw; render(); }
    }).observe(root);
  }
}
