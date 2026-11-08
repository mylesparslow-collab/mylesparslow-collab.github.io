// The film's clock, controls and captions. ?t=SECONDS opens at that moment; ?still renders one frame.
import { SCENES, TOTAL } from './scenes.js';
import { startAudio, tickAudio, hushAudio } from './audio.js';

const fontsReady = Promise.all(['20px "Jacquarda Bastarda 9"', '8px "Pixelify Sans"'].map((f) => document.fonts.load(f).catch(() => null)));
const cv = document.getElementById('plate');
const ctx = cv.getContext('2d');
const $ = (id) => document.getElementById(id);
const q = new URLSearchParams(location.search);

let t = Math.min(TOTAL - 0.01, parseFloat(q.get('t') || '0') || 0);
let playing = false;
let last = performance.now();

const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const sceneAt = (time) => SCENES.find((s) => time >= s.start && time < s.start + s.dur) ?? SCENES[SCENES.length - 1];

// chapter strip
const chapEls = SCENES.map((s) => {
  const b = document.createElement('button');
  b.className = 'chap';
  b.type = 'button';
  b.style.flex = String(s.dur);
  b.title = s.name;
  b.setAttribute('aria-label', `Jump to ${s.name}`);
  b.innerHTML = '<i></i>';
  b.addEventListener('click', (e) => {
    const r = b.getBoundingClientRect();
    seek(s.start + ((e.clientX - r.left) / r.width) * s.dur);
  });
  $('chapters').appendChild(b);
  return b;
});

let lastCaption = null;
function render() {
  const s = sceneAt(t);
  const lt = t - s.start;
  ctx.setTransform(2, 0, 0, 2, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.globalAlpha = 1;
  s.draw(ctx, lt);
  // a short fade between scenes
  const edge = Math.min(lt, s.dur - lt);
  if (edge < 0.5 && t > 0.5 && t < TOTAL - 0.5) {
    ctx.globalAlpha = 1 - edge / 0.5;
    ctx.fillStyle = '#170f1c';
    ctx.fillRect(0, 0, 240, 135);
    ctx.globalAlpha = 1;
  }
  const cap = s.captions.find(([a, b]) => lt >= a && lt < b);
  const text = cap ? cap[2] : '';
  if (text !== lastCaption) { $('caption').textContent = text; lastCaption = text; }
  $('chapname').textContent = s.name;
  $('time').textContent = `${fmt(t)} / ${fmt(TOTAL)}`;
  SCENES.forEach((sc, i) => {
    const f = Math.max(0, Math.min(1, (t - sc.start) / sc.dur));
    chapEls[i].firstChild.style.width = f * 100 + '%';
  });
}

function seek(time) {
  t = Math.max(0, Math.min(TOTAL - 0.01, time));
  hushAudio(t);
  render();
}
function setPlaying(p) {
  playing = p;
  $('play').innerHTML = p ? '&#10074;&#10074;' : '&#9654;';
  $('play').setAttribute('aria-label', p ? 'Pause' : 'Play');
  if (p) startAudio(); else hushAudio(t);
}

function loop(now) {
  if (playing) {
    t += Math.min(0.1, (now - last) / 1000);
    if (t >= TOTAL) { t = TOTAL - 0.01; setPlaying(false); }
  }
  last = now;
  tickAudio(t, playing);
  render();
  requestAnimationFrame(loop);
}

$('begin').addEventListener('click', () => { $('start').hidden = true; setPlaying(true); });
$('play').addEventListener('click', () => { $('start').hidden = true; setPlaying(!playing); });
window.addEventListener('keydown', (e) => {
  if (e.key === ' ' && e.target === document.body) { e.preventDefault(); $('start').hidden = true; setPlaying(!playing); }
  if (e.key === 'ArrowRight') seek(t + 5);
  if (e.key === 'ArrowLeft') seek(t - 5);
});

window.film = { get t() { return t; }, get playing() { return playing; }, seek };

if (q.has('still')) {
  $('start').hidden = true;
  fontsReady.then(() => { render(); document.body.dataset.ready = '1'; });
} else {
  requestAnimationFrame(loop);
}
