// The cosy room: photo-textured shell (floor/walls), Poly Haven furniture with hand-measured AABB
// colliders, and the knick-knacks (rigid bodies) sitting on top of them.
import * as THREE from 'three';
import { MODELS, TEX } from './assets.js';
import { PropBody } from './physics.js';

export const ROOM = { x0: -3, x1: 3, z0: -2.5, z1: 2.5, h: 2.6 };
export const CAT_START = { x: 0.1, z: 1.5, yaw: Math.PI }; // yaw = direction of travel (atan2(x, z)); PI faces -z

// Collider boxes in the model's local frame: [minx, miny, minz, maxx, maxy, maxz].
const SHELF_TOPS = [0.39, 0.67, 0.96, 1.28, 1.66];
const FURNITURE = [
  {
    model: 'bookshelf', pos: [-2.71, 0, -0.9], rot: 90,
    boxes: [
      [-0.69, 0, -0.29, -0.61, 2.06, 0.29], [0.61, 0, -0.29, 0.69, 2.06, 0.29], [-0.69, 0, -0.29, 0.69, 2.06, -0.25],
      [-0.69, 0, -0.29, 0.69, 0.11, 0.29], [-0.69, 2.0, -0.29, 0.69, 2.06, 0.29],
      ...SHELF_TOPS.map((t) => [-0.61, t - 0.05, -0.29, 0.61, t, 0.29]),
    ],
    cam: [-0.69, 0, -0.29, 0.69, 2.06, 0.29],
  },
  {
    model: 'desk', pos: [-1.95, 0, -0.4], rot: 90,
    boxes: [[-1.0, 0.75, -0.47, 1.0, 0.79, 0.45], [-0.93, 0, -0.30, -0.5, 0.75, 0.43], [0.5, 0, -0.30, 0.93, 0.75, 0.43]],
    cam: [-1.0, 0.0, -0.47, 1.0, 0.79, 0.45],
  },
  {
    model: 'cabinet', pos: [-2.72, 0, 0.9], rot: 90,
    boxes: [[-0.55, 0, -0.25, 0.55, 1.13, 0.25], [-0.59, 1.13, -0.28, 0.6, 1.18, 0.3]],
    cam: [-0.59, 0, -0.28, 0.6, 1.18, 0.3],
  },
  {
    model: 'coffee_table', pos: [1.35, 0, 0.4], rot: 90,
    boxes: [[-0.73, 0.5, -0.43, 0.73, 0.53, 0.43], [-0.71, 0.30, -0.42, 0.71, 0.33, 0.42],
      ...[[-0.69, -0.40], [0.69, -0.40], [-0.69, 0.40], [0.69, 0.40]].map(([x, z]) => [x - 0.04, 0, z - 0.04, x + 0.04, 0.5, z + 0.04])],
    cam: [-0.73, 0, -0.43, 0.73, 0.53, 0.43],
  },
  {
    model: 'sofa', pos: [2.64, 0, 0.4], rot: -90,
    boxes: [[-0.70, 0, -0.19, 0.70, 0.38, 0.27], [-0.78, 0, -0.36, 0.78, 0.80, -0.19], [-0.78, 0, -0.36, -0.68, 0.6, 0.30], [0.68, 0, -0.36, 0.78, 0.6, 0.30]],
    cam: [-0.78, 0, -0.36, 0.78, 0.80, 0.30],
  },
];

// Windowsill: wood board on the back wall (room shell, textured with the floor boards).
const SILL = { x0: 0.4, x1: 2.0, y0: 0.74, y1: 0.78, z0: ROOM.z0, z1: ROOM.z0 + 0.3 };

// Knick-knacks. surf = height of the supporting surface, at = [x, z].
// kind: ceramic | glass | book | plant | lamp | clock | toy | metal
const PROPS = [
  // coffee table (0.53)
  { model: 'ceramic_vase_02', kind: 'ceramic', surf: 0.53, at: [1.30, -0.12], mass: 0.7 },
  { model: 'tea_set_01', nodes: ['tea_set_01_teapot_01', 'tea_set_01_teapot_01_lid'], kind: 'ceramic', surf: 0.53, at: [1.25, 0.28], mass: 0.6 },
  { model: 'tea_set_01', nodes: ['tea_set_01_cup_small_01'], kind: 'ceramic', surf: 0.53, at: [1.55, 0.45], mass: 0.18 },
  { model: 'tea_set_01', nodes: ['tea_set_01_sugar_cup_01', 'tea_set_01_sugar_cup_01_lid'], kind: 'ceramic', surf: 0.53, at: [1.25, 0.75], mass: 0.25 },
  { model: 'binder_notebook', nodes: ['binder_notebook_closed'], kind: 'book', surf: 0.53, at: [1.45, 0.98], mass: 0.5 },
  // desk (0.79)
  { model: 'desk_lamp_arm_01', kind: 'lamp', surf: 0.79, at: [-1.85, -1.05], mass: 1.1, shrink: 0.8 },
  { model: 'book_encyclopedia_set_01', nodes: ['book_encyclopedia_set_01_book01'], kind: 'book', surf: 0.79, at: [-2.0, -0.65], mass: 0.6 },
  { model: 'plastic_thermos', kind: 'metal', surf: 0.79, at: [-1.75, -0.4], mass: 0.4 },
  { model: 'ceramic_vase_04', kind: 'ceramic', surf: 0.79, at: [-1.85, -0.0], mass: 0.6 },
  { model: 'round_spectacles', kind: 'glass', surf: 0.79, at: [-1.75, 0.4], mass: 0.05, yaw: 1.2 },
  // cabinet (1.18)
  { model: 'ceramic_vase_03', kind: 'ceramic', surf: 1.18, at: [-2.72, 0.45], mass: 0.6 },
  { model: 'mantel_clock_01', kind: 'clock', surf: 1.18, at: [-2.72, 0.82], mass: 0.8 },
  { model: 'potted_plant_04', kind: 'plant', surf: 1.18, at: [-2.72, 1.07], mass: 1.2, shrink: 0.7 },
  { model: 'antique_ceramic_vase_01', kind: 'ceramic', surf: 1.18, at: [-2.72, 1.33], mass: 0.9 },
  // bookshelf: 0.96 / 1.28 / 1.66 boards (bay x range -3.0 .. -2.42)
  { model: 'jug_01', kind: 'ceramic', surf: 0.96, at: [-2.75, -1.30], mass: 0.5, yaw: 1.57 },
  { model: 'pot_enamel_01', nodes: ['pot_enamel_01_base', 'pot_enamel_01_lid'], kind: 'metal', surf: 0.96, at: [-2.75, -1.0], mass: 0.5 },
  { model: 'book_encyclopedia_set_01', nodes: ['book_encyclopedia_set_01_book03'], kind: 'book', surf: 0.96, at: [-2.75, -0.7], mass: 0.6 },
  { model: 'alarm_clock_01', kind: 'clock', surf: 0.96, at: [-2.75, -0.4], mass: 0.3 },
  { model: 'planter_pot_clay', kind: 'plant', surf: 1.28, at: [-2.75, -1.30], mass: 0.9 },
  { model: 'rubber_duck_toy', kind: 'toy', surf: 1.28, at: [-2.75, -0.95], mass: 0.08 },
  { model: 'standing_picture_frame_01', kind: 'clock', surf: 1.28, at: [-2.75, -0.55], mass: 0.2 },
  { model: 'wine_bottles_01', nodes: ['wine_bottles_01_bordeaux'], kind: 'glass', surf: 1.66, at: [-2.75, -1.3], mass: 1.0 },
  { model: 'wine_bottles_01', nodes: ['wine_bottles_01_alsace'], kind: 'glass', surf: 1.66, at: [-2.75, -1.05], mass: 1.0 },
  { model: 'wine_bottles_01', nodes: ['wine_bottles_01_champagne'], kind: 'glass', surf: 1.66, at: [-2.75, -0.8], mass: 1.1 },
  { model: 'book_encyclopedia_set_01', nodes: ['book_encyclopedia_set_01_book02'], kind: 'book', surf: 1.66, at: [-2.75, -0.5], mass: 0.6 },
  // windowsill (0.78)
  { model: 'vintage_oil_lamp', kind: 'lamp', surf: 0.78, at: [0.75, -2.35], mass: 0.9 },
  { model: 'ceramic_vase_01', kind: 'ceramic', surf: 0.78, at: [1.2, -2.35], mass: 0.7 },
  { model: 'potted_plant_04', kind: 'plant', surf: 0.78, at: [1.7, -2.35], mass: 1.2, shrink: 0.7 },
];

export const KIND = {
  ceramic: { pts: 100, fragile: true },
  glass: { pts: 150, fragile: true },
  lamp: { pts: 120, fragile: true },
  clock: { pts: 90, fragile: false },
  plant: { pts: 80, fragile: false },
  metal: { pts: 60, fragile: false },
  book: { pts: 50, fragile: false },
  toy: { pts: 40, fragile: false },
};

function rotBox(b, pos, rotDeg) {
  const th = (rotDeg * Math.PI) / 180;
  const c = Math.round(Math.cos(th)), s = Math.round(Math.sin(th));
  const xs = [], zs = [];
  for (const x of [b[0], b[3]]) for (const z of [b[2], b[5]]) {
    xs.push(c * x + s * z + pos[0]); zs.push(-s * x + c * z + pos[2]);
  }
  return [Math.min(...xs), b[1] + pos[1], Math.min(...zs), Math.max(...xs), b[4] + pos[1], Math.max(...zs)];
}

function fixMaterials(root) {
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true; o.receiveShadow = true;
    for (const m of [].concat(o.material)) {
      if (m.transmission > 0) { m.transmission = 0; m.transparent = true; m.opacity = 0.6; m.depthWrite = false; }
    }
  });
}

export async function buildRoom({ scene, loadGLB, texLoader, world, aniso = 4 }) {
  const { x0, x1, z0, z1, h } = ROOM;
  const tex = (url, srgb, rx, ry) => {
    const t = texLoader.load(url);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.anisotropy = aniso;
    if (srgb) t.colorSpace = THREE.SRGBColorSpace;
    return t;
  };
  const floorMat = new THREE.MeshStandardMaterial({
    map: tex(TEX.floorColor, true, 4, 3.4), normalMap: tex(TEX.floorNormal, false, 4, 3.4), roughnessMap: tex(TEX.floorRough, false, 4, 3.4), roughness: 1,
  });
  const mkWall = (rx) => new THREE.MeshStandardMaterial({
    map: tex(TEX.wallColor, true, rx, 1.8), normalMap: tex(TEX.wallNormal, false, rx, 1.8), roughnessMap: tex(TEX.wallRough, false, rx, 1.8),
    color: 0xeadcc6, roughness: 1,
  });

  // floor + 4 walls (single-sided, facing in)
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), floorMat);
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const wallDefs = [
    { w: z1 - z0, pos: [x0, h / 2, 0], ry: Math.PI / 2 }, // left, faces +x
    { w: z1 - z0, pos: [x1, h / 2, 0], ry: -Math.PI / 2 }, // right
    { w: x1 - x0, pos: [0, h / 2, z0], ry: 0 }, // back, faces +z
    { w: x1 - x0, pos: [0, h / 2, z1], ry: Math.PI }, // front
  ];
  for (const w of wallDefs) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w.w, h), mkWall(w.w / 1.6));
    m.position.set(...w.pos); m.rotation.y = w.ry; m.receiveShadow = true; scene.add(m);
  }

  // window on the back wall: bright daylight panel + wooden frame + the sill
  const wood = new THREE.MeshStandardMaterial({ map: floorMat.map, normalMap: floorMat.normalMap, roughnessMap: floorMat.roughnessMap, roughness: 1, color: 0xcfc0ae });
  const win = { x0: 0.3, x1: 2.1, y0: 0.95, y1: 2.0 };
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(win.x1 - win.x0, win.y1 - win.y0), new THREE.MeshBasicMaterial({ color: 0xfff1d6, toneMapped: false }));
  glass.position.set((win.x0 + win.x1) / 2, (win.y0 + win.y1) / 2, z0 + 0.004); scene.add(glass);
  const bar = (cx, cy, w, hh) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, hh, 0.07), wood);
    m.position.set(cx, cy, z0 + 0.035); m.castShadow = false; scene.add(m);
  };
  const t = 0.06, wx = (win.x0 + win.x1) / 2, wy = (win.y0 + win.y1) / 2;
  bar(wx, win.y1, win.x1 - win.x0 + t, t); bar(wx, win.y0, win.x1 - win.x0 + t, t);
  bar(win.x0, wy, t, win.y1 - win.y0); bar(win.x1, wy, t, win.y1 - win.y0);
  bar(wx, wy, t * 0.6, win.y1 - win.y0); bar(wx, wy, win.x1 - win.x0, t * 0.6);
  const sill = new THREE.Mesh(new THREE.BoxGeometry(SILL.x1 - SILL.x0, SILL.y1 - SILL.y0, SILL.z1 - SILL.z0), wood);
  sill.position.set((SILL.x0 + SILL.x1) / 2, (SILL.y0 + SILL.y1) / 2, (SILL.z0 + SILL.z1) / 2);
  sill.castShadow = sill.receiveShadow = true; scene.add(sill);

  // colliders: floor, walls, ceiling, sill
  world.add(x0 - 1, -1, z0 - 1, x1 + 1, 0, z1 + 1, 'floor');
  world.add(x0 - 1, -1, z0 - 1, x0, h + 1, z1 + 1, 'wall');
  world.add(x1, -1, z0 - 1, x1 + 1, h + 1, z1 + 1, 'wall');
  world.add(x0 - 1, -1, z0 - 1, x1 + 1, h + 1, z0, 'wall');
  world.add(x0 - 1, -1, z1, x1 + 1, h + 1, z1 + 1, 'wall');
  world.add(x0 - 1, h, z0 - 1, x1 + 1, h + 1, z1 + 1, 'wall');
  world.add(SILL.x0, SILL.y0, SILL.z0, SILL.x1, SILL.y1, SILL.z1, 'furn');
  world.addCam(SILL.x0, 0, SILL.z0, SILL.x1, SILL.y1, SILL.z1);

  // load every model in parallel up front (the loader caches the promises)
  await Promise.all([...new Set([...FURNITURE.map((f) => f.model), ...PROPS.map((d) => d.model)])].map((m) => loadGLB(MODELS[m])));

  // furniture
  for (const f of FURNITURE) {
    const gltf = await loadGLB(MODELS[f.model]);
    const obj = gltf.scene.clone(true);
    obj.position.set(...f.pos); obj.rotation.y = (f.rot * Math.PI) / 180;
    fixMaterials(obj); scene.add(obj);
    for (const b of f.boxes) { const r = rotBox(b, f.pos, f.rot); world.add(...r, 'furn'); }
    const c = rotBox(f.cam, f.pos, f.rot); world.addCam(...c);
  }

  // props
  const props = [];
  for (const def of PROPS) {
    const gltf = await loadGLB(MODELS[def.model]);
    gltf.scene.updateMatrixWorld(true);
    const g = new THREE.Group();
    if (def.nodes) {
      for (const n of def.nodes) {
        const src = gltf.scene.getObjectByName(n);
        if (!src) { console.warn('missing node', def.model, n); continue; }
        const c = src.clone(true);
        src.matrixWorld.decompose(c.position, c.quaternion, c.scale);
        g.add(c);
      }
    } else g.add(gltf.scene.clone(true));
    g.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(g);
    const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
    g.position.sub(centre);
    const holder = new THREE.Group();
    holder.add(g); fixMaterials(holder); scene.add(holder);
    const sh = def.shrink ?? 1;
    const half = new THREE.Vector3(size.x / 2 * (sh < 1 ? sh : 1), size.y / 2, size.z / 2 * (sh < 1 ? sh : 1));
    const body = new PropBody(half, def.mass, { mu: def.kind === 'toy' ? 0.7 : 0.5, rest: def.kind === 'ceramic' || def.kind === 'glass' ? 0.2 : 0.3 });
    const p = {
      def, kind: def.kind, holder, body, size,
      start: { x: def.at[0], y: def.surf + half.y + 0.002, z: def.at[1], yaw: def.yaw || 0 },
      scored: false, pts: KIND[def.kind].pts, fragile: KIND[def.kind].fragile, name: def.model,
    };
    body.userData = p;
    props.push(p);
  }
  const reset = () => {
    for (const p of props) {
      p.scored = false;
      p.body.place(p.start.x, p.start.y, p.start.z, p.start.yaw);
      p.holder.position.copy(p.body.pos); p.holder.quaternion.copy(p.body.quat);
    }
  };
  reset();
  return { props, reset };
}
