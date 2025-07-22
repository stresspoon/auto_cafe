# QOK6 자동화 시스템

네이버 카페 챌린지 미션 현황을 매일 자동으로 확인하여 구글 시트에 O/X로 기록하는 자동화 시스템입니다.

## 📋 주요 기능

- **자동 로그인**: 네이버 카페 자동 로그인 (2차 인증 포함)
- **게시글 크롤링**: 지정 게시판 1~3페이지 순회하여 데이터 수집
- **데이터 파싱**: 게시글에서 주차 정보 및 작성자 추출
- **시트 업데이트**: 구글 시트에 참여 현황 자동 기록
- **스케줄링**: 매일 00:00 자동 실행
- **알림**: 실행 결과 이메일 알림

## 🏗️ 아키텍처

```
src/
├── main.py                 # 메인 실행 스크립트
├── config.py               # 설정 관리
├── core/                   # 핵심 공통 기능
│   ├── logger.py           # 로깅 시스템
│   ├── exceptions.py       # 사용자 정의 예외
│   └── security.py         # 자격 증명 암호화
├── naver_crawler/          # 네이버 크롤링
│   ├── service.py          # 크롤링 로직
│   └── models.py           # 데이터 모델
├── google_sheets/          # 구글 시트 연동
│   ├── service.py          # API 연동 로직
│   └── models.py           # 시트 데이터 모델
├── parser/                 # 데이터 파싱
│   └── service.py          # 파싱 로직
├── scheduler/              # 스케줄링 및 알림
│   └── service.py          # 스케줄링 로직
└── shared/                 # 공통 유틸리티
    └── utils.py            # 유틸리티 함수
```

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 환경 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 설정 값 입력
```

### 3. 구글 API 인증 설정
- Google Cloud Console에서 서비스 계정 생성
- 서비스 계정 키를 `data/credentials.json`으로 저장
- Google Sheets API 활성화

### 4. 실행

#### 수동 실행 (테스트용)
```bash
python -m src.main --manual
```

#### 자동 스케줄 실행
```bash
python -m src.main
```

#### Docker 실행
```bash
docker build -t qok6-automation .
docker run -d --env-file .env qok6-automation
```

## ⚙️ 설정

### 환경 변수
주요 환경 변수들:

```env
# 네이버 로그인
NAVER_ID=your_id
NAVER_PASSWORD=your_password

# 카페 설정
CAFE_URL=https://cafe.naver.com/your_cafe
BOARD_ID=your_board_id
CRAWL_PAGES=3

# 구글 시트
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_PATH=data/credentials.json

# 알림
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
NOTIFICATION_RECIPIENTS=admin@example.com
```

### 로깅
- 로그 레벨: DEBUG, INFO, WARNING, ERROR
- 콘솔 및 파일 로깅 지원
- 실행 시간 추적 및 성능 모니터링

## 🔒 보안

- 환경 변수를 통한 민감 정보 관리
- AES256 암호화를 통한 자격 증명 보호
- HTTPS 통신 강제
- 브라우저 헤드리스 모드로 봇 탐지 회피

## 🧪 개발

### 코드 스타일
- **클린 코드**: DRY, KISS, YAGNI 원칙 준수
- **TDD**: Red → Green → Refactor 사이클
- **타입 힌트**: 모든 함수에 타입 어노테이션 적용
- **독립적 함수**: 단일 책임 원칙, 20라인 이하

### 테스트
```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트  
pytest tests/integration/

# 전체 테스트
pytest
```

## 📊 모니터링

### 성공 지표
- 매일 00:00 자동 실행 성공률 99% 이상
- 시트 반영 정확도 99.9% 이상
- 1~3페이지 크롤링 및 시트 업데이트 2분 이내 완료

### 로그 확인
```bash
tail -f logs/qok6.log
```

## 🆘 문제 해결

### 일반적인 문제들

1. **네이버 로그인 실패**
   - 2차 인증 설정 확인
   - 계정 보안 설정 확인
   - User-Agent 헤더 업데이트

2. **구글 시트 연동 실패**
   - 서비스 계정 권한 확인
   - API 할당량 확인
   - 시트 공유 설정 확인

3. **크롤링 오류**
   - 네이버 카페 HTML 구조 변경 여부 확인
   - 페이지 로딩 시간 증가로 인한 타임아웃

## 📝 라이선스

이 프로젝트는 vooster-ai 가이드라인을 따라 개발되었습니다.

## 📞 지원

문제가 발생하면 로그 파일과 함께 이슈를 등록해주세요.