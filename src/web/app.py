"""FastAPI 웹 애플리케이션."""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path

from ..core.logger import get_logger, LoggerSetup
from ..main import QOK6AutomationSystem
from .services import ExecutionLogService
from ..scheduler.cron_service import CronService


# 응답 모델 정의
class ExecutionResponse(BaseModel):
    """실행 결과 응답 모델."""
    success: bool
    message: str
    execution_id: Optional[str] = None
    started_at: datetime
    results: Optional[Dict[str, Any]] = None


class LogEntry(BaseModel):
    """로그 엔트리 모델."""
    execution_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class LogResponse(BaseModel):
    """로그 조회 응답 모델."""
    total_count: int
    logs: List[LogEntry]


# FastAPI 앱 생성
app = FastAPI(
    title="QOK6 자동화 서비스",
    description="네이버 카페 챌린지 미션 현황을 구글 시트에 자동으로 체크하는 서비스",
    version="1.0.0"
)

# 정적 파일과 템플릿 설정
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(current_dir / "templates"))

# 전역 변수
automation_system: Optional[QOK6AutomationSystem] = None
log_service: Optional[ExecutionLogService] = None
cron_service: Optional[CronService] = None
logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화."""
    global automation_system, log_service, cron_service
    
    try:
        # 로깅 설정
        LoggerSetup.setup_logging()
        
        # 자동화 시스템 초기화
        automation_system = QOK6AutomationSystem()
        
        # 실행 로그 서비스 초기화
        log_service = ExecutionLogService()
        
        # Cron 서비스 초기화
        cron_service = CronService()
        
        logger.info("QOK6 웹 애플리케이션 시작됨")
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 중 오류: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리."""
    logger.info("QOK6 웹 애플리케이션 종료됨")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드 페이지."""
    if not automation_system or not log_service:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "error": "시스템이 초기화되지 않았습니다"
        })
    
    try:
        # 최근 실행 로그 조회
        recent_logs = log_service.get_logs(limit=10)
        success_rate = log_service.get_success_rate(days=7)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "recent_logs": recent_logs,
            "success_rate": success_rate * 100,
            "system_status": "healthy"
        })
    except Exception as e:
        logger.error(f"대시보드 로드 중 오류: {str(e)}")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "error": f"대시보드 로드 실패: {str(e)}"
        })

@app.get("/api")
async def api_root():
    """API 정보 엔드포인트."""
    return {
        "service": "QOK6 자동화 서비스",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "manual_run": "/run",
            "logs": "/logs",
            "status": "/status",
            "dashboard": "/"
        }
    }


@app.post("/run", response_model=ExecutionResponse)
async def manual_run(background_tasks: BackgroundTasks):
    """수동으로 자동화 프로세스 실행."""
    if not automation_system or not log_service:
        raise HTTPException(status_code=500, detail="시스템이 초기화되지 않았습니다")
    
    try:
        # 실행 ID 생성 및 로그 시작
        execution_id = log_service.start_execution()
        from ..shared.utils import get_kst_now
        started_at = get_kst_now()
        
        # 백그라운드에서 자동화 프로세스 실행
        background_tasks.add_task(
            run_automation_background,
            execution_id,
            started_at
        )
        
        return ExecutionResponse(
            success=True,
            message="자동화 프로세스가 백그라운드에서 시작되었습니다",
            execution_id=execution_id,
            started_at=started_at
        )
        
    except Exception as e:
        logger.error(f"수동 실행 요청 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"실행 요청 실패: {str(e)}")


async def run_automation_background(execution_id: str, started_at: datetime):
    """백그라운드에서 자동화 프로세스 실행."""
    try:
        logger.info(f"자동화 프로세스 시작: {execution_id}")
        
        # 자동화 사이클 실행
        results = await automation_system.run_automation_cycle()
        
        # 실행 완료 로그 저장
        log_service.complete_execution(
            execution_id=execution_id,
            success=results['success'],
            results=results,
            error_message=results.get('error_message')
        )
        
        if results['success']:
            logger.info(f"자동화 프로세스 완료: {execution_id}")
        else:
            logger.error(f"자동화 프로세스 실패: {execution_id} - {results.get('error_message')}")
            
    except Exception as e:
        error_msg = f"자동화 프로세스 실행 중 예상치 못한 오류: {str(e)}"
        logger.error(f"{error_msg}: {execution_id}")
        
        # 오류 로그 저장
        log_service.complete_execution(
            execution_id=execution_id,
            success=False,
            error_message=error_msg
        )


@app.get("/logs", response_model=LogResponse)
async def get_execution_logs(limit: int = 50, offset: int = 0):
    """실행 로그 조회."""
    if not log_service:
        raise HTTPException(status_code=500, detail="로그 서비스가 초기화되지 않았습니다")
    
    try:
        logs = log_service.get_logs(limit=limit, offset=offset)
        total_count = log_service.get_total_count()
        
        # LogEntry 모델로 변환
        log_entries = []
        for log_data in logs:
            # datetime 문자열을 datetime 객체로 변환
            started_at = datetime.fromisoformat(log_data['started_at'])
            completed_at = None
            if log_data.get('completed_at'):
                completed_at = datetime.fromisoformat(log_data['completed_at'])
            
            log_entry = LogEntry(
                execution_id=log_data['execution_id'],
                started_at=started_at,
                completed_at=completed_at,
                success=log_data['success'],
                message=log_data['message'],
                results=log_data.get('results'),
                error_message=log_data.get('error_message')
            )
            log_entries.append(log_entry)
        
        return LogResponse(
            total_count=total_count,
            logs=log_entries
        )
        
    except Exception as e:
        logger.error(f"로그 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그 조회 실패: {str(e)}")


@app.get("/status")
async def get_status():
    """시스템 상태 조회."""
    if not automation_system or not log_service:
        return {"status": "error", "message": "시스템이 초기화되지 않았습니다"}
    
    try:
        # 최근 실행 결과 조회
        recent_logs = log_service.get_logs(limit=5)
        
        # 성공률 계산
        if recent_logs:
            success_count = sum(1 for log in recent_logs if log['success'])
            success_rate = success_count / len(recent_logs) * 100
        else:
            success_rate = 0
        
        return {
            "status": "healthy",
            "system_initialized": True,
            "recent_executions": len(recent_logs),
            "success_rate": f"{success_rate:.1f}%",
            "last_execution": recent_logs[0] if recent_logs else None
        }
        
    except Exception as e:
        logger.error(f"상태 조회 중 오류: {str(e)}")
        return {"status": "error", "message": f"상태 조회 실패: {str(e)}"}


@app.get("/schedule")
async def get_schedule_status():
    """Cron 스케줄 상태 조회."""
    if not cron_service:
        raise HTTPException(status_code=500, detail="Cron 서비스가 초기화되지 않았습니다")
    
    try:
        status = cron_service.get_cron_status()
        return {
            "cron_status": status,
            "timezone": "KST (UTC+9)"
        }
    except Exception as e:
        logger.error(f"스케줄 상태 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"스케줄 상태 조회 실패: {str(e)}")


@app.post("/schedule")
async def setup_schedule(hour: int = 0, minute: int = 0):
    """매일 실행 스케줄 설정."""
    if not cron_service:
        raise HTTPException(status_code=500, detail="Cron 서비스가 초기화되지 않았습니다")
    
    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
        raise HTTPException(status_code=400, detail="올바른 시간을 입력해주세요 (시: 0-23, 분: 0-59)")
    
    try:
        success = cron_service.setup_daily_cron(hour=hour, minute=minute)
        
        if success:
            logger.info(f"Cron 스케줄 설정 완료: 매일 {hour:02d}:{minute:02d}")
            return {
                "success": True,
                "message": f"매일 {hour:02d}:{minute:02d}에 자동 실행되도록 설정되었습니다",
                "schedule": f"{hour:02d}:{minute:02d}",
                "timezone": "KST (UTC+9)"
            }
        else:
            raise HTTPException(status_code=500, detail="Cron 설정에 실패했습니다")
            
    except Exception as e:
        logger.error(f"스케줄 설정 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"스케줄 설정 실패: {str(e)}")


@app.delete("/schedule")
async def remove_schedule():
    """자동 실행 스케줄 제거."""
    if not cron_service:
        raise HTTPException(status_code=500, detail="Cron 서비스가 초기화되지 않았습니다")
    
    try:
        success = cron_service.remove_cron()
        
        if success:
            logger.info("Cron 스케줄 제거 완료")
            return {
                "success": True,
                "message": "자동 실행 스케줄이 제거되었습니다"
            }
        else:
            raise HTTPException(status_code=500, detail="스케줄 제거에 실패했습니다")
            
    except Exception as e:
        logger.error(f"스케줄 제거 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"스케줄 제거 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)