좋다, 이제 이거 “스킬 장착용 사이드프로젝트 로드맵”으로 박제해보자 ✅

아래는 **실제 구현 순서 기준 체크리스트**야.
그냥 위에서부터 하나씩 지워나간다고 생각하면 됨.

---

## 0. 준비 단계

* [ ] Python 가상환경 만들기 & FastAPI, Uvicorn 설치
* [ ] Docker로 PostgreSQL, Redis 컨테이너 띄우기

  * [ ] `docker-compose.yml` or 단일 `docker run`으로 Postgres
  * [ ] Redis 컨테이너도 같이

---

## 1. FastAPI + Postgres + SQLAlchemy (기본 뼈대)

**목표: `/users`, `/runs`만 있는 가장 단순한 API 서버 만들기**

* [ ] `backend/app` 폴더 구조 만들기

  * [ ] `main.py` (FastAPI 앱)
  * [ ] `config.py` (환경변수, DB URL)
  * [ ] `database.py` (engine, session, Base)
* [ ] SQLAlchemy 모델 정의

  * [ ] `models/user.py` – 최소 필드: `id`, `email`, `username`
  * [ ] `models/run.py` – 최소 필드: `id`, `user_id`, `prompt`, `state`
* [ ] Alembic 설정

  * [ ] `alembic init` 실행
  * [ ] `env.py`에서 `Base.metadata` 연결
  * [ ] 첫 마이그레이션 생성 & 적용 (`alembic revision --autogenerate`, `upgrade head`)
* [ ] 최소 라우터 구현

  * [ ] `routers/users.py` – `POST /users` (회원 가입용, 매우 단순 버전)
  * [ ] `routers/runs.py` – `POST /runs`, `GET /runs/{id}`
* [ ] 로컬에서 테스트

  * [ ] `uvicorn app.main:app --reload` 실행
  * [ ] 브라우저/Swagger `/docs`에서 API 호출해보기

---

## 2. 인증 & JWT (로그인 가능한 서비스로 만들기)

**목표: “로그인한 유저만 run 생성 가능” 상태 만들기**

* [ ] 패스워드 해싱 설정

  * [ ] `utils/security.py`에 `hash_password`, `verify_password` 함수 만들기 (passlib)
* [ ] JWT 유틸

  * [ ] `utils/auth.py`에 `create_access_token`, `verify_token` 구현
* [ ] User 관련 Pydantic 스키마

  * [ ] `schemas/user.py` – `UserCreate`, `UserRead`, `UserLogin` 등
* [ ] Auth 라우터

  * [ ] `routers/auth.py` – `POST /auth/register`
  * [ ] `routers/auth.py` – `POST /auth/login` (JWT 발급)
* [ ] 현재 유저 디펜던시

  * [ ] `dependencies.py` – `get_current_user` (Authorization 헤더에서 토큰 파싱)
* [ ] Runs 라우터에 인증 적용

  * [ ] `POST /runs`에 `current_user: User = Depends(get_current_user)` 붙이기
* [ ] 테스트

  * [ ] 회원가입 → 로그인 → 발급된 토큰으로 `POST /runs` 호출 성공

---

## 3. Celery + Redis (비동기 파이프라인 기본)

**목표: “run 생성 → 바로 응답 / 실제 처리는 백그라운드”**

* [ ] Redis 컨테이너 실행 확인
* [ ] Celery 설정 파일

  * [ ] `tasks/__init__.py`, `celery_app` 생성
  * [ ] `broker_url`, `result_backend`를 Redis로 설정
* [ ] 샘플 태스크 만들기

  * [ ] `tasks/plan.py` – `@celery_app.task`로 `process_run(run_id)` 같은 더미 태스크
  * [ ] 태스크 안에서 `time.sleep(5)` 후 DB에서 `state = "DONE"` 업데이트
* [ ] Runs 생성 시 태스크 호출

  * [ ] `POST /runs`에서 run 저장 후 `process_run.delay(run.id)` 호출
* [ ] 워커 실행

  * [ ] `celery -A app.tasks.celery_app worker --loglevel=info`로 돌려보기
* [ ] 동작 확인

  * [ ] `POST /runs` → 즉시 응답
  * [ ] 몇 초 후 `GET /runs/{id}` → `state`가 DONE으로 바뀌는지 체크

---

## 4. S3/R2 스토리지 연동

**목표: “로컬 파일 대신 오브젝트 스토리지 + URL만 DB에 저장”**

* [ ] S3 또는 Cloudflare R2 버킷 생성
* [ ] `.env`에 스토리지 관련 키/엔드포인트 저장
* [ ] `services/storage_service.py` 구현

  * [ ] `upload_to_s3(local_path, s3_key) -> url`
* [ ] 샘플 파일 업로드 로직

  * [ ] Celery 태스크에서 임시 더미 파일 만들어 업로드 후 `runs.video_url` 업데이트
  * [ ] 업로드된 URL을 브라우저에서 직접 열어보기
* [ ] 실제 파이프라인과 연결

  * [ ] 나중에 영상 합성 파이프라인(`final_video.mp4`) 위치와 연결 예정

---

## 5. 크레딧 & 결제 (PortOne 연동)

**목표: “테스트 결제 → 크레딧 충전 → 크레딧으로 run 생성 제어”**

* [ ] DB 스키마 확장

  * [ ] `users.credits` 필드 추가 (기본 0)
  * [ ] `transactions` 테이블 생성 (charge/spend, amount, status 등)
* [ ] 크레딧 서비스

  * [ ] `services/credit_service.py` – `charge_credits`, `deduct_credits` 구현
* [ ] PortOne 설정

  * [ ] PortOne 테스트 상점/채널 등록
  * [ ] 백엔드에서 PortOne SDK 초기화 (테스트 키)
* [ ] 결제 라우터

  * [ ] `routers/payments.py` – `POST /payments/charge`

    * [ ] imp_uid / amount 받아서 PortOne로 검증
    * [ ] 성공 시 `transactions` 기록 + `users.credits` 증가
* [ ] run 생성 시 크레딧 차감

  * [ ] `POST /runs`에서:

    * [ ] 현재 유저의 `credits` 확인
    * [ ] 부족하면 에러 반환
    * [ ] 충분하면 `deduct_credits` 호출, run 생성 진행
* [ ] 프론트와 연동 (최소 버전)

  * [ ] 포트원 JS SDK로 결제 버튼 하나 붙이기
  * [ ] 결제 완료 후 imp_uid를 백엔드에 POST

---

## 6. 커뮤니티 & 라이브러리 (여유 생기면)

**목표: “내 작품함 + 커뮤니티 피드”까지 한 번에 경험해보기**

* [ ] `galleries` 테이블 / 모델 구현

  * [ ] `GET /gallery` – 내 작품 목록
  * [ ] `POST /gallery/{run_id}` – 즐겨찾기/폴더 지정
* [ ] `community_posts`, `likes`, `comments` 테이블 / 모델 구현

  * [ ] `GET /community` – 게시글 리스트
  * [ ] `POST /community` – 영상(run) 기반 게시글 작성
  * [ ] `POST /community/{id}/like` – 좋아요 토글
  * [ ] `POST /community/{id}/comments` – 댓글 작성

---

## 7. 마지막 다듬기 (선택)

* [ ] CORS 설정 (프론트 도메인만 허용)
* [ ] Rate limiting(슬로우API/Redis)으로 `/runs` 남발 방지
* [ ] 최소 수준의 로깅/에러 핸들링 추가
* [ ] README에 전체 아키텍처, 실행 방법 정리

---

이 체크리스트 그대로 쓰고 싶으면,
다음에 내가 **단계 1~2용 최소 프로젝트 스캐폴딩 코드** 한 번에 뽑아줄게.
그거 기준으로 “✔ 하나씩 지워가기 모드”로 진행하면 좋을 듯.
