"""네이버 크롤링 관련 데이터 모델."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NaverPost:
    """네이버 카페 게시글을 나타내는 데이터 클래스."""
    
    title: str
    author: str
    content: str
    post_id: str
    created_at: datetime
    post_url: Optional[str] = None
    view_count: Optional[int] = None
    comment_count: Optional[int] = None
    
    def __post_init__(self) -> None:
        """게시글 데이터 유효성 검사."""
        if not self.title.strip():
            raise ValueError("게시글 제목이 비어있습니다")
        
        if not self.author.strip():
            raise ValueError("작성자 정보가 비어있습니다")
        
        if not self.post_id.strip():
            raise ValueError("게시글 ID가 비어있습니다")
    
    @property
    def is_challenge_post(self) -> bool:
        """챌린지 관련 게시글인지 확인."""
        from ..shared.utils import is_valid_week_post
        return is_valid_week_post(self.title, self.content)
    
    @property
    def week_number(self) -> Optional[int]:
        """게시글에서 주차 번호 추출."""
        from ..shared.utils import extract_week_number
        combined_text = f"{self.title} {self.content}"
        return extract_week_number(combined_text)
    
    def to_dict(self) -> dict:
        """딕셔너리 형태로 변환."""
        return {
            'title': self.title,
            'author': self.author,
            'content': self.content,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat(),
            'post_url': self.post_url,
            'view_count': self.view_count,
            'comment_count': self.comment_count,
            'is_challenge_post': self.is_challenge_post,
            'week_number': self.week_number
        }