// QOK6 자동화 서비스 대시보드 JavaScript

let currentExecutionId = null;
let statusCheckInterval = null;

// 수동 실행 함수
async function runAutomation() {
    const runBtn = document.getElementById('runBtn');
    const executionStatus = document.getElementById('executionStatus');
    const statusText = document.getElementById('statusText');

    // 버튼 비활성화
    runBtn.disabled = true;
    runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 실행 중...';

    // 상태 표시
    executionStatus.className = 'execution-status';
    executionStatus.classList.remove('hidden');
    statusText.textContent = '실행 중...';

    try {
        const response = await fetch('/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            currentExecutionId = data.execution_id;
            statusText.textContent = '실행이 시작되었습니다. 상태를 확인하는 중...';
            
            // 상태 확인 시작
            startStatusCheck();
        } else {
            throw new Error(data.detail || '실행 실패');
        }
    } catch (error) {
        console.error('실행 오류:', error);
        showExecutionError(error.message);
        resetButton();
    }
}

// 상태 확인 시작
function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(checkExecutionStatus, 2000); // 2초마다 확인
    
    // 최대 5분 후 자동 중지
    setTimeout(() => {
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
            resetButton();
            showExecutionError('실행 시간이 초과되었습니다.');
        }
    }, 300000); // 5분
}

// 실행 상태 확인
async function checkExecutionStatus() {
    if (!currentExecutionId) return;

    try {
        const response = await fetch(`/logs?limit=10`);
        const data = await response.json();
        
        if (response.ok && data.logs && data.logs.length > 0) {
            const latestLog = data.logs.find(log => log.execution_id === currentExecutionId);
            
            if (latestLog && latestLog.completed_at) {
                // 실행 완료됨
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                
                if (latestLog.success) {
                    showExecutionSuccess(latestLog);
                } else {
                    showExecutionError(latestLog.error_message || '실행 실패');
                }
                
                resetButton();
                setTimeout(refreshLogs, 1000); // 1초 후 로그 새로고침
            }
        }
    } catch (error) {
        console.error('상태 확인 오류:', error);
    }
}

// 실행 성공 표시
function showExecutionSuccess(logData) {
    const executionStatus = document.getElementById('executionStatus');
    const statusText = document.getElementById('statusText');
    
    executionStatus.className = 'execution-status success';
    statusText.innerHTML = `
        <i class="fas fa-check-circle" style="margin-right: 8px;"></i>
        실행 성공! 
        ${logData.results ? `${logData.results.weeks_processed}개 주차, ${logData.results.participants?.length || 0}명 처리` : ''}
    `;
    
    // 3초 후 숨기기
    setTimeout(() => {
        executionStatus.classList.add('hidden');
    }, 3000);
}

// 실행 오류 표시
function showExecutionError(errorMessage) {
    const executionStatus = document.getElementById('executionStatus');
    const statusText = document.getElementById('statusText');
    
    executionStatus.className = 'execution-status error';
    statusText.innerHTML = `
        <i class="fas fa-times-circle" style="margin-right: 8px;"></i>
        실행 실패: ${errorMessage}
    `;
    
    // 5초 후 숨기기
    setTimeout(() => {
        executionStatus.classList.add('hidden');
    }, 5000);
}

// 버튼 초기화
function resetButton() {
    const runBtn = document.getElementById('runBtn');
    runBtn.disabled = false;
    runBtn.innerHTML = '<i class="fas fa-play"></i> 수동 실행';
    currentExecutionId = null;
}

// 로그 새로고침
async function refreshLogs() {
    try {
        // 페이지 새로고침 (간단한 방법)
        window.location.reload();
    } catch (error) {
        console.error('로그 새로고침 오류:', error);
    }
}

// 스케줄 폼 토글
function toggleScheduleForm() {
    const scheduleForm = document.getElementById('scheduleForm');
    const scheduleBtn = document.getElementById('scheduleBtn');
    
    if (scheduleForm.classList.contains('hidden')) {
        scheduleForm.classList.remove('hidden');
        scheduleBtn.innerHTML = '<i class="fas fa-times"></i> 닫기';
        loadScheduleStatus();
    } else {
        scheduleForm.classList.add('hidden');
        scheduleBtn.innerHTML = '<i class="fas fa-clock"></i> 스케줄 설정';
    }
}

// 현재 스케줄 상태 로드
async function loadScheduleStatus() {
    const currentSchedule = document.getElementById('currentSchedule');
    
    try {
        const response = await fetch('/schedule');
        const data = await response.json();
        
        if (response.ok && data.cron_status) {
            const status = data.cron_status;
            
            if (status.active) {
                currentSchedule.innerHTML = `
                    <div class="schedule-active">
                        <i class="fas fa-clock"></i> 활성: ${status.schedule}
                        ${status.next_run ? `<div class="next-run">다음 실행: ${formatDateTime(status.next_run)}</div>` : ''}
                    </div>
                `;
            } else {
                currentSchedule.innerHTML = `
                    <div class="schedule-inactive">
                        <i class="fas fa-clock-o"></i> 자동 실행이 설정되지 않았습니다
                    </div>
                `;
            }
        } else {
            throw new Error('스케줄 상태를 가져올 수 없습니다');
        }
    } catch (error) {
        console.error('스케줄 상태 로드 오류:', error);
        currentSchedule.innerHTML = `
            <div style="color: #ef4444;">
                <i class="fas fa-exclamation-triangle"></i> 상태 로드 실패: ${error.message}
            </div>
        `;
    }
}

// 스케줄 설정
async function setupSchedule() {
    const hour = parseInt(document.getElementById('scheduleHour').value);
    const minute = parseInt(document.getElementById('scheduleMinute').value);
    
    try {
        const response = await fetch(`/schedule?hour=${hour}&minute=${minute}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`자동 실행이 매일 ${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}에 설정되었습니다`, 'success');
            loadScheduleStatus(); // 상태 다시 로드
        } else {
            throw new Error(data.detail || '스케줄 설정에 실패했습니다');
        }
    } catch (error) {
        console.error('스케줄 설정 오류:', error);
        showNotification(`스케줄 설정 실패: ${error.message}`, 'error');
    }
}

// 스케줄 제거
async function removeSchedule() {
    if (!confirm('자동 실행 스케줄을 제거하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch('/schedule', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('자동 실행 스케줄이 제거되었습니다', 'success');
            loadScheduleStatus(); // 상태 다시 로드
        } else {
            throw new Error(data.detail || '스케줄 제거에 실패했습니다');
        }
    } catch (error) {
        console.error('스케줄 제거 오류:', error);
        showNotification(`스케줄 제거 실패: ${error.message}`, 'error');
    }
}

// 페이지 로드시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 자동 새로고침 설정 (5분마다)
    setInterval(refreshLogs, 300000);
    
    // 페이지 visibility 변경 감지 (탭 전환 등)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // 페이지가 다시 활성화되면 상태 확인
            if (currentExecutionId && !statusCheckInterval) {
                startStatusCheck();
            }
        }
    });
});

// 유틸리티 함수들
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function showNotification(message, type = 'info') {
    // 토스트 알림 생성
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                type === 'error' ? 'fa-times-circle' : 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;
    
    // 스타일 추가
    Object.assign(toast.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        zIndex: '10000',
        maxWidth: '400px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        transform: 'translateX(400px)',
        transition: 'transform 0.3s ease',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
    });
    
    // 타입별 배경색
    const colors = {
        success: '#16a34a',
        error: '#ef4444',
        info: '#3b82f6'
    };
    toast.style.backgroundColor = colors[type] || colors.info;
    
    document.body.appendChild(toast);
    
    // 애니메이션으로 표시
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // 자동 제거
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
    
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// 키보드 단축키 (Ctrl+R로 수동 실행)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        const runBtn = document.getElementById('runBtn');
        if (!runBtn.disabled) {
            runAutomation();
        }
    }
});

// 에러 처리
window.addEventListener('unhandledrejection', function(event) {
    console.error('처리되지 않은 Promise 거부:', event.reason);
    showNotification('예상치 못한 오류가 발생했습니다.', 'error');
});

window.addEventListener('error', function(event) {
    console.error('JavaScript 오류:', event.error);
    showNotification('JavaScript 오류가 발생했습니다.', 'error');
});