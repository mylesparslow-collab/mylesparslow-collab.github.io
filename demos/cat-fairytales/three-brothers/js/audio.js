// Web Audio driven by the film clock: one-shots fire as the clock passes them, while beds, music and
// narration are spans that pick up at the right offset after a pause or a seek.
import { SCENES } from './scenes.js';
import { CUES, MUSIC } from './cues.js';

let ac = null, master = null;
const buffers = new Map();
const spans = []; // { from, to, name, vol, loop, fade, offset, src, gain }
const shots = []; // { at, name, vol }
let lastT = 0;

function build(narration) {
  for (const s of SCENES) {
    for (const c of CUES[s.id] || []) {
      if ('at' in c) shots.push({ ...c, at: s.start + c.at });
      else spans.push({ ...c, from: s.start + c.from, to: s.start + c.to });
    }
    s.captions.forEach(([a, b], i) => {
      const n = narration[`${s.id}-${i}`];
      if (n) spans.push({ from: s.start + a + 0.15, to: s.start + a + 0.15 + n.dur, name: `voice:${s.id}-${i}`, file: n.file, vol: 1, loop: false, fade: 0.05, offset: 0 });
    });
  }
  for (const m of MUSIC) spans.push({ ...m });
}

async function load(name, file) {
  if (buffers.has(name)) return;
  buffers.set(name, null);
  try {
    const res = await fetch(file);
    buffers.set(name, await ac.decodeAudioData(await res.arrayBuffer()));
  } catch { /* a missing sound just stays silent */ }
}

export async function startAudio() {
  if (ac) { ac.resume(); return; }
  ac = new (window.AudioContext || window.webkitAudioContext)();
  master = ac.createGain();
  master.gain.value = 0.9;
  master.connect(ac.destination);
  let narration = {};
  try { narration = await (await fetch('voice/manifest.json')).json(); } catch { /* no narration yet */ }
  build(narration);
  const names = new Set([...shots.map((s) => s.name), ...spans.map((s) => s.name)]);
  await Promise.all([...names].map((n) => {
    const sp = spans.find((s) => s.name === n && s.file);
    return load(n, sp ? sp.file : `audio/${n}.mp3`);
  }));
}

function stopSpan(s, soft = 0.08) {
  if (!s.src) return;
  const now = ac.currentTime;
  s.gain.gain.cancelScheduledValues(now);
  s.gain.gain.setValueAtTime(s.gain.gain.value, now);
  s.gain.gain.linearRampToValueAtTime(0, now + soft);
  s.src.stop(now + soft + 0.02);
  s.src = null;
}

function startSpan(s, t) {
  const buf = buffers.get(s.name);
  if (!buf) return;
  let off = s.offset + (t - s.from);
  if (s.loop) off %= buf.duration;
  else if (off >= buf.duration) return;
  const src = ac.createBufferSource();
  src.buffer = buf;
  src.loop = s.loop;
  const g = ac.createGain();
  src.connect(g).connect(master);
  const now = ac.currentTime;
  const into = t - s.from, left = s.to - t;
  const level = s.vol * Math.min(1, into / s.fade + 0.02, left / s.fade);
  g.gain.setValueAtTime(Math.max(0, level), now);
  if (into < s.fade) g.gain.linearRampToValueAtTime(s.vol, now + (s.fade - into));
  const fadeAt = Math.max(0, left - s.fade);
  g.gain.setValueAtTime(s.vol, now + fadeAt + 0.001);
  g.gain.linearRampToValueAtTime(0, now + left);
  src.start(now, Math.max(0, off));
  src.stop(now + left + 0.05);
  src.onended = () => { if (s.src === src) s.src = null; };
  s.src = src;
  s.gain = g;
}

// Called every frame by the player.
export function tickAudio(t, playing) {
  if (!ac || !spans.length) return;
  if (!playing) { lastT = t; return; }
  for (const s of spans) {
    const active = t >= s.from && t < s.to;
    if (active && !s.src) startSpan(s, t);
    else if (!active && s.src) stopSpan(s);
  }
  if (t > lastT && t - lastT < 0.5) {
    for (const s of shots) {
      if (s.at > lastT && s.at <= t) {
        const buf = buffers.get(s.name);
        if (!buf) continue;
        const src = ac.createBufferSource();
        src.buffer = buf;
        const g = ac.createGain();
        g.gain.value = s.vol;
        src.connect(g).connect(master);
        src.start();
      }
    }
  }
  lastT = t;
}

// Pause or seek: silence everything; spans restart at the right offset on the next playing tick.
export function hushAudio(t) {
  if (!ac) return;
  for (const s of spans) stopSpan(s, 0.05);
  lastT = t;
}
