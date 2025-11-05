# CSV Files 폴더

이 폴더에는 GPT-4o-mini가 생성한 모든 CSV 파일이 저장됩니다.

## 파일 네이밍 규칙

```
YYYYMMDD_HHMMSS_<run_id 앞 8자리>.csv
```

**예시:**
- `20251104_113045_41badd30.csv`
- `20251104_114523_a7f2c9d1.csv`

## 내용

각 CSV 파일은 다음 컬럼을 포함합니다:

| 컬럼 | 설명 |
|-----|------|
| scene_id | 씬 ID (scene_1, scene_2, ...) |
| sequence | 씬 순서 (1, 2, 3, ...) |
| char_id | 캐릭터 ID (char_1, char_2) |
| char_name | 캐릭터 이름 |
| text | 대사 |
| emotion | 감정 (neutral, happy, sad, excited, angry, surprised) |
| subtitle_text | 자막 텍스트 |
| subtitle_position | 자막 위치 (top, bottom) |
| duration_ms | 장면 지속 시간 (밀리초) |

## 확인 방법

```bash
# 최신 CSV 파일 보기
ls -lt backend/app/data/outputs/csv_files/ | head -n 5

# CSV 내용 확인
cat backend/app/data/outputs/csv_files/20251104_113045_41badd30.csv
```

## 주의사항

- 이 폴더의 CSV 파일은 Git에 커밋되지 않습니다 (.gitignore)
- 필요한 CSV는 별도로 백업하세요
- 오래된 파일은 주기적으로 삭제 권장
