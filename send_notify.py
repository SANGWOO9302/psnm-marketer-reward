import json, time, os, sys, urllib.request
import jwt

# 변경 파일 확인
commits = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
changed = set()
for c in commits:
    changed.update(c.get('modified', []))
    changed.update(c.get('added', []))

marketer_changed = 'marketer.html' in changed
partleader_changed = 'partleader.html' in changed
print(f"마케터 변경: {marketer_changed}, 파트장 변경: {partleader_changed}")

if not marketer_changed and not partleader_changed:
    print("알림 발송 대상 없음. 종료.")
    sys.exit(0)

# Access Token 발급
sa = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
now = int(time.time())
payload = {
    "iss": sa["client_email"],
    "scope": "https://www.googleapis.com/auth/firebase.messaging",
    "aud": "https://oauth2.googleapis.com/token",
    "iat": now,
    "exp": now + 3600
}
signed = jwt.encode(payload, sa["private_key"], algorithm="RS256")
data = ("grant_type=urn%3Aietf%3Aparams%3Aoauth2%3Agrant-type%3Ajwt-bearer&assertion=" + signed).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
res = urllib.request.urlopen(req)
token = json.loads(res.read())["access_token"]
print("Access Token 발급 완료")

FCM_URL = "https://fcm.googleapis.com/v1/projects/psnm-wholesale-reward/messages:send"
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
BASE = "https://sangwoo9302.github.io/psnm-marketer-reward"

def send_fcm(title, body, link):
    msg = {
        "message": {
            "topic": "all-users",
            "notification": {"title": title, "body": body},
            "webpush": {"fcm_options": {"link": link}}
        }
    }
    body_bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(FCM_URL, data=body_bytes, headers=HEADERS)
    try:
        resp = urllib.request.urlopen(r)
        print("발송 성공:", json.loads(resp.read()))
    except Exception as e:
        print("발송 실패:", e)

if marketer_changed:
    send_fcm(
        "📊 마케터 성과보상 대시보드 업데이트",
        "새로운 성과보상 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/marketer.html"
    )

if partleader_changed:
    send_fcm(
        "📊 파트장 KPI 대시보드 업데이트",
        "새로운 파트장 KPI 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/partleader.html"
    )
