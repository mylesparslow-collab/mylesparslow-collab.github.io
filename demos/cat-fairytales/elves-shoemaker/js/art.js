// Characters and props for The Three Brothers, in CatGPT's pixel style.
// Cats reuse CatGPT's sprite grids (catsprites.js) and detail pass (hd.js).
// New creatures (hare, horse) are built from simple shapes into the same palette-key grids,
// so they get the same outline, rounding and shading as the cats.
import { SIT, SIT_TAIL, SIT_FACES, SIT_MOUTHS, PAW_UP, WALK, SLEEP } from './catsprites.js';
import { detailGrid, detailPalette, scale2x } from './hd.js';

export const PAL = {
  newton: { o: '#2a1d2e', b: '#e9a05a', s: '#c47a3a', m: '#b5632a', l: '#fbf3e6', c: '#fbf3e6', C: '#fbf3e6', w: '#fbf3e6', a: '#fbf3e6', e: '#b9c25a', k: '#1e1a22', h: '#ffffff', p: '#f2a0a8', q: '#d9bba8' },
  skippy: { o: '#2a1d2e', b: '#f2bc7e', s: '#d99a5e', m: '#cf8648', l: '#f9e0bc', c: '#f9e0bc', C: '#f9e0bc', w: '#cf8648', a: '#f6cf9c', e: '#9a8a3a', k: '#1e1a22', h: '#ffffff', p: '#e89a98', q: '#c99a74' },
  simba: { o: '#0c0a10', b: '#2c2733', s: '#1c1822', m: '#2c2733', l: '#3a3443', c: '#3a3443', C: '#f2efe9', w: '#2c2733', a: '#2c2733', e: '#d6d86a', k: '#0c0a10', h: '#ffffff', p: '#6a4a55', q: '#0c0a10' },
  // Old Tom, the father: a grey tabby with a white blaze and a grizzled muzzle.
  tom: { o: '#2a1d2e', b: '#9c99a8', s: '#76738a', m: '#5f5c70', l: '#e6e3ec', c: '#e6e3ec', C: '#e6e3ec', w: '#e6e3ec', a: '#e6e3ec', e: '#c9b860', k: '#1e1a22', h: '#ffffff', p: '#d9a0a8', q: '#b7b2c2' },
  // A raccoon robber: grey with a black bandit mask and dark stripes.
  raccoon: { o: '#1e1a22', b: '#8f8a99', s: '#6c6878', m: '#26222c', l: '#e4e0ea', c: '#e4e0ea', C: '#e4e0ea', w: '#e4e0ea', a: '#3a3640', e: '#e8c24a', k: '#1e1a22', h: '#ffffff', p: '#c9909a', q: '#26222c' },
  hare: { o: '#2a1d2e', b: '#b08f6b', s: '#8a6c4e', m: '#6e5640', l: '#f2eadc', c: '#f2eadc', C: '#f2eadc', w: '#f2eadc', a: '#e6d8c2', e: '#5a4632', k: '#1e1a22', h: '#ffffff', p: '#e7a4a4', q: '#6e5640' },
  horse: { o: '#2a1d2e', b: '#a2603a', s: '#7a4424', m: '#3a2418', l: '#c9905e', c: '#c9905e', C: '#c9905e', w: '#f4ecdf', a: '#3c3440', e: '#4a2a1a', k: '#1e1a22', h: '#ffffff', p: '#d98a80', q: '#3a2418', r: '#b8453a', y: '#e2b84a' },
};
const FLUFF = { simba: [[10, 0], [10, 17], [11, 1], [11, 16], [15, 0], [15, 17]] };

// Prop colours (any key a palette doesn't define falls back to these).
const PROPS = {
  g: '#a7b0c4', d: '#6c7488', x: '#eef1f7', X: '#b9c0cf', y: '#e2b84a', Y: '#a8802a',
  D: '#6a4426', B: '#9a6a3e', o: '#2a1d2e', k: '#1e1a22', W: '#ffffff', r: '#b8453a', R: '#7e2a26',
  n: '#8b8f9c', N: '#5b5f6c',
};

export function bake(grid, pal = {}, flip = false) {
  const h = grid.length;
  const w = Math.max(...grid.map((r) => r.length));
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const ctx = c.getContext('2d');
  grid.forEach((row, y) =>
    [...row].forEach((ch, x) => {
      const col = pal[ch] ?? PROPS[ch];
      if (ch === '.' || !col) return;
      ctx.fillStyle = col;
      ctx.fillRect(flip ? w - 1 - x : x, y, 1, 1);
    }),
  );
  return c;
}

const cache = new Map();
const cached = (key, fn) => {
  if (!cache.has(key)) cache.set(key, fn());
  return cache.get(key);
};

function composeSit({ face = 'open', tail = 0, mouth = null, paw = null, fluff = null, mask = false } = {}) {
  const pad = paw !== null ? 3 : 0;
  const W = 22 + pad;
  const g = SIT.map((r) => ('.'.repeat(pad) + r + '.'.repeat(W)).slice(0, W).split(''));
  const put = (y, x, ch) => ch !== '.' && g[y] && x >= 0 && x < W && (g[y][x] = ch);
  const f = SIT_FACES[face];
  if (f) f.forEach((r, i) => [...r].forEach((ch, j) => (g[7 + i][pad + j] = ch)));
  if (mouth) [...SIT_MOUTHS[mouth]].forEach((ch, j) => (g[10][pad + j] = ch));
  if (mask) {
    // a bandit mask across the eyes (raccoons)
    for (const y of [6, 7, 8]) for (let x = 1; x < 17; x++) if ('bwB'.includes(g[y][pad + x]) && (x < 8 || x > 9 || y === 7)) g[y][pad + x] = 'm';
  }
  SIT_TAIL[tail].forEach((r, i) => [...r].forEach((ch, j) => put(9 + i, pad + 15 + j, ch)));
  fluff?.forEach(([y, x]) => g[y][pad + x] === '.' && (g[y][pad + x] = 'o'));
  if (paw !== null) {
    [...'osbbbb'].forEach((ch, j) => (g[17][pad + 1 + j] = ch));
    [...'osbbbo'].forEach((ch, j) => (g[18][pad + 1 + j] = ch));
    PAW_UP[paw].forEach((r, i) => [...r].forEach((ch, j) => put(4 + i, j, ch)));
  }
  return g.map((r) => r.join(''));
}

// A cat sprite at detail resolution (2 canvas px per room px).
// pose 'sit' { face, tail, mouth, paw, flip } | 'walk' { frame, flip } | 'sleep' { frame }
export function cat(id, pose = 'sit', o = {}) {
  const key = `${id}|${pose}|${JSON.stringify(o)}`;
  return cached(key, () => {
    const pal = detailPalette(PAL[id]);
    const fluff = !!FLUFF[id];
    if (pose === 'walk') return bake(detailGrid(WALK[o.frame ?? 0], { pose: 'walk', fluff }), pal, o.flip);
    if (pose === 'sleep') return bake(detailGrid(SLEEP[o.frame ?? 0], { pose: 'sleep', fluff }), pal, o.flip);
    const face = o.face ?? 'open';
    return bake(detailGrid(composeSit({ ...o, fluff: FLUFF[id] }), { pose: 'sit', fluff, face }), pal, o.flip);
  });
}

// Draws a detail sprite with its bottom edge on `feet`, left edge at x (room px).
export function put(ctx, img, x, feet, scale = 1) {
  const w = (img.width / 2) * scale, h = (img.height / 2) * scale;
  ctx.drawImage(img, Math.round(x * 2) / 2, Math.round((feet - h) * 2) / 2, w, h);
  return { x, y: feet - h, w, h };
}

// ---------- shape-built creatures ----------

class Grid {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.c = Array.from({ length: h }, () => Array(w).fill('.'));
  }
  set(x, y, ch) {
    x = Math.round(x);
    y = Math.round(y);
    if (x >= 0 && y >= 0 && x < this.w && y < this.h) this.c[y][x] = ch;
  }
  ell(cx, cy, rx, ry, ch) {
    for (let y = Math.floor(cy - ry); y <= Math.ceil(cy + ry); y++)
      for (let x = Math.floor(cx - rx); x <= Math.ceil(cx + rx); x++)
        if (((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1) this.set(x, y, ch);
  }
  line(x0, y0, x1, y1, t, ch) {
    const n = Math.ceil(Math.hypot(x1 - x0, y1 - y0) * 2) + 1;
    for (let i = 0; i <= n; i++) {
      const f = i / n;
      this.ell(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, t / 2, t / 2, ch);
    }
  }
  outline() {
    const src = this.c.map((r) => r.slice());
    const solid = (x, y) => y >= 0 && y < this.h && x >= 0 && x < this.w && src[y][x] !== '.';
    for (let y = 0; y < this.h; y++)
      for (let x = 0; x < this.w; x++)
        if (src[y][x] === '.' && (solid(x + 1, y) || solid(x - 1, y) || solid(x, y + 1) || solid(x, y - 1))) this.c[y][x] = 'o';
    return this;
  }
  rows() {
    return this.c.map((r) => r.join(''));
  }
}

const rad = (d) => (d * Math.PI) / 180;
// A two-part leg from (x, y). Angles in degrees from straight down; positive points forward (+x).
function leg(g, x, y, a1, a2, l1, l2, t1, t2, ch, hoof) {
  const kx = x + Math.sin(rad(a1)) * l1, ky = y + Math.cos(rad(a1)) * l1;
  const fx = kx + Math.sin(rad(a2)) * l2, fy = ky + Math.cos(rad(a2)) * l2;
  g.line(x, y, kx, ky, t1, ch);
  g.line(kx, ky, fx, fy, t2, ch);
  if (hoof) g.ell(fx, fy, t2 / 2 + 0.4, t2 / 2 + 0.2, hoof);
  return [fx, fy];
}

// Galloping horse, facing right. 4 frames: [frontNear, frontFar, hindNear, hindFar] as [upper, lower].
const GALLOP = [
  [[55, 75], [42, 62], [-48, -25], [-36, -14]],
  [[25, -25], [10, -40], [-22, 8], [-10, 18]],
  [[-12, -55], [-24, -48], [18, 38], [32, 50]],
  [[34, 8], [20, -18], [2, 28], [-12, 20]],
];
export function horse(frame = 0, opts = {}) {
  return cached(`horse|${frame}|${JSON.stringify(opts)}`, () => {
    const S = 1.35;
    const g = new Grid(Math.ceil(60 * S), Math.ceil(46 * S));
    const bob = [0, -1, 0, 1][frame];
    const P = (v) => v * S;
    const L = GALLOP[frame];
    const lift = (i) => (opts.lifted === i ? -8 : 0); // a hoof Newton is holding up
    // far legs first, in shade
    leg(g, P(37), P(24 + bob), L[1][0], L[1][1] + lift(1), P(7), P(7.5), P(3), P(2.2), 's', 'a');
    leg(g, P(18), P(24 + bob), L[3][0], L[3][1] + lift(3), P(7.5), P(7.5), P(3.4), P(2.2), 's', 'a');
    // tail
    const sw = [0, 1, 2, 1][frame];
    g.line(P(9), P(16 + bob), P(4), P(19 + sw), P(3.2), 'm');
    g.line(P(4), P(19 + sw), P(1.5), P(27 + sw), P(2.4), 'm');
    // body
    g.ell(P(26), P(20 + bob), P(14), P(7), 'b');
    g.ell(P(15), P(19 + bob), P(7.5), P(7.5), 'b');
    g.ell(P(37), P(19 + bob), P(6.5), P(6.5), 'b');
    g.line(P(38), P(17 + bob), P(45), P(8 + bob), P(7), 'b');
    g.ell(P(47), P(8 + bob), P(4), P(3.6), 'b');
    g.line(P(47), P(8 + bob), P(52), P(11.5 + bob), P(5), 'b');
    g.ell(P(52.5), P(12 + bob), P(2.4), P(2.2), 'l');
    g.line(P(45), P(4.5 + bob), P(44), P(0.5 + bob), P(2.2), 'b');
    g.line(P(48), P(6 + bob), P(52), P(10 + bob), P(1.3), 'w');
    // mane
    g.line(P(37), P(13 + bob), P(44.5), P(3.5 + bob), P(2.6), 'm');
    for (let i = 0; i < 4; i++) g.line(P(38 + i * 2), P(12 - i * 2.2 + bob), P(36 + i * 2 - sw), P(15 - i * 2.2 + bob), P(1.6), 'm');
    // harness: collar and a strap back to the coach
    if (opts.harness) {
      g.line(P(37), P(13 + bob), P(39), P(23 + bob), P(2.2), 'r');
    }
    g.set(P(48), P(7.5 + bob), 'k');
    g.set(P(53), P(12.5 + bob), 'q');
    // near legs
    leg(g, P(36), P(24 + bob), L[0][0], L[0][1] + lift(0), P(7), P(7.5), P(3.2), P(2.4), 'b', 'a');
    leg(g, P(16), P(24 + bob), L[2][0], L[2][1] + lift(2), P(7.5), P(7.5), P(3.6), P(2.4), 'b', 'a');
    g.outline();
    return bake(detailGrid(g.rows(), { pose: 'walk' }), detailPalette(PAL.horse));
  });
}

// Hare, facing right. frame 0 stretched, 1 gathered, 2 sitting up. opts.beard: shaggy cheeks.
export function hare(frame = 0, opts = {}) {
  return cached(`hare|${frame}|${JSON.stringify(opts)}`, () => {
    const g = new Grid(32, 24);
    if (frame === 2) {
      // sitting up on its haunches
      g.ell(13, 16, 6, 5.5, 'b');
      g.ell(15, 10, 4.5, 5, 'b');
      g.ell(16, 6, 4, 3.4, 'b');
      g.line(14, 3, 11, -2, 2.4, 'b');
      g.line(16, 3, 16, -2, 2.2, 'b');
      g.line(13.5, 2, 11.5, -1, 0.8, 'p');
      g.ell(6.5, 18, 2.2, 2, 'l');
      g.ell(15, 13, 2.5, 3, 'l');
      g.line(10, 20, 17, 20.5, 2.4, 'b');
      g.line(17, 13, 19, 16, 1.6, 'b');
      g.set(17, 5, 'k');
      g.set(19.6, 6.2, 'p');
      if (opts.beard) for (const [x, y] of [[18, 8], [19, 8.5], [17, 8.6], [20, 7.8]]) g.set(x, y, 'm');
      if (opts.tache) { g.set(18.5, 7.2, 'q'); g.set(19.5, 7.2, 'q'); }
    } else {
      const st = frame === 0;
      g.ell(13, 13, 8, 4.5, 'b');
      g.ell(8, 12, 5, 5, 'b');
      g.ell(21, 9, 4, 3.3, 'b');
      g.line(20, 7, st ? 14 : 15, st ? 3 : 1, 2.4, 'b');
      g.line(21, 7, st ? 16 : 18, st ? 2.5 : 1.2, 2.2, 'b');
      g.line(19, 6, st ? 15.5 : 16, st ? 3.8 : 2.6, 0.8, 'p');
      g.ell(3.5, 10, 2.1, 2, 'l');
      g.ell(14, 15.5, 5, 1.5, 'l');
      if (st) {
        g.line(7, 15, 0.5, 16.5, 2.6, 'b');
        g.line(18, 15, 26, 16, 2, 'b');
      } else {
        g.line(9, 15, 15, 18.5, 2.6, 'b');
        g.line(17, 15, 12, 18.5, 2, 'b');
      }
      g.set(22, 8, 'k');
      g.set(24.6, 9.2, 'p');
      if (opts.beard) for (const [x, y] of [[23, 11], [24, 11.4], [22, 11.6], [25, 10.8]]) g.set(x, y, 'm');
      if (opts.tache) { g.set(23.5, 10.2, 'q'); g.set(24.5, 10.2, 'q'); }
    }
    g.outline();
    return bake(detailGrid(g.rows(), { pose: 'walk' }), detailPalette(PAL.hare));
  });
}

// ---------- props (drawn at detail resolution via scale2x) ----------
const prop = (key, rows, pal = {}) => cached('prop|' + key, () => bake(scale2x(rows), pal));

export const HAMMER = () =>
  prop('hammer', [
    'oooooo',
    'oxXnno',
    'onnNNo',
    'oooooo',
    '..oBo.',
    '..oBo.',
    '..oBo.',
    '..oDo.',
    '..ooo.',
  ]);
export const RAZOR = () =>
  prop('razor', [
    '.oooooo....',
    'oxxxxxXo...',
    'oxxxxxXooooo',
    '.oooooooDDDo',
    '........oooo',
  ]);
export const BRUSH = () =>
  prop('brush', [
    '.oooo.',
    'oxxxxo',
    'oxxxxo',
    '.oBBo.',
    '.oBBo.',
    '.oDDo.',
    '.oooo.',
  ]);
export const SWORD = () =>
  prop('sword', [
    '..o..',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    '.oxo.',
    'oyyyo',
    'oYyYo',
    '.oDo.',
    '.oDo.',
    '.oyo.',
    '..o..',
  ]);
export const SHOE = (shine = false) =>
  prop('shoe' + shine, [
    '.oooo.',
    'onxxno',
    'ono.no',
    'ono.no',
    'oo..oo',
  ].map((r) => (shine ? r.replace(/n/g, 'x') : r)));
export const SPECTACLES = () =>
  prop('specs', [
    'ooo..ooo',
    'o.oooo.o',
    'ooo..ooo',
  ], { o: '#d9b45a' });
export const NIGHTCAP = () =>
  prop('cap', [
    '..........oo',
    '........oorWo',
    '......oorRro.',
    '....oorRrRro.',
    '..oorRrRrRo..',
    '.oWWWWWWWWo..',
    '.oooooooooo..',
  ]);
export const SATCHEL = () =>
  prop('satchel', [
    '..oooo..',
    '.o....o.',
    'oooooooo',
    'oBBBBBBo',
    'oByyBBBo',
    'oDDDDDDo',
    'oooooooo',
  ]);
export const SCISSORS = () =>
  prop('scissors', [
    'oo...oo',
    'oxo.oxo',
    '.oxoxo.',
    '..oxo..',
    '.oxoxo.',
    'oyo.oyo',
    'oyo.oyo',
    '.o...o.',
  ]);

// ---------- props for The Elves and the Shoemaker ----------
export const BONNET = () =>
  prop('bonnet', [
    '...oooo...',
    '..orrrro..',
    '.orrrrrro.',
    'orrWrrWrro',
    'oWWWWWWWWo',
    '.oo....oo.',
  ], { r: '#e88aa0', W: '#fff4e6' });
export const TOPHAT = () =>
  prop('tophat', [
    '..ooooooo..',
    '..okkkkko..',
    '..okkkkko..',
    '..orrrrro..',
    '..okkkkko..',
    'oooooooooooo',
  ].map((r) => r.padEnd(12, '.')), { k: '#2a2530', r: '#b8453a' });
export const SPECS_SIDE = () =>
  prop('specs-side', [
    'ooo...',
    'o.oooo',
    'ooo...',
  ], { o: '#d9b45a' });
// A little coat (front view) and a pointed hat, in any colour. c main, C shade.
export const COAT = (col, dark) =>
  prop('coat' + col, [
    '..ooooooo..',
    '.occcycccco',
    'occccycccco',
    'oCcccyccCco',
    'oCcccyccCco',
    'oCcccyccCco',
    '.occcyccco.',
    '..ooooooo..',
  ], { c: col, C: dark });
export const HAT = (col, dark) =>
  prop('hat' + col, [
    '...WW..',
    '..oWWo.',
    '..occo.',
    '.occco.',
    '.occco.',
    'occcco.',
    'occcccO',
    'oCCCCCo',
    'ooooooo',
  ].map((r) => r.padEnd(7, '.')), { c: col, C: dark, W: '#ffffff', O: '#2a1d2e' });
