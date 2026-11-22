/* Mockup N, "Flipbook": the viewer. Source: themed/n/flip.js, copied to mockup-n/ by themed/render_n.py.

   The viewer holds one frame at a time on a 2D canvas (never a cross-fade). The caption, the counter, the link, the row
   marked on the sheet and the strip all change in the same step as the picture, and only after the picture has loaded
   and decoded, so a slow or failed image can never leave a stale caption next to the wrong frame. A frame whose image is
   missing is drawn as a typographic card (its number, title and subtitle).

   Onion skin: the frame before is ghosted in green and the frame after in pink. A ghost is the part of a neighbouring
   frame that differs from that frame's own background (so light and dark screenshots both read), tinted and laid over
   the current frame. Mode "auto" shows the ghosts strongly for two steps of about 0.45 s after each change and then
   lets them go; "held" keeps them; "off" hides them. (Two frames at 12 a second would be 0.17 s, too short to read.)

   Play runs the frames at the page's frame rate on a requestAnimationFrame clock that is re-based after a stall. It starts
   on the frame you were on, goes once round and stops on that frame again. Scrolling the sheet steps the viewer;
   the strip, the arrows and Play move the sheet in return. Reduced motion: no onion by default, Play is one frame a click.
   No libraries. */
(function () {
  'use strict';
  var d = document, dataEl = d.getElementById('fr-data'), vwr = d.getElementById('vwr');
  if (!dataEl || !vwr) return;
  var F = JSON.parse(dataEl.textContent), N = F.length, scope = dataEl.getAttribute('data-scope');
  var START = clamp0(+vwr.getAttribute('data-start') || 0, N), FPS = +vwr.getAttribute('data-fps') || 12, FRAME_MS = 1000 / FPS, TOTAL = +vwr.getAttribute('data-total') || N;
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var stackedMQ = matchMedia('(max-width: 899px)'), compactMQ = matchMedia('(max-width: 1239px)');
  function clamp0(v, n) { return Math.min(n - 1, Math.max(0, v)); }
  var $ = function (id) { return d.getElementById(id); };
  var slot = $('v-slot'), sheetEl = $('index'), barTx = $('bar-tx'), docked = !slot;   // the homepage viewer is a hero until the sheet arrives, then it docks beside it
  var cv = $('v-cv'), stage = $('v-link'), img = $('v-img'), nEl = $('v-n'), ofEl = $('v-of'), scEl = $('v-sc'), tEl = $('v-t'), sEl = $('v-s'), openEl = $('v-open');
  var ctl = $('v-ctl'), playB = $('v-play'), prevB = $('v-prev'), nextB = $('v-next'), onionB = $('v-onion'), timeEl = $('v-time');
  var strip = $('v-strip'), track = $('v-track'), live = $('v-live'), barFr = $('bar-fr'), barN = $('bar-n');
  var X = cv.getContext('2d'), W = 0, H = 0;
  var FD = '"Sofia Sans Condensed","Arial Narrow",Arial,sans-serif', FB = '"Sofia Sans","Helvetica Neue",Arial,sans-serif';
  var pad3 = function (n) { return (n < 10 ? '00' : n < 100 ? '0' : '') + n; };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  var idx = -1, seq = 0, playing = false, loading = false, level = 0, onionT = 0, liveT = 0, progY = -1, raf = 0;
  var mode = reduced ? 2 : 0;                       // onion: 0 auto, 1 held, 2 off
  var A_STRONG = 0.42, A_WEAK = 0.22, A_HELD = 0.3, A_PLAY = 0.34;

  /* ------------------------------------------------------------------ colours from the page's tokens */
  var tk = null;
  function tok() {
    if (tk) return tk;
    var cs = getComputedStyle(d.documentElement), g = function (n) { return cs.getPropertyValue(n).trim(); };
    tk = { box: g('--box'), ink: g('--ink'), dim: g('--dim'), rule: g('--rule2'), prev: g('--prev'), next: g('--next') };
    return tk;
  }

  /* ------------------------------------------------------------------ loading frames */
  var C = new Array(N);
  function load(i) {
    var c = C[i];
    if (c) return c.p;
    c = C[i] = { img: null, ok: false, done: false };
    var f = F[i];
    c.p = new Promise(function (res) {
      var im = new Image(), timer = 0;
      var fin = function (ok) {
        if (c.done) return; c.done = true; clearTimeout(timer);
        c.ok = ok; c.img = ok ? im : null; res(c);
      };
      if (!f.src) { fin(false); return; }
      im.onload = function () { if (im.decode) im.decode().then(function () { fin(true); }, function () { fin(true); }); else fin(true); };
      im.onerror = function () { fin(false); };
      timer = setTimeout(function () { if (!c.done) { fin(false); C[i] = null; } }, 9000);   // a stalled image is drawn as a card now and tried again later
      im.src = f.src;
    });
    return c.p;
  }

  /* ------------------------------------------------------------------ drawing a frame */
  function wrap(x, text, maxW, maxLines) {
    var words = text.split(/\s+/), lines = [], cur = '', k, t;
    for (k = 0; k < words.length; k++) {
      t = cur ? cur + ' ' + words[k] : words[k];
      if (x.measureText(t).width > maxW && cur) { lines.push(cur); cur = words[k]; } else cur = t;
    }
    if (cur) lines.push(cur);
    return lines.length > maxLines ? null : lines;
  }
  function card(x, f, w, h, t) {
    var u = h / 100, m = 8 * u;
    x.fillStyle = t.box; x.fillRect(0, 0, w, h);
    x.textBaseline = 'alphabetic'; x.textAlign = 'left';
    x.fillStyle = t.dim; x.font = '600 ' + 5.4 * u + 'px ' + FB;
    x.fillText('Scene ' + f.L + '  ·  ' + f.sc, m, 12 * u);
    x.fillStyle = t.ink; x.font = '800 ' + 52 * u + 'px ' + FD;
    x.fillText(pad3(f.g), m - 1.5 * u, 59 * u);
    x.fillStyle = t.rule; x.fillRect(m, 65 * u, w - 2 * m, 0.7 * u);
    var size = 11.5 * u, lines = null, maxW = w - 2 * m;
    for (; size > 6 * u; size -= 0.5 * u) { x.font = '800 ' + size + 'px ' + FD; lines = wrap(x, f.n, maxW, 2); if (lines) break; }
    if (!lines) lines = [f.n];
    x.fillStyle = t.ink;
    lines.forEach(function (ln, k) { x.fillText(ln, m, 77 * u + k * size * 1.02); });
    var y = 77 * u + (lines.length - 1) * size * 1.02 + 7 * u;
    x.fillStyle = t.dim; x.font = '400 ' + 5.2 * u + 'px ' + FB;
    var sl = wrap(x, f.s, maxW, 2) || [f.s];
    sl.slice(0, 2).forEach(function (ln, k) { if (y + k * 6.4 * u < h - 2 * u) x.fillText(ln, m, y + k * 6.4 * u); });
  }
  function paintFrame(x, i, w, h, t) {
    var c = C[i], f = F[i];
    if (c && c.ok) {
      var im = c.img, iw = im.naturalWidth, ih = im.naturalHeight, ia = iw / ih, ca = w / h, dw, dh;
      x.fillStyle = t.box; x.fillRect(0, 0, w, h);
      x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
      if (Math.abs(ia / ca - 1) < 0.3) { var s = Math.max(w / iw, h / ih); dw = iw * s; dh = ih * s; x.drawImage(im, (w - dw) / 2, 0, dw, dh); }
      else { var s2 = Math.min(w / iw, h / ih); dw = iw * s2; dh = ih * s2; x.drawImage(im, (w - dw) / 2, (h - dh) / 2, dw, dh); }
    } else card(x, f, w, h, t);
  }

  /* ------------------------------------------------------------------ onion skin */
  var MW = 640, MH = 360, MK = {}, MKo = [];
  var sc = d.createElement('canvas'); sc.width = MW; sc.height = MH;
  var sx = sc.getContext('2d', { willReadFrequently: true });
  var gc = d.createElement('canvas'); gc.width = MW; gc.height = MH;
  var gx = gc.getContext('2d');
  function mask(j) {
    if (MK[j]) return MK[j];
    paintFrame(sx, j, MW, MH, tok());
    var id;
    try { id = sx.getImageData(0, 0, MW, MH); } catch (e) { return null; }       // a canvas tainted by a file:// page cannot be read
    var p = id.data, n = MW * MH, L = new Uint8Array(n), hist = new Uint32Array(32), k, l, bin = 0, best = 0;
    for (k = 0; k < n; k++) { l = (p[k * 4] * 54 + p[k * 4 + 1] * 183 + p[k * 4 + 2] * 19) >> 8; L[k] = l; hist[l >> 3]++; }
    for (k = 0; k < 32; k++) if (hist[k] > best) { best = hist[k]; bin = k; }
    var bg = bin * 8 + 4, v;
    for (k = 0; k < n; k++) {
      v = Math.abs(L[k] - bg) / 255; v = v < 0.05 ? 0 : Math.min(1, (v - 0.05) * 3.4);
      p[k * 4] = p[k * 4 + 1] = p[k * 4 + 2] = 255; p[k * 4 + 3] = v * 255;
    }
    var m = d.createElement('canvas'); m.width = MW; m.height = MH; m.getContext('2d').putImageData(id, 0, 0);
    MK[j] = m; MKo.push(j);
    if (MKo.length > 14) delete MK[MKo.shift()];
    return m;
  }
  function isCard(j) { return !F[j].src || (C[j] && C[j].done && !C[j].ok); }
  function ghost(j, col, a, at) {
    if (j < 0 || j >= N || isCard(j) || isCard(at)) return;   // a typographic card is never drawn over a picture, nor a picture over a card
    var c = C[j];
    if (!c || !c.done) { load(j).then(function () { if (idx === at && onionOn()) paint(); }); return; }
    var m = mask(j);
    gx.globalCompositeOperation = 'source-over'; gx.clearRect(0, 0, MW, MH);
    if (m) { gx.drawImage(m, 0, 0); gx.globalCompositeOperation = 'source-in'; gx.fillStyle = col; gx.fillRect(0, 0, MW, MH); }
    else { paintFrame(gx, j, MW, MH, tok()); gx.globalCompositeOperation = 'multiply'; gx.fillStyle = col; gx.fillRect(0, 0, MW, MH); a = a * 0.6; }
    gx.globalCompositeOperation = 'source-over';
    X.globalAlpha = a; X.drawImage(gc, 0, 0, W, H); X.globalAlpha = 1;
  }
  function onionAlpha() {
    if (mode === 2 || (mode === 0 && reduced)) return 0;
    if (mode === 1) return A_HELD;
    if (playing) return A_PLAY;
    return level === 2 ? A_STRONG : level === 1 ? A_WEAK : 0;
  }
  function onionOn() { return onionAlpha() > 0; }
  function bumpOnion() {
    clearTimeout(onionT);
    if (mode !== 0 || reduced) { level = 0; return; }
    level = 2;
    if (playing) return;
    onionT = setTimeout(function () { level = 1; paint(); onionT = setTimeout(function () { level = 0; paint(); }, 450); }, 450);
  }

  function size() {
    var r = stage.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1);
    var w = Math.max(2, Math.round(r.width * dpr)), h = Math.max(2, Math.round(r.height * dpr));
    if (w !== cv.width || h !== cv.height) { cv.width = w; cv.height = h; }
    W = w; H = h;
    var mh = Math.round(MW * H / W);                 // the onion masks are made at the stage's own proportions
    if (mh !== MH) { MH = mh; sc.height = MH; gc.height = MH; MK = {}; MKo = []; }
  }
  function paint() {
    if (idx < 0) return;
    if (!W) size();
    var t = tok();
    paintFrame(X, idx, W, H, t);
    var a = onionAlpha();
    if (a > 0) { ghost(idx - 1, t.prev, a, idx); ghost(idx + 1, t.next, a, idx); }
  }

  /* ------------------------------------------------------------------ caption, sheet and strip */
  var rows = {}, anchor = {}, T = [], curRow = null, cells = track ? Array.prototype.slice.call(track.children) : [], curCell = null, pitch = 68;
  (function collect() {
    var gi = {}, k;
    for (k = 0; k < N; k++) gi[F[k].g] = k;
    var els = scope === 'all' ? d.querySelectorAll('#index .xr__a[data-g]') : d.querySelectorAll('.work--room .case[data-g], .work--room .grp[data-g]');
    Array.prototype.forEach.call(els, function (el) {
      var i = gi[+el.getAttribute('data-g')];
      if (i === undefined) return;
      T.push({ el: el, i: i });
      if (scope === 'all') rows[i] = el;
      else if (el.classList.contains('case')) anchor[i] = el;
    });
    if (scope === 'all') anchor = rows;
  })();
  function measure() {
    if (cells.length > 1) pitch = cells[1].offsetLeft - cells[0].offsetLeft || pitch; else if (cells[0]) pitch = cells[0].offsetWidth + 4;
  }
  function setStrip(i) {
    if (!strip || strip.hidden) return;
    strip.scrollLeft = i * pitch;
    if (curCell) curCell.classList.remove('is-cur');
    curCell = cells[i]; if (curCell) curCell.classList.add('is-cur');
    strip.setAttribute('aria-valuenow', String(i + 1));
    strip.setAttribute('aria-valuetext', 'Frame ' + F[i].g + ', ' + F[i].n);
  }
  function caption(i) {
    var f = F[i];
    nEl.textContent = pad3(f.g);
    nEl.setAttribute('data-p', i > 0 ? pad3(F[i - 1].g) : '');
    nEl.setAttribute('data-n', i < N - 1 ? pad3(F[i + 1].g) : '');
    ofEl.textContent = '/ ' + pad3(TOTAL);
    scEl.textContent = 'Scene ' + f.L;
    tEl.textContent = f.n; sEl.textContent = f.s;
    stage.href = f.h; openEl.href = f.h; stage.setAttribute('aria-label', 'Open ' + f.n);
    timeEl.textContent = Math.floor(i / FPS) + '+' + (i % FPS < 10 ? '0' : '') + (i % FPS) + ' / ' + Math.floor(N / FPS) + '+' + (N % FPS < 10 ? '0' : '') + (N % FPS);
    if (barN) { barN.textContent = pad3(f.g); barFr.hidden = false; }
    if (rows[i] !== curRow) {
      if (curRow) { curRow.classList.remove('is-cur'); curRow.removeAttribute('aria-current'); }
      curRow = rows[i] || null;
      if (curRow) { curRow.classList.add('is-cur'); curRow.setAttribute('aria-current', 'true'); }
    }
    setStrip(i);
  }
  function announce() {
    clearTimeout(liveT);
    liveT = setTimeout(function () { if (!playing && idx >= 0) live.textContent = 'Frame ' + F[idx].g + ' of ' + TOTAL + ': ' + F[idx].n; }, 700);
  }

  /* ------------------------------------------------------------------ showing a frame */
  var first = true;
  function commit(i, o) {
    idx = i;
    caption(i);
    bumpOnion();
    paint();
    if (first) {
      first = false; if (img) img.hidden = true;
      ctl.hidden = false; strip.hidden = false; if (barTx) barTx.hidden = false; measure(); setStrip(i);
    }
    if (o && o.scroll) scrollToFrame(i);
    if (!playing) announce();
  }
  function show(i, o) {
    i = clamp(i, 0, N - 1);
    var me = ++seq, c = C[i];
    if (c && c.done) commit(i, o);
    else load(i).then(function () { if (seq === me) commit(i, o); });
    [i + 1, i - 1, i + 2].forEach(function (j) { if (j >= 0 && j < N) load(j); });
  }

  /* ------------------------------------------------------------------ the sheet follows the viewer, and the viewer follows the sheet */
  function lineY() {
    if (stackedMQ.matches) return vwr.getBoundingClientRect().bottom + 26;
    return window.innerHeight * (scope === 'all' ? 0.4 : 0.32);
  }
  function scrollToFrame(i) {
    var el = anchor[i]; if (!el) return;
    var y = Math.max(0, el.getBoundingClientRect().top + window.pageYOffset - lineY() + 4);
    if (Math.abs(y - window.pageYOffset) < 2) return;
    window.scrollTo(0, y); progY = window.pageYOffset;
  }
  function pick() {
    var y = lineY(), best = 0, k, r;
    for (k = 0; k < T.length; k++) { r = T[k].el.getBoundingClientRect(); if (r.top <= y) best = k; else break; }
    if (scope === 'all' && T.length && T[0].el.getBoundingClientRect().top > y) return START;   // above the sheet: the film stays on its opening frame
    return T.length ? T[best].i : START;
  }
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (playing || ticking || Math.abs(window.pageYOffset - progY) < 2) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; var i = pick(); if (i !== idx) show(i, null); });
  }, { passive: true });

  /* ------------------------------------------------------------------ hero and dock (homepage) */
  function setDock(want) {
    if (!slot || want === docked) return;
    docked = want;
    if (want) { slot.style.height = slot.offsetHeight + 'px'; vwr.classList.remove('vwr--hero'); vwr.classList.add('is-docked'); }
    else { vwr.classList.remove('is-docked'); vwr.classList.add('vwr--hero'); slot.style.height = ''; }
    size(); measure(); paint(); setStrip(idx);
  }
  function dockCheck() { if (slot && sheetEl) setDock(sheetEl.getBoundingClientRect().top < 60); }
  var dockT = false;
  if (slot) window.addEventListener('scroll', function () {
    if (dockT) return; dockT = true;
    requestAnimationFrame(function () { dockT = false; dockCheck(); });
  }, { passive: true });
  window.addEventListener('resize', function () {
    if (!slot || !docked) return;
    setDock(false); dockCheck();                      // measure the hero again at the new width, then dock if the sheet is on screen
  });

  /* ------------------------------------------------------------------ play */
  function label() {
    var t = playB.querySelector('.btn__t'), base = reduced ? 'Next frame' : compactMQ.matches ? 'Play' : playB.getAttribute('data-label');
    t.textContent = loading ? 'Loading frames' : playing ? 'Pause' : base;
  }
  function stop() {
    var was = playing || loading;
    playing = false; loading = false; cancelAnimationFrame(raf);
    playB.setAttribute('aria-pressed', 'false'); playB.removeAttribute('aria-busy'); label();
    if (was) { bumpOnion(); paint(); announce(); }
  }
  function preload() {
    var order = [], k, done = 0;
    for (k = 0; k < N; k++) order.push((idx + k) % N);
    var q = order.slice(), lanes = [];
    function lane() {
      if (!loading || !q.length) return Promise.resolve();
      var j = q.shift();
      return load(j).then(function () { done++; var t = playB.querySelector('.btn__t'); if (loading) t.textContent = 'Loading ' + done + '/' + N; return lane(); });
    }
    for (k = 0; k < 6; k++) lanes.push(lane());
    return Promise.all(lanes);
  }
  function start() {
    playing = true; loading = false; label();
    playB.setAttribute('aria-pressed', 'true');
    var startIdx = idx, t0 = performance.now(), last = t0, k = 0;
    clearTimeout(onionT); level = 2;
    function tick(now) {
      if (!playing) return;
      if (now - last > 300) t0 += now - last - FRAME_MS;      // a stall (hidden tab, slow frame): pick up from here instead of racing to catch up
      last = now;
      var steps = Math.floor((now - t0) / FRAME_MS);
      if (steps !== k) {
        k = steps;
        if (k >= N) { commit(startIdx, { scroll: !reduced && docked }); stop(); return; }
        commit((startIdx + k) % N, { scroll: !reduced && docked });   // the sheet follows only once the viewer is docked beside it
      }
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
  }
  function toggle() {
    if (reduced) { goto((idx + 1) % N); return; }
    if (playing || loading) { stop(); return; }
    loading = true; playB.setAttribute('aria-pressed', 'true'); playB.setAttribute('aria-busy', 'true'); label();
    preload().then(function () { if (loading) start(); });
  }
  function goto(i) { if (playing || loading) stop(); show(i, { scroll: true }); }

  /* ------------------------------------------------------------------ controls */
  playB.addEventListener('click', toggle);
  prevB.addEventListener('click', function () { goto((idx - 1 + N) % N); });
  nextB.addEventListener('click', function () { goto((idx + 1) % N); });
  var modes = [['Onion skin', 'Onion skin: shows after each change'], ['Onion held', 'Onion skin: held on'], ['Onion off', 'Onion skin: off']];
  function setMode(m) {
    mode = m; onionB.setAttribute('data-mode', String(m)); onionB.querySelector('.btn__t').textContent = modes[m][0];
    onionB.setAttribute('aria-label', modes[m][1] + '. Press to change.');
    if (m === 0) bumpOnion(); else level = 0;
    paint();
  }
  onionB.addEventListener('click', function () { setMode((mode + 1) % 3); });
  setMode(mode);
  if (reduced) playB.removeAttribute('aria-pressed');
  ['wheel', 'touchmove'].forEach(function (ev) { d.addEventListener(ev, function () { if (playing || loading) stop(); }, { passive: true }); });
  d.addEventListener('keydown', function (e) { if ((playing || loading) && /^(ArrowUp|ArrowDown|PageUp|PageDown|Home|End)$/.test(e.key)) stop(); });
  d.addEventListener('visibilitychange', function () { if (d.hidden) stop(); });
  if (stackedMQ.addEventListener) { stackedMQ.addEventListener('change', function () { label(); measure(); setStrip(idx); }); compactMQ.addEventListener('change', label); }

  /* the strip: press a cell to jump to it, drag to move the film under the playhead, arrow keys for single frames */
  var drag = null;
  strip.addEventListener('pointerdown', function (e) {
    if (e.button) return;
    var r = strip.getBoundingClientRect(), to = clamp(idx + Math.round((e.clientX - (r.left + r.width / 2)) / pitch), 0, N - 1);
    drag = { x: e.clientX, i: to, id: e.pointerId };
    try { strip.setPointerCapture(e.pointerId); } catch (err) {}
    if (to !== idx) goto(to);
  });
  strip.addEventListener('pointermove', function (e) {
    if (!drag || e.pointerId !== drag.id) return;
    var to = clamp(drag.i - Math.round((e.clientX - drag.x) / pitch), 0, N - 1);
    if (to !== idx) goto(to);
  });
  var end = function (e) { if (drag && e.pointerId === drag.id) { drag = null; announce(); } };
  strip.addEventListener('pointerup', end); strip.addEventListener('pointercancel', end);
  strip.addEventListener('keydown', function (e) {
    var k = e.key, to = null;
    if (k === 'ArrowLeft' || k === 'ArrowDown') to = idx - 1;
    else if (k === 'ArrowRight' || k === 'ArrowUp') to = idx + 1;
    else if (k === 'PageUp') to = idx - FPS; else if (k === 'PageDown') to = idx + FPS;
    else if (k === 'Home') to = 0; else if (k === 'End') to = N - 1;
    if (to === null) return;
    e.preventDefault(); goto(clamp(to, 0, N - 1));
  });
  strip.addEventListener('dragstart', function (e) { e.preventDefault(); });

  /* ------------------------------------------------------------------ start */
  d.addEventListener('mpn-theme', function () { tk = null; MK = {}; MKo = []; paint(); });
  if (window.ResizeObserver) new ResizeObserver(function () { size(); measure(); paint(); setStrip(idx); }).observe(stage);
  else window.addEventListener('resize', function () { size(); measure(); paint(); setStrip(idx); });
  size(); label();
  var fontsReady = d.fonts && d.fonts.load ? Promise.all([d.fonts.load('800 40px "Sofia Sans Condensed"'), d.fonts.load('400 16px "Sofia Sans"'), d.fonts.load('600 16px "Sofia Sans"')]).catch(function () {}) : Promise.resolve();
  fontsReady.then(function () { MK = {}; MKo = []; paint(); });
  dockCheck();
  show(pick(), null);
  window.addEventListener('load', function () { if (!playing && T.length) { var i = pick(); if (i !== idx) show(i, null); } });
})();
