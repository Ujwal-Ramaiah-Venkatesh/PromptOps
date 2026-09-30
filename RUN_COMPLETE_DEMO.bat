@echo off
echo ========================================
echo   COMPLETE DEPLOYMENT DEMO
echo ========================================
echo.
echo This will record a COMPLETE flow:
echo   1. Login
echo   2. Navigate Dashboard
echo   3. Show Deployment
echo   4. Open Observability
echo   5. Monitor Metrics
echo   6. Security Scan
echo   7. OPEN DEPLOYED APP
echo   8. Final Overview
echo.
echo Video will show EVERYTHING!
echo.

REM Check services
echo Checking services...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting backend...
    cd api_gateway
    start "Backend" cmd /k python main.py
    cd ..
    timeout /t 8 /nobreak >nul
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting frontend...
    cd frontend\dashboard
    start "Frontend" cmd /k npm run dev
    cd ..\..
    timeout /t 12 /nobreak >nul
)

echo.
echo ✅ Services ready!
echo.
echo Starting COMPLETE deployment demo...
echo.

python complete_deployment_demo.py

echo.
echo ========================================
echo   DEMO COMPLETE!
echo ========================================
echo.
echo Check: demo_recordings_complete\
echo   • Video file
echo   • All screenshots
echo.
pause
