#!/usr/bin/env python3
"""네이버 카페 HTML 구조 분석 도구."""

import asyncio
from playwright.async_api import async_playwright

async def analyze_cafe_structure():
    """카페 페이지의 HTML 구조를 분석합니다."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 쿠키 로드 (기존 로그인 상태)
        try:
            import json
            with open('data/naver_cookies.json', 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("쿠키 로드 성공")
        except:
            print("쿠키 로드 실패 - 로그인 필요할 수 있음")
        
        # 카페 페이지 이동
        cafe_url = "https://cafe.naver.com/westudyssat"
        board_id = "180"
        board_url = f"{cafe_url}/{board_id}?page=1"
        
        print(f"페이지 이동: {board_url}")
        await page.goto(board_url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # iframe 확인
        iframe_element = await page.query_selector("#cafe_main")
        if iframe_element:
            frame = await iframe_element.content_frame()
            if frame:
                print("iframe 구조 발견 - iframe 내부 사용")
                target_frame = frame
            else:
                print("iframe 요소 있지만 content_frame 없음 - 직접 사용")
                target_frame = page
        else:
            print("iframe 없음 - 페이지 직접 사용")
            target_frame = page
        
        # 게시글 목록 찾기
        selectors = [
            ".article-board tbody tr",
        ]
        
        for selector in selectors:
            elements = await target_frame.query_selector_all(selector)
            if elements:
                print(f"\n선택자 '{selector}': {len(elements)}개 요소 발견")
                
                # 첫 번째 요소의 HTML 구조 확인
                if len(elements) > 0:
                    first_element = elements[0]
                    html_content = await first_element.inner_html()
                    print(f"첫 번째 요소 HTML:\n{html_content}")
                    
                    # a.article 선택자 테스트
                    article_link = await first_element.query_selector("a.article")
                    if article_link:
                        title = await article_link.inner_text()
                        href = await article_link.get_attribute("href")
                        print(f"\n✅ a.article 선택자 성공!")
                        print(f"제목: {title}")
                        print(f"링크: {href}")
                        
                        # 게시글 ID 추출 테스트
                        import re
                        if href:
                            match = re.search(r'articles/(\d+)', href)
                            if match:
                                post_id = match.group(1)
                                print(f"게시글 ID: {post_id}")
                    else:
                        print("❌ a.article 선택자로 요소를 찾을 수 없음")
                        
                        # 대안 선택자들 테스트
                        test_selectors = [".article", "a", "a[href*='articles']"]
                        for test_sel in test_selectors:
                            test_elem = await first_element.query_selector(test_sel)
                            if test_elem:
                                test_text = await test_elem.inner_text()
                                test_href = await test_elem.get_attribute("href")
                                print(f"  - {test_sel}: {test_text[:30]}... | href: {test_href}")
                    
                break
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_cafe_structure())