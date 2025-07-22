"""로깅 설정 및 유틸리티 모듈."""

import logging
import os
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """로깅 시스템 설정을 담당하는 클래스."""
    
    @staticmethod
    def setup_logging(
        level: str = "INFO",
        log_file_path: Optional[str] = None,
        logger_name: str = "qok6"
    ) -> logging.Logger:
        """구조화된 로깅 시스템을 설정하고 로거 인스턴스 반환."""
        logger = logging.getLogger(logger_name)
        
        # 기존 핸들러 제거 (중복 방지)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        logger.setLevel(getattr(logging, level.upper()))
        
        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러 추가 (파일 경로가 제공된 경우)
        if log_file_path:
            LoggerSetup._create_log_directory(log_file_path)
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def _create_log_directory(log_file_path: str) -> None:
        """로그 파일 디렉토리가 없으면 생성."""
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """지정된 이름으로 로거 인스턴스 반환."""
    return logging.getLogger(f"qok6.{name}")


def log_execution_time(func):
    """함수 실행 시간을 로깅하는 데코레이터."""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 실행 완료 (소요시간: {execution_time:.2f}초)")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 실행 실패 (소요시간: {execution_time:.2f}초): {str(e)}")
            raise
    
    return wrapper