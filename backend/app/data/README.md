# Data 디렉토리

AutoShorts 데이터 파일 및 출력 관리

## 디렉토리 구조

```
app/data/
├── samples/          # 샘플 파일
│   ├── sample.csv                    # 기본 plot 샘플
│   ├── sample_characters.json        # 기본 캐릭터 샘플
│   ├── sample_narration.csv          # 해설 포함 plot 샘플
│   └── sample_narration_characters.json  # 해설 포함 캐릭터 샘플
├── outputs/          # 생성된 출력 (Git 제외)
│   └── {run_id}/     # 각 실행별 디렉토리
│       ├── characters.json  # 캐릭터 정의
│       ├── plot.csv         # 장면 시나리오
│       ├── layout.json      # 최종 레이아웃
│       └── ...              # 이미지, 오디오 등
└── uploads/          # 업로드 파일 (있는 경우)
```

## 스키마

### 1. characters.json

캐릭터 외형 및 설정 정의

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `char_id` | string | ✅ | 캐릭터 ID | `char_1` |
| `name` | string | ✅ | 캐릭터 이름 | `주인공` |
| `appearance` | string | ✅ | 외형 묘사 (이미지 생성 프롬프트용) | `귀여운 흰색 고양이, 파란색 우주복` |
| `personality` | string | ✅ | 성격/특징 | `용감하고 호기심 많은` |
| `voice_profile` | string | ✅ | 음성 프로필 | `default` |
| `seed` | integer | ✅ | 이미지 생성용 시드 | `1002` |

### 2. plot.csv (v3)

장면별 시나리오 및 표정/포즈

| 컬럼 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `scene_id` | string | ✅ | 장면 ID (순서 정보 포함) | `scene_1`, `scene_2` |
| `char_id` | string | ✅ | 캐릭터 ID (characters.json 참조) | `char_1`, `char_2` |
| `expression` | string | ✅ | 표정 (이미지 생성용) | `excited`, `happy`, `none` |
| `pose` | string | ✅ | 포즈 (이미지 생성용) | `standing`, `pointing`, `none` |
| `text` | string | ✅ | 대사 또는 해설 | `안녕하세요!` |
| `text_type` | string | ✅ | dialogue 또는 narration | `dialogue` |
| `emotion` | string | ✅ | 감정 (음성 생성용) | `neutral`, `happy`, `sad` |
| `subtitle_position` | string | ✅ | 자막 위치 | `top`, `bottom` |
| `duration_ms` | integer | ✅ | 장면 지속 시간 (밀리초) | `5000` |

### text_type 설명

- **dialogue** (대사): 캐릭터가 말하는 대사
  - 자막: 큰따옴표 자동 추가 → `"안녕하세요!"`
  - TTS 생성됨

- **narration** (해설): 해설/나레이션
  - 자막: 큰따옴표 없음 → `옛날 옛적에...`
  - TTS 생성됨

### 예시

**characters.json**:
```json
{
  "characters": [
    {
      "char_id": "char_1",
      "name": "주인공",
      "appearance": "귀여운 흰색 고양이, 파란색 우주복 착용, 큰 눈망울",
      "personality": "용감하고 호기심 많은 탐험가",
      "voice_profile": "default",
      "seed": 1002
    }
  ]
}
```

**plot.csv**:
```csv
scene_id,char_id,expression,pose,text,text_type,emotion,subtitle_position,duration_ms
scene_1,char_1,excited,standing,우주선에 탑승했습니다,dialogue,happy,bottom,5000
scene_2,char_1,amazed,looking_up,별들이 정말 아름답네요!,dialogue,happy,top,5000
```

## JSON 스키마 (layout.json)

characters.json + plot.csv → layout.json 변환

### Characters (from characters.json)
- characters.json을 그대로 사용
- `personality` → `persona` 필드로 매핑
- characters.json이 없으면 CSV에서 추출 (fallback)

### Scene (from plot.csv)
- `dialogue`: text를 대사로 변환
- `subtitles`: text를 자막으로 변환 (dialogue면 큰따옴표 추가)
- `images`: appearance + expression + pose로 이미지 프롬프트 생성
- `sfx`: text와 emotion에서 자동 추출
- `sequence`: scene_id에서 자동 추출 (scene_1 → 1)

### 이미지 프롬프트 생성
```
appearance + expression + pose
예: "귀여운 흰색 고양이, 파란색 우주복, excited expression, standing pose"
```

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

### v3 (2025-11-05) - 현재
- ✅ **캐릭터 정의 분리**: characters.json 별도 파일
- ✅ `expression`, `pose` 추가 (이미지 생성 제어)
- ❌ `char_name` 제거 (characters.json에서 참조)
- 이미지 생성: `appearance + expression + pose` 조합

### v2 (2025-11-05) - deprecated
- ❌ `sequence` 컬럼 제거
- ❌ `subtitle_text` 제거
- ✅ `text` 일원화
- ✅ `text_type` 추가

### v1 (이전 - deprecated)
- sequence, char_name 컬럼 있음
- text와 subtitle_text 분리

## 주의사항

- 출력 파일(`outputs/`)은 Git에 커밋되지 않습니다 (.gitignore)
- 필요한 CSV/JSON은 별도로 백업하세요
- 오래된 출력은 주기적으로 삭제 권장
- 샘플 파일 수정 시 스키마 준수 필수
