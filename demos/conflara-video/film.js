// Tiny film engine: everything on screen is a pure function of time t, so the page can be scrubbed or rendered frame by frame.
// The page defines window.FILM = { dur, shots, captions, cards, steps } before this script runs.
(function () {
  const F = window.FILM;
  const stage = document.getElementById('stage');
  const win = document.getElementById('win');
  const WW = win.clientWidth, WH = win.clientHeight;
  const IMG_W = 1440;
  const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const XF = 0.45; // crossfade seconds

  // shots
  const shotEls = F.shots.map((s) => {
    const d = document.createElement('div'); d.className = 'shot';
    const im = document.createElement('img'); im.src = (window.FILM_BASE || '') + 'shots/' + s.img + '.jpg'; im.alt = ''; im.decoding = 'sync';
    d.appendChild(im); win.appendChild(d);
    s.h = s.h || 1000; s.w = s.w || IMG_W;
    return { d, im, s };
  });
  function cam(s, t) {
    const k = s.cam; let a = k[0], b = k[0], u = 0;
    if (t <= k[0][0]) a = b = k[0];
    else if (t >= k[k.length - 1][0]) a = b = k[k.length - 1];
    else for (let i = 0; i < k.length - 1; i++) if (t >= k[i][0] && t <= k[i + 1][0]) { a = k[i]; b = k[i + 1]; u = ease((t - a[0]) / (b[0] - a[0] || 1)); break; }
    const z = a[3] + (b[3] - a[3]) * u;
    let x = a[1] + (b[1] - a[1]) * u, y = a[2] + (b[2] - a[2]) * u;
    x = clamp(x, 0, Math.max(0, s.w - WW / z)); y = clamp(y, 0, Math.max(0, s.h - WH / z));
    return { x, y, z };
  }

  // captions
  const eyebrow = document.getElementById('eyebrow'), capt = document.getElementById('capt'), prog = document.getElementById('prog');
  const nSteps = F.steps || 0;
  if (prog) for (let i = 0; i < nSteps; i++) prog.appendChild(document.createElement('i'));
  const cards = [...document.querySelectorAll('[data-t0]')];

  function at(t) {
    for (const { d, im, s } of shotEls) {
      const on = t >= s.t0 && t < s.t1 + XF;
      if (!on) { d.style.visibility = 'hidden'; continue; }
      d.style.visibility = 'visible';
      const fin = s.fade === false ? 1 : clamp((t - s.t0) / XF, 0, 1);
      d.style.opacity = fin;
      const c = cam(s, t - s.t0);
      im.style.transform = `translate(${-c.x * c.z}px, ${-c.y * c.z}px) scale(${c.z})`;
    }
    // caption
    let cur = null;
    for (const c of F.captions || []) if (t >= c.t0 && t < c.t1) cur = c;
    if (capt) {
      const txt = cur ? cur.text : '', eb = cur ? cur.eyebrow : '';
      if (capt.dataset.v !== txt) { capt.dataset.v = txt; capt.innerHTML = txt; }
      if (eyebrow.dataset.v !== eb) { eyebrow.dataset.v = eb; eyebrow.textContent = eb; }
      const o = cur ? clamp((t - cur.t0) / 0.35, 0, 1) * clamp((cur.t1 - t) / 0.25, 0, 1) : 0;
      capt.style.opacity = o; eyebrow.style.opacity = o;
      capt.style.transform = `translateY(${(1 - Math.min(1, (t - (cur ? cur.t0 : 0)) / 0.35)) * 8}px)`;
      if (prog) [...prog.children].forEach((el, i) => { const st = cur && cur.step; el.className = st == null ? '' : i + 1 < st ? 'done' : i + 1 === st ? 'now' : ''; });
    }
    // cards and timed elements
    for (const el of cards) {
      const t0 = +el.dataset.t0, t1 = +el.dataset.t1, fo = el.dataset.fo ? +el.dataset.fo : 0.5;
      const o = clamp((t - t0) / 0.5, 0, 1) * clamp((t1 - t) / fo, 0, 1);
      el.style.opacity = o; el.style.visibility = o > 0 ? 'visible' : 'hidden';
      for (const c of el.querySelectorAll('[data-in]')) {
        const u = ease(clamp((t - t0 - +c.dataset.in) / 0.6, 0, 1));
        c.style.opacity = u; c.style.transform = `translateY(${(1 - u) * 14}px)`;
      }
    }
    if (window.onFilmTime) window.onFilmTime(t);
  }

  // player
  const audio = document.getElementById('score');
  const scrub = document.getElementById('scrub'), clock = document.getElementById('clock'), play = document.getElementById('play');
  let t = 0, playing = false, last = 0, rendering = false;
  const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  function show() { at(t); if (scrub) scrub.value = t; if (clock) clock.textContent = `${fmt(t)} / ${fmt(F.dur)}`; }
  function tick(now) {
    if (!playing) return;
    t = audio && !audio.paused && audio.currentTime > 0 ? audio.currentTime : t + (now - last) / 1000; last = now;
    if (t >= F.dur) { t = F.dur; playing = false; play.textContent = 'Replay'; if (audio) audio.pause(); }
    show(); if (playing) requestAnimationFrame(tick);
  }
  if (play) play.onclick = () => {
    if (playing) { playing = false; play.textContent = 'Play'; audio && audio.pause(); return; }
    if (t >= F.dur) t = 0;
    playing = true; play.textContent = 'Pause'; last = performance.now();
    if (audio) { audio.currentTime = t; audio.play().catch(() => {}); }
    requestAnimationFrame(tick);
  };
  if (scrub) { scrub.max = F.dur; scrub.step = 0.01; scrub.oninput = () => { t = +scrub.value; if (audio) audio.currentTime = t; show(); }; }
  function fit() {
    if (rendering) { stage.style.transform = 'none'; return; }
    const fr = document.getElementById('frame'); stage.style.transform = `scale(${fr.clientWidth / 1280})`;
  }
  addEventListener('resize', fit); fit();
  window.__seek = (s) => { t = s; at(t); };
  window.__renderMode = () => { rendering = true; document.documentElement.classList.add('rendering'); fit(); };
  window.__ready = () => Promise.all(shotEls.map(({ im }) => (im.complete ? im.decode().catch(() => {}) : new Promise((r) => { im.onload = im.onerror = r; })))).then(() => document.fonts.ready);
  show();
})();
