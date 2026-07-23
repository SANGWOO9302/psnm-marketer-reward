// service-worker.js
// PWA 오프라인 지원(캐싱) + FCM 푸시 알림 수신을 하나의 서비스워커로 통합

const CACHE_NAME = "reward-dashboard-cache-v2";
const FILES_TO_CACHE = [
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png"
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

// ===== FCM 푸시 알림 =====
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

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "성과보상 Dashboard 업데이트";
  const options = {
    body: payload.notification?.body || "새로운 대시보드가 업로드되었습니다.",
    icon: "./icon-192.png",
    badge: "./icon-192.png"
  };
  self.registration.showNotification(title, options);
});
