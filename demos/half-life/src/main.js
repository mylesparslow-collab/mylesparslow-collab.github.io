import { mountStrata } from './strata.js';
import { mountAutopsy } from './autopsy.js';
import { mountLedger } from './ledger.js';

const get = (p) => fetch(p).then((r) => (r.ok ? r.json() : null));

const [casesFile, pages, ledger] = await Promise.all([
  get('data/cases.json'), get('data/pages.json'), get('data/ledger.json'),
]);
const byId = new Map(casesFile.cases.map((c) => [c[0], c]));
const data = {
  cases: casesFile, byId, pages, ledger,
  loadText: (id) => get(`data/text/${id}.json`).catch(() => null),
};

mountStrata(document.getElementById('strata'), data);
mountAutopsy(document.getElementById('autopsy'), data);
mountLedger(document.getElementById('ledger'), data);
