@echo off
echo ==========================================
echo PromptOps - Fresh Start Script
echo ==========================================
echo.

cd /d "%~dp0"
set PROJECT_ROOT=%CD%

echo Step 1/2: Starting Backend API on port 3800...
cd "%PROJECT_ROOT%\api_gateway"

start /B python -m uvicorn main:app --host 0.0.0.0 --port 3800 --reload > "%PROJECT_ROOT%\backend.log" 2>&1

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

curl -s http://localhost:3800/health > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Backend is healthy!
) else (
    echo Backend failed to start. Check backend.log
    exit /b 1
)

echo.
echo Step 2/2: Starting Frontend on port 3000...
cd "%PROJECT_ROOT%\frontend\dashboard"

start /B npm run dev > "%PROJECT_ROOT%\frontend.log" 2>&1

echo.
echo ==========================================
echo PromptOps is now running!
echo ==========================================
echo.
echo Backend API:  http://localhost:3800
echo   Health:     http://localhost:3800/health
echo   API Docs:   http://localhost:3800/docs
echo.
echo Frontend:     http://localhost:3000
echo.
echo Logs:
echo   Backend:    %PROJECT_ROOT%\backend.log
echo   Frontend:   %PROJECT_ROOT%\frontend.log
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.

pause
