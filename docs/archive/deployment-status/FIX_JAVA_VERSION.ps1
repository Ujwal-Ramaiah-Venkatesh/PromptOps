# PromptOps - Fix Java Version Issue
# ====================================
# This script downloads and installs Java 17 LTS
# Author: DevOps Engineer
# Date: 2026-05-11

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  PromptOps - Java 17 LTS Installation" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# Step 1: Check current Java version
Write-Host "[1/6] Checking current Java version..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version" | ForEach-Object { $_.Line }
    Write-Host "      Current: $javaVersion" -ForegroundColor Gray
} catch {
    Write-Host "      Java not found or not in PATH" -ForegroundColor Gray
}

# Step 2: Download Java 17 LTS
Write-Host "`n[2/6] Downloading Java 17 LTS..." -ForegroundColor Yellow
$downloadUrl = "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse"
$installerPath = "$env:TEMP\OpenJDK17.msi"

if (Test-Path $installerPath) {
    Write-Host "      Installer already exists at: $installerPath" -ForegroundColor Gray
} else {
    Write-Host "      Downloading to: $installerPath" -ForegroundColor Gray
    Write-Host "      This may take 2-3 minutes (approx 180 MB)..." -ForegroundColor Gray

    try {
        # Download with progress
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "      [OK] Download complete!" -ForegroundColor Green
    } catch {
        Write-Host "      [ERROR] Download failed: $_" -ForegroundColor Red
        Write-Host "`n      Please download manually from:" -ForegroundColor Yellow
        Write-Host "      https://adoptium.net/teapot/" -ForegroundColor White
        exit 1
    }
}

# Step 3: Install Java 17
Write-Host "`n[3/6] Installing Java 17 LTS..." -ForegroundColor Yellow
Write-Host "      This may take 2-3 minutes..." -ForegroundColor Gray

$installArgs = @(
    '/i'
    $installerPath
    '/quiet'
    '/norestart'
    'ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome'
    'INSTALLDIR=C:\Program Files\Eclipse Adoptium\jdk-17'
)

try {
    $process = Start-Process 'msiexec.exe' -ArgumentList $installArgs -Wait -PassThru -NoNewWindow

    if ($process.ExitCode -eq 0) {
        Write-Host "      [OK] Installation complete!" -ForegroundColor Green
    } else {
        Write-Host "      [WARNING] Installation exit code: $($process.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "      [ERROR] Installation failed: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Find Java 17 installation
Write-Host "`n[4/6] Locating Java 17 installation..." -ForegroundColor Yellow

$possiblePaths = @(
    "C:\Program Files\Eclipse Adoptium\jdk-17*",
    "C:\Program Files\Eclipse Adoptium\jdk17*",
    "C:\Program Files\Temurin\jdk-17*"
)

$javaHome = $null
foreach ($path in $possiblePaths) {
    $found = Get-Item $path -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $javaHome = $found.FullName
        break
    }
}

if ($javaHome) {
    Write-Host "      [OK] Found Java 17 at: $javaHome" -ForegroundColor Green
} else {
    Write-Host "      [ERROR] Could not locate Java 17 installation" -ForegroundColor Red
    Write-Host "      Checking C:\Program Files\Eclipse Adoptium\" -ForegroundColor Yellow
    Get-ChildItem "C:\Program Files\Eclipse Adoptium" -ErrorAction SilentlyContinue
    exit 1
}

# Step 5: Set environment variables (current session)
Write-Host "`n[5/6] Setting environment variables..." -ForegroundColor Yellow

$env:JAVA_HOME = $javaHome
$env:PATH = "$javaHome\bin;$env:PATH"

Write-Host "      [OK] JAVA_HOME = $env:JAVA_HOME" -ForegroundColor Green
Write-Host "      [OK] PATH updated" -ForegroundColor Green

# Step 6: Verify installation
Write-Host "`n[6/6] Verifying Java 17 installation..." -ForegroundColor Yellow

try {
    # Force reload of PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Check java version
    $javaCmd = Join-Path $javaHome "bin\java.exe"
    if (Test-Path $javaCmd) {
        $newVersion = & $javaCmd -version 2>&1 | Select-String "version" | ForEach-Object { $_.Line }
        Write-Host "      New Java version: $newVersion" -ForegroundColor Gray

        if ($newVersion -match "17") {
            Write-Host "`n[OK] Java 17 successfully installed!" -ForegroundColor Green
        } else {
            Write-Host "`n[WARNING] Java version mismatch" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "      [WARNING] Verification failed: $_" -ForegroundColor Yellow
}

# Final instructions
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "IMPORTANT: To use Java 17, you need to:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Close this terminal" -ForegroundColor White
Write-Host "2. Open a NEW terminal (PowerShell or Command Prompt)" -ForegroundColor White
Write-Host "3. Verify Java 17 is active:" -ForegroundColor White
Write-Host "   java -version" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Deploy your app:" -ForegroundColor White
Write-Host "   cd C:\Users\pqm847\Documents\PromptOps" -ForegroundColor Gray
Write-Host "   python mobile-deployment\deploy_android_app.py \" -ForegroundColor Gray
Write-Host "     --repo-url https://github.com/kirankumarhs29/netSenseAI \" -ForegroundColor Gray
Write-Host "     --app-name `"netSenseAI`" \" -ForegroundColor Gray
Write-Host "     --option A \" -ForegroundColor Gray
Write-Host "     --aws-bucket netsense-ai-2026" -ForegroundColor Gray
Write-Host ""
Write-Host "Or use the web UI at: http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "================================================================`n" -ForegroundColor Cyan
