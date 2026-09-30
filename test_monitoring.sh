#!/bin/bash

echo "=========================================="
echo "Post-Deployment Monitoring Test Script"
echo "=========================================="
echo ""

# Configuration
API_BASE="http://localhost:3800"
APP_NAME="jewelry-vault"
DEPLOYMENT_URL="http://jewelry-vault-promptops-123456.s3-website-us-east-1.amazonaws.com"
BUCKET_NAME="jewelry-vault-promptops-123456"

echo "Testing API: $API_BASE"
echo "App: $APP_NAME"
echo ""

# Step 1: Register application for monitoring
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Register Application for Monitoring"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "$API_BASE/api/v1/monitor/deployed/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"app_name\": \"$APP_NAME\",
    \"deployment_url\": \"$DEPLOYMENT_URL\",
    \"bucket_name\": \"$BUCKET_NAME\",
    \"region\": \"us-east-1\",
    \"check_interval_seconds\": 60,
    \"enable_auto_scaling\": true,
    \"enable_security_scan\": true
  }" | python -m json.tool 2>/dev/null || echo "Failed to parse JSON"

echo ""
echo ""
sleep 2

# Step 2: Check health status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Check Health Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_BASE/api/v1/monitor/deployed/health/$APP_NAME" | python -m json.tool 2>/dev/null || echo "Failed"

echo ""
echo ""
sleep 2

# Step 3: Get security vulnerabilities
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Security Vulnerability Scan"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_BASE/api/v1/monitor/deployed/security/$APP_NAME?rescan=true" | python -m json.tool 2>/dev/null || echo "Failed"

echo ""
echo ""
sleep 2

# Step 4: Get performance metrics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Performance Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_BASE/api/v1/monitor/deployed/performance/$APP_NAME?hours=1" | python -m json.tool 2>/dev/null || echo "Failed"

echo ""
echo ""
sleep 2

# Step 5: Get scaling recommendations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Auto-Scaling Recommendations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_BASE/api/v1/monitor/deployed/scaling/$APP_NAME" | python -m json.tool 2>/dev/null || echo "Failed"

echo ""
echo ""
sleep 2

# Step 6: Get overall monitoring status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Overall Monitoring Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_BASE/api/v1/monitor/deployed/status/$APP_NAME" | python -m json.tool 2>/dev/null || echo "Failed"

echo ""
echo ""
sleep 2

# Step 7: List all monitored applications
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: List All Monitored Applications"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API_BASE/api/v1/monitor/deployed/list" | python -m json.tool 2>/dev/null || echo "Failed"

echo ""
echo ""
echo "=========================================="
echo "✅ Monitoring Test Complete"
echo "=========================================="
echo ""
echo "The monitoring system is tracking:"
echo "  • Health checks every 60 seconds"
echo "  • Security vulnerability scanning"
echo "  • Performance metrics"
echo "  • Auto-scaling recommendations"
echo ""
echo "View API docs: $API_BASE/docs"
echo ""
