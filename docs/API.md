# AutoShorts API 명세

## REST API

### Base URL

```
http://localhost:8080/api
```

### Endpoints

#### 1. Health Check

**GET** `/`

서버 상태 확인.

**Response:**

```json
{
  "service": "AutoShorts API",
  "version": "0.1.0",
  "status": "running",
  "environment": "dev"
}
```

---

#### 2. Create Run

**POST** `/api/runs`

새로운 숏츠 생성 작업을 시작합니다.

**Request Body:**

```json
{
  "mode": "story",
  "prompt": "우주를 여행하는 고양이 이야기",
  "num_characters": 1,
  "num_cuts": 3,
  "art_style": "파스텔 수채화",
  "music_genre": "ambient",
  "reference_images": ["ref_abc123.png"],
  "lora_strength": 0.8,
  "voice_id": "default"
}
```

**Request Schema:**

- `mode` (string, required): "story" 또는 "ad"
- `prompt` (string, required): 생성할 콘텐츠의 줄글 설명
- `num_characters` (int, required): 1 또는 2
- `num_cuts` (int, required): 1~10 (씬 수)
- `art_style` (string, optional): 화풍 설명 (기본: "파스텔 수채화")
- `music_genre` (string, optional): 음악 장르 (기본: "ambient")
- `reference_images` (array[string], optional): 업로드된 참조 이미지 파일명 배열
- `lora_strength` (float, optional): 0.0~1.0 (기본: 0.8)
- `voice_id` (string, optional): TTS 음성 ID

**Response:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "PLOT_PLANNING",
  "progress": 0.0,
  "artifacts": {},
  "logs": ["Run created, starting plot planning..."]
}
```

**Status Codes:**

- `200 OK`: Run 생성 성공
- `422 Unprocessable Entity`: 입력 검증 실패

---

#### 3. Get Run Status

**GET** `/api/runs/{run_id}`

Run의 현재 상태와 진행률을 조회합니다.

**Path Parameters:**

- `run_id` (string): Run 식별자

**Response:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "RENDERING",
  "progress": 0.7,
  "artifacts": {
    "csv_path": "app/data/outputs/550e8400_plot.csv",
    "json_path": "app/data/outputs/550e8400_layout.json",
    "images": [
      {
        "scene_id": "scene_1",
        "slot_id": "center",
        "image_url": "app/data/outputs/550e8400_scene_1_center_1234567890.png"
      }
    ],
    "audio": [
      {
        "type": "bgm",
        "id": "global_bgm",
        "path": "app/data/outputs/550e8400_global_bgm.mp3"
      }
    ],
    "voice": [
      {
        "scene_id": "scene_1",
        "line_id": "scene_1_line_1",
        "audio_url": "app/data/outputs/550e8400_scene_1_scene_1_line_1.mp3"
      }
    ]
  },
  "logs": [
    "Run created, starting plot planning...",
    "CSV generated: app/data/outputs/550e8400_plot.csv",
    "JSON generated: app/data/outputs/550e8400_layout.json",
    "Transitioned to ASSET_GENERATION"
  ]
}
```

**State Values:**

- `INIT`: 초기화
- `PLOT_PLANNING`: 플롯 기획 중
- `ASSET_GENERATION`: 에셋 생성 중 (병렬)
- `RENDERING`: 영상 합성 중
- `END`: 완료
- `FAILED`: 실패
- `RECOVER`: 복구 시도 중

**Status Codes:**

- `200 OK`: 조회 성공
- `404 Not Found`: Run 없음

---

#### 4. Upload Reference Image

**POST** `/api/uploads`

참조 이미지를 업로드합니다 (ComfyUI 입력용).

**Request:**

`multipart/form-data`

- `file` (file): 이미지 파일

**Response:**

```json
{
  "filename": "ref_abc123def456.png",
  "path": "app/data/uploads/ref_abc123def456.png",
  "size": 524288
}
```

**Status Codes:**

- `200 OK`: 업로드 성공
- `413 Payload Too Large`: 파일 너무 큼
- `422 Unprocessable Entity`: 잘못된 파일 형식

---

## WebSocket API

### Connect

**WS** `/ws/{run_id}`

Run의 실시간 진행 상황을 수신합니다.

**Path Parameters:**

- `run_id` (string): Run 식별자

### Message Types

#### 1. Initial State

연결 시 초기 상태 전송.

```json
{
  "type": "initial_state",
  "state": "ASSET_GENERATION",
  "progress": 0.5,
  "artifacts": { ... },
  "logs": [ ... ]
}
```

#### 2. State Change

상태 전이 시 알림.

```json
{
  "type": "state_change",
  "state": "RENDERING",
  "message": "Transitioned to RENDERING"
}
```

#### 3. Progress Update

진행률 업데이트.

```json
{
  "type": "progress",
  "progress": 0.8,
  "message": "Rendering scene 3/3..."
}
```

#### 4. Ping/Pong

연결 유지용.

**Client → Server:**

```json
{ "type": "ping" }
```

**Server → Client:**

```json
{ "type": "pong" }
```

### Usage Example (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/550e8400-e29b-41d4-a716-446655440000');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'state_change') {
    console.log('State:', data.state, data.message);
  } else if (data.type === 'progress') {
    console.log('Progress:', data.progress * 100 + '%');
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

---

## FSM Testing Endpoints (개발용)

### 1. Transition State

**POST** `/api/fsm/{run_id}/transition`

수동으로 상태 전이 (테스트용).

**Request Body:**

```json
{
  "target_state": "RENDERING",
  "metadata": {
    "reason": "manual_test"
  }
}
```

**Response:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_state": "ASSET_GENERATION",
  "current_state": "RENDERING",
  "history": ["INIT", "PLOT_PLANNING", "ASSET_GENERATION", "RENDERING"]
}
```

### 2. Get FSM State

**GET** `/api/fsm/{run_id}/state`

FSM 상태 조회.

**Response:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_state": "RENDERING",
  "history": ["INIT", "PLOT_PLANNING", "ASSET_GENERATION", "RENDERING"],
  "is_terminal": false,
  "can_recover": true,
  "metadata": {}
}
```

### 3. Fail Run

**POST** `/api/fsm/{run_id}/fail`

Run을 실패 상태로 변경 (테스트용).

**Query Parameters:**

- `error_message` (string): 에러 메시지

**Response:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_state": "FAILED",
  "error": "Manual failure"
}
```

---

## Error Responses

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- `400 Bad Request`: 잘못된 요청
- `404 Not Found`: 리소스 없음
- `422 Unprocessable Entity`: 입력 검증 실패
- `500 Internal Server Error`: 서버 오류

---

## Rate Limiting

현재 Rate Limiting은 구현되지 않았습니다. 프로덕션 배포 시 추가 필요.

---

## Authentication

현재 인증은 구현되지 않았습니다. 프로덕션 배포 시 API 키 또는 OAuth 추가 필요.
