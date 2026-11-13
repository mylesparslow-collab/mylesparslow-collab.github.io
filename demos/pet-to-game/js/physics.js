// Small hand-rolled physics: axis-aligned static boxes, a cat capsule-ish controller, and
// point-contact rigid bodies for the knick-knacks.
import * as THREE from 'three';

const _v = new THREE.Vector3();
const _r = new THREE.Vector3();
const _p = new THREE.Vector3();
const _a = new THREE.Vector3();
const _b = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _qi = new THREE.Quaternion();

export class StaticWorld {
  constructor() {
    this.boxes = []; // {min, max, tag}
    this.camBoxes = []; // boxes that block the camera
  }
  add(minx, miny, minz, maxx, maxy, maxz, tag = 'furn') {
    const b = { min: new THREE.Vector3(minx, miny, minz), max: new THREE.Vector3(maxx, maxy, maxz), tag };
    this.boxes.push(b);
    return b;
  }
  addCam(minx, miny, minz, maxx, maxy, maxz) {
    this.camBoxes.push({ min: new THREE.Vector3(minx, miny, minz), max: new THREE.Vector3(maxx, maxy, maxz) });
  }
  // Segment from a to b against the camera-blocking boxes: returns fraction of the segment that is free.
  freeFraction(a, b) {
    let tmin = 1;
    const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
    for (const bx of this.camBoxes) {
      if (a.x > bx.min.x && a.x < bx.max.x && a.y > bx.min.y && a.y < bx.max.y && a.z > bx.min.z && a.z < bx.max.z) continue; // start inside: ignore
      let t0 = 0, t1 = 1;
      const axes = [[a.x, dx, bx.min.x, bx.max.x], [a.y, dy, bx.min.y, bx.max.y], [a.z, dz, bx.min.z, bx.max.z]];
      let hit = true;
      for (const [o, d, lo, hi] of axes) {
        if (Math.abs(d) < 1e-9) { if (o < lo || o > hi) { hit = false; break; } continue; }
        let n = (lo - o) / d, f = (hi - o) / d;
        if (n > f) [n, f] = [f, n];
        t0 = Math.max(t0, n); t1 = Math.min(t1, f);
        if (t0 > t1) { hit = false; break; }
      }
      if (hit && t0 < tmin) tmin = t0;
    }
    return tmin;
  }
}

// ---------------------------------------------------------------- cat
export const CAT = { R: 0.11, H: 0.26, STEP: 0.07, GRAV: 11, JUMP_V: 4.6, WALK: 0.9, RUN: 2.6 };

export class CatBody {
  constructor(world) {
    this.world = world;
    this.pos = new THREE.Vector3(); // feet
    this.vel = new THREE.Vector3();
    this.onGround = false;
    this.yaw = 0;
    this.coyote = 0;
    this.jumpBuf = 0;
    this.events = []; // 'jump' | 'land:<speed>'
  }
  reset(x, z, yaw) {
    this.pos.set(x, 0, z); this.vel.set(0, 0, 0); this.yaw = yaw; this.onGround = true; this.events.length = 0;
  }
  // wish: {x, z} world-space desired velocity (m/s); jump: pressed this frame
  update(dt, wish, jump) {
    const { R, H, STEP } = CAT;
    const boxes = this.world.boxes;
    const accel = this.onGround ? 16 : 4;
    const dvx = wish.x - this.vel.x, dvz = wish.z - this.vel.z;
    const dl = Math.hypot(dvx, dvz);
    const maxd = accel * dt;
    if (dl > maxd) { this.vel.x += dvx / dl * maxd; this.vel.z += dvz / dl * maxd; }
    else { this.vel.x = wish.x; this.vel.z = wish.z; }

    if (jump) this.jumpBuf = 0.12;
    this.jumpBuf = Math.max(0, this.jumpBuf - dt);
    if (this.onGround) this.coyote = 0.1; else this.coyote = Math.max(0, this.coyote - dt);
    if (this.jumpBuf > 0 && this.coyote > 0) {
      this.vel.y = CAT.JUMP_V; this.onGround = false; this.coyote = 0; this.jumpBuf = 0; this.events.push('jump');
    }

    // horizontal move + push-out
    this.pos.x += this.vel.x * dt;
    this.pos.z += this.vel.z * dt;
    for (let pass = 0; pass < 2; pass++) {
      for (const b of boxes) {
        if (b.max.y <= this.pos.y + STEP || b.min.y >= this.pos.y + H) continue;
        const cx = Math.min(Math.max(this.pos.x, b.min.x), b.max.x);
        const cz = Math.min(Math.max(this.pos.z, b.min.z), b.max.z);
        let dx = this.pos.x - cx, dz = this.pos.z - cz;
        const d2 = dx * dx + dz * dz;
        if (d2 >= R * R) continue;
        let nx, nz, push;
        if (d2 > 1e-10) { const d = Math.sqrt(d2); nx = dx / d; nz = dz / d; push = R - d; }
        else { // centre inside: exit through nearest face
          const ex = Math.min(this.pos.x - b.min.x, b.max.x - this.pos.x);
          const ez = Math.min(this.pos.z - b.min.z, b.max.z - this.pos.z);
          if (ex < ez) { nx = (this.pos.x - b.min.x < b.max.x - this.pos.x) ? -1 : 1; nz = 0; push = ex + R; }
          else { nz = (this.pos.z - b.min.z < b.max.z - this.pos.z) ? -1 : 1; nx = 0; push = ez + R; }
        }
        this.pos.x += nx * push; this.pos.z += nz * push;
        const vn = this.vel.x * nx + this.vel.z * nz;
        if (vn < 0) { this.vel.x -= nx * vn; this.vel.z -= nz * vn; }
      }
    }

    // vertical
    const prevY = this.pos.y;
    const impactV = this.vel.y;
    this.vel.y -= CAT.GRAV * dt;
    if (this.vel.y < -14) this.vel.y = -14;
    this.pos.y += this.vel.y * dt;

    let support = 0;
    const fr = R * 0.6;
    for (const b of boxes) {
      if (this.pos.x < b.min.x - fr || this.pos.x > b.max.x + fr || this.pos.z < b.min.z - fr || this.pos.z > b.max.z + fr) continue;
      if (b.max.y <= prevY + STEP && b.max.y > support) support = b.max.y;
      // head bump
      if (this.vel.y > 0 && b.min.y >= prevY + H - 0.03 && this.pos.y + H > b.min.y && b.max.y > b.min.y) {
        this.pos.y = b.min.y - H; this.vel.y = 0;
      }
    }
    if (this.vel.y <= 0 && this.pos.y <= support + 1e-4) {
      if (!this.onGround && impactV < -1.2) this.events.push('land:' + (-impactV).toFixed(2));
      this.pos.y = support; this.vel.y = 0; this.onGround = true;
    } else if (this.onGround && this.vel.y <= 0 && prevY - support < 0.04 && support < prevY) {
      this.pos.y = support; this.vel.y = 0; // snap down small steps
    } else {
      this.onGround = false;
    }
  }
}

// ---------------------------------------------------------------- props
const G = 9.8;

export class PropBody {
  // half: Vector3 half extents. Centre of the body is the box centre.
  constructor(half, mass, opts = {}) {
    this.half = half.clone();
    this.mass = mass; this.invMass = 1 / mass;
    this.mu = opts.mu ?? 0.5;
    this.rest = opts.rest ?? 0.25;
    const sx = half.x * 2, sy = half.y * 2, sz = half.z * 2;
    const k = mass / 12;
    this.invI = new THREE.Vector3(1 / (k * (sy * sy + sz * sz)), 1 / (k * (sx * sx + sz * sz)), 1 / (k * (sx * sx + sy * sy)));
    this.pos = new THREE.Vector3(); this.quat = new THREE.Quaternion();
    this.vel = new THREE.Vector3(); this.ang = new THREE.Vector3();
    this.sleeping = true; this.sleepT = 0;
    this.radius = half.length();
    this.pts = [];
    for (const sxn of [-1, 1]) for (const syn of [-1, 1]) for (const szn of [-1, 1]) this.pts.push(new THREE.Vector3(sxn * half.x, syn * half.y, szn * half.z));
    for (const syn of [-1, 1]) {
      this.pts.push(new THREE.Vector3(half.x, syn * half.y, 0), new THREE.Vector3(-half.x, syn * half.y, 0),
        new THREE.Vector3(0, syn * half.y, half.z), new THREE.Vector3(0, syn * half.y, -half.z));
    }
    this.aabb = { min: new THREE.Vector3(), max: new THREE.Vector3() };
    this.onImpact = null; // (body, speed, tag, point)
    this.lastImpact = 0;
  }
  place(x, y, z, yaw) {
    this.pos.set(x, y, z); this.quat.setFromAxisAngle(_a.set(0, 1, 0), yaw || 0);
    this.vel.set(0, 0, 0); this.ang.set(0, 0, 0); this.sleeping = true; this.sleepT = 0; this.updateAabb();
  }
  wake() { this.sleeping = false; this.sleepT = 0; }
  updateAabb() {
    const m = this.aabb.min.set(1e9, 1e9, 1e9), M = this.aabb.max.set(-1e9, -1e9, -1e9);
    for (const lp of this.pts) {
      _p.copy(lp).applyQuaternion(this.quat).add(this.pos);
      m.min(_p); M.max(_p);
    }
  }
  invIw(v, out) { // R * (invI * (R^T v))
    _qi.copy(this.quat).invert();
    out.copy(v).applyQuaternion(_qi);
    out.set(out.x * this.invI.x, out.y * this.invI.y, out.z * this.invI.z).applyQuaternion(this.quat);
    return out;
  }
  applyImpulse(point, J) { // world point, world impulse
    this.wake();
    this.vel.addScaledVector(J, this.invMass);
    _r.copy(point).sub(this.pos);
    _a.copy(_r).cross(J);
    this.ang.add(this.invIw(_a, _b));
  }
  step(dt, boxes) {
    if (this.sleeping) return;
    this.vel.y -= G * dt;
    const sp = this.vel.length();
    if (sp > 7) this.vel.multiplyScalar(7 / sp);
    this.pos.addScaledVector(this.vel, dt);
    // integrate orientation
    _q.set(this.ang.x, this.ang.y, this.ang.z, 0).multiply(this.quat);
    this.quat.set(this.quat.x + 0.5 * dt * _q.x, this.quat.y + 0.5 * dt * _q.y, this.quat.z + 0.5 * dt * _q.z, this.quat.w + 0.5 * dt * _q.w).normalize();
    this.ang.multiplyScalar(1 - 0.4 * dt);
    this.updateAabb();

    let touched = false;
    for (let it = 0; it < 3; it++) {
      for (const b of boxes) {
        if (this.aabb.max.x < b.min.x || this.aabb.min.x > b.max.x || this.aabb.max.y < b.min.y || this.aabb.min.y > b.max.y ||
          this.aabb.max.z < b.min.z || this.aabb.min.z > b.max.z) continue;
        for (const lp of this.pts) {
          _p.copy(lp).applyQuaternion(this.quat).add(this.pos);
          if (_p.x <= b.min.x || _p.x >= b.max.x || _p.y <= b.min.y || _p.y >= b.max.y || _p.z <= b.min.z || _p.z >= b.max.z) continue;
          // penetration axis
          let best = 1e9, nx = 0, ny = 0, nz = 0;
          const c = [[_p.x - b.min.x, -1, 0, 0], [b.max.x - _p.x, 1, 0, 0], [_p.y - b.min.y, 0, -1, 0], [b.max.y - _p.y, 0, 1, 0], [_p.z - b.min.z, 0, 0, -1], [b.max.z - _p.z, 0, 0, 1]];
          for (const [d, ax, ay, az] of c) if (d < best) { best = d; nx = ax; ny = ay; nz = az; }
          this.pos.x += nx * best * 0.6; this.pos.y += ny * best * 0.6; this.pos.z += nz * best * 0.6;
          _p.x += nx * best * 0.6; _p.y += ny * best * 0.6; _p.z += nz * best * 0.6;
          const n = _v.set(nx, ny, nz);
          _r.copy(_p).sub(this.pos);
          const vp = _a.copy(this.ang).cross(_r).add(this.vel); // velocity at the point
          const vn = vp.dot(n);
          if (vn < 0) {
            touched = true;
            const e = -vn > 1.2 ? this.rest : 0;
            _b.copy(_r).cross(n);
            this.invIw(_b, _b);
            _b.cross(_r);
            const denom = this.invMass + _b.dot(n);
            const j = -(1 + e) * vn / denom;
            const nn = n.clone();
            this.vel.addScaledVector(nn, j * this.invMass);
            _b.copy(_r).cross(nn).multiplyScalar(j);
            this.ang.add(this.invIw(_b, _a));
            // friction
            const vp2 = _a.copy(this.ang).cross(_r).add(this.vel);
            const vt = vp2.addScaledVector(nn, -vp2.dot(nn));
            const tl = vt.length();
            if (tl > 1e-4) {
              const t = vt.multiplyScalar(1 / tl);
              _b.copy(_r).cross(t);
              this.invIw(_b, _b);
              _b.cross(_r);
              const jt = Math.min(tl / (this.invMass + _b.dot(t)), this.mu * j);
              this.vel.addScaledVector(t, -jt * this.invMass);
              _b.copy(_r).cross(t).multiplyScalar(-jt);
              this.ang.add(this.invIw(_b, _a));
            }
            if (-vn > 0.5 && this.onImpact) this.onImpact(this, -vn, b.tag, _p);
          }
        }
      }
      this.updateAabb();
    }
    // sleep
    if (this.vel.lengthSq() < 0.0036 && this.ang.lengthSq() < 0.06 && touched) {
      this.sleepT += dt;
      if (this.sleepT > 0.4) { this.sleeping = true; this.vel.set(0, 0, 0); this.ang.set(0, 0, 0); }
    } else this.sleepT = 0;
    if (this.pos.y < -3) { this.pos.y = 0.5; this.vel.set(0, 0, 0); }
  }
}
