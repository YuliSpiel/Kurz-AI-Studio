# Kurz AI Studio - AWS Lightsail 배포 가이드

## 1. Lightsail 인스턴스 생성

### 1.1 인스턴스 선택
1. [AWS Lightsail Console](https://lightsail.aws.amazon.com) 접속
2. "Create instance" 클릭
3. 설정:
   - **Region**: Seoul (ap-northeast-2)
   - **Platform**: Linux/Unix
   - **Blueprint**: OS Only → Ubuntu 22.04 LTS
   - **Instance plan**: $20/월 (4GB RAM, 2 vCPU, 80GB SSD) 권장
   - **Instance name**: kurz-studio

### 1.2 Static IP 연결
1. "Networking" 탭 → "Create static IP"
2. 인스턴스에 연결

### 1.3 Firewall 설정
| Port | Protocol | Description |
|------|----------|-------------|
| 22   | TCP      | SSH         |
| 80   | TCP      | HTTP        |
| 443  | TCP      | HTTPS       |

---

## 2. 서버 초기 설정

### 2.1 SSH 접속
```bash
ssh -i ~/.ssh/LightsailDefaultKey-ap-northeast-2.pem ubuntu@YOUR_STATIC_IP
```

### 2.2 Docker 설치
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add user to docker group
sudo usermod -aG docker ubuntu
newgrp docker

# Verify installation
docker --version
docker compose version
```

### 2.3 프로젝트 클론
```bash
git clone https://github.com/YOUR_USERNAME/Kurz_Studio_AI.git
cd Kurz_Studio_AI
```

---

## 3. 환경 변수 설정

```bash
# Copy example env file
cp .env.production.example .env

# Edit with your values
nano .env
```

**필수 설정:**
```env
POSTGRES_PASSWORD=your_secure_db_password
JWT_SECRET=your_jwt_secret_32_chars
GEMINI_API_KEY=your_gemini_key
ELEVENLABS_API_KEY=your_elevenlabs_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/google/callback
FRONTEND_ORIGIN=https://yourdomain.com
```

---

## 4. 도메인 & SSL 설정

### 4.1 도메인 연결
1. DNS 설정에서 A 레코드 추가:
   - Type: A
   - Name: @ (또는 서브도메인)
   - Value: YOUR_STATIC_IP

### 4.2 SSL 인증서 (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot -y

# Get certificate (standalone mode)
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chmod 644 ssl/*.pem
```

### 4.3 Nginx SSL 설정
`frontend/nginx.conf` 수정:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... rest of config
}
```

---

## 5. 배포 실행

### 5.1 첫 배포
```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5.2 데이터베이스 마이그레이션
```bash
# Run migrations
docker compose exec backend alembic upgrade head
```

### 5.3 상태 확인
```bash
# Check all services
docker compose ps

# Backend health
curl http://localhost:8080/health

# View logs
docker compose logs backend
docker compose logs celery
```

---

## 6. 업데이트 배포

코드 수정 후:
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build

# Run migrations if needed
docker compose exec backend alembic upgrade head
```

---

## 7. 유지보수

### 7.1 로그 확인
```bash
# All logs
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery
```

### 7.2 데이터 백업
```bash
# Database backup
docker compose exec postgres pg_dump -U kurz kurz_db > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker compose exec -T postgres psql -U kurz kurz_db
```

### 7.3 디스크 정리
```bash
# Remove old Docker images
docker system prune -a

# Remove old video outputs (30일 이상)
find /var/lib/docker/volumes/kurz_outputs_data/_data -mtime +30 -delete
```

### 7.4 SSL 인증서 갱신
```bash
# Auto-renew (add to crontab)
0 0 1 * * certbot renew --quiet && docker compose restart frontend
```

---

## 8. 트러블슈팅

### 8.1 서비스 재시작
```bash
docker compose restart backend
docker compose restart celery
```

### 8.2 컨테이너 쉘 접속
```bash
docker compose exec backend bash
docker compose exec postgres psql -U kurz kurz_db
```

### 8.3 일반적인 문제

**1. 메모리 부족**
```bash
# Check memory
free -h

# Reduce Celery concurrency in docker-compose.yml
command: celery -A app.celery_app worker --pool=gevent --concurrency=5
```

**2. 영상 렌더링 실패**
```bash
# Check celery logs
docker compose logs celery | grep -i error

# Verify FFmpeg
docker compose exec celery ffmpeg -version
```

**3. Database connection error**
```bash
# Restart postgres
docker compose restart postgres

# Check connection
docker compose exec backend python -c "from app.database import engine; print('OK')"
```

---

## 9. 비용 예상

| 항목 | 월 비용 |
|------|--------|
| Lightsail 4GB | $20 |
| 도메인 (연간/12) | ~$1 |
| **총합** | **~$21/월** |

외부 API 비용 (사용량에 따라):
- Gemini API: 무료 티어 → 유료시 사용량 기반
- ElevenLabs: $5~22/월 (구독)

---

## 10. GCP Console 설정

### Google OAuth 설정
1. [GCP Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. OAuth 2.0 Client ID 생성/수정
3. Authorized redirect URIs 추가:
   - `https://yourdomain.com/api/auth/google/callback`
   - `https://yourdomain.com/api/youtube/callback`

### YouTube API 활성화 (공유 기능용)
1. GCP Console → APIs & Services → Library
2. "YouTube Data API v3" 검색 → Enable
