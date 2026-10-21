/* Drives a guided tour from window.TOUR: { steps: [{ img, title, text, focus: [x, y, w, h] as fractions of the screenshot, or null }] }. */
(function () {
  var T = window.TOUR, steps = T.steps;
  var DWELL = 8000;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s) { return document.querySelector(s); };
  var stage = $('.stage'), layer = $('.layer'), spot = $('.spot'), bar = $('.progress b');
  var count = $('.count'), title = $('.say h2'), text = $('.say p'), play = $('#play'), chapters = $('.chapters');
  var imgs = {}, i = 0, playing = !reduce, t0 = 0, elapsed = 0;

  steps.forEach(function (s, n) {
    if (!imgs[s.img]) {
      var im = new Image();
      im.src = s.img; im.alt = ''; im.decoding = 'async';
      im.addEventListener('load', function () { if (steps[i].img === s.img) layout(); });
      layer.insertBefore(im, spot);
      imgs[s.img] = im;
    }
    var li = document.createElement('li'), b = document.createElement('button');
    b.type = 'button'; b.textContent = s.chapter || s.title;
    b.addEventListener('click', function () { go(n, true); });
    li.appendChild(b); chapters.appendChild(li);
  });

  function layout() {
    var s = steps[i], im = imgs[s.img];
    var W = stage.clientWidth, H = stage.clientHeight;
    var a = (im.naturalWidth || 16) / (im.naturalHeight || 10);
    var w, h;
    if (W / H > a) { h = H; w = H * a; } else { w = W; h = W / a; }
    layer.style.width = w + 'px'; layer.style.height = h + 'px';
    var f = s.focus, sc = 1, tx = (W - w) / 2, ty = (H - h) / 2;
    if (f) {
      var fx = f[0] * w, fy = f[1] * h, fw = f[2] * w, fh = f[3] * h;
      sc = Math.max(1, Math.min(0.9 * W / fw, 0.9 * H / fh, 1.6));
      tx = W / 2 - sc * (fx + fw / 2); ty = H / 2 - sc * (fy + fh / 2);
      tx = sc * w >= W ? Math.min(0, Math.max(W - sc * w, tx)) : (W - sc * w) / 2;
      ty = sc * h >= H ? Math.min(0, Math.max(H - sc * h, ty)) : (H - sc * h) / 2;
      spot.style.left = fx + 'px'; spot.style.top = fy + 'px'; spot.style.width = fw + 'px'; spot.style.height = fh + 'px';
      spot.style.boxShadow = '0 0 0 ' + (2 / sc) + 'px var(--accent), 0 0 0 200vmax var(--dim)';
      spot.classList.remove('off');
    } else {
      spot.classList.add('off');
    }
    layer.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + sc + ')';
  }

  function go(n, byHand) {
    i = (n + steps.length) % steps.length;
    var s = steps[i];
    Object.keys(imgs).forEach(function (k) { imgs[k].classList.toggle('on', k === s.img); });
    imgs[s.img].alt = s.alt || s.title;
    count.textContent = 'Step ' + (i + 1) + ' of ' + steps.length;
    title.textContent = s.title;
    text.textContent = s.text;
    chapters.querySelectorAll('button').forEach(function (b, k) {
      if (k === i) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
    });
    layout();
    elapsed = 0; t0 = performance.now();
    if (byHand) setPlaying(false);
  }

  function setPlaying(on) {
    playing = on;
    play.textContent = on ? 'Pause' : 'Play';
    play.setAttribute('aria-label', on ? 'Pause the tour' : 'Play the tour');
    t0 = performance.now() - elapsed;
  }

  function tick(now) {
    if (playing && !document.hidden) {
      elapsed = now - t0;
      if (elapsed >= DWELL) { go(i + 1); elapsed = 0; }
    } else {
      t0 = now - elapsed;
    }
    bar.style.width = Math.min(100, elapsed / DWELL * 100) + '%';
    requestAnimationFrame(tick);
  }

  $('#prev').addEventListener('click', function () { go(i - 1, true); });
  $('#next').addEventListener('click', function () { go(i + 1, true); });
  play.addEventListener('click', function () { setPlaying(!playing); });
  stage.addEventListener('click', function () { go(i + 1, true); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight') go(i + 1, true);
    else if (e.key === 'ArrowLeft') go(i - 1, true);
    else if (e.key === ' ' && e.target === document.body) { e.preventDefault(); setPlaying(!playing); }
  });
  window.addEventListener('resize', layout);

  setPlaying(playing);
  go(0);
  requestAnimationFrame(tick);
})();
