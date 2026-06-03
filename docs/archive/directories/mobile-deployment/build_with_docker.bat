@echo off
REM Build Android APK using Docker with Java 17
REM ============================================

echo.
echo ======================================================================
echo   Building netSenseAI APK with Docker (Java 17)
echo ======================================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking Docker...
docker --version

REM Clone repository if not exists
echo.
echo [2/5] Preparing repository...
if not exist "%TEMP%\netSenseAI" (
    echo       Cloning netSenseAI repository...
    git clone --depth 1 https://github.com/kirankumarhs29/netSenseAI "%TEMP%\netSenseAI"
) else (
    echo       Repository already exists
)

REM Build with Docker
echo.
echo [3/5] Building APK with Docker (Java 17)...
echo       This may take 5-10 minutes on first run...
echo       (Docker will download Java 17 image - ~400 MB)
echo.

docker run --rm ^
    -v "%TEMP%\netSenseAI:/app" ^
    -w /app ^
    eclipse-temurin:17-jdk ^
    bash -c "chmod +x gradlew && ./gradlew :androidApp:assembleDebug --no-daemon --stacktrace"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo.
    echo Please check the error messages above.
    pause
    exit /b 1
)

REM Find the APK
echo.
echo [4/5] Locating APK file...
set "APK_PATH=%TEMP%\netSenseAI\androidApp\build\outputs\apk\debug"

if exist "%APK_PATH%\*.apk" (
    for %%F in ("%APK_PATH%\*.apk") do (
        set "APK_FILE=%%F"
        echo       Found: %%~nxF
    )
) else (
    echo [ERROR] APK file not found!
    pause
    exit /b 1
)

REM Copy to Downloads
echo.
echo [5/5] Copying APK to Downloads folder...
copy "%APK_FILE%" "%USERPROFILE%\Downloads\netSenseAI-debug.apk"

echo.
echo ======================================================================
echo   Build Complete!
echo ======================================================================
echo.
echo APK Location: %USERPROFILE%\Downloads\netSenseAI-debug.apk
echo.
echo Next Step - Deploy to AWS:
echo   cd C:\Users\pqm847\Documents\PromptOps
echo.
echo   python mobile-deployment\deploy_prebuilt_apk.py ^
echo     --apk-path "%USERPROFILE%\Downloads\netSenseAI-debug.apk" ^
echo     --app-name "netSenseAI" ^
echo     --version "1.0.0" ^
echo     --aws-bucket netsense-ai-2026
echo.
echo ======================================================================
echo.
pause
