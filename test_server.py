#!/usr/bin/env python3
"""간단한 테스트 서버."""

import uvicorn
from fastapi import FastAPI

# 간단한 FastAPI 앱
test_app = FastAPI(title="테스트 서버")

@test_app.get("/")
def root():
    return {"message": "테스트 서버가 정상 작동 중입니다!", "status": "OK"}

@test_app.get("/test")
def test():
    return {"test": "성공", "server": "running"}

if __name__ == "__main__":
    print("=== 간단한 테스트 서버 시작 ===")
    print("접속 주소: http://127.0.0.1:8080")
    print("중지하려면 Ctrl+C를 누르세요")
    
    uvicorn.run(
        test_app,
        host="127.0.0.1",
        port=8080,
        reload=False
    )