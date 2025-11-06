# AutoShorts 시스템 아키텍처

## 전체 구조

```
┌──────────────┐
│   Frontend   │ (React + TypeScript)
│  (Port 3000) │
└──────┬───────┘
       │ HTTP/WebSocket
       ↓
┌──────────────────┐
│   FastAPI Server │ (Port 8000)
│   (app/main.py)  │
└──────┬───────────┘
       │
       ├── Redis Pub/Sub ←─┐ 진행도 업데이트
       │                   │
       ├── Celery Broker   │
       │   (Redis)         │
       │                   │
       ↓                   │
┌────────────────────┐     │
│  Celery Workers    │─────┘
│  (Background Tasks)│
└────────────────────┘
       │
       ├── ComfyUI (이미지 생성)
       ├── Mubert API (음악 생성)
       ├── ElevenLabs/PlayHT (음성 생성)
       └── MoviePy (영상 합성)
```

---

## 컴포넌트 설명

### 1. Frontend (React + TypeScript)

**위치**: `frontend/src/`

**주요 컴포넌트**:
- `App.tsx`: 메인 앱
- `RunForm.tsx`: 프롬프트 입력 폼
- `RunStatus.tsx`: 실시간 진행도 표시

**통신**:
- REST API: `/api/runs` (POST), `/api/runs/{run_id}` (GET)
- WebSocket: `/ws/{run_id}` (실시간 업데이트)

**상태 관리**:
- useState로 run 상태 관리
- WebSocket으로 실시간 진행도 수신

---

### 2. FastAPI Server

**위치**: `backend/app/main.py`

**역할**:
1. REST API 엔드포인트 제공
2. WebSocket 연결 관리
3. FSM 레지스트리 관리
4. Redis Pub/Sub 리스너 (백그라운드 태스크)

**주요 엔드포인트**:
- `POST /api/runs`: 새 Run 생성
- `GET /api/runs/{run_id}`: Run 상태 조회
- `WS /ws/{run_id}`: 실시간 업데이트

**전역 상태**:
```python
runs: Dict[str, RunData] = {}
```

**Redis Pub/Sub 리스너**:
```python
async def redis_listener():
    """Celery 태스크가 publish한 진행도를 수신하여 WebSocket으로 브로드캐스트"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("autoshorts:progress")
    
    async for message in pubsub.listen():
        data = orjson.loads(message["data"])
        run_id = data["run_id"]
        
        # In-memory 상태 업데이트
        if run_id in runs:
            runs[run_id]["state"] = data.get("state")
            runs[run_id]["progress"] = data.get("progress")
            runs[run_id]["logs"].append(data.get("log"))
        
        # WebSocket 브로드캐스트
        await broadcast_to_websockets(run_id, data)
```

---

### 3. Celery Workers

**위치**: `backend/app/tasks/`

**태스크 목록**:
1. `plan_task` - 플롯 생성 (CSV → JSON)
2. `designer_task` - 이미지 생성
3. `composer_task` - 음악 생성
4. `voice_task` - 음성 생성
5. `director_task` - 영상 합성
6. `qa_task` - 품질 검수
7. `recover_task` - 복구 (미사용)

**병렬 실행**:
```python
chord(
    group(
        designer_task.s(...),
        composer_task.s(...),
        voice_task.s(...)
    )
)(director_task.s(...))
```

**진행도 업데이트**:
```python
from app.utils.progress import publish_progress

publish_progress(
    run_id=run_id,
    state="PLOT_GENERATION",
    progress=0.15,
    log="시나리오 CSV 생성 완료"
)
```

---

### 4. FSM (Finite State Machine)

**위치**: `backend/app/orchestrator/fsm.py`

**역할**: 워크플로 상태 관리 및 전이 제어

**상태**:
```python
class RunState(Enum):
    INIT = "INIT"
    PLOT_GENERATION = "PLOT_GENERATION"
    ASSET_GENERATION = "ASSET_GENERATION"
    RENDERING = "RENDERING"
    QA = "QA"
    END = "END"
    FAILED = "FAILED"
```

**전이 규칙**:
```python
TRANSITIONS = {
    RunState.INIT: [RunState.PLOT_GENERATION, RunState.FAILED],
    RunState.PLOT_GENERATION: [RunState.ASSET_GENERATION, RunState.FAILED],
    RunState.ASSET_GENERATION: [RunState.RENDERING, RunState.FAILED],
    RunState.RENDERING: [RunState.QA, RunState.FAILED],
    RunState.QA: [RunState.END, RunState.PLOT_GENERATION, RunState.FAILED],
    RunState.END: [],
    RunState.FAILED: [],
}
```

**크로스 프로세스 공유**:
- In-memory 레지스트리 (`_fsm_registry`)
- Redis 저장 (pickle 직렬화, 24시간 TTL)
- FastAPI와 Celery 간 공유

---

### 5. Redis

**용도**:
1. **Celery Broker**: 태스크 큐
2. **Celery Result Backend**: 태스크 결과 저장
3. **Pub/Sub**: 진행도 업데이트 채널
4. **FSM 저장소**: 크로스 프로세스 FSM 공유

**채널**:
- `autoshorts:progress`: 진행도 업데이트

**키**:
- `fsm:{run_id}`: FSM 직렬화 데이터 (TTL: 24h)

---

### 6. 외부 서비스

#### ComfyUI (이미지 생성)
- **위치**: `app/providers/images/comfyui_client.py`
- **통신**: HTTP POST `/api/generate`
- **워크플로**: `comfy_workflows/flux_omni_lora.json`
- **출력**: PNG 이미지 파일

#### Mubert API (음악 생성)
- **위치**: `app/providers/music/mubert_client.py`
- **통신**: REST API
- **입력**: `genre`, `mood`, `duration`
- **출력**: MP3 파일

#### ElevenLabs / PlayHT (TTS)
- **위치**: `app/providers/tts/`
- **통신**: REST API
- **입력**: `text`, `voice_id`, `emotion`
- **출력**: MP3 파일

---

## 데이터 흐름

### Run 생성 플로우

```
1. User → Frontend: 프롬프트 입력
   ↓
2. Frontend → FastAPI: POST /api/runs
   ↓
3. FastAPI:
   - run_id 생성 (YYYYMMDD_HHMM_프롬프트첫8글자)
   - FSM 생성 및 등록 (INIT 상태)
   - runs 딕셔너리에 추가
   ↓
4. FastAPI → Celery: plan_task 비동기 실행
   ↓
5. Celery Worker (plan_task):
   - FSM 전이: INIT → PLOT_GENERATION
   - CSV 생성 (GPT-4o-mini)
   - JSON 변환
   - publish_progress("플롯 생성 완료", progress=0.2)
   - FSM 전이: PLOT_GENERATION → ASSET_GENERATION
   - chord 생성 (designer + composer + voice → director)
   ↓
6. Celery Workers (병렬):
   - designer_task: 이미지 생성, publish_progress(progress=0.4)
   - composer_task: 음악 생성, publish_progress(progress=0.5)
   - voice_task: 음성 생성, publish_progress(progress=0.6)
   ↓
7. Celery Worker (director_task):
   - FSM 전이: ASSET_GENERATION → RENDERING
   - MoviePy 영상 합성
   - publish_progress("렌더링 완료", progress=0.8)
   - FSM 전이: RENDERING → QA
   - qa_task 트리거
   ↓
8. Celery Worker (qa_task):
   - 품질 검수 (파일 존재, JSON 유효성)
   - Pass: FSM 전이 QA → END
   - Fail: FSM 전이 QA → PLOT_GENERATION (재시도)
   - publish_progress("영상 생성 완료", progress=1.0)
   ↓
9. Redis Pub/Sub:
   - Celery workers가 publish한 메시지를 FastAPI가 수신
   ↓
10. FastAPI redis_listener:
   - runs[run_id] 업데이트
   - WebSocket 브로드캐스트
   ↓
11. Frontend WebSocket:
   - 진행도 수신
   - UI 업데이트 (progress bar, logs)
```

---

## 폴더 구조

```
backend/
├── app/
│   ├── main.py               # FastAPI 앱
│   ├── celery_app.py         # Celery 인스턴스
│   ├── config.py             # 환경 변수 설정
│   ├── schemas/
│   │   ├── run.py            # RunSpec Pydantic 모델
│   │   └── json_layout.py    # JSON 스키마 모델
│   ├── orchestrator/
│   │   └── fsm.py            # FSM 구현
│   ├── tasks/
│   │   ├── plan.py           # 플롯 생성
│   │   ├── designer.py       # 이미지 생성
│   │   ├── composer.py       # 음악 생성
│   │   ├── voice.py          # 음성 생성
│   │   ├── director.py       # 영상 합성
│   │   ├── qa.py             # 품질 검수
│   │   └── recover.py        # 복구 (미사용)
│   ├── providers/
│   │   ├── images/
│   │   │   ├── comfyui_client.py
│   │   │   └── stub_client.py
│   │   ├── music/
│   │   │   ├── mubert_client.py
│   │   │   └── stub_client.py
│   │   └── tts/
│   │       ├── elevenlabs_client.py
│   │       ├── playht_client.py
│   │       └── stub_client.py
│   └── utils/
│       ├── csv_to_json.py    # CSV → JSON 변환
│       ├── progress.py       # Redis Pub/Sub 발행
│       ├── seeds.py          # Seed 생성
│       └── sfx_tags.py       # SFX 태그 추출

frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── RunForm.tsx
│   │   └── RunStatus.tsx
│   └── api/
│       └── client.ts

docs/
├── ARCHITECTURE.md          # 이 문서
├── WORKFLOW.md              # FSM 워크플로 설명
├── DATA_SCHEMA.md           # CSV/JSON 스키마
├── CSV_SCHEMA.md            # 상세 CSV 설계
├── API.md                   # REST/WebSocket API 명세
└── PROGRESS_TRACKING.md     # 진행도 추적 시스템
```

---

## 확장 포인트

### 새로운 Agent 추가

1. `app/tasks/` 에 새 태스크 파일 생성
2. `@celery.task` 데코레이터로 등록
3. `celery_app.py`의 `include` 리스트에 추가
4. `plan_task`에서 chord/group에 포함

### 새로운 FSM 상태 추가

1. `fsm.py`의 `RunState` enum에 추가
2. `TRANSITIONS` 딕셔너리 업데이트
3. 관련 태스크에서 `fsm.transition_to()` 호출

### 새로운 Provider 추가

1. `app/providers/{category}/` 에 client 파일 생성
2. `generate()` 메서드 구현
3. Stub client 생성 (API 키 없을 때 대비)
4. 관련 태스크에서 import 및 사용

---

**작성일**: 2025-11-05  
**버전**: 1.0
