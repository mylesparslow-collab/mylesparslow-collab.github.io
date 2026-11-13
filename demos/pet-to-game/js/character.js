// Loads a pet's character.glb (contract in docs/CONTRACT.md) and makes it playable:
// clip-name mapping with Sphynx fallbacks, scale/ground normalisation, defensive root-motion stripping,
// and a small crossfading animation state machine.
import * as THREE from 'three';
import { addFurShells } from './fur.js';

// contract name -> Sphynx clip name (docs/CONTRACT.md) + loose regex fallbacks
const CLIP_FALLBACK = {
  idle: ['Cat_Idle', /idle/i],
  walk: ['Cat_Walk', /walk/i],
  run: ['Cat_Gallop_Run', /gallop|run/i],
  jump: ['Cat_Leap_Jump', /jump|leap/i],
  trot: ['Cat_Trot', /trot/i],
  pounce: ['Cat_Pounce_Attack', /pounce/i],
  stalk: ['Cat_Stalk_Hunt', /stalk/i],
  lick: ['Cat_Lick_Paw', /lick/i],
};
const ROOT_RE = /hips|pelvis|root/i;
// The shoulder joint sits ~3 cm under the withers, so a 0.22 m joint height gives ~0.25 m at the shoulder.
export const TARGET_SHOULDER = 0.22; // metres

function mapClips(clips) {
  const out = {};
  for (const [name, [sphynx, re]] of Object.entries(CLIP_FALLBACK)) {
    out[name] = clips.find((c) => c.name === name) || clips.find((c) => c.name === sphynx) || clips.find((c) => re.test(c.name)) || null;
  }
  if (!out.walk) out.walk = out.trot || out.run;
  if (!out.run) out.run = out.trot || out.walk;
  if (!out.idle) out.idle = out.walk;
  if (!out.jump) out.jump = out.pounce || out.idle;
  return out;
}

// Remove horizontal (world XZ) travel from root/hips position tracks. Returns metres-per-unit-scale
// travel speed (horizontal distance first->last keyframe / duration) measured before stripping.
function stripRootMotion(scene, clip) {
  let travel = 0;
  for (const tr of clip.tracks) {
    if (!tr.name.endsWith('.position')) continue;
    const nodeName = THREE.PropertyBinding.parseTrackName(tr.name).nodeName;
    if (!ROOT_RE.test(nodeName)) continue;
    const node = scene.getObjectByName(nodeName);
    if (!node || !node.parent) continue;
    const m3 = new THREE.Matrix3().setFromMatrix4(node.parent.matrixWorld);
    const inv = m3.clone().invert();
    const v = tr.values, n = v.length / 3;
    const d = new THREE.Vector3(), wl = new THREE.Vector3();
    for (let i = 0; i < n; i++) {
      d.set(v[i * 3] - v[0], v[i * 3 + 1] - v[1], v[i * 3 + 2] - v[2]).applyMatrix3(m3);
      if (i === n - 1) wl.copy(d);
      d.x = 0; d.z = 0; d.applyMatrix3(inv);
      v[i * 3] = v[0] + d.x; v[i * 3 + 1] = v[1] + d.y; v[i * 3 + 2] = v[2] + d.z;
    }
    if (clip.duration > 0) travel = Math.max(travel, Math.hypot(wl.x, wl.z) / clip.duration);
  }
  return travel;
}

export async function loadCharacter(url, gltfLoader, { fur = true, touch = false } = {}) {
  const gltf = await gltfLoader.loadAsync(url);
  const scene = gltf.scene;
  const wrapper = new THREE.Group();
  wrapper.add(scene);
  scene.updateMatrixWorld(true);
  const clips = mapClips(gltf.animations);
  if (!clips.idle) throw new Error('character.glb has no usable animation clips');

  // defensive root-motion strip (in pre-scale units; speeds are scaled after normalisation)
  const rawTravel = new Map();
  for (const c of new Set(Object.values(clips))) if (c) rawTravel.set(c, stripRootMotion(scene, c));

  // pose at idle frame 0 for measuring
  const mixer = new THREE.AnimationMixer(scene);
  const idleAct = mixer.clipAction(clips.idle); idleAct.play(); mixer.update(0);
  wrapper.updateMatrixWorld(true);

  const findBone = (re) => { let f = null; scene.traverse((o) => { if (!f && o.isBone && re.test(o.name)) f = o; }); return f; };
  const wp = (o) => o.getWorldPosition(new THREE.Vector3());
  // facing correction: contract says +Z; correct if the head is clearly elsewhere
  const head = findBone(/head/i), hips = findBone(/hips|pelvis/i);
  if (head && hips) {
    const d = wp(head).sub(wp(hips));
    const yaw = Math.atan2(d.x, d.z);
    if (Math.hypot(d.x, d.z) > 0.05 && Math.abs(yaw) > 0.6) { scene.rotation.y = -yaw; wrapper.updateMatrixWorld(true); }
  }

  const box = new THREE.Box3();
  const skinned = [];
  scene.traverse((o) => { if (o.isSkinnedMesh) { skinned.push(o); o.frustumCulled = false; } });
  for (const m of skinned) box.union(new THREE.Box3().setFromObject(m, true));
  const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
  // shoulder height: front upper-arm / shoulder joint above the lowest point
  const sh = findBone(/(upper_?arm|shoulder|clavicle).*(\.|_)?l\b|upper_?arm.?l|arm.?l/i) || findBone(/upper_?arm|shoulder|clavicle/i);
  let shoulderH = sh ? wp(sh).y - box.min.y : size.y * 0.78;
  if (!(shoulderH > size.y * 0.35 && shoulderH < size.y)) shoulderH = size.y * 0.78;
  const k = TARGET_SHOULDER / shoulderH;
  wrapper.scale.setScalar(k);
  scene.position.set(-centre.x, -box.min.y, -centre.z);
  wrapper.updateMatrixWorld(true);

  scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = false; } });
  let shellCount = 0;
  if (fur) shellCount = addFurShells(scene, { shells: touch ? 5 : 10, lengthObj: 0.008 / k });

  // actions
  const actions = {};
  for (const [name, clip] of Object.entries(clips)) if (clip) actions[name] = mixer.clipAction(clip);
  for (const a of Object.values(actions)) { a.stop(); a.enabled = true; }
  actions.jump.setLoop(THREE.LoopOnce, 1); actions.jump.clampWhenFinished = true;
  if (actions.lick && actions.lick !== actions.idle) { actions.lick.setLoop(THREE.LoopOnce, 1); actions.lick.clampWhenFinished = true; }
  if (actions.pounce && actions.pounce !== actions.idle) { actions.pounce.setLoop(THREE.LoopOnce, 1); actions.pounce.clampWhenFinished = true; }

  // natural ground speeds (m/s) from the clips' own root motion, if it had any
  const nat = (clip, fallback) => { const t = (rawTravel.get(clip) || 0) * k; return t > 0.15 ? t : fallback; };
  const speeds = { walk: nat(clips.walk, 0.7), run: nat(clips.run, 2.3) };

  const heightWorld = size.y * k;
  return { root: wrapper, mixer, actions, clips, speeds, shellCount, shoulder: shoulderH * k, height: heightWorld, scale: k };
}

// ---------------------------------------------------------------- animation state machine
export class CatAnimator {
  constructor(ch) {
    this.ch = ch; this.mixer = ch.mixer; this.a = ch.actions;
    this.state = null; this.cur = null;
    this.fade = 0.18; this.idleT = 0; this.lickT = 0;
    this.set('idle');
  }
  set(state, { timeScale = 1, fade = this.fade } = {}) {
    const next = this.a[state];
    if (!next) return;
    if (state === this.state) { next.timeScale = timeScale; return; }
    const prev = this.cur;
    next.enabled = true; next.setEffectiveWeight(1); next.timeScale = timeScale;
    if (state === 'jump' || state === 'lick' || state === 'pounce') next.reset();
    if (prev && prev !== next) {
      if ((this.state === 'walk' || this.state === 'run') && (state === 'walk' || state === 'run')) {
        next.time = (prev.time / prev.getClip().duration) * next.getClip().duration; // keep gait phase
        next.play(); next.crossFadeFrom(prev, fade, false);
      } else { next.play(); prev.fadeOut(fade); next.fadeIn(fade); }
    } else { next.reset().fadeIn(fade).play(); }
    this.state = state; this.cur = next;
  }
  // ground: bool; speed: horizontal m/s; vy: vertical velocity
  update(dt, { ground, speed, vy }) {
    const sp = this.ch.speeds;
    if (!ground) {
      this.idleT = 0;
      const clip = this.a.jump.getClip();
      this.set('jump', { timeScale: THREE.MathUtils.clamp(clip.duration / 0.85, 0.7, 2.2), fade: 0.12 });
    } else if (speed < 0.12) {
      this.idleT += dt;
      if (this.state === 'lick' && this.cur.isRunning()) { /* let the lick finish */ }
      else if (this.idleT > 7 && this.a.lick && this.a.lick !== this.a.idle) { this.set('lick', { fade: 0.25 }); this.idleT = 0; }
      else this.set('idle', { fade: 0.25 });
    } else {
      this.idleT = 0;
      const runNow = this.state === 'run' ? speed > (sp.walk + sp.run) * 0.42 : speed > (sp.walk + sp.run) * 0.55;
      if (runNow) this.set('run', { timeScale: THREE.MathUtils.clamp(speed / sp.run, 0.6, 1.6) });
      else this.set('walk', { timeScale: THREE.MathUtils.clamp(speed / sp.walk, 0.4, 1.7) });
    }
    this.mixer.update(dt);
  }
  get gait() { return this.state; }
}
