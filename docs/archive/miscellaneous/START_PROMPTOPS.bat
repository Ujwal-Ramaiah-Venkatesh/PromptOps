@echo off
echo ======================================
echo    Starting PromptOps Platform
echo ======================================
echo.

echo [1/2] Starting API Gateway (Backend)...
start "PromptOps API" cmd /k "cd /d c:\Users\pqm847\Documents\PromptOps\api_gateway && python main.py"
timeout /t 5 /nobreak >/dev/null

echo [2/2] Starting React Dashboard (Frontend)...
start "PromptOps Dashboard" cmd /k "cd /d c:\Users\pqm847\Documents\PromptOps\frontend\dashboard && npm run dev"

echo.
echo ======================================
echo    PromptOps is starting...
echo ======================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://localhost:3000
echo.
echo Press any key to close this window...
pause >/dev/null
