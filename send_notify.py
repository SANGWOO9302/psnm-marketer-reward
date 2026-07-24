import json, time, os, sys
import urllib.request, urllib.error, urllib.parse
import jwt

marketer_changed   = os.environ.get('MARKETER_CHANGED', '0') == '1'
partleader_changed = os.environ.get('PARTLEADER_CHANGED', '0') == '1'
print(f"[1] 마케터 변경: {marketer_changed}, 파트장 변경: {partleader_changed}")

if not marketer_changed and not partleader_changed:
    print("발송 대상 없음. 정상 종료.")
    sys.exit(0)

sa = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
private_key = sa["private_key"].replace("\\n", "\n")
PROJECT_ID = sa["project_id"]
print(f"[2] 서비스 계정 로드 완료 (project: {PROJECT_ID})")

now = int(time.time())
claims = {
    "iss": sa["client_email"],
    "scope": "https://www.googleapis.com/auth/datastore https://www.googleapis.com/auth/firebase.messaging",
    "aud": sa.get("token_uri", "https://oauth2.googleapis.com/token"),
    "iat": now,
    "exp": now + 3600,
}
assertion = jwt.encode(claims, private_key, algorithm="RS256")
if isinstance(assertion, bytes):
    assertion = assertion.decode("utf-8")

form = urllib.parse.urlencode({
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "assertion": assertion,
}).encode("utf-8")

token_req = urllib.request.Request(
    sa.get("token_uri", "https://oauth2.googleapis.com/token"),
    data=form,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    with urllib.request.urlopen(token_req) as res:
        access_token = json.loads(res.read())["access_token"]
    print("[3] Access Token 발급 완료")
except urllib.error.HTTPError as e:
    print(f"[오류] Access Token 발급 실패: {e.read().decode()}")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json; charset=UTF-8",
}

def list_tokens():
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/tokens?pageSize=300"
    tokens = []
    while url:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
        for doc in data.get("documents", []):
            fields = doc.get("fields", {})
            tok = fields.get("token", {}).get("stringValue")
            role = fields.get("role", {}).get("stringValue", "")
            if tok:
                tokens.append((tok, role))
        next_token = data.get("nextPageToken")
        if next_token:
            url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/tokens?pageSize=300&pageToken={next_token}"
        else:
            url = None
    return tokens

all_tokens = list_tokens()
print(f"[4] Firestore에서 토큰 {len(all_tokens)}개 로드 완료")

marketer_tokens   = [t for t, r in all_tokens if r == "marketer"]
partleader_tokens = [t for t, r in all_tokens if r == "partleader"]
print(f"    마케터 토큰: {len(marketer_tokens)}개, 파트장 토큰: {len(partleader_tokens)}개")

FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
BASE = "https://sangwoo9302.github.io/psnm-marketer-reward"

# ★ 핵심 수정: "notification" 필드를 빼고 "data"만 전송
# → 브라우저 자동 표시 + 서비스워커 수동 표시가 겹쳐서 2번 뜨던 문제 해결
# → 서비스워커가 data를 읽어 직접 1번만 알림을 그림
def send_to_token(token, title, body, link):
    msg = {
        "message": {
            "token": token,
            "data": {
                "title": title,
                "body": body,
                "link": link,
                "icon": f"{BASE}/icon-192.png",
            },
            "webpush": {
                "headers": {"Urgency": "high"}
            }
        }
    }
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(FCM_URL, data=data, headers=HEADERS)
    try:
        urllib.request.urlopen(req)
        return True
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"    발송 실패 (토큰 일부: {token[:15]}...): {err[:200]}")
        return False

def broadcast(tokens, title, body, link):
    success = 0
    for t in tokens:
        if send_to_token(t, title, body, link):
            success += 1
    print(f"    발송 완료: {success}/{len(tokens)}건 성공")

if marketer_changed and marketer_tokens:
    print("[5] 마케터 알림 발송 중...")
    broadcast(
        marketer_tokens,
        "📊 마케터 성과보상 대시보드 업데이트",
        "새로운 성과보상 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/marketer.html",
    )
elif marketer_changed:
    print("[5] 마케터 알림 대상 토큰 없음")

if partleader_changed and partleader_tokens:
    print("[5] 파트장 알림 발송 중...")
    broadcast(
        partleader_tokens,
        "📊 파트장 KPI 대시보드 업데이트",
        "새로운 파트장 KPI 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/partleader.html",
    )
elif partleader_changed:
    print("[5] 파트장 알림 대상 토큰 없음")

print("[완료]")
