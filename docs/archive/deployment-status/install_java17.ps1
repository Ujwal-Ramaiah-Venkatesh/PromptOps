# Install Java 17 LTS
# ====================

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "  Installing Java 17 LTS for Android Development" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

$installerPath = "C:\Users\pqm847\Downloads\jdk17.msi"

# Check if installer exists
if (Test-Path $installerPath) {
    Write-Host "[OK] Installer found: $installerPath" -ForegroundColor Green

    # Install Java 17
    Write-Host "`nInstalling Java 17 (this may take 2-3 minutes)..." -ForegroundColor Yellow

    # Silent installation with required features
    $installArgs = @(
        "/i", $installerPath,
        "/quiet",
        "/norestart",
        "ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome",
        "INSTALLDIR=C:\Program Files\Eclipse Adoptium\jdk-17"
    )

    Start-Process "msiexec.exe" -ArgumentList $installArgs -Wait -NoNewWindow

    Write-Host "[OK] Java 17 installed successfully!" -ForegroundColor Green

    # Set environment variables for current session
    $javaHome = "C:\Program Files\Eclipse Adoptium\jdk-17"

    if (Test-Path $javaHome) {
        $env:JAVA_HOME = $javaHome
        $env:PATH = "$javaHome\bin;$env:PATH"

        Write-Host "`n[OK] Environment variables set:" -ForegroundColor Green
        Write-Host "  JAVA_HOME = $env:JAVA_HOME" -ForegroundColor Gray
        Write-Host "  PATH updated with Java 17 bin directory" -ForegroundColor Gray

        # Verify installation
        Write-Host "`nVerifying Java installation..." -ForegroundColor Yellow
        & java -version

        Write-Host "`n===============================================" -ForegroundColor Cyan
        Write-Host "  Java 17 Installation Complete!" -ForegroundColor Cyan
        Write-Host "===============================================" -ForegroundColor Cyan
        Write-Host "`nYou can now deploy netSenseAI:" -ForegroundColor Green
        Write-Host "  cd C:\Users\pqm847\Documents\PromptOps" -ForegroundColor White
        Write-Host "  python mobile-deployment\deploy_android_app.py \" -ForegroundColor White
        Write-Host "    --repo-url https://github.com/kirankumarhs29/netSenseAI \" -ForegroundColor White
        Write-Host "    --app-name 'netSenseAI' \" -ForegroundColor White
        Write-Host "    --option A \" -ForegroundColor White
        Write-Host "    --aws-bucket netsense-ai-2026" -ForegroundColor White
        Write-Host ""

    } else {
        Write-Host "[ERROR] Installation directory not found: $javaHome" -ForegroundColor Red
        Write-Host "Java may have been installed to a different location." -ForegroundColor Yellow
        Write-Host "Please check: C:\Program Files\Eclipse Adoptium\" -ForegroundColor Yellow
    }

} else {
    Write-Host "[ERROR] Installer not found: $installerPath" -ForegroundColor Red
    Write-Host "Please download Java 17 from: https://adoptium.net/teapot/" -ForegroundColor Yellow
}
