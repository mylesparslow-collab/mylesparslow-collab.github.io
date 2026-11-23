/* Mockup O, "Civitas". Source: themed/o/o.js, copied to mockup-o/ by themed/render_o.py. No libraries.
   The pages work without it: every building on the map is a real link, every list is plain HTML.
   It adds the theme switch, the copy button, the random project, the before/after sliders and, on the map,
   the note beside a building, the gentle tilt on desktop and the building-to-building walk on phones. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  function qsa(s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); }
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---------- theme ---------- */
  var tb = d.getElementById('theme');
  if (tb) tb.addEventListener('click', function () {
    var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', t);
    try { localStorage.setItem('mpo-theme', t); } catch (e) {}
  });

  /* ---------- the buildings menu closes on Escape or a click elsewhere ---------- */
  var menu = d.querySelector('.bar__menu');
  if (menu) {
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); } });
    d.addEventListener('click', function (e) { if (menu.open && !menu.contains(e.target)) menu.open = false; });
  }

  /* ---------- copy the address ---------- */
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

  /* ---------- a random project ---------- */
  var sp = d.getElementById('surprise');
  if (sp) sp.addEventListener('click', function () {
    var all = qsa('.ser li > a');
    if (all.length) location.href = all[Math.floor(Math.random() * all.length)].getAttribute('href');
  });

  /* ---------- before / after sliders ---------- */
  qsa('.compare').forEach(function (c) {
    var r = c.querySelector('input'); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* ---------- the map ---------- */
  var frame = d.getElementById('frame'), plate = d.getElementById('plate'), note = d.getElementById('note');
  var dataEl = d.getElementById('walk-data');
  if (frame && plate && dataEl) {
    var B = JSON.parse(dataEl.textContent), byKey = {};
    B.forEach(function (b) { byKey[b.k] = b; b.a = d.getElementById('cv-' + b.k); });
    var panning = function () { return frame.scrollWidth > frame.clientWidth + 4; };

    /* the note beside a building (desktop): name, what it holds, and the way in */
    var hideT = 0;
    function showNote(b) {
      if (!note || !b.a || panning()) return;
      clearTimeout(hideT);
      note.querySelector('.note__n').textContent = b.a.getAttribute('data-n');
      note.querySelector('.note__s').textContent = b.a.getAttribute('data-s');
      note.setAttribute('href', b.a.getAttribute('href'));
      var bx = b.bx, right = bx[0] + bx[2];
      note.hidden = false;
      if (right < 0.78) { note.style.left = (right * 100 + 0.4) + '%'; note.style.right = 'auto'; }
      else { note.style.left = 'auto'; note.style.right = ((1 - bx[0]) * 100 + 0.4) + '%'; }
      note.style.top = Math.max(1, bx[1] * 100 + 2) + '%';
    }
    function hideNote() { hideT = setTimeout(function () { if (note) note.hidden = true; }, 160); }
    B.forEach(function (b) {
      if (!b.a) return;
      b.a.addEventListener('pointerenter', function () { showNote(b); });
      b.a.addEventListener('pointerleave', hideNote);
      b.a.addEventListener('focus', function () { showNote(b); });
      b.a.addEventListener('blur', hideNote);
    });
    if (note) {
      note.addEventListener('pointerenter', function () { clearTimeout(hideT); });
      note.addEventListener('pointerleave', hideNote);
    }

    /* the tilt: a few degrees toward the pointer, desktop only, never with reduced motion */
    if (finePointer && !reduced) {
      var tx = 0, ty = 0, cx = 0, cy = 0, raf = 0;
      var step = function () {
        cx += (tx - cx) * 0.12; cy += (ty - cy) * 0.12;
        if (Math.abs(tx - cx) < 0.002 && Math.abs(ty - cy) < 0.002) { cx = tx; cy = ty; raf = 0; }
        plate.style.transform = (cx === 0 && cy === 0) ? '' : 'perspective(2600px) rotateX(' + (-cy * 1.6).toFixed(3) + 'deg) rotateY(' + (cx * 2.2).toFixed(3) + 'deg)';
        if (raf) raf = requestAnimationFrame(step);
      };
      var kick = function () { if (!raf) raf = requestAnimationFrame(step); };
      frame.addEventListener('pointermove', function (e) {
        if (panning()) return;
        var r = frame.getBoundingClientRect();
        tx = (e.clientX - r.left) / r.width * 2 - 1; ty = (e.clientY - r.top) / r.height * 2 - 1;
        plate.classList.add('tilt'); kick();
      });
      frame.addEventListener('pointerleave', function () { tx = 0; ty = 0; kick(); });
    }

    /* the walk (phones): Previous / Next building, and the map pans to it */
    var walk = d.getElementById('walk'), cur = d.getElementById('w-cur'), i = Math.max(0, B.map(function (b) { return b.k; }).indexOf('cathedral'));
    function centre(b) {
      frame.scrollLeft = b.x * plate.offsetWidth - frame.clientWidth / 2;
      frame.scrollTop = b.y * plate.offsetHeight - frame.clientHeight / 2;
    }
    function say(b) {
      if (!cur || !b.a) return;
      cur.innerHTML = '';
      var a = d.createElement('a'); a.href = b.a.getAttribute('href'); a.textContent = b.a.getAttribute('data-n');
      var s = d.createElement('span'); s.textContent = b.a.getAttribute('data-s');
      cur.appendChild(a); cur.appendChild(s);
    }
    function setup() {
      if (panning()) {
        if (walk) walk.hidden = false;
        if (note) note.hidden = true;
        centre(B[i]); say(B[i]);
      } else if (walk) walk.hidden = true;
    }
    function go(k) { i = (i + k + B.length) % B.length; centre(B[i]); say(B[i]); }
    var pv = d.getElementById('w-prev'), nx = d.getElementById('w-next');
    if (pv) pv.addEventListener('click', function () { go(-1); });
    if (nx) nx.addEventListener('click', function () { go(1); });
    setup();
    var rt = 0;
    addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(setup, 150); });
  }

  /* a deep link lands again once the fonts have settled the layout */
  if (location.hash.length > 1 && d.fonts && d.fonts.ready) d.fonts.ready.then(function () {
    var t = d.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView();
  });
})();
