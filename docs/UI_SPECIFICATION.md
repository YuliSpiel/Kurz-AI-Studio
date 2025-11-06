# AutoShorts UI 기획서

**버전:** 1.0
**작성일:** 2025-11-05
**프로젝트:** Kurz Studio AI - AutoShorts

---

## 1. 개요

### 1.1 프로젝트 소개
AutoShorts는 AI 기반 스토리텔링형 숏폼 콘텐츠를 자동으로 제작하는 웹 애플리케이션입니다. 사용자는 간단한 프롬프트 입력만으로 스토리, 이미지, 음성, 배경음악이 포함된 완성된 숏츠 영상을 생성할 수 있습니다.

### 1.2 기술 스택
- **프론트엔드**: React 18.3 + TypeScript + Vite
- **UI 라이브러리**: Vanilla CSS (커스텀 디자인)
- **상태 관리**: React Hooks (useState)
- **통신**: REST API + WebSocket
- **빌드 도구**: Vite

### 1.3 주요 기능
1. 숏츠 생성 폼 (입력)
2. 실시간 진행 상황 모니터링
3. 결과 재생 및 다운로드

---

## 2. 애플리케이션 구조

### 2.1 전체 아키텍처
```
App.tsx (Root)
├── Header (헤더)
├── Main (메인 컨텐츠 영역)
│   ├── RunForm (생성 폼)
│   ├── RunStatus (진행 상황)
│   └── Player (결과 재생)
└── Footer (푸터)
```

### 2.2 컴포넌트 구성

#### 2.2.1 App.tsx
- **역할**: 최상위 컴포넌트, 전체 상태 관리
- **상태 관리**:
  - `currentRunId`: 현재 실행 중인 작업 ID
  - `completedRun`: 완료된 작업 데이터
- **화면 전환 로직**:
  1. 초기 상태: RunForm 표시
  2. 작업 생성: RunStatus 표시
  3. 작업 완료: Player 표시

#### 2.2.2 RunForm.tsx
- **역할**: 숏츠 생성 요청 폼
- **위치**: [frontend/src/components/RunForm.tsx](../frontend/src/components/RunForm.tsx)
- **입력 필드**:
  - 모드 (스토리텔링/광고)
  - 프롬프트 (필수)
  - 등장인물 수 (1-2명)
  - 컷 수 (1-10)
  - 화풍
  - 음악 장르
  - 참조 이미지 (선택)

#### 2.2.3 RunStatus.tsx
- **역할**: 실시간 진행 상황 표시
- **위치**: [frontend/src/components/RunStatus.tsx](../frontend/src/components/RunStatus.tsx)
- **표시 정보**:
  - Run ID
  - 현재 상태 (INIT, PLOT_PLANNING, ASSET_GENERATION, RENDERING, END, FAILED)
  - 진행률 (0-100%)
  - 실시간 로그
- **통신 방식**:
  - WebSocket: 실시간 업데이트
  - Polling (2초): WebSocket 보조

#### 2.2.4 Player.tsx
- **역할**: 완성된 숏츠 재생 및 다운로드
- **위치**: [frontend/src/components/Player.tsx](../frontend/src/components/Player.tsx)
- **표시 요소**:
  - 비디오 플레이어 (video 태그)
  - 다운로드 버튼
  - 생성된 이미지 썸네일 그리드
  - 메타데이터 (JSON 형식)

---

## 3. 화면 설계

### 3.1 화면 구성 흐름

```
[초기 화면: 생성 폼]
        ↓
    폼 제출
        ↓
[진행 상황 화면]
        ↓
    작업 완료
        ↓
[결과 재생 화면]
        ↓
   새로 만들기
        ↓
[초기 화면으로 복귀]
```

### 3.2 화면별 상세 설계

#### 3.2.1 헤더 (Header)
**파일**: [App.tsx:27-30](../frontend/src/App.tsx#L27-L30)

- **제목**: "AutoShorts"
- **부제**: "스토리텔링형 숏츠 자동 제작 시스템"
- **스타일**:
  - 가운데 정렬
  - 흰색 텍스트
  - 제목 폰트 크기: 3rem
  - 부제 폰트 크기: 1.2rem

#### 3.2.2 생성 폼 화면 (RunForm)
**파일**: [RunForm.tsx](../frontend/src/components/RunForm.tsx)

**레이아웃**:
- 최대 너비: 600px
- 중앙 정렬
- 흰색 배경 카드

**입력 필드 구성**:

1. **모드 선택** (select)
   - 옵션: 스토리텔링 / 광고
   - 기본값: 스토리텔링

2. **프롬프트** (textarea)
   - 4행 텍스트 영역
   - 필수 입력
   - 플레이스홀더: "예: 우주를 여행하는 고양이 이야기"

3. **등장인물 수** (select)
   - 옵션: 1명 / 2명
   - 기본값: 1명

4. **컷 수** (number input)
   - 범위: 1-10
   - 기본값: 3
   - 필수 입력

5. **화풍** (text input)
   - 기본값: "파스텔 수채화"
   - 플레이스홀더: "예: 파스텔 수채화, 애니메이션, 사실적"

6. **음악 장르** (text input)
   - 기본값: "ambient"
   - 플레이스홀더: "예: ambient, cinematic, upbeat"

7. **참조 이미지** (file input)
   - 다중 선택 가능
   - 이미지 파일만 허용
   - 선택된 파일 수 표시

**제출 버튼**:
- 전체 너비
- 그라데이션 배경 (보라색 계열)
- 텍스트: "숏츠 생성 시작" / "생성 중..."
- 프롬프트 미입력 시 비활성화

#### 3.2.3 진행 상황 화면 (RunStatus)
**파일**: [RunStatus.tsx](../frontend/src/components/RunStatus.tsx)

**레이아웃**:
- 최대 너비: 800px
- 중앙 정렬

**표시 요소**:

1. **상태 카드**
   - 배경색: #f9f9f9
   - 둥근 모서리
   - 표시 정보:
     - Run ID
     - 현재 상태 (색상 구분)
     - 진행률 (%)
     - 진행바 (그라데이션)

2. **상태별 색상**:
   - INIT, PLOT_PLANNING, ASSET_GENERATION, RENDERING: 파란색 (#667eea)
   - END: 녹색 (#28a745)
   - FAILED: 빨간색 (#dc3545)

3. **로그 영역**
   - 최대 높이: 300px
   - 스크롤 가능
   - 모노스페이스 폰트
   - 실시간 업데이트

4. **에러 메시지** (FAILED 상태 시)
   - 빨간색 배경
   - "생성 실패. 로그를 확인하세요."

#### 3.2.4 결과 재생 화면 (Player)
**파일**: [Player.tsx](../frontend/src/components/Player.tsx)

**레이아웃**:
- 최대 너비: 900px
- 중앙 정렬

**표시 요소**:

1. **성공 메시지**
   - "생성 완료!"
   - 녹색 (#28a745)

2. **비디오 플레이어**
   - HTML5 video 태그
   - 컨트롤 표시
   - 최대 너비: 100%
   - 최대 높이: 600px
   - 둥근 모서리 + 그림자

3. **다운로드 버튼**
   - 녹색 배경
   - 중앙 정렬
   - 텍스트: "다운로드"

4. **생성된 이미지 썸네일**
   - 그리드 레이아웃
   - 열 최소 너비: 200px
   - 자동 배치 (auto-fill)
   - 각 썸네일:
     - 이미지
     - 라벨 (scene_id - slot_id)

5. **메타데이터**
   - JSON 형식 표시
   - 코드 블록 스타일
   - 접을 수 있는 영역

6. **새로 만들기 버튼**
   - 보라색 배경 (#667eea)
   - 중앙 정렬
   - 클릭 시 초기 화면으로

#### 3.2.5 푸터 (Footer)
**파일**: [App.tsx:54-56](../frontend/src/App.tsx#L54-L56)

- **텍스트**: "Powered by FastAPI + Celery + ComfyUI + React"
- **스타일**:
  - 가운데 정렬
  - 흰색 텍스트
  - 투명도 0.8

---

## 4. 디자인 시스템

### 4.1 컬러 팔레트

#### 주요 색상
- **Primary**: #667eea (보라/파란)
- **Secondary**: #764ba2 (진한 보라)
- **Success**: #28a745 (녹색)
- **Danger**: #dc3545 (빨간색)
- **Background**: 그라데이션 (135deg, #667eea → #764ba2)

#### 텍스트 색상
- **Primary Text**: #333
- **Secondary Text**: #666
- **Light Text**: #fff

#### 배경 색상
- **Card Background**: #fff
- **Section Background**: #f9f9f9
- **Border**: #e0e0e0

### 4.2 타이포그래피

#### 폰트 패밀리
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
  Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
```

#### 폰트 크기
- **H1 (헤더 제목)**: 3rem
- **H2 (섹션 제목)**: 기본 + 굵게
- **H3 (소제목)**: 기본
- **Body**: 1rem
- **Small**: 0.9rem

### 4.3 간격 체계
- **기본 패딩**: 20px
- **카드 패딩**: 40px
- **폼 그룹 간격**: 20px
- **섹션 간격**: 30px

### 4.4 반응형 디자인
- **최대 너비**: 1200px (앱 전체)
- **폼 최대 너비**: 600px
- **진행 상황 최대 너비**: 800px
- **플레이어 최대 너비**: 900px

---

## 5. 상태 관리

### 5.1 애플리케이션 상태
**파일**: [App.tsx](../frontend/src/App.tsx)

```typescript
const [currentRunId, setCurrentRunId] = useState<string | null>(null)
const [completedRun, setCompletedRun] = useState<any>(null)
```

### 5.2 상태 전환 다이어그램

```
┌─────────────────────────────────────────────┐
│ 초기 상태                                    │
│ currentRunId: null, completedRun: null      │
└──────────────┬──────────────────────────────┘
               │ handleRunCreated(runId)
               ↓
┌─────────────────────────────────────────────┐
│ 진행 중                                      │
│ currentRunId: "xxx", completedRun: null     │
└──────────────┬──────────────────────────────┘
               │ handleRunCompleted(data)
               ↓
┌─────────────────────────────────────────────┐
│ 완료                                         │
│ currentRunId: null, completedRun: {...}     │
└──────────────┬──────────────────────────────┘
               │ handleReset()
               ↓
               (초기 상태로 복귀)
```

---

## 6. API 통신

### 6.1 API 클라이언트
**파일**: [client.ts](../frontend/src/api/client.ts)

#### 6.1.1 Run 생성
```typescript
POST /api/runs
Content-Type: application/json

Request Body: {
  mode: 'story' | 'ad',
  prompt: string,
  num_characters: 1 | 2,
  num_cuts: number,
  art_style: string,
  music_genre: string,
  reference_images?: string[],
  lora_strength?: number,
  voice_id?: string
}

Response: {
  run_id: string,
  state: string,
  progress: number,
  artifacts: {},
  logs: []
}
```

#### 6.1.2 Run 조회
```typescript
GET /api/runs/:runId

Response: {
  run_id: string,
  state: string,
  progress: number,
  artifacts: {
    video_url?: string,
    images?: Array<{
      scene_id: string,
      slot_id: string,
      image_url: string
    }>
  },
  logs: string[]
}
```

#### 6.1.3 이미지 업로드
```typescript
POST /api/uploads
Content-Type: multipart/form-data

Response: {
  filename: string
}
```

### 6.2 WebSocket 통신
**파일**: [RunStatus.tsx:18-77](../frontend/src/components/RunStatus.tsx#L18-L77)

#### 6.2.1 연결
```typescript
ws://[host]/ws/[runId]
```

#### 6.2.2 메시지 타입

**initial_state**:
```json
{
  "type": "initial_state",
  "run_id": "xxx",
  "state": "INIT",
  "progress": 0.0,
  "logs": []
}
```

**state_change**:
```json
{
  "type": "state_change",
  "message": "상태 변경 메시지"
}
```

**progress**:
```json
{
  "type": "progress",
  "progress": 0.5,
  "state": "ASSET_GENERATION",
  "message": "진행 메시지"
}
```

---

## 7. 사용자 흐름 (User Flow)

### 7.1 정상 흐름

1. **사용자가 앱 접속**
   - 헤더와 생성 폼 표시

2. **폼 작성**
   - 모드 선택 (스토리텔링/광고)
   - 프롬프트 입력 (필수)
   - 옵션 설정 (캐릭터 수, 컷 수, 화풍 등)
   - 참조 이미지 업로드 (선택)

3. **"숏츠 생성 시작" 버튼 클릭**
   - 참조 이미지가 있으면 먼저 업로드
   - Run 생성 API 호출
   - 진행 상황 화면으로 전환

4. **진행 상황 모니터링**
   - WebSocket 연결
   - 실시간 상태/진행률/로그 표시
   - 상태: INIT → PLOT_PLANNING → ASSET_GENERATION → RENDERING → END

5. **작업 완료**
   - 플레이어 화면으로 전환
   - 비디오 자동 로드
   - 썸네일 및 메타데이터 표시

6. **결과 확인**
   - 비디오 재생
   - 다운로드 버튼으로 저장
   - 생성된 이미지 확인

7. **"새로 만들기" 버튼 클릭**
   - 초기 화면으로 복귀

### 7.2 에러 흐름

1. **폼 제출 실패**
   - 에러 알림 표시
   - 폼 화면 유지

2. **작업 실패 (FAILED 상태)**
   - 진행 상황 화면에 에러 메시지 표시
   - 로그에서 상세 에러 확인 가능
   - 수동으로 "새로 만들기" 필요 (자동 복귀 없음)

---

## 8. 인터랙션 및 애니메이션

### 8.1 버튼 인터랙션

#### 제출 버튼
- **호버**: 위로 2px 이동 (`transform: translateY(-2px)`)
- **비활성화**: 투명도 0.6, 커서 not-allowed

#### 새로 만들기 버튼
- **호버**: 배경색 변경 (#667eea → #764ba2)

#### 다운로드 버튼
- **호버**: 배경색 변경 (#28a745 → #218838)

### 8.2 진행바 애니메이션
- **전환**: 너비 변화 0.5초 ease 애니메이션

### 8.3 입력 필드
- **포커스**: 테두리 색상 변경 (#e0e0e0 → #667eea), 0.3초 전환

---

## 9. 접근성 (Accessibility)

### 9.1 구현된 기능
- 시맨틱 HTML 태그 사용 (header, main, footer)
- 폼 레이블과 input 연결
- 비디오 플레이어 컨트롤 제공
- 버튼 disabled 상태 명확히 표시

### 9.2 개선 권장사항
- aria-label 추가
- 키보드 네비게이션 강화
- 스크린 리더 지원 강화
- 색상 대비 검증 (WCAG AA 기준)

---

## 10. 성능 최적화

### 10.1 구현된 최적화
- WebSocket을 통한 실시간 업데이트 (폴링 최소화)
- 조건부 렌더링 (화면별 컴포넌트 선택적 렌더)
- useEffect cleanup (WebSocket 연결 정리)

### 10.2 개선 권장사항
- 이미지 레이지 로딩
- 코드 스플리팅 (React.lazy)
- 메모이제이션 (React.memo, useMemo)
- 비디오 프리로딩 전략

---

## 11. 향후 개선 사항

### 11.1 기능 개선
1. **히스토리 기능**
   - 이전 생성 결과 목록 표시
   - 재생성/편집 기능

2. **고급 설정**
   - LoRA 강도 조절 UI
   - 음성 ID 선택
   - 씬별 개별 설정

3. **프리뷰 기능**
   - 생성 전 레이아웃 미리보기
   - 스토리 초안 확인

4. **공유 기능**
   - 소셜 미디어 공유
   - URL 공유

### 11.2 UX 개선
1. **진행 상황 개선**
   - 각 단계별 상세 진행률
   - 예상 소요 시간 표시

2. **에러 핸들링**
   - 구체적인 에러 메시지
   - 재시도 버튼

3. **반응형 디자인**
   - 모바일 최적화
   - 태블릿 레이아웃

### 11.3 기술 개선
1. **상태 관리**
   - Context API 또는 Zustand 도입
   - 전역 상태 관리 개선

2. **타입 안정성**
   - any 타입 제거
   - 엄격한 타입 정의

3. **테스트**
   - 단위 테스트 (Jest)
   - E2E 테스트 (Playwright)

---

## 12. 파일 구조

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API 클라이언트
│   ├── components/
│   │   ├── RunForm.tsx        # 생성 폼
│   │   ├── RunStatus.tsx      # 진행 상황
│   │   └── Player.tsx         # 결과 재생
│   ├── styles/
│   │   └── globals.css        # 전역 스타일
│   ├── App.tsx                # 메인 앱
│   └── main.tsx               # 엔트리 포인트
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 13. 참고 자료

### 13.1 주요 파일 링크
- [App.tsx](../frontend/src/App.tsx)
- [RunForm.tsx](../frontend/src/components/RunForm.tsx)
- [RunStatus.tsx](../frontend/src/components/RunStatus.tsx)
- [Player.tsx](../frontend/src/components/Player.tsx)
- [client.ts](../frontend/src/api/client.ts)
- [globals.css](../frontend/src/styles/globals.css)

### 13.2 백엔드 연동
- 백엔드 API: FastAPI
- 작업 큐: Celery
- 이미지 생성: ComfyUI / Gemini / Banana
- 음성 생성: ElevenLabs
- 배경음악: Suno

---

**문서 종료**
