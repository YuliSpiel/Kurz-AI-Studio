# DEPRECATED - GCP Cloud Run Deployment

> **이 폴더의 설정은 더 이상 사용되지 않습니다.**
>
> Railway 배포로 전환되었습니다.
>
> 새 배포 가이드: [../railway/README.md](../railway/README.md)

---

## 왜 전환했나요?

1. **복잡한 설정** - GCP는 Cloud Build, Cloud Run, Secret Manager, VPC 등 여러 서비스 설정 필요
2. **Worker 배포 어려움** - Celery Worker를 위해 별도 VM 필요
3. **비용** - Memorystore(Redis)만 해도 월 $30+
4. **자동 배포 없음** - GitHub 연동이 번거로움

## Railway의 장점

- Git push만으로 자동 배포
- Redis 클릭 한 번으로 추가
- Worker도 같은 방식으로 배포
- 사용량 기반 과금 (더 저렴)

---

## 기존 파일들 (참고용)

- `cloudbuild.yaml` - Cloud Build 설정
- `env.yaml` - 환경변수 템플릿
- `deploy.sh` - 배포 스크립트

## 만약 GCP를 다시 사용해야 한다면

이 파일들을 다시 활성화하고, 각 cloudbuild.yaml 파일의 주석을 제거하세요.
