"""QOK6 자동화 시스템 메인 실행 스크립트."""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.core.logger import LoggerSetup, get_logger
from src.core.exceptions import QOK6Exception
from src.naver_crawler.service import NaverCrawlerService
from src.google_sheets.service import GoogleSheetsService
from src.parser.service import DataParsingService
from src.scheduler.service import SchedulingService


class QOK6AutomationSystem:
    """QOK6 자동화 시스템의 메인 오케스트레이터."""
    
    def __init__(self) -> None:
        """시스템 초기화."""
        # 설정 로드
        self.config = Config()
        
        # 로깅 설정
        self.logger = LoggerSetup.setup_logging(
            level=self.config.log_level,
            log_file_path=self.config.log_file_path
        )
        
        # 서비스 인스턴스 초기화
        self.naver_crawler = NaverCrawlerService(
            naver_id=self.config.naver_id,
            naver_password=self.config.naver_password
        )
        
        self.google_sheets = GoogleSheetsService(
            credentials_path=self.config.google_credentials_path,
            sheet_id=self.config.google_sheet_id
        )
        
        self.parser = DataParsingService()
        
        # 스케줄러는 환경 변수가 있을 때만 초기화
        self.scheduler = None
        try:
            from os import getenv
            smtp_server = getenv('SMTP_SERVER')
            if smtp_server:
                self.scheduler = SchedulingService(
                    smtp_server=smtp_server,
                    smtp_port=int(getenv('SMTP_PORT', '587')),
                    email_user=getenv('EMAIL_USER', ''),
                    email_password=getenv('EMAIL_PASSWORD', ''),
                    notification_recipients=getenv('NOTIFICATION_RECIPIENTS', '').split(',')
                )
        except Exception as e:
            self.logger.warning(f"스케줄러 초기화 실패 (이메일 알림 비활성화): {str(e)}")
    
    async def run_automation_cycle(self) -> dict:
        """전체 자동화 사이클을 실행하고 결과 반환."""
        results = {
            'success': False,
            'total_posts': 0,
            'updated_cells': 0,
            'participants': [],
            'weeks_processed': 0,
            'error_message': None
        }
        
        try:
            self.logger.info("=== QOK6 자동화 사이클 시작 ===")
            
            # capture.txt 파일 우선 확인
            import os
            if os.path.exists('capture.txt'):
                self.logger.info("capture.txt 파일 발견, HTML에서 직접 파싱합니다 (크롤링 생략)")
                weekly_submissions = self.parser.extract_weekly_submissions_from_html('capture.txt')
                results['total_posts'] = 0  # 크롤링하지 않음
            else:
                self.logger.info("capture.txt 파일 없음, 크롤링을 시작합니다")
                
                # 1. 네이버 크롤러 초기화 및 로그인
                await self.naver_crawler.initialize_browser()
                login_success = await self.naver_crawler.login_to_naver()
                
                if not login_success:
                    raise QOK6Exception("네이버 로그인에 실패했습니다")
                
                # 2. 게시글 크롤링
                posts = await self.naver_crawler.crawl_cafe_posts(
                    cafe_url=self.config.cafe_url,
                    board_id=self.config.board_id,
                    pages=self.config.crawl_pages
                )
                results['total_posts'] = len(posts)
                
                # 3. 데이터 파싱
                challenge_posts = self.parser.filter_challenge_posts(posts)
                weekly_submissions = self.parser.extract_weekly_submissions(challenge_posts)
            
            # 파싱 결과 유효성 검증
            if not self.parser.validate_parsing_result(weekly_submissions):
                raise QOK6Exception("파싱 결과 유효성 검증에 실패했습니다")
            
            results['weeks_processed'] = len(weekly_submissions)
            
            # 4. 구글 시트 연동
            self.google_sheets.authenticate()
            
            # 참여자 목록 가져오기
            participants = self.google_sheets.get_participants_list()
            results['participants'] = participants
            
            # 5. 출석 현황 업데이트
            update_success = self.google_sheets.update_attendance_from_submissions(weekly_submissions)
            results['updated_cells'] = len(weekly_submissions) * len(participants) if update_success else 0
            
            results['success'] = True
            self.logger.info("=== QOK6 자동화 사이클 완료 ===")
            
            return results
            
        except Exception as e:
            error_msg = f"자동화 사이클 실행 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            results['error_message'] = error_msg
            return results
            
        finally:
            # 리소스 정리
            try:
                await self.naver_crawler.close()
            except Exception as e:
                self.logger.error(f"크롤러 종료 중 오류: {str(e)}")
    
    async def run_scheduled_mode(self) -> None:
        """스케줄된 자동 실행 모드."""
        if not self.scheduler:
            self.logger.error("스케줄러가 초기화되지 않았습니다")
            return
        
        self.logger.info("스케줄된 자동 실행 모드 시작")
        
        while True:
            try:
                # 매일 00:00까지 대기
                await self.scheduler.wait_until_scheduled_time(0, 0)
                
                # 자동화 작업 실행
                success = await self.scheduler.run_daily_task(
                    self.run_automation_cycle
                )
                
                if success:
                    self.logger.info("일일 자동화 작업 성공")
                else:
                    self.logger.error("일일 자동화 작업 실패")
                
            except KeyboardInterrupt:
                self.logger.info("사용자 요청으로 자동 실행 모드 종료")
                break
            except Exception as e:
                self.logger.error(f"스케줄된 실행 중 예상치 못한 오류: {str(e)}")
                # 오류 발생 시 1시간 후 재시도
                await asyncio.sleep(3600)
    
    async def run_manual_mode(self) -> None:
        """수동 즉시 실행 모드."""
        self.logger.info("수동 즉시 실행 모드 시작")
        
        results = await self.run_automation_cycle()
        
        if results['success']:
            print("✅ 자동화 작업이 성공적으로 완료되었습니다!")
            print(f"   - 크롤링한 게시글: {results['total_posts']}개")
            print(f"   - 처리한 주차: {results['weeks_processed']}개")
        else:
            print("❌ 자동화 작업이 실패했습니다.")
            print(f"   오류: {results['error_message']}")


async def main():
    """메인 실행 함수."""
    try:
        system = QOK6AutomationSystem()
        
        # 실행 모드 결정 (환경 변수 또는 명령줄 인자로)
        import sys
        
        if len(sys.argv) > 1 and sys.argv[1] == "--manual":
            await system.run_manual_mode()
        else:
            await system.run_scheduled_mode()
            
    except Exception as e:
        print(f"시스템 시작 중 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())