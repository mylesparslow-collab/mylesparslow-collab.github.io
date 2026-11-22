/* Mockup N, "Flipbook": page chrome. Source: themed/n/n.js, copied to mockup-n/ by themed/render_n.py.
   Theme switch, scenes menu on small screens, before/after sliders, a random project, copy the email.
   The viewer is in flip.js. No libraries. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var qsa = function (s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); };

  /* ---------- light and dark ---------- */
  var th = d.getElementById('theme');
  if (th) th.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('mpn-theme', next); } catch (e) {}
    d.dispatchEvent(new CustomEvent('mpn-theme'));
  });

  /* ---------- scenes menu (small screens) ---------- */
  var menu = d.getElementById('menu'), scenes = d.getElementById('scenes');
  if (menu && scenes) {
    var shut = function () { scenes.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); };
    menu.addEventListener('click', function (e) {
      e.stopPropagation();
      var o = !scenes.classList.contains('open');
      scenes.classList.toggle('open', o); menu.setAttribute('aria-expanded', o ? 'true' : 'false');
    });
    d.addEventListener('click', function (e) { if (!scenes.contains(e.target)) shut(); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape') { shut(); menu.focus(); } });
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
    var all = qsa('#index .xr__a'); if (all.length) location.href = all[Math.floor(Math.random() * all.length)].getAttribute('href');
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
})();
