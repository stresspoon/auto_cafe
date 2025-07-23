# QOK6 자동화 서비스 Docker 이미지
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="QOK6 Automation Team"
LABEL description="네이버 카페 챌린지 미션을 구글 시트에 자동으로 체크하는 서비스"
LABEL version="1.0.0"

# 시스템 패키지 설치 및 업데이트
RUN apt-get update && apt-get install -y \
    # 기본 도구
    wget \
    curl \
    gnupg \
    unzip \
    # Playwright 의존성 라이브러리
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libatspi2.0-0 \
    libxrandr2 \
    libasound2 \
    libxss1 \
    libgbm1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    # 가상 디스플레이 (헤드리스 환경)
    xvfb \
    # 폰트 (한글 지원)
    fonts-nanum \
    fonts-nanum-coding \
    fonts-nanum-extra \
    # 정리
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 비root 사용자 생성 (보안)
RUN useradd -m -u 1000 qok6user && \
    mkdir -p /app && \
    chown -R qok6user:qok6user /app

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 파일 복사 (캐시 최적화)
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN playwright install chromium && \
    playwright install-deps

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p logs data config && \
    chmod 755 logs data config

# 파일 권한 설정
RUN chown -R qok6user:qok6user /app && \
    chmod +x run_web_server.py

# 비root 사용자로 전환
USER qok6user

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/home/qok6user/.cache/ms-playwright

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/status || exit 1

# 포트 노출
EXPOSE 8001

# 실행 명령 (웹 서버 실행)
CMD ["python", "run_web_server.py"]