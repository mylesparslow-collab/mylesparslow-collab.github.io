// Tan Lines offline shell. Page: network first, so new builds arrive. Fonts and history files: cache first.
const C = 'tanlines-20261119T213422Z';
self.addEventListener('install', e => { e.waitUntil(caches.open(C).then(c => c.addAll(['./', 'fonts/Anybody.ttf', 'fonts/InstrumentSans.ttf', 'fonts/GeistMono.ttf'])).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('tanlines-') && k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;       // live scores always go straight to the network
  if (e.request.mode === 'navigate') { e.respondWith(fetch(e.request).then(r => { const cp = r.clone(); caches.open(C).then(c => c.put('./', cp)); return r; }).catch(() => caches.match('./'))); return; }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => { if (r.ok) { const cp = r.clone(); caches.open(C).then(c => c.put(e.request, cp)); } return r; })));
});
