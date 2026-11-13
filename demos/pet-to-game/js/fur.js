// Fur shells: N extra copies of each body SkinnedMesh, pushed out along the skinned normal in the
// vertex shader (after skinning), alpha-tested by a tiled strand-noise texture that thins toward the tips.
import * as THREE from 'three';

const NON_BODY = /eye|cornea|iris|sclera|teeth|tooth|tongue|mouth|claw|lash|brow/i;

function strandTexture() {
  const N = 128, data = new Uint8Array(N * N * 4);
  let s = 1234567;
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  const base = new Float32Array(N * N);
  for (let i = 0; i < base.length; i++) base[i] = rnd();
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    // slight clumping: blend each texel with its neighbours so strands are ~2 texels wide
    const v = 0.55 * base[y * N + x] + 0.15 * (base[y * N + (x + 1) % N] + base[y * N + (x + N - 1) % N] + base[((y + 1) % N) * N + x] + base[((y + N - 1) % N) * N + x]);
    const k = (y * N + x) * 4, b = Math.min(255, Math.max(0, Math.round(v * 255 * 1.25)));
    data[k] = data[k + 1] = data[k + 2] = b; data[k + 3] = 255;
  }
  const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true; t.needsUpdate = true;
  return t;
}

// root: character scene. lengthObj: fur length in the mesh's own (pre-scale) units.
export function addFurShells(root, { shells = 10, lengthObj = 0.01, tile = 70 } = {}) {
  const tex = strandTexture();
  const bodies = [];
  root.traverse((o) => {
    if (!o.isSkinnedMesh) return;
    const mats = [].concat(o.material);
    const name = `${o.name} ${mats.map((m) => m.name).join(' ')}`;
    if (NON_BODY.test(name)) return;
    if (!mats.every((m) => m.map) || mats.some((m) => m.transparent)) return;
    bodies.push(o);
  });
  let count = 0;
  for (const mesh of bodies) {
    for (let i = 1; i <= shells; i++) {
      const t = i / (shells + 1);
      const mat = [].concat(mesh.material).map((src) => {
        const m = src.clone();
        m.side = THREE.FrontSide; m.transparent = false; m.depthWrite = true;
        m.onBeforeCompile = (sh) => {
          sh.uniforms.uShell = { value: lengthObj * t };
          sh.uniforms.uShellT = { value: t };
          sh.uniforms.tFur = { value: tex };
          sh.uniforms.uTile = { value: tile };
          sh.vertexShader = sh.vertexShader
            .replace('#include <common>', '#include <common>\nuniform float uShell;\nvarying vec2 vFurUv;')
            .replace('#include <skinning_vertex>', '#include <skinning_vertex>\n  transformed += normalize(objectNormal) * uShell;\n  vFurUv = uv;');
          sh.fragmentShader = sh.fragmentShader
            .replace('#include <common>', '#include <common>\nuniform float uShellT;\nuniform float uTile;\nuniform sampler2D tFur;\nvarying vec2 vFurUv;')
            .replace('#include <map_fragment>', '#include <map_fragment>\n  float strand = texture2D(tFur, vFurUv * uTile).r;\n  if (strand < uShellT * 0.9 + 0.08) discard;\n  diffuseColor.rgb *= mix(0.6, 1.0, uShellT);');
        };
        m.customProgramCacheKey = () => 'furshell';
        return m;
      });
      const shell = new THREE.SkinnedMesh(mesh.geometry, mat.length === 1 ? mat[0] : mat);
      shell.bind(mesh.skeleton, mesh.bindMatrix);
      shell.position.copy(mesh.position); shell.quaternion.copy(mesh.quaternion); shell.scale.copy(mesh.scale);
      shell.frustumCulled = false; shell.castShadow = false; shell.receiveShadow = false; shell.name = mesh.name + '_fur' + i;
      mesh.parent.add(shell);
      count++;
    }
  }
  return count;
}
