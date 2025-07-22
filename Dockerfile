FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 브라우저 설치
RUN playwright install chromium

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY config/ ./config/

# 로그 디렉토리 생성
RUN mkdir -p logs

# 실행 사용자 생성 (보안을 위해)
RUN useradd -m -u 1000 qok6user
USER qok6user

# 메인 스크립트 실행
CMD ["python", "-m", "src.main"]