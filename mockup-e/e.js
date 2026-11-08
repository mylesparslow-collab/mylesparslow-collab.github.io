/* Case File: theme toggle, settle-in, compare sliders, Esc to go Home. */
(function () {
  'use strict';
  var root = document.documentElement;
  var btn = document.getElementById('themebtn');
  function paint() {
    var dark = root.getAttribute('data-theme') === 'dark';
    if (btn) { btn.setAttribute('aria-pressed', dark ? 'true' : 'false'); btn.setAttribute('aria-label', dark ? 'Light desk' : 'Dark desk'); }
  }
  if (btn) {
    btn.addEventListener('click', function () {
      var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', t);
      try { localStorage.setItem('cf-theme', t); } catch (e) {}
      paint();
    });
  }
  paint();

  /* papers settle in once, stickers press on once */
  var els = document.querySelectorAll('.sheet, .exhibit');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.02 });
    Array.prototype.forEach.call(els, function (el) { io.observe(el); });
  } else {
    Array.prototype.forEach.call(els, function (el) { el.classList.add('in'); });
  }

  /* before / after sliders */
  Array.prototype.forEach.call(document.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* keep the current tab in view in the scrolling tab row */
  var cur = document.querySelector('.tab.is-cur');
  if (cur && cur.scrollIntoView && cur.parentNode.scrollWidth > cur.parentNode.clientWidth) {
    cur.parentNode.scrollLeft = cur.offsetLeft - 40;
  }

  /* Esc closes the folder and returns Home (rooms only) */
  if (document.body.getAttribute('data-page') === 'room') {
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      var t = e.target, n = t && t.tagName;
      if (n === 'INPUT' || n === 'TEXTAREA' || n === 'SELECT' || (t && t.isContentEditable)) return;
      if (document.fullscreenElement) return;
      var home = document.querySelector('.tab--home');
      if (home) location.href = home.getAttribute('href');
    });
  }
})();
