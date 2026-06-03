# CloudWatch Observability - Quick Setup Guide

## What We Built

A comprehensive CloudWatch observability dashboard integrated into PromptOps UI that provides:
- ✅ Real-time metrics monitoring (CPU, Memory, Requests, Errors, Latency)
- ✅ Application health status tracking
- ✅ Live log streaming from CloudWatch Logs
- ✅ CloudWatch alarms and alerts
- ✅ Multi-deployment support
- ✅ Auto-refresh capabilities
- ✅ Security vulnerability detection

## Files Created/Modified

### Frontend Files
1. **`frontend/dashboard/src/pages/ObservabilityDashboard.tsx`** (NEW)
   - Complete React dashboard component
   - Real-time metric charts with SVG visualization
   - Health status cards
   - Log viewer with auto-refresh
   - Alert management UI

2. **`frontend/dashboard/src/App.tsx`** (MODIFIED)
   - Added ObservabilityDashboard import
   - Added 'observability' to Page type
   - Added navigation button (📊 Observability)
   - Added route for observability page

### Backend Files
3. **`api_gateway/cloudwatch_routes.py`** (NEW)
   - Complete FastAPI router for CloudWatch integration
   - Metrics endpoint with S3 and CloudFront support
   - Health check endpoint
   - Logs streaming endpoint
   - Alerts endpoint
   - Deployments discovery endpoint
   - Mock data fallback for demo purposes

4. **`api_gateway/main.py`** (MODIFIED)
   - Added cloudwatch_routes import
   - Registered CloudWatch router at `/api/v1/monitoring/cloudwatch`

### Documentation
5. **`CLOUDWATCH_OBSERVABILITY.md`** (NEW)
   - Comprehensive documentation
   - Architecture diagrams
   - API endpoint reference
   - Usage guide
   - Security considerations
   - Troubleshooting guide

## Quick Start

### 1. Start the Backend
```bash
cd api_gateway
python main.py
```

### 2. Start the Frontend
```bash
cd frontend/dashboard
npm install
npm start
```

### 3. Access the Dashboard
1. Open http://localhost:3000
2. Log in to PromptOps
3. Click **📊 Observability** in the navigation bar

## AWS Configuration (Optional)

### For Real CloudWatch Data
Create `.env` file in `api_gateway/`:
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

### Required IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:DescribeAlarms",
        "logs:FilterLogEvents",
        "s3:GetBucketWebsite",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    }
  ]
}
```

## Features Overview

### 📊 Metrics Dashboard
- **CPU Usage**: Track CPU utilization over time
- **Memory Usage**: Monitor memory consumption
- **Request Rate**: View incoming request volumes
- **Error Rate**: Identify error spikes
- **Response Time (p95)**: Monitor application latency

### 💚 Health Status
- **Visual Indicators**: Green (Healthy), Yellow (Degraded), Red (Critical)
- **Uptime Tracking**: Real-time uptime percentage
- **Issue Detection**: Automatic problem identification
- **Direct App Links**: Quick access to deployed applications

### 📋 Log Streaming
- **Real-Time Logs**: Live application logs from CloudWatch
- **Auto-Refresh**: Configurable 30-second refresh
- **Filter Support**: Search logs by patterns
- **Historical Access**: Review past log entries

### 🚨 Alert Management
- **CloudWatch Alarms**: Integration with AWS alarms
- **Severity Levels**: Critical and Warning classifications
- **Alert History**: Track alert patterns
- **Visual Notifications**: Clear alert indicators

### ⏱️ Time Range Control
- **1h**: Last 1 hour (real-time monitoring)
- **6h**: Last 6 hours (short-term trends)
- **24h**: Last 24 hours (daily patterns)
- **7d**: Last 7 days (weekly trends)

## Testing Production Issues

### Performance Degradation
1. Navigate to Observability dashboard
2. Check Latency chart for sustained spikes
3. Review CPU/Memory metrics for resource constraints
4. Examine logs for slow queries or errors

### Error Spikes
1. Monitor Error Rate chart
2. Check for recent deployment changes
3. Review error logs for stack traces
4. Verify CloudWatch alarms

### Security Vulnerabilities
1. Look for unusual Request Rate patterns
2. Check logs for authentication failures
3. Review error messages for security events
4. Verify no unauthorized access attempts

### Resource Exhaustion
1. Monitor CPU/Memory charts approaching 80-100%
2. Check for sustained high usage
3. Review logs for memory leaks
4. Consider scaling resources

## API Endpoints

All endpoints are prefixed with `/api/v1/monitoring/cloudwatch`

- `GET /metrics` - Fetch deployment metrics
- `GET /health/{deployment}` - Check deployment health
- `GET /logs/{deployment}` - Stream application logs
- `GET /alerts/{deployment}` - Get active alerts
- `GET /deployments/list` - List all deployments
- `GET /dashboard/summary` - Overall health summary

## Demo Mode

The system includes intelligent fallback to mock data when:
- AWS credentials are not configured
- CloudWatch API calls fail
- No real metrics are available

This allows you to:
- ✅ Demo the UI without AWS setup
- ✅ Test frontend functionality
- ✅ Show stakeholders the interface
- ✅ Develop without cloud dependencies

## Next Steps

### Immediate
1. ✅ Test the UI in your browser
2. ✅ Review the mock data visualization
3. ✅ Try different time ranges
4. ✅ Test auto-refresh functionality

### Short-term
1. Configure AWS credentials for real data
2. Set up CloudWatch alarms for your deployments
3. Configure log groups for your applications
4. Test with actual production deployments

### Long-term
1. Add custom metric dashboards
2. Implement alert notification system (Slack, email)
3. Add anomaly detection with ML
4. Expand to GCP and Azure monitoring
5. Integrate with incident management system

## Troubleshooting

### Issue: Observability button not visible
**Solution**: Clear browser cache and refresh

### Issue: No data displayed
**Solution**: Check backend logs, verify API endpoints are registered

### Issue: "Failed to fetch" errors
**Solution**: Ensure backend is running on correct port, check CORS configuration

### Issue: AWS authentication errors
**Solution**: Verify AWS credentials in environment variables, check IAM permissions

## Architecture Diagram

```
User Browser
    ↓
React Dashboard (ObservabilityDashboard.tsx)
    ↓
API Client (apiClient.get/post)
    ↓
FastAPI Backend (cloudwatch_routes.py)
    ↓
Boto3 SDK
    ↓
AWS CloudWatch / CloudWatch Logs / CloudFront
```

## Integration Points

### Existing PromptOps Features
- **Deployment System**: Auto-discovers deployed applications
- **Auth System**: Uses existing authentication
- **Audit Trail**: Logs all observability actions
- **ML Monitoring**: Integrates with existing ML routes

### External Systems
- **AWS CloudWatch**: Metrics and alarms
- **CloudWatch Logs**: Application logs
- **S3**: Static website metrics
- **CloudFront**: CDN performance metrics

## Security Notes

⚠️ **Important Security Considerations**:
1. Never commit AWS credentials to git
2. Use IAM roles instead of access keys when possible
3. Enable MFA for production AWS accounts
4. Rotate credentials regularly
5. Use least-privilege IAM policies
6. Monitor CloudTrail for suspicious activity

## Support

Need help? Check:
1. `CLOUDWATCH_OBSERVABILITY.md` - Full documentation
2. Backend logs in `api_gateway/backend.log`
3. Browser console for frontend errors
4. Network tab in DevTools for API calls

## Success Criteria ✅

You've successfully set up CloudWatch Observability when:
- ✅ You can see the 📊 Observability button
- ✅ The dashboard loads without errors
- ✅ Metrics charts display data (mock or real)
- ✅ Health status shows correctly
- ✅ Logs are visible in the log viewer
- ✅ Time range selection works
- ✅ Auto-refresh toggles properly

---

**Built with PromptOps** | Cloud-Native DevOps Automation Platform
