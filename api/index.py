from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import os
import json

# Create a simple FastAPI app
app = FastAPI(title="Auto Cafe API", version="1.0.0")

# Environment variables setup for Vercel
def setup_credentials():
    try:
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
        return True
    except Exception as e:
        print(f"Credential setup error: {e}")
        return False

# Setup credentials on startup
setup_credentials()

@app.get("/")
def read_root():
    return {
        "message": "Auto Cafe API is running on Vercel",
        "status": "ok",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "auto-cafe"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Auto Cafe Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 20px; background: #f0f8ff; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Auto Cafe Dashboard</h1>
            <div class="status">
                <h2>Service Status</h2>
                <p>✅ API is running successfully on Vercel</p>
                <p>🚀 Version: 1.0.0</p>
            </div>
        </div>
    </body>
    </html>
    """