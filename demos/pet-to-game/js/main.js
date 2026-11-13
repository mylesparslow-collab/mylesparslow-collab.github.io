import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { CDN, ENV_HDR, DEFAULT_PET } from './assets.js';
import { StaticWorld, CatBody, CAT } from './physics.js';
import { buildRoom, ROOM, CAT_START } from './room.js';
import { loadCharacter, CatAnimator } from './character.js';
import { GameAudio } from './audio.js';
import { Input } from './input.js';

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const GAME_SECONDS = 90;
const SUBSTEP = 1 / 120;
const coarse = matchMedia('(pointer: coarse)').matches;

// ---------------------------------------------------------------- renderer / scene
const canvas = $('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, coarse ? 1.5 : 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.9;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a130e);
const camera = new THREE.PerspectiveCamera(55, 1, 0.05, 30);

const sun = new THREE.DirectionalLight(0xffe2b8, 2.4);
sun.position.set(1.6, 3.4, -3.8); sun.target.position.set(-0.5, 0, 0.6);
sun.castShadow = true;
const sz = coarse ? 1024 : 2048;
sun.shadow.mapSize.set(sz, sz);
Object.assign(sun.shadow.camera, { left: -4.5, right: 4.5, top: 4.5, bottom: -4.5, near: 0.5, far: 12 });
sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.02;
scene.add(sun, sun.target);
scene.add(new THREE.HemisphereLight(0xfff1dd, 0x5a3f2a, 0.5));

function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.fov = w / h < 0.8 ? 68 : 55;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize); resize();

// ---------------------------------------------------------------- loaders
const draco = new DRACOLoader(); draco.setDecoderPath(CDN.draco);
const gltfLoader = new GLTFLoader(); gltfLoader.setDRACOLoader(draco);
// Some prepped models list a texture with no image (empty extensions); drop material references to those.
gltfLoader.register((parser) => ({
  name: 'DropEmptyTextures',
  beforeRoot() {
    const j = parser.json;
    const bad = new Set();
    (j.textures || []).forEach((t, i) => { if (t.source === undefined && !(t.extensions && Object.keys(t.extensions).length)) bad.add(i); });
    if (!bad.size) return null;
    const strip = (o) => {
      for (const k of Object.keys(o)) {
        const v = o[k];
        if (v && typeof v === 'object') { if (typeof v.index === 'number' && /Texture$/.test(k) && bad.has(v.index)) delete o[k]; else strip(v); }
      }
    };
    for (const m of j.materials || []) strip(m);
    return null;
  },
}));
const texLoader = new THREE.TextureLoader();
const glbCache = new Map();
const loadGLB = (url) => { if (!glbCache.has(url)) glbCache.set(url, gltfLoader.loadAsync(url)); return glbCache.get(url); };
const say = (t) => { $('loadMsg').textContent = t; };

// ---------------------------------------------------------------- state
const world = new StaticWorld();
const cat = new CatBody(world);
const audio = new GameAudio();
const input = new Input(canvas);
const state = { mode: 'loading', score: 0, time: GAME_SECONDS, best: 0, knocked: 0 };
let room = null, character = null, animator = null, petName = 'Your cat';
let selPet = null, selName = null; // pet the player is on (glb url + name), carried by the Share link
try { state.best = Number(localStorage.getItem('knockitoff.best')) || 0; } catch (_) { /* storage blocked */ }

const cam = { yaw: 0, pitch: 0.42, dist: 1.5, eff: 1.5, target: new THREE.Vector3(), shake: 0 };
const _v = new THREE.Vector3();

input.onGesture = () => { audio.unlock(); };

// ---------------------------------------------------------------- game flow
function setMode(m) {
  state.mode = m;
  document.body.classList.toggle('playing', m === 'playing');
  $('hud').classList.toggle('hidden', m !== 'playing');
  $('hint').classList.toggle('hidden', m !== 'playing');
  $('title').classList.toggle('hidden', m !== 'title');
  $('end').classList.toggle('hidden', m !== 'over');
  $('loading').classList.toggle('hidden', m !== 'loading');
  input.enabled = m === 'playing';
}

function startGame() {
  audio.unlock();
  room.reset();
  cat.reset(CAT_START.x, CAT_START.z, CAT_START.yaw);
  cam.yaw = 0; cam.pitch = 0.42;
  state.score = 0; state.time = GAME_SECONDS; state.knocked = 0;
  $('score').textContent = '0'; $('time').textContent = String(GAME_SECONDS); $('time').classList.remove('low');
  input.takeJump(); input.takeOrbit();
  setMode('playing');
  audio.play('meow', { vol: 0.8 });
  setTimeout(() => { $('hint').classList.add('hidden'); }, 7000);
}

function endGame(allDown) {
  if (state.mode !== 'playing') return;
  if (allDown) state.score += Math.round(state.time) * 5;
  if (state.score > state.best) {
    state.best = state.score;
    try { localStorage.setItem('knockitoff.best', String(state.best)); } catch (_) { /* ignore */ }
  }
  $('finalScore').textContent = String(state.score);
  $('bestScore').textContent = String(state.best);
  $('endNote').textContent = allDown
    ? `${petName} cleared the whole room with ${Math.round(state.time)}s to spare. Time bonus added.`
    : `${petName} knocked ${state.knocked} of ${room.props.length} things off.`;
  $('shareNote').textContent = '';
  setMode('over');
  audio.play('meow', { vol: 0.9, rate: 0.9 });
}

$('startBtn').addEventListener('click', startGame);
$('again').addEventListener('click', startGame);
$('muteBtn').addEventListener('click', () => {
  audio.setMuted(!audio.muted);
  $('muteBtn').textContent = audio.muted ? 'Sound off' : 'Sound on';
});
addEventListener('keydown', (e) => {
  if (e.code === 'KeyM') $('muteBtn').click();
  if (e.target && e.target.closest && e.target.closest('#pets')) return; // pet cards handle their own keys
  if ((e.code === 'Enter' || e.code === 'Space') && state.mode === 'title') startGame();
  else if (e.code === 'Enter' && state.mode === 'over') startGame();
});

function shareUrl() {
  const u = new URL(location.href);
  u.searchParams.delete('autostart'); u.searchParams.delete('probe');
  if (selPet) { u.searchParams.set('pet', selPet); if (selName) u.searchParams.set('name', selName); }
  return u.toString();
}
$('share').addEventListener('click', async () => {
  const url = shareUrl();
  const text = `${petName} knocked off ${state.score} points of stuff in Knock It Off. Beat that:`;
  try {
    if (navigator.share) { await navigator.share({ title: 'Knock It Off', text, url }); return; }
  } catch (e) { if (e && e.name === 'AbortError') return; }
  try { await navigator.clipboard.writeText(url); $('shareNote').textContent = 'Link copied. Send it to someone with a cat.'; }
  catch (_) { $('shareNote').textContent = url; }
});

// ---------------------------------------------------------------- scoring / props
const labelFor = { ceramic: 'ceramic', glass: 'glass', lamp: 'lamp', clock: 'clock', plant: 'plant', metal: 'metal', book: 'book', toy: 'toy' };
function popup(p, text) {
  _v.copy(p.body.pos).project(camera);
  if (_v.z > 1) return;
  const el = document.createElement('div');
  el.className = 'pop';
  el.textContent = text;
  const sm = document.createElement('small'); sm.textContent = labelFor[p.kind]; el.appendChild(sm);
  el.style.left = `${(_v.x * 0.5 + 0.5) * innerWidth}px`;
  el.style.top = `${(-_v.y * 0.5 + 0.5) * innerHeight}px`;
  $('popups').appendChild(el);
  setTimeout(() => el.remove(), 1200);
}

function onPropImpact(body, speed, tag, point) {
  const p = body.userData;
  const now = performance.now();
  const vol = Math.min(1, 0.25 + speed / 5);
  if (tag === 'floor' && !p.scored && state.mode === 'playing') {
    p.scored = true; state.knocked++;
    state.score += p.pts;
    $('score').textContent = String(state.score);
    popup(p, `+${p.pts}`);
    if (p.fragile && speed > 2.0) cam.shake = Math.max(cam.shake, 0.012);
    if (Math.random() < 0.4 && now - (onPropImpact.lastMeow || 0) > 4000) {
      onPropImpact.lastMeow = now; setTimeout(() => audio.play('meow', { vol: 0.7, rate: 1 + Math.random() * 0.2 }), 350);
    }
    if (state.knocked >= room.props.length) setTimeout(() => endGame(true), 1400);
  } else if (tag === 'floor' && !p.scored) {
    // knocked off before the game started: still make noise, no points
  }
  if (now - body.lastImpact < 120) return;
  body.lastImpact = now;
  switch (p.kind) {
    case 'ceramic': if (speed > 2.0) audio.play('smash_ceramic', { vol }); else audio.play(Math.random() < 0.5 ? 'clink' : 'clink2', { vol }); break;
    case 'glass': case 'lamp': if (speed > 2.0) audio.play('smash_glass', { vol }); else audio.play('clink2', { vol: vol * 0.8 }); break;
    case 'book': audio.play(Math.random() < 0.5 ? 'book1' : 'book2', { vol }); break;
    case 'clock': case 'metal': audio.play('clink', { vol, rate: 0.8 }); break;
    default: audio.play('land', { vol: vol * 0.7, rate: 1.1 }); break;
  }
}

// cat bumps props: overlap in xz plus vertical overlap -> impulse + separation
const _n = new THREE.Vector3(), _pt = new THREE.Vector3(), _J = new THREE.Vector3();
function catPushProps() {
  const R = CAT.R;
  for (const p of room.props) {
    const b = p.body, a = b.aabb;
    if (cat.pos.y + CAT.H < a.min.y + 0.01 || cat.pos.y > a.max.y - 0.01) continue;
    const cx = Math.min(Math.max(cat.pos.x, a.min.x), a.max.x), cz = Math.min(Math.max(cat.pos.z, a.min.z), a.max.z);
    const dx = cat.pos.x - cx, dz = cat.pos.z - cz, d2 = dx * dx + dz * dz;
    if (d2 >= R * R) continue;
    _n.set(b.pos.x - cat.pos.x, 0, b.pos.z - cat.pos.z);
    const dl = _n.length();
    if (dl < 1e-5) _n.set(Math.sin(cat.yaw), 0, Math.cos(cat.yaw)); else _n.multiplyScalar(1 / dl);
    const pen = R - Math.sqrt(d2);
    const along = cat.vel.x * _n.x + cat.vel.z * _n.z;
    const pushSpeed = along > 0.08 ? along * 1.15 + 0.12 : 0.15;
    const cur = b.vel.x * _n.x + b.vel.z * _n.z;
    if (cur < pushSpeed) {
      const dv = (pushSpeed - cur) / (1 + 0.5 * b.mass);
      _pt.set(b.pos.x - _n.x * b.half.x * 0.5, Math.min(Math.max(cat.pos.y + 0.17, a.min.y), a.max.y), b.pos.z - _n.z * b.half.z * 0.5);
      _J.copy(_n).multiplyScalar(dv * b.mass);
      b.applyImpulse(_pt, _J);
    } else b.wake();
    b.pos.x += _n.x * pen * 0.5; b.pos.z += _n.z * pen * 0.5;
    b.updateAabb();
  }
}

// ---------------------------------------------------------------- per-frame
const debug = { paused: false };
let acc = 0, stepDist = 0, stepFoot = 0, idleTime = 0;
function stepSim(h) {
  let wish = { x: 0, z: 0 }, jump = false;
  if (state.mode === 'playing') {
    const inp = input.read();
    const fx = -Math.sin(cam.yaw), fz = -Math.cos(cam.yaw), rx = -fz, rz = fx;
    if (inp.mag > 0) {
      const dx = fx * inp.y + rx * inp.x, dz = fz * inp.y + rz * inp.x;
      const l = Math.hypot(dx, dz) || 1;
      const spd = inp.run ? CAT.RUN : CAT.WALK * Math.min(1, inp.mag / 0.5);
      wish = { x: dx / l * spd, z: dz / l * spd };
    }
    jump = input.takeJump();
  }
  const sp = Math.hypot(wish.x, wish.z);
  if (sp > 0.05) {
    const target = Math.atan2(wish.x, wish.z);
    let d = target - cat.yaw; d = Math.atan2(Math.sin(d), Math.cos(d));
    cat.yaw += d * (1 - Math.exp(-14 * h));
  }
  cat.update(h, wish, jump);
  catPushProps();
  for (const p of room.props) p.body.step(h, world.boxes);
}

function frame(t) {
  requestAnimationFrame(frame);
  if (!room) return;
  const now = t / 1000;
  const dt = Math.min(0.05, frame.last ? now - frame.last : 0.016); frame.last = now;

  acc += dt;
  if (debug.paused) acc = 0;
  let guard = 0;
  while (acc >= SUBSTEP && guard++ < 12) { stepSim(SUBSTEP); acc -= SUBSTEP; }
  if (guard >= 12) acc = 0;

  // cat events -> sound
  for (const ev of cat.events) {
    if (ev === 'jump') { if (Math.random() < 0.15) audio.play('meow', { vol: 0.5, rate: 1.1 }); }
    else if (ev.startsWith('land:')) audio.play('land', { vol: Math.min(1, 0.3 + parseFloat(ev.slice(5)) / 6), rate: 1.2 });
  }
  cat.events.length = 0;

  // character
  const hs = Math.hypot(cat.vel.x, cat.vel.z);
  if (animator) {
    animator.update(dt, { ground: cat.onGround, speed: cat.onGround ? hs : 0, vy: cat.vel.y });
    character.root.position.copy(cat.pos);
    character.root.rotation.y = cat.yaw;
    if (cat.onGround && hs > 0.2) {
      stepDist += hs * dt;
      const stride = animator.gait === 'run' ? 0.42 : 0.26;
      if (stepDist > stride) { stepDist = 0; stepFoot ^= 1; audio.play(stepFoot ? 'step1' : 'step2', { vol: animator.gait === 'run' ? 0.55 : 0.35, cooldown: 0.05 }); }
    }
    idleTime = cat.onGround && hs < 0.1 ? idleTime + dt : 0;
    if (audio.loops.purr) audio.setLoopLevel('purr', idleTime > 1.5 && state.mode !== 'loading' ? 1 : 0);
    else if (audio.ctx && audio.buffers.purr) audio.startPurr();
  }

  // props follow bodies
  for (const p of room.props) {
    if (p.body.sleeping && p.holder.userData.synced) continue;
    p.holder.position.copy(p.body.pos); p.holder.quaternion.copy(p.body.quat);
    p.holder.userData.synced = p.body.sleeping;
  }

  // timer
  if (state.mode === 'playing') {
    state.time -= dt;
    const s = Math.max(0, Math.ceil(state.time));
    $('time').textContent = String(s);
    $('time').classList.toggle('low', s <= 10);
    if (state.time <= 0) endGame(false);
  }

  updateCamera(dt, now);
  renderer.render(scene, camera);
  if (!frame.ready) { frame.ready = true; document.documentElement.dataset.ready = '1'; } // smoke.sh waits for this
}

function updateCamera(dt, now) {
  const o = input.takeOrbit();
  if (state.mode === 'playing') {
    cam.yaw -= o.dx * 0.006;
    cam.pitch = THREE.MathUtils.clamp(cam.pitch + o.dy * 0.004, 0.06, 1.25);
  } else {
    cam.yaw += dt * 0.12; // slow turntable behind the title / end card
  }
  _v.set(cat.pos.x, cat.pos.y + 0.16, cat.pos.z);
  cam.target.lerp(_v, 1 - Math.exp(-12 * dt));
  const cp = Math.cos(cam.pitch);
  const dir = new THREE.Vector3(Math.sin(cam.yaw) * cp, Math.sin(cam.pitch), Math.cos(cam.yaw) * cp);
  const desired = cam.target.clone().addScaledVector(dir, cam.dist);
  // keep inside the room shell
  let f = 1;
  const lo = [ROOM.x0 + 0.18, 0.1, ROOM.z0 + 0.18], hi = [ROOM.x1 - 0.18, ROOM.h - 0.2, ROOM.z1 - 0.18];
  const t0 = [cam.target.x, cam.target.y, cam.target.z], d0 = [desired.x, desired.y, desired.z];
  for (let i = 0; i < 3; i++) {
    if (d0[i] > hi[i]) f = Math.min(f, (hi[i] - t0[i]) / (d0[i] - t0[i]));
    else if (d0[i] < lo[i]) f = Math.min(f, (lo[i] - t0[i]) / (d0[i] - t0[i]));
  }
  f = Math.max(0.12, f);
  const end = cam.target.clone().lerp(desired, f);
  const free = world.freeFraction(cam.target, end);
  const want = cam.dist * f * Math.max(0.1, free - 0.04);
  cam.eff = want < cam.eff ? want : cam.eff + (want - cam.eff) * (1 - Math.exp(-3 * dt)); // snap in, ease out
  camera.position.copy(cam.target).addScaledVector(dir, cam.eff);
  if (cam.shake > 0.0005) {
    camera.position.x += (Math.random() - 0.5) * cam.shake; camera.position.y += (Math.random() - 0.5) * cam.shake;
    cam.shake *= Math.exp(-9 * dt);
  }
  camera.lookAt(cam.target);
}

// ---------------------------------------------------------------- pet picker
const sameUrl = (a, b) => new URL(a, location.href).href === new URL(b, location.href).href;
async function availablePets() {
  let list = [];
  try { const r = await fetch('pets/index.json'); if (r.ok) list = await r.json(); } catch (_) { /* no index */ }
  if (!Array.isArray(list)) return [];
  const ok = await Promise.all(list.map(async (p) => {
    try { return !!(p && p.glb && (await fetch(p.glb, { method: 'HEAD' })).ok); } catch (_) { return false; }
  }));
  return list.filter((_, i) => ok[i]);
}
function choosePet(p) {
  const u = new URL(location.href);
  u.searchParams.set('pet', p.glb); u.searchParams.set('name', p.name);
  u.searchParams.delete('autostart');
  location.assign(u.toString());
}
function buildPicker(pets, current, custom) {
  const box = $('pets');
  const items = pets.slice();
  if (custom) items.push({ id: 'custom', name: 'Custom cat', glb: current, custom: true });
  if (items.length < 2) return; // nothing to choose between
  const cards = items.map((p) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'pet'; b.setAttribute('role', 'radio');
    const sel = sameUrl(p.glb, current);
    b.setAttribute('aria-checked', String(sel)); b.tabIndex = sel ? 0 : -1;
    b.classList.toggle('sel', sel);
    if (p.preview) {
      const img = document.createElement('img');
      img.src = p.preview; img.alt = ''; img.draggable = false;
      img.addEventListener('error', () => img.remove());
      b.appendChild(img);
    }
    const n = document.createElement('span'); n.textContent = p.name; b.appendChild(n);
    b.addEventListener('click', () => { if (!sel && !p.custom) choosePet(p); });
    return b;
  });
  box.append(...cards);
  box.addEventListener('keydown', (e) => {
    const i = cards.indexOf(document.activeElement);
    if (i < 0) return;
    const step = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    cards[(i + step + cards.length) % cards.length].focus();
  });
  box.classList.remove('hidden');
}

// ---------------------------------------------------------------- boot
async function boot() {
  try {
    const pets = await availablePets();
    const urlPet = params.get('pet');
    const entry = urlPet ? pets.find((p) => sameUrl(p.glb, urlPet)) : pets[0];
    let petUrl = urlPet || (entry && entry.glb) || DEFAULT_PET;
    const furOn = params.get('fur') !== '0';
    say('Furnishing the room...');
    const pmrem = new THREE.PMREMGenerator(renderer);
    const hdrP = new RGBELoader().loadAsync(ENV_HDR).then((tx) => {
      tx.mapping = THREE.EquirectangularReflectionMapping;
      scene.environment = pmrem.fromEquirectangular(tx).texture; scene.environmentIntensity = 0.85;
      tx.dispose(); pmrem.dispose();
    }).catch((e) => console.warn('HDRI failed', e));
    const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    const roomP = buildRoom({ scene, loadGLB, texLoader, world, aniso });
    const loadPet = async (url) => {
      const metaP = (async () => {
        try {
          const r = await fetch(new URL('meta.json', new URL(url, location.href)));
          if (r.ok) return await r.json();
        } catch (_) { /* optional */ }
        return null;
      })();
      const [c, m] = await Promise.all([loadCharacter(url, gltfLoader, { fur: furOn, touch: coarse }), metaP]);
      return { ch: c, meta: m };
    };
    let fellBack = false;
    const petP = loadPet(petUrl).catch(async (e) => {
      const fallback = (pets[0] && pets[0].glb) || DEFAULT_PET;
      if (!urlPet || sameUrl(fallback, petUrl)) throw e;
      console.warn('?pet= failed, using the default cat', e);
      fellBack = true; petUrl = fallback;
      return loadPet(petUrl);
    });
    const [roomRes, { ch, meta }] = await Promise.all([roomP, petP, hdrP]);
    room = roomRes; character = ch;
    const ent = fellBack ? pets.find((p) => sameUrl(p.glb, petUrl)) : entry;
    const strName = (v) => (typeof v === 'string' && v.trim() ? v : null);
    selPet = ent || urlPet ? petUrl : null;
    petName = (fellBack ? null : strName(params.get('name'))) || strName(meta && meta.name) || strName(ent && ent.name) || 'Your cat';
    petName = petName.slice(0, 40);
    selName = petName;
    buildPicker(pets, petUrl, !!urlPet && !entry && !fellBack);
    $('petName').textContent = petName;
    scene.add(character.root);
    animator = new CatAnimator(character);
    cat.reset(CAT_START.x, CAT_START.z, CAT_START.yaw);
    for (const p of room.props) p.body.onImpact = onPropImpact;
    $('bestScore').textContent = String(state.best);
    // warm shaders + upload textures before the first visible frame
    renderer.compile(scene, camera);
    setMode('title');
    if (fellBack) {
      const t = $('toast'); t.textContent = "Couldn't load that cat, playing the default one"; t.classList.remove('hidden');
      setTimeout(() => t.classList.add('hidden'), 5000);
    }
    if (params.get('autostart') === '1') startGame();
    requestAnimationFrame(frame); // started after loading so nothing ticks while assets stream in
    window.__game = { state, cat, room, character, animator, world, cam, camera, scene, renderer, input, THREE, startGame, endGame, step: stepSim, debug };
  } catch (e) {
    console.error(e);
    document.documentElement.dataset.error = String((e && e.message) || e);
    $('loadMsg').textContent = `Couldn't load the game: ${String(e.message || e)}`;
    document.querySelector('#loading .spin')?.remove();
  }
}
boot();
