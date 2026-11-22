/* Mockup L, "Tesserae": the mosaic wall. Source: themed/l/wall.js, copied to mockup-l/ by themed/render_l.py.
   Three r180 (vendor/, MIT), loaded through the page's import map. Built from the instanced-grass demo's structure.

   WHAT: thousands of small glass tesserae set in grout, five fields (one per room, or one on a room page), every project
   one larger tessera in its field (flagships in gold leaf), the pointer a raking light. Each tile has a small random tilt
   and an uneven surface, so the specular highlight jumps from tile to tile as the light moves and the gold flares.
   HOW: one quad geometry, per-instance attributes (rect, rotation + tilt + seed, colour, kind + project index); corner
   irregularity, lift and placement happen in the vertex shader, lighting (Blinn-Phong + bevel + fresnel, a two-stop
   gold ramp) in the fragment shader. The CPU only lays the wall out (on resize or theme change) and sets uniforms.
   PASSES: scene target (grout, tile shadows, tiles: 3 draws) -> half-res bright pass -> blur H -> blur V -> composite
   (bloom add, highlight shoulder, warm grade, vignette, grain) to the screen. 7 draw calls, 5 render-target switches.
   LAYOUT: the static CSS wall's .field boxes are the layout; this reads their rectangles, so both always agree.
   KEEP: TIER + ?n=, pixel ratio cap 1.5, antialias:false (edges are antialiased in the shader), pause when hidden or
   off screen, reduced motion = one settled frame redrawn only on change, info.autoReset=false + one reset per frame,
   picking on the CPU from the known layout (no GPU read-back). */
import * as THREE from 'three';

const stage = document.querySelector('[data-wall]');
const dataEl = document.getElementById('wall-data');
function boot() {
  const DATA = JSON.parse(dataEl.textContent);
  const isHome = DATA.rooms.length > 1;
  const query = new URLSearchParams(location.search);
  const probe = document.createElement('canvas').getContext('webgl2');
  if (!probe) return;                                   // the static CSS wall stays
  const dbg = probe.getExtension('WEBGL_debug_renderer_info');
  const software = /swiftshader|llvmpipe|software/i.test(String(probe.getParameter(dbg ? dbg.UNMASKED_RENDERER_WEBGL : probe.RENDERER)));
  const lose = probe.getExtension('WEBGL_lose_context'); if (lose) lose.loseContext();
  const lowEnd = software || matchMedia('(pointer:coarse)').matches || (navigator.hardwareConcurrency || 4) <= 4 || (navigator.deviceMemory || 8) <= 4;
  const TIER = { name: lowEnd ? 'low' : 'desktop', count: isHome ? (lowEnd ? 3000 : 9000) : (lowEnd ? 1400 : 3200) };
  const TARGET = Math.max(300, Math.min(60000, Math.round(+query.get('n')) || TIER.count));
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  try { start(DATA, isHome, TIER, TARGET, reduced); } catch (e) { stage.classList.remove('is-gl'); console.warn('wall: static fallback', e); }
}

/* ------------------------------------------------------------------ shaders */
const NOISE = /* glsl */`
  float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
  float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }`;

const TILE_VERT = /* glsl */`
  attribute vec4 aRect;    // centre x, centre y, width, height (CSS px, y down)
  attribute vec4 aRot;     // angle, tilt x, tilt y, seed
  attribute vec3 aCol;     // glass colour
  attribute vec2 aKind;    // kind (0 field glass, 1 stone, 2 project glass, 3 gold, 4 ground glass), project index or -1
  attribute float aShape;  // 0 a squared piece, 1 a triangle (one corner cut away), 2 a wedge (one end narrower)
  uniform vec2 uView; uniform vec4 uHover; uniform vec3 uLight; uniform float uShadow;
  varying vec2 vUv, vPos; varying vec3 vCol; varying vec4 vRot; varying float vKind, vLift, vShape;
  float hh(float n){ return fract(sin(n) * 43758.5453123); }
  void main(){
    vec2 c = position.xy;                                                     // corners at +-0.5
    float seed = aRot.w;
    float lift = (abs(aKind.y - uHover.x) < 0.5 ? uHover.y : 0.0) + (abs(aKind.y - uHover.z) < 0.5 ? uHover.w : 0.0);
    vec2 corner = sign(c);
    vec2 pulled = c * (1.0 - 0.16 * hh(seed * 7.13 + corner.x * 1.7 + corner.y * 3.9));   // every corner drawn in a little: irregular, never past its slot
    if (aShape > 0.5 && aShape < 1.5 && corner.x > 0.0 && corner.y > 0.0) pulled = vec2(-pulled.y, pulled.y);   // triangle: fold the corner away
    if (aShape > 1.5 && corner.x > 0.0) pulled.y *= 0.4 + 0.25 * hh(seed * 3.3);                             // wedge: one end narrower
    vec2 local = pulled * aRect.zw * (1.0 + 0.16 * lift);
    if (uShadow > 0.5) local += c * (3.0 + 8.0 * lift);                       // the shadow quad is larger; its edge is softened below
    float ca = cos(aRot.x), sa = sin(aRot.x);
    vec2 p = vec2(ca * local.x - sa * local.y, sa * local.x + ca * local.y) + aRect.xy;
    if (uShadow > 0.5) p += normalize(p - uLight.xy + 1e-4) * (1.0 + 5.0 * lift);   // cast away from the light
    vUv = c; vPos = p; vCol = aCol; vRot = aRot; vKind = aKind.x; vLift = lift; vShape = aShape;
    gl_Position = vec4(p.x / uView.x * 2.0 - 1.0, 1.0 - p.y / uView.y * 2.0, 0.0, 1.0);
  }`;

const TILE_FRAG = /* glsl */`
  uniform vec3 uLight; uniform float uLightR;
  varying vec2 vUv, vPos; varying vec3 vCol; varying vec4 vRot; varying float vKind, vLift, vShape;
  ${NOISE}
  void main(){
    vec2 q = abs(vUv);
    float edge = 0.5 - max(q.x, q.y);                                         // 0 at the rim, 0.5 at the centre
    float ca = cos(vRot.x), sa = sin(vRot.x);
    vec2 outL = q.x > q.y ? vec2(sign(vUv.x), 0.0) : vec2(0.0, sign(vUv.y));
    if (vShape > 0.5 && vShape < 1.5) {                                       // the triangle's cut edge
      float e2 = -(vUv.x + vUv.y) * 0.7071;
      if (e2 < edge) { edge = e2; outL = vec2(0.7071); }
    }
    float alpha = smoothstep(0.0, fwidth(edge) * 1.3, edge);                  // antialiased edge (the context has none)
    if (alpha <= 0.0) discard;
    float seed = vRot.w, kind = vKind;
    bool gold = kind > 2.5 && kind < 3.5, stone = kind > 0.5 && kind < 1.5, proj = kind > 1.5 && kind < 2.5;
    vec2 outW = vec2(ca * outL.x - sa * outL.y, sa * outL.x + ca * outL.y);
    float bev = 1.0 - smoothstep(0.0, 0.14, edge);
    vec2 rip = vec2(vnoise(vUv * 2.4 + seed), vnoise(vUv * 2.4 + seed + 17.3)) - 0.5;   // hand-made glass is never flat
    vec2 nxy = vRot.yz * (1.0 - 0.6 * vLift) + rip * (gold ? 0.5 : 0.18) + outW * bev * 0.7;
    vec3 N = normalize(vec3(nxy, 1.0));
    vec3 Lv = uLight - vec3(vPos, 0.0); float dist = length(Lv); vec3 L = Lv / dist;
    vec3 H = normalize(L + vec3(0.0, 0.0, 1.0));
    float ndl = max(dot(N, L), 0.0), ndh = max(dot(N, H), 0.0);
    float fall = 1.0 / (1.0 + dist * dist / (uLightR * uLightR));
    float near = 1.0 / (1.0 + dist * dist / (0.09 * uLightR * uLightR));    // tight pool: the gold only flares close to the light
    float body = vnoise(vUv * 3.1 + seed * 3.7), grain = vnoise(vUv * 7.0 + seed * 1.3);
    vec3 base = vCol, col;
    if (gold) {                                                               // gold leaf under glass: dark olive off-angle, a flare on-angle
      col = mix(base * 0.34, base * 1.0, pow(ndh, 16.0) * fall + 0.2 + 0.12 * body);
      col += base * pow(ndh, 140.0) * 2.2 * near;
      col += vec3(1.0, 0.93, 0.72) * pow(ndh, 900.0) * 3.2 * near;
      col += pow(max(dot(N, normalize(vec3(-0.4, -0.6, 0.7))), 0.0), 30.0) * 0.18;
    } else if (stone) {                                                       // marble: matte
      col = base * (0.7 + 0.14 * body + 0.18 * ndl * fall) * (0.95 + 0.1 * grain);
    } else {                                                                  // smalti: matte body, value moving inside each piece
      col = base * (0.78 + 0.2 * body + 0.1 * ndl * fall) * (0.93 + 0.14 * grain);
      float face = step(proj ? 0.0 : 0.8, fract(seed * 0.6180339));          // one piece in five has a face that can catch the light
      float sp = pow(ndh, proj ? 380.0 : 650.0) * (proj ? 0.55 : 0.75) * fall * face;   // a small sharp glint, never a glow
      col += sp * vec3(1.0, 0.97, 0.9);
      col += base * pow(1.0 - N.z, 2.0) * 0.1;
    }
    col *= mix(0.74, 1.0, smoothstep(0.0, 0.06, edge));                       // dark lip where the tile meets the grout
    col *= 1.0 + 0.14 * vLift;
    gl_FragColor = vec4(col, alpha);
  }`;

const SHADOW_FRAG = /* glsl */`
  uniform float uShadowA; varying vec2 vUv; varying float vLift;
  void main(){ vec2 q = abs(vUv); float a = smoothstep(0.5, 0.2, max(q.x, q.y)) * (uShadowA + 0.3 * vLift); gl_FragColor = vec4(0.0, 0.0, 0.0, a); }`;

const QUAD_VERT = /* glsl */`varying vec2 vUv; void main(){ vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const GROUT_FRAG = /* glsl */`
  uniform vec3 uGrout; uniform vec2 uView; varying vec2 vUv;
  ${NOISE}
  void main(){
    vec2 p = vec2(vUv.x, 1.0 - vUv.y) * uView;
    float n = vnoise(p * 0.3) * 0.55 + vnoise(p * 1.4) * 0.45;
    gl_FragColor = vec4(uGrout * (0.9 + 0.16 * n + 0.07 * (h21(floor(p)) - 0.5)), 1.0);
  }`;

const BRIGHT_FRAG = /* glsl */`
  uniform sampler2D tIn; uniform vec2 uTexel; uniform float uThr; varying vec2 vUv;
  void main(){
    vec3 c = 0.25 * (texture2D(tIn, vUv + uTexel * vec2(-0.5, -0.5)).rgb + texture2D(tIn, vUv + uTexel * vec2(0.5, -0.5)).rgb
                   + texture2D(tIn, vUv + uTexel * vec2(-0.5, 0.5)).rgb + texture2D(tIn, vUv + uTexel * vec2(0.5, 0.5)).rgb);
    float l = max(c.r, max(c.g, c.b));
    gl_FragColor = vec4(c * (max(l - uThr, 0.0) / max(l, 1e-4)), 1.0);      // only gold and the brightest glints get through
  }`;

const BLUR_FRAG = /* glsl */`
  uniform sampler2D tIn; uniform vec2 uDir; varying vec2 vUv;
  void main(){
    vec3 c = texture2D(tIn, vUv).rgb * 0.2270270;
    c += (texture2D(tIn, vUv + uDir * 1.3846).rgb + texture2D(tIn, vUv - uDir * 1.3846).rgb) * 0.3162162;
    c += (texture2D(tIn, vUv + uDir * 3.2308).rgb + texture2D(tIn, vUv - uDir * 3.2308).rgb) * 0.0702703;
    gl_FragColor = vec4(c, 1.0);
  }`;

const COMP_FRAG = /* glsl */`
  uniform sampler2D tScene, tBloom; uniform float uBloom, uVig, uGrain, uTime, uKnee; uniform vec2 uRes; uniform vec3 uTint;
  varying vec2 vUv;
  ${NOISE}
  void main(){
    vec3 c = texture2D(tScene, vUv).rgb + texture2D(tBloom, vUv).rgb * uBloom;
    vec3 hi = max(c - uKnee, 0.0);
    c = min(c, uKnee) + (1.0 - exp(-hi * 4.0)) * (1.0 - uKnee);            // highlights roll off instead of clipping flat
    c *= uTint;
    float v = length((vUv - 0.5) * vec2(uRes.x / uRes.y, 1.0)) * 0.9;
    c *= 1.0 - uVig * smoothstep(0.35, 1.05, v);
    c += (h21(vUv * uRes + fract(uTime * 0.37) * 91.0) - 0.5) * uGrain;
    gl_FragColor = vec4(c, 1.0);
  }`;

/* ------------------------------------------------------------------ helpers */
const hex = h => { h = (h || '#888888').trim().replace('#', ''); if (h.length === 3) h = h.replace(/./g, '$&$&'); const n = parseInt(h, 16); return [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255]; };
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const WHITE = [1, 1, 1];

function palette() {
  const cs = getComputedStyle(document.documentElement), v = n => hex(cs.getPropertyValue(n));
  const light = document.documentElement.getAttribute('data-theme') === 'light';
  return { light, grout: v('--ground'), gold: v('--gold-leaf'), stone: v('--g-stone'), ground: v('--g-ground'), slate: v('--g-slate'),
    legal: v('--g-legal'), business: v('--g-business'), creative: v('--g-creative'), design: v('--g-design'), research: v('--g-research') };
}

/* cubic-bezier(.2,.8,.2,1), the lift curve */
function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sx = t => ((ax * t + bx) * t + cx) * t, sy = t => ((ay * t + by) * t + cy) * t, dx = t => (3 * ax * t + 2 * bx) * t + cx;
  return x => { if (x <= 0) return 0; if (x >= 1) return 1; let t = x; for (let i = 0; i < 6; i++) { const d = dx(t); if (Math.abs(d) < 1e-6) break; t -= (sx(t) - x) / d; } return sy(Math.min(1, Math.max(0, t))); };
}
const LIFT = bezier(0.2, 0.8, 0.2, 1), LIFT_MS = 520;

/* ------------------------------------------------------------------ layout: where every tile goes */
function layout(DATA, TARGET, P) {
  const sr = stage.getBoundingClientRect(), W = Math.max(1, sr.width), H = Math.max(1, sr.height);
  const rel = el => { const r = el.getBoundingClientRect(); return { x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height }; };
  const panelEl = document.querySelector('.wall__panel, .band__panel');
  let panel = panelEl ? rel(panelEl) : null;
  if (panel && !(panel.x < W && panel.x + panel.w > 0 && panel.y < H && panel.y + panel.h > 0)) panel = null;   // stacked below on phones

  const panelArea = panel ? Math.max(0, Math.min(W, panel.x + panel.w) - Math.max(0, panel.x)) * Math.max(0, Math.min(H, panel.y + panel.h) - Math.max(0, panel.y)) : 0;
  const pitch = Math.sqrt(Math.max(1, W * H - panelArea) / TARGET);
  const gr = Math.min(2.2, Math.max(1.3, pitch * 0.13));                    // grout width
  const s = Math.min(16, Math.max(W < 640 ? 6.5 : TARGET >= 6000 ? 9 : 6.5, pitch - gr));   // phones get finer tiles so every project fits                           // tile size
  stage.style.setProperty('--ft', Math.ceil(2 * (s + gr) + gr * 2) + 'px'); // the room tags sit just inside each field's two frame courses
  const fields = Array.prototype.map.call(stage.querySelectorAll('.field'), el => ({ slug: el.getAttribute('data-room'), rect: rel(el), tag: (t => t && t.offsetParent ? t : null)(el.querySelector('.field__tag')) }));
  let seed = 20261121; const rnd = () => { seed = (seed + 0x6d2b79f5) | 0; let x = Math.imul(seed ^ (seed >>> 15), 1 | seed); x ^= x + Math.imul(x ^ (x >>> 7), 61 | x); return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
  const jit = (a) => (rnd() - 0.5) * 2 * a;

  /* obstacles, bucketed */
  const CELL = 48;
  const mkObs = () => ({ map: new Map(), add(x0, y0, x1, y1) { const b = [x0, y0, x1, y1]; for (let i = Math.floor(x0 / CELL); i <= Math.floor(x1 / CELL); i++) for (let j = Math.floor(y0 / CELL); j <= Math.floor(y1 / CELL); j++) { const k = i + ',' + j; if (!this.map.has(k)) this.map.set(k, []); this.map.get(k).push(b); } },
    hit(x0, y0, x1, y1) { for (let i = Math.floor(x0 / CELL); i <= Math.floor(x1 / CELL); i++) for (let j = Math.floor(y0 / CELL); j <= Math.floor(y1 / CELL); j++) { const l = this.map.get(i + ',' + j); if (l) for (const b of l) if (x0 < b[2] && x1 > b[0] && y0 < b[3] && y1 > b[1]) return true; } return false; } });
  const ALL = mkObs();                                                      // every tile already set

  const R = [], A = [], C = [], K = [];
  const SH = [];
  const push = (cx, cy, w, h, ang, col, kind, proj, tilt, shape) => {
    const T = tilt != null ? tilt : (kind === 3 ? 0.3 : kind === 1 ? 0.16 : 0.26);
    R.push(cx, cy, w, h); A.push(ang, jit(T), jit(T), rnd() * 1000); C.push(col[0], col[1], col[2]); K.push(kind, proj < 0 ? -5 : proj); SH.push(shape || 0);
    const c = Math.abs(Math.cos(ang)), sn = Math.abs(Math.sin(ang)), hx = (c * w + sn * h) / 2, hy = (sn * w + c * h) / 2;
    ALL.add(cx - hx, cy - hy, cx + hx, cy + hy);
  };
  const vary = (c, a) => { const k = 1 + jit(a); return [c[0] * k + jit(a * 0.3), c[1] * k + jit(a * 0.3), c[2] * k + jit(a * 0.3)]; };
  /* one room's smalti: mostly its own glass, some darker and lighter batches, now and then a piece from another batch */
  const OTHERS = [P.legal, P.business, P.creative, P.design, P.research, P.stone];
  const glassOf = base => () => {
    const r = rnd();
    if (r < 0.03) return vary(mix(base, OTHERS[Math.floor(rnd() * OTHERS.length)], 0.55), 0.08);
    return vary(r < 0.5 ? base : r < 0.7 ? mul(base, 0.8) : r < 0.82 ? mix(base, WHITE, 0.16) : r < 0.93 ? mul(base, 0.6) : mix(base, WHITE, 0.3), 0.12);
  };

  /* a run of tiles along one straight line, lengths varied, ends exact */
  const run = (a0, a1, c, horiz, colFn, kind, ang0) => {
    const L = a1 - a0; if (L < s * 0.5) return;
    const k = Math.max(1, Math.round(L / (s * 1.05 + gr))), lens = [];
    for (let i = 0; i < k; i++) lens.push(0.8 + 0.45 * rnd());
    const sum = lens.reduce((x, y) => x + y, 0), avail = L - (k - 1) * gr;
    let p = a0;
    for (let i = 0; i < k; i++) {
      const t = lens[i] / sum * avail;
      if (horiz) push(p + t / 2, c + jit(0.35), t, s, (ang0 || 0) + jit(0.035), colFn(), kind, -1);
      else push(c + jit(0.35), p + t / 2, s, t, (ang0 || 0) + jit(0.035), colFn(), kind, -1);
      p += t + gr;
    }
  };
  /* one course of tiles just inside a rectangle (a frame row) */
  const course = (x0, y0, x1, y1, colFn, kind) => {
    run(x0, x1, y0 + s / 2, true, colFn, kind); run(x0, x1, y1 - s / 2, true, colFn, kind);
    run(y0 + s + gr, y1 - s - gr, x0 + s / 2, false, colFn, kind); run(y0 + s + gr, y1 - s - gr, x1 - s / 2, false, colFn, kind);
  };
  /* fill a rectangle with courses of tiles that follow one gentle wave, skipping anything already set. Run at three
     sizes, like a mosaicist cutting smaller pieces for the gaps along every contour. */
  const fillPass = (x0, y0, x1, y1, colFn, kind, obsList, z) => {
    const amp = z * 0.28, k = 2 * Math.PI / (z * (22 + 10 * rnd())), ph = rnd() * 6.28;
    const wave = x => amp * Math.sin(x * k + ph), slope = x => Math.atan(amp * k * Math.cos(x * k + ph));
    const m = gr * 0.5, hit = (a0, b0, a1, b1) => { for (const o of obsList) if (o.hit(a0, b0, a1, b1)) return true; return false; };
    let y = y0 + gr * 0.5 + rnd() * z * 0.3;
    while (y < y1 - z * 0.45) {
      let h = z * (0.86 + 0.28 * rnd());
      if (y + h > y1) { h = y1 - y; if (h < z * 0.55) break; }
      let x = x0 + gr * 0.5 + rnd() * z * 0.5;
      while (x < x1 - z * 0.45) {
        let w = z * (z < s * 0.9 && rnd() < 0.3 ? 0.35 + 0.25 * rnd() : 0.72 + 0.58 * rnd());   // some slivers
        if (x + w > x1) { w = x1 - x; if (w < z * 0.5) break; }
        const cx = x + w / 2, cy = y + h / 2 + wave(cx);
        if (cy - h / 2 < y0 - 0.5 || cy + h / 2 > y1 + 0.5 || hit(cx - w / 2 - m, cy - h / 2 - m, cx + w / 2 + m, cy + h / 2 + m)) { x += Math.max(1.5, z * 0.22); continue; }
        const small = z < s * 0.9, u = rnd();
        const shape = small ? (u < 0.3 ? 1 : u < 0.45 ? 2 : 0) : (u < 0.03 ? 1 : u < 0.09 ? 2 : 0);   // cut pieces in the gaps
        push(cx, cy, w, h, slope(cx) + jit(0.07) + (shape === 1 ? Math.floor(rnd() * 4) * Math.PI / 2 : 0), colFn(), kind, -1, null, shape);
        x += w + gr * (0.55 + 0.9 * rnd());
      }
      y += h + gr * (0.6 + 0.8 * rnd());
    }
  };
  const fill = (x0, y0, x1, y1, colFn, kind, obs) => { for (const z of [s, s * 0.66, s * 0.46]) fillPass(x0, y0, x1, y1, colFn, kind, obs ? [ALL, obs] : [ALL], z); };

  const PROJ = [];                                                          // for picking: centre, half size, angle, index
  const byRoom = DATA.rooms.map(() => []);
  DATA.projects.forEach((p, i) => byRoom[p.r].push(i));
  const outer = mkObs();

  /* the inscription panel, framed by one course of stone */
  if (panel) {
    const f = s + gr;
    course(panel.x - gr - f + gr, panel.y - gr - f + gr, panel.x + panel.w + gr + f - gr, panel.y + panel.h + gr + f - gr, () => vary(P.stone, 0.06), 1);
    outer.add(panel.x - f - gr * 1.5, panel.y - f - gr * 1.5, panel.x + panel.w + f + gr * 1.5, panel.y + panel.h + f + gr * 1.5);
  }

  fields.forEach(F => {
    const ri = DATA.rooms.findIndex(r => r.slug === F.slug); if (ri < 0) return;
    const base = F.slug === 'design' ? mix(P.design, [0.42, 0.27, 0.1], 0.3) : P[F.slug], r = F.rect;
    outer.add(r.x - gr, r.y - gr, r.x + r.w + gr, r.y + r.h + gr);
    // frame: stone (slate around the white research field), then a dark row of the room's own glass
    const frameCol = F.slug === 'research' ? () => vary(P.slate, 0.07) : () => vary(P.stone, 0.06);
    course(r.x, r.y, r.x + r.w, r.y + r.h, frameCol, 1);
    const f1 = s + gr;
    course(r.x + f1, r.y + f1, r.x + r.w - f1, r.y + r.h - f1, () => vary(mul(base, 0.62), 0.07), 0);
    const ix0 = r.x + 2 * f1 + gr * 0.5, iy0 = r.y + 2 * f1 + gr * 0.5, ix1 = r.x + r.w - 2 * f1 - gr * 0.5, iy1 = r.y + r.h - 2 * f1 - gr * 0.5;
    const obs = mkObs();
    const list = byRoom[ri], n = list.length;
    // the projects sit above the room's tag, or beside it when the field is short and wide (whichever gives bigger tiles)
    let px0 = ix0, py1 = iy1;
    if (F.tag) {
      const t = rel(F.tag);
      obs.add(t.x - gr * 2, t.y - gr * 2, t.x + t.w + gr * 2, t.y + t.h + gr * 2);
      const cellOf = (w, h) => { const c = Math.max(1, Math.min(n, Math.round(Math.sqrt(n * w / h)))); return Math.min(w / c, h / Math.ceil(n / c)); };
      const above = cellOf(ix1 - ix0, t.y - gr * 2 - iy0), beside = cellOf(ix1 - (t.x + t.w + gr * 3), iy1 - iy0);
      if (beside > above * 1.15) px0 = t.x + t.w + gr * 3; else py1 = t.y - gr * 2;
    }
    // the room's projects, set in reading order on a loose grid, each outlined by one or two courses
    const pw = ix1 - px0, ph = py1 - iy0;
    if (n && pw > 0 && ph > 0) {
      let cols = Math.max(1, Math.min(n, Math.round(Math.sqrt(n * pw / ph))));
      let rows = Math.ceil(n / cols);
      while (cols > 1 && (cols - 1) * rows >= n) cols--;
      const cw = pw / cols, ch = ph / rows, cell = Math.min(cw, ch);
      const rings = cell > s * 7.5 ? 2 : 1, ringT = rings * (s + gr);
      const S0 = Math.max(s * 1.9, Math.min(48, (cell - 2 * ringT - 2 * gr) * 0.72));
      list.forEach((pi, k) => {
        const p = DATA.projects[pi], row = Math.floor(k / cols), col = k % cols;
        const inRow = row === rows - 1 ? n - row * cols : cols;
        const S = Math.min((p.f ? S0 * 1.2 : S0) * (0.92 + 0.14 * rnd()), cell - 2 * ringT - 2 * gr);
        const out = S / 2 + ringT + gr;
        const jx = Math.max(0, cw / 2 - out * 1.1) * 0.95, jy = Math.max(0, ch / 2 - out * 1.1) * 0.95;
        const cx = px0 + (col + 0.5 + (cols - inRow) / 2) * cw + jit(jx), cy = iy0 + (row + 0.5) * ch + jit(jy);
        const ang = jit(0.15);
        const own = p.a ? hex(p.a) : null, m3 = own ? (own[0] + own[1] + own[2]) / 3 : 0;   // its own screenshot's colour, as a hue shift only
        const pc = own ? mix(base, WHITE, 0.1).map((v, j) => Math.min(1, Math.max(0, v + (own[j] - m3) * 0.9))) : mix(base, WHITE, 0.1);
        push(cx, cy, S, S, ang, p.f ? vary(P.gold, 0.06) : vary(pc, 0.03), p.f ? 3 : 2, pi, p.f ? 0.22 : 0.2);
        const ca = Math.cos(ang), sa = Math.sin(ang);
        const ringCol = [() => vary(mul(base, F.slug === 'research' ? 0.45 : 0.42), 0.06), glassOf(base)]                      // the second course is the field's own glass: the contour shows in how it is laid;
        for (let g = 0; g < rings; g++) {
          const d = S / 2 + gr + s / 2 + g * (s + gr), cf = ringCol[g];
          const side = (u0, u1, v, horiz) => {                              // a run in the project's own rotated frame
            const L = u1 - u0; if (L < s * 0.5) return;
            const kk = Math.max(1, Math.round(L / (s + gr))), t = (L - (kk - 1) * gr) / kk;
            for (let i = 0; i < kk; i++) {
              const u = u0 + i * (t + gr) + t / 2, lx = horiz ? u : v, ly = horiz ? v : u;
              push(cx + ca * lx - sa * ly, cy + sa * lx + ca * ly, horiz ? t : s, horiz ? s : t, ang + jit(0.05), cf(), 0, -1, null, rnd() < 0.08 ? 2 : 0);
            }
          };
          side(-d - s / 2, d + s / 2, -d, true); side(-d - s / 2, d + s / 2, d, true);
          side(-d + s / 2 + gr, d - s / 2 - gr, -d, false); side(-d + s / 2 + gr, d - s / 2 - gr, d, false);
        }
        PROJ.push({ i: pi, cx, cy, half: S / 2 + ringT * 0.6, ang, S });
      });
    }
    fill(ix0, iy0, ix1, iy1, glassOf(base), 0, obs);
  });

  /* the ground between the panels */
  fill(gr, gr, W - gr, H - gr, () => { const r = rnd(); return vary(r < 0.93 ? P.ground : mix(P.ground, P.gold, 0.35), 0.1); }, 4, outer);

  return { W, H, s, gr, count: R.length / 4, SH: new Float32Array(SH), R: new Float32Array(R), A: new Float32Array(A), C: new Float32Array(C), K: new Float32Array(K), PROJ };
}

/* ------------------------------------------------------------------ renderer */
function start(DATA, isHome, TIER, TARGET, reduced) {
  const canvas = stage.querySelector('.stage__gl');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance' });
  let DPR = 1;
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;                   // palette hex values are used exactly as written
  renderer.info.autoReset = false;
  const halfOK = renderer.extensions.has('EXT_color_buffer_float') || renderer.extensions.has('EXT_color_buffer_half_float');
  const rtOpts = { type: halfOK ? THREE.HalfFloatType : THREE.UnsignedByteType, depthBuffer: false, stencilBuffer: false };
  const rtScene = new THREE.WebGLRenderTarget(4, 4, rtOpts), rtA = new THREE.WebGLRenderTarget(4, 4, rtOpts), rtB = new THREE.WebGLRenderTarget(4, 4, rtOpts);

  const cam = new THREE.Camera();                                           // shaders place everything in CSS pixels themselves
  // DoubleSide: the shaders flip y to CSS pixels, which reverses the quad's winding
  const shared = { uView: { value: new THREE.Vector2(1, 1) }, uLight: { value: new THREE.Vector3(0, 0, 400) }, uLightR: { value: 900 },
    uHover: { value: new THREE.Vector4(-9, 0, -9, 0) } };
  const tileMat = new THREE.ShaderMaterial({ vertexShader: TILE_VERT, fragmentShader: TILE_FRAG, side: THREE.DoubleSide, transparent: true, depthTest: false, depthWrite: false,
    uniforms: { ...shared, uShadow: { value: 0 } } });
  const shadowMat = new THREE.ShaderMaterial({ vertexShader: TILE_VERT, fragmentShader: SHADOW_FRAG, side: THREE.DoubleSide, transparent: true, depthTest: false, depthWrite: false,
    uniforms: { ...shared, uShadow: { value: 1 }, uShadowA: { value: 0.5 } } });
  const groutMat = new THREE.ShaderMaterial({ vertexShader: QUAD_VERT, fragmentShader: GROUT_FRAG, depthTest: false, depthWrite: false,
    uniforms: { uGrout: { value: new THREE.Vector3() }, uView: shared.uView } });
  const quadGeo = new THREE.PlaneGeometry(2, 2);
  const scene = new THREE.Scene();
  const grout = new THREE.Mesh(quadGeo, groutMat); grout.frustumCulled = false; grout.renderOrder = 0;
  let geo = null, shadows = null, tiles = null;

  const post = new THREE.Scene(), quad = new THREE.Mesh(quadGeo); quad.frustumCulled = false; post.add(quad);
  const brightMat = new THREE.ShaderMaterial({ vertexShader: QUAD_VERT, fragmentShader: BRIGHT_FRAG, depthTest: false, depthWrite: false,
    uniforms: { tIn: { value: rtScene.texture }, uTexel: { value: new THREE.Vector2() }, uThr: { value: 0.95 } } });
  const blurMat = new THREE.ShaderMaterial({ vertexShader: QUAD_VERT, fragmentShader: BLUR_FRAG, depthTest: false, depthWrite: false,
    uniforms: { tIn: { value: null }, uDir: { value: new THREE.Vector2() } } });
  const compMat = new THREE.ShaderMaterial({ vertexShader: QUAD_VERT, fragmentShader: COMP_FRAG, depthTest: false, depthWrite: false,
    uniforms: { tScene: { value: rtScene.texture }, tBloom: { value: rtA.texture }, uBloom: { value: 1 }, uVig: { value: 0.3 }, uGrain: { value: 0.03 },
      uTime: { value: 0 }, uKnee: { value: 0.8 }, uRes: { value: new THREE.Vector2(1, 1) }, uTint: { value: new THREE.Vector3(1.02, 1, 0.965) } } });
  scene.add(grout);

  window.__wall = { ready: false, tier: TIER.name, target: TARGET, tiles: 0, calls: 0, passes: 5, dpr: 1, fps: 0, halfFloat: halfOK };
  let L = null, P = null;
  function rebuild() {
    P = palette();
    L = layout(DATA, TARGET, P);
    const w = Math.round(L.W), h = Math.round(L.H);
    DPR = Math.min(devicePixelRatio || 1, w * h <= 440000 ? 3 : 1.5);         // a phone's small canvas can afford its full pixel ratio
    renderer.setPixelRatio(DPR); window.__wall.dpr = DPR;
    renderer.setSize(w, h, false);
    const pw = Math.max(1, Math.round(w * DPR)), ph = Math.max(1, Math.round(h * DPR));
    rtScene.setSize(pw, ph); rtA.setSize(Math.max(1, pw >> 1), Math.max(1, ph >> 1)); rtB.setSize(Math.max(1, pw >> 1), Math.max(1, ph >> 1));
    shared.uView.value.set(L.W, L.H);
    shared.uLight.value.z = Math.max(260, 0.42 * Math.max(L.W, L.H));
    shared.uLightR.value = 0.62 * Math.max(L.W, L.H);
    brightMat.uniforms.uTexel.value.set(1 / pw, 1 / ph);
    compMat.uniforms.uRes.value.set(pw, ph);
    groutMat.uniforms.uGrout.value.set(...P.grout);
    shadowMat.uniforms.uShadowA.value = P.light ? 0.3 : 0.55;
    brightMat.uniforms.uThr.value = 1.3;                                     // above any glass glint: only gold leaf blooms
    compMat.uniforms.uBloom.value = P.light ? 0.3 : 0.45;
    compMat.uniforms.uVig.value = P.light ? 0.08 : 0.22;
    compMat.uniforms.uGrain.value = P.light ? 0.022 : 0.032;
    compMat.uniforms.uKnee.value = P.light ? 0.93 : 0.8;
    if (tiles) { scene.remove(shadows, tiles); geo.dispose(); }
    geo = new THREE.InstancedBufferGeometry();
    geo.setIndex([0, 1, 2, 2, 1, 3]);
    geo.setAttribute('position', new THREE.Float32BufferAttribute([-0.5, -0.5, 0, 0.5, -0.5, 0, -0.5, 0.5, 0, 0.5, 0.5, 0], 3));
    geo.setAttribute('aRect', new THREE.InstancedBufferAttribute(L.R, 4));
    geo.setAttribute('aRot', new THREE.InstancedBufferAttribute(L.A, 4));
    geo.setAttribute('aCol', new THREE.InstancedBufferAttribute(L.C, 3));
    geo.setAttribute('aKind', new THREE.InstancedBufferAttribute(L.K, 2));
    geo.setAttribute('aShape', new THREE.InstancedBufferAttribute(L.SH, 1));
    geo.instanceCount = L.count;
    shadows = new THREE.Mesh(geo, shadowMat); shadows.frustumCulled = false; shadows.renderOrder = 1;
    tiles = new THREE.Mesh(geo, tileMat); tiles.frustumCulled = false; tiles.renderOrder = 2;
    scene.add(shadows, tiles);
    if (hover.cur >= 0 && labelOn) placeLabel(hover.cur);
  }

  /* ---------- light, hover and the label ---------- */
  const light = { x: 0, y: 0, tx: 0, ty: 0, last: -1e9, init: false };
  const hover = { cur: -1, t0: 0, prev: -1, p0: 0, pFrom: 0 };
  const label = document.getElementById('wall-label');
  let labelOn = false, kbd = false;
  const liftOf = now => {
    const a = hover.cur >= 0 ? (reduced ? 1 : LIFT(Math.min(1, (now - hover.t0) / LIFT_MS))) : 0;
    const b = hover.prev >= 0 ? (reduced ? 0 : hover.pFrom * (1 - LIFT(Math.min(1, (now - hover.p0) / LIFT_MS)))) : 0;
    return [a, b];
  };
  function setHover(i) {
    if (i === hover.cur) return;
    const now = performance.now();
    if (hover.cur >= 0) { hover.prev = hover.cur; hover.pFrom = liftOf(now)[0]; hover.p0 = now; }
    hover.cur = i; hover.t0 = now;
    stage.style.cursor = i >= 0 && !kbd ? 'pointer' : '';
    if (i >= 0) showLabel(i); else hideLabel();
    kick();
  }
  function showLabel(i) {
    if (!label) return;
    const p = DATA.projects[i];
    document.getElementById('wl-code').textContent = p.c;
    document.getElementById('wl-t').textContent = p.t;
    document.getElementById('wl-s').textContent = p.s;
    document.getElementById('wl-chip').className = 'tess tess--' + DATA.rooms[p.r].slug + (p.f ? ' tess--gold' : '');
    const img = document.getElementById('wl-img');
    if (img) {
      img.parentNode.hidden = !p.i;
      if (p.i && img.getAttribute('src') !== p.i) { img.onload = () => { if (hover.cur === i) placeLabel(i); }; img.src = p.i; }
    }
    label.setAttribute('href', p.h);
    labelOn = true; placeLabel(i); label.classList.add('is-on');
  }
  function placeLabel(i) {
    const t = L && L.PROJ.find(q => q.i === i); if (!t || !label) return;
    const lw = label.offsetWidth, lh = label.offsetHeight, m = 10;
    let x = Math.min(Math.max(m, t.cx - lw / 2), L.W - lw - m), y = t.cy - t.half - 14 - lh;
    if (y < m) y = t.cy + t.half + 14;
    label.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
  }
  function hideLabel() { labelOn = false; if (label) label.classList.remove('is-on'); }
  const pick = (x, y) => {
    if (!L) return -1;
    for (const t of L.PROJ) {
      const dx = x - t.cx, dy = y - t.cy, c = Math.cos(-t.ang), s = Math.sin(-t.ang);
      if (Math.abs(c * dx - s * dy) <= t.half && Math.abs(s * dx + c * dy) <= t.half) return t.i;
    }
    return -1;
  };
  const local = e => { const r = stage.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  const onUI = e => e.target.closest && e.target.closest('.stage__label, .field__tag, a, button');
  stage.addEventListener('pointermove', e => {
    if (e.pointerType === 'touch') return;
    const [x, y] = local(e); light.tx = x; light.ty = y; light.last = performance.now(); kbd = false;
    const overLabel = e.target.closest && e.target.closest('.stage__label');
    setHover(overLabel ? hover.cur : onUI(e) ? -1 : pick(x, y));
    kick();
  });
  stage.addEventListener('pointerleave', e => { if (e.pointerType !== 'touch') { light.last = -1e9; setHover(-1); } });
  stage.addEventListener('click', e => {
    if (onUI(e)) return;
    const [x, y] = local(e), i = pick(x, y);
    light.tx = x; light.ty = y; light.last = performance.now();
    if (e.pointerType === 'touch' || (e.pointerType === '' && matchMedia('(pointer:coarse)').matches)) { setHover(i); return; }   // tap shows the label; tap the label to open
    if (i >= 0) location.href = DATA.projects[i].h;
  });
  // keyboard: focusing a project's link elsewhere on the page lights its tessera
  document.addEventListener('focusin', e => {
    const a = e.target.closest && e.target.closest('[data-p]'); if (!a || stage.contains(a)) return;
    const i = +a.getAttribute('data-p'), t = L && L.PROJ.find(q => q.i === i); if (!t) return;
    kbd = true; light.tx = t.cx; light.ty = t.cy - 40; light.last = performance.now() + 1e6; setHover(i);
  });
  document.addEventListener('focusout', e => {
    if (!kbd) return;
    setTimeout(() => { const a = document.activeElement; if (!(a && a.closest && a.closest('[data-p]'))) { kbd = false; light.last = -1e9; setHover(-1); } }, 0);
  });

  /* ---------- frames ---------- */
  let tPrev = performance.now(), running = false, visible = true, frames = 0, fpsT = tPrev;
  function frame(now) {
    const dt = Math.min(0.05, (now - tPrev) / 1000); tPrev = now;
    const t = now / 1000;
    if (!light.init) { light.x = light.tx = L.W * 0.62; light.y = light.ty = L.H * 0.4; light.init = true; }
    if (!reduced && now - light.last > 1600) {                               // nobody pointing: the light drifts on its own
      light.tx = L.W * (0.56 + 0.34 * Math.sin(t * 0.11)); light.ty = L.H * (0.46 + 0.34 * Math.sin(t * 0.17 + 1.1));
    }
    const k = reduced ? 1 : 1 - Math.exp(-dt * (now - light.last < 1600 ? 9 : 2.2));
    light.x += (light.tx - light.x) * k; light.y += (light.ty - light.y) * k;
    shared.uLight.value.x = light.x; shared.uLight.value.y = light.y;
    const [la, lb] = liftOf(now);
    shared.uHover.value.set(hover.cur >= 0 ? hover.cur : -9, la, hover.prev >= 0 ? hover.prev : -9, lb);
    compMat.uniforms.uTime.value = t;

    renderer.info.reset();                                                  // once per frame: the stats span every pass
    renderer.setRenderTarget(rtScene); renderer.render(scene, cam);
    quad.material = brightMat; renderer.setRenderTarget(rtA); renderer.render(post, cam);
    quad.material = blurMat; blurMat.uniforms.tIn.value = rtA.texture; blurMat.uniforms.uDir.value.set(1.6 / rtA.width, 0); renderer.setRenderTarget(rtB); renderer.render(post, cam);
    blurMat.uniforms.tIn.value = rtB.texture; blurMat.uniforms.uDir.value.set(0, 1.6 / rtA.height); renderer.setRenderTarget(rtA); renderer.render(post, cam);
    quad.material = compMat; renderer.setRenderTarget(null); renderer.render(post, cam);

    const W = window.__wall; W.calls = renderer.info.render.calls; W.tiles = L.count; W.tileSize = +L.s.toFixed(2);
    frames++; if (now - fpsT > 500) { W.fps = Math.round(frames * 1000 / (now - fpsT)); frames = 0; fpsT = now; }
    if (!W.ready) { W.ready = true; stage.classList.add('is-gl'); const hint = document.getElementById('wall-hint'); if (hint) hint.hidden = false; if (label) label.hidden = false; }
  }
  const loop = now => frame(now);
  function sync() {
    const go = !reduced && visible && !document.hidden;
    if (go !== running) { running = go; renderer.setAnimationLoop(go ? loop : null); }
  }
  function kick() { if (!running && L) requestAnimationFrame(now => frame(now)); }   // reduced motion or off screen: draw once on change

  rebuild();
  frame(performance.now());
  if ('IntersectionObserver' in window) new IntersectionObserver(es => { visible = es[0].isIntersecting; sync(); }).observe(stage);
  document.addEventListener('visibilitychange', sync);
  sync();

  let rz = 0, lastW = Math.round(L.W), lastH = Math.round(L.H);
  new ResizeObserver(() => {
    clearTimeout(rz);
    rz = setTimeout(() => { const r = stage.getBoundingClientRect(); if (Math.round(r.width) === lastW && Math.round(r.height) === lastH) return; lastW = Math.round(r.width); lastH = Math.round(r.height); rebuild(); kick(); }, 120);
  }).observe(stage);
  document.addEventListener('mpl-theme', () => { rebuild(); kick(); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { rebuild(); kick(); });   // the panel's size settles with its font
  canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); renderer.setAnimationLoop(null); running = false; stage.classList.remove('is-gl'); });
}

if (stage && dataEl) boot();                           // last, so every const above is initialised
