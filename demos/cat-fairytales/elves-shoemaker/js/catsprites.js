// Pixel-art sprites for Newton, Skippy and Simba.
// Each sprite is a grid of palette keys; '.' is transparent.
//   o outline   b fur   s fur shade   m stripes   l muzzle/belly   c chest spot
//   w blaze     a paws  e iris        k pupil     h eye shine      p pink   q mouth
//   C small chest tuft (white on Simba)

export const SIT = [
  '...o..........o...',
  '..opo........opo..',
  '..obpo......opbo..',
  '..obppooooooppbo..',
  '.obbbbmwwwwmbbbbo.',
  '.obbbmbbwwbbmbbbo.',
  'obbbbbbbwwbbbbbbbo',
  'obbbkhbbwwbbkhbbbo',
  'obbbekbbllbbekbbbo',
  'osbbbbllppllbbbbso',
  '.osmbblqllqlbbmso.',
  '..ossbllllllbsso..',
  '...osbllccllbso...',
  '..osbbllCCllbbso..',
  '..osbbllllllbbso..',
  '.osbbbllllllbbbso.',
  '.osbbbbllllbbbbso.',
  '.osbaabbllbbaabso.',
  '.oaaaaobllboaaaao.',
  '..oooo.oooo.oooo..',
];

// Tail overlays drawn from column 15, rows 9..19 of SIT.
export const SIT_TAIL = [
  [
    '.......',
    '.....o.',
    '....obo',
    '....obo',
    '....obo',
    '...obo.',
    '...obo.',
    '..obso.',
    '.obso..',
    'osso...',
    'oo.....',
  ],
  [
    '.....oo',
    '....obo',
    '....obo',
    '...obo.',
    '...obo.',
    '...obo.',
    '...obo.',
    '..obso.',
    '.obso..',
    'osso...',
    'oo.....',
  ],
];

// Eye/face row overrides for SIT (rows 7 and 8).
export const SIT_FACES = {
  open: null,
  blink: ['obbbbbbbwwbbbbbbbo', 'obbkkkbbllbbkkkbbo'],
  happy: ['obbbbkbbwwbbbkbbbo', 'obbkbbkbllbkbbkbbo'],
  up: ['obbbhkbbwwbbhkbbbo', 'obbbeebbllbbeebbbo'],
  side: ['obbbbkhbwwbbbkhbbo', 'obbbbekbllbbbekbbo'],
};

// Paws raised for typing (rows 16..19 replaced).
export const SIT_TYPE = [
  [
    '.oaaobbbllbbbbbso.',
    '.oaaobbllllbbaabo.',
    '..oo.obllllboaaao.',
    '......oooooo.ooo..',
  ],
  [
    '.osbbbbllllbboaao.',
    '.obaabbllllbboaao.',
    '.oaaaobllllbo.oo..',
    '..ooo.oooooo......',
  ],
];

// Walking, side view, facing right.
const WALK_TOP = [
  '..................o...o...',
  '.................opo.opo..',
  '.................obpoopbo.',
  '....o...........obbbbbbbo.',
  '...obo..........obmbmbbbbo',
  '...obo..........obbbbkhbbo',
  '...obo..........obbbbekllo',
  '....obooooooooooobbbbbllpo',
  '.....obbmbbmbbmbbbbbbllqo.',
  '.....obbmbbmbbmbbsbllloo..',
  '.....osbbbbbbbbbbbsbCco...',
  '.....osbbbbbbbbbbbbllllo..',
  '.....ossllllllllllllllo...',
];
const WALK_LEGS = [
  [
    '.....osao.osao...oslo.oslo',
    '.....oaao.oaao...oaao.oaao',
    '......oo...oo.....oo...oo.',
  ],
  [
    '......osao.osao.oslo.oslo.',
    '......oaao.oaao.oaao.oaao.',
    '.......oo...oo...oo...oo..',
  ],
  [
    '.....oso..osao...oso..oslo',
    '....oaao..oaao..oaao..oaao',
    '.....oo....oo....oo....oo.',
  ],
  [
    '......osao.osao.oslo.oslo.',
    '......oaao.oaao.oaao.oaao.',
    '.......oo...oo...oo...oo..',
  ],
];
export const WALK = WALK_LEGS.map((legs) => [...WALK_TOP, ...legs]);

// Curled up asleep.
export const SLEEP = [
  [
    '..........................',
    '.........oooooooo.........',
    '.......oobmbbmbbmboo......',
    '.....oobbmbbmbbmbbbboo....',
    '..o.obbbbbbbbbbbbbbbbbo...',
    '.opoobbbbbbbbbbbbbbbbbbo..',
    '.obpobbbbbbbbbbbbbbbbbbbo.',
    'obbbbbobbbbbbbbbbbbbbbbbo.',
    'obkkbbbobbbbbbbbbbbbbbbbo.',
    'ollpbbbosbbbbbbbbbbbbbbso.',
    '.ollllossssssssbbbbbbbbso.',
    '..ooooaaooooooosbbbbbbbo..',
    '.....oaao.....ossssssoo...',
    '......oo.......oooooo.....',
  ],
  [
    '..........................',
    '..........................',
    '.........oooooooo.........',
    '.......oobmbbmbbmboo......',
    '..o..oobbmbbmbbmbbbboo....',
    '.opoobbbbbbbbbbbbbbbbbo...',
    '.obpobbbbbbbbbbbbbbbbbbo..',
    'obbbbbobbbbbbbbbbbbbbbbbo.',
    'obkkbbbobbbbbbbbbbbbbbbbo.',
    'ollpbbbosbbbbbbbbbbbbbbso.',
    '.ollllossssssssbbbbbbbbso.',
    '..ooooaaooooooosbbbbbbbo..',
    '.....oaao.....ossssssoo...',
    '......oo.......oooooo.....',
  ],
];

export const LAPTOP = [
  '..oooooooooooooo..',
  '..oggggggggggggo..',
  '..oggggggggggggo..',
  '..ogggggpgpggggo..',
  '..ogggggpppggggo..',
  '..oggggggpgggggo..',
  '..oggggggggggggo..',
  'oooooooooooooooooo',
  'oddddddddddddddddo',
  'oooooooooooooooooo',
];

export const YARN = [
  '..ooo..',
  '.oyyzo.',
  'oyzyyzo',
  'ozyyzyo',
  'oyyzyyo',
  '.ozyyo.',
  '..ooo.t',
];

export const HEART = ['.pp.pp.', 'ppppppp', 'ppppppp', '.ppppp.', '..ppp..', '...p...'];
export const ZED = ['zzzz', '..z.', '.z..', 'zzzz'];
export const BUBBLE = [
  '.ooooooo.',
  'owwwwwwwo',
  'owwwwwwwo',
  'owwwwwwwo',
  'owwwwwwwo',
  '.ooooooo.',
  '..oo.....',
  '.o.......',
];

// ---------- toys & extra poses ----------

export const PICKLE = [
  '..ooooo..',
  '.ogGgGgo.',
  'ogGkgkGgo',
  'oGgGqGgGo',
  '.oGgGgGo.',
  '..ooooo..',
];

export const MOUSE = [
  '..oo......',
  '.opxo.....',
  'oxxxxooo..',
  'pkxxxxxxo.',
  '.oooooooTT',
];

export const BOX_BACK = [
  'oo....................oo',
  'oBo..................oBo',
  '.oBooooooooooooooooooBo.',
  '..oDDDDDDDDDDDDDDDDDDo..',
];
export const BOX_FRONT = [
  '..oooooooooooooooooooo..',
  '..oBBBBBBBBEEBBBBBBBBo..',
  '..oBBBBBBBBEEBBBBBBBBo..',
  '..oBBBBBBBBBBBBBBBBBBo..',
  '..oBBBBBBBBBBBBBBBBBBo..',
  '..oDDDDDDDDDDDDDDDDDDo..',
  '..oooooooooooooooooooo..',
];

// Mouth overrides for SIT row 10.
export const SIT_MOUTHS = {
  yawn: '.osmbblkppklbbmso.',
  meow: '.osmbbllkkllbbmso.',
};

// A front paw raised beside the head (for batting the worm). Drawn on a sprite padded 3px left.
export const PAW_UP = [
  ['.oo..', 'oaao.', 'oaao.', 'obbo.', '.obo.', '.obbo', '..obo', '..obo', '...oo'],
  ['.....', '.....', '.oo..', 'oaao.', 'oaao.', 'obbo.', '.obbo', '..obo', '...oo'],
];

// A paw lifted to the mouth for grooming (cols 6..11).
export const GROOM_PAW = [
  ['.oooo.', 'oaaaao', 'oaaaao', '.obbo.', '.obbo.'],
  ['.oooo.', 'oaaaao', 'oaaaao', 'oaaaao', '.obbo.', '.obbo.'],
];
