/* MPWP 5.1: keyboard shortcuts, List Files bar, status line, Reveal Codes, Print Preview. Plain JS. */
(function () {
  'use strict';
  var D = document, H = D.documentElement, B = D.body;
  var $ = function (s, r) { return (r || D).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || D).querySelectorAll(s)); };
  var home = B.getAttribute('data-page') === 'home';
  var store = function (k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* boot: a 1.2 s overlay, skipped by any key or click */
  if (H.classList.contains('booting')) {
    var done = false, t;
    var end = function () {
      if (done) return; done = true; clearTimeout(t);
      H.classList.remove('booting');
      try { sessionStorage.setItem('mpwp-boot', '1'); } catch (e) {}
      D.removeEventListener('keydown', skip, true); D.removeEventListener('pointerdown', skip, true);
    };
    var skip = function (e) { e.preventDefault(); e.stopPropagation(); end(); };
    D.addEventListener('keydown', skip, true); D.addEventListener('pointerdown', skip, true);
    t = setTimeout(end, 1250);
  }

  /* bar height -> CSS var */
  var bars = $('#bars');
  var size = function () { H.style.setProperty('--bars', bars.offsetHeight + 'px'); };
  size(); addEventListener('resize', size);
  if (window.ResizeObserver) new ResizeObserver(size).observe(bars);

  /* theme: blue screen by default, Print Preview on request */
  var pbtn = $('#k-print');
  var setTheme = function (t, save) {
    H.setAttribute('data-theme', t);
    if (save) store('mpwp-theme', t);
    if (pbtn) pbtn.setAttribute('aria-pressed', t === 'print' ? 'true' : 'false');
    var m = $('meta[name="theme-color"]'); if (m) m.setAttribute('content', t === 'print' ? '#8a8a8a' : '#0a1a96');
  };
  setTheme(H.getAttribute('data-theme') === 'print' ? 'print' : 'dos', false);
  pbtn.addEventListener('click', function () { setTheme(H.getAttribute('data-theme') === 'print' ? 'dos' : 'print', true); });

  /* panels + reveal codes */
  var CD = {}; try { CD = JSON.parse($('#codes-data').textContent || '{}'); } catch (e) {}
  var cur = null, openPanel = null, lastFocus = null;
  var codes = $('#codes'), kc = $('#k-codes');
  var code = function (t) { var s = D.createElement('span'); s.className = 'cd'; s.textContent = '[' + t + ']'; return s; };
  var line = function (parts) {
    var d = D.createElement('div');
    parts.forEach(function (p) { d.appendChild(typeof p === 'string' ? D.createTextNode(p) : p); });
    $('#codes-body').appendChild(d);
  };
  var renderCodes = function () {
    var b = $('#codes-body'); b.textContent = '';
    var c = cur && CD[cur];
    if (!c) { line([code('Open Style:Directory'), ' Move the bar over a file, or scroll to a case, to see its codes ', code('HRt')]); return; }
    var t = D.createElement('span'); t.className = 'cd-t'; t.textContent = c.t;
    line([code('Open Style:Case'), code('Bold'), t, code('bold'), code('HRt')]);
    line(c.k.map(function (k) { return code('Kicker:' + k); }).concat([code('HRt')]));
    line([code('Sub:' + c.s), code('HRt')]);
    line([code('Id:' + c.id), code('Count:' + c.n), code('HRt')]);
    if (c.l.length) line(c.l.map(function (l) { return code('Link:' + l); }).concat([code('HRt')]));
  };
  var setCodes = function (on) {
    codes.hidden = !on; kc.setAttribute('aria-pressed', on ? 'true' : 'false');
    if (on) renderCodes();
    H.style.setProperty('--codes-h', on ? codes.offsetHeight + 'px' : '0px');
  };
  kc.addEventListener('click', function () { setCodes(codes.hidden); });
  var setCur = function (id) { if (id === cur) return; cur = id; if (!codes.hidden) { renderCodes(); H.style.setProperty('--codes-h', codes.offsetHeight + 'px'); } };
  var showPanel = function (id) {
    closePanel(); var p = $('#' + id); if (!p) return;
    lastFocus = D.activeElement; p.hidden = false; openPanel = p;
    var f = $('a,button', p); if (f) f.focus();
  };
  var closePanel = function () {
    if (!openPanel) return false;
    openPanel.hidden = true; openPanel = null;
    if (lastFocus && lastFocus.focus) lastFocus.focus(); return true;
  };
  $$('.pclose').forEach(function (b) { b.addEventListener('click', closePanel); });
  $('#k-help').addEventListener('click', function () { showPanel('p-help'); });
  $('#k-rooms').addEventListener('click', function (e) { e.preventDefault(); showPanel('p-rooms'); });

  /* lightbox for figures */
  var lb = null;
  var closeLb = function () { if (!lb) return false; lb.remove(); lb = null; return true; };
  D.addEventListener('click', function (e) {
    var i = e.target;
    if (i.tagName !== 'IMG' || !i.closest('.cbody') || i.closest('.compare') || i.closest('a')) return;
    lb = D.createElement('div'); lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-label', 'Enlarged figure');
    var im = D.createElement('img'); im.src = i.currentSrc || i.src; im.alt = i.alt; lb.appendChild(im);
    lb.addEventListener('click', closeLb); B.appendChild(lb);
  });

  /* before/after sliders */
  $$('.compare').forEach(function (c) {
    var r = $('input', c); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* status line + cursor */
  var secs = $$('[data-file]'), heads = $$('main h1, main h2, main h3'), curHead = null, rowFile = null;
  var stFile = $('#st-file'), stPg = $('#st-pg'), stLn = $('#st-ln'), tick = false;
  var update = function () {
    tick = false;
    var y = innerHeight * 0.35, s = secs[0], i;
    for (i = 0; i < secs.length; i++) { if (secs[i].getBoundingClientRect().top <= y) s = secs[i]; else break; }
    if (!s) return;
    var file = s.getAttribute('data-file');
    if (home && s.id === 'files' && rowFile) file = rowFile;
    var cut = file.lastIndexOf('\\') + 1; stFile.textContent = ''; var dp = D.createElement('span'); dp.className = 'dp'; dp.textContent = file.slice(0, cut); stFile.appendChild(dp); stFile.appendChild(D.createTextNode(file.slice(cut))); stPg.textContent = s.getAttribute('data-pg');
    stLn.textContent = (1 + Math.max(0, y - s.getBoundingClientRect().top) / 96).toFixed(2) + '"';
    if (!home && s.getAttribute('data-id')) setCur(s.getAttribute('data-id'));
    else if (!home) setCur(null);
    var h = heads[0], lim = innerHeight * 0.45;
    for (i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top <= lim) h = heads[i]; else break; }
    if (h !== curHead) { if (curHead) curHead.classList.remove('has-cur'); curHead = h; if (h) h.classList.add('has-cur'); }
  };
  var req = function () { if (!tick) { tick = true; requestAnimationFrame(update); } };
  addEventListener('scroll', req, { passive: true }); addEventListener('resize', req); update();

  /* home: List Files bar (roving tabindex, aria-current follows focus) */
  var rows = home ? $$('.lf-list .lf-row') : [], idx = 0, touched = false;
  var go = function (n, focus) {
    if (!rows.length) return;
    n = Math.max(0, Math.min(rows.length - 1, n));
    rows.forEach(function (r, k) { r.tabIndex = k === n ? 0 : -1; if (k === n) r.setAttribute('aria-current', 'true'); else r.removeAttribute('aria-current'); });
    idx = n; if (touched) rowFile = rows[n].getAttribute('data-path'); setCur(rows[n].getAttribute('data-id'));
    if (focus) rows[n].focus();
    req();
  };
  if (rows.length) {
    go(0, false);
    var nextDir = function (from, dir) { for (var k = from + dir; k >= 0 && k < rows.length; k += dir) if (rows[k].classList.contains('is-dir')) return k; return -1; };
    $('.lf-list').addEventListener('focusin', function (e) { var k = rows.indexOf(e.target.closest('.lf-row')); touched = true; if (k >= 0) go(k, false); });
    $('.lf-list').addEventListener('mouseover', function (e) {
      var r = e.target.closest('.lf-row'); if (!r || !matchMedia('(hover:hover)').matches) return;
      var k = rows.indexOf(r); touched = true; if (k >= 0 && k !== idx) { go(k, false); r.focus({ preventScroll: true }); }
    });
    $('.lf-list').addEventListener('keydown', function (e) {
      var k = e.key, n = null;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (k === 'ArrowDown') n = idx + 1; else if (k === 'ArrowUp') n = idx - 1;
      else if (k === 'Home') n = 0; else if (k === 'End') n = rows.length - 1;
      else if (k === 'PageDown') n = idx + 8; else if (k === 'PageUp') n = idx - 8;
      else if (k === 'Tab') { var d = nextDir(idx, e.shiftKey ? -1 : 1); if (d < 0) return; n = d; }
      if (n === null) return;
      e.preventDefault(); go(n, true);
    });
  }

  if (!home) { stFile.title = 'Back to the homepage'; stFile.addEventListener('click', function () { location.href = $('#k-home').href; }); }

  /* shortcuts: letters only, never while typing, no F-keys */
  D.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return;
    var t = e.target;
    if (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) return;
    var k = e.key;
    if (k === 'Escape') { if (closeLb() || closePanel()) return; if (!codes.hidden) { setCodes(false); return; } if (!home) location.href = $('#k-home').href; return; }
    if (k === '?') { showPanel('p-help'); e.preventDefault(); return; }
    switch (k.toLowerCase()) {
      case 'l':
        if (home) { $('#files').scrollIntoView(); if (rows.length) rows[idx].focus({ preventScroll: true }); } else location.href = $('#k-list').href;
        break;
      case 'o': showPanel('p-rooms'); break;
      case 'r': setCodes(codes.hidden); break;
      case 'p': pbtn.click(); break;
      case 'h': location.href = $('#k-home').href; break;
      case 'x': location.href = $('#k-exit').href; break;
    }
  });
  addEventListener('resize', function () { if (!codes.hidden) H.style.setProperty('--codes-h', codes.offsetHeight + 'px'); });
})();
