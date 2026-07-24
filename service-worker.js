// service-worker.js
// PWA 오프라인 지원(캐싱) + FCM 푸시 알림 수신 통합

const CACHE_NAME = "reward-dashboard-cache-v6";
const FILES_TO_CACHE = [
  "./index.html",
  "./marketer.html",
  "./partleader.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./badge-96.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// ===== FCM 알림 수신 =====
importScripts("https://www.gstatic.com/firebasejs/10.13.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.13.0/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyDGU5cSiIA4ihm_7IgMDCXw6WZFY6cHnJY",
  authDomain: "psnm-wholesale-reward.firebaseapp.com",
  projectId: "psnm-wholesale-reward",
  storageBucket: "psnm-wholesale-reward.firebasestorage.app",
  messagingSenderId: "1064215508901",
  appId: "1:1064215508901:web:38ee1c80cd1a5acc8b1a4c",
  measurementId: "G-TWLRNXQRT9"
});

const messaging = firebase.messaging();

// ★ data 전용 메시지를 받아 서비스워커가 직접 1번만 알림 표시
// (notification 필드를 안 쓰므로 브라우저 자동 표시와 겹치지 않음)
messaging.onBackgroundMessage((payload) => {
  const data  = payload.data || {};
  const title = data.title || "성과보상 Dashboard 업데이트";
  const body  = data.body  || "새로운 대시보드가 업로드되었습니다.";
  const link  = data.link  || "./index.html";
  const icon  = data.icon  || "./icon-192.png";

  self.registration.showNotification(title, {
    body,
    icon,
    badge: "./badge-96.png", // 안드로이드 상태바용 투명 배경 흰색 실루엣 아이콘
    data: { link },
    tag: data.tag || "dashboard-update-" + Date.now() // role별 고유 tag → 서로 다른 알림은 겹치지 않고 각각 유지
  });
});

// 알림 클릭 시 해당 대시보드로 이동
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const link = event.notification.data?.link || "./index.html";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && "focus" in client) {
          client.navigate(link);
          return client.focus();
        }
      }
      return clients.openWindow(link);
    })
  );
});
