// firebase-messaging-sw.js
// FCM(푸시 알림) 전용 서비스워커
// ⚠️ 아래 firebaseConfig 값을 Firebase 콘솔에서 복사한 실제 값으로 반드시 교체해야 알림이 작동합니다.
// 콘솔 위치: 프로젝트 설정(톱니바퀴) > 일반 탭 > "내 앱" 섹션 > SDK 설정 및 구성

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

// 앱이 백그라운드(화면 꺼짐/다른 앱 사용 중)일 때 알림 표시
messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "성과보상 Dashboard 업데이트";
  const options = {
    body: payload.notification?.body || "새로운 대시보드가 업로드되었습니다.",
    icon: "./icon-192.png",
    badge: "./icon-192.png"
  };
  self.registration.showNotification(title, options);
});
