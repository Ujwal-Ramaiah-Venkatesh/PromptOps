@echo off
echo ========================================
echo Security & Performance Monitoring Test
echo ========================================
echo.

REM Set your deployed app details here
set TARGET_URL=https://jewelry-vault-deploy.s3-website-us-east-1.amazonaws.com
set BUCKET_NAME=jewelry-vault-deploy
set API_URL=http://localhost:8000

echo Testing monitoring system...
echo Target URL: %TARGET_URL%
echo Bucket: %BUCKET_NAME%
echo.

echo ========================================
echo Test 1: Get System Metrics
echo ========================================
curl -X GET "%API_URL%/api/v1/advanced-monitoring/metrics/system"
echo.
echo.

echo ========================================
echo Test 2: Get Dashboard Summary
echo ========================================
curl -X GET "%API_URL%/api/v1/advanced-monitoring/dashboard/summary"
echo.
echo.

echo ========================================
echo Test 3: Run Security Scan
echo ========================================
curl -X POST "%API_URL%/api/v1/advanced-monitoring/tests/security" ^
  -H "Content-Type: application/json" ^
  -d "{\"target_url\": \"%TARGET_URL%\", \"bucket_name\": \"%BUCKET_NAME%\", \"region\": \"us-east-1\", \"scan_depth\": \"comprehensive\", \"check_ssl\": true, \"check_headers\": true, \"check_vulnerabilities\": true}"
echo.
echo Security scan started! Check the UI for results.
echo.

echo ========================================
echo Test 4: Run Quick Load Test
echo ========================================
curl -X POST "%API_URL%/api/v1/advanced-monitoring/tests/load" ^
  -H "Content-Type: application/json" ^
  -d "{\"target_url\": \"%TARGET_URL%\", \"duration_seconds\": 30, \"concurrent_users\": 10, \"requests_per_second\": 50, \"ramp_up_seconds\": 5, \"test_type\": \"load_test\"}"
echo.
echo Load test started! Monitor progress in the UI.
echo.

echo ========================================
echo Waiting 35 seconds for tests to complete...
echo ========================================
timeout /t 35 /nobreak
echo.

echo ========================================
echo Test 5: Get Active Tests
echo ========================================
curl -X GET "%API_URL%/api/v1/advanced-monitoring/tests/active"
echo.
echo.

echo ========================================
echo Test 6: Get Alerts
echo ========================================
curl -X GET "%API_URL%/api/v1/advanced-monitoring/alerts?limit=10"
echo.
echo.

echo ========================================
echo All tests completed!
echo ========================================
echo.
echo Next steps:
echo 1. Open http://localhost:3000 in your browser
echo 2. Navigate to "Security Monitor" tab
echo 3. Review test results and alerts
echo 4. Try manual tests from the UI
echo.
pause
