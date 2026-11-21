/* Mockup K, "Liner Notes". Source: themed/k/k.js, copied to mockup-k/ by themed/render_k.py. No libraries. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var qsa = function (s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); };
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var raf = window.requestAnimationFrame || function (f) { return setTimeout(f, 16); };

  /* ---------- theme ---------- */
  var tb = d.getElementById('theme');
  if (tb) tb.addEventListener('click', function () {
    var t = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', t);
    try { localStorage.setItem('mpk-theme', t); } catch (e) {}
  });

  /* ---------- records menu on small screens ---------- */
  var top = d.getElementById('nav'), menu = d.getElementById('menu');
  if (top && menu) {
    var setOpen = function (on) { top.classList.toggle('is-open', on); menu.setAttribute('aria-expanded', on ? 'true' : 'false'); };
    menu.addEventListener('click', function () {
      var on = !top.classList.contains('is-open'); setOpen(on);
      if (on) { var a = top.querySelector('.top__rooms a'); if (a) a.focus(); }
    });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && top.classList.contains('is-open')) { setOpen(false); menu.focus(); } });
    d.addEventListener('click', function (e) { if (!top.contains(e.target)) setOpen(false); });
    top.addEventListener('focusout', function () { setTimeout(function () { if (!top.contains(d.activeElement)) setOpen(false); }, 0); });
  }

  /* ---------- in-page jumps move focus, not just the scroll ---------- */
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a || a.getAttribute('href').length < 2) return;
    var t = d.getElementById(a.getAttribute('href').slice(1));
    if (!t) return;
    if (t.tagName === 'NAV' && t.querySelector('details')) t.querySelector('details').open = true;
    if (!t.hasAttribute('tabindex') && !/^(A|BUTTON|INPUT|SUMMARY)$/.test(t.tagName)) t.setAttribute('tabindex', '-1');
    setTimeout(function () { t.focus({ preventScroll: true }); }, 0);
  });
  if (location.hash.length > 1 && d.fonts && d.fonts.ready) d.fonts.ready.then(function () {
    var t = d.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView();
  });

  /* ---------- headers settle in: "AI." widens, the room's record slides out ---------- */
  qsa('.hero, .rhead').forEach(function (h) { raf(function () { raf(function () { h.classList.add('is-on'); }); }); });

  /* ---------- the crate: flip through five sleeves ---------- */
  var crate = d.getElementById('crate');
  if (crate) (function () {
    var items = qsa('.sl', crate), n = items.length, cur = 0;
    var now = d.getElementById('crate-now'), ctl = d.getElementById('crate-ctl'), hint = d.getElementById('crate-hint');
    var narrow = matchMedia('(max-width: 900px)');
    if (!n) return;
    ctl.hidden = false; hint.hidden = false;
    function place() {
      var h = items[0].offsetHeight || 400;
      items.forEach(function (li, i) {
        var o = i - cur, t, op = 1;
        if (o === 0) t = 'translate3d(0,' + (-0.05 * h) + 'px,0)';
        else if (o > 0) t = 'translate3d(' + (o * 0.012 * h) + 'px,' + (-0.05 * h - o * 0.105 * h) + 'px,' + (-o * 70) + 'px) rotateX(4deg)';
        else { t = 'translate3d(0,' + (0.1 * h) + 'px,60px) rotateX(-84deg)'; op = o === -1 ? 1 : 0; }
        if (o > 4) op = 0;
        li.style.transform = t; li.style.opacity = op;
        li.style.zIndex = String(n - Math.abs(o));
        li.classList.toggle('is-cur', o === 0);
        var a = li.querySelector('a');
        a.setAttribute('tabindex', o === 0 ? '0' : '-1');
      });
      var a0 = items[cur].querySelector('.sl__a');
      var lead = d.createElement('span'), link = d.createElement('a');
      lead.className = 'vh'; lead.textContent = 'Front of the crate: ';
      link.href = a0.getAttribute('href'); link.textContent = items[cur].querySelector('.sl__t').textContent;
      now.replaceChildren(lead, link, d.createTextNode(' · ' + (cur + 1) + ' of ' + n));
    }
    function go(i, focus) {
      cur = Math.max(0, Math.min(n - 1, i)); place();
      if (focus) items[cur].querySelector('a').focus({ preventScroll: true });
    }
    qsa('[data-d]', ctl).forEach(function (b) { b.addEventListener('click', function () { go(cur + (+b.getAttribute('data-d'))); }); });
    /* a sleeve behind the front one: the first click brings it forward, the next opens it */
    items.forEach(function (li, i) {
      li.querySelector('a').addEventListener('click', function (e) {
        if (narrow.matches) return;
        if (i !== cur) { e.preventDefault(); go(i); }
      });
    });
    crate.addEventListener('keydown', function (e) {
      if (narrow.matches) return;
      var k = e.key;
      if (k === 'ArrowRight' || k === 'ArrowDown') { e.preventDefault(); go(cur + 1, crate.contains(d.activeElement) && d.activeElement.classList.contains('sl__a')); }
      else if (k === 'ArrowLeft' || k === 'ArrowUp') { e.preventDefault(); go(cur - 1, crate.contains(d.activeElement) && d.activeElement.classList.contains('sl__a')); }
      else if (k === 'Home') { e.preventDefault(); go(0, true); }
      else if (k === 'End') { e.preventDefault(); go(n - 1, true); }
    });
    /* the wheel flips one sleeve per notch, and lets the page scroll once the crate is at either end */
    var acc = 0, lock = 0;
    crate.addEventListener('wheel', function (e) {
      if (narrow.matches) return;
      var dir = e.deltaY > 0 ? 1 : -1;
      if ((dir > 0 && cur === n - 1) || (dir < 0 && cur === 0)) return;
      e.preventDefault();
      if (Date.now() < lock) return;
      acc += e.deltaY;
      if (Math.abs(acc) > 40) { go(cur + dir); acc = 0; lock = Date.now() + 380; }
    }, { passive: false });
    /* drag: pull down to flip forward, push up to go back */
    var y0 = null, moved = false;
    crate.addEventListener('pointerdown', function (e) { if (!narrow.matches && e.pointerType !== 'mouse') { y0 = e.clientY; moved = false; } });
    crate.addEventListener('pointermove', function (e) {
      if (y0 === null) return;
      var dy = e.clientY - y0;
      if (Math.abs(dy) > 50) { go(cur + (dy > 0 ? 1 : -1)); y0 = e.clientY; moved = true; }
    });
    var up = function () { y0 = null; };
    crate.addEventListener('pointerup', up); crate.addEventListener('pointercancel', up);
    crate.addEventListener('click', function (e) { if (moved) { e.preventDefault(); moved = false; } }, true);
    /* on a phone the crate is a swipe row: keep "front" in sync for the caption only */
    var reset = function () {
      if (narrow.matches) items.forEach(function (li) { li.style.transform = ''; li.style.opacity = ''; li.style.zIndex = ''; li.querySelector('a').removeAttribute('tabindex'); li.classList.remove('is-cur'); });
      else place();
    };
    if (narrow.addEventListener) narrow.addEventListener('change', reset);
    addEventListener('resize', function () { if (!narrow.matches) place(); });
    reset();
    /* a slow first flip shows what the crate does, once, unless the visitor has already touched it */
    if (!reduced && !narrow.matches) {
      var touched = false;
      ['pointerdown', 'wheel', 'keydown', 'focusin'].forEach(function (ev) { crate.addEventListener(ev, function () { touched = true; }, { once: true }); });
      setTimeout(function () { if (!touched && cur === 0) { go(1); setTimeout(function () { if (!touched && cur === 1) go(0); }, 1300); } }, 1600);
    }
  })();

  /* ---------- before / after sliders ---------- */
  qsa('.compare').forEach(function (c) {
    var r = c.querySelector('input'); if (!r) return;
    var set = function () { c.style.setProperty('--pos', r.value + '%'); };
    r.addEventListener('input', set); set();
  });

  /* ---------- drop the needle anywhere ---------- */
  var sp = d.getElementById('surprise');
  if (sp) sp.addEventListener('click', function () {
    var all = qsa('#byroom ol a'); if (all.length) location.href = all[Math.floor(Math.random() * all.length)].getAttribute('href');
  });

  /* ---------- catalogue: by record or A to Z ---------- */
  var ctl2 = d.getElementById('catctl'), byRoom = d.getElementById('byroom'), byAz = d.getElementById('byaz');
  if (ctl2 && byRoom && byAz) {
    ctl2.hidden = false;
    var bR = d.getElementById('by-room'), bA = d.getElementById('by-az'), made = false;
    var show = function (az) {
      if (az && !made) {
        made = true;
        qsa('ol li', byRoom).sort(function (a, b) { return a.getAttribute('data-t') < b.getAttribute('data-t') ? -1 : 1; }).forEach(function (li) {
          var c = li.cloneNode(true); qsa('.see', c).forEach(function (x) { x.remove(); });
          var rec = li.closest('.rec'); if (rec) c.className = rec.className.match(/lab-\w+/)[0];
          var t = rec && rec.querySelector('.rec__t'); var nn = c.querySelector('.n');
          if (t && nn) nn.setAttribute('title', t.textContent);
          byAz.appendChild(c);
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

  /* ---------- room: the tracklist marks the track on screen; the deck plays the record as you read ---------- */
  var list = d.getElementById('list'), deck = d.getElementById('deck');
  if (list && 'IntersectionObserver' in window) {
    var det = list.querySelector('details'), mq = matchMedia('(max-width: 900px)');
    var fold = function () { if (det) det.open = !mq.matches; };
    fold(); if (mq.addEventListener) mq.addEventListener('change', fold);
    if (det) det.querySelector('summary').addEventListener('click', function (e) { if (!mq.matches) e.preventDefault(); });
    var links = {}, cur = null, nowEl = d.getElementById('deck-now');
    qsa('ol a', list).forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
    var mark = function (id) {
      if (id === cur || !links[id]) return;
      if (cur && links[cur]) links[cur].removeAttribute('aria-current');
      cur = id; var a = links[id]; a.setAttribute('aria-current', 'true');
      var tr = d.getElementById(id);
      if (nowEl && tr && tr.getAttribute('data-trk')) nowEl.textContent = tr.getAttribute('data-trk') + ' ' + tr.querySelector('.trk__t').textContent;
      if (!mq.matches) {
        var y = a.getBoundingClientRect().top - list.getBoundingClientRect().top + list.scrollTop;
        if (y < list.scrollTop + 60 || y > list.scrollTop + list.clientHeight - 80) list.scrollTop = y - list.clientHeight / 3;
      }
    };
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) mark(e.target.id); });
    }, { rootMargin: '-30% 0px -60% 0px' });
    qsa('.trk, .grp .gdiv, .extra section').forEach(function (s) { if (s.id) io.observe(s); });
  }
  if (deck) {
    var rec = d.getElementById('deck-rec'), arm = d.getElementById('deck-arm'), main = d.getElementById('main'), ticking = false;
    var upd = function () {
      ticking = false;
      var y = scrollY, r = main.getBoundingClientRect(), total = Math.max(1, main.offsetHeight - innerHeight);
      var p = Math.min(1, Math.max(0, -r.top / total));
      deck.classList.toggle('is-on', r.top < innerHeight * 0.4 && r.bottom > innerHeight * 0.6);
      if (!reduced) rec.style.transform = 'rotate(' + (y * 0.6) + 'deg)';
      arm.style.setProperty('--arm', (8 + p * 26) + 'deg');
    };
    addEventListener('scroll', function () { if (!ticking) { ticking = true; raf(upd); } }, { passive: true });
    addEventListener('resize', upd); upd();
  }
})();
