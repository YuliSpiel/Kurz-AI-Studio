# Kurz Studio AI 빠른 시작 가이드

## 빠르게 시작하기

> **Windows 사용자**: 상세한 Windows 설정 가이드는 [WINDOWS_SETUP.md](WINDOWS_SETUP.md)를 참조하세요.

### 1. 환경 설정

**Windows:**
```cmd
copy .env.example .env
```

**Linux/Mac:**
```bash
cp .env.example .env
```

`.env` 파일을 열고 필수 API 키 설정:
```bash
# OpenAI API (필수 - 스토리 생성용)
OPENAI_API_KEY=sk-proj-your_key_here

# Gemini API (권장 - 이미지 생성용, $0.039/이미지)
GEMINI_API_KEY=your_gemini_key_here

# ElevenLabs API (권장 - 음성/음악 생성용, $5/월~)
ELEVENLABS_API_KEY=sk_your_key_here

# Provider 설정 (기본값)
IMAGE_PROVIDER=gemini
TTS_PROVIDER=elevenlabs
MUSIC_PROVIDER=elevenlabs
```

> **참고**:
> - IMAGE_PROVIDER를 `gemini` (권장) 또는 `comfyui` (로컬, 무료)로 설정 가능
> - ElevenLabs API 키 설정 가이드는 [ELEVENLABS_FIX.md](ELEVENLABS_FIX.md) 참조

### 2. 백엔드 실행 (3개 터미널)

**터미널 1: Redis**
```bash
cd backend
docker-compose up -d redis
```

**터미널 2: Python 가상환경 및 의존성 설치 (최초 1회)**

**Windows (PowerShell):**
```powershell
cd backend
python -m venv kvenv
kvenv\Scripts\activate
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
cd backend
python -m venv kvenv
source kvenv/bin/activate
pip install -r requirements.txt
```

**터미널 2: Celery Worker**

**Windows:**
```cmd
cd backend
kvenv\Scripts\activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Linux/Mac:**
```bash
cd backend
source kvenv/bin/activate
celery -A app.celery_app worker --loglevel=info --pool=gevent --concurrency=10
```

**터미널 3: FastAPI**

**Windows:**
```cmd
cd backend
kvenv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

**Linux/Mac:**
```bash
cd backend
source kvenv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. 프론트엔드 실행

```bash
cd frontend
npm install  # 또는 pnpm install
npm run dev
```

브라우저에서 http://localhost:5173 접속

### 4. 이미지 생성 옵션

**옵션 1: Gemini API (권장)**
- `.env`에서 `IMAGE_PROVIDER=gemini` 설정
- `GEMINI_API_KEY` 입력
- 별도 설치 불필요, 클라우드 기반

**옵션 2: ComfyUI (로컬, 무료)**
- `.env`에서 `IMAGE_PROVIDER=comfyui` 설정
- ComfyUI를 별도로 실행 (별도 설치 필요)

**Windows:**
```cmd
cd C:\path\to\ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

**Linux/Mac:**
```bash
cd /path/to/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

### 5. 첫 영상 생성

1. 브라우저에서 http://localhost:5173 접속

2. 프론트엔드에서 입력:
   - **프롬프트**: "우주를 여행하는 고양이의 모험"
   - **컷 수**: 3-5개 (권장)
   - **스타일**: 기본 또는 원하는 스타일 선택

3. **"영상 생성 시작"** 버튼 클릭

4. 진행 상황 실시간 모니터링
   - 스토리 생성 → 이미지 생성 → 음성 생성 → 영상 합성

5. 완료 후 영상 재생/다운로드

## 테스트

### 간단한 모듈 테스트

**Windows:**
```cmd
cd backend
kvenv\Scripts\activate
python ..\test_tts_simple.py
python ..\verify_api_key.py
```

**Linux/Mac:**
```bash
cd backend
source kvenv/bin/activate
python ../test_tts_simple.py
python ../verify_api_key.py
```

## 문제 해결

### Redis 연결 안 됨
```bash
docker ps  # Redis 확인
docker-compose restart redis
```

> **Windows 사용자**: Docker Desktop이 실행 중인지 확인하세요.

### Celery worker 에러

**Windows:**
```cmd
cd backend
kvenv\Scripts\activate
celery -A app.celery_app worker --loglevel=debug --pool=solo
```

**Linux/Mac:**
```bash
cd backend
source kvenv/bin/activate
celery -A app.celery_app worker --loglevel=debug --pool=gevent --concurrency=10
```

### 이미지 생성 문제
- **Gemini 사용 시**: `GEMINI_API_KEY`가 올바르게 설정되었는지 확인
- **ComfyUI 사용 시**: ComfyUI가 http://localhost:8188 에서 실행 중인지 확인

### ElevenLabs API 에러
자세한 트러블슈팅은 [ELEVENLABS_FIX.md](ELEVENLABS_FIX.md) 참조

### FFmpeg 없음 에러
영상 생성 시 `FileNotFoundError` 발생:
```bash
ffmpeg -version  # 설치 확인
```
설치되지 않았다면 위의 [시스템 요구사항](#시스템-요구사항) 섹션 참조

### Windows 환경 문제
상세한 Windows 설정 가이드는 [WINDOWS_SETUP.md](WINDOWS_SETUP.md) 참조

## 시스템 요구사항

### 필수 프로그램
- **Python**: 3.10 이상
- **Node.js**: 18 이상
- **Docker**: Docker Desktop (Windows/Mac) 또는 Docker Engine (Linux)
- **FFmpeg**: 영상 처리용 (필수)
- **ImageMagick**: 텍스트 렌더링용 (필수)

### 하드웨어
- **메모리**: 최소 8GB RAM 권장
- **저장 공간**: 최소 5GB 여유 공간

### FFmpeg 설치

**Windows:**
1. [FFmpeg 다운로드](https://www.gyan.dev/ffmpeg/builds/) - essentials 버전
2. 압축 해제 후 `bin` 폴더를 PATH에 추가
3. 또는 Chocolatey: `choco install ffmpeg`

**Mac:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**설치 확인:**
```bash
ffmpeg -version
```

### ImageMagick 설치 (필수)

영상에 텍스트를 렌더링하기 위해 필수:

**Windows:**
1. [ImageMagick 다운로드](https://imagemagick.org/script/download.php#windows)
2. 설치 시 **"Install legacy utilities (e.g. convert)"** 반드시 체크
3. 설치 후 PC 재시작 권장
4. 환경 변수 설정:
   ```cmd
   setx IMAGEMAGICK_BINARY "C:\Program Files\ImageMagick-7.x.x-Q16-HDRI\magick.exe"
   ```

**Mac:**
```bash
brew install imagemagick
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install imagemagick
```

**설치 확인:**
```bash
magick -version
convert -version
```

> **중요**: Windows에서는 "Install legacy utilities" 옵션을 반드시 체크해야 MoviePy가 정상 작동합니다.

## 다음 단계

- [Windows 설정 가이드](WINDOWS_SETUP.md) - Windows 전용 상세 가이드
- [상세 README](README.md) - 프로젝트 전체 설명
- [ElevenLabs 설정](ELEVENLABS_FIX.md) - API 키 및 문제 해결
