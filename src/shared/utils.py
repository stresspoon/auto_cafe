"""공통 유틸리티 함수 모듈."""

import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any


def extract_week_number(text: str) -> Optional[int]:
    """텍스트에서 '*주차' 패턴을 찾아 주차 번호 반환."""
    pattern = r'\*?(\d+)\s*주차'
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None


def is_valid_week_post(title: str, content: str = "") -> bool:
    """게시글이 유효한 주차 포스트인지 확인."""
    combined_text = f"{title} {content}"
    return extract_week_number(combined_text) is not None


def sanitize_filename(filename: str) -> str:
    """파일명에서 특수문자를 제거하여 안전한 파일명 반환."""
    # Windows에서 금지된 문자 제거
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # 연속된 공백을 단일 공백으로 변환
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def get_kst_now() -> datetime:
    """한국 표준시(KST) 기준 현재 시각 반환."""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """datetime 객체를 지정된 형식으로 포맷팅."""
    return dt.strftime(format_str)


def retry_with_backoff(
    func, 
    max_retries: int = 3, 
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
):
    """지수 백오프를 사용한 재시도 데코레이터."""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                time.sleep(delay)
                delay *= backoff_factor
        
        return None
    
    return wrapper


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """리스트를 지정된 크기의 청크로 분할."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def validate_email(email: str) -> bool:
    """이메일 주소 형식 유효성 검사."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def safe_get_dict_value(
    dictionary: Dict[str, Any], 
    key: str, 
    default: Any = None
) -> Any:
    """딕셔너리에서 안전하게 값을 가져오기 (키가 없어도 예외 발생 안함)."""
    return dictionary.get(key, default)