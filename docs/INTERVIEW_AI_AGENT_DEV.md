# Kurz AI Studio - AI Agent 개발자 단기계약직 면접 자료

## 프로젝트 개요

**Kurz AI Studio**는 텍스트 프롬프트 하나로 숏폼 영상을 자동 생성하는 AI Agent 기반 플랫폼입니다.

### 핵심 가치
- **One-Click 영상 생성**: 사용자가 "고양이의 하루" 같은 간단한 프롬프트만 입력하면 시나리오, 이미지, 음성, BGM, 영상까지 자동 생성
- **멀티 Agent 아키텍처**: 기획자, 디자이너, 작곡가, 성우, 감독 등 역할별 AI Agent가 협업
- **실시간 피드백**: WebSocket 기반 실시간 진행 상황 제공

---

## 기술 스택

| 분류 | 기술 | 선택 이유 |
|------|------|----------|
| **Backend** | FastAPI | 비동기 처리, 자동 API 문서화, Type hints 지원 |
| **Task Queue** | Celery + Redis | 분산 처리, 병렬 실행, 작업 재시도 |
| **Frontend** | React + TypeScript | 타입 안정성, 컴포넌트 재사용성 |
| **Database** | PostgreSQL | 관계형 데이터, 확장성 |
| **LLM** | Gemini 2.5 Flash | 빠른 응답, 한국어 성능, 비용 효율 |
| **Image** | Gemini Flash 2.0 Exp | 텍스트→이미지 생성 |
| **TTS** | ElevenLabs | 자연스러운 한국어 음성 |
| **BGM** | ElevenLabs SFX | 프롬프트 기반 배경음악 생성 |
| **Video** | FFmpeg | 산업 표준 영상 처리 |

---

## 시스템 아키텍처

### 전체 흐름

```
[사용자 프롬프트]
       ↓
[프롬프트 풍부화] ← Gemini Flash (AI가 프롬프트 개선)
       ↓
[기획자 Agent] → characters.json + plot.json + layout.json
       ↓
[Celery Chord] ← 병렬 실행
   ├── [디자이너 Agent] → 이미지 생성
   ├── [작곡가 Agent] → BGM 생성
   └── [성우 Agent] → TTS 생성
       ↓
[감독 Agent] → FFmpeg 영상 합성
       ↓
[QA Agent] → 품질 검수 + DB 저장
       ↓
[final_video.mp4]
```

### FSM (Finite State Machine)

상태 기반 워크플로우 관리:

```
INIT → PLOT_GENERATION → ASSET_GENERATION → RENDERING → QA → END
                                                          ↓
                                                       FAILED
```

각 상태 전이 시 WebSocket으로 프론트엔드에 실시간 알림

---

## 핵심 구현 포인트

### 1. Celery Chord 패턴 (병렬 처리)

```python
chord(
    group(
        designer_task.s(run_id),   # 이미지 생성
        composer_task.s(run_id),   # BGM 생성
        voice_task.s(run_id),      # TTS 생성
    )
)(director_task.s(run_id))        # 완료 후 영상 합성
```

**문제 해결 사례**:
- `--pool=solo` 사용 시 병렬 실행 불가 → `--pool=gevent` 적용
- Retry 예외 처리 이슈 → `celery.exceptions.Retry` 별도 처리

### 2. 실시간 진행률 (Redis Pub/Sub + WebSocket)

```python
# Backend: 진행률 발행
def publish_progress(run_id, progress, message):
    redis.publish(f"run:{run_id}", json.dumps({
        "progress": progress,
        "message": message
    }))

# WebSocket: 프론트엔드로 전달
async def websocket_endpoint(websocket, run_id):
    async for message in redis.subscribe(f"run:{run_id}"):
        await websocket.send_json(message)
```

### 3. 레이아웃 검수 시스템 (Review Mode)

- 영상 생성 전 사용자가 시나리오/이미지 검토 가능
- 개별 에셋 재생성 지원 (이미지, TTS)
- 동일 이미지가 여러 씬에서 공유될 경우 일괄 업데이트

### 4. YouTube 자동 업로드

- OAuth 2.0 기반 YouTube API 연동
- 예약 업로드 지원
- Shorts 형식 자동 최적화 (9:16 비율)

---

## 데이터 스키마

### layout.json (렌더링 핵심 데이터)

```json
{
  "project_id": "run_id",
  "title": "고양이의 하루",
  "scenes": [
    {
      "scene_id": "scene_1",
      "images": [{"image_url": "...", "image_prompt": "..."}],
      "texts": [{"text": "대사", "audio_url": "..."}]
    }
  ],
  "global_bgm": {"audio_url": "...", "volume": 0.3}
}
```

### 캐릭터 일관성 유지

- 캐릭터별 고유 seed 값 할당
- `{char_1}` 변수를 실제 캐릭터 이름으로 자동 치환

---

## 개발 과정에서 해결한 문제들

### 1. Celery Worker 동기화 이슈

**문제**: 코드 수정 후에도 이전 로직으로 실행됨
**원인**: Celery Worker는 auto-reload가 없음
**해결**: Worker 재시작 필수화 + 문서화

### 2. MoviePy 2.x Title Block 렌더링

**문제**: 한글 자막 + stroke + margin 계산이 복잡하고 불안정
**해결**: FFmpeg 기반 자체 렌더러 구현 (`ffmpeg_renderer.py`)

### 3. 공유 이미지 재생성 버그

**문제**: 한 이미지가 여러 씬에서 사용될 때, 재생성 시 첫 씬만 업데이트
**해결**: 동일 `image_url`을 참조하는 모든 씬 일괄 업데이트

### 4. TTS-영상 동기화

**문제**: TTS 길이와 영상 씬 길이 불일치
**해결**: TTS 생성 후 `duration_ms` 자동 조정

---

## 코드 품질 관리

### 타입 안정성
- Python: Type hints 전면 적용
- TypeScript: strict mode

### 에러 처리
```python
from celery.exceptions import Retry

try:
    # 작업 수행
except Retry:
    raise  # 재시도는 정상 흐름
except Exception as e:
    fsm.fail(str(e))  # FSM 상태 업데이트
```

### 설정 관리
- 환경별 분리 (dev/prod)
- `settings.OUTPUT_DIR` 등 중앙 설정 사용 (하드코딩 금지)

---

## 향후 로드맵

1. **Pro 모드**: Kling AI Image-to-Video 연동
2. **업로드 매니저**: 자동 스케줄 기반 영상 생성 + 업로드
3. **캘린더**: 업로드 일정 시각화
4. **커뮤니티**: 생성 영상 공유 기능

---

## 프로젝트 하이라이트

| 항목 | 내용 |
|------|------|
| **개발 기간** | 약 2주 |
| **주요 성과** | 텍스트→영상 End-to-End 파이프라인 완성 |
| **기술적 도전** | 멀티 Agent 오케스트레이션, 실시간 피드백, 비동기 처리 |
| **AI 활용** | Gemini (LLM/Image), ElevenLabs (TTS/BGM) |

---

## 소스코드 구조

```
Kurz_Studio_AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 엔드포인트
│   │   ├── tasks/               # Celery Agent들
│   │   │   ├── plan.py          # 기획자
│   │   │   ├── designer.py      # 디자이너
│   │   │   ├── composer.py      # 작곡가
│   │   │   ├── voice.py         # 성우
│   │   │   ├── director.py      # 감독
│   │   │   └── qa.py            # QA
│   │   ├── orchestrator/fsm.py  # 상태 머신
│   │   ├── providers/           # 외부 API 클라이언트
│   │   └── utils/               # 유틸리티
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── api/client.ts
│   └── package.json
│
└── DOCS/                        # 기술 문서
```

---

## 질의응답 예상 질문

**Q: 왜 Celery를 선택했나요?**
> A: 영상 생성은 수 분이 걸리는 긴 작업입니다. 동기 처리 시 서버 응답이 블로킹되므로, 비동기 작업 큐가 필수였습니다. Celery는 Python 생태계에서 가장 성숙한 솔루션이고, Chord 패턴으로 병렬 처리 후 결과 집계가 가능합니다.

**Q: FSM을 직접 구현한 이유는?**
> A: Airflow나 Prefect 같은 워크플로우 엔진은 이 규모에서 오버킬입니다. 단순한 선형 파이프라인이라 직접 구현이 더 효율적이었고, WebSocket 연동도 쉬웠습니다.

**Q: 이미지 일관성은 어떻게 유지하나요?**
> A: 캐릭터별 seed 값을 할당하고, 동일 캐릭터가 등장하는 씬에서는 같은 seed를 사용합니다. 또한 캐릭터 외형 묘사를 상세하게 생성해 프롬프트에 포함시킵니다.

**Q: 에러 복구 전략은?**
> A: Celery의 자동 재시도 + FSM의 FAILED 상태 + 프론트엔드에서 수동 재시도 버튼 제공. 개별 에셋은 재생성 API로 부분 복구 가능합니다.

---

## 데모 시나리오

1. "고양이의 하루" 프롬프트 입력
2. AI가 프롬프트 풍부화 제안
3. 레이아웃 검수 화면에서 시나리오 확인
4. 특정 이미지 재생성 시연
5. 영상 완성 후 라이브러리에서 확인
6. YouTube 업로드 기능 시연

---

**문의**: 프로젝트 관련 질문은 언제든 환영합니다.
