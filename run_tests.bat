@echo off
REM 파일 입고 모니터링 시스템 — 테스트 실행
cd /d "%~dp0"

where pytest >nul 2>nul
if %errorlevel% neq 0 (
    py -m pytest %*
) else (
    pytest %*
)
exit /b %errorlevel%
