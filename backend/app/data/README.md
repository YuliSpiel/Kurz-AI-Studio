# Data 디렉토리

AutoShorts 데이터 파일 및 출력 관리

## 디렉토리 구조

```
app/data/
├── samples/          # 샘플 CSV 파일
│   ├── sample.csv            # 기본 샘플 (대사만)
│   └── sample_narration.csv  # 대사 + 해설 샘플
├── outputs/          # 생성된 출력 (Git 제외)
│   └── {run_id}/     # 각 실행별 디렉토리
│       ├── plot.csv       # GPT 생성 플롯
│       ├── layout.json    # 최종 레이아웃
│       └── ...            # 이미지, 오디오 등
└── uploads/          # 업로드 파일 (있는 경우)
```

## CSV 스키마 (plot.csv)

### 현재 스키마 (v2)

각 CSV 파일은 다음 컬럼을 포함합니다:

| 컬럼 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `scene_id` | string | ✅ | 장면 ID (순서 정보 포함) | `scene_1`, `scene_2` |
| `char_id` | string | ✅ | 캐릭터 ID | `char_1`, `char_2` |
| `char_name` | string | ✅ | 캐릭터 이름 | `주인공`, `해설자` |
| `text` | string | ✅ | 대사 또는 해설 (일원화됨) | `안녕하세요!` |
| `text_type` | string | ✅ | dialogue 또는 narration | `dialogue` |
| `emotion` | string | ✅ | 감정 상태 | `neutral`, `happy`, `sad` |
| `subtitle_position` | string | ✅ | 자막 위치 | `top`, `bottom` |
| `duration_ms` | integer | ✅ | 장면 지속 시간 (밀리초) | `5000` |

### text_type 설명

- **dialogue** (대사): 캐릭터가 말하는 대사
  - 자막: 큰따옴표 자동 추가 → `"안녕하세요!"`
  - TTS 생성됨

- **narration** (해설): 해설/나레이션
  - 자막: 큰따옴표 없음 → `옛날 옛적에...`
  - TTS 생성됨

### CSV 예시

```csv
scene_id,char_id,char_name,text,text_type,emotion,subtitle_position,duration_ms
scene_1,char_1,주인공,안녕하세요!,dialogue,happy,bottom,4000
scene_2,char_1,해설자,이야기가 시작됩니다,narration,neutral,bottom,5000
```

## JSON 스키마 (layout.json)

CSV → JSON 변환 시 추가되는 정보:

### Characters
- `persona`: 자동 생성됨 (`"{char_name} 설정"`)
- `voice_profile`: 기본값 `"default"`
- `seed`: 캐릭터 일관성을 위한 고정 시드

### Scene
- `dialogue`: text를 대사로 변환
- `subtitles`: text를 자막으로 변환 (dialogue면 큰따옴표 추가)
- `images`: placeholder 자동 생성 (이미지 태스크에서 채움)
- `sfx`: text와 emotion에서 자동 추출
- `sequence`: scene_id에서 자동 추출 (scene_1 → 1)

## 확인 방법

```bash
# 샘플 CSV 보기
cat backend/app/data/samples/sample.csv

# 최신 생성 결과 확인
ls -lt backend/app/data/outputs/ | head -n 5

# 특정 run_id 결과 보기
cat backend/app/data/outputs/20251105_1234_테스트/plot.csv
cat backend/app/data/outputs/20251105_1234_테스트/layout.json
```

## 변경 이력

### v2 (2025-11-05) - 현재
- ❌ `sequence` 컬럼 제거 (scene_id에서 자동 추출)
- ❌ `subtitle_text` 제거
- ✅ `text` 일원화 (대사/해설 모두 포함)
- ✅ `text_type` 추가 (dialogue/narration 구분)
- JSON 생성 시 `persona` 자동 추가

### v1 (이전 - deprecated)
- sequence 컬럼 있음
- text와 subtitle_text 분리
- text_type 없음

## 주의사항

- 출력 파일(`outputs/`)은 Git에 커밋되지 않습니다 (.gitignore)
- 필요한 CSV/JSON은 별도로 백업하세요
- 오래된 출력은 주기적으로 삭제 권장
- 샘플 파일 수정 시 스키마 준수 필수
