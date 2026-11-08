(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)');

  /* theme toggle: the head script already set data-theme (saved choice, else the system) */
  var tb = d.getElementById('theme');
  function paint() {
    var dark = root.getAttribute('data-theme') === 'dark';
    if (tb) { tb.setAttribute('aria-pressed', dark ? 'true' : 'false'); tb.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode'); tb.querySelector('.theme__t').textContent = dark ? 'Light' : 'Dark'; }
  }
  paint();
  if (tb) tb.addEventListener('click', function () {
    var n = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', n);
    try { localStorage.setItem('sw-theme', n); } catch (e) {}
    paint();
  });
  try {
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      var s = null; try { s = localStorage.getItem('sw-theme'); } catch (x) {}
      if (!s) { root.setAttribute('data-theme', e.matches ? 'dark' : 'light'); paint(); }
    });
  } catch (e) {}

  /* fit big display words to one line */
  function fit() {
    Array.prototype.forEach.call(d.querySelectorAll('.fit'), function (el) {
      var box = el.closest('[data-fitbox]') || el.parentNode;
      var cs = getComputedStyle(box);
      var avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var cap = +el.getAttribute('data-cap') || 200;
      var vw = innerWidth;
      if (el.getAttribute('data-cap') === '200') cap = Math.min(200, Math.max(48, vw * 0.11));
      el.style.fontSize = '100px';
      var w = el.getBoundingClientRect().width;
      if (!w) return;
      var s = Math.min(cap, (100 * avail) / w);
      el.style.fontSize = Math.max(10, Math.floor(s * 10) / 10) + 'px';
    });
  }
  function fitNums() {
    Array.prototype.forEach.call(d.querySelectorAll('.stats dd, .badge dd'), function (el) {
      el.style.fontSize = '';
      var box = el.parentNode, cs = getComputedStyle(box);
      var avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var w = el.scrollWidth;
      if (w > avail) el.style.fontSize = Math.max(11, Math.floor(parseFloat(getComputedStyle(el).fontSize) * avail / w * 10) / 10) + 'px';
    });
  }
  var raf = 0;
  function sched() { cancelAnimationFrame(raf); raf = requestAnimationFrame(function () { fit(); fitNums(); }); }
  fit(); fitNums();
  addEventListener('resize', sched);
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(function () { fit(); fitNums(); });
  addEventListener('load', function () { fit(); fitNums(); });

  /* sticker dragging: pick up, move around the slab, elastic drop. A click still opens the link. */
  var zTop = 100;
  Array.prototype.forEach.call(d.querySelectorAll('.wall'), function (wall) {
    var slab = wall.closest('.slab');
    var all = [];
    Array.prototype.forEach.call(wall.querySelectorAll('.sticker'), function (s) {
      var dx = 0, dy = 0, sx = 0, sy = 0, bx = 0, by = 0, pid = null, moved = false, block = false;
      all.push(function () { dx = 0; dy = 0; s.style.setProperty('--dx', '0px'); s.style.setProperty('--dy', '0px'); });
      s.addEventListener('dragstart', function (e) { e.preventDefault(); });
      s.addEventListener('pointerdown', function (e) {
        if (e.button > 0) return;
        pid = e.pointerId; sx = e.clientX; sy = e.clientY; bx = dx; by = dy; moved = false; block = false;
      });
      s.addEventListener('pointermove', function (e) {
        if (e.pointerId !== pid) return;
        var mx = e.clientX - sx, my = e.clientY - sy;
        if (!moved) {
          if (Math.hypot(mx, my) < 6) return;
          moved = true;
          try { s.setPointerCapture(pid); } catch (x) {}
          s.classList.add('is-drag');
          s.parentNode.style.zIndex = ++zTop;
        }
        dx = bx + mx; dy = by + my;
        s.style.setProperty('--dx', dx + 'px'); s.style.setProperty('--dy', dy + 'px');
        var r = s.getBoundingClientRect(), b = slab.getBoundingClientRect(), fx = 0, fy = 0;
        if (r.left < b.left + 4) fx = b.left + 4 - r.left; else if (r.right > b.right - 4) fx = b.right - 4 - r.right;
        if (r.top < b.top + 4) fy = b.top + 4 - r.top; else if (r.bottom > b.bottom - 4) fy = b.bottom - 4 - r.bottom;
        if (fx || fy) { dx += fx; dy += fy; s.style.setProperty('--dx', dx + 'px'); s.style.setProperty('--dy', dy + 'px'); }
        e.preventDefault();
      });
      function end(e) {
        if (e.pointerId !== pid) return;
        pid = null;
        if (moved) { block = true; s.classList.remove('is-drag'); setTimeout(function () { block = false; }, 60); }
      }
      s.addEventListener('pointerup', end);
      s.addEventListener('pointercancel', end);
      s.addEventListener('click', function (e) { if (block) { e.preventDefault(); e.stopPropagation(); block = false; } });
    });
    var tidy = slab.querySelector('.tidy');
    if (tidy) tidy.addEventListener('click', function () { all.forEach(function (f) { f(); }); });
  });

  /* case cards pop in once */
  var cards = d.querySelectorAll('.case');
  if (cards.length) {
    if (reduce.matches || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(cards, function (c) { c.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
      }, { rootMargin: '0px 0px -8% 0px' });
      Array.prototype.forEach.call(cards, function (c) { io.observe(c); });
      setTimeout(function () { Array.prototype.forEach.call(cards, function (c) { if (!c.classList.contains('in') && c.getBoundingClientRect().top < innerHeight) c.classList.add('in'); }); }, 900);
      /* a deep link must never land on a hidden card */
      addEventListener('hashchange', function () { var t = d.getElementById(location.hash.slice(1)); if (t && t.classList.contains('case')) t.classList.add('in'); });
      var h0 = d.getElementById(location.hash.slice(1)); if (h0 && h0.classList && h0.classList.contains('case')) h0.classList.add('in');
    }
  }

  /* before / after sliders */
  Array.prototype.forEach.call(d.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* copy the email */
  var cb = d.getElementById('copy');
  if (cb) cb.addEventListener('click', function () {
    var t = cb.getAttribute('data-copy'), st = d.getElementById('copystat');
    function ok(m) { if (st) st.textContent = m; setTimeout(function () { if (st) st.textContent = ''; }, 2200); }
    function fallback() {
      var ta = d.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;left:-9999px;top:0';
      d.body.appendChild(ta); ta.select();
      var good = false; try { good = d.execCommand('copy'); } catch (e) {}
      d.body.removeChild(ta); ok(good ? 'Copied!' : 'Select the text and copy it');
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function () { ok('Copied!'); }, fallback);
    else fallback();
  });

  /* Esc on a room page goes Home */
  if (d.body.classList.contains('room')) addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !e.defaultPrevented && !/^(INPUT|TEXTAREA|SELECT)$/.test((d.activeElement || {}).tagName || '')) location.href = '../index.html';
  });
})();
