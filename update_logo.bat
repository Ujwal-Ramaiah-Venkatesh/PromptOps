@echo off
REM PromptOps Logo Update Script
REM This script synchronizes the logo across all required locations

echo ========================================
echo   PromptOps Logo Update Utility
echo ========================================
echo.

REM Check if source logo exists
set "SOURCE_LOGO=branding\promptops-logo.png"

if not exist "%SOURCE_LOGO%" (
    echo ERROR: Source logo not found at %SOURCE_LOGO%
    echo.
    echo Please save your new logo as: branding\promptops-logo.png
    echo Then run this script again.
    pause
    exit /b 1
)

echo [1/3] Backing up existing logos...
if exist "assets\promptops-logo.png" (
    copy "assets\promptops-logo.png" "assets\promptops-logo.png.backup" >nul 2>&1
    echo   - Backed up assets\promptops-logo.png
)
if exist "frontend\dashboard\public\promptops-logo.png" (
    copy "frontend\dashboard\public\promptops-logo.png" "frontend\dashboard\public\promptops-logo.png.backup" >nul 2>&1
    echo   - Backed up frontend\dashboard\public\promptops-logo.png
)
echo.

echo [2/3] Copying new logo to all locations...
copy "%SOURCE_LOGO%" "assets\promptops-logo.png" >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ Updated: assets\promptops-logo.png
) else (
    echo   ✗ Failed: assets\promptops-logo.png
)

copy "%SOURCE_LOGO%" "frontend\dashboard\public\promptops-logo.png" >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ Updated: frontend\dashboard\public\promptops-logo.png
) else (
    echo   ✗ Failed: frontend\dashboard\public\promptops-logo.png
)
echo.

echo [3/3] Verifying logo files...
for %%F in (branding\promptops-logo.png assets\promptops-logo.png frontend\dashboard\public\promptops-logo.png) do (
    if exist "%%F" (
        echo   ✓ Exists: %%F
    ) else (
        echo   ✗ Missing: %%F
    )
)
echo.

echo ========================================
echo   Logo Update Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart the frontend dev server to see changes
echo 2. Clear browser cache (Ctrl+Shift+R)
echo 3. Check login page and navigation bar
echo.
pause
