"""참여자 관련 데이터 모델."""

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class Participant:
    """챌린지 참여자를 나타내는 데이터 클래스."""
    
    name: str                    # 참여자 이름
    nickname: str                # 네이버 카페 닉네임
    email: Optional[str] = None  # 이메일 (선택사항)
    active: bool = True          # 활성 상태
    
    def __post_init__(self) -> None:
        """참여자 데이터 유효성 검사."""
        if not self.name.strip():
            raise ValueError("참여자 이름이 비어있습니다")
        
        if not self.nickname.strip():
            raise ValueError("닉네임이 비어있습니다")
    
    def to_dict(self) -> dict:
        """딕셔너리 형태로 변환."""
        return {
            'name': self.name,
            'nickname': self.nickname,
            'email': self.email,
            'active': self.active
        }


@dataclass
class ChallengeInfo:
    """챌린지 정보를 나타내는 데이터 클래스."""
    
    name: str                    # 챌린지 이름
    start_week: int              # 시작 주차
    end_week: int                # 종료 주차
    current_week: Optional[int] = None  # 현재 주차
    
    def __post_init__(self) -> None:
        """챌린지 정보 유효성 검사."""
        if self.start_week < 1:
            raise ValueError("시작 주차는 1 이상이어야 합니다")
        
        if self.end_week < self.start_week:
            raise ValueError("종료 주차는 시작 주차 이후여야 합니다")
        
        if self.current_week and (self.current_week < self.start_week or self.current_week > self.end_week):
            raise ValueError("현재 주차가 챌린지 기간을 벗어났습니다")
    
    @property
    def total_weeks(self) -> int:
        """전체 주차 수 반환."""
        return self.end_week - self.start_week + 1
    
    @property
    def week_range(self) -> List[int]:
        """주차 범위 리스트 반환."""
        return list(range(self.start_week, self.end_week + 1))
    
    def to_dict(self) -> dict:
        """딕셔너리 형태로 변환."""
        return {
            'name': self.name,
            'start_week': self.start_week,
            'end_week': self.end_week,
            'current_week': self.current_week,
            'total_weeks': self.total_weeks
        }