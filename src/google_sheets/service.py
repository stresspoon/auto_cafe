"""구글 시트 연동 서비스 모듈."""

from typing import List, Dict, Any, Optional, Tuple
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError

from ..core.logger import get_logger, log_execution_time
from ..core.exceptions import GoogleSheetsError, AuthenticationError, SheetUpdateError
from .models import SheetUpdateRequest, SheetData


class GoogleSheetsService:
    """구글 시트 API를 통한 시트 읽기/쓰기를 담당하는 서비스."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, credentials_path: str, sheet_id: str) -> None:
        """구글 API 인증 정보와 시트 ID로 서비스 초기화."""
        self._credentials_path = credentials_path
        self._sheet_id = sheet_id
        self._logger = get_logger(__name__)
        self._service = None
    
    @log_execution_time
    def authenticate(self) -> None:
        """구글 API 서비스 계정으로 인증."""
        try:
            credentials = Credentials.from_service_account_file(
                self._credentials_path, 
                scopes=self.SCOPES
            )
            
            self._service = build('sheets', 'v4', credentials=credentials)
            self._logger.info("구글 시트 API 인증 완료")
            
        except FileNotFoundError:
            raise AuthenticationError(f"인증 파일을 찾을 수 없습니다: {self._credentials_path}")
        except GoogleAuthError as e:
            raise AuthenticationError(f"구글 API 인증 실패: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"인증 중 예상치 못한 오류 발생: {str(e)}")
    
    @log_execution_time
    def read_sheet_data(self, range_name: str) -> SheetData:
        """지정된 범위의 시트 데이터를 읽어오기."""
        if not self._service:
            raise GoogleSheetsError("구글 시트 API 서비스가 인증되지 않았습니다")
        
        try:
            result = self._service.spreadsheets().values().get(
                spreadsheetId=self._sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            self._logger.info(f"시트 데이터 읽기 완료: {len(values)}행")
            
            return SheetData(range_name=range_name, values=values)
            
        except Exception as e:
            raise GoogleSheetsError(f"시트 데이터 읽기 실패: {str(e)}")
    
    @log_execution_time
    def update_sheet_data(self, updates: List[SheetUpdateRequest]) -> bool:
        """여러 셀을 배치 업데이트."""
        if not self._service:
            raise GoogleSheetsError("구글 시트 API 서비스가 인증되지 않았습니다")
        
        if not updates:
            self._logger.warning("업데이트할 데이터가 없습니다")
            return True
        
        try:
            # 배치 업데이트 요청 구성
            batch_update_values = []
            for update in updates:
                batch_update_values.append({
                    'range': update.range_name,
                    'values': update.values
                })
            
            body = {
                'valueInputOption': 'RAW',
                'data': batch_update_values
            }
            
            result = self._service.spreadsheets().values().batchUpdate(
                spreadsheetId=self._sheet_id,
                body=body
            ).execute()
            
            updated_cells = result.get('totalUpdatedCells', 0)
            self._logger.info(f"시트 배치 업데이트 완료: {updated_cells}개 셀 업데이트")
            
            return True
            
        except Exception as e:
            raise SheetUpdateError(f"시트 업데이트 실패: {str(e)}")
    
    @log_execution_time
    def update_attendance_status(
        self, 
        participant_name: str, 
        week_number: int, 
        status: str = "O"
    ) -> bool:
        """참여자의 특정 주차 출석 상태를 업데이트."""
        # TODO: 실제 시트 구조에 맞는 셀 위치 계산 로직 필요
        # 현재는 스켈레톤 구현
        
        try:
            # 참여자 행과 주차 열을 찾아서 해당 셀에 상태 업데이트
            cell_range = self._find_cell_position(participant_name, week_number)
            
            if cell_range:
                update_request = SheetUpdateRequest(
                    range_name=cell_range,
                    values=[[status]]
                )
                
                return self.update_sheet_data([update_request])
            else:
                self._logger.warning(f"참여자 '{participant_name}', {week_number}주차 셀 위치를 찾을 수 없습니다")
                return False
                
        except Exception as e:
            raise SheetUpdateError(f"출석 상태 업데이트 실패: {str(e)}")
    
    def _find_cell_position(self, participant_name: str, week_number: int) -> Optional[str]:
        """참여자 이름과 주차 번호로 해당 셀의 위치를 찾기."""
        # TODO: 실제 시트 레이아웃에 맞춰 구현 필요
        # 예시: A열에 참여자 이름, 1행에 주차 정보가 있다고 가정
        self._logger.info(f"셀 위치 찾기 시도: {participant_name}, {week_number}주차 (구현 예정)")
        return None
    
    def get_participants_list(self) -> List[str]:
        """시트에서 참여자 목록을 가져오기."""
        # TODO: 실제 시트 구조에 맞춰 구현 필요
        self._logger.info("참여자 목록 가져오기 (구현 예정)")
        return []