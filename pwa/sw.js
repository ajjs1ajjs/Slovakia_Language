/* Offline-first: app shell + lessons.json кешуємо при install, уроки/аудіо — при читанні */
const V = 'sk-pwa-v4';
const SHELL = ['./','index.html','style.css','app.js','manifest.webmanifest','icon.svg','lessons.json'];
self.addEventListener('install', e=>{
  e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e=>{
  if(e.request.method!=='GET') return;
  e.respondWith(caches.match(e.request).then(hit=>{
    const net = fetch(e.request).then(r=>{
      if(r.ok){ const cp=r.clone(); caches.open(V).then(c=>c.put(e.request,cp)); }
      return r;
    }).catch(()=>hit);
    return hit || net;
  }));
});
