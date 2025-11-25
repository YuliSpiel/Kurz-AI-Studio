# Railway 배포 가이드

## 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Railway Project                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [Frontend]        [Backend]         [Worker]            │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐          │
│  │ React   │ ──── │ FastAPI │ ──── │ Celery  │          │
│  │ Nginx   │      │         │      │ FFmpeg  │          │
│  └─────────┘      └─────────┘      └─────────┘          │
│       │                │                │                │
│       │                ▼                ▼                │
│       │          ┌─────────┐      ┌─────────┐           │
│       │          │ Redis   │      │ Volume  │           │
│       │          │ (Queue) │      │ (Files) │           │
│       │          └─────────┘      └─────────┘           │
│       │                │                                 │
│       │                ▼                                 │
│       └────────► │ Postgres│ (선택사항)                  │
│                  └─────────┘                            │
└──────────────────────────────────────────────────────────┘
```

## 사전 준비

1. [Railway 계정](https://railway.app) 가입
2. GitHub 연동
3. API 키 준비:
   - GEMINI_API_KEY
   - ELEVENLABS_API_KEY
   - MINIMAX_API_KEY + MINIMAX_GROUP_ID

---

## Step 1: Railway 프로젝트 생성

1. Railway Dashboard에서 **New Project** 클릭
2. **Empty Project** 선택
3. 프로젝트 이름: `kurz-studio`

---

## Step 2: Redis 추가

1. **+ New** → **Database** → **Redis**
2. 자동으로 `REDIS_URL` 환경변수 생성됨

---

## Step 3: Backend 서비스 배포

### 3.1 서비스 생성

1. **+ New** → **GitHub Repo** → 저장소 선택
2. 서비스 이름: `backend`

### 3.2 설정

**Settings 탭:**
```
Root Directory: backend
Watch Paths: /backend/**
```

**Variables 탭에서 환경변수 추가:**
```bash
# Redis 연결 (Railway 변수 참조)
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}

# 필수 API 키
GEMINI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
MINIMAX_API_KEY=your_key_here
MINIMAX_GROUP_ID=your_group_id

# 공통 설정
ENV=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8080

# JWT (보안을 위해 랜덤 문자열 생성!)
JWT_SECRET_KEY=generate-secure-random-string

# Provider 설정
IMAGE_PROVIDER=gemini
TTS_PROVIDER=minimax
MUSIC_PROVIDER=elevenlabs
```

### 3.3 도메인 설정

1. **Settings** → **Networking** → **Generate Domain**
2. 생성된 URL 복사 (예: `kurz-backend-xxx.up.railway.app`)

---

## Step 4: Worker 서비스 배포

### 4.1 서비스 생성

1. **+ New** → **GitHub Repo** → 같은 저장소 선택
2. 서비스 이름: `worker`

### 4.2 설정

**Settings 탭:**
```
Root Directory: backend
Watch Paths: /backend/**
Builder: Dockerfile
Dockerfile Path: Dockerfile.worker
```

**Variables 탭 (Backend와 동일하게):**
```bash
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
GEMINI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
MINIMAX_API_KEY=your_key_here
MINIMAX_GROUP_ID=your_group_id
ENV=production
IMAGE_PROVIDER=gemini
TTS_PROVIDER=minimax
MUSIC_PROVIDER=elevenlabs
```

### 4.3 Volume 연결 (파일 저장용)

1. **+ New** → **Volume**
2. 마운트 경로: `/app/app/data/outputs`
3. Worker 서비스에 연결

---

## Step 5: Frontend 배포

### 5.1 서비스 생성

1. **+ New** → **GitHub Repo** → 같은 저장소 선택
2. 서비스 이름: `frontend`

### 5.2 설정

**Settings 탭:**
```
Root Directory: frontend
Watch Paths: /frontend/**
```

**Variables 탭:**
```bash
# Backend URL (Step 3에서 생성한 도메인)
VITE_API_URL=https://kurz-backend-xxx.up.railway.app
```

### 5.3 도메인 설정

1. **Settings** → **Networking** → **Generate Domain**
2. 이 URL이 사용자 접속 URL

---

## Step 6: Backend CORS 업데이트

Backend 서비스의 Variables에서 추가:
```bash
FRONTEND_ORIGIN=https://kurz-frontend-xxx.up.railway.app
```

---

## 배포 확인

### Health Check
```bash
curl https://kurz-backend-xxx.up.railway.app/health
```

### 로그 확인
Railway Dashboard에서 각 서비스의 **Deployments** → 로그 확인

---

## 트러블슈팅

### 빌드 실패 시
```bash
# 로컬에서 Docker 빌드 테스트
cd backend
docker build -t kurz-backend .
```

### Worker 연결 안 될 때
1. Redis 서비스 실행 중인지 확인
2. REDIS_URL 변수가 올바른지 확인
3. Worker 로그에서 "Connected to Redis" 메시지 확인

### 영상 생성 안 될 때
1. Worker 로그 확인
2. Volume이 제대로 마운트됐는지 확인
3. API 키들이 유효한지 확인

---

## 비용 예상

| 서비스 | 예상 비용 |
|--------|----------|
| Frontend | ~$0 (사용량 적음) |
| Backend | ~$5/월 |
| Worker | ~$10-20/월 (영상 렌더링 시 CPU 사용) |
| Redis | ~$5/월 |
| Volume | ~$1/월 (1GB 기준) |
| **총합** | **~$20-30/월** |

> Railway는 사용량 기반 과금. 사용 안 하면 비용 적음.

---

## 유용한 Railway CLI 명령어

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 로그 확인
railway logs

# 환경변수 확인
railway variables

# 배포
railway up
```

---

## 로컬 개발 시 Railway 환경 사용

```bash
# Railway 환경변수로 로컬 실행
railway run python -m uvicorn app.main:app --reload
```

---

## 설정 파일 위치

이 디렉토리의 파일들:
- `backend.toml` - Backend 서비스 Railway 설정
- `worker.toml` - Worker 서비스 Railway 설정
- `frontend.toml` - Frontend 서비스 Railway 설정
- `env.template` - 환경변수 템플릿
