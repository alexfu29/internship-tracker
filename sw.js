/* Service worker: the app opens with no network, and never serves you stale
   code when you have one.

   Those two goals usually fight. The standard PWA recipe is cache-first,
   which loads instantly offline and then serves the old app for a session —
   or forever, if the update dance goes wrong. That failure has already cost
   this project three rounds of "I don't see any changes", so it is the one
   outcome this file is written to prevent.

   So: NETWORK-FIRST for everything this app owns.

     online   → fetch it, use it, and keep a copy
     offline  → serve the copy from the last time you were online

   Fresh whenever the network can answer; working whenever it can't. The cost
   is that a load waits on the network instead of painting from cache — one
   file from a CDN, which is a fair price for never wondering which version
   you are looking at.

   What it deliberately does NOT touch: anything cross-origin. api.github.com,
   the profile reader, the model endpoints and the local agent on 127.0.0.1
   all go straight past. Caching a sync response is how you would resurrect
   deleted contacts, and caching a LinkedIn read is how a stale profile would
   verify as current. Your data lives in localStorage and syncs through the
   GitHub API; this file is only ever about the app's own code.

   Bump VERSION whenever index.html changes. It names the cache, so a bump
   is what evicts the old copy. It does not have to match APP_VERSION in
   index.html — that one is what's displayed, and it is true by construction
   because it lives in the file being executed. */

var VERSION = "2026-08-20c";
var CACHE = "internship-tracker-" + VERSION;
var SHELL = "./";

self.addEventListener("install", function (e) {
  // There is only ever one page, and network-first means an activating worker
  // can't serve anything stale — so there is nothing to gain by waiting.
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(function (c) { return c.add(SHELL); })
      // A failed precache must not fail the install: the fetch handler fills
      // the cache on the first successful load anyway, and an uninstalled
      // worker would mean no offline at all.
      .catch(function () { })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        // Only ever delete caches this file made. Something else on
        // github.io may own the others.
        if (k !== CACHE && k.indexOf("internship-tracker-") === 0) {
          return caches.delete(k);
        }
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;

  var url;
  try { url = new URL(req.url); } catch (err) { return; }
  if (url.origin !== self.location.origin) return;   // see the note above

  /* `cache: "no-cache"` is the whole point of this line, and leaving it off
     made the first version of this file a no-op.

     "Network-first" only means the worker asks the network before the Cache
     API. It says nothing about the browser's own HTTP cache, which sits
     underneath and will happily answer a plain fetch() from a still-fresh
     entry — and GitHub Pages serves this file with max-age=600. So the ten
     minutes of staleness this worker was written to eliminate flowed straight
     through it: the page ran the previous build while the worker sat there
     believing it had gone to the network.

     no-cache does not mean "don't cache". It means revalidate: send the
     ETag, take a 304 when nothing changed. So the cost is a conditional
     request, not a re-download.

     Requested by URL rather than by passing `req`, because a navigation
     request cannot be reconstructed with a different cache mode. Same-origin
     GET only, so nothing is lost by dropping the original Request object. */
  e.respondWith(
    fetch(req.url, { cache: "no-cache", credentials: "same-origin" }).then(function (resp) {
      // Only keep a copy of a real answer. Caching a 404 or an opaque error
      // would hand it back as the offline version forever after.
      if (resp && resp.ok && resp.type === "basic") {
        var copy = resp.clone();
        caches.open(CACHE).then(function (c) { c.put(req.url, copy); });
      }
      return resp;
    }).catch(function () {
      // Offline. ignoreSearch so ?d=2026-08-20 and the ?cb= cache-busters
      // still match the copy that was saved without them.
      return caches.match(req, { ignoreSearch: true }).then(function (hit) {
        if (hit) return hit;
        if (req.mode === "navigate") return caches.match(SHELL);
        return Response.error();
      });
    })
  );
});

// The page asks for this to show you what it is actually running, rather than
// asserting a version number that nothing checked.
self.addEventListener("message", function (e) {
  if (e.data === "version" && e.source) e.source.postMessage({ swVersion: VERSION });
});
