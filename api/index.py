import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles  
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Get the project root directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

app = FastAPI(title="QOK6 자동화 서비스", version="1.0.0")

# Safe environment setup
def setup_environment():
    """Safely setup environment variables without causing crashes"""
    try:
        # Google Credentials
        google_creds_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if google_creds_str:
            # Clean the JSON string
            google_creds_str = google_creds_str.replace('\n', '\\n').replace('\r', '')
            google_creds = json.loads(google_creds_str)
            
            credentials_path = '/tmp/credentials.json'
            with open(credentials_path, 'w') as f:
                json.dump(google_creds, f)
            os.environ['GOOGLE_CREDENTIALS_PATH'] = credentials_path
            
        # Naver Cookies
        naver_cookies_str = os.getenv('NAVER_COOKIES_JSON')
        if naver_cookies_str:
            naver_cookies = json.loads(naver_cookies_str)
            
            cookies_path = '/tmp/naver_cookies.json'
            with open(cookies_path, 'w') as f:
                json.dump(naver_cookies, f)
            os.environ['NAVER_COOKIES_PATH'] = cookies_path
            
        return {"status": "success", "message": "Environment setup completed"}
        
    except Exception as e:
        print(f"Environment setup error: {e}")
        return {"status": "error", "message": str(e)}

# Initialize environment
env_status = setup_environment()

# Setup static files and templates for the original web interface
try:
    static_path = project_root / "src" / "web" / "static"
    templates_path = project_root / "src" / "web" / "templates"
    
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    if templates_path.exists():
        templates = Jinja2Templates(directory=str(templates_path))
    else:
        templates = None
        
except Exception as e:
    print(f"Static files setup error: {e}")
    templates = None

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드 페이지 - 기존 웹 인터페이스 사용"""
    if templates:
        # 기존 템플릿이 있으면 사용
        try:
            # 샘플 데이터로 대시보드 렌더링
            recent_logs = [
                {
                    'execution_id': 'demo-001',
                    'started_at': datetime.now().isoformat(),
                    'success': True,
                    'message': 'Demo execution',
                    'results': {
                        'weeks_processed': 4,
                        'total_posts': 152,
                        'participants': ['user1', 'user2', 'user3']
                    }
                }
            ]
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "recent_logs": recent_logs,
                "success_rate": 85.5,
                "system_status": "healthy"
            })
            
        except Exception as e:
            print(f"Template rendering error: {e}")
            # Fall back to simple HTML
            pass
    
    # Fallback simple dashboard
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QOK6 자동화 서비스</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0; padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; margin: 0 auto; 
                background: white; padding: 30px;
                border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #333; font-size: 2.5em; margin-bottom: 10px; }
            .header p { color: #666; font-size: 1.2em; }
            .status-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }
            .status-card { 
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white; padding: 25px; border-radius: 12px;
                text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .status-card i { font-size: 3em; margin-bottom: 15px; opacity: 0.9; }
            .status-card h3 { margin: 0 0 10px 0; font-size: 1.1em; }
            .status-card .value { font-size: 2em; font-weight: bold; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .feature-card { 
                background: #f8f9fa; padding: 25px; border-radius: 10px;
                border-left: 4px solid #007bff; transition: transform 0.2s;
            }
            .feature-card:hover { transform: translateY(-5px); }
            .feature-card h3 { color: #333; margin-bottom: 15px; }
            .feature-card ul { list-style: none; padding: 0; }
            .feature-card li { padding: 8px 0; color: #666; }
            .feature-card li i { color: #007bff; margin-right: 10px; }
            .btn { 
                display: inline-block; padding: 12px 25px; margin: 10px;
                background: #007bff; color: white; text-decoration: none;
                border-radius: 25px; transition: all 0.3s;
                border: none; cursor: pointer; font-size: 1em;
            }
            .btn:hover { background: #0056b3; transform: translateY(-2px); }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #1e7e34; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-robot"></i> QOK6 자동화 서비스</h1>
                <p>네이버 카페 챌린지 미션 → 구글 시트 자동 체크</p>
            </div>
            
            <div class="status-cards">
                <div class="status-card">
                    <i class="fas fa-heartbeat"></i>
                    <h3>시스템 상태</h3>
                    <div class="value">정상 운영</div>
                </div>
                <div class="status-card">
                    <i class="fas fa-cloud"></i>
                    <h3>호스팅</h3>
                    <div class="value">Vercel</div>
                </div>
                <div class="status-card">
                    <i class="fas fa-code-branch"></i>
                    <h3>버전</h3>
                    <div class="value">v1.0.0</div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/api" class="btn">
                    <i class="fas fa-api"></i> API 문서
                </a>
                <a href="/health" class="btn btn-success">
                    <i class="fas fa-stethoscope"></i> 헬스체크
                </a>
            </div>
            
            <div class="features">
                <div class="feature-card">
                    <h3><i class="fas fa-spider"></i> 크롤링 기능</h3>
                    <ul>
                        <li><i class="fas fa-check"></i> 네이버 카페 자동 크롤링</li>
                        <li><i class="fas fa-check"></i> 챌린지 미션 참여자 수집</li>
                        <li><i class="fas fa-check"></i> 실시간 데이터 처리</li>
                    </ul>
                </div>
                <div class="feature-card">
                    <h3><i class="fas fa-table"></i> Google Sheets 연동</h3>
                    <ul>
                        <li><i class="fas fa-check"></i> 자동 데이터 업데이트</li>
                        <li><i class="fas fa-check"></i> 실시간 동기화</li>
                        <li><i class="fas fa-check"></i> 백업 및 복구</li>
                    </ul>
                </div>
                <div class="feature-card">
                    <h3><i class="fas fa-clock"></i> 스케줄링</h3>
                    <ul>
                        <li><i class="fas fa-check"></i> 자동 실행 스케줄</li>
                        <li><i class="fas fa-check"></i> Cron 작업 관리</li>
                        <li><i class="fas fa-check"></i> 에러 알림</li>
                    </ul>
                </div>
                <div class="feature-card">
                    <h3><i class="fas fa-chart-bar"></i> 모니터링</h3>
                    <ul>
                        <li><i class="fas fa-check"></i> 실행 로그 관리</li>
                        <li><i class="fas fa-check"></i> 성공률 통계</li>
                        <li><i class="fas fa-check"></i> 웹 대시보드</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/api")
def api_info():
    """API 정보 엔드포인트"""
    return {
        "service": "QOK6 자동화 서비스",
        "version": "1.0.0",
        "status": "running",
        "environment_setup": env_status,
        "endpoints": {
            "dashboard": "/",
            "api_info": "/api",
            "health": "/health",
            "env_test": "/env-test"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "service": "qok6-automation",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/env-test")
def env_test():
    """Environment variables test endpoint"""
    return {
        "google_credentials_exists": bool(os.getenv('GOOGLE_CREDENTIALS_JSON')),
        "naver_cookies_exists": bool(os.getenv('NAVER_COOKIES_JSON')),
        "google_credentials_path": os.getenv('GOOGLE_CREDENTIALS_PATH'),
        "naver_cookies_path": os.getenv('NAVER_COOKIES_PATH'),
        "setup_status": env_status,
        "static_files_available": bool(templates),
        "project_root": str(project_root)
    }