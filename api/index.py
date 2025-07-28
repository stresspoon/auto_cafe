import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

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

from src.web.app import app

# Vercel expects a variable named 'app'
app = app