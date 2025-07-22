#!/usr/bin/env python3
"""QOK6 웹 서버 실행 스크립트."""

import uvicorn
from src.web.app import app

if __name__ == "__main__":
    print("QOK6 자동화 웹 서비스를 시작합니다...")
    print("API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.")
    print("서비스를 중지하려면 Ctrl+C를 누르세요.")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )