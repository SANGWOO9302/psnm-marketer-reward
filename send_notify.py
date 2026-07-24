import json, time, os, sys
import urllib.request, urllib.error, urllib.parse
import jwt

# ---------------------------------------------------------------
# 1) 변경 파일 확인
# ---------------------------------------------------------------
marketer_changed   = os.environ.get('MARKETER_CHANGED', '0') == '1'
partleader_changed = os.environ.get('PARTLEADER_CHANGED', '0') == '1'
print(f"[1] 마케터 변경: {marketer_changed}, 파트장 변경: {partleader_changed}")

if not marketer_changed and not partleader_changed:
    print("발송 대상 없음. 정상 종료.")
    sys.exit(0)

# ---------------------------------------------------------------
# 2) 서비스 계정 JSON 로드 및 검증
# ---------------------------------------------------------------
raw = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '')
if not raw.strip():
    print("[오류] FIREBASE_SERVICE_ACCOUNT 시크릿이 비어 있습니다.")
    sys.exit(1)

try:
    sa = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"[오류] 서비스 계정 JSON 파싱 실패: {e}")
    print("→ GitHub Secrets에 JSON 파일 '전체 내용'이 그대로 들어갔는지 확인하세요.")
    sys.exit(1)

# 필수 필드 확인
for key in ("client_email", "private_key", "project_id", "token_uri"):
    if key not in sa:
        print(f"[오류] 서비스 계정 JSON에 '{key}' 필드가 없습니다.")
        sys.exit(1)

print(f"[2] 서비스 계정 로드 완료")
print(f"    project_id  : {sa['project_id']}")
print(f"    client_email: {sa['client_email']}")

# private_key 줄바꿈 정규화 (\n 이스케이프가 문자로 남아있는 경우 복원)
private_key = sa["private_key"]
if "\\n" in private_key:
    print("    private_key: 이스케이프된 \\n 발견 → 실제 줄바꿈으로 변환")
    private_key = private_key.replace("\\n", "\n")

if not private_key.startswith("-----BEGIN"):
    print("[오류] private_key 형식이 올바르지 않습니다 (BEGIN 헤더 없음).")
    sys.exit(1)

print(f"    private_key : 정상 (길이 {len(private_key)}자)")

# ---------------------------------------------------------------
# 3) Access Token 발급
# ---------------------------------------------------------------
TOKEN_URI = sa.get("token_uri", "https://oauth2.googleapis.com/token")
now = int(time.time())

claims = {
    "iss":   sa["client_email"],
    "scope": "https://www.googleapis.com/auth/firebase.messaging",
    "aud":   TOKEN_URI,
    "iat":   now,
    "exp":   now + 3600,
}

try:
    assertion = jwt.encode(claims, private_key, algorithm="RS256")
except Exception as e:
    print(f"[오류] JWT 서명 실패: {e}")
    print("→ private_key가 손상되었을 가능성이 높습니다. 서비스 계정 키를 재발급하세요.")
    sys.exit(1)

# PyJWT 1.x는 bytes를 반환하므로 문자열로 통일
if isinstance(assertion, bytes):
    assertion = assertion.decode("utf-8")

# form body를 정식으로 URL 인코딩
form = urllib.parse.urlencode({
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "assertion":  assertion,
}).encode("utf-8")

token_req = urllib.request.Request(
    TOKEN_URI,
    data=form,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)

try:
    with urllib.request.urlopen(token_req) as res:
        access_token = json.loads(res.read())["access_token"]
    print("[3] Access Token 발급 완료")
except urllib.error.HTTPError as e:
    detail = e.read().decode("utf-8", errors="replace")
    print(f"[오류] Access Token 발급 실패 (HTTP {e.code})")
    print(f"    Google 응답: {detail}")
    print()
    print("    ── 원인별 조치 ──")
    print("    invalid_grant  : 서버 시간 문제이거나 private_key가 손상됨 → 키 재발급")
    print("    invalid_client : client_email이 잘못됨 → 서비스 계정 JSON 재확인")
    print("    invalid_scope  : 권한 범위 문제 → Firebase 프로젝트 권한 확인")
    sys.exit(1)

# ---------------------------------------------------------------
# 4) FCM 발송
# ---------------------------------------------------------------
PROJECT_ID = sa["project_id"]
FCM_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
BASE = "https://sangwoo9302.github.io/psnm-marketer-reward"

def send_fcm(title, body, link):
    msg = {
        "message": {
            "topic": "all-users",
            "notification": {"title": title, "body": body},
            "webpush": {
                "notification": {
                    "title": title,
                    "body":  body,
                    "icon":  f"{BASE}/icon-192.png",
                },
                "fcm_options": {"link": link},
            },
        }
    }
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        FCM_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as res:
            print(f"    발송 성공: {json.loads(res.read())}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"[오류] FCM 발송 실패 (HTTP {e.code})")
        print(f"    Google 응답: {detail}")
        sys.exit(1)

if marketer_changed:
    print("[4] 마케터 알림 발송 중...")
    send_fcm(
        "📊 마케터 성과보상 대시보드 업데이트",
        "새로운 성과보상 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/marketer.html",
    )

if partleader_changed:
    print("[4] 파트장 알림 발송 중...")
    send_fcm(
        "📊 파트장 KPI 대시보드 업데이트",
        "새로운 파트장 KPI 대시보드가 업로드되었습니다. 확인해보세요!",
        f"{BASE}/partleader.html",
    )

print("[완료] 모든 작업이 정상 종료되었습니다.")
