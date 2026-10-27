/* Appearance controls: style, presets, custom colours, fonts, size, corners, density, backdrop, texture.
   Applies saved settings on every page that loads it; builds the panel only where #appearance-btn exists. */
(function () {
  'use strict';
  var KEY = 'portfolio-appearance', OLD = 'portfolio-scheme';
  var root = document.documentElement;
  var P = function (name, dark, bg, surface, ink, muted, accent, mark) { return { name: name, dark: dark, bg: bg, surface: surface, ink: ink, muted: muted, accent: accent, mark: mark }; };
  var PRESETS = {
    eggshell: P('Eggshell', 0, '#f2eee3', '#fbf9f3', '#15120f', '#5f4e40', '#6b3f22', '#a9822f'),
    pine: P('Original', 0, '#f4f6f4', '#ffffff', '#18201c', '#56625b', '#23593f', '#23593f'),
    sky: P('Sky & ruby', 0, '#e8f3fb', '#ffffff', '#192838', '#4c6073', '#9b111e', '#9b111e'),
    'eggshell-night': P('Eggshell night', 1, '#1b1712', '#241f18', '#efe8d8', '#b3a58f', '#e0b266', '#e0b266'),
    'pine-night': P('Original night', 1, '#121a16', '#1a251f', '#e4ede8', '#9db1a6', '#6fcf9f', '#6fcf9f'),
    'sky-night': P('Sky night', 1, '#0f1b28', '#16273a', '#e3eef8', '#9bb3c8', '#ff6b7a', '#ff6b7a'),
    matrix: P('Matrix', 1, '#020a04', '#07140a', '#b7ffc8', '#6cc283', '#2cff6b', '#2cff6b'),
    mono: P('Mono', 0, '#ffffff', '#f4f4f4', '#111111', '#555555', '#111111', '#111111'),
    neon: P('Neon', 1, '#0b0620', '#150d33', '#f1eaff', '#a999d6', '#ff3df0', '#29f0ff')
  };
  var TWIN = { eggshell: 'eggshell-night', pine: 'pine-night', sky: 'sky-night' };
  var UNTWIN = { 'eggshell-night': 'eggshell', 'pine-night': 'pine', 'sky-night': 'sky' };
  var FONTS = {
    editorial: ['Editorial', null, null],
    classic: ['Classic serif', 'Georgia, "Times New Roman", serif', 'Georgia, "Times New Roman", serif'],
    clean: ['Clean sans', 'system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif', 'system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'],
    typewriter: ['Typewriter', 'ui-monospace, Menlo, Consolas, monospace', 'ui-monospace, Menlo, Consolas, monospace']
  };
  // Styles restyle the whole page: their own palette (light and dark), fonts loaded on demand, and the type rules in appearance.css.
  var GF = 'https://fonts.googleapis.com/css2?display=swap&family=';
  var STYLES = {
    classic: { name: 'Classic' },
    deco: { name: 'Art Deco', dark: 1, font: 'Poiret+One&family=Josefin+Sans:wght@300;400;600',
      display: '"Poiret One", "Josefin Sans", sans-serif', body: '"Josefin Sans", "Avenir Next", sans-serif',
      light: P('Art Deco', 0, '#f1e7cc', '#f8f1dd', '#0b1a17', '#4a5a4f', '#0f3a31', '#8f6b22'),
      night: P('Art Deco', 1, '#0b1a17', '#10241f', '#efe3c2', '#b9a983', '#d6aa4f', '#d6aa4f') },
    terminal: { name: 'Terminal', dark: 1, font: 'VT323&family=JetBrains+Mono:wght@400;600',
      display: '"VT323", "JetBrains Mono", monospace', body: '"JetBrains Mono", ui-monospace, Menlo, monospace', mono: '"JetBrains Mono", ui-monospace, Menlo, monospace',
      light: P('Terminal', 0, '#eef6ea', '#f7fbf4', '#0b2a14', '#3d6b4a', '#0a7a31', '#0a7a31'),
      night: P('Terminal', 1, '#031208', '#06200f', '#35ff7a', '#22b552', '#c9ffd9', '#35ff7a') },
    swiss: { name: 'Swiss', dark: 0, font: 'Archivo:wdth,wght@75..100,400..800',
      display: '"Archivo", "Helvetica Neue", Arial, sans-serif', body: '"Archivo", "Helvetica Neue", Arial, sans-serif',
      light: P('Swiss', 0, '#f5f4f0', '#ffffff', '#111111', '#6d6c68', '#d4231a', '#e5281d'),
      night: P('Swiss', 1, '#0e0e0e', '#1a1a1a', '#f2f1ec', '#a3a29d', '#ff3b2f', '#ff3b2f') }
  };
  var COLORS = [['bg', 'Background'], ['surface', 'Panels'], ['ink', 'Text'], ['muted', 'Secondary text'], ['accent', 'Links and labels'], ['mark', 'Highlight']];
  var DEF = { style: 'classic', sdark: null, preset: 'eggshell', custom: null, font: 'editorial', size: 100, radius: 6, density: 1, backdrop: 'none', texture: 'grain' };
  var S;

  function load() {
    var s = null;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) {}
    if (!s || typeof s !== 'object') {
      s = {};
      try { var o = localStorage.getItem(OLD); if (PRESETS[o]) s.preset = o; } catch (e) {}
    }
    S = {};
    for (var k in DEF) S[k] = (s[k] !== undefined && s[k] !== null) ? s[k] : DEF[k];
    if (!PRESETS[S.preset] && S.preset !== 'custom') S.preset = 'eggshell';
    if (S.preset === 'custom' && !S.custom) S.preset = 'eggshell';
    if (!FONTS[S.font]) S.font = 'editorial';
    S.size = Math.min(130, Math.max(85, +S.size || 100));
    S.radius = Math.min(20, Math.max(0, +S.radius));
    S.density = [0.8, 1, 1.25].indexOf(+S.density) < 0 ? 1 : +S.density;
    if (S.texture !== 'none') S.texture = 'grain';
    if (!STYLES[S.style]) S.style = 'classic';
    if (S.sdark !== 0 && S.sdark !== 1) S.sdark = null;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  function sty() { return S.style !== 'classic' && STYLES[S.style]; }
  function cur() { var y = sty(); if (y) return (S.sdark === null ? y.dark : S.sdark) ? y.night : y.light; return S.preset === 'custom' ? S.custom : PRESETS[S.preset]; }
  function mix(a, b, pct) { return 'color-mix(in srgb, ' + a + ' ' + pct + '%, ' + b + ')'; }

  var VARS = ['--bg', '--surface', '--rule', '--ink', '--muted', '--accent', '--mark', '--mark-soft', '--display', '--body', '--mono', '--radius', '--density'];
  function apply() {
    var st = root.style, y = sty(), legacy = !y && (S.preset === 'eggshell' || S.preset === 'pine' || S.preset === 'sky');
    VARS.forEach(function (v) { st.removeProperty(v); });
    if (S.preset === 'eggshell' || legacy === false || true) {
      if (legacy && (S.preset === 'pine' || S.preset === 'sky')) root.setAttribute('data-scheme', S.preset); else root.removeAttribute('data-scheme');
    }
    if (!legacy) {
      var c = cur();
      st.setProperty('--bg', c.bg); st.setProperty('--surface', c.surface); st.setProperty('--ink', c.ink);
      st.setProperty('--muted', c.muted); st.setProperty('--accent', c.accent); st.setProperty('--mark', c.mark);
      st.setProperty('--rule', mix(c.ink, c.bg, 18));
      st.setProperty('--mark-soft', mix(c.mark, c.bg, 22));
    }
    root.style.colorScheme = cur().dark ? 'dark' : 'light';
    if (y) {
      root.setAttribute('data-style', S.style);
      st.setProperty('--display', y.display); st.setProperty('--body', y.body); if (y.mono) st.setProperty('--mono', y.mono);
      var ln = document.getElementById('ap-style-font');
      if (!ln) { ln = document.createElement('link'); ln.id = 'ap-style-font'; ln.rel = 'stylesheet'; (document.head || root).appendChild(ln); }
      if (ln.getAttribute('href') !== GF + y.font) ln.setAttribute('href', GF + y.font);
    } else root.removeAttribute('data-style');
    var f = FONTS[S.font];
    if (f[1]) { st.setProperty('--display', f[1]); st.setProperty('--body', f[2]); }
    if (S.font === 'typewriter') st.setProperty('--mono', f[1]);
    st.fontSize = S.size === 100 ? '' : S.size + '%';
    st.setProperty('--radius', S.radius + 'px');
    st.setProperty('--density', S.density);
    root.setAttribute('data-backdrop', S.backdrop);
    root.setAttribute('data-texture', S.texture);
    if (cur().dark) root.setAttribute('data-dark', ''); else root.removeAttribute('data-dark');
    backdrop();
    syncUI();
  }

  /* Backdrops */
  var SHADERS = { plasma: 'Plasma silk', marble: 'Marble', ink: 'Warped ink', nebula: 'Nebula' };
  var BASE = ((document.currentScript && document.currentScript.src) || '').replace(/[^\/]*$/, '');
  var cv, cx, raf, drops, lastT = 0, glx, onSize;
  function stopCanvas() {
    if (raf) cancelAnimationFrame(raf); raf = 0;
    if (onSize) { window.removeEventListener('resize', onSize); onSize = null; }
    if (glx) { var lose = glx.getExtension('WEBGL_lose_context'); if (lose) lose.loseContext(); glx = null; }
    if (cv) { cv.remove(); cv = null; }
  }
  function loadShaders(done) {
    if (window.PortfolioShaders) return done();
    var s = document.createElement('script'); s.src = BASE + 'shaders.js'; s.onload = done;
    document.head.appendChild(s);
  }
  // A full-screen fragment shader drawn at half resolution and 30 fps; one still frame under reduced motion.
  function shaderBackdrop(key, reduced) {
    var lib = window.PortfolioShaders, def = lib[key];
    var c = document.createElement('canvas'), gl = c.getContext('webgl', { antialias: false, depth: false, powerPreference: 'low-power' });
    if (!gl) return;
    function sh(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
    var pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, 'attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}'));
    gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, lib.PRE + def.frag));
    gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return;
    gl.useProgram(pr);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(pr, 'a'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    def.colors.forEach(function (h, i) { var n = parseInt(h.slice(1), 16); gl.uniform3f(gl.getUniformLocation(pr, 'u_c' + (i + 1)), (n >> 16) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255); });
    var uT = gl.getUniformLocation(pr, 'u_time'), uR = gl.getUniformLocation(pr, 'u_res'), t0 = performance.now(), last = 0;
    cv = c; glx = gl; cv.className = 'bd-canvas bd-shader'; cv.setAttribute('aria-hidden', 'true');
    document.body.insertBefore(cv, document.body.firstChild);
    function draw(ms) { gl.uniform1f(uT, 20 + (ms - t0) / 1000); gl.uniform2f(uR, cv.width, cv.height); gl.drawArrays(gl.TRIANGLES, 0, 3); }
    onSize = function () { cv.width = Math.ceil(innerWidth / 2); cv.height = Math.ceil(innerHeight / 2); gl.viewport(0, 0, cv.width, cv.height); if (reduced) draw(t0); };
    window.addEventListener('resize', onSize); onSize();
    if (reduced) return draw(t0);
    (function tick(ms) { raf = requestAnimationFrame(tick); if (ms - last < 33) return; last = ms; draw(ms); })(t0);
  }
  function backdrop() {
    stopCanvas();
    if (!document.body) return;
    var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (SHADERS[S.backdrop]) {
      var want = S.backdrop;
      loadShaders(function () { if (S.backdrop === want && !cv) shaderBackdrop(want, reduced); });
      return;
    }
    if (S.backdrop !== 'rain' || reduced) return;
    cv = document.createElement('canvas'); cv.className = 'bd-canvas'; cv.setAttribute('aria-hidden', 'true');
    document.body.insertBefore(cv, document.body.firstChild);
    cx = cv.getContext('2d');
    function size() { cv.width = innerWidth; cv.height = innerHeight; drops = new Array(Math.ceil(cv.width / 18)).fill(0).map(function () { return Math.random() * cv.height / 18; }); }
    size(); window.addEventListener('resize', size);
    var chars = '01アイウエオカキクケコサシスセソ';
    (function tick(t) {
      raf = requestAnimationFrame(tick);
      if (t - lastT < 70) return; lastT = t;
      cx.fillStyle = 'rgba(0,0,0,0.06)'; cx.globalCompositeOperation = 'destination-out'; cx.fillRect(0, 0, cv.width, cv.height);
      cx.globalCompositeOperation = 'source-over';
      cx.fillStyle = getComputedStyle(root).getPropertyValue('--accent') || '#2cff6b';
      cx.font = '16px monospace';
      for (var i = 0; i < drops.length; i++) {
        cx.fillText(chars.charAt(Math.floor(Math.random() * chars.length)), i * 18, drops[i] * 18);
        if (drops[i] * 18 > cv.height && Math.random() > 0.975) drops[i] = 0; drops[i]++;
      }
    })(0);
  }

  /* Panel */
  var panel, btn;
  function el(tag, attrs, html) { var e = document.createElement(tag); for (var k in attrs || {}) e.setAttribute(k, attrs[k]); if (html != null) e.innerHTML = html; return e; }
  function seg(label, name, opts) {
    var h = '<div class="ap-row"><span class="ap-label">' + label + '</span><div class="ap-seg" role="group" aria-label="' + label + '">';
    opts.forEach(function (o) { h += '<button type="button" data-' + name + '="' + o[0] + '" aria-pressed="false">' + o[1] + '</button>'; });
    return h + '</div></div>';
  }
  function build() {
    btn = document.getElementById('appearance-btn');
    panel = el('aside', { id: 'appearance-panel', class: 'ap', 'aria-label': 'Appearance settings', hidden: '' });
    var h = '<div class="ap-head"><strong>Appearance</strong><button type="button" class="ap-x" aria-label="Close appearance settings">&times;</button></div>';
    h += seg('Style', 'style', Object.keys(STYLES).map(function (k) { return [k, STYLES[k].name]; }));
    h += seg('Mode', 'mode', [['light', 'Light'], ['dark', 'Dark']]);
    h += '<div class="ap-row"><span class="ap-label">Theme</span><div class="ap-presets" role="group" aria-label="Theme">';
    Object.keys(PRESETS).forEach(function (k) { var p = PRESETS[k]; h += '<button type="button" class="ap-preset" data-preset="' + k + '" aria-pressed="false"><i style="background:' + p.bg + ';box-shadow:inset -0.6rem 0 0 ' + p.accent + '"></i>' + p.name + '</button>'; });
    h += '<button type="button" class="ap-preset" data-preset="custom" aria-pressed="false"><i class="ap-rainbow"></i>Custom</button></div></div>';
    h += '<div class="ap-row"><span class="ap-label">Colours <small>(editing switches to Custom)</small></span><div class="ap-colors">';
    COLORS.forEach(function (c) { h += '<label>' + c[1] + '<input type="color" data-color="' + c[0] + '"></label>'; });
    h += '</div></div>';
    h += seg('Font', 'font', Object.keys(FONTS).map(function (k) { return [k, FONTS[k][0]]; }));
    h += '<div class="ap-row"><label class="ap-label" for="ap-size">Text size <output id="ap-size-o"></output></label><input id="ap-size" type="range" min="85" max="130" step="5"></div>';
    h += '<div class="ap-row"><label class="ap-label" for="ap-radius">Corners <output id="ap-radius-o"></output></label><input id="ap-radius" type="range" min="0" max="20" step="2"></div>';
    h += seg('Spacing', 'density', [['0.8', 'Compact'], ['1', 'Normal'], ['1.25', 'Airy']]);
    h += seg('Backdrop', 'backdrop', [['none', 'None'], ['glow', 'Soft glow'], ['grid', 'Grid'], ['rain', 'Rain']].concat(Object.keys(SHADERS).map(function (k) { return [k, SHADERS[k]]; })));
    h += seg('Texture', 'texture', [['grain', 'Paper grain'], ['none', 'None']]);
    h += '<div class="ap-row ap-foot"><button type="button" class="ap-reset">Reset to defaults</button></div>';
    panel.innerHTML = h;
    document.body.appendChild(panel);

    function open(v) { panel.hidden = !v; btn.setAttribute('aria-expanded', String(v)); if (v) panel.querySelector('.ap-x').focus(); else btn.focus(); }
    btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', 'appearance-panel');
    btn.addEventListener('click', function () { open(panel.hidden); });
    panel.querySelector('.ap-x').addEventListener('click', function () { open(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) open(false); });

    panel.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var d = b.dataset;
      if (d.style) { S.style = d.style; S.sdark = null; S.font = 'editorial'; }
      else if (d.preset) { S.style = 'classic'; if (d.preset === 'custom' && !S.custom) S.custom = JSON.parse(JSON.stringify(cur())); S.preset = d.preset; }
      else if (d.mode && sty()) S.sdark = d.mode === 'dark' ? 1 : 0;
      else if (d.mode) { var p = S.preset; if (d.mode === 'dark' && TWIN[p]) S.preset = TWIN[p]; else if (d.mode === 'light' && UNTWIN[p]) S.preset = UNTWIN[p]; else if (d.mode === 'dark' && !cur().dark) S.preset = 'eggshell-night'; else if (d.mode === 'light' && cur().dark) S.preset = 'eggshell'; }
      else if (d.font) S.font = d.font;
      else if (d.density) S.density = +d.density;
      else if (d.backdrop) S.backdrop = d.backdrop;
      else if (d.texture) S.texture = d.texture;
      else if (b.classList.contains('ap-reset')) { S = JSON.parse(JSON.stringify(DEF)); }
      else return;
      save(); apply();
    });
    panel.addEventListener('input', function (e) {
      var t = e.target;
      if (t.dataset.color) {
        if (S.preset !== 'custom' || sty()) { S.custom = JSON.parse(JSON.stringify(cur())); S.preset = 'custom'; S.style = 'classic'; }
        S.custom[t.dataset.color] = t.value;
        var c = S.custom, lum = function (h) { var n = parseInt(h.slice(1), 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)); };
        c.dark = lum(c.bg) < 128 ? 1 : 0;
      } else if (t.id === 'ap-size') S.size = +t.value;
      else if (t.id === 'ap-radius') S.radius = +t.value;
      else return;
      save(); apply();
    });
  }
  function syncUI() {
    document.querySelectorAll('.swatch[data-pick]').forEach(function (b) { b.setAttribute('aria-pressed', String(!sty() && b.dataset.pick === S.preset)); });
    if (!panel) return;
    var c = cur(), base = UNTWIN[S.preset] || S.preset;
    panel.querySelectorAll('[data-style]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.style === S.style)); });
    panel.querySelectorAll('[data-preset]').forEach(function (b) { b.setAttribute('aria-pressed', String(!sty() && b.dataset.preset === S.preset)); });
    panel.querySelectorAll('[data-mode]').forEach(function (b) { b.setAttribute('aria-pressed', String((b.dataset.mode === 'dark') === !!c.dark)); });
    panel.querySelectorAll('[data-font]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.font === S.font)); });
    panel.querySelectorAll('[data-density]').forEach(function (b) { b.setAttribute('aria-pressed', String(+b.dataset.density === S.density)); });
    panel.querySelectorAll('[data-backdrop]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.backdrop === S.backdrop)); });
    panel.querySelectorAll('[data-texture]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.texture === S.texture)); });
    panel.querySelectorAll('input[data-color]').forEach(function (i) { i.value = c[i.dataset.color]; });
    panel.querySelector('#ap-size').value = S.size; panel.querySelector('#ap-size-o').textContent = S.size + '%';
    panel.querySelector('#ap-radius').value = S.radius; panel.querySelector('#ap-radius-o').textContent = S.radius + 'px';
  }

  function swatches() {
    document.querySelectorAll('.swatch[data-pick]').forEach(function (b) {
      b.addEventListener('click', function () { S.preset = b.dataset.pick; S.style = 'classic'; save(); apply(); });
    });
  }
  load(); apply();
  document.addEventListener('DOMContentLoaded', function () { backdrop(); swatches(); syncUI(); if (document.getElementById('appearance-btn')) { build(); syncUI(); } });
  if (document.readyState !== 'loading' && document.getElementById('appearance-btn') && !panel) { build(); syncUI(); }
})();
