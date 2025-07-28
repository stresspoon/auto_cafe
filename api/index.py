import sys
import os
import json
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Environment variables setup for Vercel
if os.getenv('GOOGLE_CREDENTIALS_JSON'):
    google_creds = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
    os.environ['GOOGLE_CREDENTIALS_PATH'] = '/tmp/credentials.json'
    with open('/tmp/credentials.json', 'w') as f:
        json.dump(google_creds, f)

if os.getenv('NAVER_COOKIES_JSON'):
    naver_cookies = json.loads(os.getenv('NAVER_COOKIES_JSON'))
    os.environ['NAVER_COOKIES_PATH'] = '/tmp/naver_cookies.json'
    with open('/tmp/naver_cookies.json', 'w') as f:
        json.dump(naver_cookies, f)

# Disable scheduler in production
os.environ['SCHEDULER_ENABLED'] = 'false'

try:
    from src.web.app import app
except ImportError as e:
    print(f"Import error: {e}")
    # Create a simple fallback app
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"message": "Auto Cafe API - Import Error", "error": str(e)}

# Vercel expects a variable named 'app'
app = app