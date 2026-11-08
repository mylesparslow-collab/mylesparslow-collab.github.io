// Sound for every scene, in each scene's local seconds.
// [at, name, vol]                       a one-shot that plays when the clock passes `at`
// [from, to, name, vol, { loop, fade }] a bed or music that plays over a span (and resumes after a seek)
const ONE = (at, name, vol = 0.6) => ({ at, name, vol });
const BED = (from, to, name, vol = 0.4, o = {}) => ({ from, to, name, vol, loop: o.loop ?? true, fade: o.fade ?? 1, offset: o.offset ?? 0 });
const every = (from, to, step, name, vol) => {
  const out = [];
  for (let t = from; t < to; t += step) out.push(ONE(+t.toFixed(2), name, vol));
  return out;
};

export const CUES = {
  title: [
    BED(0, 15, 'wind', 0.2),
    ONE(0.2, 'page_turn', 0.9),
    ONE(9.2, 'meow_a', 0.35),
  ],
  cottage: [
    BED(0, 25, 'fire', 0.55),
    BED(0, 25, 'clock_tick', 0.3),
    BED(0, 8, 'purr', 0.3),
    ONE(2, 'rocking_chair_creak', 0.3), ONE(9, 'rocking_chair_creak', 0.25), ONE(17, 'rocking_chair_creak', 0.3),
    ONE(9.6, 'meow_b', 0.45), ONE(10.6, 'meow_a', 0.4), ONE(11.6, 'meow_c', 0.35),
  ],
  crossroads: [
    BED(0, 15, 'birds', 0.45),
    ONE(0.4, 'footsteps_gravel', 0.45), ONE(3, 'footsteps_gravel', 0.35),
    ONE(6.2, 'meow_b', 0.3),
    BED(7, 15, 'wind', 0.25),
    ONE(9.5, 'crow', 0.35),
    ONE(9, 'footsteps_gravel', 0.3),
  ],
  montage: [
    ...every(0.8, 24, 2.6, 'scissors_snip', 0.55),
    ...every(1.6, 24, 2.6, 'anvil_ting', 0.45),
    ...every(2.3, 24, 2.6, 'sword_swish', 0.4),
    ONE(4, 'bellows', 0.35), ONE(13, 'quench_hiss', 0.35), ONE(9, 'razor_strop', 0.35), ONE(17.5, 'sword_clash', 0.35),
    BED(18.75, 25, 'wind', 0.25),
  ],
  home: [
    BED(0, 15, 'birds', 0.45),
    ONE(0, 'footsteps_gravel', 0.35),
    ONE(2, 'door_creak', 0.5),
    ONE(5.4, 'meow_a', 0.4), ONE(5.9, 'meow_b', 0.4), ONE(6.4, 'meow_c', 0.35),
    BED(6, 15, 'purr', 0.3),
    ONE(10, 'kettle', 0.2),
  ],
  skippy: [
    BED(0, 30, 'birds', 0.35),
    ...[2, 2.5, 3, 3.5, 4.1].map((t) => ONE(t, 'hare_thump', 0.5)),
    ONE(5.8, 'razor_strop', 0.5),
    BED(8.6, 24.5, 'grass_run', 0.5, { fade: 0.4 }),
    ONE(12, 'lather', 0.8), ONE(13.4, 'lather', 0.8), ONE(14.8, 'lather', 0.8),
    ONE(16, 'razor_scrape', 0.8), ONE(17.6, 'razor_scrape', 0.8), ONE(19.2, 'razor_scrape', 0.8), ONE(20.8, 'razor_scrape', 0.8),
    ONE(25.1, 'cheer_pop', 0.5), ONE(25.8, 'meow_a', 0.45),
  ],
  newton: [
    BED(0, 27, 'hoofbeats_gallop', 0.7, { fade: 4 }),
    BED(0, 27, 'carriage_rattle', 0.45, { fade: 4 }),
    ONE(6.4, 'meow_b', 0.45),
    ONE(7.5, 'horse_whinny', 0.45),
    ...[12.2, 15.2, 18.2, 21.2].map((t) => ONE(t, 'horseshoe_clank', 0.5)),
    ...[13, 16, 19, 22].map((t) => ONE(t, 'anvil_ting', 0.8)),
    ONE(25.4, 'cheer_pop', 0.5), ONE(26.5, 'horse_whinny', 0.3),
  ],
  simba: [
    BED(0, 12, 'wind', 0.4, { fade: 2 }),
    BED(5, 12, 'rain_light', 0.5, { fade: 2 }),
    BED(9, 35.5, 'rain_heavy', 0.7, { fade: 3 }),
    ONE(7.2, 'cat_huff', 0.5),
    ONE(12.4, 'sword_clash', 0.5),
    BED(14.5, 34.5, 'sword_whoosh_loop', 0.5, { fade: 0.5 }),
    ONE(18.05, 'thunder_a', 0.9), ONE(26.55, 'thunder_b', 0.9), ONE(31.05, 'thunder_a', 0.8),
    ONE(34.6, 'sword_swish', 0.5),
    BED(35.5, 40, 'birds', 0.3, { fade: 2 }),
    ONE(36.4, 'meow_c', 0.35),
  ],
  verdict: [
    BED(0, 25, 'fire', 0.5),
    BED(0, 25, 'clock_tick', 0.25),
    ONE(3, 'rocking_chair_creak', 0.3),
    ONE(9.1, 'meow_a', 0.4),
    ONE(19.6, 'meow_b', 0.4), ONE(20.1, 'meow_c', 0.4),
    BED(16, 25, 'purr', 0.35),
  ],
  end: [
    BED(0, 14, 'fire', 0.4, { fade: 3 }),
    BED(0, 14, 'purr', 0.4, { fade: 3 }),
    BED(0, 12, 'clock_tick', 0.2, { fade: 2 }),
    ONE(12.4, 'book_close', 0.8),
  ],
};

// Music runs across scenes, so it is given in film seconds.
export const MUSIC = [
  BED(0, 41, 'music_home', 0.3, { loop: false, fade: 2 }),
  BED(40, 55, 'music_home', 0.25, { loop: false, fade: 2, offset: 41 }),
  BED(55, 81, 'music_lively', 0.35, { loop: false, fade: 2 }),
  BED(80, 95, 'music_home', 0.25, { loop: false, fade: 2, offset: 56 }),
  BED(95, 154, 'music_trials', 0.22, { loop: false, fade: 3 }),
  BED(194, 240, 'music_tender', 0.32, { loop: false, fade: 3 }),
];
