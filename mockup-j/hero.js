/* Mockup J, "Working Drawings": the cover sheet's plate. Source: themed/j/hero.js.
   The current project is drawn as ink lines (an edge filter of its own screenshot, done in the shader) and the
   pointer stirs a small fluid whose dye is the mask that turns the drawing into the built thing.

   The simulation is the stable-fluids "solve" mode of the websiteoftheyear skill's tested demo
   (assets/gl-demos/fluid-reveal.html): same shaders, same step order, same dt clamp and decay. What changed:
   it runs on plain WebGL2 instead of three.js (the page needs nothing else from three), it is sized to the
   plate instead of the window, layer A is computed from layer B in the composite, and colours come from the
   page's CSS tokens so the light and dark themes reach the canvas.

   Cost: 8 + ITER passes a frame (22), all but the last on a target about a quarter of the plate; one
   full-resolution pass; pixel ratio capped at 2; at most 60 steps a second; paused when less than a quarter of the plate is on screen, when the tab is
   hidden, and once the dye has healed with nothing moving.
   Without WebGL2 half-float targets, or under reduced motion, the plate falls back to a 2D-canvas drawing
   and a button that plots it into the photograph. */
(function () {
  'use strict';
  var d = document, M = window.MPJ, now = d.getElementById('now'), dataEl = d.getElementById('now-data');
  if (!now || !dataEl || !M) return;
  var S = JSON.parse(dataEl.textContent);
  var plate = d.getElementById('plate'), img = d.getElementById('now-img'), inkC = d.getElementById('now-ink'), glC = d.getElementById('now-gl');
  var link = d.getElementById('now-link'), nEl = d.getElementById('now-n'), sEl = d.getElementById('now-s'), codeEl = d.getElementById('now-code');
  var iEl = d.getElementById('now-i'), ctl = d.getElementById('now-ctl'), bBtn = d.getElementById('now-build'), hint = d.getElementById('now-hint');
  var idx = 0, built = false, mode = 'ink', G = null;
  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  var ITER = 14, VEL_DECAY = 0.35, DYE_DECAY = 0.5, FORCE = 0.8, DISTORT = 0.03, MAX_V = 2, SPLAT_R = 0.011, LO = 0.3, HI = 0.6, IDLE_MS = 2200;

  /* ------------------------------------------------------------------ captions and controls */
  function caption() {
    var s = S[idx];
    link.href = s.h; nEl.textContent = s.n; sEl.textContent = s.s; codeEl.textContent = s.code;
    iEl.textContent = pad(idx + 1) + ' / ' + pad(S.length);
  }
  function setBuilt(on) {
    built = on; bBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    bBtn.textContent = on ? 'Show the drawing' : 'Show it built';
    now.classList.toggle('is-built', on);
    if (G) G.buildTo = on ? 1 : 0;
  }
  function show(i) {
    idx = (i + S.length) % S.length; caption(); setBuilt(false);
    var s = S[idx], im = new Image();
    var ready = function () {
      if (S[idx] !== s) return;
      img.src = s.src; img.width = s.w; img.height = s.hh;
      if (mode === 'gl') G.setImage(im); else drawInk(im);
    };
    im.src = s.src;
    if (im.decode) im.decode().then(ready, function () { im.onload = ready; if (im.complete && im.naturalWidth) ready(); });
    else im.onload = ready;
  }
  function drawInk(im) {
    try { M.inkDraw(im, inkC, Math.min(im.naturalWidth, Math.round(plate.clientWidth * 2)), null, true); now.classList.add('is-ink'); }
    catch (e) { now.classList.remove('is-ink'); }
  }
  if (matchMedia('(pointer: coarse)').matches) hint.textContent = 'Every project here starts as a drawing of itself. Drag across this one to build it.';
  ctl.hidden = false; hint.hidden = false;
  ctl.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b === bBtn) setBuilt(!built); else show(idx + (+b.getAttribute('data-d')));
  });
  plate.addEventListener('click', function () { if (!G || !G.dragged) location.href = S[idx].h; });

  /* ------------------------------------------------------------------ WebGL2 */
  function startGL() {
    var gl = glC.getContext('webgl2', { antialias: false, alpha: false, powerPreference: 'high-performance' });
    if (!gl) return null;
    if (!gl.getExtension('EXT_color_buffer_float') && !gl.getExtension('EXT_color_buffer_half_float')) return null;
    var aniso = gl.getExtension('EXT_texture_filter_anisotropic');
    var HEAD = '#version 300 es\nprecision highp float;\nin vec2 vUv; out vec4 o;\n';
    var VERT = '#version 300 es\nin vec2 aPos; out vec2 vUv; void main(){ vUv = aPos * .5 + .5; gl_Position = vec4(aPos, 0., 1.); }';
    function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
    var vs = sh(gl.VERTEX_SHADER, VERT);
    function prog(frag) {
      var p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, HEAD + frag));
      gl.bindAttribLocation(p, 0, 'aPos'); gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
      var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
      for (var i = 0; i < n; i++) { var a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
      return { p: p, u: u };
    }
    var P;
    try {
      P = {
        // Gaussian capsule along the pointer's last move, pulling the field toward uColor.
        splat: prog('uniform sampler2D uSrc; uniform vec2 uFrom, uPoint; uniform vec3 uColor; uniform float uAspect, uRadius, uStrength;\n' +
          'void main(){ vec2 s = vec2(uAspect, 1.), a = uFrom * s, ab = uPoint * s - a, p = vUv * s;\n' +
          '  float t = clamp(dot(p - a, ab) / max(dot(ab, ab), 1e-8), 0., 1.), d = length(p - a - ab * t);\n' +
          '  o = vec4(mix(texture(uSrc, vUv).xyz, uColor, exp(-d * d / uRadius) * uStrength), 1.); }'),
        // Semi-Lagrangian: look back along the velocity, sample bilinearly, decay.
        advect: prog('uniform sampler2D uVel, uSrc; uniform float uDt, uAspect, uDecay;\n' +
          'void main(){ vec2 back = vUv - uDt * texture(uVel, vUv).xy * vec2(1. / uAspect, 1.); o = texture(uSrc, back) * uDecay; }'),
        div: prog('uniform sampler2D uVel; uniform vec2 uTexel;\n' +
          'void main(){ float l = texture(uVel, vUv - vec2(uTexel.x, 0.)).x, r = texture(uVel, vUv + vec2(uTexel.x, 0.)).x;\n' +
          '  float b = texture(uVel, vUv - vec2(0., uTexel.y)).y, t = texture(uVel, vUv + vec2(0., uTexel.y)).y;\n' +
          '  o = vec4(.5 * (r - l + t - b), 0., 0., 1.); }'),
        scale: prog('uniform sampler2D uSrc; uniform float uK; void main(){ o = uK * texture(uSrc, vUv); }'),
        jacobi: prog('uniform sampler2D uP, uDiv; uniform vec2 uTexel;\n' +
          'void main(){ float l = texture(uP, vUv - vec2(uTexel.x, 0.)).x, r = texture(uP, vUv + vec2(uTexel.x, 0.)).x;\n' +
          '  float b = texture(uP, vUv - vec2(0., uTexel.y)).x, t = texture(uP, vUv + vec2(0., uTexel.y)).x;\n' +
          '  o = vec4((l + r + b + t - texture(uDiv, vUv).x) * .25, 0., 0., 1.); }'),
        grad: prog('uniform sampler2D uP, uVel; uniform vec2 uTexel;\n' +
          'void main(){ float l = texture(uP, vUv - vec2(uTexel.x, 0.)).x, r = texture(uP, vUv + vec2(uTexel.x, 0.)).x;\n' +
          '  float b = texture(uP, vUv - vec2(0., uTexel.y)).x, t = texture(uP, vUv + vec2(0., uTexel.y)).x;\n' +
          '  o = vec4(texture(uVel, vUv).xy - .5 * vec2(r - l, t - b), 0., 1.); }'),
        // Final pass: the drawing (edges of the screenshot, as ink on paper), the built screenshot, the fluid mask
        // between them with a red pencil line on its edge, plus the two straight wipes (plot in, build).
        comp: prog('uniform sampler2D uImg, uDye, uVel; uniform vec2 uRes; uniform vec3 uPaper, uInk, uRed;\n' +
          'uniform float uAspect, uImgAspect, uDistort, uLo, uHi, uBuild, uPlot, uReady, uLine, uBias, uGain, uTh, uZoom;\n' +
          'vec2 cover(vec2 uv){ uv = vec2(uv.x / uZoom, 1. - (1. - uv.y) / uZoom); float s = uAspect / uImgAspect; if (s > 1.) return vec2(uv.x, 1. - (1. - uv.y) / s); return vec2(uv.x * s, uv.y); }\n' +
          'float lum(vec2 uv){ return dot(texture(uImg, uv, uBias).rgb, vec3(.2126, .7152, .0722)); }\n' +
          'float edge(vec2 uv){ float s = uAspect / uImgAspect; vec2 px = uLine / uRes * (s > 1. ? vec2(1., 1. / s) : vec2(s, 1.));\n' +
          '  px /= uZoom;\n  float a = lum(uv + px * vec2(-1., 1.)), b = lum(uv + px * vec2(0., 1.)), c = lum(uv + px * vec2(1., 1.));\n' +
          '  float dd = lum(uv + px * vec2(-1., 0.)), f = lum(uv + px * vec2(1., 0.));\n' +
          '  float g = lum(uv + px * vec2(-1., -1.)), h = lum(uv + px * vec2(0., -1.)), j = lum(uv + px * vec2(1., -1.));\n' +
          '  float gx = (c + 2. * f + j) - (a + 2. * dd + g), gy = (a + 2. * b + c) - (g + 2. * h + j);\n' +
          '  return clamp((length(vec2(gx, gy)) - uTh) * uGain, 0., 1.); }\n' +
          'void main(){ float m = smoothstep(uLo, uHi, texture(uDye, vUv).x);\n' +
          '  vec2 off = texture(uVel, vUv).xy * uDistort * vec2(1. / uAspect, 1.);\n' +
          '  float ax = 1.5 / uRes.x;\n' +
          '  float plotted = 1. - smoothstep(uPlot - ax, uPlot + ax, vUv.x);\n' +
          '  vec3 drawing = mix(uPaper, uInk, edge(cover(vUv - off)) * plotted * uReady);\n' +
          '  float wipe = uBuild <= 0. ? 0. : 1. - smoothstep(uBuild - ax, uBuild + ax, vUv.x);\n' +
          '  float k = max(m, wipe) * uReady;\n' +
          '  vec3 col = mix(drawing, texture(uImg, cover(vUv - off * .6)).rgb, k);\n' +
          '  float line = (1. - smoothstep(0., 1.6 * fwidth(m) + 1e-4, abs(m - .5))) * (1. - wipe);\n' +
          '  float pl = (1. - smoothstep(0., ax, abs(vUv.x - uPlot))) * step(.002, uPlot) * step(uPlot, .998);\n' +
          '  float bl = (1. - smoothstep(0., ax, abs(vUv.x - uBuild))) * step(.002, uBuild) * step(uBuild, .998);\n' +
          '  o = vec4(mix(col, uRed, max(line, max(pl, bl)) * uReady), 1.); }')
      };
    } catch (e) { if (window.console) console.warn('plate shaders', e); return null; }

    var vao = gl.createVertexArray(), buf = gl.createBuffer();
    gl.bindVertexArray(vao); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.disable(gl.DEPTH_TEST); gl.disable(gl.BLEND);

    function rt(w, h) {
      var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      var f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
      var ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
      gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
      return { t: t, f: f, w: w, h: h, ok: ok };
    }
    function pair(w, h) { return { read: rt(w, h), write: rt(w, h), swap: function () { var x = this.read; this.read = this.write; this.write = x; } }; }
    function free(r) { if (!r) return; (r.read ? [r.read, r.write] : [r]).forEach(function (x) { gl.deleteTexture(x.t); gl.deleteFramebuffer(x.f); }); }

    var st = { W: 2, H: 2, sim: null, vel: null, prs: null, dye: null, div: null, tex: null, imgAspect: 1.6, ready: 0,
      build: 0, buildTo: 0, plot: 0, dragged: false, passes: 0, alive: true };
    function alloc() {
      var cw = plate.clientWidth, ch = plate.clientHeight, dpr = Math.min(window.devicePixelRatio || 1, 2);
      if (cw < 8 || ch < 8) return false;
      glC.width = Math.round(cw * dpr); glC.height = Math.round(ch * dpr);
      var long = clamp(Math.round(Math.max(cw, ch) / 4), 128, 320);
      var sw = Math.max(2, Math.round(cw >= ch ? long : long * cw / ch)), shh = Math.max(2, Math.round(cw >= ch ? long * ch / cw : long));
      [st.vel, st.prs, st.dye, st.div].forEach(free);
      st.vel = pair(sw, shh); st.prs = pair(sw, shh); st.dye = pair(sw, shh); st.div = rt(sw, shh);
      st.W = cw; st.H = ch; st.sim = [sw, shh]; if (typeof readZoom === 'function') readZoom();
      return st.div.ok;
    }
    if (!alloc()) return null;

    var unit = 0;
    function run(pr, target, u) {
      gl.useProgram(pr.p); unit = 0;
      for (var k in u) {
        var loc = pr.u[k], v = u[k]; if (loc == null) continue;
        if (typeof v === 'number') gl.uniform1f(loc, v);
        else if (v.length === 2) gl.uniform2f(loc, v[0], v[1]);
        else if (v.length === 3) gl.uniform3f(loc, v[0], v[1], v[2]);
        else { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, v.t || v); gl.uniform1i(loc, unit); unit++; }
      }
      gl.bindFramebuffer(gl.FRAMEBUFFER, target ? target.f : null);
      if (target) gl.viewport(0, 0, target.w, target.h); else gl.viewport(0, 0, glC.width, glC.height);
      gl.drawArrays(gl.TRIANGLES, 0, 3); st.passes++;
    }

    function step(dt, real, from, to, moved) {
      var aspect = st.W / st.H, texel = [1 / st.sim[0], 1 / st.sim[1]];
      var sp = function (v) { return clamp(v / real * FORCE, -MAX_V, MAX_V); };
      var vx = sp((to[0] - from[0]) * aspect), vy = sp(to[1] - from[1]);
      var vel = st.vel, prs = st.prs, D = st.dye, div = st.div;
      if (moved) {                                                                    // 1. splat force + density
        run(P.splat, vel.write, { uSrc: vel.read, uFrom: from, uPoint: to, uColor: [vx, vy, 0], uAspect: aspect, uRadius: SPLAT_R, uStrength: 0.6 }); vel.swap();
        run(P.splat, D.write, { uSrc: D.read, uFrom: from, uPoint: to, uColor: [1, 1, 1], uAspect: aspect, uRadius: SPLAT_R, uStrength: 1 }); D.swap();
      }
      run(P.advect, vel.write, { uVel: vel.read, uSrc: vel.read, uDt: dt, uAspect: aspect, uDecay: Math.pow(VEL_DECAY, dt) }); vel.swap();   // 2
      run(P.div, div, { uVel: vel.read, uTexel: texel });                                                                               // 3. divergence
      run(P.scale, prs.write, { uSrc: prs.read, uK: 0.8 }); prs.swap();                                                                 // 4. warm start
      for (var i = 0; i < ITER; i++) { run(P.jacobi, prs.write, { uP: prs.read, uDiv: div, uTexel: texel }); prs.swap(); }
      run(P.grad, vel.write, { uP: prs.read, uVel: vel.read, uTexel: texel }); vel.swap();                                              // 5. project
      run(P.advect, D.write, { uVel: vel.read, uSrc: D.read, uDt: dt, uAspect: aspect, uDecay: Math.pow(DYE_DECAY, dt) }); D.swap();     // 6. dye
    }
    var qs = (location.search.match(/ink=([\d.,-]+)/) || [])[1];
    // line offset in output pixels, mip bias, gain, threshold: finer and lighter on 1x screens so small type stays legible
    var INK = qs ? qs.split(',').map(Number) : ((window.devicePixelRatio || 1) < 1.5 ? [0.55, -2, 2.0, 0.10] : [1.1, -0.7, 2.7, 0.07]);
    var INK_SMALL = [0.8, -1.2, 2.1, 0.09];                       // phone-sized plates: the same picture in far fewer pixels
    var col = { paper: [1, 1, 1], ink: [0, 0, 0], red: [1, 0, 0] };
    var zoom = 1;
    function readZoom() { zoom = parseFloat(getComputedStyle(plate).getPropertyValue('--zoom')) || 1; }
    readZoom();
    function colours() { ['paper', 'ink', 'red'].forEach(function (k) { col[k] = M.rgb(M.token('--' + k)).map(function (v) { return v / 255; }); }); }
    colours(); d.addEventListener('mpj-theme', colours);
    function composite() {
      run(P.comp, null, { uImg: st.tex || st.dye.read, uDye: st.dye.read, uVel: st.vel.read, uRes: [glC.width, glC.height],
        uPaper: col.paper, uInk: col.ink, uRed: col.red, uAspect: st.W / st.H, uImgAspect: st.imgAspect,
        uDistort: DISTORT, uLo: LO, uHi: HI, uBuild: st.build, uPlot: st.plot, uReady: st.tex ? 1 : 0, uLine: (qs || st.W >= 600 ? INK : INK_SMALL)[0], uBias: (qs || st.W >= 600 ? INK : INK_SMALL)[1], uGain: (qs || st.W >= 600 ? INK : INK_SMALL)[2], uTh: (qs || st.W >= 600 ? INK : INK_SMALL)[3], uZoom: zoom });
    }
    function clearSim() { [st.vel.read, st.vel.write, st.dye.read, st.dye.write, st.prs.read, st.prs.write].forEach(function (r) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, r.f); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT); }); }
    st.setImage = function (im) {
      var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.generateMipmap(gl.TEXTURE_2D);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      if (aniso) gl.texParameterf(gl.TEXTURE_2D, aniso.TEXTURE_MAX_ANISOTROPY_EXT, 4);
      if (st.tex) gl.deleteTexture(st.tex);
      st.tex = t; st.imgAspect = im.naturalWidth / im.naturalHeight;
      st.plot = 0; st.build = 0; st.buildTo = 0; clearSim(); lastInput = performance.now() - IDLE_MS + 900;
    };

    /* pointer, ghost pointer, loop */
    var ptr = [0.5, 0.5], prev = [0.5, 0.5], lastInput = performance.now(), wasGhost = false, last = performance.now(), visible = true, raf = 0, downAt = null;
    function aim(e) { var r = plate.getBoundingClientRect(); ptr = [clamp((e.clientX - r.left) / r.width, 0, 1), clamp(1 - (e.clientY - r.top) / r.height, 0, 1)]; lastInput = performance.now(); }
    plate.addEventListener('pointerdown', function (e) { aim(e); prev = ptr.slice(); downAt = [e.clientX, e.clientY]; st.dragged = false; });
    plate.addEventListener('pointermove', function (e) { aim(e); if (downAt && Math.abs(e.clientX - downAt[0]) + Math.abs(e.clientY - downAt[1]) > 8) st.dragged = true; });
    plate.addEventListener('pointerup', function () { setTimeout(function () { downAt = null; st.dragged = false; }, 0); });
    if ('ResizeObserver' in window) new ResizeObserver(function () { if (st.alive && Math.abs(plate.clientWidth - st.W) + Math.abs(plate.clientHeight - st.H) > 1) alloc(); }).observe(plate);
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { visible = es[0].intersectionRatio > 0.25; if (visible) { last = performance.now(); kick(); } }, { threshold: [0, 0.25, 0.5] }).observe(plate);
    d.addEventListener('visibilitychange', function () { last = performance.now(); kick(); });
    glC.addEventListener('webglcontextlost', function (e) { e.preventDefault(); st.alive = false; fallback(); });

    var lastMove = performance.now(), slept = false;
    function frame(t) {
      raf = 0;
      if (!st.alive || !visible || d.hidden) return;
      raf = requestAnimationFrame(frame);
      if (t - last < 15) return;                                  // never more than about 60 steps a second
      // The ghost pointer works in shifts (7 s on, 9 s off) so an idle page is not simulating forever.
      var ghost = t - lastInput > IDLE_MS && st.build < 0.01 && (t % 16000) < 7000;
      var animating = (st.tex && st.plot < 1) || st.build !== st.buildTo;
      if (!ghost && !animating && t - lastMove > 5000) { slept = true; last = t; return; }   // the dye has healed: hold the last frame
      if (slept) { slept = false; prev = ptr.slice(); }
      var real = clamp((t - last) / 1000, 1 / 240, 0.25), dt = Math.min(real, 1 / 30); last = t;
      st.passes = 0;
      if (ghost) { var a = t / 1000 * 0.55; ptr = [0.5 + 0.34 * Math.sin(a), 0.5 + 0.24 * Math.sin(2 * a + 0.6)]; }
      if (ghost !== wasGhost) prev = ptr.slice();                 // no streak when control changes hands
      wasGhost = ghost;
      var moved = st.tex && (ptr[0] !== prev[0] || ptr[1] !== prev[1]);
      if (moved || animating) lastMove = t;
      step(dt, real, prev, ptr, moved); prev = ptr.slice();
      if (st.tex && st.plot < 1) st.plot = Math.min(1, st.plot + real / 0.9);
      if (st.build !== st.buildTo) { var dir = st.buildTo > st.build ? 1 : -1; st.build = clamp(st.build + dir * real / 0.9, 0, 1); }
      composite();
      window.__mpj = { mode: 'gl', sim: st.sim, passes: st.passes, canvas: [glC.width, glC.height] };
    }
    function kick() { if (!raf && st.alive) raf = requestAnimationFrame(frame); }
    kick();
    return st;
  }

  function fallback() {
    mode = 'ink'; G = null; now.classList.remove('is-gl');
    hint.textContent = 'Every project here starts as a drawing of itself. Use the button to build this one.';
    window.__mpj = { mode: 'ink', passes: 0 };
    show(idx);
  }

  if (!M.reduced) { try { G = startGL(); } catch (e) { G = null; } }
  if (G) { mode = 'gl'; now.classList.add('is-gl'); show(0); } else fallback();
})();
