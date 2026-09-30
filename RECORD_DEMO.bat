@echo off
echo ========================================
echo   AUTOMATED DEMO RECORDING
echo ========================================
echo.

echo Checking prerequisites...
echo.

REM Check if backend is running
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend is not running!
    echo    Starting backend...
    cd api_gateway
    start "PromptOps Backend" cmd /k python main.py
    cd ..
    timeout /t 8 /nobreak >nul
)

REM Check if frontend is running
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Frontend is not running!
    echo    Starting frontend...
    cd frontend\dashboard
    start "PromptOps Frontend" cmd /k npm run dev
    cd ..\..
    timeout /t 12 /nobreak >nul
)

echo.
echo ✅ Services are running
echo.
echo ========================================
echo   STARTING AUTOMATED DEMO RECORDING
echo ========================================
echo.
echo The browser will open automatically.
echo The script will:
echo   • Login to PromptOps
echo   • Navigate through the UI
echo   • Fill forms automatically
echo   • Run security scans
echo   • Run load tests
echo   • Record video of everything
echo.
echo Video will be saved to: demo_recordings\
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

python auto_demo_recording.py

echo.
echo ========================================
echo   RECORDING COMPLETE
echo ========================================
echo.
echo Check the demo_recordings folder for:
echo   • Video file (.webm)
echo   • Screenshots (.png)
echo.
pause
