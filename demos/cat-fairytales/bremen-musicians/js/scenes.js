// The Bremen Town Musicians. Shared helpers come from The Three Brothers (same series); its scene
// functions are left in place but unused.
// The ten scenes of The Three Brothers. Each scene draws itself from its local time t (seconds),
// so the film can be paused and scrubbed anywhere.
import { cat, put, horse, hare, HAMMER, RAZOR, BRUSH, SWORD, SHOE, SPECTACLES, NIGHTCAP, SCISSORS } from './art.js';
import {
  W, H, hash, bayer, rect, disc, ellipse, pline, layer, gradient, hills, cloud, tree,
  lerp, clamp, ease, seg, travel, mixHex,
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

// Old Tom: a grey cat with spectacles and a striped nightcap.
function drawTom(ctx, x, feet, o = {}) {
  const img = cat('tom', 'sit', { face: o.face ?? 'open', mouth: o.mouth ?? null, tail: o.tail ?? 0, flip: !!o.flip });
  const r = put(ctx, img, x, feet);
  const sx = o.flip ? x + 22 - 18 : x; // the 18-wide body sits at the left of the 22-wide sprite
  if (o.face !== 'blink') put(ctx, SPECTACLES(), sx + 4.5, r.y + 9.5);
  put(ctx, NIGHTCAP(), sx + 3, r.y + 4.5);
  return r;
}

// A son speaking or reacting: returns the sprite rectangle.
function son(ctx, id, x, feet, o = {}) {
  return put(ctx, cat(id, 'sit', o), x, feet);
}

function runner(ctx, id, x, feet, t, flip = false, rate = 16) {
  const f = Math.floor(t * rate) % 4;
  const bob = f % 2 ? -1 : 0;
  return put(ctx, cat(id, 'walk', { frame: f, flip }), x, feet + bob);
}

function dust(ctx, x, feet, t, seed) {
  for (let i = 0; i < 4; i++) {
    const age = (t * 3 + i / 4 + hash(seed + i)) % 1;
    const r = Math.round(1 + age * 3);
    ctx.globalAlpha = 0.55 * (1 - age);
    disc(ctx, x - age * 14 - i * 3, feet - 1 - age * 3, r, '#e8dcc0');
  }
  ctx.globalAlpha = 1;
}

// The front of the family cottage (used outdoors).
function cottage(ctx, x, ground, o = {}) {
  const wall = '#dcc9a2', wallD = '#b9a37c', thatch = '#b8914e', thatchD = '#8a6a34';
  rect(ctx, x, ground - 38, 70, 38, wall);
  for (let i = 0; i < 70; i += 7) rect(ctx, x + i, ground - 38, 1, 38, wallD);
  // timber frame
  rect(ctx, x, ground - 38, 70, 2, '#6a4426');
  rect(ctx, x, ground - 20, 70, 2, '#6a4426');
  rect(ctx, x, ground - 38, 2, 38, '#6a4426');
  rect(ctx, x + 68, ground - 38, 2, 38, '#6a4426');
  // thatched roof
  for (let i = 0; i < 26; i++) rect(ctx, x - 6 + i, ground - 38 - i, 82 - i * 2, 1, i % 3 ? thatch : thatchD);
  rect(ctx, x - 6, ground - 38, 82, 2, thatchD);
  // chimney
  rect(ctx, x + 50, ground - 66, 9, 18, '#7a6a66');
  rect(ctx, x + 49, ground - 67, 11, 2, '#5a4e4c');
  // door + window
  rect(ctx, x + 40, ground - 26, 14, 26, '#5a3424');
  rect(ctx, x + 41, ground - 25, 12, 25, o.doorLit ? '#f2c36a' : '#3a2418');
  rect(ctx, x + 12, ground - 33, 14, 10, '#6a4426');
  rect(ctx, x + 13, ground - 32, 12, 8, o.night ? '#f2c36a' : '#9fc3d8');
  rect(ctx, x + 18, ground - 32, 1, 8, '#6a4426');
  // step
  rect(ctx, x + 38, ground - 1, 18, 2, '#8a7a70');
}

// ---------- 1. Title ----------
const PLACE = (title) => (ctx, t) => {
  rect(ctx, 0, 0, W, H, '#1d1424');
  ctx.fillStyle = '#e9d9b4';
  ctx.font = '10px "Pixelify Sans", monospace';
  ctx.textAlign = 'center';
  ctx.fillText(title, W / 2, H / 2);
  ctx.fillStyle = '#8a7a9a';
  ctx.font = '7px "Pixelify Sans", monospace';
  ctx.fillText('scene still to be animated', W / 2, H / 2 + 12);
};

// ---------- 2. The cottage ----------
function cottageInside(ctx) {
  // walls: warm planks
  gradient(ctx, 0, 0, W, 100, ['#3c241e', '#55352a', '#5e3c2e']);
  for (let x = 0; x < W; x += 13) {
    rect(ctx, x, 10, 1, 90, '#3a221c');
    for (let y = 18; y < 100; y += 23) rect(ctx, x + 6, y + ((x / 13) % 2) * 9, 1, 1, '#2a1814');
  }
  rect(ctx, 0, 0, W, 10, '#2a1814');
  rect(ctx, 0, 10, W, 2, '#3a221c');
  // floorboards
  gradient(ctx, 0, 100, W, 35, ['#7a5236', '#6a462e', '#4a2e1e']);
  for (let y = 104; y < H; y += 6) rect(ctx, 0, y, W, 1, '#4e321f');
  for (let i = 0; i < 18; i++) rect(ctx, Math.floor(hash(i + 3) * W), 100 + 6 * Math.floor(hash(i + 40) * 6), 1, 5, '#4e321f');
  // fireplace: stone arch
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
  // mantel things: candle, jug
  rect(ctx, 20, 33, 3, 7, '#efe2c2');
  rect(ctx, 21, 31, 1, 2, '#ffd36a');
  rect(ctx, 74, 32, 8, 8, '#4a6a8a');
  rect(ctx, 73, 32, 10, 1, '#2f4a66');
  // window with moon
  rect(ctx, 194, 24, 34, 36, '#2a1814');
  gradient(ctx, 196, 26, 30, 32, ['#141a3a', '#1f2a52', '#2e3a6a']);
  disc(ctx, 218, 34, 4, '#f3e9c6');
  disc(ctx, 216, 33, 3, '#141a3a');
  for (const [sx, sy] of [[200, 30], [206, 44], [222, 50], [210, 28]]) rect(ctx, sx, sy, 1, 1, '#e8e2ff');
  rect(ctx, 210, 26, 2, 32, '#2a1814');
  rect(ctx, 196, 41, 30, 2, '#2a1814');
  rect(ctx, 192, 60, 38, 3, '#4a2e22');
  // clock
  rect(ctx, 126, 14, 16, 34, '#4a2e22');
  rect(ctx, 127, 15, 14, 32, '#3a221c');
  disc(ctx, 134, 22, 5, '#e9dcb8');
  rect(ctx, 134, 18, 1, 4, INK);
  rect(ctx, 134, 22, 3, 1, INK);
  rect(ctx, 129, 30, 10, 15, '#24140f');
  // rug
  ellipse(ctx, 164, 118, 56, 9, '#c9a25a');
  ellipse(ctx, 164, 118, 53, 8, '#8a3a3a');
  ellipse(ctx, 164, 118, 44, 6, '#a24a42');
  for (let x = 116; x < 212; x += 6) rect(ctx, x, 118, 3, 1, '#c9a25a');
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

function rockingChair(ctx, x, feet, rock) {
  const c = '#5a3424', d = '#3a2016';
  rect(ctx, x + 1, feet - 34, 2, 34, c);
  rect(ctx, x + 21, feet - 34, 2, 34, c);
  rect(ctx, x + 1, feet - 35, 22, 2, d);
  for (let i = 0; i < 4; i++) rect(ctx, x + 5 + i * 4, feet - 33, 2, 16, c);
  rect(ctx, x - 1, feet - 12, 26, 2, c);
  // rockers: a shallow arc
  for (let i = -4; i < 30; i++) {
    const y = feet + 1 + Math.round(((i - 12) / 16) ** 2 * 3 - rock * (i - 12) * 0.12);
    rect(ctx, x + i, y, 1, 2, d);
  }
}

function sceneCottage(ctx, t) {
  ctx.drawImage(layer('cottage-in', W, H, cottageInside), 0, 0);
  // pendulum
  const sw = Math.sin(t * Math.PI) * 3;
  pline(ctx, 134, 31, 134 + sw, 41, '#c9a25a');
  disc(ctx, 134 + sw, 42, 1, '#e2b84a');
  fire(ctx, t, 30, 100, 44);
  // Old Tom in his rocking chair
  const rock = Math.sin(t * 1.6);
  const talking = (t > 15 && t < 24) || (t > 1 && t < 3);
  rockingChair(ctx, 95 + rock * 0.6, 116, rock);
  drawTom(ctx, 96 + rock * 0.6, 116 + (rock > 0.3 ? -0.5 : 0), {
    face: blinkAt(t, 1) ? 'blink' : t > 15 ? 'side' : 'happy',
    mouth: talking && Math.floor(t * 5) % 2 ? 'meow' : null,
  });
  // the three sons, each hopping when named
  const kids = [['newton', 140, 9.6], ['skippy', 163, 10.6], ['simba', 186, 11.6]];
  kids.forEach(([id, x, named], i) => {
    const hop = t > named && t < named + 0.5 ? -Math.round(Math.sin(((t - named) / 0.5) * Math.PI) * 4) : 0;
    const face = blinkAt(t, i + 5) ? 'blink' : t > named && t < named + 1.4 ? 'happy' : t > 15 ? 'up' : 'side';
    son(ctx, id, x, 117 + hop, { face, tail: Math.floor(t * 1.5 + i) % 2, flip: true });
  });
  // the fire's light, then the dark corners of the room
  ctx.globalAlpha = 0.75 + 0.25 * Math.sin(t * 9) * Math.sin(t * 5.3);
  ctx.drawImage(layer('fireglow', W, H, (c, w, h) => glowLayer(c, w, h, 52, 92, 140, 'rgba(255,170,90,0.07)')), 0, 0);
  ctx.globalAlpha = 1;
  ctx.drawImage(layer('vig-night', W, H, (c, w, h) => vignette(c, w, h, 'rgba(14,8,18,0.22)')), 0, 0);
}

// ---------- 6. Skippy and the hare ----------
function meadowSky(ctx, w, h) {
  gradient(ctx, 0, 0, w, 80, ['#7fb7e0', '#a6d0ec', '#d2e8ef', '#eef4e4']);
}
function meadowFar(ctx, w, h) {
  hills(ctx, w, 66, 6, [[2, 1], [5, 0.4]], '#9ec384', '#b6d49a', 2);
  for (let i = 0; i < 10; i++) {
    const x = Math.floor(hash(i + 90) * w);
    tree(ctx, x, 70 + Math.floor(hash(i + 91) * 6), 1, { trunk: '#6a5a44', dark: '#6f9a5a', mid: '#82ad68', light: '#9cc47e' });
  }
}
function meadowNear(ctx, w, h) {
  hills(ctx, w, 86, 5, [[3, 1], [7, 0.3]], '#79ad5a', '#94c470', 5);
}
function meadowGround(ctx, w, h) {
  gradient(ctx, 0, 0, w, h, ['#6aa64c', '#5d9a45', '#4f8a3c']);
  // a trodden path
  for (let x = 0; x < w; x++) {
    const y = 15 + Math.round(Math.sin((x / w) * Math.PI * 4) * 1.5);
    rect(ctx, x, y, 1, 7, bayer(x, y) < 0.5 ? '#b89a6a' : '#a88a5c');
  }
  for (let i = 0; i < 120; i++) {
    const x = Math.floor(hash(i + 7) * w), y = Math.floor(hash(i + 8) * h);
    if (y > 13 && y < 23) continue;
    rect(ctx, x, y, 1, 2, '#3f7a30');
    rect(ctx, x + 1, y - 1, 1, 2, '#3f7a30');
    if (hash(i + 9) > 0.8) rect(ctx, x, y - 2, 1, 1, ['#f4f0e0', '#f2d24a', '#e88aa0'][i % 3]);
  }
}
function tile(ctx, img, off, y) {
  const w = img.width;
  let x = -(((off % w) + w) % w);
  for (; x < W; x += w) ctx.drawImage(img, Math.round(x), y);
}

function sceneSkippy(ctx, t) {
  const s = travel(t, 64, 8, 10.5, 21.5, 25);
  tile(ctx, layer('m-sky', W, 80, meadowSky), 0, 0);
  ctx.globalAlpha = 0.95;
  [[30, 18, 1], [140, 10, 1.3], [210, 26, 0.9]].forEach(([x, y, k], i) => {
    const cx = ((x - s * 0.05 - t * 1.5 + 400) % 300) - 30;
    cloud(ctx, cx, y, k, '#fbfdff', '#d8e6f0');
  });
  ctx.globalAlpha = 1;
  tile(ctx, layer('m-far', 480, 135, meadowFar), s * 0.2, 0);
  tile(ctx, layer('m-near', 480, 135, meadowNear), s * 0.45, 0);
  tile(ctx, layer('m-ground', 480, 37, meadowGround), s, 98);
  const ground = 116;

  // the family at the cottage door, left behind once the chase starts
  const hx = 8 - s;
  if (hx > -90) {
    cottage(ctx, hx - 22, 104);
    drawTom(ctx, hx + 2, 110, { face: blinkAt(t, 2) ? 'blink' : 'side' });
    son(ctx, 'newton', hx + 26, 112, { face: t > 8 ? 'up' : 'side', tail: 1 });
    son(ctx, 'simba', hx + 48, 112, { face: 'side', tail: 0 });
  }

  // the hare
  let hX, hF, hY = 114, beard = true, tache = false;
  if (t < 1.5) hX = 300;
  else if (t < 4.5) { hX = lerp(260, 176, ease(seg(t, 1.5, 4.5))); hF = Math.floor(t * 8) % 2; }
  else if (t < 8) { hX = 176; hF = 2; }
  else if (t < 24.5) { hX = 176 + Math.sin(t * 1.3) * 8; hF = Math.floor(t * 10) % 2; }
  else { hX = 176 + Math.sin(24.5 * 1.3) * 8; hF = 2; }
  if (t > 21) { beard = false; tache = true; }
  if (hF !== 2 && hF === 0) hY -= 3;

  // Skippy
  const lath = clamp(seg(t, 12, 15)) * (1 - seg(t, 16, 21.5));
  let sk;
  if (t < 8.6) {
    sk = son(ctx, 'skippy', 92, ground + 1, {
      face: t > 5 ? 'up' : blinkAt(t, 3) ? 'blink' : 'side', paw: t > 5.5 ? Math.floor(t * 3) % 2 : null, tail: Math.floor(t) % 2,
    });
    if (t > 5.5) put(ctx, BRUSH(), sk.x + 0.5, sk.y + 6 - (Math.floor(t * 3) % 2) * 2);
  } else if (t < 25) {
    const x = lerp(92, hX - 14, ease(seg(t, 8.6, 11.5)));
    if (hF !== undefined && hX < 300) put(ctx, hare(hF, { beard, tache }), hX, hY);
    sk = runner(ctx, 'skippy', x, ground + 3, t, false, 15);
    dust(ctx, x + 4, ground + 3, t, 11);
    // the tools at the hare's cheek
    const fx = hX + 23, fy = hY - 13;
    if (t > 11.5 && t < 16) put(ctx, BRUSH(), fx - 2 + Math.sin(t * 22) * 1.5, fy + 9);
    if (t > 16 && t < 21.8) {
      const stroke = (t * 3) % 1;
      put(ctx, RAZOR(), fx - 6 + stroke * 4, fy + 4 + stroke * 3);
      if (stroke < 0.15) sparkle(ctx, fx + 4, fy + 1, 2);
      for (let i = 0; i < 5; i++) {
        const a = (t * 2 + i / 5) % 1;
        rect(ctx, fx - a * 30, fy + 6 + a * 8 + i, 1, 1, '#6e5640');
      }
    }
    if (lath > 0) {
      const r = Math.round(1 + lath * 2.5);
      disc(ctx, fx + 1, fy + 8, r, '#ffffff');
      disc(ctx, fx - 1, fy + 9, Math.max(1, r - 1), '#f3f6fb');
      if (lath > 0.5) disc(ctx, fx + 3, fy + 6, 1, '#ffffff');
    }
  }
  if (t >= 25) {
    put(ctx, hare(2, { tache: true }), hX, 114);
    sk = son(ctx, 'skippy', hX - 26, ground + 2, { face: 'happy', paw: 0, tail: 1 });
    put(ctx, RAZOR(), sk.x - 1, sk.y + 3);
    const p = (t - 25) * 2;
    for (let i = 0; i < 3; i++) if (Math.floor(p + i * 0.6) % 2) sparkle(ctx, hX + 16 + i * 5, 100 - i * 4, 1 + (i % 2));
  }
}

// ---------- 7. Newton and the coach ----------
function roadSky(ctx, w, h) {
  gradient(ctx, 0, 0, w, 90, ['#f0b46e', '#f3c886', '#f6dca6', '#f8ead0']);
  disc(ctx, 60, 48, 12, '#fff2c8');
  disc(ctx, 60, 48, 10, '#fff8e2');
}
function roadFar(ctx, w, h) {
  hills(ctx, w, 72, 7, [[2, 1], [4, 0.5]], '#c9a86a', '#dcbe82', 3);
  hills(ctx, w, 84, 4, [[3, 1], [9, 0.3]], '#a8945a', '#bca86c', 8);
  for (let i = 0; i < 9; i++) tree(ctx, Math.floor(hash(i + 300) * w), 86, 1, { trunk: '#5a4434', dark: '#7a7a3e', mid: '#8e8e48', light: '#a8a45a' });
}
function roadGround(ctx, w, h) {
  gradient(ctx, 0, 0, w, 10, ['#8a9a4c', '#7a8c44']);
  gradient(ctx, 0, 10, w, 24, ['#c2a072', '#b08a5e', '#9a7650']);
  for (let x = 0; x < w; x++) {
    if (bayer(x, 0) < 0.5) rect(ctx, x, 18, 1, 1, '#8a6a46');
    if (bayer(x, 3) < 0.5) rect(ctx, x, 27, 1, 1, '#8a6a46');
  }
  for (let i = 0; i < 40; i++) rect(ctx, Math.floor(hash(i + 500) * w), 12 + Math.floor(hash(i + 501) * 20), 1, 1, '#d8bc8e');
  gradient(ctx, 0, 34, w, 6, ['#7a8c44', '#6a7a3a']);
}
function fence(ctx, off) {
  for (let i = -1; i < 10; i++) {
    const x = Math.round(i * 30 - (((off % 30) + 30) % 30));
    rect(ctx, x, 84, 3, 22, '#6a4a30');
    rect(ctx, x, 84, 3, 1, '#8a6a46');
  }
  rect(ctx, 0, 89, W, 2, '#7a5a3a');
  rect(ctx, 0, 97, W, 2, '#7a5a3a');
}
function coach(ctx, x, ground, t, moving) {
  const body = '#2f5a4a', trim = '#e2b84a';
  rect(ctx, x + 6, ground - 40, 40, 26, INK);
  rect(ctx, x + 7, ground - 39, 38, 24, body);
  rect(ctx, x + 7, ground - 39, 38, 2, trim);
  rect(ctx, x + 7, ground - 17, 38, 2, trim);
  rect(ctx, x + 14, ground - 34, 12, 10, '#f3dc9a');
  rect(ctx, x + 15, ground - 33, 10, 8, '#3a2a2a');
  rect(ctx, x + 30, ground - 34, 10, 16, '#24443a');
  rect(ctx, x + 4, ground - 44, 44, 4, INK);
  rect(ctx, x + 5, ground - 43, 42, 2, '#3a6a58');
  // a driver's bench and lantern
  rect(ctx, x + 44, ground - 26, 10, 2, INK);
  disc(ctx, x + 50, ground - 32, 1, '#ffd36a');
  // shafts
  pline(ctx, x + 46, ground - 18, x + 70, ground - 22, '#5a3a22');
  for (const wx of [x + 14, x + 38]) {
    disc(ctx, wx, ground - 7, 7, INK);
    disc(ctx, wx, ground - 7, 6, '#7a4a2a');
    disc(ctx, wx, ground - 7, 4, '#c9a25a');
    disc(ctx, wx, ground - 7, 3, '#7a4a2a');
    const a = moving ? t * 9 : 0;
    for (let k = 0; k < 3; k++) {
      const an = a + (k * Math.PI) / 3;
      pline(ctx, wx - Math.cos(an) * 5, ground - 7 - Math.sin(an) * 5, wx + Math.cos(an) * 5, ground - 7 + Math.sin(an) * 5, '#5a3a22');
    }
    disc(ctx, wx, ground - 7, 1, trim);
  }
}

const HITS = [13, 16, 19, 22];
function sceneNewton(ctx, t) {
  const s = travel(t, 96, 8.5, 10.5, 23, 26.5);
  tile(ctx, layer('r-sky', W, 90, roadSky), 0, 0);
  tile(ctx, layer('r-far', 480, 135, roadFar), s * 0.15, 0);
  tile(ctx, layer('r-ground', 480, 40, roadGround), s, 96);
  const ground = 122;

  // Tom and the brothers lean on the fence, left behind by the chase
  const fx = 10 - s;
  if (fx > -80) {
    drawTom(ctx, fx, 104, { face: t > 6 ? 'up' : 'side' });
    son(ctx, 'skippy', fx + 24, 104, { face: 'side', tail: 1 });
    son(ctx, 'simba', fx + 46, 104, { face: blinkAt(t, 9) ? 'blink' : 'side' });
  }
  fence(ctx, s * 1.0 + 12);

  // horse: enters from the left, then runs with the camera, then leaves to the right
  let hx;
  if (t < 9) hx = lerp(-150, 60, seg(t, 0, 9));
  else hx = 60 + (t - 9) * 96 - s + lerp(0, 34, ease(seg(t, 9, 11)));
  const hf = Math.floor(t * 11) % 4;
  const hitI = HITS.findIndex((h) => t > h - 1.1 && t < h + 0.3);
  if (hx > -160 && hx < W + 20) {
    coach(ctx, hx - 62, ground, t, true);
    put(ctx, horse(hf, { harness: true, lifted: hitI >= 0 ? hitI : undefined }), hx, ground);
  }

  // Newton
  let nx;
  if (t < 9) {
    const n = son(ctx, 'newton', 150, ground + 1, { face: t > 5.5 ? 'up' : 'open', tail: t > 5.5 ? 1 : 0 });
    if (t > 6.5) put(ctx, HAMMER(), n.x - 2, n.y + 8);
  } else if (t < 25) {
    nx = lerp(150, hx + 44, ease(seg(t, 9, 11.5)));
    runner(ctx, 'newton', nx, ground + 3, t, false, 18);
    dust(ctx, nx + 4, ground + 3, t, 21);
    // the hammer swings down onto the lifted hoof at each hit
    if (hitI >= 0) {
      const h = HITS[hitI];
      const k = t < h ? seg(t, h - 1.1, h) : 1;
      const swing = Math.sin(k * Math.PI * 3) ** 2;
      const img = HAMMER();
      ctx.save();
      ctx.translate(nx + 22, ground - 12);
      ctx.rotate(-1.2 + swing * 1.6);
      ctx.drawImage(img, -3, -9, img.width / 2, img.height / 2);
      ctx.restore();
      if (t > h && t < h + 0.25) for (let i = 0; i < 6; i++) sparkle(ctx, nx + 28 + hash(i + h) * 10 - 5, ground - 8 - hash(i + h * 3) * 8, i % 2 ? 1 : 2, i % 2 ? '#ffd36a' : '#fff6d8');
    }
    // old shoes fly off behind
    for (const h of HITS) {
      const a = t - (h - 0.8);
      if (a > 0 && a < 1.6) {
        const sx = nx + 20 - a * 70, sy = ground - 14 - a * 30 + a * a * 30;
        ctx.save();
        ctx.translate(sx, sy);
        ctx.rotate(a * 9);
        const img = SHOE();
        ctx.drawImage(img, -3, -2.5, img.width / 2, img.height / 2);
        ctx.restore();
      }
    }
  } else {
    const n = son(ctx, 'newton', 120, ground + 1, { face: 'happy', paw: Math.floor(t * 2) % 2, tail: 1 });
    put(ctx, HAMMER(), n.x - 1, n.y + 7 - (Math.floor(t * 2) % 2) * 2);
    for (let i = 0; i < 4; i++) if (Math.floor((t - 25) * 3 + i * 0.7) % 2) sparkle(ctx, 120 + i * 7, 92 - (i % 2) * 6, 1 + (i % 2));
  }
}

// ---------- 8. Simba and the storm ----------
function yardSky(storm) {
  return (ctx, w, h) =>
    gradient(ctx, 0, 0, w, 96, storm ? ['#2a2e44', '#3c4258', '#565c6e', '#6c7080'] : ['#8ab8dc', '#aecfe6', '#d4e6ee', '#eaf2ea']);
}
function yardFar(storm) {
  return (ctx, w, h) => {
    hills(ctx, w, 78, 6, [[2, 1], [5, 0.4]], storm ? '#4a5a4a' : '#9ec384', storm ? '#5a6a58' : '#b6d49a', 4);
    for (let i = 0; i < 7; i++) tree(ctx, 100 + Math.floor(hash(i + 700) * 140), 82, 1, storm
      ? { trunk: '#3a3430', dark: '#33463a', mid: '#3e5444', light: '#4a604e' }
      : { trunk: '#6a5a44', dark: '#6f9a5a', mid: '#82ad68', light: '#9cc47e' });
  };
}
function yardGround(storm) {
  return (ctx, w, h) => {
    gradient(ctx, 0, 0, w, h, storm ? ['#3e6a38', '#355e30', '#2c5028'] : ['#6aa64c', '#5d9a45', '#4f8a3c']);
    for (let i = 0; i < 90; i++) {
      const x = Math.floor(hash(i + 800) * w), y = Math.floor(hash(i + 801) * h);
      rect(ctx, x, y, 1, 2, storm ? '#28461f' : '#3f7a30');
      rect(ctx, x + 1, y - 1, 1, 2, storm ? '#28461f' : '#3f7a30');
    }
  };
}
const STRIKES = [18, 26.5, 31];
const PUDDLES = [[128, 126, 9], [196, 122, 7], [222, 130, 10], [108, 112, 5]];

function sceneSimba(ctx, t) {
  const dark = clamp(seg(t, 0, 10) * (1 - seg(t, 33, 39)));
  const rain = clamp(seg(t, 5, 8) * 0.3 + seg(t, 9, 15) * 0.7) * (1 - seg(t, 32.5, 35.5));
  const flash = Math.max(0, ...STRIKES.map((s) => (t > s ? Math.exp(-(t - s) * 7) : 0)));
  // sky and land cross-fade from clear to storm
  ctx.drawImage(layer('y-sky0', W, 96, yardSky(false)), 0, 0);
  ctx.globalAlpha = dark;
  ctx.drawImage(layer('y-sky1', W, 96, yardSky(true)), 0, 0);
  ctx.globalAlpha = 1;
  // storm clouds rolling in
  for (let i = 0; i < 7; i++) {
    const cx = ((i * 47 + t * (3 + (i % 3))) % 300) - 30;
    ctx.globalAlpha = dark * 0.95;
    cloud(ctx, cx, 10 + (i % 3) * 9, 1.2 + (i % 2) * 0.4, i % 2 ? '#4a4e62' : '#3c4054', '#2c3042');
  }
  ctx.globalAlpha = 1;
  // lightning bolt in the distance
  for (const s of STRIKES) {
    if (t > s && t < s + 0.18) {
      let x = 170 + hash(s * 10) * 50, y = 0;
      while (y < 78) {
        const nx = x + (hash(Math.floor(s * 100 + y)) - 0.5) * 12, ny = y + 6 + hash(y + s) * 6;
        pline(ctx, x, y, nx, ny, '#fff8e0');
        pline(ctx, x + 1, y, nx + 1, ny, '#c8d4ff');
        x = nx; y = ny;
      }
    }
  }
  ctx.drawImage(layer('y-far0', W, 135, yardFar(false)), 0, 0);
  ctx.globalAlpha = dark;
  ctx.drawImage(layer('y-far1', W, 135, yardFar(true)), 0, 0);
  ctx.globalAlpha = 1;
  ctx.drawImage(layer('y-gr0', W, 40, yardGround(false)), 0, 95);
  ctx.globalAlpha = dark;
  ctx.drawImage(layer('y-gr1', W, 40, yardGround(true)), 0, 95);
  ctx.globalAlpha = 1;
  // puddles
  for (const [px, py, r] of PUDDLES) {
    ctx.globalAlpha = clamp(rain * 1.5 + seg(t, 33, 36) * (1 - seg(t, 38, 40)) * 0.6);
    ellipse(ctx, px, py, r, 2, mixHex('#9fc3d8', '#5a6a88', dark));
    ellipse(ctx, px - 1, py - 1, Math.round(r / 2), 0, '#e8f2f8');
    ctx.globalAlpha = 1;
  }

  // the cottage with its porch, where the others shelter
  cottage(ctx, -10, 108, { doorLit: dark > 0.5 });
  rect(ctx, -2, 64, 100, 4, '#6a4426');
  for (let i = 0; i < 6; i++) rect(ctx, -2 + i, 60 + i, 100 - i, 1, '#8a6a34');
  rect(ctx, 94, 66, 2, 42, '#6a4426');
  rect(ctx, -2, 108, 100, 3, '#7a5a3a');
  const flinch = flash > 0.3;
  drawTom(ctx, 4, 108, { face: flinch ? 'blink' : t > 34 ? 'happy' : 'side' });
  son(ctx, 'newton', 30, 108, { face: flinch ? 'blink' : t > 15 ? 'up' : 'side', tail: 1 });
  son(ctx, 'skippy', 56, 108, { face: flinch ? 'blink' : blinkAt(t, 4) ? 'blink' : 'side', tail: 0 });

  // Simba
  const sx = 150, feet = 120;
  const whirl = t > 14.5 && t < 34.5;
  let sm;
  if (t < 12) {
    sm = son(ctx, 'simba', sx, feet, {
      face: t > 6 ? 'side' : t > 3 ? 'up' : 'open',
      mouth: t > 7 && t < 9 && Math.floor(t * 4) % 2 ? 'meow' : null,
      tail: Math.floor(t * 0.8) % 2, flip: t > 6,
    });
  } else if (!whirl) {
    // drawing (t 12–14.5) or lowering (34.5–36) the sword, then sitting pleased
    if (t > 36) {
      sm = son(ctx, 'simba', sx, feet, { face: blinkAt(t, 8) ? 'blink' : 'happy', tail: 1 });
      if (Math.floor(t * 3) % 2) sparkle(ctx, sx + 4, feet - 22, 1);
      if (Math.floor(t * 3 + 1) % 2) sparkle(ctx, sx + 16, feet - 16, 1);
    } else {
      sm = son(ctx, 'simba', sx, feet, { face: 'side', paw: 0, tail: 1 });
      put(ctx, SWORD(), sm.x - 1, sm.y + 6);
    }
  } else {
    sm = son(ctx, 'simba', sx, feet, { face: flash > 0.3 ? 'blink' : 'up', paw: 0, tail: Math.floor(t * 2) % 2 });
  }

  // rain, kept off the porch and off Simba's whirling blade
  const cx = sx + 9, cy = feet - 32, rx = 19;
  if (rain > 0) {
    const n = Math.round(rain * 220);
    ctx.fillStyle = dark > 0.5 ? '#9aaccc' : '#b8cfe6';
    for (let i = 0; i < n; i++) {
      const sp = 140 + hash(i * 3) * 60;
      const y = ((hash(i * 7) * (H + 30) + t * sp) % (H + 30)) - 20;
      const x = ((hash(i * 11) * (W + 40) - y * 0.25 + 400) % (W + 40)) - 20;
      if (x < 98 && y > 62) continue;
      if (whirl && Math.abs(x - cx) < rx && y > cy - 2) {
        if (y < cy + 2) {
          rect(ctx, x - 2, cy - 2, 1, 1, '#e8f2ff');
          rect(ctx, x + 2, cy - 3, 1, 1, '#e8f2ff');
        }
        continue;
      }
      ctx.fillRect(Math.round(x), Math.round(y), 1, 4);
    }
    // splashes on the ground
    for (let i = 0; i < Math.round(rain * 40); i++) {
      const a = (t * 3 + hash(i)) % 1;
      const x = Math.floor(hash(i + 51) * W), y = 100 + Math.floor(hash(i + 52) * 34);
      if (x < 98 && y < 112) continue;
      if (whirl && Math.abs(x - cx) < rx - 3 && y > feet - 6 && y < feet + 6) continue;
      if (a < 0.3) { rect(ctx, x - 1, y - 1, 1, 1, '#d8e6f6'); rect(ctx, x + 1, y - 1, 1, 1, '#d8e6f6'); }
    }
  }
  if (whirl) {
    // the blade itself, spun so fast it makes a disc of light
    const spin = t * 26;
    ctx.globalAlpha = 0.35;
    ellipse(ctx, cx, cy, rx, 4, '#dfe8f6');
    ctx.globalAlpha = 0.6;
    ellipse(ctx, cx, cy - 1, rx - 4, 2, '#f4f8ff');
    ctx.globalAlpha = 1;
    for (let k = 0; k < 4; k++) {
      for (let j = 0; j < 22; j++) {
        const a = spin + k * (Math.PI / 2) - j * 0.07;
        ctx.globalAlpha = 1 - j / 22;
        rect(ctx, Math.round(cx + Math.cos(a) * rx), Math.round(cy + Math.sin(a) * 4), 2, 1, '#ffffff');
      }
    }
    ctx.globalAlpha = 1;
    const a = spin;
    pline(ctx, sm.x + 1.5, sm.y + 5, cx + Math.cos(a) * rx, cy + Math.sin(a) * 4, '#eef1f7');
    // droplets flung off the rim
    for (let i = 0; i < 8; i++) {
      const p = (t * 2.5 + i / 8) % 1, side = i % 2 ? 1 : -1;
      ctx.globalAlpha = rain * (1 - p);
      rect(ctx, cx + side * (rx + p * 18), cy - 2 + p * p * 30 - p * 8, 1, 1, '#e8f2ff');
    }
    ctx.globalAlpha = 1;
  }
  // dim everything under the storm, and light it all up in a flash
  ctx.globalAlpha = dark * 0.12;
  rect(ctx, 0, 0, W, H, '#1a1c30');
  ctx.globalAlpha = flash * 0.55;
  rect(ctx, 0, 0, W, H, '#f4f6ff');
  ctx.globalAlpha = 1;
}

// ---------- text in the picture ----------
function words(ctx, text, x, y, size, col, font = '"Jacquarda Bastarda 9", "Pixelify Sans", monospace', shadow = INK) {
  ctx.font = `${size}px ${font}`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  if (shadow) { ctx.fillStyle = shadow; ctx.fillText(text, x, y + 1); }
  ctx.fillStyle = col;
  ctx.fillText(text, x, y);
}
function stars(ctx, t, n = 40, seed = 1) {
  for (let i = 0; i < n; i++) {
    const tw = Math.sin(t * 2 + i) > 0.6;
    rect(ctx, Math.floor(hash(i + seed) * W), Math.floor(hash(i + seed + 99) * 70), 1, 1, tw ? '#ffffff' : '#b8b0d8');
  }
}
function heart(ctx, x, y, col = '#ff8fb1') {
  x = Math.round(x); y = Math.round(y);
  rect(ctx, x, y, 2, 1, col); rect(ctx, x + 3, y, 2, 1, col);
  rect(ctx, x - 1, y + 1, 7, 2, col); rect(ctx, x, y + 3, 5, 1, col); rect(ctx, x + 1, y + 4, 3, 1, col); rect(ctx, x + 2, y + 5, 1, 1, col);
}
const stepAlpha = (v) => Math.round(clamp(v) * 4) / 4; // fades in hard steps, like old games

// ---------- 1. Title ----------
function nightHill(ctx, w, h) {
  gradient(ctx, 0, 0, w, 100, ['#120c22', '#1d1636', '#2c2350', '#3c2f5e']);
  hills(ctx, w, 104, 8, [[1, 1], [3, 0.3]], '#1a2a24', '#2a3e32', 2);
  hills(ctx, w, 118, 4, [[2, 1], [5, 0.4]], '#14201c', null, 6);
}
function sceneTitle(ctx, t) {
  ctx.drawImage(layer('title-bg', W, H, nightHill), 0, 0);
  stars(ctx, t, 50, 3);
  disc(ctx, 30, 70, 9, '#f6edc8');
  disc(ctx, 33, 68, 8, '#1d1636');
  // the little house on the hill, window lit
  ctx.globalAlpha = 1;
  cottage(ctx, 158, 110, { night: true, doorLit: true });
  ctx.globalAlpha = 0.5;
  ctx.drawImage(layer('vig-title', W, H, (c, w, h) => vignette(c, w, h, 'rgba(10,6,20,0.5)')), 0, 0);
  ctx.globalAlpha = 1;
  // the three brothers walk up the hill and sit
  [['newton', 0], ['skippy', 1], ['simba', 2]].forEach(([id, i]) => {
    const stop = 40 + i * 24;
    const x = lerp(-30 - i * 26, stop, ease(seg(t, 1 + i * 0.4, 8 + i * 0.4)));
    const feet = 112 - Math.round(Math.sin((x / W) * Math.PI) * 4);
    if (t < 8 + i * 0.4) runner(ctx, id, x, feet, t, false, 8);
    else son(ctx, id, x, feet, { face: blinkAt(t, i) ? 'blink' : 'happy', tail: Math.floor(t + i) % 2 });
  });
  ctx.globalAlpha = stepAlpha(seg(t, 3, 5.5));
  words(ctx, 'The Three Brothers', W / 2, 22, 20, '#f2e2b6');
  ctx.globalAlpha = stepAlpha(seg(t, 5.5, 7.5));
  words(ctx, 'after the Brothers Grimm', W / 2, 38, 8, '#b8a8c8', '"Pixelify Sans", monospace');
  ctx.globalAlpha = 1;
}

// ---------- 3. Three roads ----------
function crossSky(ctx, w, h) {
  gradient(ctx, 0, 0, w, 80, ['#9cc8e6', '#bddbec', '#e4eee4', '#f4eed2']);
  hills(ctx, w, 70, 6, [[2, 1], [5, 0.4]], '#a6c88a', '#bcd8a0', 9);
  for (let i = 0; i < 8; i++) tree(ctx, Math.floor(hash(i + 900) * w), 74, 1, { trunk: '#6a5a44', dark: '#6f9a5a', mid: '#82ad68', light: '#9cc47e' });
  gradient(ctx, 0, 76, w, 59, ['#7ab25a', '#68a24c', '#58903f']);
  // three roads meeting in a Y
  const road = (x0, y0, x1, y1, wd) => {
    for (let i = 0; i <= 60; i++) {
      const f = i / 60, x = lerp(x0, x1, f), y = lerp(y0, y1, f), r = lerp(wd, wd * 0.35, f);
      ellipse(ctx, x, y, Math.round(r), 1, '#c8aa78');
    }
  };
  road(120, 135, 120, 108, 22);
  road(120, 110, -10, 96, 14);
  road(120, 110, 250, 96, 14);
  road(120, 110, 132, 78, 10);
  for (let i = 0; i < 60; i++) rect(ctx, Math.floor(hash(i + 950) * w), 80 + Math.floor(hash(i + 951) * 55), 1, 1, '#4a8034');
}
function signpost(ctx, x, ground) {
  rect(ctx, x, ground - 34, 3, 34, '#6a4426');
  rect(ctx, x - 16, ground - 32, 16, 5, '#8a6238'); rect(ctx, x - 18, ground - 31, 2, 3, '#8a6238');
  rect(ctx, x + 3, ground - 26, 16, 5, '#8a6238'); rect(ctx, x + 19, ground - 25, 2, 3, '#8a6238');
  rect(ctx, x - 6, ground - 40, 14, 5, '#8a6238');
  for (const [a, b] of [[x - 14, ground - 30], [x + 5, ground - 24], [x - 4, ground - 38]]) rect(ctx, a, b, 9, 1, '#4a2e1a');
}
function sceneCrossroads(ctx, t) {
  ctx.drawImage(layer('cross-bg', W, H, crossSky), 0, 0);
  [[40, 16, 1], [170, 10, 1.2]].forEach(([x, y, k]) => cloud(ctx, ((x + t * 2) % 280) - 20, y, k, '#ffffff', '#dfeaf2'));
  signpost(ctx, 118, 108);
  // walk in together from the bottom road, then part three ways
  const ids = ['newton', 'skippy', 'simba'];
  ids.forEach((id, i) => {
    const gx = 96 + i * 18;
    if (t < 5) {
      const x = lerp(-40 + i * 18, gx, ease(seg(t, 0, 4.5)));
      if (t < 4.5) runner(ctx, id, x, 122 - i, t, false, 8);
      else son(ctx, id, gx, 122 - i, { face: 'side', flip: i === 0 });
    } else if (t < 8) {
      son(ctx, id, gx, 122 - i, { face: blinkAt(t, i) ? 'blink' : i === 0 ? 'side' : 'happy', flip: i === 0, paw: t > 6 && t < 7.5 ? Math.floor(t * 4) % 2 : null });
    } else {
      const k = seg(t, 8 + i * 0.6, 15);
      if (i === 0) runner(ctx, id, lerp(gx, 250, k), lerp(122, 104, k), t, false, 8);
      if (i === 1) { const x = lerp(gx, 128, k), y = lerp(121, 84, k); if (y > 86) runner(ctx, id, x, y, t, false, 8); }
      if (i === 2) runner(ctx, id, lerp(gx, -40, k), lerp(120, 104, k), t, true, 8);
    }
  });
}

// ---------- 4. Learning a trade ----------
const SEASONS = [['#a8d488', '#f6b8c8'], ['#7ab25a', '#f2d24a'], ['#c8843a', '#d9542e'], ['#e8eef4', '#ffffff']];
function scenePanels(ctx, t) {
  rect(ctx, 0, 0, W, H, '#1d1424');
  const season = Math.min(3, Math.floor(t / 6.25));
  const [ground, fleck] = SEASONS[season];
  const panels = [
    { x: 4, id: 'skippy', bg: '#e9dcc0', wall: '#c9b48e' },
    { x: 82, id: 'newton', bg: '#3a2a2a', wall: '#2a1c1c' },
    { x: 160, id: 'simba', bg: '#c9d2dc', wall: '#a8b2c0' },
  ];
  panels.forEach((p, i) => {
    const pw = 76, ph = 118, py = 8;
    rect(ctx, p.x - 1, py - 1, pw + 2, ph + 2, '#e2b84a');
    rect(ctx, p.x, py, pw, ph, p.bg);
    rect(ctx, p.x, py, pw, 70, p.wall);
    // a window showing the season outside
    rect(ctx, p.x + 48, py + 10, 20, 16, '#6a4426');
    rect(ctx, p.x + 49, py + 11, 18, 14, season === 3 ? '#cfd8e2' : '#9fc3d8');
    rect(ctx, p.x + 49, py + 20, 18, 5, ground);
    for (let k = 0; k < 4; k++) {
      const fy = (t * 6 + k * 4 + i * 2) % 14;
      if (season >= 2) rect(ctx, p.x + 51 + ((k * 5 + Math.floor(t * 2)) % 15), py + 11 + fy, 1, 1, fleck);
    }
    rect(ctx, p.x + 57, py + 11, 1, 14, '#6a4426');
    const feet = py + ph - 14;
    rect(ctx, p.x, feet, pw, ph - (feet - py), mixHex(p.bg, '#2a1d2e', 0.25));
    const beat = Math.floor(t * 4 + i) % 2;
    if (p.id === 'skippy') {
      // practising on a very patient hedge in a pot
      rect(ctx, p.x + 46, feet - 6, 12, 6, '#a8603a');
      disc(ctx, p.x + 52, feet - 14, 7, '#4f8a3c');
      disc(ctx, p.x + 50, feet - 16, 4, '#6aa64c');
      const c = son(ctx, 'skippy', p.x + 18, feet + 1, { face: 'up', paw: beat, tail: 1 });
      put(ctx, SCISSORS(), c.x + 0.5 + beat, c.y + 5 - beat * 2);
      for (let k = 0; k < 3; k++) { const a = (t * 2 + k / 3) % 1; rect(ctx, p.x + 44 - a * 6, feet - 14 + a * 12, 1, 1, '#4f8a3c'); }
    } else if (p.id === 'newton') {
      // the forge glow and the anvil
      ctx.globalAlpha = 0.5 + 0.2 * Math.sin(t * 7);
      disc(ctx, p.x + 12, feet - 18, 12, '#d9542e');
      ctx.globalAlpha = 1;
      rect(ctx, p.x + 4, feet - 22, 16, 22, '#4a3a3a');
      rect(ctx, p.x + 6, feet - 16, 12, 6, '#ff9a3a');
      rect(ctx, p.x + 40, feet - 12, 20, 4, '#5b5f6c');
      rect(ctx, p.x + 44, feet - 8, 12, 8, '#4a4e5a');
      rect(ctx, p.x + 42, feet - 13, 16, 1, '#8b8f9c');
      rect(ctx, p.x + 47, feet - 15, 6, 2, beat ? '#ffb060' : '#ff8a3a');
      const c = son(ctx, 'newton', p.x + 24, feet + 1, { face: 'up', paw: beat, tail: 1 });
      put(ctx, HAMMER(), c.x - 1, c.y + 6 - beat * 3);
      if (!beat) for (let k = 0; k < 4; k++) sparkle(ctx, p.x + 48 + hash(k + Math.floor(t * 4)) * 8, feet - 18 - hash(k + 7 + Math.floor(t * 4)) * 6, 1, '#ffd36a');
    } else {
      // a straw dummy to fence against
      rect(ctx, p.x + 52, feet - 30, 2, 30, '#6a4426');
      ellipse(ctx, p.x + 53, feet - 22, 6, 8, '#d8b86a');
      disc(ctx, p.x + 53, feet - 33, 4, '#d8b86a');
      rect(ctx, p.x + 51, feet - 22, 5, 1, '#b8943a');
      const c = son(ctx, 'simba', p.x + 18, feet + 1, { face: 'side', paw: 0, tail: beat });
      const lunge = Math.sin(t * 6) > 0.3;
      ctx.save();
      ctx.translate(c.x + 2, c.y + 8);
      ctx.rotate(lunge ? -1.45 : -0.6);
      const img = SWORD();
      ctx.drawImage(img, -2.5, -17, img.width / 2, img.height / 2);
      ctx.restore();
      if (lunge) sparkle(ctx, p.x + 47, feet - 22, 1);
    }
    // snow over everything in winter
    if (season === 3) for (let k = 0; k < 12; k++) rect(ctx, p.x + ((k * 13 + i * 7) % pw), py + ((t * 10 + k * 9) % ph), 1, 1, '#ffffff');
  });
}

// ---------- 5. Home again ----------
function homeBg(ctx, w, h) {
  gradient(ctx, 0, 0, w, 90, ['#9cc8e6', '#c0dcec', '#e6f0e6']);
  hills(ctx, w, 82, 5, [[2, 1], [5, 0.4]], '#9ec384', '#b6d49a', 12);
  gradient(ctx, 0, 100, w, 35, ['#6aa64c', '#5d9a45', '#4f8a3c']);
  for (let i = 0; i < 40; i++) {
    const x = Math.floor(hash(i + 1200) * w), y = 102 + Math.floor(hash(i + 1201) * 30);
    rect(ctx, x, y, 1, 1, ['#f4f0e0', '#f2d24a', '#e88aa0', '#3f7a30'][i % 4]);
  }
}
function sceneHome(ctx, t) {
  ctx.drawImage(layer('home-bg', W, H, homeBg), 0, 0);
  [[60, 18, 1], [180, 12, 1.1]].forEach(([x, y, k]) => cloud(ctx, ((x + t * 1.5) % 280) - 20, y, k, '#ffffff', '#dfeaf2'));
  cottage(ctx, 20, 104, { doorLit: t > 2 });
  // Old Tom steps out of the door
  const tomX = lerp(62, 80, ease(seg(t, 2, 4)));
  if (t > 2) drawTom(ctx, tomX, 112, { face: t > 5 ? 'happy' : 'open', mouth: t > 4.5 && t < 6 && Math.floor(t * 5) % 2 ? 'meow' : null, tail: 1 });
  ['newton', 'skippy', 'simba'].forEach((id, i) => {
    const stop = 112 + i * 24;
    const x = lerp(260 + i * 30, stop, ease(seg(t, 0, 5 + i * 0.4)));
    if (t < 5 + i * 0.4) runner(ctx, id, x, 118, t, true, 9);
    else son(ctx, id, x, 118, { face: blinkAt(t, i) ? 'blink' : t > 7 ? 'side' : 'happy', flip: true, tail: Math.floor(t + i) % 2 });
  });
  for (let k = 0; k < 5; k++) {
    const a = (t - 5.5 - k * 0.5);
    if (a > 0 && a < 3) { ctx.globalAlpha = 1 - a / 3; heart(ctx, 100 + k * 12 + Math.sin(a * 3) * 2, 92 - a * 10); ctx.globalAlpha = 1; }
  }
}

// ---------- 9. The house ----------
function sceneVerdict(ctx, t) {
  ctx.drawImage(layer('cottage-in', W, H, cottageInside), 0, 0);
  const sw = Math.sin(t * Math.PI) * 3;
  pline(ctx, 134, 31, 134 + sw, 41, '#c9a25a');
  disc(ctx, 134 + sw, 42, 1, '#e2b84a');
  fire(ctx, t, 30, 100, 44);
  const rock = Math.sin(t * 1.2) * 0.6;
  rockingChair(ctx, 95 + rock, 116, rock);
  drawTom(ctx, 96 + rock, 116, { face: blinkAt(t, 1) ? 'blink' : 'side', mouth: t < 8 && Math.floor(t * 5) % 2 ? 'meow' : null });
  const hop = (a) => (t > a && t < a + 0.5 ? -Math.round(Math.sin(((t - a) / 0.5) * Math.PI) * 4) : 0);
  // Simba front and centre: proud, then softens
  const sFace = t < 9 ? 'side' : t < 13 ? 'blink' : t < 16 ? 'side' : 'happy';
  son(ctx, 'newton', 140, 116 + hop(20), { face: t > 19 ? 'happy' : 'side', flip: true, tail: 1 });
  son(ctx, 'skippy', 186, 116 + hop(20.4), { face: t > 19 ? 'happy' : blinkAt(t, 6) ? 'blink' : 'side', flip: true, tail: 0 });
  son(ctx, 'simba', 163, 121 + hop(9), { face: sFace, flip: t > 13 && t < 16 ? false : true, tail: 1, mouth: t > 16 && t < 19 && Math.floor(t * 4) % 2 ? 'meow' : null });
  if (t > 9 && t < 13) for (let k = 0; k < 3; k++) if (Math.floor(t * 3 + k) % 2) sparkle(ctx, 162 + k * 10, 96 - (k % 2) * 4, 1, '#ffd36a');
  for (let k = 0; k < 6; k++) {
    const a = t - 19.5 - k * 0.6;
    if (a > 0 && a < 3) { ctx.globalAlpha = 1 - a / 3; heart(ctx, 146 + k * 9 + Math.sin(a * 3) * 2, 94 - a * 10); ctx.globalAlpha = 1; }
  }
  ctx.globalAlpha = 0.75 + 0.25 * Math.sin(t * 9) * Math.sin(t * 5.3);
  ctx.drawImage(layer('fireglow', W, H, (c, w, h) => glowLayer(c, w, h, 52, 92, 140, 'rgba(255,170,90,0.07)')), 0, 0);
  ctx.globalAlpha = 1;
  ctx.drawImage(layer('vig-night', W, H, (c, w, h) => vignette(c, w, h, 'rgba(14,8,18,0.22)')), 0, 0);
}

// ---------- 10. Together ----------
function sceneEnd(ctx, t) {
  ctx.drawImage(layer('cottage-in', W, H, cottageInside), 0, 0);
  fire(ctx, t * 0.6, 30, 100, 44);
  rockingChair(ctx, 95, 116, 0);
  drawTom(ctx, 96, 116, { face: 'blink' });
  // a heap of sleeping brothers on the rug
  put(ctx, cat('simba', 'sleep', { frame: Math.floor(t / 1.1) % 2 }), 150, 120);
  put(ctx, cat('skippy', 'sleep', { frame: Math.floor(t / 1.3 + 1) % 2 }), 168, 121);
  put(ctx, cat('newton', 'sleep', { frame: Math.floor(t / 1.2) % 2, flip: true }), 160, 112);
  for (let k = 0; k < 3; k++) {
    const a = (t * 0.5 + k / 3) % 1;
    ctx.globalAlpha = 1 - a;
    words(ctx, 'z', 186 + a * 10 + k * 3, 96 - a * 16, 6 + k, '#e8e2ff', '"Pixelify Sans", monospace', null);
    ctx.globalAlpha = 1;
  }
  ctx.globalAlpha = 0.6 + 0.2 * Math.sin(t * 5);
  ctx.drawImage(layer('fireglow', W, H, (c, w, h) => glowLayer(c, w, h, 52, 92, 140, 'rgba(255,170,90,0.07)')), 0, 0);
  ctx.globalAlpha = 1;
  ctx.drawImage(layer('vig-night', W, H, (c, w, h) => vignette(c, w, h, 'rgba(14,8,18,0.22)')), 0, 0);
  // the book closes
  const k = stepAlpha(seg(t, 12, 14));
  if (k > 0) {
    ctx.globalAlpha = k;
    rect(ctx, 0, 0, W, H, '#170f1c');
    ctx.globalAlpha = stepAlpha(seg(t, 14, 15.5));
    words(ctx, 'The End', W / 2, H / 2 - 4, 22, '#f2e2b6');
    ctx.globalAlpha = 1;
  }
}


// =====================================================================
// THE BREMEN TOWN MUSICIANS
// =====================================================================
const COSTUME = { tom: 'donkey', newton: 'dog', skippy: 'rooster', simba: null };
const EAR = '#8a8798', EAR_IN = '#d9a0a8', HOUND = '#7a4a2a', RED = '#d9342e', GOLD = '#e2b84a', BLANKET = '#2f6a8a';

// Costume pieces as [dx, dy, w, h, colour] relative to the sprite, for each pose (facing right).
const WEAR = {
  donkey: {
    sit: [[1, -10, 5, 12, INK], [2, -9, 3, 11, EAR], [3, -7, 1, 7, EAR_IN], [12, -10, 5, 12, INK], [13, -9, 3, 11, EAR], [14, -7, 1, 7, EAR_IN], [1, 13, 16, 4, INK], [2, 13, 14, 3, BLANKET], [2, 13, 14, 1, GOLD]],
    walk: [[16, -9, 5, 11, INK], [17, -8, 3, 10, EAR], [18, -6, 1, 6, EAR_IN], [20, -9, 5, 11, INK], [21, -8, 3, 10, EAR], [6, 6, 12, 6, INK], [7, 7, 10, 4, BLANKET], [7, 7, 10, 1, GOLD]],
  },
  dog: {
    sit: [[-2, 2, 5, 10, INK], [-1, 3, 3, 8, HOUND], [15, 2, 5, 10, INK], [16, 3, 3, 8, HOUND], [4, 11, 10, 2, RED], [8, 13, 2, 2, GOLD]],
    walk: [[15, 1, 5, 9, INK], [16, 2, 3, 7, HOUND], [17, 9, 7, 2, RED], [20, 11, 2, 2, GOLD]],
  },
  rooster: {
    sit: [[5, -3, 8, 4, INK], [6, -2, 2, 3, RED], [8, -4, 2, 5, RED], [10, -3, 2, 4, RED], [8, 11, 2, 3, RED]],
    walk: [[18, -4, 7, 4, INK], [19, -3, 2, 3, RED], [21, -4, 2, 4, RED], [23, -3, 1, 3, RED], [24, 9, 2, 3, RED]],
  },
};
function wear(ctx, kind, r, pose, flip) {
  if (!kind) return;
  const W0 = pose === 'walk' ? 26 : 22;
  const base = pose === 'sit' && flip ? 4 : 0; // a flipped sit sprite has its body on the right
  for (const [dx, dy, w, h, col] of WEAR[kind][pose]) {
    const x = flip ? (pose === 'walk' ? r.x + W0 - dx - w : r.x + base + 18 - dx - w) : r.x + dx;
    rect(ctx, x, r.y + dy, w, h, col);
  }
}
// One of the four musicians. o: { pose: 'sit'|'walk', face, mouth, tail, paw, flip, rate }
function musician(ctx, id, x, feet, t, o = {}) {
  const pose = o.pose ?? 'sit';
  let r;
  if (pose === 'walk') r = runner(ctx, id, x, feet, t, !!o.flip, o.rate ?? 8);
  else r = put(ctx, cat(id, 'sit', { face: o.face ?? 'open', mouth: o.mouth ?? null, tail: o.tail ?? 0, paw: o.paw ?? null, flip: !!o.flip }), x, feet);
  wear(ctx, COSTUME[id], r, pose, !!o.flip);
  if (id === 'tom' && pose === 'sit' && o.face !== 'blink') put(ctx, SPECTACLES(), r.x + (o.flip ? 4 : 0) + 4.5, r.y + 9.5);
  return r;
}
function robber(ctx, x, feet, t, o = {}) {
  if (o.pose === 'walk') return runner(ctx, 'raccoon', x, feet, t, !!o.flip, o.rate ?? 8);
  return put(ctx, cat('raccoon', 'sit', { mask: true, face: o.face ?? 'open', mouth: o.mouth ?? null, tail: o.tail ?? 0, flip: !!o.flip }), x, feet);
}
function note(ctx, x, y, col = '#f2e2b6') {
  x = Math.round(x); y = Math.round(y);
  rect(ctx, x, y + 4, 3, 2, col); rect(ctx, x + 2, y, 1, 5, col); rect(ctx, x + 3, y, 2, 1, col); rect(ctx, x + 4, y + 1, 1, 1, col);
}
function notes(ctx, x, y, t, n = 3, col) {
  for (let k = 0; k < n; k++) {
    const a = (t * 0.6 + k / n) % 1;
    ctx.globalAlpha = 1 - a;
    note(ctx, x + Math.sin(a * 6 + k) * 4 + k * 3, y - a * 20, col);
  }
  ctx.globalAlpha = 1;
}
const walkTo = (t, t0, t1, x0, x1) => lerp(x0, x1, seg(t, t0, t1));
const moving = (t, t0, t1) => t > t0 && t < t1;
// A four-friend procession walking right; who lists ids in order from the front.
function procession(ctx, who, lead, feet, t, gap = 26) {
  who.forEach((id, i) => musician(ctx, id, lead - i * gap, feet, t, { pose: 'walk' }));
}

// ---------- B1. Title ----------
function duskRoad(ctx, w, h) {
  gradient(ctx, 0, 0, w, 96, ['#2e2450', '#5a3a6a', '#a8586a', '#e88a6a', '#f6c27a']);
  disc(ctx, 176, 80, 14, '#ffd88a');
  hills(ctx, w, 86, 6, [[2, 1], [5, 0.3]], '#3a3050', '#4a3a5e', 11);
  hills(ctx, w, 98, 4, [[3, 1], [7, 0.3]], '#2a2440', null, 14);
  gradient(ctx, 0, 104, w, 31, ['#3a3048', '#2a2238']);
  for (let x = 0; x < w; x++) rect(ctx, x, 108 + Math.round(Math.sin(x / 40) * 1.5), 1, 9, bayer(x, 0) < 0.5 ? '#7a6058' : '#6a5050');
}
function sceneBTitle(ctx, t) {
  ctx.drawImage(layer('b-dusk', W, H, duskRoad), 0, 0);
  stars(ctx, t, 18, 21);
  // signpost to Bremen
  rect(ctx, 196, 82, 3, 30, '#4a2e1e');
  rect(ctx, 186, 84, 30, 8, '#7a5232');
  rect(ctx, 216, 85, 2, 6, '#7a5232'); rect(ctx, 218, 86, 1, 4, '#7a5232');
  words(ctx, 'BREMEN', 201, 88.5, 6, '#f2e2b6', '"Pixelify Sans", monospace', null);
  // the four set off along the road
  if (t > 4) procession(ctx, ['skippy', 'simba', 'newton', 'tom'], walkTo(t, 4, 12, 40, 150), 118, t);
  ctx.globalAlpha = stepAlpha(seg(t, 1, 3));
  words(ctx, 'The Bremen Town Musicians', W / 2, 24, 13, '#f2e2b6');
  ctx.globalAlpha = stepAlpha(seg(t, 2.5, 4.5));
  words(ctx, 'after the Brothers Grimm', W / 2, 40, 8, '#d8c0d0', '"Pixelify Sans", monospace');
  ctx.globalAlpha = 1;
}

// ---------- B2. The donkey ----------
function farmyard(ctx, w, h) {
  gradient(ctx, 0, 0, w, 90, ['#8cc0e2', '#b4d6ea', '#e2eee6']);
  hills(ctx, w, 80, 5, [[2, 1], [5, 0.4]], '#a6c88a', '#bcd8a0', 15);
  gradient(ctx, 0, 92, w, 43, ['#b89a6a', '#a8885a', '#8a7048']);
  // barn
  rect(ctx, 12, 44, 80, 56, '#9a3a2e');
  for (let x = 12; x < 92; x += 5) rect(ctx, x, 44, 1, 56, '#7e2a22');
  for (let i = 0; i < 20; i++) rect(ctx, 8 + i * 2, 44 - i, 88 - i * 4, 1, '#5a3a2e');
  rect(ctx, 38, 66, 28, 34, '#e9dcc0');
  rect(ctx, 40, 68, 24, 32, '#7e2a22');
  pline(ctx, 40, 68, 63, 99, '#e9dcc0'); pline(ctx, 63, 68, 40, 99, '#e9dcc0');
  rect(ctx, 46, 30, 12, 9, '#e9dcc0'); rect(ctx, 47, 31, 10, 7, '#2a1814');
  // fence and hay
  for (let x = 100; x < w; x += 16) rect(ctx, x, 82, 2, 18, '#e9dcc0');
  rect(ctx, 100, 86, w - 100, 2, '#e9dcc0'); rect(ctx, 100, 93, w - 100, 2, '#e9dcc0');
  rect(ctx, 200, 96, 24, 14, '#d8b860'); rect(ctx, 200, 100, 24, 1, '#b8943a'); rect(ctx, 200, 105, 24, 1, '#b8943a');
  for (let i = 0; i < 50; i++) rect(ctx, Math.floor(hash(i + 1500) * w), 96 + Math.floor(hash(i + 1501) * 38), 1, 1, '#8a6a40');
}
function sack(ctx, x, y) {
  rect(ctx, x - 1, y - 1, 12, 11, INK);
  rect(ctx, x, y, 10, 9, '#c9a46a');
  rect(ctx, x + 3, y - 3, 4, 3, '#c9a46a'); rect(ctx, x + 2, y - 1, 6, 1, '#8a6a3a');
  rect(ctx, x + 1, y + 6, 8, 1, '#a8844a');
}
function sceneDonkey(ctx, t) {
  ctx.drawImage(layer('b-farm', W, H, farmyard), 0, 0);
  // hens pecking about
  for (let i = 0; i < 3; i++) {
    const hx = 120 + i * 22 + Math.sin(t * 0.7 + i) * 6, peck = Math.floor(t * 3 + i) % 3 === 0 ? 1 : 0;
    rect(ctx, hx - 1, 114 - 1, 8, 6, INK); rect(ctx, hx, 114, 6, 4, '#f4f0e6');
    rect(ctx, hx + 5, 111 + peck, 3, 3, '#f4f0e6'); rect(ctx, hx + 6, 110 + peck, 1, 1, RED); rect(ctx, hx + 8, 112 + peck, 1, 1, GOLD);
  }
  const feet = 120;
  if (t < 6) {
    const x = walkTo(t, 0, 6, 60, 96);
    const r = musician(ctx, 'tom', x, feet, t, { pose: 'walk', rate: 5 });
    sack(ctx, r.x + 8, r.y - 4 + (Math.floor(t * 5) % 2));
  } else if (t < 16) {
    const drop = seg(t, 6, 6.5);
    sack(ctx, 104 + drop * 10, 96 + ease(drop) * 14);
    if (t < 7) dust(ctx, 120, 120, t, 31);
    musician(ctx, 'tom', 96, feet, t, { face: t < 9 ? 'open' : 'blink', tail: 0 });
  } else {
    sack(ctx, 114, 110);
    const x = t < 18 ? 96 : walkTo(t, 18, 24, 96, 250);
    if (t < 18) musician(ctx, 'tom', 96, feet, t, { face: 'up', mouth: Math.floor(t * 4) % 2 ? 'meow' : null, tail: 1 });
    else musician(ctx, 'tom', x, feet, t, { pose: 'walk', rate: 7 });
    notes(ctx, (t < 18 ? 104 : x + 20), 96, t);
  }
}

// ---------- B3. The dog ----------
function sceneDog(ctx, t) {
  tile(ctx, layer('m-sky', W, 80, meadowSky), 0, 0);
  [[40, 16, 1], [170, 10, 1.2]].forEach(([x, y, k]) => cloud(ctx, ((x + t * 2) % 280) - 20, y, k, '#ffffff', '#dfeaf2'));
  tile(ctx, layer('m-far', 480, 135, meadowFar), 30, 0);
  tile(ctx, layer('m-near', 480, 135, meadowNear), 60, 0);
  tile(ctx, layer('m-ground', 480, 37, meadowGround), 90, 98);
  const feet = 118;
  // Newton the old hound, panting in the grass
  if (t < 16) {
    musician(ctx, 'newton', 150, feet, t, { face: t > 7 ? 'side' : 'blink', mouth: Math.floor(t * 5) % 2 ? 'meow' : null, flip: true, tail: 0 });
    if (t < 7) for (let k = 0; k < 2; k++) if (Math.floor(t * 5 + k) % 2) rect(ctx, 152 + k * 3, 106, 1, 1, '#9fd0ff');
  }
  if (t < 6) musician(ctx, 'tom', walkTo(t, 0, 6, -30, 110), feet, t, { pose: 'walk' });
  else if (t < 16) musician(ctx, 'tom', 110, feet, t, { face: blinkAt(t, 3) ? 'blink' : 'side', mouth: t > 16 - 6 && Math.floor(t * 4) % 2 ? 'meow' : null });
  if (t >= 16) {
    const lead = walkTo(t, 18, 24, 160, 290);
    if (t < 18) {
      musician(ctx, 'tom', 110, feet, t, { face: 'happy', tail: 1 });
      musician(ctx, 'newton', 150, feet - Math.round(Math.abs(Math.sin((t - 16) * 6)) * 4), t, { face: 'happy', flip: true, tail: 1 });
    } else procession(ctx, ['newton', 'tom'], lead, feet, t);
  }
}

// ---------- B4. The cat ----------
function wallRoad(ctx, w, h) {
  gradient(ctx, 0, 0, w, 84, ['#94c0de', '#b8d6e8', '#e4eee2']);
  hills(ctx, w, 76, 5, [[2, 1], [5, 0.4]], '#a6c88a', '#bcd8a0', 17);
  gradient(ctx, 0, 84, w, 51, ['#7ab25a', '#68a24c', '#58903f']);
  for (let x = 0; x < w; x++) rect(ctx, x, 112, 1, 10, bayer(x, 1) < 0.5 ? '#c8aa78' : '#b89a6a');
  // dry-stone wall
  for (let y = 80; y < 104; y += 4)
    for (let x = ((y / 4) % 2) * 5; x < w; x += 10) {
      rect(ctx, x, y, 9, 3, (x + y) % 3 ? '#9a96a0' : '#86828e');
      rect(ctx, x, y + 3, 10, 1, '#5e5a66');
    }
  rect(ctx, 0, 78, w, 3, '#b0acb6');
}
function sceneCat(ctx, t) {
  ctx.drawImage(layer('b-wall', W, H, wallRoad), 0, 0);
  const feet = 120;
  if (t < 15) {
    // Simba sulking on top of the wall
    musician(ctx, 'simba', 150, 79, t, { face: t > 8 && t < 15 ? 'side' : 'blink', mouth: t > 8.5 && t < 13 && Math.floor(t * 4) % 2 ? 'meow' : null, tail: Math.floor(t * 0.5) % 2, flip: true });
    // a little rain cloud over his head, for the sulk
    if (t < 8) { cloud(ctx, 154, 46, 0.6, '#9aa0b0', '#7a8090'); for (let k = 0; k < 4; k++) rect(ctx, 150 + k * 4, 52 + ((t * 30 + k * 5) % 8), 1, 2, '#7aa0d0'); }
  }
  if (t < 6) procession(ctx, ['newton', 'tom'], walkTo(t, 0, 6, -10, 112), feet, t);
  else if (t < 17) {
    musician(ctx, 'newton', 112, feet, t, { face: 'up', tail: 1 });
    musician(ctx, 'tom', 86, feet, t, { face: blinkAt(t, 2) ? 'blink' : 'up', mouth: t > 15 && Math.floor(t * 4) % 2 ? 'meow' : null });
  }
  if (t >= 15 && t < 17) {
    const k = seg(t, 15, 16.2);
    musician(ctx, 'simba', lerp(150, 136, k), lerp(79, feet, ease(k)) - Math.sin(k * Math.PI) * 10, t, { face: 'happy', tail: 1 });
  }
  if (t >= 17) procession(ctx, ['simba', 'newton', 'tom'], walkTo(t, 17, 22, 150, 300), feet, t);
}

// ---------- B5. The rooster ----------
function gateYard(ctx, w, h) {
  gradient(ctx, 0, 0, w, 84, ['#f0c88a', '#f4dca6', '#f6ead0']);
  disc(ctx, 40, 60, 10, '#fff2c8');
  hills(ctx, w, 78, 5, [[2, 1], [5, 0.4]], '#b8c07a', '#cad08a', 19);
  gradient(ctx, 0, 86, w, 49, ['#8ab05a', '#76a04c', '#62903f']);
  for (let x = 0; x < w; x++) rect(ctx, x, 114, 1, 9, bayer(x, 2) < 0.5 ? '#c8aa78' : '#b89a6a');
  // farm gate
  rect(ctx, 150, 70, 5, 42, '#6a4426'); rect(ctx, 214, 70, 5, 42, '#6a4426');
  for (const y of [76, 88, 100]) rect(ctx, 155, y, 59, 3, '#8a6238');
  pline(ctx, 155, 102, 213, 77, '#8a6238'); pline(ctx, 155, 103, 213, 78, '#8a6238');
  // a cottage chimney beyond, smoking
  rect(ctx, 196, 50, 30, 22, '#dcc9a2'); for (let i = 0; i < 10; i++) rect(ctx, 192 + i, 50 - i, 38 - i * 2, 1, '#b8914e');
}
function sceneRooster(ctx, t) {
  ctx.drawImage(layer('b-gate', W, H, gateYard), 0, 0);
  for (let k = 0; k < 4; k++) { const a = (t * 0.3 + k / 4) % 1; ctx.globalAlpha = 0.6 * (1 - a); disc(ctx, 212 + a * 8, 38 - a * 20, 2 + Math.round(a * 3), '#e8e2d8'); }
  ctx.globalAlpha = 1;
  const feet = 122;
  // Skippy the rooster crowing on top of the gatepost
  const crow = (t < 6 && Math.floor(t * 2) % 3 !== 2) || (t > 8.5 && t < 14 && Math.floor(t * 4) % 2);
  if (t < 16) {
    musician(ctx, 'skippy', 142, 70, t, { face: crow ? 'up' : 'side', mouth: crow ? 'meow' : null, tail: 1, flip: true });
    if (t < 6) notes(ctx, 150, 46, t, 2, '#ffffff');
  }
  if (t < 7) procession(ctx, ['simba', 'newton', 'tom'], walkTo(t, 0, 7, -20, 128), feet, t);
  else if (t < 18) {
    musician(ctx, 'simba', 128, feet, t, { face: blinkAt(t, 5) ? 'blink' : 'up', tail: 0 });
    musician(ctx, 'newton', 104, feet, t, { face: 'up', tail: 1 });
    musician(ctx, 'tom', 80, feet, t, { face: 'up', mouth: t > 15 && t < 18 && Math.floor(t * 4) % 2 ? 'meow' : null });
  }
  if (t >= 16 && t < 18) {
    const k = seg(t, 16, 17.2);
    musician(ctx, 'skippy', lerp(142, 152, k), lerp(70, feet, ease(k)) - Math.sin(k * Math.PI) * 12, t, { face: 'happy', tail: 1 });
  }
  if (t >= 18) procession(ctx, ['skippy', 'simba', 'newton', 'tom'], walkTo(t, 18, 22, 160, 300), feet, t);
}

// ---------- B6. The forest ----------
function nightWoods(ctx, w, h) {
  gradient(ctx, 0, 0, w, 100, ['#0e0c22', '#18163a', '#24224a', '#2e2c52']);
  hills(ctx, w, 92, 4, [[2, 1], [6, 0.3]], '#141c24', null, 23);
  for (let i = 0; i < 14; i++) {
    const x = Math.floor((i / 14) * w + hash(i + 1600) * 20), s = 1.3 + hash(i + 1601) * 0.8;
    rect(ctx, x - 1, 110 - 24 * s, 3, 24 * s, '#0e1418');
    for (let k = 0; k < 5; k++) ellipse(ctx, x + 1, 110 - 24 * s - 4 + k * 6 * s, Math.round((4 + k * 2.5) * s), Math.round(3 * s), '#121c22');
  }
  gradient(ctx, 0, 110, w, 25, ['#1a2422', '#121a1a']);
}
function sceneForest(ctx, t) {
  const s = travel(t, 22, 0, 1.5, 11, 13.5);
  ctx.drawImage(layer('b-sky', W, 100, (c, w, h) => gradient(c, 0, 0, w, 100, ['#0e0c22', '#18163a', '#24224a', '#2e2c52'])), 0, 0);
  stars(ctx, t, 40, 41);
  disc(ctx, 200, 24, 8, '#f3ead0');
  tile(ctx, layer('b-woods', 480, 135, nightWoods), s, 0);
  const feet = 122;
  // a far-off lit window appears once the rooster looks
  if (t > 16) {
    ctx.globalAlpha = stepAlpha(seg(t, 16, 17.5));
    disc(ctx, 226, 96, 5, '#5a4020');
    rect(ctx, 224, 94, 4, 3, '#ffd36a');
    ctx.globalAlpha = 1;
  }
  if (t < 13) procession(ctx, ['skippy', 'simba', 'newton', 'tom'], 150, feet, t);
  else {
    musician(ctx, 'tom', 72, feet, t, { face: blinkAt(t, 1) ? 'blink' : 'up' });
    musician(ctx, 'newton', 98, feet, t, { face: 'up', tail: 1 });
    musician(ctx, 'simba', 124, feet, t, { face: 'up', tail: 0 });
    // the rooster flies to the treetop
    const k = seg(t, 13.5, 15.5);
    const x = lerp(150, 168, k), y = lerp(feet, 64, ease(k)) - Math.sin(k * Math.PI) * 10;
    musician(ctx, 'skippy', x, y, t, { face: t > 16 ? 'up' : 'happy', mouth: t > 18.5 && t < 24 && Math.floor(t * 4) % 2 ? 'meow' : null, tail: 1 });
    if (k >= 1) rect(ctx, 164, 64, 28, 2, '#0e1418');
  }
  // fireflies
  for (let i = 0; i < 6; i++) if (Math.sin(t * 2 + i * 1.7) > 0.4) rect(ctx, Math.floor(hash(i + 1700) * W), 80 + Math.floor(hash(i + 1701) * 30) + Math.round(Math.sin(t + i) * 2), 1, 1, '#e8f070');
}

// ---------- B7. The robbers' house ----------
const WIN = { x: 118, y: 36, w: 68, h: 40 };
function robberHouse(ctx, w, h) {
  gradient(ctx, 0, 0, w, 100, ['#0e0c22', '#18163a', '#24224a']);
  gradient(ctx, 0, 112, w, 23, ['#1e2a22', '#141e1a']);
  // a big timbered wall filling the frame
  rect(ctx, 40, 12, 200, 100, '#5a4a40');
  for (let x = 40; x < 240; x += 9) rect(ctx, x, 12, 1, 100, '#4a3c34');
  rect(ctx, 40, 12, 200, 3, '#2a1c16'); rect(ctx, 40, 60, 200, 2, '#2a1c16');
  for (let i = 0; i < 14; i++) rect(ctx, 30 + i, 12 - i, 220, 1, i % 3 ? '#3a2e24' : '#2e241c');
  // door on the left
  rect(ctx, 58, 64, 24, 48, '#2a1c16'); rect(ctx, 60, 66, 20, 46, '#3a2818');
  rect(ctx, 76, 88, 2, 2, GOLD);
}
function robberRoom(ctx, t, empty, faces) {
  const { x, y, w, h } = WIN;
  ctx.save();
  ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  gradient(ctx, x, y, w, h, ['#7a4a2a', '#9a6438', '#b87a44']);
  disc(ctx, x + 10, y + 12, 3, '#ffd36a');
  rect(ctx, x + 9, y + 15, 3, 6, '#efe2c2');
  if (!empty) {
    robber(ctx, x + 2, y + 34, t, { face: 'happy', mouth: Math.floor(t * 4) % 2 ? 'meow' : null, tail: 0 });
    robber(ctx, x + 24, y + 33, t, { face: blinkAt(t, 9) ? 'blink' : 'happy', mouth: Math.floor(t * 3 + 1) % 2 ? 'meow' : null, tail: 1 });
    robber(ctx, x + 46, y + 34, t, { face: 'side', flip: true, tail: 0 });
  }
  if (faces) faces(ctx);
  // the table, piled with supper and gold
  rect(ctx, x, y + 30, w, 10, '#5a3420'); rect(ctx, x, y + 30, w, 2, '#7a4a2a');
  ellipse(ctx, x + 22, y + 28, 6, 3, '#c97a3a'); rect(ctx, x + 27, y + 25, 3, 2, '#efe2c2');
  for (let k = 0; k < 9; k++) disc(ctx, x + 40 + (k % 4) * 3, y + 28 - Math.floor(k / 4) * 2, 1, k % 2 ? '#ffd36a' : GOLD);
  rect(ctx, x + 12, y + 25, 3, 5, '#b8453a');
  ctx.restore();
}
function windowFrame(ctx, broken) {
  const { x, y, w, h } = WIN;
  rect(ctx, x - 3, y - 3, w + 6, 3, '#2a1c16'); rect(ctx, x - 3, y + h, w + 6, 4, '#2a1c16');
  rect(ctx, x - 3, y, 3, h, '#2a1c16'); rect(ctx, x + w, y, 3, h, '#2a1c16');
  if (!broken) { rect(ctx, x + w / 2 - 1, y, 2, h, '#2a1c16'); rect(ctx, x, y + h / 2 - 1, w, 2, '#2a1c16'); }
}
function warmSpill(ctx) {
  ctx.globalAlpha = 0.18;
  ellipse(ctx, WIN.x + WIN.w / 2, 120, 50, 6, '#ffb060');
  ctx.globalAlpha = 1;
}
function sceneRobbers(ctx, t) {
  ctx.drawImage(layer('b-rhouse', W, H, robberHouse), 0, 0);
  stars(ctx, t, 20, 51);
  robberRoom(ctx, t, false);
  windowFrame(ctx, false);
  warmSpill(ctx);
  const feet = 124;
  // the four creep up and peek over the sill (only heads show above the grass)
  const k = ease(seg(t, 0, 5));
  ['tom', 'newton', 'simba', 'skippy'].forEach((id, i) => {
    const x = lerp(-30 - i * 24, 104 + i * 22, k);
    const peek = t > 6 ? -Math.round(ease(seg(t, 6 + i * 0.3, 7 + i * 0.3)) * 4) : 0;
    musician(ctx, id, x, feet + peek, t, { face: t > 20 ? 'happy' : 'up', tail: i % 2, mouth: t > 11 && t < 18 && id === 'newton' && Math.floor(t * 4) % 2 ? 'meow' : null });
  });
  // tall grass in front of them
  for (let x = 0; x < W; x += 2) rect(ctx, x, 116 + (hash(x) > 0.5 ? 0 : 2), 1, 20, x % 4 ? '#18241e' : '#1e2c24');
  if (t > 20) for (let i = 0; i < 3; i++) if (Math.floor(t * 3 + i) % 2) sparkle(ctx, 120 + i * 24, 96 - (i % 2) * 4, 1, '#ffd36a');
}

// ---------- B8. The concert ----------
function sceneConcert(ctx, t) {
  const shake = t > 10 && t < 15.5 ? Math.round(Math.sin(t * 50)) : 0;
  ctx.save();
  ctx.translate(shake, 0);
  ctx.drawImage(layer('b-rhouse', W, H, robberHouse), 0, 0);
  stars(ctx, t, 20, 51);
  const crashed = t > 15.5;
  robberRoom(ctx, t, crashed && t > 16.2, crashed && t > 19 ? (c) => {
    // the four tuck into the robbers' supper
    ['tom', 'newton', 'simba', 'skippy'].forEach((id, i) => musician(c, id, WIN.x + 2 + i * 16, WIN.y + 34, t, { face: 'happy', mouth: Math.floor(t * 3 + i) % 2 ? 'meow' : null, tail: 1 }));
  } : null);
  windowFrame(ctx, crashed);
  warmSpill(ctx);
  // the stack: donkey, dog on his back, cat on the dog, rooster on top
  const base = 124;
  const order = ['tom', 'newton', 'simba', 'skippy'];
  if (!crashed) {
    const sx = 132;
    let feet = base;
    order.forEach((id, i) => {
      const climb = i === 0 ? 1 : ease(seg(t, 1 + i * 2.2, 2.2 + i * 2.2));
      if (climb <= 0) { musician(ctx, id, 60 + i * 20, base, t, { face: 'up', tail: 1 }); return; }
      const lift = t > 14.6 ? ease(seg(t, 14.6, 15.5)) : 0;
      const singing = t > 10 && t < 15.5;
      const x = lerp(60 + i * 20, sx, climb) + lift * (8 + i * 6), f = lerp(base, feet, climb) - lift * (6 + i * 4);
      const r = musician(ctx, id, x, f, t, { face: singing ? 'up' : climb < 1 ? 'happy' : 'side', mouth: singing && Math.floor(t * 6 + i) % 2 ? (i === 3 ? 'meow' : 'yawn') : null, tail: 1 });
      feet = r.y + 3;
      if (singing) notes(ctx, r.x + 20, r.y + 2, t + i, 2, ['#ffd36a', '#9fd0ff', '#f6b8c8', '#ffffff'][i]);
    });
  } else {
    // glass flies, robbers flee out of the door and away to the left
    for (let i = 0; i < 14; i++) {
      const a = t - 15.5;
      if (a > 1.2) break;
      const gx = WIN.x + WIN.w / 2 + (hash(i) - 0.5) * 60 * a * 2, gy = WIN.y + 20 + (hash(i + 9) - 0.7) * 40 * a + a * a * 60;
      rect(ctx, gx, gy, 2, 1, '#cfe6ff');
    }
    for (let i = 0; i < 3; i++) {
      const a = seg(t, 16.2 + i * 0.4, 21 + i * 0.4);
      if (a > 0 && a < 1) robber(ctx, lerp(70, -40, a), 112, t, { pose: 'walk', flip: true, rate: 18 });
    }
  }
  ctx.restore();
}

// ---------- B9. The robber returns ----------
function sceneReturn(ctx, t) {
  ctx.drawImage(layer('cottage-in', W, H, cottageInside), 0, 0);
  fire(ctx, t * 0.3, 30, 100, 20);
  const feet = 116;
  // where everyone sleeps
  const simba = musician(ctx, 'simba', 70, feet, t, { face: t > 9 && t < 11 ? 'side' : 'open', tail: 0 });
  musician(ctx, 'newton', 176, feet, t, { face: t > 13 && t < 15 ? 'up' : 'blink', mouth: t > 13 && t < 14.5 && Math.floor(t * 6) % 2 ? 'meow' : null, tail: 1 });
  musician(ctx, 'tom', 200, feet, t, { face: t > 15.5 && t < 17 ? 'side' : 'blink', tail: 0 });
  musician(ctx, 'skippy', 120, 12, t, { face: t > 17 ? 'up' : 'blink', mouth: t > 17 && t < 20 && Math.floor(t * 4) % 2 ? 'meow' : null, tail: 1 });
  // the robber creeps in from the right towards the "coals"
  let rx, ry = feet, rflip = true, rate = 5;
  if (t < 9) rx = walkTo(t, 0, 9, 250, 92);
  else if (t < 11) { rx = 92; ry = feet - Math.round(Math.sin(seg(t, 9.2, 10.4) * Math.PI) * 10); }
  else if (t < 16) { rx = walkTo(t, 11, 16, 92, 196); rflip = false; rate = 16; }
  else { const k = seg(t, 16, 17.5); rx = lerp(196, 260, k); ry = feet - Math.sin(k * Math.PI) * 50 - k * 20; rflip = false; rate = 20; }
  if (rx < 250) robber(ctx, rx, ry, t, { pose: 'walk', flip: rflip, rate });
  if (t > 9.3 && t < 10.6) for (let k = 0; k < 3; k++) pline(ctx, rx + 6 + k * 3, ry - 14, rx + 10 + k * 3, ry - 6, '#ffffff');
  if (t > 13.4 && t < 14) sparkle(ctx, 186, feet - 4, 2);
  if (t > 16 && t < 16.4) sparkle(ctx, 206, feet - 10, 3, '#ffd36a');
  // the dark
  ctx.globalAlpha = 0.62;
  rect(ctx, 0, 0, W, H, '#0a0612');
  ctx.globalAlpha = 1;
  ctx.globalAlpha = 0.5;
  ctx.drawImage(layer('fireglow', W, H, (c, w, h) => glowLayer(c, w, h, 52, 92, 140, 'rgba(255,170,90,0.07)')), 0, 0);
  ctx.globalAlpha = 1;
  // Simba's eyes glow like coals
  if (t < 9.2 || t > 10.6) {
    rect(ctx, simba.x + 4, simba.y + 8, 2, 1, '#ffd84a');
    rect(ctx, simba.x + 12, simba.y + 8, 2, 1, '#ffd84a');
  }
  if (t > 9.2 && t < 9.5) { ctx.globalAlpha = 0.5; rect(ctx, 0, 0, W, H, '#fff6e0'); ctx.globalAlpha = 1; }
}

// ---------- B10. Home at last ----------
function sceneBEnd(ctx, t) {
  ctx.drawImage(layer('cottage-in', W, H, cottageInside), 0, 0);
  fire(ctx, t, 30, 100, 44);
  const feet = 117;
  ['tom', 'newton', 'simba', 'skippy'].forEach((id, i) => {
    const sing = Math.floor(t * 2 + i * 0.5) % 2;
    const r = musician(ctx, id, 110 + i * 26, feet, t, { face: blinkAt(t, i + 20) ? 'blink' : 'happy', mouth: sing ? 'meow' : null, tail: i % 2, flip: i > 1 });
    if (sing && t < 20) notes(ctx, r.x + 10, r.y - 2, t + i, 1, ['#ffd36a', '#9fd0ff', '#f6b8c8', '#ffffff'][i]);
  });
  ctx.globalAlpha = 0.75 + 0.25 * Math.sin(t * 9) * Math.sin(t * 5.3);
  ctx.drawImage(layer('fireglow', W, H, (c, w, h) => glowLayer(c, w, h, 52, 92, 140, 'rgba(255,170,90,0.07)')), 0, 0);
  ctx.globalAlpha = 1;
  ctx.drawImage(layer('vig-night', W, H, (c, w, h) => vignette(c, w, h, 'rgba(14,8,18,0.22)')), 0, 0);
  const k = stepAlpha(seg(t, 21, 23));
  if (k > 0) {
    ctx.globalAlpha = k;
    rect(ctx, 0, 0, W, H, '#170f1c');
    ctx.globalAlpha = stepAlpha(seg(t, 23, 24.5));
    words(ctx, 'The End', W / 2, H / 2 - 4, 22, '#f2e2b6');
    ctx.globalAlpha = 1;
  }
}

export const SCENES = [
  { id: 'title', name: 'Once upon a time', dur: 12, draw: sceneBTitle,
    captions: [[4, 12, 'This is the story of four old friends who set off to become musicians.']] },
  { id: 'donkey', name: 'The donkey', dur: 24, draw: sceneDonkey,
    captions: [
      [0, 8, 'Once there was a donkey who had carried sacks to the mill for many long years.'],
      [8, 16, 'Now he was old and tired, and his master had no more use for him.'],
      [16, 24, '“I shall go to Bremen,” said the donkey, “and be a town musician.”'],
    ] },
  { id: 'dog', name: 'The dog', dur: 24, draw: sceneDog,
    captions: [
      [0, 7.5, 'Along the road he found an old hound lying in the grass, panting.'],
      [7.5, 16, '“I’m too old to hunt,” said the dog, “so my master wants rid of me.”'],
      [16, 24, '“Come with me to Bremen,” said the donkey. “You can play the drum.”'],
    ] },
  { id: 'cat', name: 'The cat', dur: 22, draw: sceneCat,
    captions: [
      [0, 8, 'Soon they came upon a cat sitting on a wall, with a face like three rainy days.'],
      [8, 15, '“I would rather sit by the fire than chase mice,” he said, “and now nobody wants me.”'],
      [15, 22, '“Come to Bremen,” they said. “You know all about night music.”'],
    ] },
  { id: 'rooster', name: 'The rooster', dur: 22, draw: sceneRooster,
    captions: [
      [0, 7.5, 'Then they passed a farmyard, where a rooster was crowing with all his might.'],
      [7.5, 15, '“The cook wants me in the soup tomorrow,” he cried, “so I’m crowing while I can.”'],
      [15, 22, '“Come with us,” said the donkey. “Anything is better than soup.”'],
    ] },
  { id: 'forest', name: 'The forest', dur: 26, draw: sceneForest,
    captions: [
      [0, 9, 'Bremen was too far to reach in one day, so they stopped in a forest for the night.'],
      [9, 18, 'The rooster flew to the top of a tree, and far away he saw a little light.'],
      [18, 26, '“A house!” he called. “Where there’s a light, there may be supper.”'],
    ] },
  { id: 'robbers', name: 'The robbers', dur: 30, draw: sceneRobbers,
    captions: [
      [0, 10, 'Through the window they saw a band of robbers, feasting at a table piled with gold.'],
      [10, 20, '“That’s the place for us,” said the dog. “But how do we get them out?”'],
      [20, 30, 'So the four friends put their heads together and made a plan.'],
    ] },
  { id: 'concert', name: 'The concert', dur: 25, draw: sceneConcert,
    captions: [
      [0, 9.5, 'The donkey stood under the window, the dog climbed on his back, the cat on the dog, and the rooster on top.'],
      [9.5, 15.5, 'Then, all together, they began to make their music.'],
      [15.5, 25, 'The robbers thought a monster had come for them, and they ran into the woods as fast as they could go.'],
    ] },
  { id: 'return', name: 'The robber returns', dur: 27, draw: sceneReturn,
    captions: [
      [0, 9, 'Late that night, one robber crept back to see if the house was empty.'],
      [9, 18, 'He took the cat’s glowing eyes for coals, and the cat flew at his face.'],
      [18, 27, 'The dog bit him, the donkey kicked him, and the rooster crowed. The robber ran, and never came back.'],
    ] },
  { id: 'end', name: 'Home at last', dur: 28, draw: sceneBEnd,
    captions: [
      [0, 10, 'The four musicians liked the little house so much that they never wanted to leave.'],
      [10, 20, 'And as far as anyone knows, they never did get to Bremen.'],
    ] },
];
let acc = 0;
for (const s of SCENES) { s.start = acc; acc += s.dur; }
export const TOTAL = acc;
