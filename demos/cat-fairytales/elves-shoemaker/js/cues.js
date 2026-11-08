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
    BED(0, 10, 'wind', 0.25),
    ONE(0.2, 'page_turn', 0.9),
    ONE(8.6, 'meow_a', 0.3),
  ],
  poor: [
    BED(0, 25, 'fire', 0.12),
    BED(0, 25, 'clock_tick', 0.3),
    BED(0, 25, 'wind', 0.12),
    ...[1.8, 3.2, 4.6, 6.0, 7.4].map((t) => ONE(t, 'scissors_snip', 0.6)),
    ONE(13.2, 'meow_b', 0.3),
    ...[19.4, 20.6, 21.8].map((t) => ONE(t, 'rocking_chair_creak', 0.2)),
  ],
  morning: [
    BED(0, 20, 'birds', 0.4),
    ...[1.2, 2.2, 3.0].map((t) => ONE(t, 'rocking_chair_creak', 0.15)),
    ONE(3.5, 'meow_a', 0.4),
    ONE(7.4, 'door_creak', 0.4), ONE(8.1, 'shop_bell', 0.6),
    ...[11.9, 12.5, 13.1, 13.7].map((t) => ONE(t, 'coins', 0.5)),
    ONE(14.4, 'coins', 0.4),
    ONE(13.9, 'door_creak', 0.35), ONE(14.4, 'shop_bell', 0.6),
    ONE(17.7, 'cheer_pop', 0.4), ONE(17.9, 'meow_c', 0.3),
  ],
  montage: [
    BED(0, 30, 'clock_tick', 0.15),
    ...[1, 2, 3, 4, 5, 6, 7].map((i) => ONE(i * 3.75, 'page_turn', 0.6)),
    ...[0, 2, 4, 6].flatMap((i) => [ONE(i * 3.75 + 1.5, 'scissors_snip', 0.5), ONE(i * 3.75 + 2.2, 'scissors_snip', 0.5)]),
    ...[1, 3, 5, 7].flatMap((i) => [ONE(i * 3.75 + 0.1, 'shop_bell', 0.45), ONE(i * 3.75 + 1.35, 'coins', 0.5), ONE(i * 3.75 + 0.5, 'cheer_pop', 0.25)]),
    ...[1, 3, 5].map((i) => BED(i * 3.75, i * 3.75 + 3.75, 'birds', 0.3, { fade: 0.3 })),
    BED(0, 3.75, 'wind', 0.12, { fade: 0.3 }), BED(7.5, 11.25, 'wind', 0.12, { fade: 0.3 }), BED(15, 30, 'wind', 0.22, { fade: 0.6 }),
  ],
  watch: [
    BED(0, 25, 'wind', 0.2),
    BED(0, 25, 'fire', 0.08),
    BED(2, 10, 'clock_tick', 0.35),
    ...[3, 4.2, 5.4].map((t) => ONE(t, 'rocking_chair_creak', 0.2)),
    ONE(9.6, 'clock_midnight', 0.55),
    ...every(11.2, 17, 0.35, 'tap', 0.1),
    ONE(12.9, 'meow_c', 0.2),
    ONE(17.4, 'tap', 0.3), ONE(18.0, 'tap', 0.3), ONE(18.6, 'tap', 0.3),
    ...every(20.4, 25, 0.9, 'tap_run', 0.3),
  ],
  work: [
    BED(0, 25, 'wind', 0.1),
    BED(0, 25, 'fire', 0.1),
    ...every(1.4, 10.9, 0.45, 'tap', 0.5),
    ...every(1.5, 10.9, 1.35, 'stitch', 0.35),
    ONE(11.0, 'cheer_pop', 0.5), ONE(11.6, 'meow_a', 0.3), ONE(12.2, 'meow_c', 0.3),
    BED(15, 25, 'birds', 0.4, { fade: 3 }),
    ...[18.2, 18.7, 19.2].map((t) => ONE(t, 'tap_run', 0.3)),
    ONE(21.5, 'door_creak', 0.3), ONE(23.2, 'meow_b', 0.4),
  ],
  gifts: [
    BED(0, 20, 'fire', 0.5),
    BED(6, 20, 'purr', 0.3),
    ...[0.6, 1.3, 2.0, 2.7].map((t) => ONE(t, 'scissors_snip', 0.5)),
    ...every(3, 12.5, 1.6, 'stitch', 0.25),
    ONE(2, 'rocking_chair_creak', 0.25), ONE(10, 'rocking_chair_creak', 0.25),
    ONE(16.8, 'cheer_pop', 0.3), ONE(17.5, 'meow_a', 0.35),
  ],
  dance: [
    BED(0, 13, 'wind', 0.15, { fade: 2 }),
    BED(13.5, 25, 'wind', 0.35, { fade: 1 }),
    ONE(5.0, 'cheer_pop', 0.4), ONE(5.5, 'cheer_pop', 0.4), ONE(6.0, 'cheer_pop', 0.4),
    ONE(5.2, 'meow_a', 0.35), ONE(5.7, 'meow_b', 0.35), ONE(6.2, 'meow_c', 0.35),
    ...every(6.4, 12.4, 0.3, 'tap', 0.2),
    ONE(13.6, 'door_creak', 0.4), ONE(14.0, 'shop_bell', 0.5),
    ...every(14.4, 19.5, 0.4, 'tap', 0.18),
    ONE(22.9, 'book_close', 0.8),
  ],
};

// Music runs across scenes, so it is given in film seconds.
// Scenes start at: title 0, poor 10, morning 35, montage 55, watch 85, work 110, gifts 135, dance 155, end 180.
export const MUSIC = [
  BED(0, 55, 'music_largo', 0.3, { loop: false, fade: 2 }),
  BED(55, 85, 'music_allegro', 0.2, { loop: false, fade: 2 }),
  BED(86, 109, 'music_largo', 0.1, { loop: false, fade: 3, offset: 56 }),
  BED(110, 135, 'music_allegro', 0.2, { loop: false, fade: 2, offset: 40 }),
  BED(135, 155, 'music_largo', 0.3, { loop: false, fade: 2, offset: 90 }),
  BED(155, 180, 'music_allegro', 0.35, { loop: false, fade: 2, offset: 70 }),
];
