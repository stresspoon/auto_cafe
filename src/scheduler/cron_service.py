"""Cron 기반 스케줄링 서비스."""

import asyncio
import subprocess
from datetime import datetime, time
from typing import Optional, Callable
from pathlib import Path

from ..core.logger import get_logger, log_execution_time
from ..shared.utils import get_kst_now


class CronService:
    """Cron 기반 자동 스케줄링 서비스."""
    
    def __init__(self, python_path: Optional[str] = None, script_path: Optional[str] = None) -> None:
        """Cron 서비스 초기화."""
        self._logger = get_logger(__name__)
        self._python_path = python_path or "python3"
        self._script_path = script_path or str(Path(__file__).parent.parent.parent / "src" / "main.py")
        self._cron_comment = "# QOK6 자동화 서비스"
        
    def setup_daily_cron(self, hour: int = 0, minute: int = 0) -> bool:
        """매일 지정 시간에 실행되는 cron 작업 설정."""
        try:
            # 기존 cron 작업 확인 및 제거
            self._remove_existing_cron()
            
            # 새로운 cron 작업 추가
            cron_command = f"{minute} {hour} * * * cd {Path.cwd()} && source venv/bin/activate && {self._python_path} -m src.main --manual >> logs/cron.log 2>&1"
            cron_entry = f"{cron_command} {self._cron_comment}"
            
            # crontab에 추가
            result = subprocess.run(
                ["crontab", "-l"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            existing_crontab = result.stdout if result.returncode == 0 else ""
            new_crontab = existing_crontab.strip() + f"\n{cron_entry}\n" if existing_crontab.strip() else f"{cron_entry}\n"
            
            # 새로운 crontab 설정
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                self._logger.info(f"Cron 작업 설정 성공: 매일 {hour:02d}:{minute:02d}에 실행")
                return True
            else:
                self._logger.error("Cron 작업 설정 실패")
                return False
                
        except Exception as e:
            self._logger.error(f"Cron 작업 설정 중 오류: {str(e)}")
            return False
    
    def _remove_existing_cron(self) -> None:
        """기존 QOK6 cron 작업 제거."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                self._logger.info("기존 crontab이 없습니다")
                return
            
            # QOK6 관련 작업 제거
            lines = result.stdout.split('\n')
            filtered_lines = [line for line in lines if self._cron_comment not in line]
            new_crontab = '\n'.join(filtered_lines).strip()
            
            if new_crontab != result.stdout.strip():
                # 변경된 crontab 적용
                process = subprocess.Popen(
                    ["crontab", "-"],
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=new_crontab + '\n' if new_crontab else '')
                
                if process.returncode == 0:
                    self._logger.info("기존 QOK6 cron 작업 제거 완료")
                else:
                    self._logger.error("기존 cron 작업 제거 실패")
                    
        except Exception as e:
            self._logger.error(f"기존 cron 작업 제거 중 오류: {str(e)}")
    
    def remove_cron(self) -> bool:
        """QOK6 cron 작업 제거."""
        try:
            self._remove_existing_cron()
            self._logger.info("QOK6 cron 작업 제거 완료")
            return True
        except Exception as e:
            self._logger.error(f"Cron 작업 제거 실패: {str(e)}")
            return False
    
    def get_cron_status(self) -> dict:
        """현재 cron 작업 상태 조회."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return {
                    "active": False,
                    "schedule": None,
                    "next_run": None
                }
            
            # QOK6 관련 작업 찾기
            lines = result.stdout.split('\n')
            qok6_cron = None
            
            for line in lines:
                if self._cron_comment in line:
                    qok6_cron = line.replace(self._cron_comment, '').strip()
                    break
            
            if not qok6_cron:
                return {
                    "active": False,
                    "schedule": None,
                    "next_run": None
                }
            
            # cron 표현식 파싱
            cron_parts = qok6_cron.split()
            if len(cron_parts) >= 5:
                minute = cron_parts[0]
                hour = cron_parts[1]
                
                # 다음 실행 시간 계산
                next_run = self._calculate_next_run(minute, hour)
                
                return {
                    "active": True,
                    "schedule": f"매일 {hour}:{minute:>02s}",
                    "next_run": next_run.isoformat() if next_run else None,
                    "cron_expression": f"{minute} {hour} * * *"
                }
            
            return {
                "active": True,
                "schedule": "알 수 없음",
                "next_run": None
            }
            
        except Exception as e:
            self._logger.error(f"Cron 상태 조회 중 오류: {str(e)}")
            return {
                "active": False,
                "schedule": None,
                "next_run": None,
                "error": str(e)
            }
    
    def _calculate_next_run(self, minute_str: str, hour_str: str) -> Optional[datetime]:
        """다음 실행 시간 계산."""
        try:
            minute = int(minute_str)
            hour = int(hour_str)
            
            now = get_kst_now()
            target_time = time(hour=hour, minute=minute)
            
            # 오늘 날짜로 실행 시간 생성
            today_run = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
            # 오늘 실행 시간이 이미 지났으면 내일로
            if today_run <= now:
                from datetime import timedelta
                next_run = today_run + timedelta(days=1)
            else:
                next_run = today_run
            
            return next_run
            
        except Exception as e:
            self._logger.error(f"다음 실행 시간 계산 중 오류: {str(e)}")
            return None
    
    @log_execution_time
    async def wait_until_scheduled_time(self, hour: int = 0, minute: int = 0) -> None:
        """지정된 시간까지 대기."""
        while True:
            now = get_kst_now()
            target_time = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
            # 오늘 시간이 지났으면 내일로
            if target_time <= now:
                from datetime import timedelta
                target_time += timedelta(days=1)
            
            # 대기 시간 계산
            wait_seconds = (target_time - now).total_seconds()
            self._logger.info(f"다음 실행까지 {wait_seconds:.0f}초 대기 (실행 시간: {target_time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            await asyncio.sleep(wait_seconds)
            break
    
    def test_cron_setup(self) -> bool:
        """Cron 설정 테스트."""
        try:
            # 1분 후 실행되는 임시 테스트 작업 생성
            now = get_kst_now()
            test_minute = (now.minute + 1) % 60
            test_hour = now.hour + (1 if now.minute == 59 else 0)
            test_hour = test_hour % 24
            
            self._logger.info(f"Cron 테스트: {test_hour:02d}:{test_minute:02d}에 실행 예정")
            
            # 임시 테스트 명령
            test_command = f"{test_minute} {test_hour} * * * echo 'QOK6 Cron Test - {now.isoformat()}' >> /tmp/qok6_cron_test.log"
            test_entry = f"{test_command} # QOK6 테스트"
            
            # 현재 crontab 가져오기
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            existing_crontab = result.stdout if result.returncode == 0 else ""
            new_crontab = existing_crontab.strip() + f"\n{test_entry}\n" if existing_crontab.strip() else f"{test_entry}\n"
            
            # 테스트 crontab 설정
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=new_crontab)
            
            return process.returncode == 0
            
        except Exception as e:
            self._logger.error(f"Cron 테스트 중 오류: {str(e)}")
            return False