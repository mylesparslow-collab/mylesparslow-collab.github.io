// Detailed cats: every sprite grid is redrawn at double resolution, then given the detail a
// bigger sprite can hold: rounded edges, rim light and shadow, fur texture, two-tone eyes with a
// catchlight, darker inner ears, whiskers, and fluffy edges for long-haired cats.
// Grids use the same palette keys as sprites.js, plus a few extra shades:
//   B fur highlight   L shaded cream   E dark iris   P dark pink   O soft outline   W whiskers

const BODY = 'bsmB';
const LIGHT = 'lcCa';

// Scale2x on palette keys: doubles the grid and rounds off diagonal staircases.
export function scale2x(grid) {
  const h = grid.length, w = Math.max(...grid.map((r) => r.length));
  const at = (x, y) => (grid[Math.max(0, Math.min(h - 1, y))][Math.max(0, Math.min(w - 1, x))] ?? '.');
  const out = Array.from({ length: h * 2 }, () => new Array(w * 2).fill('.'));
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const P = at(x, y), A = at(x, y - 1), D = at(x, y + 1), C = at(x - 1, y), B = at(x + 1, y);
      let e0 = P, e1 = P, e2 = P, e3 = P;
      // Round the silhouette and big shapes; keep eyes, noses and mouths exactly as drawn.
      if (A !== D && C !== B && !'ekhpq'.includes(P)) {
        if (C === A && !'ekhq'.includes(A)) e0 = A;
        if (A === B && !'ekhq'.includes(B)) e1 = B;
        if (D === C && !'ekhq'.includes(C)) e2 = C;
        if (B === D && !'ekhq'.includes(D)) e3 = D;
      }
      out[y * 2][x * 2] = e0;
      out[y * 2][x * 2 + 1] = e1;
      out[y * 2 + 1][x * 2] = e2;
      out[y * 2 + 1][x * 2 + 1] = e3;
    }
  }
  return out;
}

// pose: 'sit' | 'walk' | 'sleep'. fluff: long hair. Returns rows of palette keys at double size.
export function detailGrid(grid, { pose = 'sit', fluff = false, face = 'open' } = {}) {
  const g = scale2x(grid);
  const H = g.length, W = g[0].length;
  const src = g.map((r) => r.slice());
  const was = (x, y) => (y < 0 || y >= H || x < 0 || x >= W ? '.' : src[y][x]);
  const edge = (ch) => ch === 'o' || ch === '.';

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const ch = src[y][x];
      if (ch === 'b') {
        // Shadow on the right and underneath, light on the top-left: the cat gets some volume.
        if (edge(was(x + 1, y)) || edge(was(x + 2, y)) || edge(was(x, y + 1))) g[y][x] = 's';
        else if ((edge(was(x, y - 1)) || edge(was(x - 1, y))) && x < W * 0.55 && y < H * 0.75) g[y][x] = 'B';
        // Where fur meets a white or cream patch, the edge zig-zags like real fur.
        else if (y % 4 < 2 && (LIGHT.includes(was(x + 1, y)) || LIGHT.includes(was(x - 1, y)))) g[y][x] = LIGHT.includes(was(x + 1, y)) ? was(x + 1, y) : was(x - 1, y);
        // The shadow's edge is ragged too, so the shading reads as fur rather than a band.
        else if (y % 4 === 1 && was(x + 1, y) === 'b' && (edge(was(x + 2, y)) || edge(was(x + 3, y)))) g[y][x] = 's';
      } else if (LIGHT.includes(ch)) {
        if (edge(was(x + 1, y)) || edge(was(x, y + 1))) g[y][x] = 'L';
      } else if (ch === 'o') {
        // A softer outline along the top of the head and back, where the light hits.
        if (was(x, y + 1) === 'b' && y < H * 0.5) g[y][x] = 'O';
      } else if (ch === 'e') {
        // Two-tone irises: darker at the bottom.
        if (was(x, y + 1) !== 'e' && was(x, y - 1) === 'e') g[y][x] = 'E';
      } else if (ch === 'h') {
        // One sharp catchlight per eye.
        if (was(x - 1, y) === 'h' || was(x, y - 1) === 'h') g[y][x] = 'k';
      } else if (ch === 'p') {
        if (was(x, y + 1) !== 'p' && was(x, y - 1) === 'p') g[y][x] = 'P';
      }
    }
  }

  // Eyes: a 4x4 eye gets a proper cat eye, a slit pupil with a catchlight in a two-tone iris.
  if (pose === 'sit' && (face === 'open' || face === 'happy' && false)) {
    const EYE = ['ekhe', 'ekke', 'EkkE', 'EEEE'];
    for (let y = 0; y < H - 3; y++) {
      for (let x = 0; x < W - 3; x++) {
        if (!'ekh'.includes(src[y][x]) || 'ekh'.includes(was(x - 1, y)) || 'ekh'.includes(was(x, y - 1))) continue;
        let ok = true;
        for (let j = 0; j < 4 && ok; j++) for (let i = 0; i < 4; i++) if (!'ekh'.includes(src[y + j][x + i])) { ok = false; break; }
        if (!ok || 'ekh'.includes(was(x + 4, y))) continue;
        EYE.forEach((row, j) => [...row].forEach((ch, i) => (g[y + j][x + i] = ch)));
      }
    }
  }

  // Toes: little gaps between the toes on each front paw, and a shaped nose.
  for (let y = 1; y < H - 1; y++) {
    for (let x = 1; x < W - 1; x++) {
      if (src[y][x] !== 'a' || was(x, y + 1) !== 'o' || was(x, y - 1) !== 'a') continue;
      let start = x;
      while (src[y][start - 1] === 'a') start--;
      let end = x;
      while (src[y][end + 1] === 'a') end++;
      if (end - start >= 4 && (x - start === 2 || end - x === 2)) g[y][x] = 'L';
    }
  }
  if (pose === 'sit') {
    const row = src[19] || [];
    const L = row.indexOf('p'), R = row.lastIndexOf('p');
    if (L > 0 && R - L >= 3) { g[19][L] = 'l'; g[19][R] = 'l'; }
  }

  // Fluffy cheeks: little tufts sticking out either side of the face.
  if (pose === 'sit') {
    for (const y of [19, 21]) {
      const row = src[y];
      if (!row) continue;
      const left = row.findIndex((c) => c !== '.');
      const right = W - 1 - [...row].reverse().findIndex((c) => c !== '.');
      if (left > 0 && row[left] === 'o') { g[y][left - 1] = 'o'; g[y][left] = 's'; }
      if (right < W - 1 && row[right] === 'o' && right < W * 0.8) { g[y][right + 1] = 'o'; g[y][right] = 's'; }
    }
  }

  // Whiskers from the muzzle of a sitting cat.
  if (pose === 'sit') {
    for (const [row, lift] of [[19, -1], [21, 1]]) {
      const r = src[row];
      if (!r) continue;
      const L = r.indexOf('l'), R = r.lastIndexOf('l');
      if (L < 0) continue;
      for (let i = 1; i <= 5; i++) {
        const y = row + (i > 3 ? lift : 0);
        for (const x of [L - i, R + i]) if ((BODY + 'O').includes(g[y]?.[x] ?? '.') && g[y][x] !== 'O') g[y][x] = 'W';
      }
    }
  }

  // Long hair: ragged tufts along the sides and cheeks.
  if (fluff) {
    for (let y = Math.floor(H * 0.4); y < H - 4; y += 3) {
      const row = src[y];
      const left = row.findIndex((c) => c !== '.');
      const right = W - 1 - [...row].reverse().findIndex((c) => c !== '.');
      for (const [x, dir] of [[left, -1], [right, 1]]) {
        if (x <= 0 || x >= W - 1 || row[x] !== 'o') continue;
        g[y][x + dir] = 'o';
        g[y][x] = 's';
        if (g[y + 1][x + dir] === '.') g[y + 1][x + dir] = 'o';
      }
    }
  }
  return g.map((r) => r.join(''));
}

const hx = (s) => { const v = String(s).replace('#', ''); return [0, 2, 4].map((i) => parseInt(v.slice(i, i + 2), 16) || 0); };
const mix = (a, b, t) => '#' + hx(a).map((v, i) => Math.round(v + (hx(b)[i] - v) * t).toString(16).padStart(2, '0')).join('');
const luma = (c) => { const [r, g, b] = hx(c); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; };

// Adds the extra shades a detailed sprite needs to a cat's palette.
export function detailPalette(pal) {
  const dark = luma(pal.b) < 0.2;
  return {
    ...pal,
    B: mix(pal.b, '#fffaf0', dark ? 0.14 : 0.22),
    L: mix(pal.l, pal.s, 0.35),
    E: mix(pal.e, '#1e1a22', 0.35),
    P: mix(pal.p, '#5a2a3a', 0.3),
    O: mix(pal.o, pal.b, 0.35),
    W: dark ? '#cfc8d6' : '#fffaf0',
  };
}
