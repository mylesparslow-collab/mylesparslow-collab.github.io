// The eight scenes of The Elves and the Shoemaker. Each scene draws itself from its local time t (seconds),
// so the film can be paused and scrubbed anywhere. Nothing here keeps state between frames.
import { cat, put, hare, SPECTACLES, NIGHTCAP, BONNET, SPECS_SIDE, HAT } from './art.js';
import {
  W, H, hash, bayer, rect, disc, ellipse, pline, layer, gradient, hills, tree,
  lerp, clamp, ease, seg, mixHex,
} from './paint.js';

const INK = '#2a1d2e';

// ---------- shared bits ----------

function sparkle(ctx, x, y, s, col = '#fff6d8') {
  x = Math.round(x); y = Math.round(y);
  rect(ctx, x, y - s, 1, s * 2 + 1, col);
  rect(ctx, x - s, y, s * 2 + 1, 1, col);
  if (s > 1) rect(ctx, x - 1, y - 1, 3, 3, col);
}
function blinkAt(t, seed) {
  return (t + hash(seed) * 5) % 4.3 < 0.14;
}
const stepAlpha = (v) => Math.round(clamp(v) * 4) / 4; // fades in hard steps, like old games

function words(ctx, text, x, y, size, col, font = '"Jacquarda Bastarda 9", "Pixelify Sans", monospace', shadow = INK, maxW = 0) {
  ctx.font = `${size}px ${font}`;
  if (maxW) {
    const w = ctx.measureText(text).width;
    if (w > maxW) { size = Math.floor(size * (maxW / w)); ctx.font = `${size}px ${font}`; }
  }
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  if (shadow) { ctx.fillStyle = shadow; ctx.fillText(text, x, y + 1); }
  ctx.fillStyle = col;
  ctx.fillText(text, x, y);
}
function stars(ctx, t, n = 40, seed = 1, maxY = 70) {
  for (let i = 0; i < n; i++) {
    const tw = Math.sin(t * 2 + i) > 0.6;
    rect(ctx, Math.floor(hash(i + seed) * W), Math.floor(hash(i + seed + 99) * maxY), 1, 1, tw ? '#ffffff' : '#b8b0d8');
  }
}
function flakes(ctx, t, x0, y0, w, h, n, seed = 1, speed = 9) {
  ctx.fillStyle = '#f4f8ff';
  for (let i = 0; i < n; i++) {
    const sp = speed * (0.6 + hash(i + seed) * 0.8);
    const x = x0 + (((hash(i + seed + 7) * w + Math.sin(t * 1.3 + i) * 3) % w) + w) % w;
    const y = y0 + (hash(i + seed + 50) * h + t * sp) % h;
    ctx.fillRect(Math.floor(x), Math.floor(y), 1, 1);
  }
}
function glowLayer(ctx, w, h, cx, cy, R, col) {
  ctx.fillStyle = col;
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const d = Math.hypot((x - cx) * 0.8, y - cy) / R;
      const band = Math.floor((1 - d) * 4 + bayer(x, y) * 0.5);
      for (let k = 0; k < band; k++) ctx.fillRect(x, y, 1, 1);
    }
}
function vignette(ctx, w, h, col, strength = 1) {
  ctx.fillStyle = col;
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const d = Math.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2));
      const band = Math.floor((d - 0.7) * 5 * strength + bayer(x, y) * 0.5);
      for (let k = 0; k < band; k++) ctx.fillRect(x, y, 1, 1);
    }
}
const glowAt = (ctx, key, cx, cy, R, col, a = 1) => {
  ctx.globalAlpha = a;
  ctx.drawImage(layer(key, W, H, (c, w, h) => glowLayer(c, w, h, cx, cy, R, col)), 0, 0);
  ctx.globalAlpha = 1;
};
const vig = (ctx, a = 1, col = 'rgba(14,8,18,0.22)') => {
  ctx.globalAlpha = a;
  ctx.drawImage(layer('vig-' + col, W, H, (c, w, h) => vignette(c, w, h, col)), 0, 0);
  ctx.globalAlpha = 1;
};

// ---------- characters ----------

// Old Tom at 2x: a grey cat with spectacles and a striped nightcap. He sits, or walks (facing right unless flip).
function drawTom(ctx, x, feet, o = {}) {
  const sc = o.scale ?? 2;
  if (o.walk !== undefined) {
    const f = o.walk % 4;
    const img = cat('tom', 'walk', { frame: f, flip: !!o.flip });
    const r = put(ctx, img, x, feet + (f % 2 ? -sc * 0.5 : 0), sc);
    // head is at cols 16-25 of the 26-wide sprite (mirrored when flipped)
    const hx = (c, w) => (o.flip ? x + (26 - c - w) * sc : x + c * sc);
    put(ctx, SPECS_SIDE(), hx(20.5, 6), r.y + 7 * sc, sc * 0.5 + 0.5 > 1 ? 1 : 1);
    put(ctx, NIGHTCAP(), hx(15.5, 12), r.y + 4.5 * sc, sc * 0.55 < 1 ? 1 : 1.0 + (sc > 1.5 ? 0.0 : 0));
    return r;
  }
  const img = cat('tom', 'sit', { face: o.face ?? 'open', mouth: o.mouth ?? null, tail: o.tail ?? 0, flip: !!o.flip });
  const r = put(ctx, img, x, feet, sc);
  const sx = o.flip ? x + (22 - 18) * sc : x;
  if (o.face !== 'blink') put(ctx, SPECTACLES(), sx + 4.5 * sc, r.y + 9.5 * sc, sc > 1.5 ? 1.5 : 1);
  put(ctx, NIGHTCAP(), sx + 3 * sc, r.y + 4.5 * sc, sc > 1.5 ? 1.5 : 1);
  return r;
}

function elf(ctx, id, x, feet, o = {}) {
  return put(ctx, cat(id, 'sit', { face: o.face ?? 'open', tail: o.tail ?? 0, flip: !!o.flip, mouth: o.mouth ?? null }), x, feet, o.scale ?? 1);
}
function runner(ctx, id, x, feet, t, flip = false, rate = 16, scale = 1) {
  const f = Math.floor(t * rate) % 4;
  return put(ctx, cat(id, 'walk', { frame: f, flip }), x, feet + (f % 2 ? -1 : 0), scale);
}
const COATS = { newton: ['#3f9a52', '#2c6e3a'], skippy: ['#d2483a', '#9a2e26'], simba: ['#8a5ac8', '#5e3a96'] };
// Little coat and pointed hat worn over a sitting elf (sprite is 22 wide; the body fills the left 18 columns).
function dressed(ctx, id, x, feet, o = {}) {
  const r = elf(ctx, id, x, feet, o);
  const [col, dk] = COATS[id];
  const fl = !!o.flip;
  const u = (c, w) => (fl ? x + 22 - c - w : x + c);
  const y = r.y;
  // coat over the chest and belly
  rect(ctx, u(2, 14), y + 11, 14, 7, INK);
  rect(ctx, u(3, 12), y + 11, 12, 6, col);
  rect(ctx, u(3, 2), y + 12, 2, 5, dk);
  rect(ctx, u(13, 2), y + 12, 2, 5, dk);
  rect(ctx, u(8.5, 1), y + 11, 1, 6, '#e2b84a');
  rect(ctx, u(7, 4), y + 11, 4, 1, '#fbf3e6');
  rect(ctx, u(3, 12), y + 16, 12, 1, dk);
  // hat
  const widths = [8, 8, 7, 6, 6, 5, 4, 3, 2, 1];
  widths.forEach((w, i) => {
    const bend = i > 5 ? Math.round((i - 5) * 0.6) : 0;
    const cx = fl ? x + 22 - 9 - bend : x + 9 + bend;
    rect(ctx, cx - w / 2 - 1, y + 3 - i, w + 2, 1, INK);
  });
  widths.forEach((w, i) => {
    const bend = i > 5 ? Math.round((i - 5) * 0.6) : 0;
    const cx = fl ? x + 22 - 9 - bend : x + 9 + bend;
    rect(ctx, cx - w / 2, y + 3 - i, w, 1, i < 2 ? dk : col);
  });
  const tipx = fl ? x + 22 - 9 - 3 : x + 9 + 3;
  rect(ctx, tipx - 1, y - 8, 2, 2, '#ffffff');
  return r;
}

function shoe(ctx, x, y, w, h, col, o = {}) {
  const { prog = 1, flip = false, shine = false } = o;
  const dk = o.dark ?? '#3a2418';
  const sole = Math.max(1, Math.round(h * 0.18));
  const prof = (u) => {
    if (u < 0.05) return 0.55 + (u / 0.05) * 0.2;
    if (u < 0.11) return 0.75 + ((u - 0.05) / 0.06) * 0.25;
    if (u < 0.36) return 1 - ((u - 0.11) / 0.25) * 0.08;
    if (u < 0.5) return 0.92 - ((u - 0.36) / 0.14) * 0.38;
    if (u < 0.78) return 0.54 - ((u - 0.5) / 0.28) * 0.06;
    return 0.2 + 0.28 * Math.sqrt(Math.max(0, 1 - ((u - 0.78) / 0.22) ** 2));
  };
  const X = (i) => (flip ? x + w - 1 - i : x + i);
  const tops = [];
  for (let i = 0; i < w; i++) tops.push(Math.max(sole + 1, Math.round(h * prof(i / w) * (sole + (1 - sole / h) * prog) / (sole + 1 - sole / h + 0.0001))));
  for (let i = -1; i <= w; i++) {
    const ti = tops[Math.min(w - 1, Math.max(0, i))];
    rect(ctx, X(i), y - ti - 1, 1, ti + 2, INK);
  }
  const hi = mixHex(col, '#ffffff', shine ? 0.55 : 0.28);
  for (let i = 0; i < w; i++) {
    const ti = tops[i];
    rect(ctx, X(i), y - ti, 1, ti - sole, col);
    rect(ctx, X(i), y - sole, 1, sole, dk);
    if (ti > sole + 1) rect(ctx, X(i), y - ti, 1, 1, hi);
    if (shine && i % 5 === 1 && ti > sole + 3) rect(ctx, X(i), y - ti + 1, 1, 2, '#ffffff');
  }
  if (prog > 0.6 && w >= 10) {
    // the opening for the foot, and laces
    const a = Math.round(w * 0.12), b = Math.round(w * 0.36);
    const dep = Math.max(1, Math.round(h * 0.12));
    for (let i = a; i < b; i++) rect(ctx, X(i), y - tops[i], 1, dep, '#1a0e16');
    for (let i = Math.round(w * 0.4); i < w * 0.7; i += w >= 30 ? 4 : 3) {
      const ti = tops[i];
      rect(ctx, X(i), y - ti + 1, 1, w >= 30 ? 3 : 2, '#f4ead2');
    }
    if (w >= 30) { const i = Math.round(w * 0.8); rect(ctx, X(i), y - tops[i] + 1, 1, Math.round(tops[i] - sole - 1), mixHex(col, '#000000', 0.25)); }
  }
  return { w, h };
}
const shoePair = (ctx, x, y, col, o = {}) => {
  shoe(ctx, x, y, o.w ?? 14, o.h ?? 9, col, { ...o, flip: false });
  shoe(ctx, x + (o.w ?? 14) + 2, y, o.w ?? 14, o.h ?? 9, col, { ...o, flip: false });
};

// a little coat laid flat with its sleeves out (13 x 9)
function drawCoat(ctx, x, y, col, dk) {
  const parts = [[3, 1, 7, 8], [0, 2, 3, 4], [10, 2, 3, 4]];
  parts.forEach(([a, b, w, h]) => rect(ctx, x + a - 1, y + b - 1, w + 2, h + 2, INK));
  parts.forEach(([a, b, w, h]) => rect(ctx, x + a, y + b, w, h, col));
  rect(ctx, x + 3, y + 7, 7, 2, dk);
  rect(ctx, x, y + 5, 3, 1, dk);
  rect(ctx, x + 10, y + 5, 3, 1, dk);
  rect(ctx, x + 6, y + 1, 1, 8, '#e2b84a');
  rect(ctx, x + 5, y + 1, 3, 1, '#fbf3e6');
}

// ---------- the workshop ----------

const CT0 = 48, CT1 = 172;     // counter left/right
const TOPY = 96;               // back edge of the counter top
const TOPB = 108;              // front edge of the counter top
const HOLE = [41, 96];         // the mouse hole
const DOOR = [5, 40, 24, 56];  // the front door's opening
const SHOP = {
  day: { wall: ['#d6b282', '#c79f6c', '#b88e5c'], floor: ['#a06f44', '#8a5c34', '#6e4828'], beam: '#6a4426', plank: '#ac8352', dark: '#3a2418', top: '#b07d48', front: '#845a34' },
  night: { wall: ['#4c3244', '#583a4a', '#62445a'], floor: ['#5c3c36', '#4c302e', '#3c2626'], beam: '#2c1a22', plank: '#3c2634', dark: '#1a0e16', top: '#7a5234', front: '#5a3a26' },
};

function shopBack(ctx, w, h, P) {
  gradient(ctx, 0, 0, W, 90, P.wall);
  for (let x = 0; x < W; x += 12) rect(ctx, x, 10, 1, 80, P.plank);
  rect(ctx, 0, 0, W, 9, P.beam);
  rect(ctx, 0, 9, W, 1, P.dark);
  rect(ctx, 0, 88, W, 8, P.beam);
  rect(ctx, 0, 88, W, 1, P.dark);
  gradient(ctx, 0, 96, W, 39, P.floor);
  for (let y = 100; y < H; y += 6) rect(ctx, 0, y, W, 1, P.dark);
  for (let i = 0; i < 16; i++) rect(ctx, Math.floor(hash(i + 3) * W), 96 + 6 * Math.floor(hash(i + 40) * 6), 1, 5, P.dark);
  // front door frame (the opening is painted live)
  rect(ctx, 2, 36, 30, 60, P.beam);
  rect(ctx, 2, 36, 30, 1, P.dark);
  // shelves
  rect(ctx, 36, 32, 68, 44, P.beam);
  rect(ctx, 38, 34, 64, 40, mixHex(P.plank, '#000000', 0.35));
  for (const y of [52, 74]) {
    rect(ctx, 36, y, 68, 3, P.beam);
    rect(ctx, 36, y, 68, 1, mixHex(P.beam, '#ffffff', 0.18));
    rect(ctx, 36, y + 3, 68, 1, P.dark);
  }
  // wall clock
  rect(ctx, 105, 21, 18, 38, P.beam);
  rect(ctx, 106, 22, 16, 36, mixHex(P.beam, '#000000', 0.3));
  disc(ctx, 114, 31, 6, '#2a1d2e');
  disc(ctx, 114, 31, 5, '#efe3c0');
  rect(ctx, 109, 40, 10, 16, '#1a0e16');
  // window
  rect(ctx, 129, 23, 48, 52, P.beam);
  rect(ctx, 127, 72, 52, 4, mixHex(P.beam, '#ffffff', 0.12));
  rect(ctx, 127, 76, 52, 1, P.dark);
  // stair archway
  rect(ctx, 198, 34, 34, 62, P.beam);
  rect(ctx, 202, 38, 26, 58, '#120a14');
  for (let i = 0; i < 6; i++) {
    rect(ctx, 204 + i * 3, 90 - i * 8, 24 - i * 3, 8, '#2a1a24');
    rect(ctx, 204 + i * 3, 90 - i * 8, 24 - i * 3, 1, '#4a3040');
  }
  // mouse hole
  disc(ctx, HOLE[0], HOLE[1] - 8, 6, P.dark);
  rect(ctx, HOLE[0] - 6, HOLE[1] - 8, 13, 8, P.dark);
  disc(ctx, HOLE[0], HOLE[1] - 8, 4, '#0c0610');
  rect(ctx, HOLE[0] - 4, HOLE[1] - 8, 9, 8, '#0c0610');
}
function counterBack(ctx, w, h, P) {
  const cw = CT1 - CT0;
  rect(ctx, CT0, TOPY, cw, TOPB - TOPY, P.top);
  for (let y = TOPY + 3; y < TOPB; y += 4) rect(ctx, CT0, y, cw, 1, mixHex(P.top, '#000000', 0.18));
  for (let i = 0; i < 12; i++) rect(ctx, CT0 + 2 + Math.floor(hash(i + 70) * (cw - 6)), TOPY + 1 + Math.floor(hash(i + 71) * 10), 3, 1, mixHex(P.top, '#000000', 0.28));
  rect(ctx, CT0, TOPY, cw, 1, mixHex(P.top, '#ffffff', 0.25));
  rect(ctx, CT0, TOPB, cw, 2, mixHex(P.top, '#000000', 0.35));
  rect(ctx, CT0, TOPB + 2, cw, H - TOPB - 2, P.front);
  for (let x = CT0 + 4; x < CT1 - 20; x += 38) {
    rect(ctx, x, TOPB + 6, 34, 18, mixHex(P.front, '#000000', 0.18));
    rect(ctx, x + 1, TOPB + 7, 32, 16, P.front);
    rect(ctx, x + 14, TOPB + 13, 6, 2, '#e2b84a');
  }
  rect(ctx, CT0 - 1, TOPY, 1, H - TOPY, P.dark);
  rect(ctx, CT1, TOPY, 1, H - TOPY, P.dark);
}
const shopLayers = (night) => {
  const P = night ? SHOP.night : SHOP.day;
  return [layer(night ? 'shop-n' : 'shop-d', W, H, (c, w, h) => shopBack(c, w, h, P)),
    layer(night ? 'ctr-n' : 'ctr-d', W, H, (c, w, h) => counterBack(c, w, h, P))];
};

function outsideView(ctx, kind, t, x0, y0, w, h, seed = 3) {
  ctx.save();
  ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.clip();
  const g = (cols) => gradient(ctx, x0, y0, w, h, cols);
  const ground = (y, col, edge) => { rect(ctx, x0, y0 + Math.round(h * y), w, h, col); rect(ctx, x0, y0 + Math.round(h * y), w, 1, edge); };
  if (kind === 'night' || kind === 'winternight') {
    g(['#141a3a', '#1f2a52', '#33407a']);
    disc(ctx, x0 + w * 0.75, y0 + h * 0.2, 4, '#f3e9c6');
    disc(ctx, x0 + w * 0.75 - 2, y0 + h * 0.2 - 1, 3, '#1f2a52');
    for (let i = 0; i < 9; i++) rect(ctx, x0 + Math.floor(hash(i + seed) * w), y0 + Math.floor(hash(i + seed + 9) * h * 0.55), 1, 1, i % 2 ? '#ffffff' : '#b8b0d8');
    ground(0.78, '#dfe8f4', '#ffffff');
    flakes(ctx, t, x0, y0, w, h, 14, seed, 8);
  } else if (kind === 'dawn') {
    g(['#2a2f66', '#8a5a86', '#f0a88a', '#ffd9a0']);
    ground(0.78, '#e8dfe6', '#ffffff');
    disc(ctx, x0 + w * 0.35, y0 + h * 0.74, 5, '#ffe6a0');
  } else if (kind === 'spring') {
    g(['#7fb7e0', '#a6d0ec', '#d2e8ef']);
    ground(0.7, '#7fb85e', '#9ccc78');
    for (let i = 0; i < 12; i++) rect(ctx, x0 + Math.floor(hash(i + 4) * w), y0 + Math.floor(h * 0.72 + hash(i + 5) * h * 0.2), 2, 2, i % 2 ? '#f6b8c8' : '#ffffff');
    disc(ctx, x0 + w * 0.3, y0 + h * 0.5, 7, '#f6b8c8');
    rect(ctx, x0 + w * 0.3 - 1, y0 + h * 0.5, 3, h * 0.25, '#6a4426');
  } else if (kind === 'summer') {
    g(['#4f9be0', '#7fc0ee', '#bfe2f4']);
    disc(ctx, x0 + w * 0.7, y0 + h * 0.2, 5, '#fff2a0');
    ground(0.7, '#4f9a3a', '#6ab84a');
    disc(ctx, x0 + w * 0.3, y0 + h * 0.52, 8, '#3f8a30');
    rect(ctx, x0 + w * 0.3 - 1, y0 + h * 0.55, 3, h * 0.22, '#6a4426');
  } else if (kind === 'autumn') {
    g(['#d8a870', '#ecc890', '#f6e0b0']);
    ground(0.72, '#b88c48', '#d8aa60');
    disc(ctx, x0 + w * 0.3, y0 + h * 0.5, 8, '#d9542e');
    disc(ctx, x0 + w * 0.34, y0 + h * 0.47, 5, '#e8902e');
    rect(ctx, x0 + w * 0.3 - 1, y0 + h * 0.55, 3, h * 0.22, '#5a3a22');
    for (let i = 0; i < 5; i++) rect(ctx, x0 + ((hash(i + 8) * w + t * 5 * (0.6 + hash(i))) % w), y0 + ((hash(i + 12) * h + t * 8) % h), 1, 1, '#d9542e');
  } else if (kind === 'winter') {
    g(['#aab8cc', '#c8d4e2', '#e6edf4']);
    ground(0.74, '#f4f8ff', '#ffffff');
    rect(ctx, x0 + w * 0.3 - 1, y0 + h * 0.52, 3, h * 0.24, '#5a4a40');
    disc(ctx, x0 + w * 0.3, y0 + h * 0.5, 6, '#f4f8ff');
    flakes(ctx, t, x0, y0, w, h, 22, seed, 10);
  } else { // day
    g(['#7fb7e0', '#a6d0ec', '#e2f0f0']);
    ground(0.8, '#e8f0f8', '#ffffff');
    rect(ctx, x0 + w * 0.15, y0 + h * 0.3, 10, 3, '#fbfdff');
    rect(ctx, x0 + w * 0.5, y0 + h * 0.18, 12, 3, '#fbfdff');
    rect(ctx, x0 + ((t * 6) % (w + 8)) - 4, y0 + h * 0.4, 2, 1, '#2a1d2e');
  }
  ctx.restore();
}
const windowGlass = (ctx, kind, t) => {
  outsideView(ctx, kind, t, 132, 26, 42, 44, 5);
  rect(ctx, 152, 26, 2, 44, '#6a4426');
  rect(ctx, 132, 47, 42, 2, '#6a4426');
};

function doorLeaf(ctx, open, kind, t, bell = 0) {
  const [x, y, w, h] = DOOR;
  if (open > 0.02) {
    outsideView(ctx, kind, t, x, y, w, h, 11);
    rect(ctx, x, y + h - 14, w, 14, kind === 'day' ? '#dfe8f4' : '#c9d6e8');
  }
  const lw = Math.max(2, Math.round(w * (1 - open)));
  rect(ctx, x, y, lw, h, '#5a3424');
  for (let i = 0; i < lw; i += 5) rect(ctx, x + i, y, 1, h, '#3e2418');
  rect(ctx, x, y + 3, lw, 1, '#7a4a30');
  rect(ctx, x, y + h - 14, lw, 1, '#3e2418');
  if (lw > 8) rect(ctx, x + lw - 4, y + h / 2, 2, 3, '#e2b84a');
  // the shop bell on a spring, above the door
  const sw = bell > 0 ? Math.sin(bell * 38) * 2.5 * (1 - Math.min(1, bell)) : 0;
  pline(ctx, 20, 34, 20 + sw * 0.4, 38, '#a8802a');
  disc(ctx, 20 + sw, 40, 2, '#e2b84a');
  rect(ctx, 20 + sw, 41, 1, 1, '#a8802a');
}

function clockHands(ctx, hh, mm) {
  const ang = (v) => v * Math.PI * 2 - Math.PI / 2;
  const hand = (len, a) => pline(ctx, 114, 31, 114 + Math.cos(a) * len, 31 + Math.sin(a) * len, INK);
  hand(2.5, ang(((hh % 12) + mm / 60) / 12));
  hand(4, ang(mm / 60));
}
function pendulum(ctx, t) {
  const sw = Math.sin(t * Math.PI) * 3;
  pline(ctx, 114, 41, 114 + sw, 51, '#c9a25a');
  disc(ctx, 114 + sw, 52, 1, '#e2b84a');
}

function candle(ctx, x, feet, t, o = {}) {
  const h = o.h ?? 7;
  rect(ctx, x - 1, feet - 1, 5, 1, '#6a4426');
  rect(ctx, x, feet - h, 3, h - 1, '#efe2c2');
  rect(ctx, x, feet - h, 1, h - 1, '#d4c4a0');
  rect(ctx, x + 1, feet - h - 1, 1, 1, INK);
  if (o.lit === false) return;
  const f = Math.floor(t * 9);
  const k = hash(f + (o.seed ?? 0));
  const fh = 3 + (k > 0.6 ? 1 : 0);
  rect(ctx, x + 1, feet - h - 1 - fh, 1, fh, '#ff9a3a');
  rect(ctx, x, feet - h - 1 - fh + 1, 3, Math.max(1, fh - 1), '#ffb84a');
  rect(ctx, x + 1, feet - h - fh, 1, Math.max(1, fh - 2), '#fff3c0');
}

function jar(ctx, x, feet, level) {
  rect(ctx, x - 1, feet - 14, 14, 1, '#8a96a8');
  rect(ctx, x, feet - 13, 12, 13, '#cfe0ee');
  rect(ctx, x + 1, feet - 12, 10, 11, '#e8f2fa');
  rect(ctx, x, feet - 13, 1, 13, '#ffffff');
  rect(ctx, x + 11, feet - 13, 1, 13, '#9ab0c4');
  const rows = Math.round(level * 9);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < 4; c++) {
      const cx = x + 1 + c * 2 + (r % 2), cy = feet - 2 - r;
      if (cx + 2 <= x + 11) { rect(ctx, cx, cy, 2, 1, '#e2b84a'); rect(ctx, cx, cy - 1 + 1, 1, 1, '#a8802a'); }
    }
  }
  if (level === 0) rect(ctx, x + 5, feet - 2, 2, 1, '#e2b84a'); // one lonely coin
  rect(ctx, x - 1, feet - 15, 14, 2, '#a8802a'); // lid
  rect(ctx, x + 3, feet - 15, 6, 1, '#4a3a1a');
}

// pairs of shoes on the two shelves
const SHOE_COLS = ['#8a5a30', '#b8453a', '#3f6aa8', '#5a8a4a', '#8a5a9a', '#c89a3a', '#6a4a3a', '#a84a6a'];
function shelfShoes(ctx, n) {
  for (let i = 0; i < Math.min(8, n); i++) {
    const row = i < 4 ? 0 : 1, slot = i % 4;
    const y = row ? 74 : 52;
    shoe(ctx, 40 + slot * 15, y, 6, 6, SHOE_COLS[i]);
    shoe(ctx, 46 + slot * 15, y, 6, 6, SHOE_COLS[i], { flip: false });
  }
}
// the counter's pair of finished shoes, with a gleam
function counterPair(ctx, x, feet, t, col = '#a8602e', gleam = true) {
  shoe(ctx, x, feet, 16, 10, col, { shine: true });
  shoe(ctx, x + 18, feet, 16, 10, col, { shine: true });
  if (gleam) {
    const k = Math.floor(t * 4) % 3;
    sparkle(ctx, x + 5 + k * 11, feet - 12 - (k % 2) * 3, 1 + (k === 1 ? 1 : 0));
  }
}
function leatherHide(ctx, x, y, w, h) {
  ellipse(ctx, x + w / 2, y + h / 2, w / 2 + 1, h / 2 + 1, '#4a2e1c');
  ellipse(ctx, x + w / 2, y + h / 2, w / 2, h / 2, '#9a6a3a');
  ellipse(ctx, x + w / 2 - 2, y + h / 2 - 1, w / 3, h / 3, '#b07a44');
  rect(ctx, x + 3, y + h - 3, 3, 1, '#7a4e28');
}
// flat shoe-shaped pieces cut from leather
function cutPieces(ctx, x, y, n = 1, col = '#a8703a') {
  for (let i = 0; i < n; i++) {
    const ox = x + i * 22;
    ellipse(ctx, ox + 8, y, 9, 3, '#4a2e1c');
    ellipse(ctx, ox + 8, y, 8, 2, col);
    ellipse(ctx, ox + 16, y - 2, 5, 3, '#4a2e1c');
    ellipse(ctx, ox + 16, y - 2, 4, 2, mixHex(col, '#ffffff', 0.12));
  }
}
function scissors(ctx, x, y, open) {
  const a = 0.15 + open * 0.5;
  const blade = (s) => pline(ctx, x, y, x + Math.cos(s * a) * 9, y + Math.sin(s * a) * 9 * 0.35 * s, '#e8edf4');
  blade(1); blade(-1);
  pline(ctx, x, y, x - 3, y - 2, '#e2b84a');
  pline(ctx, x, y, x - 3, y + 2, '#e2b84a');
  rect(ctx, x - 5, y - 3, 2, 2, '#e2b84a');
  rect(ctx, x - 5, y + 1, 2, 2, '#e2b84a');
}

// night lighting: a cool wash over the room, then warm glow where candles burn
function nightWash(ctx, a = 0.22) {
  ctx.fillStyle = `rgba(14,10,46,${a})`;
  ctx.fillRect(0, 0, W, H);
}
function candleGlow(ctx, t, cx, cy, key, a = 1) {
  glowAt(ctx, key, cx, cy, 130, 'rgba(255,176,96,0.08)', a * (0.8 + 0.2 * Math.sin(t * 9) * Math.sin(t * 5.3)));
}

// a surprised "!" over someone's head
function bang(ctx, x, y) {
  rect(ctx, x, y, 2, 5, '#f0c040');
  rect(ctx, x, y + 6, 2, 2, '#f0c040');
}

// ---------- 1. Title ----------
function snowSky(ctx, w, h) {
  gradient(ctx, 0, 0, w, 100, ['#10132e', '#1a2048', '#2c3468', '#4a4f86']);
  hills(ctx, w, 96, 6, [[1, 1], [3, 0.35]], '#3a4478', '#5a6498', 2);
  // far cottages with lit windows
  for (const [x, y] of [[14, 96], [48, 99], [92, 97]]) {
    rect(ctx, x, y - 10, 18, 10, '#2a2c52');
    for (let i = 0; i < 9; i++) rect(ctx, x - 1 + i * 1, y - 10 - i, 20 - i * 2 > 0 ? 20 - i * 2 : 0, 1, '#d8e0f0');
    rect(ctx, x + 5, y - 7, 3, 3, '#f0c36a');
    rect(ctx, x + 11, y - 7, 3, 3, '#f0c36a');
  }
}
function snowGround(ctx, w, h) {
  gradient(ctx, 0, 100, w, 35, ['#c6d2e6', '#dde6f2', '#eef3fa']);
  hills(ctx, w, 104, 3, [[2, 1], [5, 0.4]], '#dde6f2', '#ffffff', 4);
  for (let i = 0; i < 30; i++) rect(ctx, Math.floor(hash(i + 20) * w), 110 + Math.floor(hash(i + 21) * 22), 3, 1, '#b4c2da');
}
function shopFront(ctx, x, t) {
  const g = 112; // ground
  // walls
  rect(ctx, x, 62, 80, g - 62, '#7a4e3a');
  for (let y = 64; y < g; y += 4) for (let xx = x + (y % 8 ? 0 : 3); xx < x + 80; xx += 6) rect(ctx, xx, y, 5, 1, '#8c5c46');
  rect(ctx, x, 62, 80, 2, '#4a2e22');
  rect(ctx, x, 84, 80, 2, '#4a2e22');
  rect(ctx, x, 62, 3, g - 62, '#4a2e22');
  rect(ctx, x + 77, 62, 3, g - 62, '#4a2e22');
  // snowy gable roof
  for (let i = 0; i < 30; i++) rect(ctx, x - 6 + i, 62 - i, 92 - i * 2, 1, i % 4 === 0 ? '#3a2430' : '#52323a');
  for (let i = 0; i < 30; i++) rect(ctx, x - 6 + i, 62 - i, 92 - i * 2, 1, i < 3 ? '#ffffff' : i % 5 < 2 ? '#e8eff8' : '#52323a');
  rect(ctx, x - 7, 61, 94, 3, '#ffffff');
  rect(ctx, x - 7, 63, 94, 1, '#b4c2da');
  // chimney with smoke
  rect(ctx, x + 56, 28, 9, 22, '#6a4a44');
  rect(ctx, x + 55, 26, 11, 3, '#ffffff');
  for (let i = 0; i < 4; i++) {
    const a = (t * 0.35 + i / 4) % 1;
    ctx.globalAlpha = (1 - a) * 0.6;
    disc(ctx, x + 60 + Math.sin(a * 6 + i) * 3 + a * 6, 24 - a * 22, 2 + a * 2, '#c8d0e0');
  }
  ctx.globalAlpha = 1;
  // shop window (lit) with Old Tom inside
  rect(ctx, x + 6, 88, 32, 22, '#2a1814');
  rect(ctx, x + 8, 90, 28, 18, '#f2c36a');
  gradient(ctx, x + 8, 90, 28, 18, ['#f6d27c', '#e8a850']);
  const tom = put(ctx, cat('tom', 'sit', { face: blinkAt(t, 4) ? 'blink' : 'happy', tail: Math.floor(t * 0.8) % 2 }), x + 12, 108);
  put(ctx, SPECTACLES(), x + 16.5, tom.y + 9.5);
  put(ctx, NIGHTCAP(), x + 15, tom.y + 4.5);
  rect(ctx, x + 21, 90, 1, 18, '#2a1814');
  rect(ctx, x + 6, 109, 32, 3, '#4a2e22');
  rect(ctx, x + 8, 106, 3, 2, '#a8602e'); // shoes in the window
  // door
  rect(ctx, x + 48, 84, 18, g - 84, '#3a2418');
  rect(ctx, x + 50, 86, 14, g - 86, '#5a3424');
  rect(ctx, x + 51, 88, 12, 8, '#f2c36a');
  rect(ctx, x + 61, 100, 2, 3, '#e2b84a');
  rect(ctx, x + 46, g - 2, 22, 2, '#dfe8f4');
  // upstairs window, dim
  rect(ctx, x + 30, 68, 14, 12, '#2a1814');
  rect(ctx, x + 32, 70, 10, 8, '#8a6a8a');
  rect(ctx, x + 36, 70, 1, 8, '#2a1814');
  // snow drift along the base
  ellipse(ctx, x + 10, g, 18, 3, '#ffffff');
  ellipse(ctx, x + 72, g, 16, 3, '#ffffff');
}
function shopSign(ctx, x, t) {
  // iron bracket
  rect(ctx, x + 2, 66, 30, 2, '#2a1d2e');
  pline(ctx, x + 2, 78, x + 18, 68, '#2a1d2e');
  const sway = Math.sin(t * 1.7) * 2.5;
  // board hangs from two chains; it swings at the bottom
  const rows = 17;
  for (let r = 0; r < rows; r++) {
    const o = Math.round(sway * (r / rows));
    const y = 70 + r;
    rect(ctx, x - 22 + o, y, 28, 1, r === 0 || r === rows - 1 ? '#2a1d2e' : '#c9a25a');
    rect(ctx, x - 22 + o, y, 1, 1, '#2a1d2e');
    rect(ctx, x + 5 + o, y, 1, 1, '#2a1d2e');
    if (r > 1 && r < rows - 2) rect(ctx, x - 20 + o, y, 24, 1, '#3a2430');
  }
  pline(ctx, x - 14, 68, x - 14 + Math.round(sway * 0.1), 70, '#2a1d2e');
  pline(ctx, x - 1, 68, x - 1 + Math.round(sway * 0.1), 70, '#2a1d2e');
  const o = Math.round(sway * 0.5);
  shoe(ctx, x - 17 + o, 83, 20, 9, '#e8a860', { shine: true });
  // snow cap on the sign
  rect(ctx, x - 22, 69, 28, 1, '#ffffff');
}
function lamp(ctx, x, t) {
  rect(ctx, x, 72, 3, 40, '#2a1d2e');
  rect(ctx, x - 3, 64, 9, 8, '#2a1d2e');
  rect(ctx, x - 2, 65, 7, 6, '#f6d27c');
  rect(ctx, x - 4, 62, 11, 2, '#ffffff');
}
function sceneTitle(ctx, t) {
  ctx.drawImage(layer('t-sky', W, H, snowSky), 0, 0);
  stars(ctx, t, 50, 3, 60);
  disc(ctx, 30, 32, 8, '#f6edc8');
  disc(ctx, 33, 30, 7, '#1c2250');
  ctx.drawImage(layer('t-snow', W, H, snowGround), 0, 0);
  // pines
  [[8, 108], [60, 106], [112, 104]].forEach(([x, y]) => {
    tree(ctx, x, y, 1.1, { trunk: '#4a3a30', dark: '#1d3a34', mid: '#2a5046', light: '#3a6458' });
    ellipse(ctx, x - 1, y - 24, 6, 2, '#ffffff');
  });
  lamp(ctx, 126, t);
  shopFront(ctx, 150, t);
  shopSign(ctx, 146, t);
  glowAt(ctx, 'lampglow', 127, 68, 38, 'rgba(255,214,130,0.08)', 0.8 + 0.2 * Math.sin(t * 7));
  glowAt(ctx, 'winglow', 176, 100, 34, 'rgba(255,190,100,0.07)');
  flakes(ctx, t, 0, 0, W, H, 90, 2, 12);
  // the three elves walk up the lane and sit in front of the shop
  [['newton', 0], ['skippy', 1], ['simba', 2]].forEach(([id, i]) => {
    const stop = 40 + i * 32;
    const x = lerp(-30 - i * 26, stop, ease(seg(t, 1 + i * 0.4, 8 + i * 0.4)));
    const feet = 124 - Math.round(Math.sin((x / W) * Math.PI) * 2);
    if (t < 8 + i * 0.4) runner(ctx, id, x, feet, t, false, 8);
    else elf(ctx, id, x, feet, { face: blinkAt(t, i) ? 'blink' : 'up', tail: Math.floor(t + i) % 2 });
  });
  ctx.globalAlpha = 0.45;
  ctx.drawImage(layer('vig-title', W, H, (c, w, h) => vignette(c, w, h, 'rgba(8,6,20,0.5)')), 0, 0);
  ctx.globalAlpha = 1;
  ctx.globalAlpha = stepAlpha(seg(t, 3, 5.5));
  words(ctx, 'The Elves and the Shoemaker', W / 2, 20, 17, '#f2e2b6', undefined, INK, 226);
  ctx.globalAlpha = stepAlpha(seg(t, 5.5, 7.5));
  words(ctx, 'after the Brothers Grimm', 102, 36, 8, '#b8a8c8', '"Pixelify Sans", monospace');
  ctx.globalAlpha = 1;
}

// ---------- 2. Poor ----------
function emptyShelfJar(ctx) { /* the shelves stay bare */ }

function sceneShopNight(ctx, t, o = {}) {
  const [back, ctr] = shopLayers(true);
  ctx.drawImage(back, 0, 0);
  windowGlass(ctx, o.window ?? 'winternight', t);
  doorLeaf(ctx, 0, 'night', t);
  clockHands(ctx, o.hh ?? 11, o.mm ?? 30);
  pendulum(ctx, t);
  return ctr;
}

function scenePoor(ctx, t) {
  const ctr = sceneShopNight(ctx, t, { hh: 8 + t / 25, mm: 5 + t * 1.5 });
  const walkStart = 18.3;
  const gone = t > 23.2;
  // Old Tom behind the counter
  let tx = 98;
  const walking = t >= walkStart;
  if (walking) tx = lerp(98, 204, ease(seg(t, walkStart + 0.9, 23.2)));
  const alpha = walking ? 1 - clamp((tx - 176) / 28) : 1;
  const yawn = t > 12.5 && t < 16;
  if (!gone) {
    ctx.save();
    if (walking) { ctx.beginPath(); ctx.rect(0, 0, 232, H); ctx.clip(); }
    ctx.globalAlpha = stepAlpha(alpha);
    if (walking && t > walkStart + 0.9) drawTom(ctx, tx, 106, { walk: Math.floor(t * 6), flip: false });
    else drawTom(ctx, tx, 106, {
      face: yawn ? 'blink' : blinkAt(t, 9) ? 'blink' : t > 17 ? 'up' : 'side',
      mouth: yawn ? 'yawn' : null,
      tail: Math.floor(t * 0.6) % 2,
    });
    ctx.restore();
  }
  ctx.drawImage(ctr, 0, 0);

  // on the counter
  candle(ctx, 58, 106, t, { h: t > 21 ? 4 : 7 });
  jar(ctx, 156, 107, 0);
  if (t < 4.3) {
    leatherHide(ctx, 98, 98, 36, 9);
  } else if (t < 8.2) {
    // the hide is cut: a dark line follows the scissors, the piece shrinks
    const k = seg(t, 4.3, 8.2);
    leatherHide(ctx, 98 + k * 6, 98, 36 - k * 14, 9);
    cutPieces(ctx, 100, 105, 1);
  } else {
    cutPieces(ctx, 100, 103, 2, '#a8703a');
  }
  if (t < 8.2 && t > 1.2) {
    const k = ((t - 1.2) * 0.9) % 1;
    scissors(ctx, 100 + seg(t, 1.2, 8.2) * 36 + 3, 102, 0.5 + 0.5 * Math.sin(t * 8));
    if (Math.floor(t * 8) % 8 === 0) sparkle(ctx, 112 + k * 20, 99, 1, '#e8edf4');
  }
  // the room darkens and the candle gutters as Tom goes up to bed
  const dim = seg(t, 20, 24);
  nightWash(ctx, 0.2 + dim * 0.16);
  candleGlow(ctx, t, 59, 100, 'cg-poor', 1 - dim * 0.55);
  vig(ctx, 1);
  // two glints in the mouse hole, near the end
  if (t > 22.6 && !(t > 23.9 && t < 24.05)) {
    rect(ctx, HOLE[0] - 2, HOLE[1] - 5, 1, 1, '#ffe08a');
    rect(ctx, HOLE[0] + 1, HOLE[1] - 5, 1, 1, '#ffe08a');
  }
}

// ---------- 3. Morning ----------
function sceneMorning(ctx, t) {
  const [back, ctr] = shopLayers(false);
  ctx.drawImage(back, 0, 0);
  windowGlass(ctx, 'day', t);
  // the front door opens twice: the hare comes in and goes out
  const doorOpen = ease(seg(t, 7.4, 8.1)) * (1 - ease(seg(t, 11.2, 11.9))) + ease(seg(t, 13.9, 14.5)) * (1 - ease(seg(t, 16.4, 17)));
  const bell = t > 8 && t < 9.4 ? t - 8 : t > 14.3 && t < 15.7 ? t - 14.3 : 0;
  doorLeaf(ctx, doorOpen, 'day', t, bell);
  clockHands(ctx, 7, 12 + t * 0.4);
  pendulum(ctx, t);
  shelfShoes(ctx, 0);

  // Tom comes down the stairs, finds the shoes
  const found = t > 3.2;
  const tx = found ? 98 : lerp(206, 98, ease(seg(t, 0.4, 3.2)));
  if (!found) {
    ctx.globalAlpha = stepAlpha(seg(t, 0.4, 1.4));
    drawTom(ctx, tx, 106, { walk: Math.floor(t * 6), flip: true });
    ctx.globalAlpha = 1;
  } else {
    const hop = t > 6.3 && t < 7.2 ? -Math.round(Math.sin(((t - 6.3) / 0.9) * Math.PI) * 4) : t > 16.8 && t < 17.8 ? -Math.round(Math.sin(((t - 16.8) / 1.0) * Math.PI) * 4) : 0;
    drawTom(ctx, tx, 106 + hop, {
      face: blinkAt(t, 12) ? 'blink' : t < 6.3 ? 'up' : t < 9 ? 'happy' : t < 16 ? 'side' : 'happy',
      mouth: t > 3.4 && t < 5.2 && Math.floor(t * 5) % 2 ? 'meow' : t > 17 && t < 18.4 && Math.floor(t * 5) % 2 ? 'meow' : null,
      tail: Math.floor(t * 1.2) % 2,
    });
    if (t < 5.4) bang(ctx, tx + 20, 56 + Math.round(Math.sin(t * 10) * 1));
  }
  ctx.drawImage(ctr, 0, 0);

  jar(ctx, 156, 107, t > 14 ? lerp(0, 0.28, seg(t, 14, 15)) : 0);
  candle(ctx, 58, 106, t, { h: 3, lit: false });

  // the shoes: on the counter, then sold to the hare
  const hx = 4; // where the hare stands
  const shoeX = t < 10.3 ? 108 : lerp(108, 54, ease(seg(t, 10.3, 11.6)));
  if (t < 12.2) {
    counterPair(ctx, shoeX, 105, t, '#a8602e', t < 10.3);
    if (t > 3.2 && t < 7) for (let i = 0; i < 4; i++) {
      const a = (t * 1.5 + i / 4) % 1;
      sparkle(ctx, 108 + Math.sin(i * 2.4) * 18 + 17, 88 - a * 6 + Math.cos(i) * 4, 1 + (i % 2), a < 0.5 ? '#fff6d8' : '#ffe08a');
    }
  }
  // the hare in her bonnet
  let hX = -40, hF = 2, hY = 116;
  if (t >= 8.1 && t < 10.4) { hX = lerp(-34, hx, ease(seg(t, 8.1, 10.4))); hF = Math.floor(t * 7) % 2; hY = hF === 0 ? 113 : 116; }
  else if (t >= 10.4 && t < 14.6) { hX = hx; hF = 2; }
  else if (t >= 14.6 && t < 17) { hX = lerp(hx, -40, ease(seg(t, 14.6, 17))); hF = 1 + (Math.floor(t * 7) % 2) * 0; hF = Math.floor(t * 7) % 2; hY = hF === 0 ? 113 : 116; }
  if (hX > -38 && hX < 245) {
    const HS = 1.3;
    const hr = put(ctx, hare(hF), hX, hY, HS);
    put(ctx, BONNET(), hX + (hF === 2 ? 11.5 : 19) * HS, hr.y + (hF === 2 ? 5.5 : 6.5) * HS, 1);
    if (t >= 11.6 && t < 14.6) {
      shoe(ctx, hX + 26, 118, 8, 6, '#a8602e', { shine: true });
      shoe(ctx, hX + 35, 118, 8, 6, '#a8602e', { shine: true });
    }
  }
  // her coins land on the counter and in a little stack
  const coinsAt = [11.9, 12.5, 13.1, 13.7];
  coinsAt.forEach((c, i) => {
    if (t > c) {
      const drop = Math.max(0, 1 - (t - c) * 5);
      const y = 106 - (i % 2) * 2 - Math.floor(i / 2) * 2 - drop * 8;
      ellipse(ctx, 78 + (i % 2) * 5, y, 3, 1, '#a8802a');
      ellipse(ctx, 78 + (i % 2) * 5, y - 1, 3, 1, '#e2b84a');
      rect(ctx, 77 + (i % 2) * 5, y - 1, 1, 1, '#fff1b0');
    }
  });
  if (t > 14.2 && t < 15.2) {
    // Tom sweeps the coins into the jar
    for (let i = 0; i < 4; i++) {
      const k = clamp(seg(t, 14.2 + i * 0.1, 15 + i * 0.05));
      ellipse(ctx, lerp(78 + (i % 2) * 5, 160, k), 106 - Math.sin(k * Math.PI) * 14, 3, 1, '#e2b84a');
    }
  }
  // leather for two pairs
  if (t > 17.6) {
    const pop = ease(seg(t, 17.6, 18.2));
    ctx.globalAlpha = pop;
    leatherHide(ctx, 112, 98, 22, 9);
    leatherHide(ctx, 134, 100, 22, 8);
    ctx.globalAlpha = 1;
    if (t < 19.3) sparkle(ctx, 120 + Math.sin(t * 9) * 12, 94 - Math.abs(Math.sin(t * 7)) * 3, 1 + (Math.floor(t * 6) % 2));
  }
  vig(ctx, 0.5, 'rgba(60,34,18,0.18)');
}

// ---------- 4. Montage: night and morning, four times over ----------
const SEASON_AM = ['spring', 'summer', 'autumn', 'winter'];
function scenePanels(ctx, t) {
  const beat = Math.min(7, Math.floor(t / 3.75));
  const u = t - beat * 3.75;
  const k = Math.floor(beat / 2);
  const night = beat % 2 === 0;
  const shelves = night ? [0, 2, 4, 6][k] : [2, 4, 6, 8][k];
  const jarLevel = night ? [0.0, 0.18, 0.4, 0.7][k] : [0.18, 0.4, 0.7, 1][k];
  const [back, ctr] = shopLayers(night);
  ctx.drawImage(back, 0, 0);
  const wk = night ? (k === 3 ? 'winternight' : 'night') : SEASON_AM[k];
  windowGlass(ctx, wk, t * 1.5);
  doorLeaf(ctx, 0, 'night', t);
  clockHands(ctx, night ? 11 : 8, night ? 40 + u * 5 : 5 + u * 3);
  pendulum(ctx, t);
  shelfShoes(ctx, shelves);

  if (!night) {
    const hop = u > 1 && u < 1.7 ? -Math.round(Math.sin(((u - 1) / 0.7) * Math.PI) * 4) : 0;
    drawTom(ctx, 98, 106 + hop, { face: blinkAt(t, 14) ? 'blink' : u > 0.8 ? 'happy' : 'up', tail: Math.floor(t * 1.5) % 2, mouth: u > 1 && u < 2 && Math.floor(u * 6) % 2 ? 'meow' : null });
  }
  ctx.drawImage(ctr, 0, 0);

  jar(ctx, 156, 107, jarLevel);
  if (night) {
    candle(ctx, 58, 106, t, { h: 6 - k });
    // leather waits on the counter: k+1 hides, snipped one by one
    const n = k + 1;
    for (let i = 0; i < n; i++) {
      const appear = ease(seg(u, 0.4 + i * 0.35, 0.8 + i * 0.35));
      ctx.globalAlpha = appear;
      leatherHide(ctx, 88 + (i % 3) * 22, 98 + Math.floor(i / 3) * 3, 20, 8);
    }
    ctx.globalAlpha = 1;
    if (u > 1.4 && u < 3.1) scissors(ctx, 100 + (u - 1.4) * 14, 103, 0.5 + 0.5 * Math.sin(u * 9));
    nightWash(ctx, 0.24);
    candleGlow(ctx, t, 59, 100, 'cg-mont');
  } else {
    candle(ctx, 58, 106, t, { h: 2, lit: false });
    // new pairs appear on the counter, popping in with a gleam
    const pairs = k + 1;
    for (let i = 0; i < pairs; i++) {
      const col = SHOE_COLS[(k * 2 + i) % 8];
      const pop = ease(seg(u, 0.1 + i * 0.25, 0.5 + i * 0.25));
      if (pop <= 0) continue;
      const sy = 105;
      const x0 = 74 + i * 22 + (pairs > 3 ? -8 : 0);
      ctx.globalAlpha = pop;
      shoe(ctx, x0, sy, 9, 7, col, { shine: true });
      shoe(ctx, x0 + 10, sy, 9, 7, col, { shine: true });
      ctx.globalAlpha = 1;
      if (u < 1.6) sparkle(ctx, x0 + 5 + Math.sin(u * 8 + i) * 6, sy - 10 - (u * 4) % 3, 1 + (i % 2));
    }
    // a bundle of coins
    const c = ease(seg(u, 1.2, 1.8));
    if (c > 0) for (let i = 0; i < 3; i++) {
      ellipse(ctx, 140 + i * 5, 106 - (1 - c) * 6, 3, 1, '#a8802a');
      ellipse(ctx, 140 + i * 5, 105 - (1 - c) * 6, 3, 1, '#e2b84a');
    }
    vig(ctx, 0.5, 'rgba(60,34,18,0.18)');
  }
  vig(ctx, night ? 1 : 0);
  // a quick dark flash on each cut
  const fade = Math.max(1 - seg(u, 0, 0.3), seg(u, 3.45, 3.75));
  if (fade > 0 && t > 0.2 && t < 29.8) {
    ctx.globalAlpha = stepAlpha(fade);
    rect(ctx, 0, 0, W, H, '#170f1c');
    ctx.globalAlpha = 1;
  }
}

// ---------- 5. The watch ----------
const ELF_IDS = ['newton', 'skippy', 'simba'];
// a stage-managed drape across the stair archway, with a slit for Tom's eyes
function curtain(ctx, tomX, feet, t) {
  const gx = tomX + 6, gw = 32, gTop = feet - 40, gBot = feet - 40 + 26;
  const x0 = tomX - 8, x1 = tomX + 56;
  rect(ctx, x0 - 2, 32, x1 - x0 + 4, 3, '#4a2e1c');
  for (let x = x0; x < x1; x++) {
    const fold = Math.floor(x / 4) % 2;
    const col = fold ? '#7a2434' : '#5e1a2a';
    const inGap = x >= gx && x < gx + gw;
    // the panels hang open around Tom's head and close again below his chin
    const edge = Math.min(Math.abs(x - gx), Math.abs(x - gx - gw + 1));
    if (inGap) {
      rect(ctx, x, 35, 1, gTop - 35, col);
      rect(ctx, x, gBot, 1, 101 - gBot, col);
    } else rect(ctx, x, 35, 1, 66, col);
  }
  rect(ctx, x0, 99, x1 - x0, 2, '#3a1220');
}
function sceneWatch(ctx, t) {
  const [back, ctr] = shopLayers(true);
  ctx.drawImage(back, 0, 0);
  windowGlass(ctx, 'winternight', t);
  doorLeaf(ctx, 0, 'night', t);
  // a Christmas garland over the window and door
  for (let x = 129; x < 177; x += 3) {
    const y = 21 + Math.round(Math.sin((x - 129) / 48 * Math.PI) * 5);
    rect(ctx, x, y, 3, 3, '#2f6a3a');
    if ((x / 3) % 3 === 0) rect(ctx, x + 1, y + 1, 1, 1, '#d2483a');
  }
  const mm = t < 10 ? 46 + (t / 10) * 14 : 0;
  clockHands(ctx, t < 10 ? 11 : 12, t < 10 ? mm : 0);
  pendulum(ctx, t);
  shelfShoes(ctx, 8);

  // Tom lays out the leather, then hides behind the curtain
  const tomIn = t < 3;
  const hidingX = 192;
  if (t < 2.6) drawTom(ctx, 98, 106, { face: blinkAt(t, 3) ? 'blink' : 'side' });
  else if (t < 6) drawTom(ctx, lerp(98, hidingX, ease(seg(t, 2.6, 6))), 106, { walk: Math.floor(t * 6), flip: false });
  else {
    const peek = t > 12 ? 'up' : blinkAt(t, 5) ? 'blink' : 'side';
    drawTom(ctx, hidingX, 106, { face: peek, mouth: t > 14 && Math.floor(t * 4) % 2 ? 'meow' : null });
  }
  if (t >= 6 || true) curtain(ctx, hidingX, 106, t);
  // his candle shows in the slit
  if (t >= 6) {
    candle(ctx, hidingX + 20, 104, t, { h: 5, seed: 3 });
  }
  ctx.drawImage(ctr, 0, 0);
  jar(ctx, 156, 107, 0.7);
  candle(ctx, 58, 106, t, { h: 2, lit: false });
  cutPieces(ctx, 100, 103, 2, '#a8703a');

  // the clock strikes
  if (t > 10 && t < 12) {
    for (let i = 0; i < 4; i++) {
      const a = (t - 10) * 2;
      rect(ctx, 100 - Math.round(a * 4) - i, 28 + i * 4, 3, 1, '#e8dcb0');
      rect(ctx, 124 + Math.round(a * 4) + i, 28 + i * 4, 3, 1, '#e8dcb0');
    }
  }
  // the three elves come out of the mouse hole one by one and cross to the counter
  const ARR = [10.8, 12.4, 14.0];
  const holeGlow = seg(t, 9.8, 11);
  ELF_IDS.forEach((id, i) => {
    const a = ARR[i];
    if (t < a) return;
    const walkEnd = a + 3.4;
    const jumpAt = 17.2 + i * 0.6;
    const onX = 62 + i * 22;
    if (t < jumpAt) {
      const x = lerp(HOLE[0] - 12, 54 + i * 6, ease(seg(t, a, a + 4.6)));
      const feet = lerp(98, 116, ease(seg(t, a, a + 1.8)));
      runner(ctx, id, x, feet, t, false, 6);
    } else if (t < jumpAt + 0.8) {
      const k = seg(t, jumpAt, jumpAt + 0.8);
      const x = lerp(54 + i * 6, onX, k);
      const feet = lerp(116, 105, k) - Math.sin(k * Math.PI) * 14;
      put(ctx, cat(id, 'walk', { frame: 1, flip: false }), x, feet);
    } else {
      const work = t > 20.2;
      elf(ctx, id, onX, 105, { face: work ? 'side' : t > jumpAt + 0.9 ? 'up' : 'open', tail: Math.floor(t * 2 + i) % 2 });
    }
  });
  // tools come out at the end: tap tap tap
  if (t > 20.2) {
    const k = Math.floor(t * 5) % 2;
    pline(ctx, 82, 96 - k * 3, 86, 100 - k * 5, '#8b8f9c');
    rect(ctx, 85, 98 - k * 5, 4, 3, '#b9c0cf');
    if (k === 1) sparkle(ctx, 90, 104, 1, '#ffe08a');
    const sx = 110 + Math.sin(t * 5) * 3;
    pline(ctx, sx, 94, sx + 3, 101, '#e8edf4');
    ellipse(ctx, 132, 104, 5, 1, '#fff6d8');
  }
  nightWash(ctx, 0.22);
  candleGlow(ctx, t, hidingX + 21, 98, 'cg-watch', t > 5.5 ? 0.7 : 0);
  if (holeGlow > 0) glowAt(ctx, 'hole-glow', HOLE[0], 92, 16, 'rgba(255,230,140,0.07)', holeGlow * (0.7 + 0.3 * Math.sin(t * 6)));
  vig(ctx, 1);
}

// ---------- 6. Work: a close-up on the bench ----------
function benchBg(ctx, w, h) {
  gradient(ctx, 0, 0, W, 78, ['#2a1a26', '#3c2434', '#4c3040']);
  for (let x = 0; x < W; x += 14) rect(ctx, x, 0, 1, 78, '#241420');
  // a bench top in perspective
  gradient(ctx, 0, 78, W, 57, ['#8a5a34', '#9a6a3e', '#7a4e2c']);
  for (let y = 84; y < H; y += 7) rect(ctx, 0, y, W, 1, '#5a3820');
  for (let i = 0; i < 22; i++) {
    const y = 80 + Math.floor(hash(i + 4) * 52);
    rect(ctx, Math.floor(hash(i + 5) * W), y, 6 + Math.floor(hash(i + 6) * 12), 1, '#6a4426');
  }
  rect(ctx, 0, 77, W, 2, '#5a3820');
  rect(ctx, 0, 79, W, 1, '#c99a62');
  // tool rack on the wall: hanging awls and a mallet
  for (let i = 0; i < 5; i++) {
    rect(ctx, 20 + i * 9, 34, 1, 16 + (i % 2) * 4, '#a7b0c4');
    rect(ctx, 19 + i * 9, 50 + (i % 2) * 4, 3, 5, '#6a4426');
  }
  rect(ctx, 14, 32, 48, 2, '#3a2418');
}
function sceneWork(ctx, t) {
  const night = 1 - seg(t, 14, 24);
  ctx.drawImage(layer('bench-bg', W, H, benchBg), 0, 0);
  // a window at upper right lets in the first light
  rect(ctx, 176, 6, 52, 40, '#3a2418');
  outsideView(ctx, t < 14 ? 'winternight' : 'dawn', t, 179, 9, 46, 34, 6);
  if (t >= 14) { ctx.globalAlpha = 1 - seg(t, 14, 18) * 0; }
  rect(ctx, 201, 9, 2, 34, '#3a2418');
  rect(ctx, 179, 25, 46, 2, '#3a2418');

  candle(ctx, 128, 88, t, { h: 12, seed: 5 });
  const taps = Math.floor(t / 0.45);
  const tapPhase = (t % 0.45) / 0.45;
  const SC = 1.6;
  // ---- the left shoe is built up by Newton and Skippy
  const build = seg(t, 1.2, 10.8);
  const shoeA = { x: 50, y: 112, w: 52, h: 30 };
  shoe(ctx, shoeA.x, shoeA.y, shoeA.w, shoeA.h, '#a8602e', { prog: build, shine: build >= 1 });
  // stitches climbing as Skippy sews
  const stitches = Math.floor(build * 18);
  for (let i = 0; i < stitches; i++) rect(ctx, shoeA.x + 6 + i * 3, shoeA.y - 6 - Math.round(Math.sin(i / 18 * 2.6) * 3), 2, 1, '#f4ead2');
  // nails along the sole
  for (let i = 0; i < Math.floor(build * 12); i++) rect(ctx, shoeA.x + 4 + i * 4, shoeA.y - 3, 1, 1, '#eef1f7');
  // ---- the right shoe is polished by Simba
  const shine = seg(t, 1.6, 10.5);
  const shoeB = { x: 194, y: 114, w: 38, h: 22 };
  const bx = lerp(shoeB.x, 112, ease(seg(t, 17.5, 19.5)));
  shoe(ctx, bx, shoeB.y, shoeB.w, shoeB.h, mixHex('#8a5a30', '#e08a44', shine), { shine: shine > 0.7, flip: true });
  // Newton
  const hammerUp = tapPhase < 0.5 ? tapPhase * 2 : (1 - tapPhase) * 2;
  const nOpen = t < 11.5 || t > 18.5;
  const happy = t > 11.5 && t < 18;
  const hop = (i, base) => (happy ? -Math.abs(Math.sin((t - 11.5) * 6 + i * 1.7)) * 6 : 0) + base;
  const gone = (i) => t > 18 + i * 0.5;
  // elves scamper out left at the end
  const scamper = (i, x, feet, flip) => {
    const k = seg(t, 18 + i * 0.5, 21 + i * 0.5);
    const xx = lerp(x, -60, ease(k) * ease(k));
    runner(ctx, ELF_IDS[i], xx, feet, t, true, 14, SC);
  };
  if (!gone(0)) {
    const r = elf(ctx, 'newton', 8, hop(0, 116), { scale: SC, face: happy ? 'happy' : blinkAt(t, 7) ? 'blink' : 'side', tail: Math.floor(t * 2) % 2 });
    if (!happy) {
      // hammer
      const hx = r.x + 36, hy = r.y + 26;
      const ang = -0.9 + hammerUp * 1.1;
      const ex = hx + Math.cos(ang) * 12, ey = hy + Math.sin(ang) * 12;
      pline(ctx, hx, hy, ex, ey, '#8a5a30');
      pline(ctx, hx, hy + 1, ex, ey + 1, '#6a4426');
      rect(ctx, ex - 2, ey - 3, 6, 5, INK);
      rect(ctx, ex - 1, ey - 2, 4, 3, '#b9c0cf');
      if (tapPhase > 0.45 && tapPhase < 0.6) sparkle(ctx, shoeA.x + 8 + (taps % 6) * 6, shoeA.y - 8, 1, '#ffe08a');
    }
  } else scamper(0, 8, 116);
  // Skippy sews at the other side of shoe A (faces left)
  if (!gone(1)) {
    const r = elf(ctx, 'skippy', 106, hop(1, 116), { scale: SC, flip: true, face: happy ? 'happy' : blinkAt(t, 8) ? 'blink' : 'side', tail: Math.floor(t * 2 + 1) % 2 });
    if (!happy) {
      const sw = Math.sin(t * 5);
      const nx = shoeA.x + 34 + sw * 4, ny = shoeA.y - 14 + Math.cos(t * 5) * 2;
      pline(ctx, r.x + 6, r.y + 24, nx, ny, '#e8edf4');
      pline(ctx, nx, ny, nx - 14, ny - 6 + (build * 8), '#c9a2e8'); // thread
      rect(ctx, nx - 1, ny - 1, 3, 3, '#e8edf4');
    }
  } else scamper(1, 106, 116);
  // Simba polishes shoe B
  if (!gone(2)) {
    const r = elf(ctx, 'simba', 152, hop(2, 118), { scale: SC, face: happy ? 'happy' : blinkAt(t, 9) ? 'blink' : 'side', tail: Math.floor(t * 2 + 2) % 2 });
    if (!happy) {
      const px = shoeB.x + 12 + Math.sin(t * 7) * 8, py = shoeB.y - 14 + Math.cos(t * 3) * 1;
      ellipse(ctx, px, py, 7, 4, INK);
      ellipse(ctx, px, py, 6, 3, '#f4ead2');
      rect(ctx, px - 3, py - 1, 5, 1, '#ffffff');
      if (Math.floor(t * 7) % 3 === 0) sparkle(ctx, shoeB.x + 4 + Math.floor(hash(Math.floor(t * 7)) * 28), shoeB.y - 22 + Math.floor(hash(Math.floor(t * 7) + 3) * 6), 1);
    }
  } else scamper(2, 152, 118);
  // the pair is done
  if (t > 10.8 && t < 14) {
    const k = seg(t, 10.8, 14);
    for (let i = 0; i < 10; i++) {
      const a = i / 10 * Math.PI * 2 + t * 2;
      const rr = 10 + k * 46;
      sparkle(ctx, 124 + Math.cos(a) * rr * 1.2, 92 + Math.sin(a) * rr * 0.5, i % 3 === 0 ? 2 : 1, i % 2 ? '#fff6d8' : '#ffe08a');
    }
  }
  if (t > 11.5) {
    const g = t < 16 ? 1 : 0.5;
    if (Math.floor(t * 3) % 2) sparkle(ctx, 92, 88, 2); else sparkle(ctx, 206, 96, 2);
  }
  // morning comes up in the room as they work
  nightWash(ctx, 0.2 * night);
  candleGlow(ctx, t, 129, 78, 'cg-work', night);
  if (t > 15) { ctx.globalAlpha = seg(t, 15, 24) * 0.22; rect(ctx, 0, 0, W, H, '#ffb890'); ctx.globalAlpha = 1; }
  // Tom peeks in at the end
  if (t > 21.3) {
    const k = ease(seg(t, 21.3, 23));
    const tx = lerp(250, 196, k);
    drawTom(ctx, tx, 156, { scale: 3, face: t > 24 ? 'up' : 'side' });
    if (t > 23.2) bang(ctx, tx + 40, 58);
  }
  vig(ctx, 1);
}

// ---------- 7. Gifts: the cottage by the fire ----------
function cottageInside(ctx) {
  gradient(ctx, 0, 0, W, 100, ['#3c241e', '#55352a', '#5e3c2e']);
  for (let x = 0; x < W; x += 13) {
    rect(ctx, x, 10, 1, 90, '#3a221c');
    for (let y = 18; y < 100; y += 23) rect(ctx, x + 6, y + ((x / 13) % 2) * 9, 1, 1, '#2a1814');
  }
  rect(ctx, 0, 0, W, 10, '#2a1814');
  rect(ctx, 0, 10, W, 2, '#3a221c');
  gradient(ctx, 0, 100, W, 35, ['#7a5236', '#6a462e', '#4a2e1e']);
  for (let y = 104; y < H; y += 6) rect(ctx, 0, y, W, 1, '#4e321f');
  for (let i = 0; i < 18; i++) rect(ctx, Math.floor(hash(i + 3) * W), 100 + 6 * Math.floor(hash(i + 40) * 6), 1, 5, '#4e321f');
  rect(ctx, 14, 44, 76, 56, '#6d6670');
  for (let y = 46; y < 100; y += 5)
    for (let x = 14 + ((y / 5) % 2) * 4; x < 90; x += 8) {
      rect(ctx, x, y, 7, 4, (x + y) % 3 ? '#7d7680' : '#625b66');
      rect(ctx, x, y + 4, 8, 1, '#4e4852');
    }
  rect(ctx, 28, 60, 48, 40, '#1a1214');
  for (let i = 0; i < 6; i++) rect(ctx, 28 + i, 60 - i, 48 - i * 2, 1, '#1a1214');
  rect(ctx, 10, 40, 84, 5, '#4a2e22');
  rect(ctx, 10, 45, 84, 1, '#2a1814');
  rect(ctx, 20, 33, 3, 7, '#efe2c2');
  rect(ctx, 21, 31, 1, 2, '#ffd36a');
  rect(ctx, 74, 32, 8, 8, '#4a6a8a');
  rect(ctx, 73, 32, 10, 1, '#2f4a66');
  // a stocking hung from the mantel
  rect(ctx, 46, 40, 2, 6, '#2a1814');
  rect(ctx, 45, 46, 4, 8, '#b8453a');
  rect(ctx, 45, 52, 7, 3, '#b8453a');
  rect(ctx, 45, 46, 4, 2, '#fbf3e6');
  rect(ctx, 194, 24, 34, 36, '#2a1814');
  gradient(ctx, 196, 26, 30, 32, ['#141a3a', '#1f2a52', '#2e3a6a']);
  disc(ctx, 218, 34, 4, '#f3e9c6');
  disc(ctx, 216, 33, 3, '#141a3a');
  for (const [sx, sy] of [[200, 30], [206, 44], [222, 50], [210, 28]]) rect(ctx, sx, sy, 1, 1, '#e8e2ff');
  rect(ctx, 210, 26, 2, 32, '#2a1814');
  rect(ctx, 196, 41, 30, 2, '#2a1814');
  rect(ctx, 192, 60, 38, 3, '#4a2e22');
  ellipse(ctx, 124, 120, 50, 8, '#c9a25a');
  ellipse(ctx, 124, 120, 47, 7, '#8a3a3a');
  ellipse(ctx, 124, 120, 38, 5, '#a24a42');
  for (let x = 78; x < 172; x += 6) rect(ctx, x, 120, 3, 1, '#c9a25a');
}
function fire(ctx, t, x0, y0, w) {
  const f = Math.floor(t * 12);
  rect(ctx, x0 + 4, y0 - 3, w - 8, 3, '#3a241c');
  rect(ctx, x0 + 8, y0 - 5, w - 16, 2, '#4a2e22');
  for (let i = 0; i < 7; i++) {
    const x = x0 + 6 + (i * (w - 12)) / 6;
    const h = 7 + Math.round(hash(f * 7 + i) * 8) + (i === 3 ? 6 : 0);
    disc(ctx, x, y0 - 4 - h * 0.35, Math.round(h * 0.35), '#d9482e');
    disc(ctx, x, y0 - 4 - h * 0.45, Math.round(h * 0.25), '#ff9a3a');
    disc(ctx, x, y0 - 4 - h * 0.5, Math.round(h * 0.12), '#ffe08a');
    if (hash(f * 13 + i) > 0.7) rect(ctx, x + Math.round(hash(f + i) * 4 - 2), y0 - 6 - h - Math.round(hash(f * 3 + i) * 6), 1, 1, '#ffd36a');
  }
}
function table(ctx, x, y, w) {
  rect(ctx, x, y, w, 5, '#4a2e1c');
  rect(ctx, x, y, w, 1, '#a67443');
  rect(ctx, x + 1, y + 1, w - 2, 3, '#7a5230');
  rect(ctx, x + 3, y + 5, 3, 22, '#4a2e1c');
  rect(ctx, x + w - 6, y + 5, 3, 22, '#4a2e1c');
}
function sceneGifts(ctx, t) {
  ctx.drawImage(layer('cottage-in', W, H, cottageInside), 0, 0);
  fire(ctx, t, 30, 100, 44);
  // the work table at right
  const TX = 140, TY = 96;
  table(ctx, TX, TY, 78);
  // cloth, thread and scissors on the table
  const set = [['newton', 0], ['skippy', 1], ['simba', 2]];
  const sew = (i) => 3 + i * 3.2;          // coat i finished
  const hatDone = (i) => 12.6 + i * 1.1;     // hat i finished
  // Tom by the fire
  const sitting = t < 13;
  const tx = 92;
  let face = 'side';
  if (t > 13) face = 'happy';
  if (blinkAt(t, 21)) face = 'blink';
  drawTom(ctx, tx, 116, { face, tail: Math.floor(t * 0.9) % 2, mouth: t > 0.5 && t < 1.8 && Math.floor(t * 5) % 2 ? 'meow' : null });
  // the cloth he is working on, in front of his belly
  if (t < 12.4) {
    const i = t < 6.2 ? 0 : t < 9.4 ? 1 : 2;
    const [id] = set[i];
    const k = t < 12.4 ? 1 : 0;
    if (t > 1.4) {
      const prog = i === 0 ? seg(t, 1.4, 6.2) : i === 1 ? seg(t, 6.2, 9.4) : seg(t, 9.4, 12.4);
      const col = COATS[id];
      const x = tx + 17, y = 112;
      ctx.globalAlpha = 1;
      rect(ctx, x, y - 8, 12, 8, INK);
      rect(ctx, x + 1, y - 7, 10, 6, col[0]);
      rect(ctx, x + 1, y - 2, 10, 1, col[1]);
      // the needle goes in and out, a thread trailing
      const nx = x + 1 + prog * 9;
      const up = Math.floor(t * 6) % 2;
      pline(ctx, nx, y - 9 + up * 5, nx + 3, y - 4 + up * 5, '#e8edf4');
      pline(ctx, nx + 3, y - 4 + up * 5, nx + 8, y - 1, '#f4ead2');
    }
  }
  // snips of the scissors at the start
  if (t < 3.4 && t > 0.2) scissors(ctx, tx + 24, 108, 0.5 + 0.5 * Math.sin(t * 8));
  // finished coats and hats on the table, one by one
  set.forEach(([id], i) => {
    const [col, dk] = COATS[id];
    const cx = TX + 8 + i * 22;
    const cs = ease(seg(t, sew(i) + 2.6, sew(i) + 3.2));
    if (t >= sew(i) + 2.8) {
      ctx.globalAlpha = cs;
      drawCoat(ctx, cx - 1, TY - 10 - (1 - cs) * 8, col, dk);
      ctx.globalAlpha = 1;
      if (t < sew(i) + 4.4) sparkle(ctx, cx + 5 + Math.sin(t * 8) * 4, TY - 14 - (t * 4) % 3, 1 + (i % 2));
    }
    if (t >= hatDone(i)) {
      const hs = ease(seg(t, hatDone(i), hatDone(i) + 0.6));
      ctx.globalAlpha = hs;
      put(ctx, HAT(col, dk), cx + 1, TY - 10 - (1 - hs) * 8, 1);
      ctx.globalAlpha = 1;
      if (t < hatDone(i) + 1.4) sparkle(ctx, cx + 7, TY - 22 - (t * 5) % 3, 1);
    }
  });
  // at the very end Tom admires his work
  if (t > 16.5) {
    const k = Math.floor(t * 3) % 3;
    heart(ctx, 134 + k * 2, 70 - ((t * 5) % 6), '#ff8fb1');
  }
  // the fire's light, then the dark corners
  ctx.globalAlpha = 0.75 + 0.25 * Math.sin(t * 9) * Math.sin(t * 5.3);
  ctx.drawImage(layer('fireglow', W, H, (c, w, h) => glowLayer(c, w, h, 52, 92, 140, 'rgba(255,170,90,0.07)')), 0, 0);
  ctx.globalAlpha = 1;
  vig(ctx, 1);
}
function heart(ctx, x, y, col = '#ff8fb1') {
  x = Math.round(x); y = Math.round(y);
  rect(ctx, x, y, 2, 1, col); rect(ctx, x + 3, y, 2, 1, col);
  rect(ctx, x - 1, y + 1, 7, 2, col); rect(ctx, x, y + 3, 5, 1, col); rect(ctx, x + 1, y + 4, 3, 1, col); rect(ctx, x + 2, y + 5, 1, 1, col);
}

// ---------- 8. The dance ----------
function note(ctx, x, y, col) {
  x = Math.round(x); y = Math.round(y);
  rect(ctx, x, y + 4, 3, 2, col);
  rect(ctx, x + 2, y, 1, 5, col);
  rect(ctx, x + 3, y, 2, 1, col);
}
function sceneDance(ctx, t) {
  const [back, ctr] = shopLayers(true);
  ctx.drawImage(back, 0, 0);
  windowGlass(ctx, 'winternight', t);
  // the door opens for the elves to leave
  const open = ease(seg(t, 13.6, 14.6)) * (1 - ease(seg(t, 21.2, 22)));
  doorLeaf(ctx, open, 'night', t, t > 13.8 && t < 15.4 ? t - 13.8 : 0);
  clockHands(ctx, 12, 5);
  pendulum(ctx, t);
  shelfShoes(ctx, 8);
  for (let x = 129; x < 177; x += 3) {
    const y = 21 + Math.round(Math.sin((x - 129) / 48 * Math.PI) * 5);
    rect(ctx, x, y, 3, 3, '#2f6a3a');
    if ((x / 3) % 3 === 0) rect(ctx, x + 1, y + 1, 1, 1, '#d2483a');
  }
  // Tom: peeks from the curtain, then comes out to wave goodbye
  const hidingX = 192;
  if (t < 16) {
    drawTom(ctx, hidingX, 106, { face: t > 5 && t < 9 ? 'happy' : blinkAt(t, 6) ? 'blink' : 'side', mouth: null });
    curtain(ctx, hidingX, 106, t);
    candle(ctx, hidingX + 20, 104, t, { h: 5, seed: 3 });
  } else {
    const k = ease(seg(t, 16, 20));
    const tx = lerp(hidingX, 120, k);
    if (k < 1 && t < 19.5) drawTom(ctx, tx, 106, { walk: Math.floor(t * 6), flip: true });
    else drawTom(ctx, 120, 106, { face: blinkAt(t, 10) ? 'blink' : 'happy', tail: Math.floor(t * 2) % 2, flip: true });
  }
  ctx.drawImage(ctr, 0, 0);
  jar(ctx, 156, 107, 1);
  candle(ctx, 58, 106, t, { h: 2, lit: false });

  // the clothes on the counter, until they are put on
  set3: for (let i = 0; i < 3; i++) {
    const wearAt = 5 + i * 0.5;
    if (t >= wearAt) continue set3;
    const [col, dk] = COATS[ELF_IDS[i]];
    drawCoat(ctx, 72 + i * 24, 96, col, dk);
    put(ctx, HAT(col, dk), 77 + i * 24 + 3, 96, 1);
    if (t < 4.5) sparkle(ctx, 78 + i * 24 + Math.sin(t * 6 + i) * 5, 90 - (t * 3) % 3, 1);
  }

  // the elves
  ELF_IDS.forEach((id, i) => {
    const onX = 74 + i * 24;
    const wear = t >= 5 + i * 0.5;
    const draw = (x, feet, o = {}, sc = 1) => (wear ? dressed(ctx, id, x, feet, { ...o }) : elf(ctx, id, x, feet, { ...o, scale: sc }));
    const a = 0.6 + i * 1.0; // arrival from the hole
    if (t < a) return;
    if (t < 3 + i * 0.3) {
      const k = seg(t, a, 3 + i * 0.3);
      const x = lerp(HOLE[0] - 12, 54 + i * 4, ease(k));
      runner(ctx, id, x, lerp(98, 116, ease(seg(t, a, a + 1.4))), t, false, 8);
    } else if (t < 3.8 + i * 0.3) {
      const k = seg(t, 3 + i * 0.3, 3.8 + i * 0.3);
      put(ctx, cat(id, 'walk', { frame: 1 }), lerp(54 + i * 4, onX, k), lerp(116, 105, k) - Math.sin(k * Math.PI) * 14);
    } else if (t < 12) {
      // admiring, putting on, dancing on the counter
      if (!wear) {
        draw(onX, 105, { face: t > 4 + i * 0.4 ? 'up' : 'happy', tail: Math.floor(t * 3 + i) % 2 });
      } else {
        const beat = (t - 6) * 3.4 + i * 0.8;
        const dancing = t > 6.2;
        const hopY = dancing ? Math.abs(Math.sin(beat * Math.PI * 0.5)) * 7 : 0;
        const flip = dancing && Math.floor(beat / 2) % 2 === 1;
        const sway = dancing ? Math.round(Math.sin(beat * 0.9) * 4) : 0;
        draw(onX + sway, 105 - hopY, { face: 'happy', tail: Math.floor(t * 4 + i) % 2, flip });
        if (t > 5 + i * 0.5 && t < 6 + i * 0.5) {
          for (let s = 0; s < 4; s++) sparkle(ctx, onX + 9 + Math.cos(s * 1.6 + t * 8) * 12, 92 + Math.sin(s * 1.6 + t * 8) * 8, 1);
        }
      }
    } else if (t < 13) {
      const beat = (t - 6) * 3.4 + i * 0.8;
      draw(onX, 105 - Math.abs(Math.sin(beat * Math.PI * 0.5)) * 6, { face: 'happy', flip: i % 2 === 0 });
    } else {
      // skip along the counter, down to the floor and out of the door
      const lead = 13 + i * 0.9;
      const k = seg(t, lead, lead + 5.4);
      const px = lerp(onX, 10, ease(k));
      let feet = 105, sc = 1;
      if (k < 0.2) feet = 105;
      else feet = lerp(105, 117, ease(seg(k, 0.2, 0.3)));
      if (k > 0.3) feet = lerp(117, 98, ease(seg(k, 0.3, 0.85)));
      const hopS = Math.abs(Math.sin(k * 24)) * 5 * (k < 0.85 ? 1 : 0.4);
      if (k < 0.85) draw(px, feet - hopS, { face: 'happy', flip: true, tail: Math.floor(t * 4) % 2 });
      else {
        // out into the snow, growing smaller as they go
        const o = seg(k, 0.85, 1);
        const fx = lerp(px, 11, o);
        const sy = lerp(98, 74, o);
        ctx.save();
        ctx.beginPath(); ctx.rect(DOOR[0], DOOR[1], DOOR[2], DOOR[3]); ctx.clip();
        const s2 = lerp(1, 0.5, o);
        const eimg = cat(id, 'sit', { face: 'happy', flip: true });
        put(ctx, eimg, fx, sy - Math.abs(Math.sin(t * 12)) * 2, s2);
        ctx.restore();
      }
      if (k < 0.2 && t > lead) sparkle(ctx, px + 12, 94, 1);
    }
  });
  // music floats up from the dance
  if (t > 6.2 && t < 13.2) {
    for (let i = 0; i < 5; i++) {
      const a = (t * 0.55 + i / 5) % 1;
      ctx.globalAlpha = Math.min(1, (1 - a) * 1.6);
      note(ctx, 70 + i * 17 + Math.sin(a * 6 + i) * 4, 92 - a * 36, ['#ffe08a', '#ff8fb1', '#9ad8ff', '#b8f0a0', '#e2b8ff'][i]);
    }
    ctx.globalAlpha = 1;
  }
  // the room gets warmer as they dance
  nightWash(ctx, 0.2 - seg(t, 5, 8) * 0.08);
  candleGlow(ctx, t, 100, 100, 'cg-dance', seg(t, 4, 8) * 0.8);
  vig(ctx, 1);

  // The End
  const k = stepAlpha(seg(t, 21.8, 23.2));
  if (k > 0) {
    ctx.globalAlpha = k;
    rect(ctx, 0, 0, W, H, '#170f1c');
    ctx.globalAlpha = stepAlpha(seg(t, 23.2, 24.6));
    words(ctx, 'The End', W / 2, H / 2 - 4, 22, '#f2e2b6');
    ctx.globalAlpha = 1;
  }
}

// ---------- the running order ----------
export const SCENES = [
  { id: 'title', name: 'A snowy night', dur: 10, draw: sceneTitle,
    captions: [[3, 10, 'This is the story of a poor old shoemaker, and three very small helpers.']] },
  { id: 'poor', name: 'The last of the leather', dur: 25, draw: scenePoor,
    captions: [
      [0, 10.5, 'Once there was a shoemaker named Tom, who had grown so poor that he had leather for only one more pair of shoes.'],
      [10.5, 18, 'He cut out the leather, left it on his bench, and went sadly up to bed.'],
    ] },
  { id: 'morning', name: 'A pair of shoes', dur: 20, draw: sceneMorning,
    captions: [
      [0, 9.5, 'In the morning, there on the bench stood a pair of shoes, so finely made that not one stitch was wrong.'],
      [9.5, 20, 'A customer paid so much for them that Tom could buy leather for two pairs.'],
    ] },
  { id: 'montage', name: 'Night and morning', dur: 30, draw: scenePanels,
    captions: [
      [0, 15, 'Every night he left the leather out, and every morning the shoes were finished.'],
      [15, 30, 'Soon his shelves were full, and Tom was poor no longer.'],
    ] },
  { id: 'watch', name: 'Christmas Eve', dur: 25, draw: sceneWatch,
    captions: [
      [0, 10, 'One night, just before Christmas, Tom hid behind the curtain to see who his helpers were.'],
      [10, 25, 'At midnight, three tiny cats crept out of the mouse hole and climbed onto his bench.'],
    ] },
  { id: 'work', name: 'The little helpers', dur: 25, draw: sceneWork,
    captions: [
      [0, 12, 'They stitched and hammered and polished so quickly that Tom could hardly follow their paws.'],
      [12, 25, 'When the shoes were done, they scampered off before the sun came up.'],
    ] },
  { id: 'gifts', name: 'Little coats', dur: 20, draw: sceneGifts,
    captions: [
      [0, 12, '“They have made me rich,” said Tom, “and they have nothing to wear.”'],
      [12, 20, 'So he sewed three little coats and three little hats.'],
    ] },
  { id: 'dance', name: 'The elves dance', dur: 25, draw: sceneDance,
    captions: [
      [0, 12, 'That night the elves found their new clothes, and they put them on and danced for joy.'],
      [12, 25, 'Then they skipped out into the snow, and Tom never needed their help again.'],
    ] },
];
let acc = 0;
for (const s of SCENES) { s.start = acc; acc += s.dur; }
export const TOTAL = acc;
