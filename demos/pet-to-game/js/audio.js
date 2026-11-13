// Web Audio wrapper. Only plays recorded samples (sfx/*.mp3); unlocked on the first user gesture.
import { SFX } from './assets.js';

export class GameAudio {
  constructor() {
    this.ctx = null; this.buffers = {}; this.master = null; this.muted = false;
    this.loading = null; this.loops = {}; this.last = {};
  }
  async unlock() {
    if (this.ctx) { if (this.ctx.state === 'suspended') this.ctx.resume().catch(() => {}); return; }
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      this.ctx = new AC();
      this.master = this.ctx.createGain(); this.master.gain.value = this.muted ? 0 : 1; this.master.connect(this.ctx.destination);
      if (this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
      this.loading = Promise.all(Object.entries(SFX).map(async ([k, url]) => {
        try {
          const r = await fetch(url); const ab = await r.arrayBuffer();
          this.buffers[k] = await new Promise((res, rej) => this.ctx.decodeAudioData(ab, res, rej));
        } catch (e) { /* missing sound is not fatal */ }
      }));
      await this.loading;
      this.startLoop('ambience', 0.5);
    } catch (e) { /* audio is optional */ }
  }
  setMuted(m) {
    this.muted = m;
    if (this.master) this.master.gain.value = m ? 0 : 1;
  }
  play(name, { vol = 1, rate = 1, jitter = 0.06, cooldown = 0 } = {}) {
    if (!this.ctx || !this.buffers[name]) return;
    const now = this.ctx.currentTime;
    if (cooldown && now - (this.last[name] || -9) < cooldown) return;
    this.last[name] = now;
    const src = this.ctx.createBufferSource(); src.buffer = this.buffers[name];
    src.playbackRate.value = rate * (1 + (Math.random() * 2 - 1) * jitter);
    const g = this.ctx.createGain(); g.gain.value = vol;
    src.connect(g); g.connect(this.master); src.start();
  }
  // Seamless loop by overlapping crossfaded copies of a short recording.
  startLoop(name, vol) {
    const buf = this.buffers[name];
    if (!this.ctx || !buf || this.loops[name]) return;
    const out = this.ctx.createGain(); out.gain.value = 0; out.connect(this.master);
    const L = { out, vol, level: 0, timer: null };
    const xf = Math.min(0.8, buf.duration * 0.25);
    const spawn = () => {
      const t = this.ctx.currentTime;
      const src = this.ctx.createBufferSource(); src.buffer = buf;
      const g = this.ctx.createGain();
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(1, t + xf);
      g.gain.setValueAtTime(1, t + buf.duration - xf); g.gain.linearRampToValueAtTime(0, t + buf.duration);
      src.connect(g); g.connect(out); src.start(t);
      L.timer = setTimeout(spawn, (buf.duration - xf) * 1000);
    };
    spawn();
    this.loops[name] = L;
    this.setLoopLevel(name, 1);
  }
  setLoopLevel(name, level) {
    const L = this.loops[name];
    if (!L) return;
    L.level = level;
    L.out.gain.cancelScheduledValues(this.ctx.currentTime);
    L.out.gain.linearRampToValueAtTime(L.vol * level, this.ctx.currentTime + 0.6);
  }
  startPurr() { if (!this.loops.purr) { this.startLoop('purr', 0.5); this.setLoopLevel('purr', 0); } }
}
