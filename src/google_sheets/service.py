"""구글 시트 연동 서비스 모듈."""

import time
from typing import List, Dict, Any, Optional, Tuple, Set
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError

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
    def update_sheet_data(self, updates: List[SheetUpdateRequest], max_retries: int = 3) -> bool:
        """여러 셀을 배치 업데이트 (재시도 로직 포함)."""
        if not self._service:
            raise GoogleSheetsError("구글 시트 API 서비스가 인증되지 않았습니다")
        
        if not updates:
            self._logger.warning("업데이트할 데이터가 없습니다")
            return True
        
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
        
        # 지수 백오프로 재시도
        for attempt in range(max_retries):
            try:
                result = self._service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self._sheet_id,
                    body=body
                ).execute()
                
                updated_cells = result.get('totalUpdatedCells', 0)
                self._logger.info(f"시트 배치 업데이트 완료: {updated_cells}개 셀 업데이트")
                
                return True
                
            except HttpError as e:
                if e.resp.status in [429, 503, 500]:  # 재시도 가능한 오류
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt, 5)  # 최대 5초
                        self._logger.warning(f"API 오류로 {wait_time}초 후 재시도 ({attempt + 1}/{max_retries}): {e.resp.status}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise SheetUpdateError(f"시트 업데이트 재시도 횟수 초과: {str(e)}")
                else:
                    raise SheetUpdateError(f"시트 업데이트 실패: {str(e)}")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 5)
                    self._logger.warning(f"예상치 못한 오류로 {wait_time}초 후 재시도 ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise SheetUpdateError(f"시트 업데이트 실패: {str(e)}")
        
        return False
    
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
        try:
            # 전체 시트 데이터 읽기 (헤더와 참여자 목록 포함)
            sheet_data = self.read_sheet_data("A:Z")  # 충분히 큰 범위
            
            if not sheet_data.values:
                self._logger.warning("시트에 데이터가 없습니다")
                return None
            
            # 헤더 행에서 주차 열 찾기 (첫 번째 행)
            week_column = None
            header_row = sheet_data.values[0]
            for col_idx, cell_value in enumerate(header_row):
                if str(cell_value).strip() == f"{week_number}주차":
                    week_column = col_idx
                    break
            
            if week_column is None:
                self._logger.warning(f"{week_number}주차 열을 찾을 수 없습니다")
                return None
            
            # 참여자 행 찾기 (A열에서 검색)
            participant_row = None
            for row_idx in range(1, len(sheet_data.values)):  # 헤더 제외
                if sheet_data.values[row_idx] and sheet_data.values[row_idx][0] == participant_name:
                    participant_row = row_idx
                    break
            
            if participant_row is None:
                self._logger.warning(f"참여자 '{participant_name}'를 찾을 수 없습니다")
                return None
            
            # 셀 위치 계산 (1-based 인덱스를 A1 표기법으로 변환)
            col_letter = self._column_number_to_letter(week_column + 1)
            cell_position = f"{col_letter}{participant_row + 1}"
            
            self._logger.debug(f"셀 위치 찾기 성공: {participant_name}, {week_number}주차 -> {cell_position}")
            return cell_position
            
        except Exception as e:
            self._logger.error(f"셀 위치 찾기 중 오류: {str(e)}")
            return None
    
    def _column_number_to_letter(self, col_num: int) -> str:
        """열 번호를 알파벳으로 변환 (1=A, 2=B, ..., 26=Z, 27=AA)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(col_num % 26 + ord('A')) + result
            col_num //= 26
        return result
    
    def get_participants_list(self) -> List[str]:
        """시트에서 참여자 목록을 가져오기."""
        try:
            # A열에서 참여자 목록 읽기 (헤더 제외)
            sheet_data = self.read_sheet_data("A:A")
            
            if not sheet_data.values or len(sheet_data.values) <= 1:
                self._logger.warning("시트에 참여자 데이터가 없습니다")
                return []
            
            # 첫 번째 행(헤더) 제외하고 참여자 이름만 추출
            participants = []
            for row in sheet_data.values[1:]:  # 헤더 제외
                if row and row[0] and str(row[0]).strip():  # 빈 셀 제외
                    participants.append(str(row[0]).strip())
            
            self._logger.info(f"참여자 목록 가져오기 완료: {len(participants)}명")
            return participants
            
        except Exception as e:
            self._logger.error(f"참여자 목록 가져오기 실패: {str(e)}")
            return []
    
    @log_execution_time
    def batch_update_attendance(self, attendance_data: Dict[str, Dict[int, str]]) -> bool:
        """참여자별 주차별 출석 현황을 배치 업데이트."""
        if not attendance_data:
            self._logger.info("업데이트할 출석 데이터가 없습니다")
            return True
        
        try:
            update_requests = []
            
            for participant_name, week_statuses in attendance_data.items():
                for week_number, status in week_statuses.items():
                    cell_position = self._find_cell_position(participant_name, week_number)
                    if cell_position:
                        update_request = SheetUpdateRequest(
                            range_name=cell_position,
                            values=[[status]]
                        )
                        update_requests.append(update_request)
                    else:
                        self._logger.warning(f"셀 위치를 찾을 수 없음: {participant_name}, {week_number}주차")
            
            if update_requests:
                success = self.update_sheet_data(update_requests)
                self._logger.info(f"배치 출석 업데이트 완료: {len(update_requests)}개 셀")
                return success
            else:
                self._logger.warning("업데이트할 유효한 셀이 없습니다")
                return False
                
        except Exception as e:
            raise SheetUpdateError(f"배치 출석 업데이트 실패: {str(e)}")
    
    @log_execution_time 
    def update_attendance_from_submissions(self, weekly_submissions: Dict[int, Set[str]]) -> bool:
        """주차별 제출자 정보를 바탕으로 출석 현황을 업데이트 (제출자만 O로 표시, 기존 데이터 보존)."""
        try:
            # 제출자만 O로 업데이트 (X 표시는 하지 않음)
            attendance_data = {}
            
            for week_number, submitters in weekly_submissions.items():
                self._logger.info(f"{week_number}주차 제출자 {len(submitters)}명 업데이트 예정: {list(submitters)}")
                
                for submitter in submitters:
                    if submitter not in attendance_data:
                        attendance_data[submitter] = {}
                    attendance_data[submitter][week_number] = "O"
            
            # 배치 업데이트 실행 (제출자만)
            if attendance_data:
                success = self.batch_update_attendance(attendance_data)
                if success:
                    total_updates = sum(len(weeks) for weeks in attendance_data.values())
                    self._logger.info(f"출석 현황 업데이트 완료: {total_updates}개 셀이 'O'로 표시됨")
                return success
            else:
                self._logger.warning("업데이트할 제출자 데이터가 없습니다")
                return True
            
        except Exception as e:
            raise SheetUpdateError(f"제출 정보 기반 출석 업데이트 실패: {str(e)}")