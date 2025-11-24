# Kurz AI Studio 배포 가이드 (초보자용)

인터넷에 서비스를 올려서 다른 사람들도 쓸 수 있게 만드는 방법입니다.

---

## 먼저 알아야 할 것들

### 배포가 뭔가요?
지금은 여러분 컴퓨터에서만 이 프로그램이 돌아가죠?
**배포**는 이걸 인터넷 서버에 올려서 `https://kurz.com` 같은 주소로
누구나 접속할 수 있게 만드는 거예요.

### 뭐가 필요한가요?
1. **서버** - 24시간 켜져있는 컴퓨터 (클라우드 서비스 이용)
2. **도메인** - `kurz.com` 같은 주소 (선택사항, 없어도 됨)
3. **API 키들** - 이미 갖고 있는 것들 (Gemini, ElevenLabs)

---

## 전체 과정 미리보기

```
1단계: 무료 서비스 가입 (10분)
   ↓
2단계: Google Cloud 설정 (15분)
   ↓
3단계: 비밀 키 등록 (5분)
   ↓
4단계: 배포 명령어 실행 (10분)
   ↓
5단계: Google 로그인 설정 (5분)
   ↓
완료! 🎉
```

---

# 1단계: 무료 서비스 가입 (10분)

우리 앱은 데이터베이스(PostgreSQL)와 캐시(Redis)가 필요해요.
이걸 무료로 제공하는 서비스에 가입합니다.

## 1-1. Neon 가입 (데이터베이스)

1. https://neon.tech 접속
2. **"Sign Up"** 클릭
3. GitHub 또는 Google 계정으로 가입
4. **"Create a project"** 클릭
5. 설정:
   - Project name: `kurz-studio`
   - Region: **Asia Pacific (Singapore)** 선택 ← 한국과 가까워서 빠름
6. **"Create project"** 클릭
7. 화면에 나오는 **Connection string** 복사해서 메모장에 저장
   ```
   postgresql://kurz_owner:abc123@ep-xxx.ap-southeast-1.aws.neon.tech/kurz?sslmode=require
   ```
   ⚠️ 이 주소는 비밀이에요! 공유하면 안됩니다.

## 1-2. Upstash 가입 (캐시)

1. https://upstash.com 접속
2. **"Sign Up"** 클릭
3. GitHub 또는 Google 계정으로 가입
4. **"Create Database"** 클릭
5. 설정:
   - Name: `kurz-redis`
   - Type: **Regional**
   - Region: **Asia Pacific (Tokyo)** 또는 **Singapore**
6. **"Create"** 클릭
7. **"Redis"** 탭에서 **REST URL** 말고 **"Connect to your database"** 섹션의 URL 복사
   ```
   rediss://default:abc123@apn1-xxx.upstash.io:6379
   ```
   ⚠️ `rediss://`로 시작해야 해요 (s가 2개!)

---

# 2단계: Google Cloud 설정 (15분)

## 2-1. Google Cloud 계정 만들기

1. https://console.cloud.google.com 접속
2. Google 계정으로 로그인
3. 처음이면 **무료 크레딧 $300** 받기 (카드 등록 필요하지만 자동 결제 안됨)

## 2-2. 새 프로젝트 만들기

1. 화면 상단의 프로젝트 선택 드롭다운 클릭
2. **"새 프로젝트"** 클릭
3. 설정:
   - 프로젝트 이름: `kurz-studio`
   - 위치: 그대로 두기
4. **"만들기"** 클릭
5. 만들어지면 그 프로젝트 선택

## 2-3. 터미널에서 Google Cloud 설정

맥 터미널을 열고:

```bash
# Google Cloud CLI 설치 (처음 한번만)
brew install --cask google-cloud-sdk
```

설치 후:

```bash
# Google 로그인
gcloud auth login
```
→ 브라우저가 열리면 Google 계정으로 로그인

```bash
# 프로젝트 선택 (아까 만든 프로젝트 ID)
gcloud config set project kurz-studio
```

```bash
# 필요한 기능 켜기
gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com
```

---

# 3단계: 비밀 키 등록 (5분)

API 키들을 안전하게 저장합니다.

## 터미널에서 하나씩 실행:

```bash
# 1. JWT 시크릿 (자동 생성)
echo -n "$(openssl rand -hex 32)" | gcloud secrets create JWT_SECRET --data-file=-
```

```bash
# 2. Gemini API 키
echo -n "여기에_실제_Gemini_API키_입력" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

```bash
# 3. ElevenLabs API 키
echo -n "여기에_실제_ElevenLabs_API키_입력" | gcloud secrets create ELEVENLABS_API_KEY --data-file=-
```

```bash
# 4. Google OAuth Client ID
echo -n "여기에_실제_Client_ID_입력" | gcloud secrets create GOOGLE_CLIENT_ID --data-file=-
```

```bash
# 5. Google OAuth Client Secret
echo -n "여기에_실제_Client_Secret_입력" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-
```

💡 **팁**: 각 명령어에서 `여기에_실제_xxx_입력` 부분을 실제 키로 바꿔주세요!

---

# 4단계: 배포하기 (10분)

## 4-1. 프로젝트 폴더로 이동

```bash
cd ~/Documents/01.AI_Workspace/Kurz_Studio_AI
```

## 4-2. Backend 배포

**한 번에 빌드 + 배포** (소스에서 직접):

```bash
gcloud run deploy kurz-backend \
  --source ./backend \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-secrets="JWT_SECRET=JWT_SECRET:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,ELEVENLABS_API_KEY=ELEVENLABS_API_KEY:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest" \
  --set-env-vars="DATABASE_URL=여기에_Neon_주소,REDIS_URL=여기에_Upstash_주소,CELERY_BROKER_URL=여기에_Upstash_주소,CELERY_RESULT_BACKEND=여기에_Upstash_주소"
```

⚠️ `여기에_Neon_주소`와 `여기에_Upstash_주소`를 1단계에서 저장한 실제 주소로 바꿔주세요!

💡 **중간에 물어보면:**
- "API [run.googleapis.com] not enabled" → `y` 입력
- "Allow unauthenticated invocations" → `y` 입력

배포 완료되면 이런 URL이 나와요:
```
Service URL: https://kurz-backend-xxx-du.a.run.app
```
이 주소 메모해두세요!

## 4-3. Frontend 배포

```bash
gcloud run deploy kurz-frontend \
  --source ./frontend \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
  --set-env-vars="VITE_API_URL=https://kurz-backend-233920104122.asia-northeast3.run.app"

  
```

배포 완료되면:
```
Service URL: https://kurz-frontend-xxx-du.a.run.app
```
🎉 이게 여러분의 사이트 주소예요!

## 4-4. Backend에 Frontend 주소 알려주기

```bash
FRONTEND_URL="https://kurz-frontend-xxx-du.a.run.app"  # 실제 URL로 변경!
BACKEND_URL="https://kurz-backend-xxx-du.a.run.app"    # 실제 URL로 변경!

gcloud run services update kurz-backend \
  --region asia-northeast3 \
  --update-env-vars="FRONTEND_ORIGIN=$FRONTEND_URL,GOOGLE_REDIRECT_URI=$BACKEND_URL/api/auth/google/callback"
```

---

# 5단계: Google 로그인 설정 (5분)

## GCP Console에서 OAuth 설정 업데이트

1. https://console.cloud.google.com/apis/credentials 접속
2. **OAuth 2.0 클라이언트 ID** 클릭 (기존에 만들어둔 것)
3. **승인된 리디렉션 URI**에 추가:
   ```
   https://kurz-backend-233920104122.asia-northeast3.run.app/api/auth/google/callback
   ```
   (xxx 부분은 실제 Backend URL에서 복사)
4. **저장** 클릭

---

# 완료! 🎉

이제 Frontend URL로 접속하면 서비스가 작동합니다!

```
https://kurz-frontend-xxx-du.a.run.app
```

---

## 나중에 코드 수정하면?

코드 고친 후 다시 배포 (똑같은 명령어!):

```bash
# Backend 재배포
gcloud run deploy kurz-backend --source ./backend --region asia-northeast3

# Frontend 재배포
gcloud run deploy kurz-frontend --source ./frontend --region asia-northeast3
```

---

## 문제가 생기면?

### 로그 보기
```bash
# Backend 로그
gcloud run logs tail kurz-backend --region asia-northeast3

# Frontend 로그
gcloud run logs tail kurz-frontend --region asia-northeast3
```

### 서비스 상태 확인
```bash
gcloud run services list --region asia-northeast3
```

### 서비스 삭제 (처음부터 다시 하고 싶을 때)
```bash
gcloud run services delete kurz-backend --region asia-northeast3
gcloud run services delete kurz-frontend --region asia-northeast3
```

---

## 비용은?

| 사용량 | 예상 비용 |
|--------|----------|
| 거의 안씀 (테스트) | **$0** (무료) |
| 가끔 씀 (MVP) | **$1~5/월** |
| 많이 씀 | $10~20/월 |

💡 처음 가입하면 **$300 무료 크레딧**이 있어서 1년은 무료로 쓸 수 있어요!

---

## 용어 정리

| 용어 | 쉬운 설명 |
|------|----------|
| **Cloud Run** | Google이 제공하는 서버. 사용한 만큼만 돈 냄 |
| **Container** | 프로그램을 박스에 담아서 어디서든 똑같이 돌아가게 함 |
| **Docker** | Container를 만드는 도구 |
| **Secret Manager** | 비밀번호를 안전하게 저장하는 금고 |
| **gcloud** | Google Cloud를 터미널에서 조작하는 명령어 |

---

## 다음 단계 (선택)

### 커스텀 도메인 연결하기
`kurz-frontend-xxx.run.app` 대신 `kurz.com` 같은 주소 쓰고 싶으면:

1. 도메인 구매 (Namecheap, Cloudflare 등에서 연 $10~15)
2. ```bash
   gcloud run domain-mappings create \
     --service kurz-frontend \
     --domain kurz.com \
     --region asia-northeast3
   ```
3. 표시되는 DNS 설정을 도메인 업체에서 설정
4. SSL 인증서는 자동으로 발급됨!
