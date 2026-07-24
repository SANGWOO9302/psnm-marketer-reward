import json, time, os, urllib.request, urllib.error
import jwt

marketer_changed   = os.environ.get('MARKETER_CHANGED', '0') == '1'
partleader_changed = os.environ.get('PARTLEADER_CHANGED', '0') == '1'
print(f"마케터 변경: {marketer_changed}, 파트장 변경: {partleader_changed}")

if not marketer_changed and not partleader_changed:
    print("알림 발송 대상 없음. 종료.")
    exit(0)

# Access Token 발급
sa = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
now = int(time.time())
jwt_payload = {
    "iss": sa["client_email"],
    "scope": "https://www.googleapis.com/auth/firebase.messaging",
    "aud": "https://oauth2.googleapis.com/token",
    "iat": now,
    "exp": now + 3600
}
signed = jwt.encode(jwt_payload, sa["private_key"], algorithm="RS256")
token_data = (
    "grant_type=urn%3Aietf%3Aparams%3Aoauth2%3Agrant-type%3Ajwt-bearer"
    "&assertion=" + signed
).encode()
token_req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=token_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
token_res = urllib.request.urlopen(token_req)
access_token = json.loads(token_res.read())["access_token"]
print("Access Token 발급 완료")

PROJECT_ID = "psnm-wholesale-reward"
FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
BASE = "https://sangwoo9302.github.io/psnm-marketer-reward"

def send_fcm(title, body, link):
    msg = {
        "message": {
            "topic": "all-users",
            "notification": {
                "title": title,
                "body": body
            },
            "webpush": {
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": f"{BASE}/icon-192.png"
                },
                "fcm_options": {
                    "link": link
                }
            }
        }
    }
    body_bytes = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        FCM_URL,
        data=body_bytes,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"발송 성공: {result}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"발송 실패 ({e.code}): {err_body}")
        raise

if marketer_changed:
    print("마케터 알림 발송 중...")
    send_fcm(
        "📊 마케터 성과보상 대시보드 업데이트",
        "새로운 성과보상 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/marketer.html"
    )

if partleader_changed:
    print("파트장 알림 발송 중...")
    send_fcm(
        "📊 파트장 KPI 대시보드 업데이트",
        "새로운 파트장 KPI 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/partleader.html"
    )

print("완료")
