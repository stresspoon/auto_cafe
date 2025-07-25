# 제품 요구사항 문서 (PRD)

## 1. 총괄 요약
네이버 카페에 업로드된 챌린지 미션 현황을 매일 00시 자동 확인하여 구글 시트에 `O/X`로 표기하는 자동화 서비스. 챌린지 진행자는 수작업 없이 참여자 진행 상황을 실시간 파악할 수 있어 운영 효율이 향상된다.

## 2. 문제 정의
- 진행자는 매일 카페 게시글을 열람하며 참여자별 업로드 여부를 수동 확인하고 시트에 기록함.  
- 인원·주차 증가 시 확인 누락, 입력 오류, 시간 소모 발생.  
- 현행 프로세스는 반복적·비효율적이며 자동화 솔루션 부재.

## 3. 목표 및 목적
- 1차 목표: 네이버 카페 → 구글 시트 자동 동기화
- 부가 목표: 운영 시간 90% 절감, 입력 오류 0건 달성, 참여 현황 실시간 공개
- 성공 지표:
  - 매일 00:00 자동 실행 성공률 99% 이상
  - 시트 반영 정확도 99.9% 이상
  - 운영자 주간 업무 시간 5시간 → 0.5시간 축소

## 4. 타깃 사용자
### 주요 사용자
- 챌린지 진행자: 20~40대, 온라인 강의·챌린지 운영 경험, 자동화 니즈 높음
### 2차 사용자
- 참여자: 개인 진척 상황 확인 가능  
- 경영진: 활동 데이터 기반 리포트 활용

## 5. 사용자 스토리
- 진행자로서, 매일 수동 확인 없이도 시트에 자동 체크되어 운영 시간을 절약하고 싶다.  
- 진행자로서, 참여 주차별 현황을 한눈에 보고 미달자를 즉시 파악하고 싶다.  
- 참여자로서, 내 미션 업로드가 제대로 기록되었는지 즉시 확인하고 싶다.

## 6. 기능 요구사항
### 핵심 기능
1. 네이버 자동 로그인  
   - 입력된 ID/PW, 2차 인증 처리(OTP API 또는 Cookie 저장)  
   - AC: 로그인 실패 시 재시도 3회, 실패 로깅

2. 카페 게시글 크롤링  
   - 지정 게시판 1~3페이지 순회, 제목·작성자·본문 파싱  
   - `*주차` 키워드와 작성자 닉네임 추출  
   - AC: 100건/page, 중복·삭제 게시글 제외

3. 구글 시트 업데이트  
   - 사전 정의된 Sheet ID, 사용자명 행, 주차 열에 `O` 기록, 없으면 `X`  
   - AC: API 호출 오류 시 재시도, 최대 5초 내 응답

4. 스케줄러  
   - 매일 00:00 UTC+9 자동 실행  
   - AC: Cron 기반, 실행 로그 저장, 실패 시 이메일 알림

### 보조 기능
- 수동 즉시 실행 버튼 (웹 UI 또는 CLI)  
- 최근 실행 로그 조회  
- 설정 파일(카페 URL, 시트 ID, 주차 수) UI 편집

## 7. 비기능 요구사항
- 성능: 1~3페이지 크롤링 및 시트 업데이트 2분 이내 완료  
- 보안: 자격 증명 암호화 저장(AES256), HTTPS 통신  
- 사용성: 설정 UI 국문, 3-step 이내 설정 완료  
- 확장성: 주차·페이지 수 증가 시 5만 게시글까지 대응  
- 호환성: Windows/Linux 서버, Python 3.10 이상

## 8. 기술 고려사항
- 아키텍처: 
  - `Scheduler` → `Crawler(Naver)` → `Parser` → `GSuite API Service` → `Logger`
- 스택: Python, Selenium/Playwright, Google Sheets API v4, Cron, Docker  
- 데이터: 게시글 메타(작성자, 작성일, 주차), 시트 셀 값  
- 외부 연동: Google OAuth, 네이버 로그인, SendGrid(알림)  
- 배포: Docker 이미지 → AWS ECS 또는 EC2

## 9. 성공 지표
- 일일 Task 성공률  
- 시트 반영 시간(평균, p95)  
- 수동 수정 건수  
- 운영자 만족도 설문(4점/5점 이상)

## 10. 일정 및 마일스톤
- Phase 0 (2주): 요구사항 확정, 기술 검증(PoC)  
- Phase 1 (4주): MVP  
  - 자동 로그인, 1페이지 크롤링, 시트 반영  
- Phase 2 (3주): 범위 확대  
  - 3페이지, 주차 자동 인식, 알림  
- Phase 3 (2주): UI·모니터링, 클라우드 배포  
- 런칭: 2024-Q3 Week2

## 11. 위험 및 대응
- 네이버 보안 정책 변경 → 크롤링 차단  
  - 대응: Selenium 스텔스 모드, 쿠키 재생성 스크립트  
- Google API 호출 제한  
  - 대응: 배치 쓰로틀링, 캐시  
- 00시 트래픽 집중 → 실행 지연  
  - 대응: 재시도 로직, 오프피크 시간 옵션  
- 사용자 인증정보 유출  
  - 대응: KeyVault 저장, 정기 교체

## 12. 향후 고려사항
- 멀티 카페·게시판 지원  
- Slack/카카오 알림 통합  
- 대시보드 시각화(Google Data Studio)  
- AI를 활용한 게시글 자동 분류 및 부정행위 탐지