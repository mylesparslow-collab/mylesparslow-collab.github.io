/* Mockup C: theme toggle, floor-plan <-> directory sync, before/after sliders. No libraries. */
(function () {
  'use strict';
  var d = document.documentElement;

  /* theme toggle (the head script already set data-theme, so there is no flash) */
  var btn = document.querySelector('.theme');
  function paint() {
    if (!btn) return;
    var t = d.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    var other = t === 'light' ? 'dark' : 'light';
    btn.setAttribute('aria-label', 'Theme: ' + t + '. Switch to ' + other + '.');
    btn.querySelector('span').textContent = t === 'light' ? 'Light' : 'Dark';
  }
  paint();
  if (btn) btn.addEventListener('click', function () {
    var t = d.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    d.setAttribute('data-theme', t);
    try { localStorage.setItem('mpc-theme', t); } catch (e) {}
    paint();
  });

  /* lobby: hovering or focusing a room on the plan lights its directory column, and the other way round */
  var lobby = document.querySelector('body.lobby');
  if (lobby) {
    var scope = document.querySelectorAll('#plan [data-room], #directory [data-room]');
    var set = function (room, on) {
      Array.prototype.forEach.call(scope, function (el) {
        if (el.getAttribute('data-room') === room) el.classList.toggle('is-hot', on);
      });
    };
    Array.prototype.forEach.call(scope, function (el) {
      var r = el.getAttribute('data-room');
      el.addEventListener('mouseenter', function () { set(r, true); });
      el.addEventListener('mouseleave', function () { set(r, false); });
      el.addEventListener('focusin', function () { set(r, true); });
      el.addEventListener('focusout', function () { set(r, false); });
    });
  }

  /* room pages: fit the giant room word to one line and size the plate to the word */
  function fit() {
    var g = document.querySelector('.giant');
    if (!g) return;
    var l = g.firstElementChild, top = g.parentNode, cs = getComputedStyle(g);
    var avail = g.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    g.style.fontSize = '100px';
    var w = l.getBoundingClientRect().width;
    if (!w || !avail) return;
    g.style.fontSize = Math.min(100 * avail / w * 0.995, innerWidth * 0.30) + 'px';
    var p = top.querySelector('.plate');
    if (!p) return;
    if (innerWidth > 1100) {
      p.style.setProperty('--plate-w', Math.max(160, Math.min(380, innerWidth * 0.2)) + 'px');
      top.style.setProperty('--hang', Math.round(p.getBoundingClientRect().height * 0.5) + 'px');
    } else { p.style.removeProperty('--plate-w'); top.style.removeProperty('--hang'); }
  }
  if (document.querySelector('.giant')) {
    fit();
    window.addEventListener('resize', fit);
    window.addEventListener('load', fit);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  }

  /* room = a sheet opened out of the floor plan: backdrop click, Esc or the close button go back to the plan */
  if (document.getElementById('sheet')) {
    var plan = '../index.html#plan';
    document.addEventListener('click', function (e) {
      if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var t = e.target;
      if (!t.closest || t.closest('.sheet') || t.closest('.wf')) return;
      location.href = plan;
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || e.defaultPrevented || document.fullscreenElement) return;
      if (e.target.closest && e.target.closest('input,textarea,select')) return;
      location.href = plan;
    });
  }

  /* before / after sliders: a range input drives --pos */
  Array.prototype.forEach.call(document.querySelectorAll('.compare'), function (c) {
    var r = c.querySelector('input');
    if (!r) return;
    var upd = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', upd); upd();
  });
})();
