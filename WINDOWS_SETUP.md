# Windows 환경 설정 가이드

Kurz Studio AI를 Windows에서 실행하기 위한 상세 가이드입니다.

## 목차
1. [필수 프로그램 설치](#1-필수-프로그램-설치)
2. [프로젝트 설정](#2-프로젝트-설정)
3. [백엔드 설정](#3-백엔드-설정)
4. [프론트엔드 설정](#4-프론트엔드-설정)
5. [실행 방법](#5-실행-방법)
6. [문제 해결](#6-문제-해결)

---

## 1. 필수 프로그램 설치

### 1.1 Python 설치

1. [Python 공식 사이트](https://www.python.org/downloads/)에서 **Python 3.10 이상** 다운로드
2. 설치 시 **"Add Python to PATH"** 체크 필수
3. 설치 확인:
   ```cmd
   python --version
   ```
   출력 예시: `Python 3.11.x`

### 1.2 Node.js 설치

1. [Node.js 공식 사이트](https://nodejs.org/)에서 **LTS 버전 (18 이상)** 다운로드
2. 기본 설정으로 설치
3. 설치 확인:
   ```cmd
   node --version
   npm --version
   ```

### 1.3 Docker Desktop 설치

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드
2. 설치 후 Docker Desktop 실행
3. Docker Desktop이 실행 중인지 확인 (시스템 트레이에 Docker 아이콘)
4. 설치 확인:
   ```cmd
   docker --version
   docker-compose --version
   ```

> **중요**: WSL 2를 사용하는 경우, Docker Desktop 설정에서 "Use WSL 2 based engine"이 활성화되어 있어야 합니다.

### 1.4 Git 설치 (선택)

1. [Git for Windows](https://git-scm.com/download/win) 다운로드
2. 기본 설정으로 설치

### 1.5 FFmpeg 설치 (필수 - 영상 처리)

**방법 1: 수동 설치 (권장)**

1. [FFmpeg 다운로드](https://www.gyan.dev/ffmpeg/builds/) - **ffmpeg-release-essentials.zip** 다운로드
2. 압축 해제 (예: `C:\ffmpeg`)
3. 환경 변수 PATH에 추가:
   - `Win + R` → `sysdm.cpl` 엔터
   - "고급" 탭 → "환경 변수" 버튼
   - "시스템 변수"에서 `Path` 선택 → "편집"
   - "새로 만들기" → `C:\ffmpeg\bin` 입력
   - 확인 → PC 재시작

4. 설치 확인:
   ```cmd
   ffmpeg -version
   ```

**방법 2: Chocolatey 사용**

```cmd
choco install ffmpeg
```

> **참고**: FFmpeg는 MoviePy가 영상 인코딩에 필수적으로 사용하는 외부 프로그램입니다.

### 1.6 ImageMagick 설치 (필수 - 텍스트 렌더링)

**방법 1: 수동 설치 (권장)**

1. [ImageMagick 다운로드](https://imagemagick.org/script/download.php#windows)
2. **Windows 64-bit 버전** 다운로드 (ImageMagick-7.x.x-Q16-HDRI-x64-dll.exe)
3. 설치 시 **반드시 체크할 항목**:
   - ✅ **"Install legacy utilities (e.g. convert)"** - 필수!
   - ✅ "Add application directory to your system path" - 권장
4. 설치 완료 후 PC 재시작 (권장)
5. 설치 확인:
   ```cmd
   magick -version
   convert -version
   ```

**방법 2: Chocolatey 사용**

```cmd
choco install imagemagick
```

> **중요**: ImageMagick은 MoviePy가 영상에 텍스트를 렌더링할 때 필수적으로 사용하는 외부 프로그램입니다. "Install legacy utilities" 옵션을 반드시 체크해야 합니다!

### 1.7 MoviePy ImageMagick 설정 (필수)

ImageMagick 설치 후 MoviePy가 인식하도록 설정:

**방법 1: 환경 변수 설정**

```cmd
setx IMAGEMAGICK_BINARY "C:\Program Files\ImageMagick-7.x.x-Q16-HDRI\magick.exe"
```

**방법 2: moviepy 설정 파일 수정**

Python에서 직접 설정:
```python
# backend/app/config.py 또는 초기화 파일에 추가
import os
os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe'
```

> **참고**: ImageMagick 버전에 따라 경로가 다를 수 있습니다. `C:\Program Files\ImageMagick-*` 폴더를 확인하세요.

---

## 2. 프로젝트 설정

### 2.1 프로젝트 다운로드

```cmd
git clone https://github.com/your-repo/Kurz_Studio_AI.git
cd Kurz_Studio_AI
```

또는 ZIP 파일로 다운로드 후 압축 해제

### 2.2 환경 변수 파일 생성

```cmd
copy .env.example .env
```

### 2.3 `.env` 파일 편집

메모장이나 VS Code로 `.env` 파일을 열고 API 키 입력:

```bash
# 필수 - OpenAI API 키
OPENAI_API_KEY=sk-proj-your_openai_key_here

# 권장 - Gemini API 키 (이미지 생성용)
GEMINI_API_KEY=your_gemini_key_here

# 권장 - ElevenLabs API 키 (음성/음악 생성용)
ELEVENLABS_API_KEY=sk_your_elevenlabs_key_here

# Provider 설정
IMAGE_PROVIDER=gemini
TTS_PROVIDER=elevenlabs
MUSIC_PROVIDER=elevenlabs
```

#### API 키 발급 방법:

- **OpenAI**: https://platform.openai.com/api-keys
- **Gemini**: https://aistudio.google.com/app/apikey
- **ElevenLabs**: https://elevenlabs.io/app/settings/api-keys

---

## 3. 백엔드 설정

### 3.1 Redis 실행

**PowerShell 또는 CMD를 관리자 권한으로 실행:**

```cmd
cd backend
docker-compose up -d redis
```

Redis가 실행 중인지 확인:
```cmd
docker ps
```

`redis` 컨테이너가 목록에 보여야 합니다.

### 3.2 Python 가상환경 생성

```cmd
cd backend
python -m venv kvenv
```

### 3.3 가상환경 활성화

**PowerShell:**
```powershell
kvenv\Scripts\Activate.ps1
```

**CMD:**
```cmd
kvenv\Scripts\activate
```

> **PowerShell 실행 정책 오류 시:**
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3.4 Python 패키지 설치

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

설치가 완료되면 다음 명령어로 확인:
```cmd
pip list
```

---

## 4. 프론트엔드 설정

### 4.1 의존성 설치

**새 터미널(CMD 또는 PowerShell) 열기:**

```cmd
cd frontend
npm install
```

또는 pnpm 사용:
```cmd
npm install -g pnpm
pnpm install
```

---

## 5. 실행 방법

### 5.1 터미널 3개 준비

총 3개의 터미널(CMD 또는 PowerShell)이 필요합니다:

#### 터미널 1: Redis (이미 실행 중이면 생략)

```cmd
cd backend
docker-compose up -d redis
```

#### 터미널 2: Celery Worker

```cmd
cd backend
kvenv\Scripts\activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```

> **중요**: Windows에서는 `--pool=solo` 옵션이 필수입니다.

#### 터미널 3: FastAPI 서버

```cmd
cd backend
kvenv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

서버가 실행되면:
- API: http://localhost:8080
- API 문서: http://localhost:8080/docs

### 5.2 프론트엔드 실행

**새 터미널(4번째) 열기:**

```cmd
cd frontend
npm run dev
```

브라우저에서 http://localhost:5173 접속

---

## 6. 문제 해결

### 6.1 Python 가상환경 활성화 오류

**PowerShell에서 스크립트 실행 정책 오류:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**또는 CMD 사용:**
```cmd
kvenv\Scripts\activate.bat
```

### 6.2 Docker 연결 오류

1. Docker Desktop이 실행 중인지 확인
2. Docker Desktop 설정:
   - Settings → General → "Use WSL 2 based engine" 체크
   - Settings → Resources → WSL Integration에서 사용 중인 WSL 배포판 선택

3. Redis 재시작:
   ```cmd
   cd backend
   docker-compose down
   docker-compose up -d redis
   ```

### 6.3 Celery Worker 오류

**Windows에서 Celery 실행 시 반드시 `--pool=solo` 옵션 사용:**
```cmd
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**더 자세한 로그 보기:**
```cmd
celery -A app.celery_app worker --loglevel=debug --pool=solo
```

### 6.4 포트 충돌 오류

다른 프로그램이 포트를 사용 중인 경우:

**사용 중인 포트 확인:**
```cmd
netstat -ano | findstr :8080
netstat -ano | findstr :5173
netstat -ano | findstr :6379
```

**프로세스 종료:**
```cmd
taskkill /PID <프로세스_ID> /F
```

### 6.5 FFmpeg 관련 오류

**증상**: `FileNotFoundError: [WinError 2] The system cannot find the file specified` (영상 생성 시)

**해결책**:
1. FFmpeg가 설치되어 있는지 확인:
   ```cmd
   ffmpeg -version
   ```

2. 설치되지 않았다면 [1.5 FFmpeg 설치](#15-ffmpeg-설치-필수---영상-처리) 참조

3. PATH 설정 확인:
   ```cmd
   echo %PATH%
   ```
   출력에 `C:\ffmpeg\bin` (또는 설치한 경로) 포함되어야 함

4. 설치 후 **PC 재시작** 필수 (PATH 적용)

5. VS Code 사용 중이라면 VS Code도 재시작

### 6.5.1 PATH 수동 설정 방법 (상세)

FFmpeg를 `C:\ffmpeg`에 압축 해제했다고 가정:

**단계별 설명:**

1. **시스템 속성 열기**
   - `Win + R` 눌러서 실행 창 열기
   - `sysdm.cpl` 입력 후 엔터

2. **환경 변수 창 열기**
   - "고급" 탭 클릭
   - 하단의 "환경 변수" 버튼 클릭

3. **시스템 변수 편집**
   - 아래쪽 "시스템 변수" 섹션에서 `Path` 찾기
   - `Path` 선택 후 "편집" 버튼 클릭

4. **새 경로 추가**
   - "새로 만들기" 버튼 클릭
   - `C:\ffmpeg\bin` 입력 (bin 폴더까지 포함!)
   - 확인 버튼 클릭

5. **모든 창 닫기**
   - 확인 → 확인 → 확인 (3번)

6. **PC 재시작** (필수!)

7. **확인**
   - 새 CMD 창 열기
   - `ffmpeg -version` 실행

### 6.6 ImageMagick 관련 오류

**증상 1**: `OSError: MoviePy Error: creation of None failed because of the following error`

**증상 2**: 텍스트가 영상에 표시되지 않음

**해결책**:

1. ImageMagick 설치 확인:
   ```cmd
   magick -version
   convert -version
   ```

2. legacy utilities 설치 확인:
   - `convert -version`이 동작하지 않으면 재설치 필요
   - 재설치 시 **"Install legacy utilities"** 반드시 체크

3. 환경 변수 설정:
   ```cmd
   setx IMAGEMAGICK_BINARY "C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
   ```
   (버전에 맞게 경로 수정)

4. ImageMagick 설치 경로 확인:
   ```cmd
   dir "C:\Program Files\ImageMagick*" /s /b | findstr magick.exe
   ```

5. PC 재시작 후 재테스트

### 6.7 파일 경로 오류

Windows에서는 경로 구분자가 백슬래시(`\`)입니다:
```cmd
# 올바른 경로
cd C:\Users\Jiyun\Documents\GitHub\Kurz_Studio_AI

# 또는 슬래시도 사용 가능
cd C:/Users/Jiyun/Documents/GitHub/Kurz_Studio_AI
```

### 6.7 한글 경로 문제

프로젝트 경로에 한글이 포함되어 있으면 문제가 발생할 수 있습니다. 영문 경로로 이동하는 것을 권장합니다.

---

## 7. 테스트

### 7.1 API 키 검증

```cmd
cd backend
kvenv\Scripts\activate
python ..\verify_api_key.py
```

### 7.2 ElevenLabs TTS 테스트

```cmd
cd backend
kvenv\Scripts\activate
python ..\test_tts_simple.py
```

### 7.3 전체 시스템 테스트

1. 백엔드 3개 터미널 모두 실행 중인지 확인
2. 프론트엔드 실행
3. 브라우저에서 http://localhost:5173 접속
4. 간단한 프롬프트 입력:
   - 프롬프트: "고양이가 우주를 여행하는 이야기"
   - 컷 수: 3
5. 생성 시작 버튼 클릭
6. 진행 상황 모니터링

---

## 8. 개발 환경 권장 사항

### 8.1 추천 IDE

- **VS Code**: https://code.visualstudio.com/
  - 확장: Python, Pylance, ESLint, Prettier

### 8.2 추천 터미널

- **Windows Terminal**: Microsoft Store에서 설치
- PowerShell 7: https://github.com/PowerShell/PowerShell/releases

### 8.3 유용한 도구

- **Postman**: API 테스트용
- **Docker Desktop**: 컨테이너 관리 GUI
- **Git Bash**: Unix 스타일 명령어 사용

---

## 9. 자동 실행 스크립트 (선택)

### 9.1 백엔드 자동 실행 스크립트

`backend/start_backend.bat` 파일 생성:

```batch
@echo off
echo Starting Kurz Studio AI Backend...

echo.
echo [1/3] Starting Redis...
docker-compose up -d redis

echo.
echo [2/3] Starting Celery Worker...
start cmd /k "kvenv\Scripts\activate && celery -A app.celery_app worker --loglevel=info --pool=solo"

echo.
echo [3/3] Starting FastAPI Server...
timeout /t 3 /nobreak > nul
start cmd /k "kvenv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"

echo.
echo Backend services started!
echo API: http://localhost:8080
echo Docs: http://localhost:8080/docs
pause
```

실행:
```cmd
cd backend
start_backend.bat
```

### 9.2 전체 시스템 자동 실행 스크립트

프로젝트 루트에 `start_all.bat` 파일 생성:

```batch
@echo off
echo Starting Kurz Studio AI...

echo.
echo [Backend] Starting services...
cd backend
start cmd /k "docker-compose up -d redis && timeout /t 2 /nobreak > nul && kvenv\Scripts\activate && celery -A app.celery_app worker --loglevel=info --pool=solo"
start cmd /k "timeout /t 5 /nobreak > nul && kvenv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"

echo.
echo [Frontend] Starting dev server...
cd ..\frontend
timeout /t 8 /nobreak > nul
start cmd /k "npm run dev"

echo.
echo All services started!
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8080
pause
```

---

## 10. 다음 단계

- [QUICKSTART.md](QUICKSTART.md) - 빠른 시작 가이드
- [ELEVENLABS_FIX.md](ELEVENLABS_FIX.md) - ElevenLabs API 설정
- [README.md](README.md) - 프로젝트 전체 설명

---

## 11. 추가 지원

문제가 해결되지 않으면:
1. GitHub Issues에 문의
2. 로그 파일 첨부 (backend/logs/)
3. 에러 메시지 전체 복사

**Windows 환경 정보 수집:**
```cmd
systeminfo
python --version
node --version
docker --version
```
