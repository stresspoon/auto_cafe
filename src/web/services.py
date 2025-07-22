"""웹 서비스 관련 서비스 모듈."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..core.logger import get_logger
from ..shared.utils import get_kst_now


class ExecutionLogService:
    """실행 로그 저장 및 조회 서비스."""
    
    def __init__(self, log_file_path: str = "logs/executions.json") -> None:
        """실행 로그 서비스 초기화."""
        self._log_file_path = Path(log_file_path)
        self._logger = get_logger(__name__)
        
        # 로그 디렉토리 생성
        self._log_file_path.parent.mkdir(exist_ok=True)
        
        # 로그 파일이 없으면 초기화
        if not self._log_file_path.exists():
            self._save_logs([])
    
    def start_execution(self) -> str:
        """새로운 실행 시작하고 실행 ID 반환."""
        execution_id = str(uuid.uuid4())
        started_at = get_kst_now()
        
        # 시작 로그 저장
        log_entry = {
            "execution_id": execution_id,
            "started_at": started_at.isoformat(),
            "completed_at": None,
            "success": False,
            "message": "실행 시작",
            "results": None,
            "error_message": None
        }
        
        self._add_log_entry(log_entry)
        self._logger.info(f"실행 시작 로그 저장: {execution_id}")
        
        return execution_id
    
    def complete_execution(
        self,
        execution_id: str,
        success: bool,
        results: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """실행 완료 상태로 업데이트."""
        completed_at = get_kst_now()
        
        # 기존 로그 찾아서 업데이트
        logs = self._load_logs()
        
        for log_entry in logs:
            if log_entry['execution_id'] == execution_id:
                log_entry['completed_at'] = completed_at.isoformat()
                log_entry['success'] = success
                log_entry['results'] = results
                log_entry['error_message'] = error_message
                
                if success:
                    log_entry['message'] = "실행 성공"
                else:
                    log_entry['message'] = "실행 실패"
                
                break
        else:
            # 해당 실행 ID가 없으면 새로 추가
            log_entry = {
                "execution_id": execution_id,
                "started_at": completed_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "success": success,
                "message": "실행 성공" if success else "실행 실패",
                "results": results,
                "error_message": error_message
            }
            logs.append(log_entry)
        
        self._save_logs(logs)
        self._logger.info(f"실행 완료 로그 저장: {execution_id} (성공: {success})")
    
    def get_logs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """실행 로그 조회 (최신순)."""
        logs = self._load_logs()
        
        # 시작 시간 기준 내림차순 정렬
        logs.sort(key=lambda x: x['started_at'], reverse=True)
        
        # 페이지네이션 적용
        return logs[offset:offset + limit]
    
    def get_total_count(self) -> int:
        """전체 로그 개수 반환."""
        logs = self._load_logs()
        return len(logs)
    
    def get_success_rate(self, days: int = 7) -> float:
        """최근 N일간 성공률 계산."""
        from datetime import timedelta
        
        logs = self._load_logs()
        cutoff_date = get_kst_now() - timedelta(days=days)
        
        # 최근 N일간 로그 필터링
        recent_logs = []
        for log in logs:
            if log.get('completed_at'):
                log_date = datetime.fromisoformat(log['completed_at'])
                if log_date >= cutoff_date:
                    recent_logs.append(log)
        
        if not recent_logs:
            return 0.0
        
        success_count = sum(1 for log in recent_logs if log.get('success', False))
        return success_count / len(recent_logs)
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """N일 이전의 로그 정리."""
        from datetime import timedelta
        
        logs = self._load_logs()
        cutoff_date = get_kst_now() - timedelta(days=days)
        
        # 최근 로그만 유지
        filtered_logs = []
        removed_count = 0
        
        for log in logs:
            log_date = datetime.fromisoformat(log['started_at'])
            if log_date >= cutoff_date:
                filtered_logs.append(log)
            else:
                removed_count += 1
        
        if removed_count > 0:
            self._save_logs(filtered_logs)
            self._logger.info(f"{removed_count}개의 오래된 로그를 정리했습니다")
        
        return removed_count
    
    def _add_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """새 로그 엔트리 추가."""
        logs = self._load_logs()
        logs.append(log_entry)
        
        # 최대 1000개까지만 유지 (메모리 절약)
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        self._save_logs(logs)
    
    def _load_logs(self) -> List[Dict[str, Any]]:
        """로그 파일에서 로그 데이터 로드."""
        try:
            if not self._log_file_path.exists():
                return []
            
            with open(self._log_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self._logger.error(f"로그 파일 로드 중 오류: {str(e)}")
            return []
    
    def _save_logs(self, logs: List[Dict[str, Any]]) -> None:
        """로그 데이터를 파일에 저장."""
        try:
            with open(self._log_file_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self._logger.error(f"로그 파일 저장 중 오류: {str(e)}")