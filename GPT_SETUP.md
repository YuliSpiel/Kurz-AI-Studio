# GPT-4o-mini 연동 가이드

## 📋 개요

AutoShorts는 이제 **GPT-4o-mini**를 사용하여 자동으로 시나리오 CSV를 생성합니다!

### 변경 사항

- ✅ GPT-4o-mini로 스토리 생성
- ✅ 날짜시간 네이밍 (예: `20251104_113045_41badd30.csv`)
- ✅ `backend/app/data/outputs/csv_files/` 폴더에 저장
- ✅ 폴백: API 키 없으면 룰 기반 생성

---

## 🔑 1단계: OpenAI API 키 발급

### 1.1 OpenAI 계정 생성
https://platform.openai.com/signup

### 1.2 API 키 발급
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 이름 입력 (예: `AutoShorts`)
4. 키 복사 (형식: `sk-proj-...`)

### 1.3 요금 충전
- https://platform.openai.com/account/billing
- 최소 $5 충전 권장
- GPT-4o-mini는 매우 저렴:
  - 입력: $0.15 / 1M tokens
  - 출력: $0.60 / 1M tokens
  - **1회 생성당 약 $0.001 (0.1원 수준)**

---

## ⚙️ 2단계: 환경 변수 설정

### 2.1 `.env` 파일 편집

프로젝트 루트에서:

```bash
cd /Users/yuli/Documents/01.AI_Workspace/Kurz_Studio_AI
nano .env
# 또는
code .env
```

### 2.2 API 키 추가

```bash
# OpenAI (추가)
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# 기존 설정들...
COMFY_URL=http://localhost:8188
TTS_PROVIDER=elevenlabs
MUSIC_PROVIDER=mubert
```

### 2.3 저장 후 확인

```bash
cat .env | grep OPENAI
# OPENAI_API_KEY=sk-proj-... 출력되면 성공
```

---

## 🔄 3단계: 백엔드 재시작

### 3.1 패키지 업데이트

```bash
cd backend
source kvenv/bin/activate  # 또는 .venv/bin/activate
pip install openai
```

### 3.2 FastAPI 재시작

FastAPI가 실행 중인 터미널에서:
1. `Ctrl + C` (종료)
2. 재실행:
```bash
uvicorn app.main:app --reload
```

### 3.3 Celery 재시작

Celery Worker 터미널에서:
1. `Ctrl + C` (종료)
2. 재실행:
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

---

## 🎬 4단계: 테스트

### 4.1 프론트엔드에서 생성

1. http://localhost:5173 접속
2. 입력:
   - **프롬프트**: "우주를 여행하는 호기심 많은 고양이의 모험"
   - **모드**: 스토리텔링
   - **컷 수**: 3
3. "숏츠 생성 시작" 클릭

### 4.2 로그 확인

**Celery 터미널**에서 다음 로그를 확인:
```
[2025-11-04 11:30:45] Calling GPT-4o-mini for plot generation...
[2025-11-04 11:30:48] ✅ CSV generated with GPT-4o-mini: app/data/outputs/csv_files/20251104_113045_41badd30.csv
[2025-11-04 11:30:48] Generated 3 scenes
```

### 4.3 CSV 파일 확인

```bash
# 최신 CSV 보기
ls -lt backend/app/data/outputs/csv_files/ | head -n 5

# CSV 내용 확인
cat backend/app/data/outputs/csv_files/20251104_113045_41badd30.csv
```

**예상 출력:**
```csv
scene_id,sequence,char_id,char_name,text,emotion,subtitle_text,subtitle_position,duration_ms
scene_1,1,char_1,나비,"우주선 문이 열렸어! 이제 시작이야!",excited,우주로의 첫 발,bottom,5000
scene_2,2,char_1,나비,"와, 저 별들 좀 봐! 정말 아름다워...",happy,별빛 속으로,top,5000
scene_3,3,char_1,나비,"이제 새로운 행성을 찾아 떠나볼까?",neutral,모험의 시작,bottom,5000
```

---

## 🐛 문제 해결

### 문제 1: API 키 오류

**증상:**
```
OpenAI API key not set, using rule-based generation
```

**해결:**
1. `.env` 파일에 `OPENAI_API_KEY` 확인
2. 키 앞뒤 공백 제거
3. FastAPI 재시작

### 문제 2: API 요금 부족

**증상:**
```
GPT-4o-mini failed: insufficient_quota
```

**해결:**
1. https://platform.openai.com/account/billing
2. 크레딧 충전 ($5 이상)

### 문제 3: Rate Limit 초과

**증상:**
```
GPT-4o-mini failed: rate_limit_exceeded
```

**해결:**
1. 잠시 대기 (1분)
2. 또는 더 높은 Tier로 업그레이드

### 문제 4: 폴백 동작

API가 실패해도 **자동으로 룰 기반 생성**으로 폴백됩니다:
```
GPT-4o-mini failed: ..., falling back to rule-based generation
CSV generated (rule-based fallback): ...
```

---

## 📊 비용 추정

| 항목 | 비용 |
|-----|------|
| 1회 생성 (3컷) | ~$0.001 (0.1원) |
| 100회 생성 | ~$0.10 (100원) |
| 1000회 생성 | ~$1.00 (1,300원) |

**매우 저렴**하므로 부담 없이 사용 가능! 🎉

---

## 🎨 프롬프트 작성 팁

### 좋은 예시

```
✅ "우주를 탐험하는 호기심 많은 고양이가 새로운 행성에서 친구를 만나는 이야기"
✅ "바쁜 직장인이 아침에 간편하게 만드는 건강한 스무디 레시피 소개"
✅ "작은 로봇이 처음으로 인간의 감정을 배우며 성장하는 감동적인 순간"
```

### 나쁜 예시

```
❌ "고양이"  (너무 짧음)
❌ "뭔가 재밌는 거"  (모호함)
❌ "이거 저거 다 넣어줘"  (구체성 부족)
```

### 팁
- **구체적으로**: 주제, 분위기, 스타일 명시
- **감정 표현**: 감동적, 재미있는, 신비로운 등
- **대상 명확히**: 누가 무엇을 하는지

---

## 📁 CSV 파일 관리

### 파일 위치
```
backend/app/data/outputs/csv_files/
├── 20251104_113045_41badd30.csv
├── 20251104_114523_a7f2c9d1.csv
└── 20251104_115612_f8e3d4a2.csv
```

### 백업
```bash
# 중요한 CSV 백업
cp backend/app/data/outputs/csv_files/20251104_113045_41badd30.csv ~/backup/

# 전체 폴더 백업
cp -r backend/app/data/outputs/csv_files ~/backup/csv_archive_$(date +%Y%m%d)
```

### 정리
```bash
# 7일 이상 된 파일 삭제
find backend/app/data/outputs/csv_files -name "*.csv" -mtime +7 -delete
```

---

## 🚀 다음 단계

1. ✅ CSV 생성 완료
2. 🔲 이미지 생성 (ComfyUI)
3. 🔲 TTS 생성 (ElevenLabs)
4. 🔲 음악 생성 (Mubert)
5. 🔲 영상 합성 (MoviePy)

각 단계별로 Provider를 추가 설정해야 합니다!

---

문제가 있으면 로그를 확인하거나 질문하세요! 😊
