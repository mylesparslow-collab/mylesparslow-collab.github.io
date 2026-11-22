// Builds themed/n/strip.jpg: one row of film-strip thumbnails, 128x80 px each (shown at 64x40), one per frame,
// in frame order. Projects without a lead image get a typographic cell (frame number and title).
// Usage, with the static server running on the repo: node themed/n/make_strip.mjs [base-url]
import { execSync } from 'child_process';
import { pathToFileURL } from 'url';
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'fs';
import { homedir } from 'os';
let chromium;
const cands = () => { const o = []; try { o.push(execSync('npm root -g').toString().trim() + '/playwright'); } catch {} const n = homedir() + '/.npm/_npx'; if (existsSync(n)) for (const d of readdirSync(n)) o.push(`${n}/${d}/node_modules/playwright`); return o.filter(d => existsSync(d + '/index.mjs')); };
try { ({ chromium } = await import('playwright')); } catch { for (const d of cands()) { try { ({ chromium } = await import(pathToFileURL(d + '/index.mjs').href)); break; } catch {} } }
const base = process.argv[2] || 'http://localhost:8898';
const here = new URL('.', import.meta.url).pathname;
const frames = JSON.parse(readFileSync(here + 'frames.json', 'utf8'));
const b = await chromium.launch();
const p = await b.newPage();
await p.goto(base + '/themed/n/frames.json');
const url = await p.evaluate(async ({ frames, base }) => {
  const f = new FontFace('SSC', 'url(' + base + '/themed/n/fonts/SofiaSansCondensed.woff2)', { weight: '1 1000' });
  await f.load(); document.fonts.add(f);
  const W = 128, H = 80, c = document.createElement('canvas'); c.width = W * frames.length; c.height = H;
  const x = c.getContext('2d'); x.imageSmoothingQuality = 'high';
  for (let i = 0; i < frames.length; i++) {
    const fr = frames[i], ox = i * W;
    x.fillStyle = '#fbfbf9'; x.fillRect(ox, 0, W, H);
    if (fr.src) {
      const im = new Image(); im.src = base + '/' + fr.src; await im.decode();
      const s = Math.max(W / im.naturalWidth, H / im.naturalHeight), w = im.naturalWidth * s, h = im.naturalHeight * s;
      x.drawImage(im, ox + (W - w) / 2, (H - h) / 2, w, h);
    } else {
      x.fillStyle = '#151515'; x.font = '800 54px SSC'; x.textBaseline = 'alphabetic'; x.fillText(String(fr.g).padStart(3, '0'), ox + 8, 56);
      x.font = '700 14px SSC'; let t = fr.title; while (x.measureText(t).width > W - 16 && t.length > 3) t = t.slice(0, -2);
      x.fillText(t === fr.title ? t : t + '…', ox + 8, 74);
    }
  }
  return c.toDataURL('image/jpeg', 0.7);
}, { frames, base });
writeFileSync(here + 'strip.jpg', Buffer.from(url.split(',')[1], 'base64'));
console.log('strip.jpg', frames.length, 'cells');
await b.close();
