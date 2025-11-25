# DEPRECATED - Google Cloud Run 배포 가이드

> **이 문서는 더 이상 사용되지 않습니다.**
>
> Railway 배포로 전환되었습니다.
>
> 새 배포 가이드: [../deploy/railway/README.md](../deploy/railway/README.md)

---

# (참고용) Kurz AI Studio - Google Cloud Run 배포 가이드

MVP를 위한 간단한 서버리스 배포 가이드입니다.

---

## 아키텍처

```
                    ┌─────────────────┐
                    │   Cloud Run     │
                    │   (Frontend)    │
                    │   React+Nginx   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Cloud Run     │  │    Cloud SQL    │  │    Upstash      │
│   (Backend)     │  │   PostgreSQL    │  │     Redis       │
│   FastAPI       │  │                 │  │   (Serverless)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 사전 준비

### 1. Google Cloud SDK 설치
```bash
# macOS
brew install --cask google-cloud-sdk

# 또는 직접 다운로드
# https://cloud.google.com/sdk/docs/install
```

### 2. 로그인 및 프로젝트 설정
```bash
# 로그인
gcloud auth login

# 프로젝트 생성 (또는 기존 프로젝트 사용)
gcloud projects create kurz-studio --name="Kurz Studio"

# 프로젝트 선택
gcloud config set project kurz-studio

# 결제 계정 연결 (GCP Console에서)
# https://console.cloud.google.com/billing
```

---

## 1단계: 외부 서비스 설정 (5분)

### Upstash Redis (무료)
1. [upstash.com](https://upstash.com) 가입
2. Redis 데이터베이스 생성 (Region: Tokyo 또는 Singapore)
3. Connection URL 복사: `rediss://default:xxx@xxx.upstash.io:6379`

### Neon PostgreSQL (무료)
1. [neon.tech](https://neon.tech) 가입
2. 새 프로젝트 생성 (Region: Singapore)
3. Connection string 복사: `postgresql://user:pass@xxx.neon.tech/dbname?sslmode=require`

> **참고**: Cloud SQL도 사용 가능하지만 월 $10+ 비용 발생

---

## 2단계: Secret Manager 설정 (3분)

```bash
# Secret Manager API 활성화
gcloud services enable secretmanager.googleapis.com

# 시크릿 생성
echo -n "$(openssl rand -hex 32)" | gcloud secrets create JWT_SECRET --data-file=-

echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-

echo -n "your-elevenlabs-api-key" | gcloud secrets create ELEVENLABS_API_KEY --data-file=-

echo -n "your-google-client-id" | gcloud secrets create GOOGLE_CLIENT_ID --data-file=-

echo -n "your-google-client-secret" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-
```

또는 스크립트 사용:
```bash
chmod +x deploy/cloudrun/setup-secrets.sh
./deploy/cloudrun/setup-secrets.sh
```

---

## 3단계: 배포 (5분)

### 자동 배포 (권장)
```bash
# API 활성화
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# 배포 실행
chmod +x deploy/cloudrun/deploy.sh
./deploy/cloudrun/deploy.sh
```

### 수동 배포

**Backend 배포:**
```bash
# 이미지 빌드 & 푸시
gcloud builds submit \
  --tag gcr.io/$(gcloud config get-value project)/kurz-backend \
  -f deploy/cloudrun/backend.dockerfile .

# Cloud Run 배포
gcloud run deploy kurz-backend \
  --image gcr.io/$(gcloud config get-value project)/kurz-backend \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-secrets="JWT_SECRET=JWT_SECRET:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,ELEVENLABS_API_KEY=ELEVENLABS_API_KEY:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest" \
  --set-env-vars="DATABASE_URL=postgresql+asyncpg://...,REDIS_URL=rediss://..."
```

**Frontend 배포:**
```bash
# Backend URL 확인
BACKEND_URL=$(gcloud run services describe kurz-backend --region asia-northeast3 --format='value(status.url)')

# 이미지 빌드 & 푸시
gcloud builds submit \
  --tag gcr.io/$(gcloud config get-value project)/kurz-frontend \
  -f deploy/cloudrun/frontend.dockerfile \
  --build-arg VITE_API_URL=$BACKEND_URL .

# Cloud Run 배포
gcloud run deploy kurz-frontend \
  --image gcr.io/$(gcloud config get-value project)/kurz-frontend \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1
```

---

## 4단계: OAuth 설정 업데이트

배포 후 URL을 확인하고 GCP Console에서 OAuth 설정 업데이트:

```bash
# URL 확인
gcloud run services describe kurz-backend --region asia-northeast3 --format='value(status.url)'
gcloud run services describe kurz-frontend --region asia-northeast3 --format='value(status.url)'
```

[GCP Console](https://console.cloud.google.com/apis/credentials)에서:
1. OAuth 2.0 Client ID 선택
2. Authorized redirect URIs에 추가:
   - `https://kurz-backend-xxx.run.app/api/auth/google/callback`

---

## 5단계: 환경 변수 업데이트

```bash
# Backend에 Frontend URL 설정
FRONTEND_URL=$(gcloud run services describe kurz-frontend --region asia-northeast3 --format='value(status.url)')
BACKEND_URL=$(gcloud run services describe kurz-backend --region asia-northeast3 --format='value(status.url)')

gcloud run services update kurz-backend \
  --region asia-northeast3 \
  --set-env-vars="FRONTEND_ORIGIN=$FRONTEND_URL,GOOGLE_REDIRECT_URI=$BACKEND_URL/api/auth/google/callback"
```

---

## 커스텀 도메인 (선택)

```bash
# 도메인 매핑
gcloud run domain-mappings create \
  --service kurz-frontend \
  --domain yourdomain.com \
  --region asia-northeast3

# DNS 설정 확인
gcloud run domain-mappings describe \
  --domain yourdomain.com \
  --region asia-northeast3
```

DNS에서 표시된 CNAME/A 레코드 추가 후 자동으로 SSL 발급됨.

---

## 비용 예상

| 서비스 | 무료 티어 | 초과 시 |
|--------|----------|---------|
| Cloud Run | 200만 요청/월 | $0.00002/요청 |
| Upstash Redis | 10,000 명령/일 | $0.2/100K 명령 |
| Neon PostgreSQL | 0.5GB | $19/월 (Pro) |
| Cloud Build | 120분/일 | $0.003/분 |

**MVP 예상 비용: $0~5/월** (저사용량 기준)

---

## 업데이트 배포

코드 수정 후:
```bash
# 간단 배포
./deploy/cloudrun/deploy.sh

# 또는 수동
gcloud builds submit --config=deploy/cloudrun/cloudbuild.yaml
```

---

## 트러블슈팅

### Cold Start 느림
```bash
# 최소 인스턴스 1개 유지 (비용 발생)
gcloud run services update kurz-backend \
  --min-instances 1 \
  --region asia-northeast3
```

### 로그 확인
```bash
# 실시간 로그
gcloud run logs tail kurz-backend --region asia-northeast3

# 로그 검색
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=kurz-backend" --limit 50
```

### 서비스 삭제
```bash
gcloud run services delete kurz-backend --region asia-northeast3
gcloud run services delete kurz-frontend --region asia-northeast3
```

---

## Celery Worker 대안

Cloud Run은 긴 백그라운드 작업에 제한이 있어, 영상 렌더링을 위한 대안:

### 옵션 1: Cloud Run Jobs (권장)
```bash
# 별도 Job으로 배포
gcloud run jobs create kurz-worker \
  --image gcr.io/PROJECT_ID/kurz-backend \
  --command "celery" \
  --args "-A,app.celery_app,worker,--pool=solo" \
  --region asia-northeast3 \
  --task-timeout 60m
```

### 옵션 2: 동기 처리
짧은 영상만 지원하도록 Backend에서 직접 처리 (timeout 5분 내)

### 옵션 3: Compute Engine
장기 작업용으로 별도 VM 운영 (월 $5~10)

---

## 참고 자료

- [Cloud Run 문서](https://cloud.google.com/run/docs)
- [Upstash 문서](https://docs.upstash.com/)
- [Neon 문서](https://neon.tech/docs)
