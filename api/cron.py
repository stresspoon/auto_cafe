import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException

# Get the project root directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

app = FastAPI()

# Environment setup function
def setup_environment():
    """Setup environment variables for automation"""
    try:
        # Google Credentials
        google_creds_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if google_creds_str:
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
            
        return True
        
    except Exception as e:
        print(f"Environment setup error: {e}")
        return False

# Mock automation function for now
async def run_automation_cycle():
    """Run the automation cycle - simplified for Vercel"""
    try:
        # Setup environment
        env_setup = setup_environment()
        if not env_setup:
            return {
                "success": False,
                "error": "Environment setup failed",
                "timestamp": datetime.now().isoformat()
            }
        
        # Simulate automation work
        print("Starting automation cycle...")
        
        # Here you would integrate your actual automation logic
        # For now, return a success response
        results = {
            "success": True,
            "message": "Automation cycle completed successfully",
            "timestamp": datetime.now().isoformat(),
            "execution_id": f"cron-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "processed_items": 0,  # Placeholder
            "environment_ready": env_setup
        }
        
        print(f"Automation cycle completed: {results}")
        return results
        
    except Exception as e:
        error_msg = f"Automation cycle failed: {str(e)}"
        print(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/")
@app.post("/")
async def cron_handler():
    """Vercel Cron endpoint - handles both GET and POST requests"""
    try:
        print(f"Cron job triggered at {datetime.now().isoformat()}")
        
        # Run automation cycle
        results = await run_automation_cycle()
        
        # Log results
        if results["success"]:
            print(f"✅ Cron job completed successfully: {results['execution_id']}")
        else:
            print(f"❌ Cron job failed: {results.get('error', 'Unknown error')}")
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        error_msg = f"Cron handler error: {str(e)}"
        print(error_msg)
        
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

# For manual testing
@app.get("/test")
async def test_cron():
    """Test endpoint to manually trigger automation"""
    return await cron_handler()