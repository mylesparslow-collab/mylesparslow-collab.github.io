// Sound for every scene, in each scene's local seconds (same format as The Three Brothers).
const ONE = (at, name, vol = 0.6) => ({ at, name, vol });
const BED = (from, to, name, vol = 0.4, o = {}) => ({ from, to, name, vol, loop: o.loop ?? true, fade: o.fade ?? 1, offset: o.offset ?? 0 });

export const CUES = {
  title: [BED(0, 12, 'wind', 0.2), ONE(0.2, 'page_turn', 0.9), BED(4, 12, 'hooves_donkey', 0.25, { fade: 2 })],
  donkey: [
    BED(0, 24, 'hens', 0.35), BED(0, 6, 'hooves_donkey', 0.35),
    ONE(6.2, 'sack_drop', 1.3), ONE(8.5, 'donkey_bray', 0.45), ONE(17, 'donkey_bray', 0.6),
    BED(18, 24, 'hooves_donkey', 0.35),
  ],
  dog: [
    BED(0, 24, 'birds', 0.35), BED(0, 6, 'hooves_donkey', 0.3),
    BED(0, 7, 'dog_pant', 0.3, { fade: 0.5 }), ONE(13.5, 'dog_bark', 0.5), ONE(16.3, 'dog_bark', 0.6), ONE(17, 'dog_bark', 0.5),
    BED(18, 24, 'footsteps_gravel', 0.3),
  ],
  cat: [
    BED(0, 22, 'birds', 0.3), BED(0, 6, 'footsteps_gravel', 0.3),
    ONE(2, 'meow_c', 0.35), ONE(9, 'cat_huff', 0.45), ONE(15.6, 'meow_a', 0.45),
    BED(17, 22, 'footsteps_gravel', 0.3),
  ],
  rooster: [
    BED(0, 22, 'hens', 0.25), ONE(0.3, 'rooster_crow', 0.7), ONE(3.6, 'rooster_crow', 0.6),
    BED(0, 7, 'footsteps_gravel', 0.3), ONE(9, 'rooster_crow', 0.5), ONE(17.3, 'cheer_pop', 0.5),
    BED(18, 22, 'footsteps_gravel', 0.3),
  ],
  forest: [
    BED(0, 26, 'crickets', 0.45), BED(0, 13, 'footsteps_gravel', 0.25),
    ONE(5, 'owl', 0.45), ONE(13.6, 'cheer_pop', 0.4), ONE(18.6, 'rooster_crow', 0.4),
  ],
  robbers: [
    BED(0, 30, 'crickets', 0.3), BED(0, 30, 'tavern', 0.4, { fade: 2 }),
    ONE(3, 'robbers_laugh', 0.5), ONE(9, 'coins', 0.45), ONE(16, 'robbers_laugh', 0.4), ONE(24, 'coins', 0.35),
  ],
  concert: [
    BED(0, 15.5, 'tavern', 0.35), BED(0, 25, 'crickets', 0.25),
    ONE(3.2, 'cheer_pop', 0.4), ONE(5.4, 'cheer_pop', 0.4), ONE(7.6, 'cheer_pop', 0.4),
    ONE(10.1, 'donkey_bray', 0.8), ONE(10.3, 'dog_bark', 0.8), ONE(10.5, 'meow_c', 0.8), ONE(10.7, 'rooster_crow', 0.8),
    ONE(12.6, 'donkey_bray', 0.7), ONE(12.8, 'dog_bark', 0.7), ONE(13, 'meow_b', 0.8), ONE(13.2, 'rooster_crow', 0.7),
    ONE(15.5, 'glass_smash', 1.5), ONE(16.2, 'screams_flee', 0.7), ONE(17, 'running_away', 0.6),
  ],
  return: [
    BED(0, 27, 'crickets', 0.2), BED(0, 27, 'fire', 0.2), BED(0, 27, 'clock_tick', 0.2),
    ONE(1, 'wood_creak', 1.3), ONE(5, 'wood_creak', 1.2), ONE(9.2, 'scratch', 1.6), ONE(9.3, 'cat_huff', 0.6),
    ONE(13.4, 'dog_bark', 0.8), ONE(16, 'thud', 2.5), ONE(17.2, 'rooster_crow', 0.7), ONE(17.8, 'screams_flee', 0.5),
    ONE(18.6, 'running_away', 0.4),
  ],
  end: [
    BED(0, 21, 'fire', 0.45), BED(0, 21, 'purr', 0.3),
    ONE(3, 'meow_a', 0.3), ONE(8, 'meow_b', 0.3), ONE(21.4, 'book_close', 0.8),
  ],
};

// Music in film seconds.
export const MUSIC = [
  BED(0, 12, 'music_road', 0.3, { loop: false, fade: 2 }),
  BED(12, 104, 'music_road', 0.22, { loop: true, fade: 3, offset: 12 }),
  BED(104, 160, 'music_sneaky', 0.25, { loop: true, fade: 3 }),
  BED(185, 212, 'music_sneaky', 0.18, { loop: true, fade: 3, offset: 20 }),
  BED(212, 240, 'music_cosy', 0.32, { loop: false, fade: 3 }),
];
