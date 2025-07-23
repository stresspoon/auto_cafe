"""네이버 카페 크롤링 서비스 모듈."""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

from ..core.logger import get_logger, log_execution_time
from ..core.exceptions import NaverCrawlerError, LoginFailedError, CrawlingError
from .models import NaverPost


class NaverCrawlerService:
    """네이버 카페 자동 로그인 및 게시글 크롤링을 담당하는 서비스."""
    
    def __init__(self, naver_id: str, naver_password: str) -> None:
        """네이버 로그인 정보로 크롤러 서비스 초기화."""
        self._naver_id = naver_id
        self._naver_password = naver_password
        self._logger = get_logger(__name__)
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._cookies_path = Path("data/naver_cookies.json")
    
    @log_execution_time
    async def initialize_browser(self) -> None:
        """Playwright 브라우저를 초기화하고 설정."""
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self._page = await self._browser.new_page()
            
            # User-Agent 설정으로 봇 탐지 회피
            await self._page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            self._logger.info("브라우저 초기화 완료")
            
        except Exception as e:
            raise NaverCrawlerError(f"브라우저 초기화 실패: {str(e)}")
    
    @log_execution_time
    async def login_to_naver(self, max_retries: int = 3) -> bool:
        """네이버에 자동 로그인 수행."""
        if not self._page:
            raise NaverCrawlerError("브라우저가 초기화되지 않았습니다")
        
        # 저장된 쿠키로 먼저 로그인 시도
        if await self._try_login_with_cookies():
            return True
        
        # 쿠키 로그인 실패 시 일반 로그인 진행
        for attempt in range(max_retries):
            try:
                self._logger.info(f"네이버 로그인 시도 {attempt + 1}/{max_retries}")
                
                # 네이버 로그인 페이지로 이동
                await self._page.goto("https://nid.naver.com/nidlogin.login", wait_until="networkidle")
                
                # 로그인 정보 입력
                await self._page.fill("#id", self._naver_id)
                await self._page.fill("#pw", self._naver_password)
                
                # 로그인 버튼 클릭
                await self._page.click("#log\\.login")
                
                # 로그인 결과 대기 및 확인
                await self._page.wait_for_load_state("networkidle", timeout=10000)
                
                # 로그인 성공 여부 확인
                if await self._verify_login_success():
                    await self._save_cookies()
                    self._logger.info("네이버 로그인 성공")
                    return True
                else:
                    self._logger.warning(f"로그인 시도 {attempt + 1} 실패")
                    
            except Exception as e:
                self._logger.error(f"로그인 시도 {attempt + 1} 중 오류: {str(e)}")
                if attempt == max_retries - 1:
                    raise LoginFailedError(f"네이버 로그인 {max_retries}회 모두 실패: {str(e)}")
        
        return False
    
    @log_execution_time
    async def crawl_cafe_posts(
        self, 
        cafe_url: str, 
        board_id: str, 
        pages: int = 3
    ) -> List[NaverPost]:
        """지정된 카페 게시판에서 게시글 목록을 크롤링."""
        if not self._page:
            raise NaverCrawlerError("브라우저가 초기화되지 않았습니다")
        
        posts = []
        
        try:
            # 1단계: 게시글 목록 수집
            for page_num in range(1, pages + 1):
                page_posts = await self._crawl_single_page(cafe_url, board_id, page_num)
                posts.extend(page_posts)
                
                self._logger.info(f"페이지 {page_num} 크롤링 완료: {len(page_posts)}개 게시글")
            
            # 2단계: 각 게시글의 상세 내용 가져오기
            self._logger.info(f"총 {len(posts)}개 게시글의 상세 내용 크롤링 시작")
            
            for i, post in enumerate(posts):
                if post.post_url:
                    content = await self._get_post_content(post.post_url)
                    if content:
                        post.content = content
                        self._logger.debug(f"게시글 {i+1}/{len(posts)} 내용 수집 완료")
                    else:
                        self._logger.warning(f"게시글 {post.post_id} 내용 수집 실패")
                
                # 너무 빠른 요청 방지
                if i < len(posts) - 1:
                    await self._page.wait_for_timeout(500)
            
            # 중복 제거 (post_id 기준)
            unique_posts = self._remove_duplicate_posts(posts)
            
            # 챌린지 게시글만 필터링
            challenge_posts = [post for post in unique_posts if post.is_challenge_post]
            self._logger.info(f"전체 크롤링 완료: 총 {len(posts)}개 → 중복 제거 후 {len(unique_posts)}개 → 챌린지 게시글 {len(challenge_posts)}개")
            
            return unique_posts
            
        except Exception as e:
            raise CrawlingError(f"게시글 크롤링 중 오류 발생: {str(e)}")
    
    async def _crawl_single_page(
        self, 
        cafe_url: str, 
        board_id: str, 
        page_num: int
    ) -> List[NaverPost]:
        """단일 페이지의 게시글을 크롤링."""
        from datetime import datetime
        
        posts = []
        
        try:
            # 카페 게시판 페이지 URL 생성 (새로운 형태)
            board_url = f"{cafe_url}/{board_id}?page={page_num}"
            
            # 페이지로 이동
            await self._page.goto(board_url, wait_until="networkidle")
            await self._page.wait_for_timeout(2000)  # 페이지 로드 대기
            
            # 현재 페이지에서 직접 요소 찾기 (iframe 사용하지 않음)
            frame = self._page
            
            # iframe 구조가 있는지 먼저 확인
            iframe_element = await self._page.query_selector("#cafe_main")
            if iframe_element:
                inner_frame = await iframe_element.content_frame()
                if inner_frame:
                    frame = inner_frame
                    self._logger.info("iframe 구조를 사용합니다")
                else:
                    self._logger.info("iframe이 있지만 content_frame을 사용할 수 없습니다. 직접 접근합니다.")
            else:
                self._logger.info("iframe 구조가 없습니다. 직접 접근합니다.")
            
            # 게시글 목록 수집 (다양한 선택자 시도)
            post_elements = []
            
            # 최신 네이버 카페 구조 시도
            selectors = [
                ".article-board tbody tr",  # 기존 구조
                ".ArticleItem",  # 새로운 구조 1
                ".post-item",    # 새로운 구조 2
                "[data-article-id]",  # data attribute 기반
                "article",       # semantic HTML
                ".list-item"     # 일반적인 목록
            ]
            
            for selector in selectors:
                post_elements = await frame.query_selector_all(selector)
                if post_elements:
                    self._logger.info(f"게시글 요소를 찾았습니다 (선택자: {selector}, 개수: {len(post_elements)})")
                    break
            
            if not post_elements:
                self._logger.warning("게시글 요소를 찾을 수 없습니다. 페이지 구조를 확인합니다.")
                
                # 페이지의 모든 텍스트 내용 확인 (디버깅용)
                page_content = await frame.inner_text("body")
                if "westudyssat" in page_content.lower():
                    self._logger.info("카페 페이지로 접근했지만 게시글 구조를 인식하지 못했습니다.")
                else:
                    self._logger.error("카페 페이지로 접근하지 못했을 수 있습니다.")
                
                return posts
            
            for idx, post_element in enumerate(post_elements):  # 모든 게시글 처리
                try:
                    # 공지사항 등 제외 (더 관대하게 처리)
                    is_notice = await post_element.get_attribute("class")
                    self._logger.info(f"게시글 {idx+1}: class = {is_notice}")
                    
                    # 공지사항 체크 활성화
                    if is_notice and "notice" in is_notice.lower():
                        self._logger.info(f"게시글 {idx+1}: 공지사항으로 건너뜀 (class: {is_notice})")
                        continue
                    
                    # 기본 텍스트 확인
                    element_text = await post_element.inner_text()
                    self._logger.info(f"게시글 {idx+1} 텍스트: {element_text[:100]}...")
                    
                    # 게시글 ID 추출 (스크린샷 기반 정확한 구조)
                    # 테이블의 첫 번째 열에서 게시글 번호 추출
                    post_id_selectors = [
                        "td:first-child",             # 첫 번째 td (가장 가능성 높음)
                        ".td_num",                    # 번호 전용 클래스가 있을 경우
                        ".board-number"               # 기존 선택자
                    ]
                    
                    post_id = "unknown"
                    for selector in post_id_selectors:
                        post_id_elem = await post_element.query_selector(selector)
                        if post_id_elem:
                            post_id_text = await post_id_elem.inner_text()
                            post_id = post_id_text.strip()
                            if post_id and post_id.isdigit():
                                break
                    
                    # href에서 게시글 ID 추출 (실제 구조 기반)
                    if post_id == "unknown":
                        link_elem = await post_element.query_selector("a.article")
                        if link_elem:
                            href = await link_elem.get_attribute("href")
                            if href:
                                import re
                                # 실제 형태: articleid=1403 패턴에서 ID 추출
                                if "articleid=" in href:
                                    match = re.search(r'articleid=(\d+)', href)
                                    if match:
                                        post_id = match.group(1)
                                # 백업으로 articles/2667 패턴도 체크
                                elif "articles/" in href:
                                    match = re.search(r'articles/(\d+)', href)
                                    if match:
                                        post_id = match.group(1)
                    
                    self._logger.info(f"게시글 {idx+1}: ID = {post_id}")
                    
                    # 제목 추출 (개발자 도구 기반 정확한 선택자)
                    title_selectors = [
                        "a.article",                 # a태그에 article 클래스 (정확한 선택자!)
                        ".article",                  # article 클래스 직접
                        "a[href*='articles']",       # articles가 포함된 링크
                        "td:nth-child(2) a",         # 두 번째 td의 링크
                        "a[href*='ArticleRead']"     # 기존 선택자
                    ]
                    
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = await post_element.query_selector(selector)
                        if title_elem:
                            break
                    
                    if not title_elem:
                        self._logger.warning(f"게시글 {idx+1}에서 제목을 찾을 수 없습니다")
                        continue
                    title = await title_elem.inner_text()
                    title = title.strip()
                    self._logger.info(f"게시글 {idx+1} - ID: {post_id}, 제목: {title[:50]}...")
                    
                    # 작성자 추출 (스크린샷 기반 - 세 번째 열에 작성자가 있음)
                    author_selectors = [
                        "td:nth-child(3) a",         # 세 번째 td의 링크 (가장 가능성 높음)
                        "td:nth-child(3)",           # 세 번째 td 자체
                        ".td_name .p-nick a",        # 기존 선택자
                        ".p-nick a",                 # 직접 선택자
                        ".writer",                   # 일반적인 작성자
                        ".author"                    # 작성자
                    ]
                    
                    author_elem = None
                    for selector in author_selectors:
                        author_elem = await post_element.query_selector(selector)
                        if author_elem:
                            break
                    
                    if not author_elem:
                        self._logger.warning(f"게시글 {idx+1}에서 작성자를 찾을 수 없습니다 - 제목에서 추출 시도")
                        # 제목에서 이름 추출 시도
                        from src.shared.utils import extract_name_from_title
                        extracted_name = extract_name_from_title(title)
                        author = extracted_name if extracted_name else "unknown_author"
                        if extracted_name:
                            self._logger.info(f"게시글 {idx+1}: 제목에서 이름 추출 성공 - {extracted_name}")
                    else:
                        author = await author_elem.inner_text()
                    
                    # 작성일 추출 (스크린샷 기준 네 번째 열)
                    date_selectors = [
                        "td:nth-child(4)",           # 네 번째 td (날짜 열)
                        ".td_date"                   # 기존 선택자
                    ]
                    
                    created_at = datetime.now()  # 기본값
                    for selector in date_selectors:
                        date_elem = await post_element.query_selector(selector)
                        if date_elem:
                            date_str = await date_elem.inner_text()
                            try:
                                created_at = self._parse_date(date_str)
                                break
                            except:
                                continue
                    
                    # 게시글 URL 추출 (title_elem에서 href 가져오기)
                    post_url = None
                    if title_elem:
                        href = await title_elem.get_attribute("href")
                        if href:
                            if href.startswith("http"):
                                post_url = href
                            elif href.startswith("/"):
                                post_url = f"https://cafe.naver.com{href}"
                            else:
                                post_url = f"https://cafe.naver.com/{href}"
                    
                    # 조회수 추출 (스크린샷 기준 다섯 번째 열)
                    view_selectors = [
                        "td:nth-child(5)",           # 다섯 번째 td (조회수 열)
                        ".td_view"                   # 기존 선택자
                    ]
                    
                    view_count = None
                    for selector in view_selectors:
                        view_elem = await post_element.query_selector(selector)
                        if view_elem:
                            view_text = await view_elem.inner_text()
                            try:
                                view_count = int(view_text.strip())
                                break
                            except ValueError:
                                continue
                    
                    # NaverPost 객체 생성 (content는 상세 페이지에서 가져와야 함)
                    post = NaverPost(
                        title=title,
                        author=author,
                        content="",  # 나중에 상세 페이지에서 채워야 함
                        post_id=post_id,
                        created_at=created_at,
                        post_url=post_url,
                        view_count=view_count
                    )
                    
                    posts.append(post)
                    self._logger.info(f"게시글 수집 성공: {post.post_id} - {post.title[:30]}... (작성자: {post.author})")
                    
                except Exception as e:
                    self._logger.error(f"게시글 {idx+1} 파싱 중 오류: {str(e)}")
                    import traceback
                    self._logger.debug(f"상세 오류: {traceback.format_exc()}")
                    continue
            
            self._logger.info(f"페이지 {page_num}에서 {len(posts)}개 게시글 수집")
            
        except Exception as e:
            self._logger.error(f"페이지 {page_num} 크롤링 중 오류: {str(e)}")
        
        return posts
    
    def _extract_cafe_id(self, cafe_url: str) -> str:
        """카페 URL에서 카페 ID 추출."""
        import re
        match = re.search(r'cafe\.naver\.com/([^/?]+)', cafe_url)
        return match.group(1) if match else ""
    
    def _parse_date(self, date_str: str) -> 'datetime':
        """날짜 문자열을 datetime 객체로 변환."""
        from datetime import datetime
        import re
        
        # "2024.01.15." 형식
        if '.' in date_str:
            date_str = date_str.strip('.')
            try:
                return datetime.strptime(date_str, "%Y.%m.%d")
            except ValueError:
                pass
        
        # "01.15." 형식 (올해)
        if re.match(r'^\d{2}\.\d{2}\.$', date_str):
            current_year = datetime.now().year
            date_str = f"{current_year}.{date_str}"
            try:
                return datetime.strptime(date_str.strip('.'), "%Y.%m.%d")
            except ValueError:
                pass
        
        # "12:34" 형식 (오늘)
        if ':' in date_str and '.' not in date_str:
            today = datetime.now()
            try:
                time_parts = date_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                return today.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except (ValueError, IndexError):
                pass
        
        # 파싱 실패 시 현재 시간 반환
        return datetime.now()
    
    async def _get_post_content(self, post_url: str) -> Optional[str]:
        """게시글 상세 페이지에서 본문 내용을 가져오기."""
        try:
            # 게시글 상세 페이지로 이동
            await self._page.goto(post_url, wait_until="networkidle")
            await self._page.wait_for_timeout(1000)
            
            # iframe으로 전환
            iframe_element = await self._page.query_selector("#cafe_main")
            if not iframe_element:
                self._logger.error("상세 페이지 iframe을 찾을 수 없습니다")
                return None
            
            frame = await iframe_element.content_frame()
            if not frame:
                self._logger.error("상세 페이지 iframe content를 찾을 수 없습니다")
                return None
            
            # 본문 내용 추출
            content_selectors = [
                ".se-main-container",  # 스마트에디터 ONE
                ".ContentRenderer",     # 새로운 에디터
                "#postViewArea",       # 구 에디터
                ".NHN_Writeform_Main", # 구 에디터2
                ".content.CafeViewer"  # 모바일 에디터
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = await frame.query_selector(selector)
                if content_elem:
                    content = await content_elem.inner_text()
                    if content.strip():
                        break
            
            return content.strip()
            
        except Exception as e:
            self._logger.error(f"게시글 내용 가져오기 중 오류: {str(e)}")
            return None
    
    def _remove_duplicate_posts(self, posts: List[NaverPost]) -> List[NaverPost]:
        """중복 게시글 제거 (post_id 기준)."""
        seen_ids = set()
        unique_posts = []
        
        for post in posts:
            if post.post_id not in seen_ids:
                seen_ids.add(post.post_id)
                unique_posts.append(post)
            else:
                self._logger.debug(f"중복 게시글 제거: ID={post.post_id}, 제목={post.title}")
        
        if len(posts) != len(unique_posts):
            self._logger.info(f"중복 게시글 {len(posts) - len(unique_posts)}개 제거됨")
        
        return unique_posts
    
    async def close(self) -> None:
        """브라우저 리소스 정리."""
        try:
            if self._browser:
                await self._browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
            
            self._logger.info("브라우저 리소스 정리 완료")
            
        except Exception as e:
            self._logger.error(f"브라우저 종료 중 오류 발생: {str(e)}")
    
    async def _try_login_with_cookies(self) -> bool:
        """저장된 쿠키를 사용하여 로그인 시도."""
        if not self._cookies_path.exists():
            self._logger.info("저장된 쿠키가 없습니다")
            return False
        
        try:
            with open(self._cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            await self._page.context.add_cookies(cookies)
            await self._page.goto("https://www.naver.com", wait_until="networkidle")
            
            if await self._verify_login_success():
                self._logger.info("쿠키를 사용한 자동 로그인 성공")
                return True
            else:
                self._logger.info("저장된 쿠키가 만료되었습니다")
                return False
                
        except Exception as e:
            self._logger.warning(f"쿠키 로그인 시도 중 오류: {str(e)}")
            return False
    
    async def _verify_login_success(self) -> bool:
        """로그인 성공 여부를 확인."""
        try:
            # 네이버 메인페이지로 이동하여 로그인 상태 확인
            await self._page.goto("https://www.naver.com", wait_until="networkidle")
            
            # 로그인된 사용자의 프로필 영역 확인
            profile_selector = ".MyView-module__link_login___HpHMW, .area_links .link_login"
            login_button_selector = ".link_login"
            
            # 로그인 버튼이 있으면 로그인 실패
            login_button = await self._page.query_selector(login_button_selector)
            if login_button:
                return False
            
            # 프로필 영역이 있으면 로그인 성공
            profile = await self._page.query_selector(profile_selector)
            return profile is not None
            
        except Exception as e:
            self._logger.error(f"로그인 확인 중 오류: {str(e)}")
            return False
    
    async def _save_cookies(self) -> None:
        """현재 세션의 쿠키를 저장."""
        try:
            # data 디렉토리가 없으면 생성
            self._cookies_path.parent.mkdir(exist_ok=True)
            
            cookies = await self._page.context.cookies()
            with open(self._cookies_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            self._logger.info(f"쿠키를 {self._cookies_path}에 저장했습니다")
            
        except Exception as e:
            self._logger.error(f"쿠키 저장 중 오류: {str(e)}")