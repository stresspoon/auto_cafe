from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
import json

app = FastAPI(title="Auto Cafe API", version="1.0.0")

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

@app.get("/")
def read_root():
    return {
        "message": "Auto Cafe API is running on Vercel",
        "status": "ok",
        "version": "1.0.0",
        "environment_setup": env_status
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "auto-cafe"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auto Cafe Dashboard</title>
        <meta charset="UTF-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background-color: #f5f5f5;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .status { 
                padding: 20px; 
                background: #e8f5e8; 
                border-radius: 8px; 
                margin: 20px 0;
                border-left: 4px solid #4caf50;
            }
            .header {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .feature {
                background: #f0f8ff;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                border-left: 3px solid #2196f3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Auto Cafe Dashboard</h1>
                <p>네이버 카페 자동화 시스템</p>
            </div>
            
            <div class="status">
                <h2>📊 시스템 상태</h2>
                <p>✅ API 서버: 정상 운영 중</p>
                <p>🚀 버전: 1.0.0</p>
                <p>☁️ 호스팅: Vercel</p>
            </div>
            
            <div class="feature">
                <h3>🔧 주요 기능</h3>
                <ul>
                    <li>네이버 카페 회원 정보 크롤링</li>
                    <li>Google Sheets 연동</li>
                    <li>자동 스케줄링</li>
                    <li>웹 대시보드</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>📈 API 엔드포인트</h3>
                <ul>
                    <li><code>GET /</code> - API 상태 확인</li>
                    <li><code>GET /health</code> - 헬스체크</li>
                    <li><code>GET /dashboard</code> - 현재 페이지</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/env-test")
def env_test():
    """Environment variables test endpoint"""
    return {
        "google_credentials_exists": bool(os.getenv('GOOGLE_CREDENTIALS_JSON')),
        "naver_cookies_exists": bool(os.getenv('NAVER_COOKIES_JSON')),
        "google_credentials_path": os.getenv('GOOGLE_CREDENTIALS_PATH'),
        "naver_cookies_path": os.getenv('NAVER_COOKIES_PATH'),
        "setup_status": env_status
    }