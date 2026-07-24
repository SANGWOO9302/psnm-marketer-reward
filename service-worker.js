// service-worker.js
// PWA 오프라인 지원(캐싱) + FCM 푸시 알림 수신 통합

const CACHE_NAME = "reward-dashboard-cache-v3";
const FILES_TO_CACHE = [
  "./index.html",
  "./marketer.html",
  "./partleader.html",
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

// 백그라운드 알림 수신 (앱이 꺼져있거나 다른 화면일 때)
messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "성과보상 Dashboard 업데이트";
  const body  = payload.notification?.body  || "새로운 대시보드가 업로드되었습니다.";
  const link  = payload.fcmOptions?.link || payload.webpush?.fcmOptions?.link || "./index.html";

  self.registration.showNotification(title, {
    body,
    icon: "./icon-192.png",
    badge: "./icon-192.png",
    data: { link }
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

// ===== 토픽 구독 메시지 수신 =====
// index.html / marketer.html / partleader.html에서
// postMessage로 토픽 구독 요청을 받아 처리
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SUBSCRIBE_TOPIC") {
    // 토픽 구독은 서버에서 처리하므로 토큰을 클라이언트로 전달
    event.source.postMessage({
      type: "TOKEN_READY",
      token: event.data.token
    });
  }
});
