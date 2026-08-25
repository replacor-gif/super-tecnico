'use strict';

const CACHE_VERSION = 'super-tecnico-shell-v9';
const APP_SHELL = [
  './', './index.html', './proyectos.html', './conductos.html', './ventilacion.html', './tuberias-frigorificas.html', './frigorista.html', './normativa.html', './conectores.html', './plataformas-embebidas.html', './actualizaciones.html',
  './assets/common.css', './assets/app-theme.css', './assets/app-shell.js', './assets/project-core.js', './assets/project-manager.css', './assets/project-manager.js', './assets/super-tecnico-logo.png',
  './assets/duct-designer.css', './assets/duct-designer.js', './assets/ventilation-designer.css', './assets/ventilation-rules.js', './assets/ventilation-designer.js',
  './assets/refrigerant-piping.css', './assets/refrigerant-piping-engine.js', './assets/refrigerant-piping.js', './data/refrigerant-piping/property-grid.json', './data/refrigerant-piping/design-rules.json',
  './assets/connectors.css', './assets/connectors.js', './data/connectors/catalog.json', './data/connectors/sources.json',
  './assets/embedded-platforms.css', './assets/embedded-platforms.js', './data/embedded-platforms/catalog.json', './data/embedded-platforms/guides.json',
  './assets/updates.css', './assets/updates.js', './data/updates/feed.json', './data/core/project-roadmap.json', './data/electroia/engine-audit-report.json', './data/electroia/public-release-readiness.json', './data/electroia/document-profiles.json', './data/electroia/public-execution-policy.json'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_VERSION).then(cache => Promise.allSettled(APP_SHELL.map(url => cache.add(url)))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('super-tecnico-') && key !== CACHE_VERSION).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || url.pathname.includes('/api/')) return;
  event.respondWith(caches.match(request, { ignoreSearch: true }).then(cached => {
    const network = fetch(request).then(response => {
      if (response.ok) caches.open(CACHE_VERSION).then(cache => cache.put(request, response.clone()));
      return response;
    }).catch(() => cached || (request.mode === 'navigate' ? caches.match('./index.html') : Response.error()));
    return cached || network;
  }));
});
