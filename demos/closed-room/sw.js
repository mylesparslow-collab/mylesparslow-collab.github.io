// Closed Room service worker: keeps the app and its code library available
// offline, so a meeting can be transcribed with the network switched off.
// Model weights are cached separately by the library (Cache Storage
// "transformers-cache"). Nothing is ever uploaded from here.
const SHELL = "closed-room-shell-v2";
const CODE = "closed-room-code-v1";
const SHELL_FILES = ["./", "./index.html", "./worker.js", "./icon.svg", "./sample-meeting.mp3"];

const LIB = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/dist/";
const CODE_FILES = ["transformers.min.js", "ort-wasm-simd-threaded.jsep.mjs", "ort-wasm-simd-threaded.jsep.wasm"].map((f) => LIB + f);

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches
      .open(SHELL)
      .then((c) => c.addAll(SHELL_FILES))
      // Library code is cached up front so offline works from the first visit.
      // A failure here is not fatal: the fetch handler caches it on first use.
      .then(() => caches.open(CODE).then((c) => c.addAll(CODE_FILES)).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((ks) => Promise.all(ks.filter((k) => k.startsWith("closed-room-") && k !== SHELL && k !== CODE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Pinned library code from the CDN: cache first, it never changes.
  if (url.hostname === "cdn.jsdelivr.net") {
    e.respondWith(
      caches.open(CODE).then(async (c) => {
        const hit = await c.match(req);
        if (hit) return hit;
        const res = await fetch(req);
        if (res.ok) c.put(req, res.clone());
        return res;
      })
    );
    return;
  }

  // The app itself: network first so updates arrive, cache when offline.
  if (url.origin === self.location.origin) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(SHELL).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req, { ignoreSearch: true }).then((r) => r || caches.match("./index.html")))
    );
  }
});
