# QOK6 자동화 시스템 설정 가이드

## 실행하기 전에 필요한 설정

### 1. 환경 변수 파일 생성 (.env)
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

```bash
# 네이버 계정 정보
NAVER_ID=stresspoon
NAVER_PASSWORD=LI7985600!)

# 네이버 카페 정보  
CAFE_URL=https://cafe.naver.com/westudyssat
BOARD_ID=180
CRAWL_PAGES=3

# 구글 시트 정보
GOOGLE_SHEET_ID=1EEKpb0PDWHnlJanc2rs136wVP9SwA7JOd8UImn52PYw
GOOGLE_CREDENTIALS_PATH=data/credentials.json

# 스케줄링 설정
EXECUTION_TIME=00:00
TIMEZONE=Asia/Seoul

# 알림 설정 (선택사항)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
NOTIFICATION_RECIPIENTS=

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/qok6.log

# 암호화 키 (자동 생성됨)
ENCRYPTION_KEY=
```

### 2. Google API 인증 파일 설정
- `autocafe-466304-5dff2bd3ac29.json` 파일을 `data/credentials.json`으로 이름을 변경하여 저장하세요.

### 3. 실행 방법

#### 의존성 설치
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### 웹 서버 실행
```bash
python run_web_server.py
```

또는

```bash
python -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

#### API 사용법
- 웹 인터페이스: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 수동 실행: POST http://localhost:8000/run
- 실행 로그 조회: GET http://localhost:8000/logs
- 시스템 상태: GET http://localhost:8000/status

### 4. 참고사항
- 모든 설정 파일(.env, credentials.json)은 로컬에서만 관리되며 GitHub에는 업로드되지 않습니다.
- 처음 실행 시 Chrome 브라우저가 자동으로 실행됩니다 (Playwright 사용).
- 로그는 `logs/` 폴더에 저장됩니다.