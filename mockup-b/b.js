/* Mockup B: workshop with five rooms. GSAP 3.12.5 + ScrollTrigger + Lenis 1.1.13.
   Shared by the homepage and the in-theme room pages (rooms.js adds the case-study bits). */
(function () {
  'use strict';
  var root = document.documentElement;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasG = !!(window.gsap && window.ScrollTrigger);
  var canHover = matchMedia('(hover: hover) and (pointer: fine)').matches;
  var EMAIL_OK = true;
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; }

  /* If the animation libraries failed to load, show everything and keep the rest working. */
  if (!hasG) {
    root.classList.remove('anim', 'loading');
    var ld = $('.loader'); if (ld) ld.style.display = 'none';
    var hh = $('#hero'); if (hh) hh.style.clipPath = 'none';
  }
  var anim = root.classList.contains('anim') && hasG && !reduce;
  if (hasG) gsap.registerPlugin(ScrollTrigger);

  /* ---------- smooth scroll ---------- */
  var lenis = null;
  if (hasG && !reduce && window.Lenis) {
    lenis = new Lenis({ lerp: 0.1, smoothWheel: true });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
    gsap.ticker.lagSmoothing(0);
  }

  /* ---------- theme toggle: light -> dark -> red; the head script has already set data-theme ---------- */
  var THEMES = ['light', 'dark', 'red'], TCOL = { light: '#ebe5da', dark: '#141312', red: '#bf2400' };
  var tbtn = $('.theme'), tlab = $('.theme .sct');
  function curTheme() { var t = root.getAttribute('data-theme'); return THEMES.indexOf(t) < 0 ? 'light' : t; }
  function setTheme(t, persist) {
    root.setAttribute('data-theme', t);
    tlab.textContent = 'In ' + t; tlab.dataset.text = tlab.textContent;
    tbtn.setAttribute('aria-label', 'In ' + t + ' theme. Switch to ' + THEMES[(THEMES.indexOf(t) + 1) % 3] + '.');
    var m = $('meta[name="theme-color"]'); if (m) m.setAttribute('content', TCOL[t]);
    if (persist) store('mpb-theme', t);
  }
  setTheme(curTheme(), false);
  tbtn.addEventListener('click', function () { setTheme(THEMES[(THEMES.indexOf(curTheme()) + 1) % 3], true); });

  /* ---------- scramble (pointerenter only; accessible names are fixed aria-labels) ---------- */
  var GLY = '!<>-_\\/[]{}=+*^?#ABCDEFGHJKLMNPRSTUVWXYZ0123456789';
  function scramble(el, dur) {
    var final = el.dataset.text || (el.dataset.text = el.textContent), len = final.length, t0 = performance.now();
    if (!el.style.minWidth) el.style.minWidth = el.getBoundingClientRect().width + 'px';
    cancelAnimationFrame(el._raf);
    (function step(now) {
      var p = Math.min(1, (now - t0) / (dur * 1000)), s = '';
      for (var i = 0; i < len; i++) { var c = final.charAt(i); s += (c === ' ' || i / len < p) ? c : GLY.charAt((Math.random() * GLY.length) | 0); }
      el.textContent = s;
      if (p < 1) el._raf = requestAnimationFrame(step); else el.textContent = final;
    })(t0);
  }
  if (canHover && !reduce) {
    $$('[data-scramble]').forEach(function (host) {
      var t = $('.sct', host); if (!t) return;
      host.addEventListener('pointerenter', function (e) { if (e.pointerType === 'touch') return; scramble(t, 0.3); });
    });
  }

  /* ---------- hero: project frame, slow crossfade + prev/next (no pointer tracking) ---------- */
  var frame = $('#frame'), fimgs = frame ? $$('img', frame) : [], fbtn = $('.frame__btn'), capN = $('.cap__n'), capS = $('.cap__s');
  var ctlN = $('.ctl__n'), cur = 0, heroVisible = true, hovering = false, lastStep = 0;
  var pad2 = function (n) { return (n < 10 ? '0' : '') + n; };
  if (frame) {
  fimgs.forEach(function (im, i) { im.hidden = false; im.classList.toggle('is-on', i === 0); });
  function show(i) {
    i = (i + fimgs.length) % fimgs.length;
    if (i === cur || !fimgs[i]) return;
    fimgs[cur].classList.remove('is-on'); fimgs[i].classList.add('is-on'); cur = i;
    var im = fimgs[i];
    capN.textContent = im.dataset.n; capS.textContent = im.dataset.s;
    if (ctlN) ctlN.textContent = pad2(i + 1) + ' / ' + pad2(fimgs.length);
    fbtn.setAttribute('aria-label', 'Open project: ' + im.dataset.n + ', ' + im.dataset.s);
    lastStep = performance.now();
  }
  if (ctlN) ctlN.textContent = '01 / ' + pad2(fimgs.length);
  $$('.ctl__b').forEach(function (btn) { btn.addEventListener('click', function () { show(cur + (+btn.dataset.d)); }); });
  frame.addEventListener('pointerenter', function () { hovering = true; });
  frame.addEventListener('pointerleave', function () { hovering = false; lastStep = performance.now(); });
  if (!reduce) {
    setInterval(function () {
      if (!heroVisible || document.hidden || hovering) return;
      if (performance.now() - lastStep >= 3500) show(cur + 1);
    }, 250);
  }
  if ('IntersectionObserver' in window) new IntersectionObserver(function (en) { heroVisible = en[0].isIntersecting; }).observe($('#hero'));
  fbtn.addEventListener('click', function () { go(new URL(fimgs[cur].dataset.h, location.href).href); });
  }

  /* ---------- page transition: wavy red curtain ---------- */
  var cur$ = $('#cur'), curtain = $('.curtain'), leaving = false, leaveT = 0, cp = { p: 0 };
  function curD(p) {
    var L = 118 * (1 - p) - 8 * p, a = 16 * (1 - p), y = function (k) { return (L + (k % 2 ? a : -a)).toFixed(2); };
    return 'M0 ' + L.toFixed(2) + ' Q10 ' + y(0) + ' 20 ' + L.toFixed(2) + ' Q30 ' + y(1) + ' 40 ' + L.toFixed(2) + ' Q50 ' + y(0) + ' 60 ' + L.toFixed(2) + ' Q70 ' + y(1) + ' 80 ' + L.toFixed(2) + ' Q90 ' + y(0) + ' 100 ' + L.toFixed(2) + ' L100 130 L0 130Z';
  }
  function curSet(p) { cp.p = p; cur$.setAttribute('d', curD(p)); }
  /* arrival: the page opens covered, then the curtain's wavy lower edge lifts away (continues the upward move of the exit) */
  function curU(q) {
    var B = 130 * (1 - q) - 18 * q, a = 16 * Math.sin(Math.PI * q), y = function (k) { return (B + (k % 2 ? a : -a)).toFixed(2); }, b = B.toFixed(2);
    return 'M0 -20 L100 -20 L100 ' + b + ' Q90 ' + y(0) + ' 80 ' + b + ' Q70 ' + y(1) + ' 60 ' + b + ' Q50 ' + y(0) + ' 40 ' + b + ' Q30 ' + y(1) + ' 20 ' + b + ' Q10 ' + y(0) + ' 0 ' + b + 'Z';
  }
  var arrived = root.classList.contains('arriving');
  function arrive(onDone) {
    var o = { q: 0 };
    function end() { root.classList.remove('arriving'); curSet(0); if (onDone) onDone(); }
    if (!hasG || reduce) { end(); return; }
    cur$.setAttribute('d', curU(0));
    gsap.to(o, { q: 1, duration: 0.7, delay: 0.08, ease: 'expo.inOut', onUpdate: function () { cur$.setAttribute('d', curU(o.q)); }, onComplete: end });
  }
  function curReset() {
    if (root.classList.contains('arriving')) return;
    leaving = false; clearTimeout(leaveT);
    if (hasG) gsap.killTweensOf(cp);
    curSet(0); curtain.classList.remove('on');
  }
  function go(href) {
    if (leaving) return;
    if (!hasG || reduce) { location.href = href; return; }
    leaving = true; curSet(0); curtain.classList.add('on');
    try { sessionStorage.setItem('mpb-go', '1'); } catch (e) {}
    gsap.fromTo(cp, { p: 0 }, { p: 1, duration: 0.35, ease: 'power3.inOut', onUpdate: function () { curSet(cp.p); }, onComplete: function () { location.href = href; } });
    leaveT = setTimeout(curReset, 2500); /* navigation did not happen (blocked, download, error) */
  }
  window.addEventListener('pageshow', function () { curReset(); closeMenu(true); });

  /* ---------- link handling ---------- */
  function roomTop(room) {
    var top = $('#rooms').getBoundingClientRect().top + window.scrollY, i, r = $$('.room');
    for (i = 0; i < r.length && r[i] !== room; i++) top += r[i].offsetHeight;
    return top;
  }
  function scrollToHash(h, instant) {
    var el = null; try { el = $(h); } catch (e) {} if (!el) return;
    var y = el.classList.contains('room') ? roomTop(el) : el.getBoundingClientRect().top + window.scrollY;
    y -= parseFloat(getComputedStyle(el).scrollMarginTop) || 0;
    if (lenis) lenis.scrollTo(y, instant ? { immediate: true } : { duration: 1.2, easing: function (t) { return 1 - Math.pow(1 - t, 4); } });
    else window.scrollTo({ top: y, behavior: (reduce || instant) ? 'auto' : 'smooth' });
    try { history.replaceState(null, '', h); } catch (e) {}
    /* move keyboard focus with the jump, so the next Tab continues from the target */
    if (!instant) {
      if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
      try { el.focus({ preventScroll: true }); } catch (e) {}
    }
  }
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest('a'); if (!a) return;
    if (a.hasAttribute('data-copy')) {
      e.preventDefault(); copyMail(a); return;
    }
    var h = a.getAttribute('href'); if (!h) return;
    if (a.target && a.target !== '_self') return;
    if (a.hasAttribute('download')) return;
    if (/^(mailto|tel|javascript):/i.test(h)) return;
    var u; try { u = new URL(a.href, location.href); } catch (er) { return; }
    if (u.origin !== location.origin) return;
    var norm = function (p) { return p.replace(/index\.html$/, ''); };
    var same = norm(u.pathname) === norm(location.pathname) && u.search === location.search;
    if (same && u.hash) { /* hash link on this page */
      e.preventDefault(); closeMenu(false); scrollToHash(u.hash); return;
    }
    if (same) return;
    e.preventDefault(); go(u.href);
  });

  /* ---------- menu overlay ---------- */
  var menu = $('#menu'), mbtn = $('.menu-btn'), mclose = $('.menu__close'), isOpen = false, lastFocus = null;
  var inertEls = [$('#page'), $('#chrome')];
  function setInert(on) { inertEls.forEach(function (el) { if (!el) return; if (on) el.setAttribute('inert', ''); else el.removeAttribute('inert'); }); }
  function openMenu() {
    if (isOpen) return; isOpen = true; lastFocus = document.activeElement;
    menu.classList.add('open'); menu.setAttribute('aria-hidden', 'false'); mbtn.setAttribute('aria-expanded', 'true');
    setInert(true); if (lenis) lenis.stop();
    if (hasG && !reduce) gsap.fromTo(menu, { clipPath: 'inset(0% 0% 100% 0%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: 0.7, ease: 'expo.inOut', overwrite: true });
    else menu.style.clipPath = 'none';
    setTimeout(function () { mclose.focus(); }, 30);
  }
  function closeMenu(instant) {
    if (!isOpen && !menu.classList.contains('open')) return;
    isOpen = false; setInert(false); if (lenis) lenis.start();
    mbtn.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-hidden', 'true');
    var fin = function () { menu.classList.remove('open'); menu.style.clipPath = ''; };
    if (instant === true || !hasG || reduce) { if (hasG) gsap.killTweensOf(menu); fin(); }
    else gsap.fromTo(menu, { clipPath: 'inset(0% 0% 0% 0%)' }, { clipPath: 'inset(0% 0% 100% 0%)', duration: 0.35, ease: 'expo.in', overwrite: true, onComplete: fin });
    if (lastFocus && lastFocus.focus && instant !== false) try { lastFocus.focus({ preventScroll: true }); } catch (e) {}
  }
  mbtn.addEventListener('click', openMenu);
  mclose.addEventListener('click', function () { closeMenu(); });
  document.addEventListener('keydown', function (e) {
    if (!isOpen) return;
    if (e.key === 'Escape') { e.preventDefault(); closeMenu(); return; }
    if (e.key !== 'Tab') return;
    var f = $$('a[href],button', menu).filter(function (n) { return n.offsetParent !== null || n === mclose; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    else if (!menu.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
  });

  /* ---------- click-to-copy email ---------- */
  var toast = $('.toast'), toastT = 0;
  function say(t) { toast.textContent = t; toast.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(function () { toast.classList.remove('on'); }, 1800); }
  function copyMail(a) {
    var m = a.dataset.copy;
    function ok() { say('Copied ' + m); }
    function fail() { location.href = 'mailto:' + m; }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(m).then(ok, fail); else fail();
  }

  /* ---------- chrome context: "Myles Parslow . Business" and the strip ground ---------- */
  var chrome = $('#chrome'), ctx = $('.ctx'), STRIP = 58;
  function setChrome(sec) {
    var lab = sec ? sec.getAttribute('data-chrome') : '', sh = sec ? (sec.getAttribute('data-short') || lab) : '', g = sec && sec.getAttribute('data-ground');
    if (ctx) { ctx.hidden = !lab; $('.ctx__f', ctx).textContent = lab; $('.ctx__s', ctx).textContent = sh; }
    chrome.style.setProperty('--cbg', g ? 'var(--r-' + g + ')' : 'var(--bg)');
    chrome.style.setProperty('--cfg', g ? 'var(--rfg)' : 'var(--fg)'); chrome.style.setProperty('--cacc', g ? 'var(--racc)' : 'var(--accent)');
  }
  setChrome($('[data-chrome]'));

  /* ---------- rooms: about panel, pixel-mosaic thumbs, sticky top for tall cards ---------- */
  var rooms = $$('.room');
  rooms.forEach(function (room) {
    var about = $('.room__about', room), def = about.dataset.default;
    $$('.row', room).forEach(function (row) {
      var on = function () { about.textContent = row.dataset.about; };
      var off = function () { about.textContent = def; };
      row.addEventListener('pointerenter', on); row.addEventListener('focus', on);
      row.addEventListener('pointerleave', off); row.addEventListener('blur', off);
      var img = $('.th img', row);
      if (img && canHover && !reduce) row.addEventListener('pointerenter', function () { mosaic($('.th', row), img); });
    });
  });
  function mosaic(box, img) {
    if (!img.complete || !img.naturalWidth) return;
    var cv = $('canvas', box);
    if (!cv) { cv = document.createElement('canvas'); box.appendChild(cv); }
    var w = cv.width = box.clientWidth, h = cv.height = box.clientHeight, ctx = cv.getContext('2d'), t = document.createElement('canvas'), tc = t.getContext('2d');
    ctx.imageSmoothingEnabled = false; cv.style.display = 'block'; clearTimeout(cv._t);
    var steps = [14, 8, 5, 3, 2, 1], k = 0;
    (function next() {
      var b = steps[k++];
      if (b === 1) { cv.style.display = 'none'; return; }
      t.width = Math.ceil(w / b); t.height = Math.ceil(h / b);
      /* cover-crop the 8:5 thumb into the box */
      tc.drawImage(img, 0, 0, t.width, t.height); ctx.drawImage(t, 0, 0, w, h);
      cv._t = setTimeout(next, 70);
    })();
  }
  /* warm the row thumbnails once the page is idle, so image decode never lands mid-scroll */
  window.addEventListener('load', function () {
    setTimeout(function () {
      $$('.room .th img').forEach(function (im) { im.loading = 'eager'; if (im.decode) im.decode().catch(function () {}); });
    }, 1500);
  });
  function fitSticky() {
    rooms.forEach(function (r) { r.style.top = Math.min(0, window.innerHeight - r.offsetHeight) + 'px'; });
  }
  if (rooms.length) fitSticky();
  var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { if (rooms.length) fitSticky(); if (hasG) ScrollTrigger.refresh(); }, 150); });

  /* ---------- words (line-mask reveal at word level, robust to resize) ---------- */
  function splitWords(el) {
    var t = el.textContent.trim(); el.setAttribute('aria-label', t); el.textContent = '';
    t.split(/\s+/).forEach(function (wd, i, arr) {
      var w = document.createElement('span'), s = document.createElement('span');
      w.className = 'w'; w.setAttribute('aria-hidden', 'true'); s.textContent = wd; w.appendChild(s); el.appendChild(w);
      if (i < arr.length - 1) el.appendChild(document.createTextNode(' '));
    });
  }

  if (hasG) {
    /* chrome: the strip takes the ground of the section under it, and the top-left pill names the room */
    var csecs = $$('[data-chrome]'), cnow = csecs[0] || null;
    var chromeTick = function () {
      var hit = null, y = STRIP + 2;
      for (var i = 0; i < csecs.length; i++) { var r = csecs[i].getBoundingClientRect(); if (r.top <= y && r.bottom > y) hit = csecs[i]; } /* last in DOM order = on top of a sticky stack */
      if (hit !== cnow) { cnow = hit; setChrome(hit); }
    };
    ScrollTrigger.create({ start: 0, end: 'max', onUpdate: chromeTick, onRefresh: chromeTick });
    chromeTick();
    ScrollTrigger.create({ start: 8, end: 'max', onToggle: function (self) { chrome.classList.toggle('scrolled', self.isActive); } });

    if (!reduce) {
      /* scroll reveals: fromTo only, clamp so page-bottom elements still fire */
      $$('[data-words]').forEach(function (el) {
        if (!$('.w', el)) splitWords(el);
        gsap.fromTo($$('.w>span', el), { yPercent: 115 }, { yPercent: 0, duration: 0.9, ease: 'expo.out', stagger: 0.07, scrollTrigger: { trigger: el, start: 'clamp(top 85%)' } });
      });
      $$('[data-fade]').forEach(function (el) {
        gsap.fromTo(el, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.9, ease: 'expo.out', scrollTrigger: { trigger: el, start: 'clamp(top 88%)' } });
      });

      /* sticky card stack: previous card scales back and dims as the next arrives (desktop only) */
      var mm = gsap.matchMedia();
      mm.add('(min-width: 901px)', function () {
        var slots = $$('.slot');
        rooms.forEach(function (card, i) {
          if (i === rooms.length - 1) return;
          var st = { trigger: slots[i + 1], start: 'top bottom', end: 'top top', scrub: true };
          gsap.fromTo(card, { scale: 1 }, { scale: 0.92, ease: 'none', scrollTrigger: st });
          gsap.fromTo($('.room__shade', card), { opacity: 0 }, { opacity: 0.2, ease: 'none', scrollTrigger: st });
        });
      });
    }
  }

  /* ---------- intro: loader -> M mask exit -> hero build ---------- */
  var hero = $('#hero'), loader = $('.loader');
  var mPoly = $('#mPoly'), mRect = $('#mRect'), mRed = $('#mRed');
  function mT(s, cx, cy) { return 'translate(' + (cx - s * 0.5) + ' ' + (cy - s * 0.5) + ') scale(' + s + ')'; }
  function finishIntro() {
    root.classList.remove('loading'); root.classList.remove('anim');
    hero.style.clipPath = 'none'; if (loader) loader.style.display = 'none';
    try { sessionStorage.setItem('mpb-seen', '1'); } catch (e) {}
    afterReady();
  }
  function heroBuild(delay) {
    var tl = gsap.timeline({ delay: delay || 0 });
    tl.fromTo($$('.hero .w>span'), { yPercent: 115, visibility: 'visible' }, { yPercent: 0, duration: 0.9, ease: 'expo.out', stagger: 0.07 }, 0);
    tl.fromTo('#frame', { opacity: 0, clipPath: 'inset(100% 0% 0% 0%)' }, { opacity: 1, clipPath: 'inset(0% 0% 0% 0%)', duration: 1.1, ease: 'expo.out', clearProps: 'clipPath' }, 0.15);
    tl.fromTo('.cap, .hero__foot', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.9, ease: 'expo.out', stagger: 0.09, clearProps: 'all' }, 0.45);
    tl.fromTo('#chrome', { opacity: 0 }, { opacity: 1, duration: 0.6, ease: 'expo.out', clearProps: 'opacity' }, 0.2);
    tl.eventCallback('onComplete', finishIntro);
    return tl;
  }
  function afterReady() {
    window.__mpbDone = true;
    var h = ''; try { h = decodeURIComponent(location.hash || ''); } catch (e) {}
    if (h.length > 1) { var again = function () { scrollToHash(h, true); }; again(); if (document.fonts && document.fonts.ready) document.fonts.ready.then(again); window.addEventListener('load', again); }
    if (hasG) ScrollTrigger.refresh();
  }
  function runIntro() {
    if (!hero) { /* in-theme room page: short arrival only, no loader replay */
      root.classList.remove('loading');
      if (hasG && anim) gsap.fromTo('#chrome', { opacity: 0 }, { opacity: 1, duration: 0.6, ease: 'expo.out', delay: arrived ? 0.5 : 0.05, clearProps: 'opacity', onComplete: function () { root.classList.remove('anim'); } }); else root.classList.remove('anim');
      afterReady(); if (arrived) arrive();
      return;
    }
    if (!anim) { if (arrived) arrive(afterReady); else afterReady(); return; }
    if (!root.classList.contains('loading')) {
      if (arrived) { arrive(); heroBuild(0.55); } else heroBuild(0.05);
      return;
    }
    var t0 = performance.now(), n = $('.loader__n'), done = 0, finished = false;
    var vw = window.innerWidth, vh = window.innerHeight, cx = vw / 2, cy = vh / 2;
    var s0 = Math.min(vh * 0.36, vw * 0.5);
    mRed.setAttribute('transform', mT(s0, cx, cy));
    mPoly.setAttribute('transform', mT(s0, cx, cy));
    hero.style.clipPath = 'url(#mClip)';
    var tasks = [];
    $$('#frame img').slice(0, 3).forEach(function (im) { tasks.push(im.decode ? im.decode().catch(function () {}) : Promise.resolve()); });
    tasks.push(document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve());
    var total = tasks.length, shown = { v: 0 };
    function paint() { n.textContent = String(Math.round(shown.v)).padStart(3, '0'); }
    function bump() { done++; gsap.to(shown, { v: Math.min(99, done / total * 100), duration: 0.5, ease: 'expo.out', onUpdate: paint }); }
    tasks.forEach(function (p) { p.then(bump, bump); });
    function exit() {
      if (finished) return; finished = true;
      loader.style.pointerEvents = 'none'; /* pointer-events:none at exit start */
      shown.v = 100; paint();
      var reach = Math.hypot(vw, vh) * 1.3 / s0;
      var o = { p: 0 };
      gsap.fromTo(o, { p: 0 }, { p: 1, duration: 0.45, ease: 'expo.out',
        onStart: function () { loader.classList.add('is-open'); },
        onUpdate: function () {
          var s = s0 * (1 + o.p * (reach * 1.2)), tr = mT(s, cx, cy);
          mPoly.setAttribute('transform', tr); mRed.setAttribute('transform', tr);
          var q = Math.max(0, (o.p - 0.7) / 0.3), rw = (vw + 40) * q, rh = (vh + 40) * q;
          mRect.setAttribute('x', cx - rw / 2); mRect.setAttribute('y', cy - rh / 2); mRect.setAttribute('width', rw); mRect.setAttribute('height', rh);
        } });
      gsap.to(mRed, { opacity: 0, duration: 0.3, ease: 'expo.out' });
      mRect.setAttribute('x', 0); mRect.setAttribute('width', 0);
      heroBuild(0.12);
    }
    Promise.all(tasks).then(function () { var w = Math.max(0, 900 - (performance.now() - t0)); setTimeout(exit, w); }); /* 0.9 s minimum */
    setTimeout(exit, 4000); /* 4 s cap */
  }
  /* wait for the first paint of fonts to be requested, then run */
  runIntro();
  window.MPB = { go: go, scrollToHash: scrollToHash, lenis: lenis, hasG: hasG, reduce: reduce, $: $, $$: $$ };
})();
