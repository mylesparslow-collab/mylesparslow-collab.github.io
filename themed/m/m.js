/* Mockup M, "Redline". Drives the view switch, the reviewer filter, the theme, the review menu, the copy button,
   the before/after sliders and the random project. The page works without any of it: every sentence is already
   attributed in the markup that the generator writes. */
(function () {
  'use strict';
  var d = document, de = d.documentElement;
  function qs(s, r) { return (r || d).querySelector(s); }
  function qsa(s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); }
  function save(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  /* ---------- the key starts folded on phones, so the pitch is the first thing read ---------- */
  if (window.matchMedia && matchMedia('(max-width: 640px)').matches) qsa('details.bal--key').forEach(function (k) { k.removeAttribute('open'); });

  /* ---------- theme ---------- */
  var themeBtn = d.getElementById('theme');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var next = de.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    de.setAttribute('data-theme', next); save('mpm-theme', next);
  });

  /* ---------- review menu (narrow screens) ---------- */
  var bar = d.getElementById('rb'), menu = d.getElementById('menu');
  function setMenu(open) {
    if (!bar || !menu) return;
    bar.classList.toggle('rb--open', open);
    menu.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (menu) {
    menu.addEventListener('click', function () { setMenu(menu.getAttribute('aria-expanded') !== 'true'); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape') { setMenu(false); setPop(false); } });
    d.addEventListener('click', function (e) { if (bar.classList.contains('rb--open') && !bar.contains(e.target)) setMenu(false); });
    qsa('.rb__arts a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  }

  /* ---------- markup view: All markup / No markup ---------- */
  var vAll = d.getElementById('v-all'), vClean = d.getElementById('v-clean');
  function anchorTop() {                                // the element at the top of the window, so the page does not jump when the layout changes width
    var best = null, y = 80;
    qsa('.sec,.art,.term,.row').forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top <= y && r.bottom > y) best = { el: el, off: r.top };
    });
    return best;
  }
  function setView(v, keep) {
    var a = keep ? anchorTop() : null;
    de.setAttribute('data-view', v);
    if (vAll) vAll.setAttribute('aria-pressed', v === 'all' ? 'true' : 'false');
    if (vClean) vClean.setAttribute('aria-pressed', v === 'clean' ? 'true' : 'false');
    if (a) window.scrollBy(0, a.el.getBoundingClientRect().top - a.off);
    save('mpm-view', v);
  }
  if (vAll && vClean) {
    setView(de.getAttribute('data-view') === 'clean' ? 'clean' : 'all', false);
    vAll.addEventListener('click', function () { setView('all', true); });
    vClean.addEventListener('click', function () { setView('clean', true); });
  }

  /* ---------- reviewer filter ---------- */
  var revBtn = d.getElementById('rev-btn'), pop = d.getElementById('rev-pop'), cur = d.getElementById('rev-cur'), status = d.getElementById('rev-status');
  function setPop(open) {
    if (!revBtn) return;
    revBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (revBtn) {
    revBtn.addEventListener('click', function () { setPop(revBtn.getAttribute('aria-expanded') !== 'true'); });
    d.addEventListener('click', function (e) { if (pop && !pop.contains(e.target) && !revBtn.contains(e.target)) setPop(false); });
  }
  var chips = qsa('.chip[data-rev]');
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      var who = c.getAttribute('data-rev');
      if (who === 'all') de.removeAttribute('data-rev'); else {
        de.setAttribute('data-rev', who);
        if (de.getAttribute('data-view') === 'clean') setView('all', true);
      }
      chips.forEach(function (o) { o.setAttribute('aria-pressed', o === c ? 'true' : 'false'); });
      var name = who === 'all' ? 'everyone' : qs('.chip__t', c).textContent;
      if (cur) cur.textContent = name.toLowerCase() === 'local models' ? 'local models' : name === 'everyone' ? 'everyone' : name;
      if (status) {
        var n = who === 'all' ? 0 : qsa('.ix li[data-authors~="' + who + '"], .sec[data-authors~="' + who + '"]').length;
        status.textContent = who === 'all' ? 'Showing everyone’s changes.' : 'Showing changes by ' + name + ': ' + n + (n === 1 ? ' project.' : ' projects.');
      }
      setPop(false);
    });
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
    var all = qsa('.ix li a.ix__a'); if (all.length) location.href = all[Math.floor(Math.random() * all.length)].getAttribute('href');
  });

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

  /* a deep link lands again once the fonts have settled the layout */
  if (location.hash.length > 1 && d.fonts && d.fonts.ready) d.fonts.ready.then(function () {
    var t = d.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView();
  });
})();
