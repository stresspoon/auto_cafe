"""구글 시트 관련 데이터 모델."""

from dataclasses import dataclass
from typing import List, Any, Optional


@dataclass
class SheetUpdateRequest:
    """시트 업데이트 요청을 나타내는 데이터 클래스."""
    
    range_name: str
    values: List[List[Any]]
    
    def __post_init__(self) -> None:
        """업데이트 요청 데이터 유효성 검사."""
        if not self.range_name.strip():
            raise ValueError("범위 이름이 비어있습니다")
        
        if not self.values:
            raise ValueError("업데이트할 값이 비어있습니다")


@dataclass
class SheetData:
    """시트에서 읽어온 데이터를 나타내는 데이터 클래스."""
    
    range_name: str
    values: List[List[Any]]
    
    def __post_init__(self) -> None:
        """시트 데이터 유효성 검사."""
        if not self.range_name.strip():
            raise ValueError("범위 이름이 비어있습니다")
        
        # values는 빈 리스트일 수 있음 (빈 시트인 경우)
        if self.values is None:
            self.values = []
    
    @property
    def row_count(self) -> int:
        """데이터 행 수 반환."""
        return len(self.values)
    
    @property
    def column_count(self) -> int:
        """데이터 열 수 반환 (가장 긴 행 기준)."""
        return max(len(row) for row in self.values) if self.values else 0
    
    def get_cell_value(self, row: int, col: int) -> Any:
        """특정 셀의 값을 가져오기 (0-based 인덱스)."""
        try:
            return self.values[row][col]
        except IndexError:
            return None
    
    def find_row_by_value(self, search_value: Any, column: int = 0) -> Optional[int]:
        """특정 열에서 값을 찾아 행 번호 반환 (0-based)."""
        for i, row in enumerate(self.values):
            if len(row) > column and row[column] == search_value:
                return i
        return None
    
    def find_column_by_value(self, search_value: Any, row: int = 0) -> Optional[int]:
        """특정 행에서 값을 찾아 열 번호 반환 (0-based)."""
        if row < len(self.values):
            target_row = self.values[row]
            try:
                return target_row.index(search_value)
            except ValueError:
                return None
        return None


@dataclass
class ParticipantStatus:
    """참여자의 출석 현황을 나타내는 데이터 클래스."""
    
    name: str
    week_statuses: List[str]  # ["O", "X", "O", ...] 형태
    
    def __post_init__(self) -> None:
        """참여자 상태 데이터 유효성 검사."""
        if not self.name.strip():
            raise ValueError("참여자 이름이 비어있습니다")
        
        if not self.week_statuses:
            self.week_statuses = []
    
    @property
    def total_weeks(self) -> int:
        """전체 주차 수 반환."""
        return len(self.week_statuses)
    
    @property
    def attended_weeks(self) -> int:
        """출석한 주차 수 반환."""
        return sum(1 for status in self.week_statuses if status == "O")
    
    @property
    def attendance_rate(self) -> float:
        """출석률 계산 (0.0 ~ 1.0)."""
        if self.total_weeks == 0:
            return 0.0
        return self.attended_weeks / self.total_weeks
    
    def get_week_status(self, week: int) -> Optional[str]:
        """특정 주차의 출석 상태 반환 (1-based 인덱스)."""
        if 1 <= week <= len(self.week_statuses):
            return self.week_statuses[week - 1]
        return None
    
    def update_week_status(self, week: int, status: str) -> None:
        """특정 주차의 출석 상태 업데이트 (1-based 인덱스)."""
        if week < 1:
            raise ValueError("주차는 1 이상이어야 합니다")
        
        # 필요하면 리스트 크기 확장
        while len(self.week_statuses) < week:
            self.week_statuses.append("X")
        
        self.week_statuses[week - 1] = status