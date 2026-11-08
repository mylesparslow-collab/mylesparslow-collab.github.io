// Pixel painting helpers. Everything is in "room pixels": the film is 240×135 of them,
// drawn onto a 480×270 canvas so the detailed cats get their half-pixels.
export const W = 240, H = 135;

export function hash(n) {
  n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b);
  n ^= n >>> 13;
  n = Math.imul(n, 0xc2b2ae35);
  n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}

const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map((v) => (v + 0.5) / 16);
export const bayer = (x, y) => BAYER[(y & 3) * 4 + (x & 3)];

export function rect(ctx, x, y, w, h, col) {
  ctx.fillStyle = col;
  ctx.fillRect(x, y, w, h);
}
export function disc(ctx, cx, cy, r, col) {
  ctx.fillStyle = col;
  for (let dy = -r; dy <= r; dy++) {
    const w = Math.floor(Math.sqrt(r * r - dy * dy) + 0.3);
    ctx.fillRect(Math.round(cx - w), Math.round(cy + dy), w * 2 + 1, 1);
  }
}
export function ellipse(ctx, cx, cy, rx, ry, col) {
  ctx.fillStyle = col;
  for (let dy = -ry; dy <= ry; dy++) {
    const w = Math.floor(rx * Math.sqrt(Math.max(0, 1 - (dy * dy) / (ry * ry))) + 0.3);
    ctx.fillRect(Math.round(cx - w), Math.round(cy + dy), w * 2 + 1, 1);
  }
}
// A 1px pixel line (Bresenham).
export function pline(ctx, x0, y0, x1, y1, col) {
  ctx.fillStyle = col;
  x0 = Math.round(x0); y0 = Math.round(y0); x1 = Math.round(x1); y1 = Math.round(y1);
  const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  for (;;) {
    ctx.fillRect(x0, y0, 1, 1);
    if (x0 === x1 && y0 === y1) break;
    const e2 = 2 * err;
    if (e2 >= dy) { err += dy; x0 += sx; }
    if (e2 <= dx) { err += dx; y0 += sy; }
  }
}

// Offscreen layers, painted once and cached.
const layers = new Map();
export function layer(key, w, h, paint) {
  if (!layers.has(key)) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    const ctx = c.getContext('2d');
    paint(ctx, w, h);
    layers.set(key, c);
  }
  return layers.get(key);
}

// Vertical dithered gradient through a list of colours.
export function gradient(ctx, x0, y0, w, h, cols) {
  for (let y = 0; y < h; y++) {
    const f = (y / Math.max(1, h - 1)) * (cols.length - 1);
    const i = Math.min(cols.length - 2, Math.floor(f));
    const fr = f - i;
    for (let x = 0; x < w; x++) {
      ctx.fillStyle = bayer(x0 + x, y0 + y) < fr ? cols[i + 1] : cols[i];
      ctx.fillRect(x0 + x, y0 + y, 1, 1);
    }
  }
}

// Rolling hills: fills below a wavy line. Tiles horizontally across w.
export function hills(ctx, w, base, amp, waves, col, edge, seed = 1) {
  for (let x = 0; x < w; x++) {
    const a = (x / w) * Math.PI * 2;
    let y = base;
    waves.forEach(([k, m], i) => (y += Math.sin(a * k + seed * (i + 1)) * amp * m));
    y = Math.round(y);
    rect(ctx, x, y, 1, 200, col);
    if (edge) rect(ctx, x, y, 1, 1, edge);
  }
}

// A soft pixel cloud from overlapping discs.
export function cloud(ctx, x, y, s, col, shade) {
  const blobs = [[0, 0, 5], [6, -2, 6], [13, 0, 5], [18, 1, 4], [-5, 1, 4]];
  if (shade) blobs.forEach(([dx, dy, r]) => disc(ctx, x + dx * s, y + dy * s + 2, Math.round(r * s), shade));
  blobs.forEach(([dx, dy, r]) => disc(ctx, x + dx * s, y + dy * s, Math.round(r * s), col));
  rect(ctx, x - 9 * s, y + 2 * s, 31 * s, 4 * s, col);
}

export function tree(ctx, x, ground, s, cols) {
  rect(ctx, x - 1, ground - 10 * s, 3, 10 * s, cols.trunk);
  disc(ctx, x + 1, ground - 15 * s, 7 * s, cols.dark);
  disc(ctx, x - 3 * s, ground - 13 * s, 5 * s, cols.dark);
  disc(ctx, x, ground - 16 * s, 6 * s, cols.mid);
  disc(ctx, x - 2 * s, ground - 18 * s, 3 * s, cols.light);
}

export const lerp = (a, b, t) => a + (b - a) * t;
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const ease = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
export const seg = (t, a, b) => clamp((t - a) / (b - a));

// Distance travelled under a speed that ramps up between a0..a1 and down between d0..d1.
export function travel(t, v, a0, a1, d0, d1) {
  let s = 0;
  const dt = 1 / 60;
  for (let u = a0; u < Math.min(t, d1); u += dt) {
    const k = u < a1 ? (u - a0) / (a1 - a0) : u > d0 ? 1 - (u - d0) / (d1 - d0) : 1;
    s += v * ease(k) * dt;
  }
  return s;
}

export function mixHex(a, b, t) {
  const p = (s) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
  const A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('');
}
