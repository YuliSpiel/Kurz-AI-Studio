# AutoShorts 데이터 스키마

## CSV 스키마 (Plot Generation 출력)

기획자 Agent가 생성하는 중간 형식입니다.

### 컬럼 정의

| 컬럼명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `scene_id` | string | 씬 식별자 (순서 포함) | "scene_1" |
| `char_id` | string | 등장 캐릭터 ID | "char_1" |
| `char_name` | string | 캐릭터 이름 | "주인공" |
| `text` | string | 대사 또는 해설 내용 | "안녕하세요!" |
| `text_type` | string | 텍스트 타입 (dialogue/narration) | "dialogue" |
| `emotion` | string | 감정 (neutral, happy, sad 등) | "happy" |
| `subtitle_position` | string | 자막 위치 (top, center, bottom) | "bottom" |
| `duration_ms` | int | 씬 지속 시간 (밀리초) | 5000 |

**참고:**
- `sequence` 필드는 제거됨 (scene_id에서 추출: "scene_1" → 1)
- `subtitle_text`는 `text`로 통합됨
- `text_type`이 `dialogue`면 자막에 큰따옴표 자동 추가
- 자세한 스키마 정의는 `CSV_SCHEMA.md` 참조

### 샘플 CSV

```csv
scene_id,char_id,char_name,text,text_type,emotion,subtitle_position,duration_ms
scene_1,char_1,주인공,우주선에 탑승했습니다,dialogue,neutral,bottom,5000
scene_2,char_1,주인공,별들이 정말 아름답네요!,dialogue,happy,top,5000
scene_2,,,주인공이 우주를 바라보며 감탄한다,narration,neutral,top,3000
scene_3,char_2,친구,함께 떠나볼까요?,dialogue,excited,bottom,5000
```

---

## JSON 스키마 (최종 레이아웃)

모든 Agent가 작업하는 최종 데이터 구조입니다. 전체 예시는 파일 하단 참조.

### 최상위 구조

```json
{
  "project_id": "20251105_1430_우주여행고양이",
  "title": "AutoShorts 20251105_1430_우주여행고양이",
  "mode": "story",
  "timeline": { ... },
  "characters": [ ... ],
  "scenes": [ ... ],
  "global_bgm": { ... },
  "metadata": { ... }
}
```

**참고:** `project_id`는 `YYYYMMDD_HHMM_프롬프트첫8글자` 형식

---

## 데이터 흐름

### 1. 사용자 입력 → CSV

**입력**: RunSpec 
**처리**: Plan Agent (GPT-4o-mini 또는 룰 기반)
**출력**: `{run_id}/plot.csv`

### 2. CSV → JSON

**처리**: `utils/csv_to_json.py`
- scene_id에서 sequence 추출
- text + text_type → 자막 생성 (dialogue면 큰따옴표 추가)
- Character, Scene, Timeline 객체 생성

**출력**: `{run_id}/layout.json`

### 3. JSON 업데이트 (각 Agent)

- **Designer**: `scenes[].images[].image_url` 채우기
- **Composer**: `global_bgm.audio_url`, `scenes[].sfx[].audio_url` 채우기
- **Voice**: `scenes[].dialogue[].audio_url` 채우기
- **Director**: JSON 읽고 MoviePy로 영상 합성
- **QA**: 품질 검수 (Pass → END, Fail → PLOT_GENERATION 재시도)

---

**전체 JSON 스키마 및 필드 정의는 기존 내용 유지 (너무 길어서 생략)**
