# 실시간 진행도 추적 시스템

## 개요

AutoShorts는 Redis Pub/Sub와 WebSocket을 조합하여 Celery 백그라운드 태스크의 진행도를 프론트엔드에 실시간으로 전달합니다.

---

## 아키텍처

```
Celery Worker                FastAPI Server               Frontend
     │                             │                          │
     │  1. publish_progress()      │                          │
     ├────────────────────────────>│                          │
     │    Redis Pub/Sub             │                          │
     │    (autoshorts:progress)     │                          │
     │                              │                          │
     │                              │  2. redis_listener()     │
     │                              │     receives message     │
     │                              │                          │
     │                              │  3. Update runs[run_id]  │
     │                              │                          │
     │                              │  4. broadcast_to_websockets()
     │                              ├─────────────────────────>│
     │                              │     WebSocket message    │
     │                              │                          │
     │                              │                          │  5. UI update
     │                              │                          │     (progress bar, logs)
```

---

## 구성 요소

### 1. `publish_progress()` (Celery 측)

**위치**: `backend/app/utils/progress.py`

**역할**: Celery 태스크가 진행도를 Redis Pub/Sub로 발행

```python
def publish_progress(
    run_id: str,
    state: str = None,
    progress: float = None,
    log: str = None
):
    """
    진행도 업데이트를 Redis pub/sub로 발행.
    
    Args:
        run_id: Run 식별자
        state: 상태 (PLOT_GENERATION, ASSET_GENERATION 등)
        progress: 0.0~1.0 진행률
        log: 로그 메시지 (프론트엔드 표시용)
    """
    client = get_redis_client()
    
    message = {"run_id": run_id}
    if state:
        message["state"] = state
    if progress is not None:
        message["progress"] = progress
    if log:
        message["log"] = log
    
    client.publish(
        "autoshorts:progress",
        orjson.dumps(message)
    )
```

**사용 예시** (Celery 태스크 내):
```python
from app.utils.progress import publish_progress

@celery.task
def plan_task(run_id, spec):
    publish_progress(run_id, state="PLOT_GENERATION", progress=0.1, log="플롯 생성 시작")
    
    # CSV 생성
    csv_path = generate_csv_from_prompt(...)
    publish_progress(run_id, progress=0.15, log=f"CSV 생성 완료: {csv_path}")
    
    # JSON 변환
    json_path = csv_to_json(...)
    publish_progress(run_id, progress=0.2, log=f"JSON 레이아웃 생성 완료")
```

---

### 2. `redis_listener()` (FastAPI 측)

**위치**: `backend/app/main.py`

**역할**: Redis Pub/Sub 메시지를 수신하여 WebSocket으로 브로드캐스트

```python
async def redis_listener():
    """
    Redis pub/sub 리스너 (백그라운드 태스크).
    Celery 워커가 발행한 진행도 메시지를 수신하여 WebSocket으로 전달.
    """
    global redis_client, pubsub
    
    # Redis 연결
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Pub/Sub 구독
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("autoshorts:progress")
    
    logger.info("Redis Pub/Sub listener started")
    
    # 메시지 수신 루프
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = orjson.loads(message["data"])
            run_id = data.get("run_id")
            
            if run_id:
                # In-memory 상태 업데이트
                if run_id in runs:
                    if "state" in data:
                        runs[run_id]["state"] = data["state"]
                    if "progress" in data:
                        runs[run_id]["progress"] = data["progress"]
                    if "log" in data:
                        runs[run_id]["logs"].append(data["log"])
                
                # WebSocket 브로드캐스트
                await broadcast_to_websockets(run_id, {
                    "type": "progress",
                    "run_id": run_id,
                    "state": data.get("state"),
                    "progress": data.get("progress"),
                    "message": data.get("log", "")
                })
```

**시작 방법**:
```python
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())
```

---

### 3. `broadcast_to_websockets()` (FastAPI 측)

**위치**: `backend/app/main.py`

**역할**: 연결된 모든 WebSocket 클라이언트에 메시지 전송

```python
async def broadcast_to_websockets(run_id: str, message: dict):
    """
    특정 run_id를 구독하는 WebSocket 클라이언트에게 메시지 브로드캐스트.
    
    Args:
        run_id: Run 식별자
        message: 전송할 메시지 (dict)
    """
    if run_id in active_connections:
        websockets = active_connections[run_id]
        disconnected = []
        
        for ws in websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send failed: {e}")
                disconnected.append(ws)
        
        # 끊어진 연결 제거
        for ws in disconnected:
            websockets.remove(ws)
```

---

### 4. WebSocket 엔드포인트

**위치**: `backend/app/main.py`

**경로**: `/ws/{run_id}`

```python
@app.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()
    
    # 연결 등록
    if run_id not in active_connections:
        active_connections[run_id] = []
    active_connections[run_id].append(websocket)
    
    logger.info(f"WebSocket connected for run {run_id}")
    
    # 초기 상태 전송
    if run_id in runs:
        await websocket.send_json({
            "type": "initial_state",
            "state": runs[run_id]["state"],
            "progress": runs[run_id]["progress"],
            "logs": runs[run_id]["logs"]
        })
    
    try:
        # Ping/Pong 처리
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run {run_id}")
        active_connections[run_id].remove(websocket)
```

---

### 5. Frontend WebSocket 클라이언트

**위치**: `frontend/src/components/RunStatus.tsx`

```typescript
useEffect(() => {
  // WebSocket 연결
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/${runId}`
  const websocket = new WebSocket(wsUrl)

  websocket.onopen = () => {
    console.log('WebSocket connected')
  }

  websocket.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'initial_state') {
      setStatus(data)
      setLogs(data.logs || [])
    } else if (data.type === 'progress') {
      // 진행도 업데이트
      if (data.message) {
        setLogs((prev) => [...prev, data.message])
      }
      setStatus((prev) => ({
        ...prev,
        progress: data.progress ?? prev?.progress,
        state: data.state ?? prev?.state,
      }))
    }
  }

  websocket.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  websocket.onclose = () => {
    console.log('WebSocket disconnected')
  }

  return () => {
    websocket.close()
  }
}, [runId])
```

---

## 메시지 타입

### 1. Initial State

WebSocket 연결 시 FastAPI가 전송하는 초기 상태.

```json
{
  "type": "initial_state",
  "state": "ASSET_GENERATION",
  "progress": 0.4,
  "logs": [
    "플롯 생성 시작",
    "CSV 생성 완료",
    "JSON 레이아웃 생성 완료",
    "디자이너: 이미지 생성 시작"
  ]
}
```

### 2. Progress Update

Celery 태스크가 발행하는 진행도 업데이트.

```json
{
  "type": "progress",
  "run_id": "20251105_1430_우주여행고양이",
  "state": "PLOT_GENERATION",
  "progress": 0.15,
  "message": "시나리오 CSV 생성 완료"
}
```

### 3. Ping/Pong

연결 유지용 heartbeat.

**Client → Server:**
```json
{ "type": "ping" }
```

**Server → Client:**
```json
{ "type": "pong" }
```

---

## 진행도 매핑

| 단계 | 상태 | 진행률 | 로그 예시 |
|------|------|--------|----------|
| 플롯 생성 시작 | PLOT_GENERATION | 0.10 | "플롯 생성 시작: 프롬프트 분석 중..." |
| CSV 생성 | PLOT_GENERATION | 0.12 | "시나리오 생성 중 (GPT-4o-mini)..." |
| CSV 완료 | PLOT_GENERATION | 0.15 | "시나리오 CSV 생성 완료" |
| JSON 변환 | PLOT_GENERATION | 0.17 | "JSON 레이아웃 변환 중..." |
| JSON 완료 | PLOT_GENERATION | 0.20 | "JSON 레이아웃 생성 완료" |
| 에셋 생성 시작 | ASSET_GENERATION | 0.25 | "에셋 생성 시작 (디자이너, 작곡가, 성우)" |
| 이미지 생성 | ASSET_GENERATION | 0.30-0.40 | "디자이너: 이미지 생성 중..." |
| 음악 생성 | ASSET_GENERATION | 0.40-0.50 | "작곡가: 배경음악 생성 중..." |
| 음성 생성 | ASSET_GENERATION | 0.50-0.65 | "성우: 음성 합성 중..." |
| 렌더링 시작 | RENDERING | 0.75 | "렌더링 단계 시작" |
| 렌더링 완료 | RENDERING | 0.80 | "렌더링 완료: {output_path}" |
| QA 시작 | QA | 0.85 | "QA: 품질 검수 시작..." |
| QA 검사 | QA | 0.87-0.95 | "QA: 영상 파일 확인 완료" |
| 완료 | END | 1.00 | "영상 생성 완료! 🎉" |

---

## Redis 채널 구조

### Channel: `autoshorts:progress`

**발행자**: Celery Workers
**구독자**: FastAPI Server (`redis_listener`)

**메시지 포맷**:
```json
{
  "run_id": "20251105_1430_우주여행고양이",
  "state": "PLOT_GENERATION",
  "progress": 0.15,
  "log": "시나리오 CSV 생성 완료"
}
```

---

## 폴링 폴백 (Fallback)

WebSocket이 실패할 경우를 대비한 HTTP 폴링.

**위치**: `frontend/src/components/RunStatus.tsx`

```typescript
// Polling fallback
const interval = setInterval(() => {
  getRun(runId).then((data) => {
    setStatus(data)
    if (data.state === 'END') {
      clearInterval(interval)
      onCompleted(data)
    } else if (data.state === 'FAILED') {
      clearInterval(interval)
    }
  })
}, 2000)  // 2초마다 폴링
```

**동작**:
- WebSocket과 병행하여 2초마다 `/api/runs/{run_id}` 폴링
- WebSocket이 끊어져도 진행도 업데이트 지속
- `END` 또는 `FAILED` 상태 시 폴링 중단

---

## 디버깅

### Celery 측 로그 확인

```bash
celery -A app.celery_app worker --loglevel=info
```

### FastAPI 측 로그 확인

```bash
uvicorn app.main:app --reload --log-level=info
```

### Redis Pub/Sub 모니터링

```bash
redis-cli
> SUBSCRIBE autoshorts:progress
```

### WebSocket 디버깅 (브라우저)

```javascript
// 개발자 콘솔
const ws = new WebSocket('ws://localhost:8000/ws/20251105_1430_우주여행고양이')
ws.onmessage = (e) => console.log(JSON.parse(e.data))
```

---

## 성능 고려사항

### 1. Redis Pub/Sub 오버헤드

- 메시지는 작게 유지 (< 1KB)
- 너무 빈번한 publish 지양 (진행도 1% 단위 정도)

### 2. WebSocket 연결 관리

- 연결 수 제한 (동시 최대 100개 정도)
- 끊어진 연결 자동 정리

### 3. 메모리 누수 방지

- `runs` 딕셔너리는 END/FAILED 후 일정 시간 뒤 삭제
- `active_connections`에서 끊어진 WebSocket 즉시 제거

---

**작성일**: 2025-11-05  
**버전**: 1.0
