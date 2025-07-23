# QOK6 자동화 서비스 배포 가이드

> 네이버 카페 챌린지 미션을 구글 시트에 자동으로 체크하는 서비스

## 📋 목차

- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
  - [Windows 환경](#windows-환경)
  - [macOS 환경](#macos-환경)
  - [Linux 환경](#linux-환경)
  - [Docker 환경](#docker-환경)
- [설정 파일 구성](#설정-파일-구성)
- [실행 방법](#실행-방법)
- [보안 체크리스트](#보안-체크리스트)
- [트러블슈팅](#트러블슈팅)

## 🖥️ 시스템 요구사항

### 최소 요구사항
- **Python**: 3.10 이상
- **메모리**: 1GB RAM 이상
- **저장공간**: 500MB 이상
- **네트워크**: 인터넷 연결 (네이버, 구글 API 접근)
- **운영체제**: Windows 10, macOS 10.15, Ubuntu 20.04 이상

### 추천 사양
- **Python**: 3.11+
- **메모리**: 2GB RAM 이상
- **저장공간**: 1GB 이상
- **CPU**: 2코어 이상

## 📦 설치 방법

### Windows 환경

#### 1. Python 설치
```powershell
# Python 3.11 다운로드 및 설치
# https://www.python.org/downloads/windows/
# 설치 시 "Add Python to PATH" 체크 필수
```

#### 2. 프로젝트 다운로드 및 설정
```powershell
# PowerShell 관리자 권한으로 실행
git clone <repository-url>
cd auto_cafe

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

#### 3. 환경 설정
```powershell
# 설정 파일 복사
copy config\settings.ini.example config\settings.ini

# 설정 파일 편집 (메모장 또는 VS Code)
notepad config\settings.ini
```

### macOS 환경

#### 1. 필수 도구 설치
```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 설치
brew install python@3.11

# Git 설치 (없는 경우)
brew install git
```

#### 2. 프로젝트 설정
```bash
# 프로젝트 클론
git clone <repository-url>
cd auto_cafe

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

#### 3. 환경 설정
```bash
# 설정 파일 복사
cp config/settings.ini.example config/settings.ini

# 설정 파일 편집
nano config/settings.ini
# 또는
open -a TextEdit config/settings.ini
```

### Linux 환경 (Ubuntu/Debian)

#### 1. 시스템 패키지 설치
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# 추가 라이브러리 (Playwright 의존성)
sudo apt install -y libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libdrm2 libxkbcommon0 libgtk-3-0 libatspi2.0-0 libxrandr2 \
    libasound2 libxss1 libgbm1
```

#### 2. 프로젝트 설정
```bash
# 프로젝트 클론
git clone <repository-url>
cd auto_cafe

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### Docker 환경

#### 1. Dockerfile
```dockerfile
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 설치
RUN playwright install chromium
RUN playwright install-deps

# 애플리케이션 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# 포트 노출
EXPOSE 8001

# 실행 명령
CMD ["python", "run_web_server.py"]
```

#### 2. Docker Compose (선택사항)
```yaml
version: '3.8'

services:
  qok6-automation:
    build: .
    container_name: qok6-automation
    ports:
      - "8001:8001"
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
```

#### 3. Docker 실행
```bash
# 이미지 빌드
docker build -t qok6-automation .

# 컨테이너 실행
docker run -d \
  --name qok6-automation \
  -p 8001:8001 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  qok6-automation

# 또는 Docker Compose 사용
docker-compose up -d
```

## ⚙️ 설정 파일 구성

### 1. config/settings.ini
```ini
[NAVER]
# 네이버 계정 정보
NAVER_ID=your_naver_id
NAVER_PASSWORD=your_naver_password

# 카페 정보
CAFE_URL=https://cafe.naver.com/your_cafe_name
BOARD_ID=123
CRAWL_PAGES=3

[GOOGLE]
# 구글 시트 정보
CREDENTIALS_PATH=data/credentials.json
SHEET_ID=your_google_sheet_id

[LOGGING]
# 로그 설정
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/qok6.log

[EMAIL]
# 이메일 알림 설정 (선택사항)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
NOTIFICATION_RECIPIENTS=admin@example.com,manager@example.com
```

### 2. 구글 서비스 계정 키 (data/credentials.json)
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 선택
3. Google Sheets API 활성화
4. 서비스 계정 생성
5. JSON 키 다운로드 → `data/credentials.json`에 저장

### 3. 네이버 쿠키 파일 (data/naver_cookies.json)
```json
{
  "cookies": [
    {
      "name": "NID_AUT",
      "value": "your_cookie_value",
      "domain": ".naver.com"
    }
  ]
}
```

## 🚀 실행 방법

### 1. 웹 서버 실행
```bash
# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 웹 서버 시작
python run_web_server.py

# 브라우저에서 접속
# http://localhost:8001
```

### 2. 수동 실행 (CLI)
```bash
# 즉시 실행
python -m src.main --manual

# 스케줄 모드 (매일 00:00 대기)
python -m src.main
```

### 3. 자동 실행 (Cron 스케줄링)
웹 대시보드에서 "스케줄 설정" 버튼을 사용하거나:

```bash
# 수동 cron 설정
crontab -e

# 다음 라인 추가 (매일 00:00 실행)
0 0 * * * cd /path/to/auto_cafe && source venv/bin/activate && python -m src.main --manual >> logs/cron.log 2>&1
```

### 4. 서비스로 등록 (Linux)
```bash
# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/qok6-automation.service > /dev/null <<EOF
[Unit]
Description=QOK6 Automation Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/path/to/auto_cafe
Environment=PYTHONPATH=/path/to/auto_cafe
ExecStart=/path/to/auto_cafe/venv/bin/python run_web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화 및 시작
sudo systemctl enable qok6-automation
sudo systemctl start qok6-automation

# 상태 확인
sudo systemctl status qok6-automation
```

## 🔒 보안 체크리스트

### 필수 보안 조치

#### 1. 자격 증명 보안
- [ ] `config/settings.ini` 파일 권한 설정 (`chmod 600`)
- [ ] `data/credentials.json` 파일 권한 설정 (`chmod 600`)
- [ ] 환경 변수로 민감한 정보 관리 (선택사항)
- [ ] `.gitignore`에 설정 파일들 추가 확인

#### 2. 네트워크 보안
- [ ] 웹 서버는 내부 네트워크에서만 접근 가능하도록 설정
- [ ] 필요시 HTTPS 적용 (리버스 프록시 사용)
- [ ] 방화벽에서 필요한 포트만 개방 (8001)

#### 3. 시스템 보안
- [ ] 서비스 전용 사용자 계정 생성 (root 사용 금지)
- [ ] 로그 파일 접근 권한 제한
- [ ] 정기적인 의존성 업데이트

#### 4. 구글 서비스 계정 보안
- [ ] 서비스 계정에 최소 권한만 부여
- [ ] 구글 시트 공유 범위 제한
- [ ] API 키 정기 갱신

### 환경 변수 사용 (권장)
```bash
# .env 파일 생성
cat > .env << EOF
NAVER_ID=your_naver_id
NAVER_PASSWORD=your_naver_password
GOOGLE_SHEET_ID=your_sheet_id
EOF

# 권한 설정
chmod 600 .env
```

## 🔧 트러블슈팅

### 일반적인 문제

#### 1. Python 버전 오류
```
Error: Python 3.10+ required
```
**해결책:**
- Python 버전 확인: `python --version`
- Python 3.11 설치 후 가상환경 재생성

#### 2. 모듈 설치 오류
```
ERROR: Could not install packages due to an EnvironmentError
```
**해결책:**
```bash
# 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Playwright 브라우저 오류
```
Error: Browser executable not found
```
**해결책:**
```bash
# 브라우저 재설치
playwright install chromium
# 또는 모든 브라우저 설치
playwright install
```

### Windows 특화 문제

#### 1. 인코딩 오류
```
UnicodeDecodeError: 'cp949' codec can't decode
```
**해결책:**
```powershell
# PowerShell에서 UTF-8 설정
$env:PYTHONIOENCODING="utf-8"

# 또는 시스템 환경 변수 설정
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
```

#### 2. 경로 문제
```
FileNotFoundError: [WinError 2] The system cannot find the file
```
**해결책:**
- 절대 경로 사용
- 백슬래시를 슬래시로 변경 또는 raw string 사용

#### 3. 권한 문제
```
PermissionError: [WinError 5] Access is denied
```
**해결책:**
- PowerShell을 관리자 권한으로 실행
- Windows Defender 예외 설정 추가

### macOS 특화 문제

#### 1. Gatekeeper 문제
```
"Python" cannot be opened because the developer cannot be verified
```
**해결책:**
```bash
# Homebrew로 설치한 Python 사용
brew install python@3.11
```

#### 2. 권한 문제
```
Operation not permitted
```
**해결책:**
- 시스템 환경설정 → 보안 및 개인정보보호 → 개인정보 보호
- 터미널에 "풀 디스크 접근" 권한 부여

### Linux 특화 문제

#### 1. 의존성 누락
```
ImportError: libgobject-2.0.so.0: cannot open shared object file
```
**해결책:**
```bash
# Ubuntu/Debian
sudo apt install -y python3-dev libglib2.0-dev

# CentOS/RHEL
sudo yum install -y python3-devel glib2-devel
```

#### 2. 디스플레이 서버 문제
```
Error: Could not find display
```
**해결책:**
```bash
# 가상 디스플레이 설정
sudo apt install -y xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
```

### Docker 특화 문제

#### 1. 권한 문제
```
docker: permission denied
```
**해결책:**
```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
# 로그아웃 후 재로그인 필요
```

#### 2. 볼륨 마운트 문제
```
Error: cannot create directory
```
**해결책:**
```bash
# 호스트 디렉토리 권한 설정
chmod 755 ./config ./data ./logs

# SELinux 환경의 경우
sudo setsebool -P container_manage_cgroup on
```

### 네트워크 문제

#### 1. 네이버 로그인 실패
- 쿠키 파일 확인 및 업데이트
- 2단계 인증 설정 확인
- IP 차단 여부 확인 (VPN 사용 고려)

#### 2. 구글 API 오류
- 서비스 계정 키 파일 확인
- API 할당량 확인
- 방화벽 설정 확인

### 로그 분석

#### 로그 파일 위치
- 애플리케이션 로그: `logs/qok6.log`
- Cron 실행 로그: `logs/cron.log`
- 웹 서버 로그: `server.log`

#### 주요 오류 패턴
```bash
# 로그에서 오류 검색
grep -i error logs/qok6.log
grep -i exception logs/qok6.log

# 최근 로그 확인
tail -f logs/qok6.log
```

## 📞 지원 및 문의

문제가 해결되지 않을 경우:

1. 로그 파일 확인
2. GitHub Issues에 문의
3. 설정 파일 재확인
4. 환경 재구축 고려

## 📝 버전 히스토리

- **v1.0.0**: 초기 릴리스
- **v1.1.0**: 웹 UI 추가
- **v1.2.0**: Cron 스케줄링 추가
- **v1.3.0**: Docker 지원 추가