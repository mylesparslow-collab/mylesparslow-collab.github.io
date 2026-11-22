/* Mockup L, "Tesserae". Source: themed/l/l.js, copied to mockup-l/ by themed/render_l.py. No libraries.
   The wall itself is wall.js (a module); this file is the page: theme, rooms menu, index, sliders, copy, room list. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var qsa = function (s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); };

  /* ---------- theme (wall.js listens for mpl-theme and re-reads the glass colours) ---------- */
  var tb = d.getElementById('theme');
  if (tb) tb.addEventListener('click', function () {
    var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', t);
    try { localStorage.setItem('mpl-theme', t); } catch (e) {}
    d.dispatchEvent(new CustomEvent('mpl-theme'));
  });

  /* ---------- rooms menu on small screens ---------- */
  var bar = d.getElementById('nav'), menu = d.getElementById('menu');
  if (bar && menu) {
    var setOpen = function (on) { bar.classList.toggle('is-open', on); menu.setAttribute('aria-expanded', on ? 'true' : 'false'); };
    menu.addEventListener('click', function () {
      var on = !bar.classList.contains('is-open'); setOpen(on);
      if (on) { var a = bar.querySelector('.bar__rooms a'); if (a) a.focus(); }
    });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && bar.classList.contains('is-open')) { setOpen(false); menu.focus(); } });
    d.addEventListener('click', function (e) { if (!bar.contains(e.target)) setOpen(false); });
    bar.addEventListener('focusout', function () { setTimeout(function () { if (!bar.contains(d.activeElement)) setOpen(false); }, 0); });
  }

  /* ---------- skip link and in-page jumps move focus, not just the scroll ---------- */
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a || a.getAttribute('href').length < 2) return;
    var t = d.getElementById(a.getAttribute('href').slice(1));
    if (!t) return;
    if (!t.hasAttribute('tabindex') && !/^(A|BUTTON|INPUT|SUMMARY)$/.test(t.tagName)) t.setAttribute('tabindex', '-1');
    setTimeout(function () { t.focus({ preventScroll: true }); }, 0);
  });
  if (location.hash.length > 1 && d.fonts && d.fonts.ready) d.fonts.ready.then(function () {
    var t = d.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView();
  });

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

  /* ---------- the index: by room or A to Z ---------- */
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

  /* ---------- room list: fold on small screens, mark the project on screen ---------- */
  var list = d.getElementById('list');
  if (list && 'IntersectionObserver' in window) {
    var det = list.querySelector('details'), mq = matchMedia('(max-width: 1100px)');
    var fold = function () { if (det) det.open = !mq.matches; };
    fold(); if (mq.addEventListener) mq.addEventListener('change', fold);
    if (det) det.querySelector('summary').addEventListener('click', function (e) { if (!mq.matches) e.preventDefault(); });
    var links = {}, cur = null;
    qsa('ol a', list).forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var mark = function (id) {
      if (id === cur || !links[id]) return;
      if (cur && links[cur]) links[cur].removeAttribute('aria-current');
      cur = id; var a = links[id]; a.setAttribute('aria-current', 'true');
      if (!mq.matches) {
        var top = a.getBoundingClientRect().top - list.getBoundingClientRect().top + list.scrollTop;
        if (top < list.scrollTop + 30 || top > list.scrollTop + list.clientHeight - 90) list.scrollTop = top - list.clientHeight / 2;
      }
    };
    var arts = qsa('.case');
    var pick = function () {
      var line = innerHeight * 0.35, id = null;
      for (var i = 0; i < arts.length; i++) { if (arts[i].getBoundingClientRect().top <= line) id = arts[i].id; else break; }
      if (id) mark(id);
    };
    var spy = new IntersectionObserver(function (es) {
      var hit = false; es.forEach(function (e) { if (e.isIntersecting) { hit = true; mark(e.target.id); } });
      if (!hit) pick();
    }, { rootMargin: '-20% 0px -65% 0px' });
    arts.forEach(function (a) { spy.observe(a); });
    if (det) qsa('ol a', list).forEach(function (a) { a.addEventListener('click', function () { if (mq.matches) det.open = false; }); });
  }
})();
