// Every local asset the game references. tools/smoke.sh imports this list and checks each URL returns 200.
const M = (n) => `assets/models/${n}.glb`;

export const MODELS = {
  bookshelf: M('wooden_bookshelf_worn'),
  desk: M('metal_office_desk'),
  cabinet: M('painted_wooden_cabinet'),
  coffee_table: M('CoffeeTable_01'),
  sofa: M('Sofa_01'),
  ceramic_vase_01: M('ceramic_vase_01'),
  ceramic_vase_02: M('ceramic_vase_02'),
  ceramic_vase_03: M('ceramic_vase_03'),
  ceramic_vase_04: M('ceramic_vase_04'),
  antique_ceramic_vase_01: M('antique_ceramic_vase_01'),
  tea_set_01: M('tea_set_01'),
  wine_bottles_01: M('wine_bottles_01'),
  book_encyclopedia_set_01: M('book_encyclopedia_set_01'),
  binder_notebook: M('binder_notebook'),
  potted_plant_04: M('potted_plant_04'),
  planter_pot_clay: M('planter_pot_clay'),
  vintage_oil_lamp: M('vintage_oil_lamp'),
  desk_lamp_arm_01: M('desk_lamp_arm_01'),
  alarm_clock_01: M('alarm_clock_01'),
  mantel_clock_01: M('mantel_clock_01'),
  standing_picture_frame_01: M('standing_picture_frame_01'),
  rubber_duck_toy: M('rubber_duck_toy'),
  round_spectacles: M('round_spectacles'),
  pot_enamel_01: M('pot_enamel_01'),
  jug_01: M('jug_01'),
  plastic_thermos: M('plastic_thermos'),
};

export const TEX = {
  floorColor: 'assets/tex/floor_Color.jpg',
  floorNormal: 'assets/tex/floor_NormalGL.jpg',
  floorRough: 'assets/tex/floor_Roughness.jpg',
  wallColor: 'assets/tex/wall_Color.jpg',
  wallNormal: 'assets/tex/wall_NormalGL.jpg',
  wallRough: 'assets/tex/wall_Roughness.jpg',
};

export const ENV_HDR = 'assets/env/lythwood_lounge_1k.hdr';

export const DEFAULT_PET = 'pets/default/character.glb';

export const SFX = {
  step1: 'sfx/step1.mp3', step2: 'sfx/step2.mp3', land: 'sfx/land.mp3',
  clink: 'sfx/clink.mp3', clink2: 'sfx/clink2.mp3',
  smash_ceramic: 'sfx/smash_ceramic.mp3', smash_glass: 'sfx/smash_glass.mp3',
  book1: 'sfx/book1.mp3', book2: 'sfx/book2.mp3',
  meow: 'sfx/meow.mp3', purr: 'sfx/purr.mp3', ambience: 'sfx/ambience.mp3',
};

export const CDN = {
  three: 'vendor/three@0.170.0/build/three.module.js',
  draco: 'vendor/three@0.170.0/examples/jsm/libs/draco/gltf/',
};
