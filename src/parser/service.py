"""데이터 파싱 서비스 모듈."""

import re
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from ..core.logger import get_logger, log_execution_time
from ..core.exceptions import ParsingError
from ..naver_crawler.models import NaverPost
from ..shared.utils import extract_week_number, get_kst_now


class DataParsingService:
    """게시글 데이터에서 주차 정보 및 작성자를 추출하는 서비스."""
    
    def __init__(self) -> None:
        """데이터 파싱 서비스 초기화."""
        self._logger = get_logger(__name__)
        self._week_pattern = re.compile(r'\*?(\d+)\s*주차')
        self._author_pattern = re.compile(r'[a-zA-Z0-9가-힣_]+')
    
    @log_execution_time
    def extract_weekly_submissions(
        self, 
        posts: List[NaverPost]
    ) -> Dict[int, Set[str]]:
        """게시글 목록에서 주차별 제출자 정보를 추출."""
        weekly_submissions = {}
        
        try:
            for post in posts:
                week_number = self._extract_week_from_post(post)
                if week_number:
                    author = self._normalize_author_name(post.author)
                    
                    if week_number not in weekly_submissions:
                        weekly_submissions[week_number] = set()
                    
                    weekly_submissions[week_number].add(author)
                    
                    self._logger.debug(f"주차별 제출 추가: {author} -> {week_number}주차")
            
            total_submissions = sum(len(authors) for authors in weekly_submissions.values())
            self._logger.info(
                f"주차별 제출 정보 추출 완료: "
                f"{len(weekly_submissions)}개 주차, 총 {total_submissions}건"
            )
            
            # 디버깅을 위해 실제 데이터 출력
            for week, authors in weekly_submissions.items():
                self._logger.info(f"  {week}주차 제출자: {list(authors)}")
            
            return weekly_submissions
            
        except Exception as e:
            raise ParsingError(f"주차별 제출 정보 추출 중 오류 발생: {str(e)}")
    
    @log_execution_time
    def filter_challenge_posts(self, posts: List[NaverPost]) -> List[NaverPost]:
        """챌린지 관련 게시글만 필터링."""
        challenge_posts = []
        
        try:
            for post in posts:
                if self._is_challenge_post(post):
                    challenge_posts.append(post)
            
            self._logger.info(
                f"챌린지 게시글 필터링 완료: "
                f"전체 {len(posts)}개 중 {len(challenge_posts)}개 추출"
            )
            
            return challenge_posts
            
        except Exception as e:
            raise ParsingError(f"챌린지 게시글 필터링 중 오류 발생: {str(e)}")
    
    def _extract_week_from_post(self, post: NaverPost) -> Optional[int]:
        """게시글에서 주차 번호 추출."""
        # 제목에서 먼저 검색
        week_from_title = extract_week_number(post.title)
        if week_from_title:
            return week_from_title
        
        # 내용에서 검색
        week_from_content = extract_week_number(post.content)
        return week_from_content
    
    def _is_challenge_post(self, post: NaverPost) -> bool:
        """게시글이 챌린지 관련인지 판단."""
        # 주차 키워드가 있으면 챌린지 게시글로 판단
        if self._extract_week_from_post(post):
            return True
        
        # 추가 키워드 검사 (필요시)
        challenge_keywords = ['챌린지', '미션', '과제', '인증']
        combined_text = f"{post.title} {post.content}".lower()
        
        return any(keyword in combined_text for keyword in challenge_keywords)
    
    def _normalize_author_name(self, author: str) -> str:
        """작성자 이름을 정규화 (공백 제거, 특수문자 처리 등)."""
        # 기본적인 정규화: 공백 제거, 소괄호 내용 제거
        normalized = author.strip()
        normalized = re.sub(r'\([^)]*\)', '', normalized).strip()
        
        return normalized
    
    @log_execution_time
    def generate_attendance_report(
        self, 
        weekly_submissions: Dict[int, Set[str]],
        all_participants: List[str]
    ) -> Dict[str, Dict[int, str]]:
        """참여자별 주차별 출석 현황 리포트 생성."""
        attendance_report = {}
        
        try:
            for participant in all_participants:
                normalized_participant = self._normalize_author_name(participant)
                attendance_report[normalized_participant] = {}
                
                # 모든 주차에 대해 출석 여부 확인
                all_weeks = sorted(weekly_submissions.keys()) if weekly_submissions else []
                
                for week in all_weeks:
                    if normalized_participant in weekly_submissions.get(week, set()):
                        attendance_report[normalized_participant][week] = "O"
                    else:
                        attendance_report[normalized_participant][week] = "X"
            
            self._logger.info(
                f"출석 현황 리포트 생성 완료: "
                f"{len(all_participants)}명, {len(all_weeks)}주차"
            )
            
            return attendance_report
            
        except Exception as e:
            raise ParsingError(f"출석 현황 리포트 생성 중 오류 발생: {str(e)}")
    
    def get_recent_posts_only(
        self, 
        posts: List[NaverPost], 
        days_threshold: int = 7
    ) -> List[NaverPost]:
        """최근 N일 내 게시글만 필터링."""
        try:
            threshold_date = get_kst_now() - timedelta(days=days_threshold)
            recent_posts = [
                post for post in posts 
                if post.created_at >= threshold_date
            ]
            
            self._logger.info(
                f"최근 {days_threshold}일 게시글 필터링: "
                f"전체 {len(posts)}개 중 {len(recent_posts)}개"
            )
            
            return recent_posts
            
        except Exception as e:
            raise ParsingError(f"최근 게시글 필터링 중 오류 발생: {str(e)}")
    
    def validate_parsing_result(
        self, 
        weekly_submissions: Dict[int, Set[str]]
    ) -> bool:
        """파싱 결과의 유효성 검증."""
        try:
            # 기본 유효성 검사
            if not weekly_submissions:
                self._logger.warning("파싱 결과가 비어있습니다")
                return False
            
            # 주차 번호 유효성 검사 (1~52주차 범위)
            invalid_weeks = [week for week in weekly_submissions.keys() if week < 1 or week > 52]
            if invalid_weeks:
                self._logger.warning(f"유효하지 않은 주차 번호 발견: {invalid_weeks}")
                return False
            
            # 작성자 이름 유효성 검사
            for week, authors in weekly_submissions.items():
                invalid_authors = [
                    author for author in authors 
                    if not author or len(author.strip()) < 2
                ]
                if invalid_authors:
                    self._logger.warning(f"{week}주차에 유효하지 않은 작성자명 발견: {invalid_authors}")
                    return False
            
            self._logger.info("파싱 결과 유효성 검증 통과")
            return True
            
        except Exception as e:
            self._logger.error(f"파싱 결과 유효성 검증 중 오류 발생: {str(e)}")
            return False
    
    def extract_names_from_html_file(self, file_path: str) -> List[str]:
        """HTML 파일에서 'a.article' CSS 선택자를 사용하여 이름을 추출."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'lxml')
            article_links = soup.select('a.article')
            names = [link.get_text(strip=True) for link in article_links]
            
            self._logger.info(f"HTML 파일에서 {len(names)}개의 이름 추출 완료: {file_path}")
            return names
            
        except FileNotFoundError:
            self._logger.error(f"파일을 찾을 수 없습니다: {file_path}")
            raise ParsingError(f"파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            self._logger.error(f"HTML 파일 파싱 중 오류 발생: {str(e)}")
            raise ParsingError(f"HTML 파일 파싱 중 오류 발생: {str(e)}")
    
    def parse_week_and_name(self, text: str) -> Tuple[Optional[int], str]:
        """'1주차 김상현' 형태의 텍스트에서 주차와 이름을 분리."""
        try:
            # 주차 패턴 매칭
            week_match = self._week_pattern.search(text)
            
            if week_match:
                week_number = int(week_match.group(1))
                # 주차 부분을 제거하고 이름만 추출
                name_part = text.replace(week_match.group(0), '').strip()
                return week_number, name_part
            else:
                # 주차 정보가 없으면 전체를 이름으로 간주
                return None, text.strip()
                
        except Exception as e:
            self._logger.error(f"주차/이름 파싱 중 오류: {str(e)}")
            return None, text.strip()
    
    def extract_weekly_submissions_from_html(self, file_path: str) -> Dict[int, Set[str]]:
        """HTML 파일에서 주차별 제출자 정보를 직접 추출."""
        try:
            raw_names = self.extract_names_from_html_file(file_path)
            weekly_submissions = {}
            
            for raw_name in raw_names:
                week_number, name = self.parse_week_and_name(raw_name)
                
                if week_number and name:
                    if week_number not in weekly_submissions:
                        weekly_submissions[week_number] = set()
                    
                    # 이름 정규화
                    normalized_name = self._normalize_author_name(name)
                    weekly_submissions[week_number].add(normalized_name)
                    
                    self._logger.debug(f"HTML에서 추출: {normalized_name} -> {week_number}주차")
            
            self._logger.info(f"HTML에서 주차별 제출자 추출 완료: {len(weekly_submissions)}개 주차")
            return weekly_submissions
            
        except Exception as e:
            raise ParsingError(f"HTML에서 주차별 제출자 추출 중 오류 발생: {str(e)}")