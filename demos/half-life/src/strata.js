// The strata: every opinion as a point, played through time.
// x = decision year, y = log(1 + citations received so far), colour = recent-citation heat.

const Y0 = 1790;
const Y1 = 2014;
const NY = Y1 - Y0 + 1;
const HALF_LIFE_HEAT = 4;
const DECAY = Math.pow(0.5, 1 / HALF_LIFE_HEAT);
const SECONDS_FULL = 45;
const NB = 12; // heat buckets; 0 = dust (nothing cited yet)
const TOP_LABELS = 4;

const CSS = `
.hl-strata{position:relative;font-family:var(--font-sans);color:var(--ink)}
.hl-stage{position:relative;width:100%;height:clamp(380px,65vh,720px)}
.hl-stage canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:pan-y}
.hl-tip{position:absolute;pointer-events:none;z-index:2;max-width:260px;padding:6px 9px;background:var(--bg-2);color:var(--ink);border:1px solid var(--line);font-size:12px;line-height:1.35;display:none}
.hl-tip b{display:block;font-weight:600}
.hl-tip span{color:var(--muted)}
.hl-caption{margin:10px 0 0;min-height:1.5em;font-size:14px;color:var(--muted)}
.hl-controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px 12px;margin-top:10px}
.hl-controls button{font:inherit;font-size:13px;font-family:var(--font-sans);color:var(--ink);background:transparent;border:1px solid var(--line);padding:6px 14px;cursor:pointer;min-width:64px}
.hl-controls button:focus-visible,.hl-controls input:focus-visible{outline:2px solid var(--ember);outline-offset:2px}
.hl-controls input[type=range]{flex:1 1 200px;min-width:0;accent-color:var(--ember)}
`;

function parseColor(ctx, c, fallback) {
  try {
    ctx.fillStyle = '#000';
    ctx.fillStyle = c || fallback;
    const s = ctx.fillStyle;
    if (s[0] === '#') {
      return [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16)];
    }
    const m = s.match(/[\d.]+/g);
    return [+m[0], +m[1], +m[2]];
  } catch (e) {
    return [128, 128, 128];
  }
}

const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;

export function mountStrata(el, data) {
  const rowsIn = data.cases.cases;
  const N = rowsIn.length;

  // ---- precompute: sort by (clamped) year, then per-year cumulative log-y and heat ----
  const order = rowsIn.map((r, i) => i).sort((a, b) => rowsIn[a][2] - rowsIn[b][2]);
  const rows = new Array(N);
  const yr = new Uint16Array(N);
  const logy = new Float32Array(N * NY);
  const heat16 = new Uint16Array(N * NY);
  const yearCount = new Uint16Array(NY);
  const yearTop = new Int32Array(NY).fill(-1);
  const yearTopN = new Uint16Array(NY);
  const rawHeat = new Float32Array(N * NY);
  let maxLog = 1;
  let maxHeat = 1;
  const nPerYear = new Float32Array(NY);
  for (let s = 0; s < N; s++) {
    const r = rowsIn[order[s]];
    rows[s] = r;
    yr[s] = Math.min(Y1, Math.max(Y0, r[2]));
    const py = r[6];
    nPerYear.fill(0);
    for (let j = 0; j < py.length; j += 2) {
      const k = Math.min(NY - 1, Math.max(0, py[j] - Y0));
      nPerYear[k] += py[j + 1];
    }
    let cum = 0;
    let h = 0;
    // small fixed per-case offset so low integer counts don't stack into hard bands
    const jit = (((Math.imul(r[0], 2654435761) >>> 0) / 4294967296) - 0.5) * 0.9;
    for (let k = 0; k < NY; k++) {
      const n = nPerYear[k];
      cum += n;
      h = h * DECAY + n;
      logy[k * N + s] = Math.log1p(cum > 0 ? cum + jit : 0);
      rawHeat[k * N + s] = h;
      if (h > maxHeat) maxHeat = h;
      if (n > 0) {
        yearCount[k]++;
        if (n > yearTopN[k]) { yearTopN[k] = n; yearTop[k] = s; }
      }
    }
    if (logy[(NY - 1) * N + s] > maxLog) maxLog = logy[(NY - 1) * N + s];
  }
  const hScale = 65535 / maxHeat;
  for (let i = 0; i < rawHeat.length; i++) heat16[i] = rawHeat[i] * hScale;
  const idToIdx = new Map();
  for (let s = 0; s < N; s++) idToIdx.set(rows[s][0], s);
  // first sorted index with year > y, for early exit
  const yearEnd = new Int32Array(NY + 1);
  {
    let s = 0;
    for (let k = 0; k < NY; k++) {
      while (s < N && yr[s] <= Y0 + k) s++;
      yearEnd[k] = s;
    }
  }
  const bucketOf = new Uint8Array(4096); // heat16 >> 4 -> bucket
  for (let q = 0; q < 4096; q++) {
    const t = Math.min(1, Math.log1p((q * 16 + 8) / hScale) / Math.log1p(30));
    bucketOf[q] = 1 + Math.min(NB - 2, Math.floor(t * (NB - 1)));
  }

  // ---- DOM ----
  if (!document.getElementById('hl-strata-css')) {
    const st = document.createElement('style');
    st.id = 'hl-strata-css';
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  const root = document.createElement('div');
  root.className = 'hl-strata';
  root.innerHTML = `
    <div class="hl-stage"><canvas aria-label="Every Supreme Court opinion by decision year and citations received so far, played through time" role="img"></canvas><div class="hl-tip"></div></div>
    <p class="hl-caption"></p>
    <div class="hl-controls">
      <button type="button" class="hl-play"></button>
      <input type="range" class="hl-scrub" min="${Y0}" max="${Y1}" step="1" aria-label="Year">
      <button type="button" class="hl-speed" aria-label="Playback speed">1×</button>
    </div>`;
  el.appendChild(root);
  const stage = root.querySelector('.hl-stage');
  const canvas = root.querySelector('canvas');
  const tip = root.querySelector('.hl-tip');
  const caption = root.querySelector('.hl-caption');
  const playBtn = root.querySelector('.hl-play');
  const scrub = root.querySelector('.hl-scrub');
  const speedBtn = root.querySelector('.hl-speed');
  const ctx = canvas.getContext('2d');

  // ---- state ----
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  let T = reduce.matches ? Y1 : Y0;
  let playing = !reduce.matches;
  let speed = 1;
  let selected = -1;
  let W = 0, H = 0, dpr = 1;
  let colors = null;
  let dirty = true;
  let raf = 0;
  let last = 0;
  let lastCaptionYear = -1;
  const bx = [], by = [], bn = new Int32Array(NB);
  for (let b = 0; b < NB; b++) { bx.push(new Float32Array(N)); by.push(new Float32Array(N)); }
  const M = { l: 46, r: 14, t: 14, b: 28 };

  const X = (y) => M.l + ((y - Y0) / (Y1 - Y0)) * (W - M.l - M.r);
  const Y = (v) => M.t + (1 - v / maxLog) * (H - M.t - M.b);

  function readColors() {
    const cs = getComputedStyle(document.documentElement);
    const g = (n, f) => cs.getPropertyValue(n).trim() || f;
    const ash = parseColor(ctx, g('--ash', '#a39b8e'), '#a39b8e');
    const e1 = parseColor(ctx, g('--ember', '#2c8bd0'), '#2c8bd0');
    const e2 = parseColor(ctx, g('--ember-2', '#a3d3f2'), '#a3d3f2');
    const bucket = [];
    for (let b = 0; b < NB; b++) {
      if (b === 0) { bucket.push(rgba(ash, 0.3)); continue; }
      const t = (b - 1) / (NB - 2);
      const c = t < 0.5 ? mix(ash, e2, t * 2) : mix(e2, e1, (t - 0.5) * 2);
      bucket.push(rgba(c, 0.45 + 0.55 * t));
    }
    // the very hottest bucket flares in the orange accent
    bucket[NB - 1] = g('--accent', '#e57a2e');
    colors = {
      bucket,
      ink: g('--ink', '#1d1a16'), muted: g('--muted', '#6b645a'), line: g('--line', '#d4ccbd'),
      ember: g('--ember', '#2c8bd0'), accent: g('--accent', '#e57a2e'), sans: g('--font-sans', 'system-ui, sans-serif'),
      mono: g('--font-mono', 'ui-monospace, monospace'),
    };
    dirty = true;
  }

  function resize() {
    const r = stage.getBoundingClientRect();
    W = Math.max(1, Math.round(r.width));
    H = Math.max(1, Math.round(r.height));
    dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    dirty = true;
  }

  // ---- draw ----
  function draw() {
    if (!colors || !W) return;
    const k = Math.min(NY - 1, Math.max(0, Math.floor(T) - Y0));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const plotW = W - M.l - M.r;
    const plotB = H - M.b;

    // axes
    ctx.font = `11px ${colors.sans}`;
    ctx.textBaseline = 'top';
    ctx.textAlign = 'center';
    const step = plotW < 560 ? 50 : 20;
    ctx.lineWidth = 1;
    for (let y = Math.ceil(Y0 / step) * step; y <= Y1; y += step) {
      const x = Math.round(X(y)) + 0.5;
      ctx.strokeStyle = colors.line;
      ctx.globalAlpha = 0.6;
      ctx.beginPath(); ctx.moveTo(x, M.t); ctx.lineTo(x, plotB); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = colors.muted;
      ctx.fillText(String(y), x, plotB + 7);
    }
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (const v of [1, 10, 100, 1000]) {
      const ly = Math.log1p(v);
      if (ly > maxLog) break;
      const y = Math.round(Y(ly)) + 0.5;
      ctx.strokeStyle = colors.line;
      ctx.globalAlpha = 0.6;
      ctx.beginPath(); ctx.moveTo(M.l, y); ctx.lineTo(W - M.r, y); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = colors.muted;
      ctx.fillText(v >= 1000 ? '1k' : String(v), M.l - 6, y);
    }
    ctx.save();
    ctx.translate(11, M.t + (plotB - M.t) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = colors.muted;
    ctx.fillText('citations so far (log)', 0, 0);
    ctx.restore();

    // year readout
    ctx.fillStyle = colors.ink;
    ctx.globalAlpha = 0.22;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.font = `500 ${Math.round(Math.min(96, Math.max(40, W / 9)))}px ${colors.mono}`;
    ctx.fillText(String(Math.floor(T)), M.l + 12, M.t);
    ctx.globalAlpha = 1;

    // playhead
    const px = X(Math.min(Y1, T));
    ctx.strokeStyle = colors.accent;
    ctx.globalAlpha = 0.5;
    ctx.beginPath(); ctx.moveTo(Math.round(px) + 0.5, M.t); ctx.lineTo(Math.round(px) + 0.5, plotB); ctx.stroke();
    ctx.globalAlpha = 1;

    // bucket visible points, track hottest labels
    bn.fill(0);
    const end = yearEnd[k];
    const topI = new Int32Array(TOP_LABELS).fill(-1);
    const topH = new Float32Array(TOP_LABELS);
    for (let i = 0; i < end; i++) {
      const o = k * N + i;
      const ly = logy[o];
      const hv = heat16[o];
      let b = 0;
      if (ly > 0) b = bucketOf[hv >> 4];
      const n = bn[b]++;
      bx[b][n] = X(yr[i]);
      by[b][n] = Y(ly);
      if (hv > topH[TOP_LABELS - 1]) {
        let j = TOP_LABELS - 1;
        while (j > 0 && hv > topH[j - 1]) { topH[j] = topH[j - 1]; topI[j] = topI[j - 1]; j--; }
        topH[j] = hv; topI[j] = i;
      }
    }
    for (let b = 0; b < NB; b++) {
      const n = bn[b];
      if (!n) continue;
      const s = b === 0 ? 1 : 1.4 + (b / NB) * 1.6;
      const xs = bx[b], ys = by[b];
      ctx.fillStyle = colors.bucket[b];
      ctx.beginPath();
      for (let j = 0; j < n; j++) ctx.rect(xs[j] - s / 2, ys[j] - s / 2, s, s);
      ctx.fill();
    }

    // selected trajectory + ring
    if (selected >= 0) {
      const y0 = Math.max(0, yr[selected] - Y0);
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (k < y0) { ctx.globalAlpha = 0.35; ctx.setLineDash([3, 3]); }
      for (let j = y0; j < NY; j++) {
        const x = X(Y0 + j), y = Y(logy[j * N + selected]);
        if (j === y0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        if (j === k) { ctx.stroke(); ctx.globalAlpha = 0.35; ctx.setLineDash([3, 3]); ctx.beginPath(); ctx.moveTo(x, y); }
      }
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;
      if (yr[selected] <= Y0 + k) {
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(X(yr[selected]), Y(logy[k * N + selected]), 6, 0, Math.PI * 2);
        ctx.stroke();
        ctx.lineWidth = 1;
      }
    }

    // labels for the hottest cases
    ctx.font = `12px ${colors.sans}`;
    ctx.textBaseline = 'middle';
    const boxes = [];
    for (let j = 0; j < TOP_LABELS; j++) {
      const i = topI[j];
      if (i < 0 || topH[j] < 1.5 * hScale) continue;
      let name = rows[i][1];
      if (name.length > 30) name = name.slice(0, 29) + '…';
      const tw = ctx.measureText(name).width;
      const x = X(yr[i]), y = Y(logy[k * N + i]);
      const left = x + 8 + tw > W - 4;
      const lx = left ? x - 8 - tw : x + 8;
      if (boxes.some((q) => lx < q[0] + q[2] && lx + tw > q[0] && Math.abs(y - q[1]) < 14)) continue;
      boxes.push([lx, y, tw]);
      ctx.fillStyle = colors.ink;
      ctx.textAlign = 'left';
      ctx.fillText(name, lx, y);
      ctx.strokeStyle = colors.ink;
      ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.stroke();
    }


    if (k !== lastCaptionYear) {
      lastCaptionYear = k;
      const cnt = yearCount[k];
      const t = yearTop[k];
      caption.textContent = `${Y0 + k} · ${cnt} ${cnt === 1 ? 'opinion' : 'opinions'} cited this year` +
        (t >= 0 ? `, most often ${rows[t][1]}` : '');
    }
  }

  function frame(now) {
    raf = 0;
    if (playing) {
      const dt = last ? Math.min(0.1, (now - last) / 1000) : 0;
      T += dt * ((Y1 - Y0) / SECONDS_FULL) * speed;
      if (T >= Y1) { T = Y1; setPlaying(false); }
      syncScrub();
      dirty = true;
    }
    last = playing ? now : 0;
    if (dirty) { dirty = false; draw(); }
    if (playing) raf = requestAnimationFrame(frame);
  }
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function syncScrub() { const v = String(Math.floor(T)); if (scrub.value !== v) scrub.value = v; }
  function setPlaying(p) {
    playing = p;
    playBtn.textContent = p ? 'Pause' : 'Play';
    playBtn.setAttribute('aria-label', p ? 'Pause playback' : 'Play');
    last = 0;
    if (p && T >= Y1) { T = Y0; }
    dirty = true;
    kick();
  }

  // ---- controls ----
  playBtn.addEventListener('click', () => setPlaying(!playing));
  scrub.addEventListener('input', () => { T = +scrub.value; dirty = true; kick(); });
  speedBtn.addEventListener('click', () => {
    speed = speed === 1 ? 4 : 1;
    speedBtn.textContent = speed + '×';
  });

  // ---- hit testing, tooltip, select ----
  function hit(mx, my) {
    const k = Math.min(NY - 1, Math.max(0, Math.floor(T) - Y0));
    const end = yearEnd[k];
    let best = -1, bd = 10 * 10;
    for (let i = 0; i < end; i++) {
      const dx = X(yr[i]) - mx;
      if (dx > 10 || dx < -10) continue;
      const dy = Y(logy[k * N + i]) - my;
      const d = dx * dx + dy * dy;
      if (d <= bd) { bd = d; best = i; }
    }
    return best;
  }
  function pos(e) {
    const r = canvas.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  }
  function showTip(i, mx, my) {
    if (i < 0) { tip.style.display = 'none'; return; }
    const k = Math.min(NY - 1, Math.max(0, Math.floor(T) - Y0));
    const c = Math.round(Math.expm1(logy[k * N + i]));
    const r = rows[i];
    tip.innerHTML = '';
    const b = document.createElement('b');
    b.textContent = r[1];
    const s = document.createElement('span');
    s.textContent = `${r[3]} · ${r[2]} · ${c} ${c === 1 ? 'citation' : 'citations'} so far`;
    tip.append(b, s);
    tip.style.display = 'block';
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let tx = mx + 14, ty = my - th - 10;
    if (tx + tw > W) tx = mx - tw - 14;
    if (tx < 0) tx = 0;
    if (ty < 0) ty = my + 16;
    tip.style.left = tx + 'px';
    tip.style.top = ty + 'px';
  }
  canvas.addEventListener('pointermove', (e) => {
    const [mx, my] = pos(e);
    const i = hit(mx, my);
    canvas.style.cursor = i >= 0 ? 'pointer' : '';
    showTip(i, mx, my);
  });
  canvas.addEventListener('pointerleave', () => { tip.style.display = 'none'; });
  canvas.addEventListener('click', (e) => {
    const [mx, my] = pos(e);
    const i = hit(mx, my);
    showTip(i, mx, my);
    if (i >= 0) window.dispatchEvent(new CustomEvent('hl:select', { detail: { id: rows[i][0] } }));
  });
  window.addEventListener('hl:select', (e) => {
    const i = idToIdx.get(e.detail && e.detail.id);
    selected = i === undefined ? -1 : i;
    dirty = true;
    kick();
  });

  // ---- theme, size, reduced motion ----
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { readColors(); kick(); });
  new MutationObserver(() => { readColors(); kick(); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  new ResizeObserver(() => { resize(); kick(); }).observe(stage);

  readColors();
  resize();
  syncScrub();
  setPlaying(playing);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { dirty = true; kick(); });
}
