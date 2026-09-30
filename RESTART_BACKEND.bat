@echo off
echo ==========================================
echo Restarting PromptOps Backend
echo ==========================================
echo.

echo Step 1: Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Step 2: Starting fresh backend on port 3800...
cd /d "%~dp0\api_gateway"
start /B python -m uvicorn main:app --host 0.0.0.0 --port 3800

echo.
echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo Step 3: Testing backend health...
curl -s http://localhost:3800/health
echo.

echo.
echo ==========================================
echo Backend restarted successfully!
echo ==========================================
echo.
echo Backend API:  http://localhost:3800
echo API Docs:     http://localhost:3800/docs
echo.
pause
