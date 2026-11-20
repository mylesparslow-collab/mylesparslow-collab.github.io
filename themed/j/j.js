/* Mockup J, "Working Drawings". Source: themed/j/j.js, copied to mockup-j/ by themed/render_j.py. No libraries. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var qsa = function (s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); };
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- colour tokens, shared with the canvases ---------- */
  function token(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
  function rgb(hex) { hex = hex.replace('#', ''); if (hex.length === 3) hex = hex.replace(/./g, '$&$&'); var n = parseInt(hex, 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }

  /* ---------- the drawing of a picture, as ink on paper ----------
     Two tests per pixel, the same recipe as the cover plate's shader (hero.js):
     1. strokes: how far its brightness is from a blurred copy, which turns type into single ink strokes;
     2. rules: a Sobel edge for faint lines (panel borders), switched off where test 1 already sees detail.
     Runs in slices of a few milliseconds so that no frame carries the whole image; done() is called when the
     canvas holds the drawing. Pass sync=true for a one-off that may block (the cover plate's fallback). */
  function inkDraw(img, canvas, W, done, sync) {
    var H = Math.round(W * img.naturalHeight / img.naturalWidth), job = (canvas._job || 0) + 1;
    canvas._job = job;                                                // a newer call on the same canvas cancels this one
    canvas.width = W; canvas.height = H;
    var x = canvas.getContext('2d', { willReadFrequently: true });
    x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
    var small = d.createElement('canvas'), k3 = 3.4, bl, src, s, L, D, i;
    small.width = Math.max(2, Math.round(W / k3)); small.height = Math.max(2, Math.round(H / k3));
    var n = W * H, p = rgb(token('--paper')), k = rgb(token('--ink')), y = 0, stage = -2;
    var sm = function (a, b, v) { v = Math.min(1, Math.max(0, (v - a) / (b - a))); return v * v * (3 - 2 * v); };
    function slice() {
      if (canvas._job !== job) return;
      var t0 = performance.now(), X;
      while (sync || performance.now() - t0 < 5) {
        if (stage === -2) {                                            // setup, part 1: the blurred copy, scaled back up
          small.getContext('2d').drawImage(img, 0, 0, small.width, small.height);
          x.drawImage(small, 0, 0, W, H); bl = x.getImageData(0, 0, W, H).data; stage = -1;
          if (!sync) break;
        } else if (stage === -1) {                                     // setup, part 2: the picture itself, then a blank sheet
          x.drawImage(img, 0, 0, W, H); src = x.getImageData(0, 0, W, H); s = src.data;
          L = new Float32Array(n); D = new Float32Array(n);
          x.fillStyle = token('--paper'); x.fillRect(0, 0, W, H); stage = 0;
          if (!sync) break;
        } else if (stage === 0) {                                             // pass 1: brightness and its distance from the blur
          var end = Math.min(n, y + 50000);
          for (i = y; i < end; i++) {
            L[i] = (0.2126 * s[i * 4] + 0.7152 * s[i * 4 + 1] + 0.0722 * s[i * 4 + 2]) / 255;
            D[i] = Math.abs(L[i] - (0.2126 * bl[i * 4] + 0.7152 * bl[i * 4 + 1] + 0.0722 * bl[i * 4 + 2]) / 255);
          }
          y = end; if (y >= n) { stage = 1; y = 0; }
        } else {                                                       // pass 2: strokes and rules, 24 rows at a time
          var last = Math.min(H, y + 24);
          for (; y < last; y++) for (X = 0; X < W; X++) {
            i = y * W + X; var e = 0, dd = D[i];
            if (X > 0 && y > 0 && X < W - 1 && y < H - 1) {
              var a = L[i - W - 1], b = L[i - W], c = L[i - W + 1], l = L[i - 1], f = L[i + 1], g = L[i + W - 1], h = L[i + W], j = L[i + W + 1];
              var gx = (c + 2 * f + j) - (a + 2 * l + g), gy = (g + 2 * h + j) - (a + 2 * b + c);
              e = Math.sqrt(gx * gx + gy * gy);
            }
            var v = Math.max(sm(0.05, 0.21, dd), Math.min(1, Math.max(0, (e - 0.05) * 6)) * (1 - sm(0.02, 0.08, dd)));
            s[i * 4] = p[0] + (k[0] - p[0]) * v; s[i * 4 + 1] = p[1] + (k[1] - p[1]) * v; s[i * 4 + 2] = p[2] + (k[2] - p[2]) * v; s[i * 4 + 3] = 255;
          }
          if (y >= H) { x.putImageData(src, 0, 0); if (done) done(); return; }
        }
      }
      setTimeout(slice, 0);
    }
    slice();
  }
  window.MPJ = { inkDraw: inkDraw, token: token, rgb: rgb, reduced: reduced };

  /* ---------- theme ---------- */
  var tb = d.getElementById('theme');
  if (tb) tb.addEventListener('click', function () {
    var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', t);
    try { localStorage.setItem('mpj-theme', t); } catch (e) {}
    d.dispatchEvent(new CustomEvent('mpj-theme'));
  });

  /* ---------- rooms menu on small screens ---------- */
  var strip = d.getElementById('nav'), menu = d.getElementById('menu');
  if (strip && menu) {
    var setOpen = function (on) { strip.classList.toggle('is-open', on); menu.setAttribute('aria-expanded', on ? 'true' : 'false'); };
    menu.addEventListener('click', function () {
      var on = !strip.classList.contains('is-open'); setOpen(on);
      if (on) { var a = strip.querySelector('.strip__rooms a'); if (a) a.focus(); }
    });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && strip.classList.contains('is-open')) { setOpen(false); menu.focus(); } });
    d.addEventListener('click', function (e) { if (!strip.contains(e.target)) setOpen(false); });
    strip.addEventListener('focusout', function () { setTimeout(function () { if (!strip.contains(d.activeElement)) setOpen(false); }, 0); });
  }

  /* ---------- skip link and in-page jumps move focus, not just the scroll ---------- */
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var t = d.getElementById(a.getAttribute('href').slice(1));
    if (!t) return;
    if (!t.hasAttribute('tabindex') && !/^(A|BUTTON|INPUT|SUMMARY)$/.test(t.tagName)) t.setAttribute('tabindex', '-1');
    setTimeout(function () { t.focus({ preventScroll: true }); }, 0);
  });
  /* a deep link lands again once the font has settled the layout */
  if (location.hash.length > 1 && d.fonts && d.fonts.ready) d.fonts.ready.then(function () {
    var t = d.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView();
  });

  /* ---------- plates: each project first as its drawing, then plotted into the built thing ---------- */
  var plates = qsa('[data-ink]');
  if (plates.length && !reduced && 'IntersectionObserver' in window) {
    var idle = window.requestIdleCallback || function (fn) { return setTimeout(fn, 60); };
    var ink = function (fig) {
      if (fig._ink) return; fig._ink = 1;
      var img = fig.querySelector('img'), cv = fig.querySelector('canvas');
      var go = function () {
        idle(function () {
          try {
            var W = Math.min(img.naturalWidth, Math.round(fig.clientWidth * 2));   // drawn at 2x and scaled down, so the lines stay fine on 1x screens
            if (W < 40) return;
            fig._W = W;
            inkDraw(img, cv, W, function () { fig.classList.add('is-inked'); if (fig._seen) build(fig); });
          } catch (e) { /* a tainted canvas or no 2D context: the photograph simply shows */ }
        });
      };
      if (img.complete && img.naturalWidth) go(); else { img.loading = 'eager'; img.addEventListener('load', go, { once: true }); }
    };
    var build = function (fig) {
      if (fig._built || !fig.classList.contains('is-inked')) return; fig._built = 1;
      setTimeout(function () { fig.classList.add('is-built'); }, 420);
    };
    var near = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { ink(e.target); near.unobserve(e.target); } }); }, { rootMargin: '500px 0px' });
    var seen = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target._seen = 1; build(e.target); seen.unobserve(e.target); } }); }, { threshold: 0.55 });
    plates.forEach(function (f) { near.observe(f); seen.observe(f); });
    d.addEventListener('mpj-theme', function () {
      plates.forEach(function (f) {
        if (!f._W || f._built) return;                                // not started yet (it will read the new colours) or already a photograph
        try { inkDraw(f.querySelector('img'), f.querySelector('canvas'), f._W, function () { f.classList.add('is-inked'); if (f._seen) build(f); }); } catch (e) {}
      });
    });
  }

  /* ---------- before / after sliders ---------- */
  qsa('.compare').forEach(function (c) {
    var r = c.querySelector('input'); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* ---------- a random project ---------- */
  var sp = d.getElementById('surprise');
  if (sp) sp.addEventListener('click', function () {
    var all = qsa('#byroom ol a'); if (all.length) location.href = all[Math.floor(Math.random() * all.length)].getAttribute('href');
  });

  /* ---------- drawing index: by room or A to Z ---------- */
  var ctl = d.getElementById('ixctl'), byRoom = d.getElementById('byroom'), byAz = d.getElementById('byaz');
  if (ctl && byRoom && byAz) {
    ctl.hidden = false;
    var bR = d.getElementById('by-room'), bA = d.getElementById('by-az'), made = false;
    var show = function (az) {
      if (az && !made) {
        made = true;
        qsa('ol li', byRoom).sort(function (a, b) { return a.getAttribute('data-t') < b.getAttribute('data-t') ? -1 : 1; }).forEach(function (li) {
          var c = li.cloneNode(true); qsa('.see', c).forEach(function (n) { n.remove(); }); byAz.appendChild(c);
        });
      }
      byAz.hidden = !az; byRoom.hidden = az;
      bA.setAttribute('aria-pressed', az ? 'true' : 'false'); bR.setAttribute('aria-pressed', az ? 'false' : 'true');
    };
    bR.addEventListener('click', function () { show(false); });
    bA.addEventListener('click', function () { show(true); });
  }

  /* ---------- copy the email ---------- */
  var cb = d.getElementById('copy');
  if (cb) cb.addEventListener('click', function () {
    var t = cb.getAttribute('data-copy'), st = d.getElementById('copystat');
    function ok(m) { if (st) { st.textContent = m; setTimeout(function () { st.textContent = ''; }, 2400); } }
    function fallback() {
      var ta = d.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px;top:0';
      d.body.appendChild(ta); ta.select();
      var good = false; try { good = d.execCommand('copy'); } catch (e) {}
      d.body.removeChild(ta); ok(good ? 'Copied.' : 'Select the address and copy it.');
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { ok('Copied.'); }, fallback);
    else fallback();
  });

  /* ---------- drawing list: mark the project on screen ---------- */
  var list = d.getElementById('list');
  if (list && 'IntersectionObserver' in window) {
    var det = list.querySelector('details'), mq = matchMedia('(max-width: 820px)');
    var fold = function () { if (det) det.open = !mq.matches; };
    fold(); if (mq.addEventListener) mq.addEventListener('change', fold);
    if (det) det.querySelector('summary').addEventListener('click', function (e) { if (!mq.matches) e.preventDefault(); });
    var links = {}, cur = null;
    qsa('ol a', list).forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var mark = function (id) {
      if (id === cur || !links[id]) return;
      if (cur && links[cur]) links[cur].removeAttribute('aria-current');
      cur = id; var a = links[id]; a.setAttribute('aria-current', 'true');
      if (!mq.matches) {                                           // keep the marked entry inside the list's own scroll area
        var top = a.getBoundingClientRect().top - list.getBoundingClientRect().top + list.scrollTop;
        if (top < list.scrollTop + 30 || top > list.scrollTop + list.clientHeight - 90) list.scrollTop = top - list.clientHeight / 2;
      }
    };
    var arts = qsa('.dwg');
    var pick = function () {                       // by geometry: the last project whose top is above the reading line
      var line = innerHeight * 0.35, id = null;
      for (var i = 0; i < arts.length; i++) { if (arts[i].getBoundingClientRect().top <= line) id = arts[i].id; else break; }
      if (id) mark(id);
    };
    var spy = new IntersectionObserver(function (es) {
      var hit = false; es.forEach(function (e) { if (e.isIntersecting) { hit = true; mark(e.target.id); } });
      if (!hit) pick();                            // a jump (End key, a deep link) can skip the band entirely
    }, { rootMargin: '-20% 0px -65% 0px' });
    arts.forEach(function (a) { spy.observe(a); });
    if (det) qsa('ol a', list).forEach(function (a) { a.addEventListener('click', function () { if (mq.matches) det.open = false; }); });
  }
})();
