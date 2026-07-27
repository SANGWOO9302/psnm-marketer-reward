import json, time, os, sys
import urllib.request, urllib.error, urllib.parse
import jwt

sa = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
private_key = sa["private_key"].replace("\\n", "\n")
PROJECT_ID = sa["project_id"]

# Access Token 발급
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
with urllib.request.urlopen(token_req) as res:
    access_token = json.loads(res.read())["access_token"]
print("Access Token 발급 완료")

HEADERS = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json; charset=UTF-8",
}

def list_docs(collection):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{collection}?pageSize=300"
    docs = []
    while url:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
        for doc in data.get("documents", []):
            docs.append(doc)
        next_token = data.get("nextPageToken")
        url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{collection}?pageSize=300&pageToken={next_token}" if next_token else None
    return docs

def field_str(fields, key, default=""):
    return fields.get(key, {}).get("stringValue", default)

def field_bool(fields, key, default=False):
    if key not in fields:
        return default
    return fields[key].get("booleanValue", default)

# 1) 완료 처리됐지만 아직 알림 안 보낸 메시지 찾기
messages = list_docs("messages")
targets = []
for doc in messages:
    fields = doc.get("fields", {})
    status = field_str(fields, "status")
    notified = field_bool(fields, "notified", True)  # notified 필드 없으면 이미 알림 필요없는 예전 메시지로 간주
    if status == "완료" and notified is False:
        targets.append({
            "name": doc["name"],  # 전체 문서 경로 (업데이트용)
            "sabun": field_str(fields, "sabun"),
            "role": field_str(fields, "role"),
            "category": field_str(fields, "category"),
        })

print(f"완료 처리된 미알림 메시지: {len(targets)}건")

if not targets:
    print("발송 대상 없음. 종료.")
    sys.exit(0)

# 2) 토큰 목록 로드 (sabun 기준 매칭)
tokens = list_docs("tokens")
sabun_token_map = {}  # sabun -> [token, ...]
for doc in tokens:
    fields = doc.get("fields", {})
    sabun = field_str(fields, "sabun")
    token = field_str(fields, "token")
    if sabun and token:
        sabun_token_map.setdefault(sabun, []).append(token)

FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
BASE = "https://sangwoo9302.github.io/psnm-marketer-reward"

def send_push(token, title, body):
    msg = {
        "message": {
            "token": token,
            "data": {
                "title": title,
                "body": body,
                "link": f"{BASE}/index.html",
                "icon": f"{BASE}/icon-192.png",
                "tag": "message-completed",
            },
            "webpush": {"headers": {"Urgency": "high"}}
        }
    }
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(FCM_URL, data=data, headers=HEADERS)
    try:
        urllib.request.urlopen(req)
        return True
    except urllib.error.HTTPError as e:
        print(f"    발송 실패: {e.read().decode()[:150]}")
        return False

def patch_notified_true(doc_full_name):
    # doc_full_name: projects/.../documents/messages/xxxx
    url = f"https://firestore.googleapis.com/v1/{doc_full_name}?updateMask.fieldPaths=notified"
    body = {"fields": {"notified": {"booleanValue": True}}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="PATCH")
    try:
        urllib.request.urlopen(req)
        return True
    except urllib.error.HTTPError as e:
        print(f"    notified 갱신 실패: {e.read().decode()[:150]}")
        return False

# 3) 발송 + notified 처리
sent = 0
for t in targets:
    tokens_for_sabun = sabun_token_map.get(t["sabun"], [])
    if not tokens_for_sabun:
        print(f"    사번 {t['sabun']}: 등록된 토큰 없음 (알림 발송 스킵, notified만 처리)")
    else:
        for tok in tokens_for_sabun:
            if send_push(tok, "✅ 문의가 완료 처리되었습니다",
                          f"[{t['category']}] 문의하신 내용이 완료 처리되었습니다."):
                sent += 1
    patch_notified_true(t["name"])

print(f"완료: 총 {sent}건 알림 발송, {len(targets)}건 notified 갱신")
