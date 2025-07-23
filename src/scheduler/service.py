"""스케줄링 및 알림 관리 서비스 모듈."""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ..core.logger import get_logger, log_execution_time
from ..core.exceptions import SchedulingError
from ..shared.utils import get_kst_now, format_datetime


class SchedulingService:
    """자동 실행 스케줄링 및 알림을 관리하는 서비스."""
    
    def __init__(
        self, 
        smtp_server: str,
        smtp_port: int,
        email_user: str,
        email_password: str,
        notification_recipients: List[str]
    ) -> None:
        """스케줄링 서비스 초기화."""
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._email_user = email_user
        self._email_password = email_password
        self._notification_recipients = notification_recipients
        self._logger = get_logger(__name__)
    
    @log_execution_time
    async def run_daily_task(
        self, 
        task_func: callable,
        *args,
        **kwargs
    ) -> bool:
        """일일 자동화 작업을 실행하고 결과를 반환."""
        execution_start = get_kst_now()
        
        try:
            self._logger.info(f"일일 자동화 작업 시작: {format_datetime(execution_start)}")
            
            # 작업 실행
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                result = task_func(*args, **kwargs)
            
            execution_end = get_kst_now()
            duration = execution_end - execution_start
            
            self._logger.info(
                f"일일 자동화 작업 완료: {format_datetime(execution_end)} "
                f"(소요시간: {duration.total_seconds():.1f}초)"
            )
            
            # 성공 알림 전송 (선택사항)
            await self._send_success_notification(execution_start, execution_end, result)
            
            return True
            
        except Exception as e:
            execution_end = get_kst_now()
            duration = execution_end - execution_start
            
            self._logger.error(
                f"일일 자동화 작업 실패: {str(e)} "
                f"(소요시간: {duration.total_seconds():.1f}초)"
            )
            
            # 실패 알림 전송
            await self._send_failure_notification(execution_start, execution_end, str(e))
            
            return False
    
    @log_execution_time
    def send_email_notification(
        self, 
        subject: str, 
        body: str,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """이메일 알림 전송."""
        if not recipients:
            recipients = self._notification_recipients
        
        if not recipients:
            self._logger.warning("알림 수신자가 설정되지 않았습니다")
            return False
        
        try:
            # 이메일 메시지 구성
            message = MIMEMultipart()
            message['From'] = self._email_user
            message['To'] = ', '.join(recipients)
            message['Subject'] = subject
            
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self._smtp_server, self._smtp_port) as server:
                server.starttls()
                server.login(self._email_user, self._email_password)
                server.sendmail(self._email_user, recipients, message.as_string())
            
            self._logger.info(f"이메일 알림 전송 완료: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            self._logger.error(f"이메일 알림 전송 실패: {str(e)}")
            return False
    
    async def _send_success_notification(
        self, 
        start_time: datetime, 
        end_time: datetime,
        result: Any
    ) -> None:
        """작업 성공 알림 전송."""
        try:
            duration = end_time - start_time
            
            subject = f"[QOK6] 일일 자동화 작업 성공 - {format_datetime(start_time, '%Y-%m-%d')}"
            
            body = f"""
QOK6 자동화 시스템 일일 작업이 성공적으로 완료되었습니다.

📅 실행 일시: {format_datetime(start_time)}
⏱️ 소요 시간: {duration.total_seconds():.1f}초
✅ 실행 결과: 성공

작업 상세 정보는 로그 파일을 확인해주세요.

---
QOK6 자동화 시스템
            """.strip()
            
            # 비동기 이메일 전송 (블로킹 방지)
            asyncio.create_task(
                asyncio.to_thread(
                    self.send_email_notification,
                    subject,
                    body
                )
            )
            
        except Exception as e:
            self._logger.error(f"성공 알림 전송 중 오류 발생: {str(e)}")
    
    async def _send_failure_notification(
        self, 
        start_time: datetime, 
        end_time: datetime,
        error_message: str
    ) -> None:
        """작업 실패 알림 전송."""
        try:
            duration = end_time - start_time
            
            subject = f"[QOK6] ⚠️ 일일 자동화 작업 실패 - {format_datetime(start_time, '%Y-%m-%d')}"
            
            body = f"""
⚠️ QOK6 자동화 시스템 일일 작업이 실패했습니다.

📅 실행 일시: {format_datetime(start_time)}
⏱️ 소요 시간: {duration.total_seconds():.1f}초
❌ 실행 결과: 실패

오류 내용:
{error_message}

즉시 시스템 점검이 필요합니다. 로그 파일을 확인하고 문제를 해결해주세요.

---
QOK6 자동화 시스템
            """.strip()
            
            # 실패 알림은 즉시 전송
            self.send_email_notification(subject, body)
            
        except Exception as e:
            self._logger.error(f"실패 알림 전송 중 오류 발생: {str(e)}")
    
    def get_next_execution_time(self, target_hour: int = 0, target_minute: int = 0) -> datetime:
        """다음 실행 시간 계산 (매일 지정 시간)."""
        now = get_kst_now()
        
        next_execution = now.replace(
            hour=target_hour, 
            minute=target_minute, 
            second=0, 
            microsecond=0
        )
        
        # 이미 오늘의 실행 시간이 지났다면 내일로 설정
        if next_execution <= now:
            next_execution += timedelta(days=1)
        
        return next_execution
    
    def calculate_sleep_duration(self, target_time: datetime) -> float:
        """다음 실행까지 대기할 시간 계산 (초 단위)."""
        now = get_kst_now()
        
        if target_time <= now:
            return 0.0
        
        duration = target_time - now
        return duration.total_seconds()
    
    @log_execution_time
    async def wait_until_scheduled_time(
        self, 
        target_hour: int = 0, 
        target_minute: int = 0
    ) -> None:
        """지정된 시간까지 대기."""
        try:
            next_execution = self.get_next_execution_time(target_hour, target_minute)
            sleep_duration = self.calculate_sleep_duration(next_execution)
            
            if sleep_duration > 0:
                self._logger.info(
                    f"다음 실행 시간까지 대기: {format_datetime(next_execution)} "
                    f"({sleep_duration/3600:.1f}시간)"
                )
                
                await asyncio.sleep(sleep_duration)
            
            self._logger.info("스케줄된 실행 시간 도달")
            
        except Exception as e:
            raise SchedulingError(f"스케줄 대기 중 오류 발생: {str(e)}")
    
    def create_execution_summary(self, results: Dict[str, Any]) -> str:
        """실행 결과 요약 생성."""
        try:
            summary_parts = []
            
            if 'total_posts' in results:
                summary_parts.append(f"크롤링한 게시글: {results['total_posts']}개")
            
            if 'updated_cells' in results:
                summary_parts.append(f"업데이트한 셀: {results['updated_cells']}개")
            
            if 'participants' in results:
                summary_parts.append(f"참여자 수: {len(results['participants'])}명")
            
            if 'weeks_processed' in results:
                summary_parts.append(f"처리한 주차: {results['weeks_processed']}개")
            
            return " | ".join(summary_parts) if summary_parts else "실행 완료"
            
        except Exception as e:
            self._logger.error(f"실행 요약 생성 중 오류 발생: {str(e)}")
            return "실행 완료 (요약 생성 실패)"