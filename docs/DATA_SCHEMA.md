# AutoShorts 데이터 스키마

## CSV 스키마 (Plot Planning 출력)

기획자 Agent가 생성하는 중간 형식입니다.

### 컬럼 정의

| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `scene_id` | string | 씬 식별자 | "scene_1" |
| `sequence` | int | 씬 순서 (1부터 시작) | 1 |
| `char_id` | string | 등장 캐릭터 ID | "char_1" |
| `char_name` | string | 캐릭터 이름 | "주인공" |
| `text` | string | 대사 내용 | "안녕하세요!" |
| `emotion` | string | 감정 (neutral, happy, sad 등) | "happy" |
| `subtitle_text` | string | 자막 텍스트 (대사와 다를 수 있음) | "장면 1" |
| `subtitle_position` | string | 자막 위치 (top, center, bottom) | "bottom" |
| `duration_ms` | int | 씬 지속 시간 (밀리초) | 5000 |

### 샘플 CSV

```csv
scene_id,sequence,char_id,char_name,text,emotion,subtitle_text,subtitle_position,duration_ms
scene_1,1,char_1,주인공,우주선에 탑승했습니다,neutral,우주 여행 시작,bottom,5000
scene_2,2,char_1,주인공,별들이 정말 아름답네요!,happy,별빛 속으로,top,5000
scene_3,3,char_2,친구,함께 떠나볼까요?,excited,모험의 시작,bottom,5000
```

---

## JSON 스키마 (최종 레이아웃)

모든 Agent가 작업하는 최종 데이터 구조입니다.

### 최상위 구조

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "AutoShorts 550e8400",
  "mode": "story",
  "timeline": { ... },
  "characters": [ ... ],
  "scenes": [ ... ],
  "global_bgm": { ... },
  "metadata": { ... }
}
```

### Timeline

영상 전체 메타데이터.

```json
{
  "total_duration_ms": 15000,
  "aspect_ratio": "9:16",
  "fps": 30,
  "resolution": "1080x1920"
}
```

### Character

캐릭터 정의.

```json
{
  "char_id": "char_1",
  "name": "주인공",
  "persona": "용감하고 호기심 많은 탐험가",
  "voice_profile": "default",
  "seed": 1001
}
```

**필드**:
- `char_id`: 고유 식별자
- `name`: 캐릭터 이름
- `persona`: 성격/설정 (이미지 프롬프트에 사용)
- `voice_profile`: TTS 음성 ID
- `seed`: 이미지 생성 시 고정 seed (일관성 유지)

### Scene

씬 단위 구조.

```json
{
  "scene_id": "scene_1",
  "sequence": 1,
  "duration_ms": 5000,
  "images": [ ... ],
  "subtitles": [ ... ],
  "dialogue": [ ... ],
  "bgm": null,
  "sfx": [ ... ],
  "bg_seed": 2001,
  "transition": "fade"
}
```

#### images (ImageSlot)

이미지 배치 슬롯.

```json
{
  "slot_id": "center",
  "type": "character",
  "ref_id": "char_1",
  "image_url": "app/data/outputs/run_123_scene_1_center.png",
  "z_index": 1
}
```

**필드**:
- `slot_id`: "left", "center", "right" (좌/중앙/우 배치)
- `type`: "character", "background", "prop"
- `ref_id`: 참조 ID (character의 경우 char_id)
- `image_url`: 생성된 이미지 경로 (Designer가 채움)
- `z_index`: 레이어 순서 (높을수록 위)

#### subtitles (Subtitle)

자막.

```json
{
  "position": "bottom",
  "text": "우주 여행 시작",
  "style": "default",
  "start_ms": 0,
  "duration_ms": 5000
}
```

**필드**:
- `position`: "top", "center", "bottom"
- `text`: 자막 텍스트
- `style`: 스타일 프리셋 (향후 확장)
- `start_ms`: 씬 시작 기준 타이밍
- `duration_ms`: 자막 표시 시간

#### dialogue (DialogueLine)

대사 라인.

```json
{
  "line_id": "scene_1_line_1",
  "char_id": "char_1",
  "text": "우주선에 탑승했습니다",
  "emotion": "neutral",
  "audio_url": "app/data/outputs/run_123_scene_1_line_1.mp3",
  "start_ms": 0,
  "duration_ms": 2000
}
```

**필드**:
- `line_id`: 고유 라인 ID
- `char_id`: 말하는 캐릭터
- `text`: 대사 텍스트
- `emotion`: 감정 ("neutral", "happy", "sad", "excited", "angry", "surprised")
- `audio_url`: TTS 음성 파일 경로 (Voice Agent가 채움)
- `start_ms`: 씬 시작 기준 타이밍
- `duration_ms`: 음성 재생 시간

#### bgm (BGM)

씬별 배경음악 (선택적, 없으면 global_bgm 사용).

```json
{
  "bgm_id": "scene_1_bgm",
  "genre": "ambient",
  "mood": "calm",
  "audio_url": "app/data/outputs/run_123_scene_1_bgm.mp3",
  "start_ms": 0,
  "duration_ms": 5000,
  "volume": 0.3
}
```

**필드**:
- `bgm_id`: BGM 식별자
- `genre`: 장르 (ambient, cinematic, upbeat 등)
- `mood`: 무드 (calm, energetic, mysterious 등)
- `audio_url`: 오디오 파일 경로 (Composer가 채움)
- `start_ms`: 씬 시작 기준 타이밍
- `duration_ms`: 재생 시간
- `volume`: 볼륨 (0.0~1.0)

#### sfx (SFX)

효과음.

```json
{
  "sfx_id": "scene_1_sfx_whoosh",
  "tags": ["whoosh", "transition"],
  "audio_url": "app/data/sfx/whoosh.mp3",
  "start_ms": 500,
  "volume": 0.5
}
```

**필드**:
- `sfx_id`: 효과음 식별자
- `tags`: 무드 태그 배열 (검색/선택에 사용)
- `audio_url`: 효과음 파일 경로
- `start_ms`: 씬 시작 기준 타이밍
- `volume`: 볼륨 (0.0~1.0)

### global_bgm

전역 배경음악 (모든 씬에 적용, 씬별 BGM이 없을 경우).

```json
{
  "bgm_id": "global_bgm",
  "genre": "ambient",
  "mood": "cinematic",
  "audio_url": "app/data/outputs/run_123_global_bgm.mp3",
  "start_ms": 0,
  "duration_ms": 15000,
  "volume": 0.3
}
```

### metadata

추가 메타데이터 (자유 형식).

```json
{
  "art_style": "파스텔 수채화",
  "music_genre": "ambient",
  "generated_from": "app/data/outputs/run_123_plot.csv",
  "comfy_workflow": "flux_omni_lora.json",
  "tts_provider": "elevenlabs",
  "music_provider": "mubert"
}
```

---

## 데이터 흐름

### 1. 사용자 입력 → CSV

**입력**:
```json
{
  "mode": "story",
  "prompt": "우주를 여행하는 고양이",
  "num_characters": 1,
  "num_cuts": 3
}
```

**변환** (기획자 Agent):
- LLM 또는 룰 기반으로 CSV 생성
- 등장인물, 씬별 대사, 자막 구조화

**출력**: `run_123_plot.csv`

### 2. CSV → JSON

**변환 로직** (`utils/csv_to_json.py`):

1. **CSV 읽기 및 그룹화**
   - scene_id로 행 그룹화
   - 캐릭터 추출 (unique char_id)

2. **Character 생성**
   ```python
   for char_id, char_name in characters:
       seed = BASE_CHAR_SEED + int(char_id.split("_")[1])
       Character(char_id, name, persona, "default", seed)
   ```

3. **Scene 생성**
   - CSV의 각 scene_id → Scene 객체
   - dialogue: CSV row → DialogueLine
   - subtitles: CSV subtitle_* 컬럼 → Subtitle
   - images: 기본 슬롯 생성 (image_url은 빈 값)
   - bg_seed: `BG_SEED_BASE + sequence`

4. **Timeline 계산**
   - `total_duration_ms = sum(scene.duration_ms)`

5. **JSON 저장**

**출력**: `run_123_layout.json`

### 3. JSON 업데이트 (Agent별)

#### Designer Agent

- `scenes[].images[].image_url` 채우기
- ComfyUI 생성 결과 경로 입력

#### Composer Agent

- `global_bgm.audio_url` 채우기
- 또는 `scenes[].bgm.audio_url` (씬별 BGM)
- `scenes[].sfx[].audio_url` 채우기

#### Voice Agent

- `scenes[].dialogue[].audio_url` 채우기
- TTS 생성 결과 경로 입력

#### Director Agent

- 최종 JSON 읽기
- MoviePy로 영상 합성
- `artifacts.video_url` 추가

---

## Seed 정책

일관된 이미지 생성을 위해 seed를 고정합니다.

### Character Seed

```python
char_seed = BASE_CHAR_SEED + char_number
```

- `char_1` → 1001
- `char_2` → 1002

**목적**: 같은 캐릭터는 항상 동일한 외형 유지

### Background Seed

```python
bg_seed = BG_SEED_BASE + scene_sequence
```

- `scene_1` → 2001
- `scene_2` → 2002

**목적**: 씬별 배경 다양성 확보, 재생성 시 동일 결과

---

## SFX 태그 추출

대사 텍스트와 감정에서 효과음 태그를 추출합니다.

### 규칙 기반 매핑

```python
EMOTION_SFX_MAP = {
    "happy": ["upbeat_chime", "sparkle"],
    "sad": ["soft_piano", "rain"],
    "excited": ["energetic_swoosh", "pop"],
    "calm": ["gentle_bell", "ambient_pad"],
    "neutral": ["subtle_whoosh"],
}
```

### 키워드 기반 추출

| 키워드 | SFX 태그 |
|--------|---------|
| 문, 열다, 닫다 | door |
| 발소리, 걷다, 뛰다 | footsteps |
| 바람, 공기 | wind |
| 물, 바다, 강 | water |

### 예시

```python
text = "우주선 문이 열렸습니다"
emotion = "neutral"

tags = extract_sfx_tags(text, emotion)
# → ["door", "subtle_whoosh"]
```

---

## JSON 스키마 검증

Pydantic 모델로 자동 검증됩니다.

```python
from app.schemas.json_layout import ShortsJSON

with open("run_123_layout.json") as f:
    data = json.load(f)

shorts = ShortsJSON(**data)  # 검증 및 파싱
```

**검증 항목**:
- 필수 필드 존재
- 타입 일치 (string, int, float, enum)
- 범위 제약 (예: volume 0.0~1.0)
- 참조 무결성 (예: dialogue.char_id가 characters에 존재)

---

## 확장 가능성

### 새로운 필드 추가

예: **transitions** (씬 전환 효과)

1. Pydantic 모델 확장:
   ```python
   class Scene(BaseModel):
       ...
       transition: str = "fade"
       transition_duration_ms: int = 500
   ```

2. CSV 컬럼 추가: `transition`

3. Director Agent에서 전환 효과 적용

### 다중 캐릭터 대화

현재는 씬당 1명 대사. 확장 시:

```json
{
  "scene_id": "scene_1",
  "dialogue": [
    { "char_id": "char_1", "text": "안녕?" },
    { "char_id": "char_2", "text": "반가워!" }
  ]
}
```

타이밍 자동 계산 (순차 또는 중첩).

---

## 샘플 JSON (전체)

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "우주 여행하는 고양이",
  "mode": "story",
  "timeline": {
    "total_duration_ms": 15000,
    "aspect_ratio": "9:16",
    "fps": 30,
    "resolution": "1080x1920"
  },
  "characters": [
    {
      "char_id": "char_1",
      "name": "주인공 고양이",
      "persona": "호기심 많고 용감한 우주 탐험가",
      "voice_profile": "default",
      "seed": 1001
    }
  ],
  "scenes": [
    {
      "scene_id": "scene_1",
      "sequence": 1,
      "duration_ms": 5000,
      "images": [
        {
          "slot_id": "center",
          "type": "character",
          "ref_id": "char_1",
          "image_url": "app/data/outputs/run_123_scene_1_center.png",
          "z_index": 1
        }
      ],
      "subtitles": [
        {
          "position": "bottom",
          "text": "우주 여행 시작",
          "style": "default",
          "start_ms": 0,
          "duration_ms": 5000
        }
      ],
      "dialogue": [
        {
          "line_id": "scene_1_line_1",
          "char_id": "char_1",
          "text": "우주선에 탑승했어요",
          "emotion": "neutral",
          "audio_url": "app/data/outputs/run_123_scene_1_line_1.mp3",
          "start_ms": 0,
          "duration_ms": 2000
        }
      ],
      "bgm": null,
      "sfx": [
        {
          "sfx_id": "scene_1_sfx",
          "tags": ["whoosh", "ambient"],
          "audio_url": "app/data/sfx/whoosh.mp3",
          "start_ms": 0,
          "volume": 0.5
        }
      ],
      "bg_seed": 2001,
      "transition": "fade"
    }
  ],
  "global_bgm": {
    "bgm_id": "global_bgm",
    "genre": "ambient",
    "mood": "dreamy",
    "audio_url": "app/data/outputs/run_123_global_bgm.mp3",
    "start_ms": 0,
    "duration_ms": 15000,
    "volume": 0.3
  },
  "metadata": {
    "art_style": "파스텔 수채화",
    "music_genre": "ambient",
    "generated_from": "app/data/outputs/run_123_plot.csv"
  }
}
```
