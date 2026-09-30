@echo off
echo ========================================
echo   PROMPTOPS DEPLOYMENT DEMO
echo   Automated Setup Script
echo ========================================
echo.

REM Check if services are already running
echo [1/5] Checking if services are running...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Backend is already running
) else (
    echo ✗ Backend is not running
    echo   Starting backend...
    cd api_gateway
    start "PromptOps Backend" cmd /k python main.py
    cd ..
    timeout /t 5 /nobreak >nul
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Frontend is already running
) else (
    echo ✗ Frontend is not running
    echo   Starting frontend...
    cd frontend\dashboard
    start "PromptOps Frontend" cmd /k npm run dev
    cd ..\..
    timeout /t 10 /nobreak >nul
)

echo.
echo [2/5] Verifying AWS credentials...
aws sts get-caller-identity >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ AWS credentials configured
) else (
    echo ✗ AWS credentials not found
    echo   Please run: aws configure
    pause
    exit /b 1
)

echo.
echo [3/5] Testing backend API...
curl -s http://localhost:8000/health | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✓ Backend API responding
) else (
    echo ✗ Backend API not responding
    echo   Waiting 10 seconds and retrying...
    timeout /t 10 /nobreak >nul
    curl -s http://localhost:8000/health | findstr "healthy" >nul
    if %errorlevel% neq 0 (
        echo ✗ Backend still not responding
        pause
        exit /b 1
    )
    echo ✓ Backend API now responding
)

echo.
echo [4/5] Testing frontend...
curl -s http://localhost:3000 | findstr "PromptOps" >nul
if %errorlevel% equ 0 (
    echo ✓ Frontend responding
) else (
    echo ✗ Frontend not responding
    echo   Please check if npm run dev started successfully
)

echo.
echo [5/5] Preparing demo environment...
echo ✓ Demo repository: https://github.com/ashi100sh/jewelry-vault
echo ✓ Demo credentials: admin@promptops.com / admin123
echo ✓ Demo app name: jewelry-vault-demo

echo.
echo ========================================
echo   DEMO READY!
echo ========================================
echo.
echo Next Steps:
echo 1. Open browser: http://localhost:3000
echo 2. Login with: admin@promptops.com / admin123
echo 3. Click "Deploy App" or navigate to deployment
echo 4. Fill in:
echo    - App Name: jewelry-vault-demo
echo    - GitHub URL: https://github.com/ashi100sh/jewelry-vault
echo    - Branch: main
echo    - Region: us-east-1
echo 5. Click "Deploy Now"
echo 6. Watch the magic happen!
echo.
echo Press any key to open the browser...
pause >nul

start http://localhost:3000

echo.
echo Demo started! Good luck! 🚀
echo.
pause
