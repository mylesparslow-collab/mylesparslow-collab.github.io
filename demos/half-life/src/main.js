import { mountStrata } from './strata.js';
import { mountAutopsy } from './autopsy.js';
import { mountLedger } from './ledger.js';

const get = (p) => fetch(p).then((r) => (r.ok ? r.json() : null));

const fail = () => { document.getElementById('strata').append(Object.assign(document.createElement('p'), { textContent: 'Couldn\u2019t load the data.' })); };
let casesFile, pages, ledger, textIndex;
try {
  [casesFile, pages, ledger, textIndex] = await Promise.all([
    get('data/cases.json'), get('data/pages.json'), get('data/ledger.json'), get('data/text/index.json'),
  ]);
  if (!casesFile || !pages || !ledger || !textIndex) throw new Error('missing data');
} catch (e) {
  fail();
  throw e;
}
const textIds = new Set(textIndex);
const byId = new Map(casesFile.cases.map((c) => [c[0], c]));
const data = {
  cases: casesFile, byId, pages, ledger, textIds,
  loadText: (id) => (textIds.has(Number(id)) ? get(`data/text/${id}.json`).catch(() => null) : Promise.resolve(null)),
};

mountStrata(document.getElementById('strata'), data);
mountAutopsy(document.getElementById('autopsy'), data);
mountLedger(document.getElementById('ledger'), data);
