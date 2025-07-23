# 🚀 QOK6 자동화 서비스 빠른 시작 가이드

> 5분 안에 시작하는 네이버 카페 → 구글 시트 자동화

## 📌 빠른 설치 (macOS/Linux)

```bash
# 1. 프로젝트 클론
git clone <repository-url> auto_cafe
cd auto_cafe

# 2. 가상환경 설정
python3 -m venv venv
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 4. 설정 파일 복사
cp config/settings.ini.example config/settings.ini
```

## ⚙️ 필수 설정

### 1. 네이버 계정 설정
`config/settings.ini` 편집:
```ini
[NAVER]
NAVER_ID=your_naver_id
NAVER_PASSWORD=your_password
CAFE_URL=https://cafe.naver.com/westudyssat
BOARD_ID=14
```

### 2. 구글 시트 설정

#### 구글 서비스 계정 키 생성:
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. "API 및 서비스" → "사용 설정" → "Google Sheets API" 검색 및 활성화
4. "사용자 인증 정보" → "서비스 계정 만들기"
5. JSON 키 다운로드 → `data/credentials.json`로 저장

#### settings.ini에 시트 ID 추가:
```ini
[GOOGLE]
SHEET_ID=your_google_sheet_id
```

### 3. 구글 시트 권한 설정
1. 구글 시트 열기
2. 우측 상단 "공유" 클릭
3. 서비스 계정 이메일 추가 (credentials.json에서 확인)
4. "편집자" 권한 부여

## 🎯 실행

### 웹 대시보드 실행
```bash
python run_web_server.py
```
브라우저에서 http://localhost:8001 접속

### 즉시 실행 (CLI)
```bash
python -m src.main --manual
```

## ✅ 체크리스트

- [ ] Python 3.10+ 설치됨
- [ ] 네이버 계정 정보 입력됨
- [ ] 구글 서비스 계정 키 저장됨 (`data/credentials.json`)
- [ ] 구글 시트에 서비스 계정 권한 부여됨
- [ ] 웹 대시보드 접속 가능

## 🐳 Docker로 실행 (선택사항)

```bash
# 빌드
docker build -t qok6-automation .

# 실행
docker run -d \
  --name qok6 \
  -p 8001:8001 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  qok6-automation
```

## 🔧 문제 해결

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Browser executable not found"
```bash
playwright install chromium
```

### "구글 시트 접근 거부"
→ 구글 시트에 서비스 계정 이메일이 추가되었는지 확인

### "네이버 로그인 실패"
→ 2단계 인증 확인, 쿠키 파일 업데이트

## 📞 도움말

- 상세 가이드: [DEPLOYMENT.md](DEPLOYMENT.md)
- 문제 신고: GitHub Issues
- 웹 대시보드: http://localhost:8001/docs (API 문서)