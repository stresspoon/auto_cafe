"""설정 관리 모듈 - 환경 변수 및 설정 파일 로드."""

import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """애플리케이션 설정을 관리하는 클래스."""
    
    def __init__(self) -> None:
        """환경 변수를 로드하여 설정 초기화."""
        load_dotenv()
    
    @property
    def naver_id(self) -> str:
        """네이버 로그인 ID 반환."""
        return self._get_required_env("NAVER_ID")
    
    @property
    def naver_password(self) -> str:
        """네이버 로그인 패스워드 반환."""
        return self._get_required_env("NAVER_PASSWORD")
    
    @property
    def cafe_url(self) -> str:
        """네이버 카페 URL 반환."""
        return self._get_required_env("CAFE_URL")
    
    @property
    def board_id(self) -> str:
        """게시판 ID 반환."""
        return self._get_required_env("BOARD_ID")
    
    @property
    def crawl_pages(self) -> int:
        """크롤링할 페이지 수 반환."""
        return int(self._get_env_with_default("CRAWL_PAGES", "3"))
    
    @property
    def google_sheet_id(self) -> str:
        """구글 시트 ID 반환."""
        return self._get_required_env("GOOGLE_SHEET_ID")
    
    @property
    def google_credentials_path(self) -> str:
        """구글 API 인증 파일 경로 반환."""
        return self._get_required_env("GOOGLE_CREDENTIALS_PATH")
    
    @property
    def log_level(self) -> str:
        """로그 레벨 반환."""
        return self._get_env_with_default("LOG_LEVEL", "INFO")
    
    @property
    def log_file_path(self) -> str:
        """로그 파일 경로 반환."""
        return self._get_env_with_default("LOG_FILE_PATH", "logs/qok6.log")
    
    @property
    def encryption_key(self) -> Optional[str]:
        """암호화 키 반환."""
        return os.getenv("ENCRYPTION_KEY")
    
    
    def _get_required_env(self, key: str) -> str:
        """필수 환경 변수 값을 반환하며, 없으면 예외 발생."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {key}")
        return value
    
    def _get_env_with_default(self, key: str, default: str) -> str:
        """환경 변수 값을 반환하며, 없으면 기본값 사용."""
        return os.getenv(key, default)