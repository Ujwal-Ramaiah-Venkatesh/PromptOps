<div align="center">
  <img src="assets/promptops-logo.png" alt="PromptOps Logo" width="200"/>
  
  # CloudWatch Observability Integration
</div>

## Overview

The CloudWatch Observability feature provides real-time monitoring, health checks, and security analysis for all deployed applications in the PromptOps platform. This integration helps detect production issues, security vulnerabilities, and performance degradation before they impact users.

## Features

### 1. **Real-Time Metrics Dashboard**
- **CPU Usage**: Monitor application CPU utilization trends
- **Memory Usage**: Track memory consumption patterns
- **Request Rate**: View incoming request volumes
- **Error Rate**: Identify error spikes and patterns
- **Response Time (p95)**: Monitor application latency at 95th percentile

### 2. **Health Status Monitoring**
- **Uptime Tracking**: Real-time uptime percentage
- **Status Indicators**: Visual health status (Healthy/Degraded/Critical)
- **Issue Detection**: Automatic identification of problems
- **Resource Checks**: Verification of all deployment resources

### 3. **Log Streaming**
- **Real-Time Logs**: Live application log streaming
- **Log Search**: Filter logs by patterns and timestamps
- **Error Tracking**: Automatic error log highlighting
- **Historical Access**: Access logs from past deployments

### 4. **Alert Management**
- **CloudWatch Alarms**: Integration with AWS CloudWatch alarms
- **Severity Levels**: Critical and Warning alert classifications
- **Alert History**: Track alert patterns over time
- **Notification**: Real-time alert notifications

### 5. **Multi-Deployment Support**
- **Deployment Selector**: Switch between different deployments
- **Environment Filtering**: View production, staging, or development metrics
- **Multi-Region**: Support for deployments across AWS regions
- **Multi-Cloud Ready**: Architecture supports GCP and Azure expansion

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PromptOps UI                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Observability Dashboard (React Component)           │   │
│  │  - Metric Charts                                     │   │
│  │  - Health Status Cards                               │   │
│  │  - Log Viewer                                        │   │
│  │  - Alert Notifications                               │   │
│  └───────────────────┬──────────────────────────────────┘   │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ REST API Calls
                         │
┌────────────────────────▼────────────────────────────────────┐
│              API Gateway (FastAPI)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CloudWatch Routes Module                            │   │
│  │  - /api/v1/monitoring/cloudwatch/metrics             │   │
│  │  - /api/v1/monitoring/cloudwatch/health              │   │
│  │  - /api/v1/monitoring/cloudwatch/logs                │   │
│  │  - /api/v1/monitoring/cloudwatch/alerts              │   │
│  └───────────────────┬──────────────────────────────────┘   │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ Boto3 SDK
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   AWS CloudWatch                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Metrics    │  │     Logs     │  │    Alarms    │      │
│  │              │  │              │  │              │      │
│  │ - CPU        │  │ - App Logs   │  │ - Thresholds │      │
│  │ - Memory     │  │ - Error Logs │  │ - Triggers   │      │
│  │ - Network    │  │ - Access Logs│  │ - Actions    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Metrics Endpoint
```http
GET /api/v1/monitoring/cloudwatch/metrics
```

**Query Parameters:**
- `deployment`: Deployment name (required)
- `environment`: Environment (default: "production")
- `hours`: Time range in hours (1-168, default: 1)
- `region`: AWS region (default: "us-east-1")

**Response:**
```json
{
  "deployment": "jewelry-vault",
  "environment": "production",
  "region": "us-east-1",
  "time_range": {
    "start": "2026-06-03T06:00:00",
    "end": "2026-06-03T07:00:00",
    "hours": 1
  },
  "metrics": {
    "cpu": [...],
    "memory": [...],
    "requests": [...],
    "errors": [...],
    "latency": [...]
  }
}
```

### Health Check Endpoint
```http
GET /api/v1/monitoring/cloudwatch/health/{deployment}
```

**Response:**
```json
{
  "status": "healthy",
  "uptime": 99.95,
  "lastCheck": "2026-06-03T07:30:00",
  "issues": [],
  "checks": {
    "endpoint": "healthy",
    "metrics": "healthy",
    "alarms": "no_alarms",
    "resources": "healthy"
  }
}
```

### Logs Endpoint
```http
GET /api/v1/monitoring/cloudwatch/logs/{deployment}
```

**Query Parameters:**
- `environment`: Environment (default: "production")
- `limit`: Maximum log entries (1-10000, default: 100)
- `filter_pattern`: Optional log filter pattern

**Response:**
```json
{
  "deployment": "jewelry-vault",
  "environment": "production",
  "total": 100,
  "logs": [
    "[2026-06-03T07:30:00] Application started successfully",
    "[2026-06-03T07:30:01] Connected to database",
    ...
  ]
}
```

### Alerts Endpoint
```http
GET /api/v1/monitoring/cloudwatch/alerts/{deployment}
```

**Response:**
```json
{
  "deployment": "jewelry-vault",
  "environment": "production",
  "total": 2,
  "alerts": [
    {
      "title": "High Error Rate",
      "message": "Error rate exceeded threshold",
      "severity": "critical",
      "timestamp": "2026-06-03T07:25:00",
      "metric": "ErrorCount",
      "threshold": 10
    }
  ]
}
```

### Deployments List Endpoint
```http
GET /api/v1/monitoring/cloudwatch/deployments/list
```

**Response:**
```json
{
  "total": 1,
  "deployments": [
    {
      "name": "jewelry-vault",
      "environment": "production",
      "version": "v1.2.3",
      "deployedAt": "2026-06-03T06:00:00",
      "url": "https://app-promptops-891400.s3.us-east-1.amazonaws.com/index.html",
      "region": "us-east-1",
      "provider": "AWS"
    }
  ]
}
```

## Usage Guide

### Accessing the Dashboard

1. **Navigate to Observability**
   - Log into PromptOps dashboard
   - Click the **"📊 Observability"** button in the navigation bar

2. **Select Deployment**
   - Use the deployment selector dropdown
   - Choose the application you want to monitor

3. **View Metrics**
   - Review real-time metrics in the chart grid
   - Each chart shows the last selected time range (1h, 6h, 24h, 7d)

4. **Check Health Status**
   - View the health card at the top
   - Green status = Healthy
   - Yellow status = Degraded
   - Red status = Critical

5. **Monitor Logs**
   - Scroll to the bottom to view recent logs
   - Logs auto-refresh every 30 seconds if enabled

6. **Review Alerts**
   - Active alerts appear in the alerts section
   - Click on alerts for more details

### Time Range Selection

Use the time range buttons to adjust the metrics view:
- **1h**: Last 1 hour (5-minute intervals)
- **6h**: Last 6 hours
- **24h**: Last 24 hours
- **7d**: Last 7 days

### Auto-Refresh

Enable auto-refresh to automatically update metrics every 30 seconds:
- Toggle the **"Auto-refresh (30s)"** checkbox
- Useful for monitoring production deployments in real-time

## Security Considerations

### 1. **AWS Credentials**
The CloudWatch integration requires AWS credentials with appropriate permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:DescribeAlarms",
        "logs:FilterLogEvents",
        "logs:GetLogEvents",
        "s3:GetBucketWebsite",
        "s3:ListBucket",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. **Environment Variables**
Configure AWS credentials securely:

```bash
# .env file
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### 3. **IAM Best Practices**
- Use IAM roles for EC2/ECS deployments instead of access keys
- Enable MFA for IAM users
- Rotate credentials regularly
- Use least-privilege principle

### 4. **Network Security**
- API endpoints should be behind authentication
- Use HTTPS for all communications
- Implement rate limiting on monitoring endpoints

## Testing Production Issues

The observability dashboard helps identify and troubleshoot:

### 1. **Performance Issues**
- **Symptom**: High latency (p95 > 500ms)
- **Detection**: Latency chart shows sustained spikes
- **Action**: Check CPU/Memory metrics, review logs for slow queries

### 2. **Error Spikes**
- **Symptom**: Increased error rate
- **Detection**: Errors chart shows spikes
- **Action**: Review error logs, check for deployment changes

### 3. **Resource Exhaustion**
- **Symptom**: High CPU/Memory usage
- **Detection**: CPU/Memory charts near 80-100%
- **Action**: Scale resources, optimize code, check for memory leaks

### 4. **Availability Issues**
- **Symptom**: Health status degraded/critical
- **Detection**: Red status indicator, uptime < 99%
- **Action**: Check CloudWatch alarms, review recent deployments

### 5. **Security Vulnerabilities**
- **Symptom**: Unusual traffic patterns, authentication failures
- **Detection**: Request rate anomalies, error logs with security events
- **Action**: Review access logs, check for suspicious IPs, rotate credentials

## Integration with Existing Systems

### ML Model Monitoring
The observability dashboard integrates with existing ML monitoring routes:
- `/api/v1/monitoring/metrics/{model_name}`
- `/api/v1/monitoring/drift/prediction`
- `/api/v1/monitoring/retrain/check`

### CI/CD Integration
CloudWatch metrics can trigger automated actions:
- Rollback deployments on critical errors
- Scale resources based on load
- Alert teams via Slack/Email

### Cost Optimization
Use observability data to:
- Identify over-provisioned resources
- Optimize resource allocation
- Track cost per request/transaction

## Troubleshooting

### Issue: No Metrics Displayed
**Cause**: CloudWatch credentials not configured or insufficient permissions
**Solution**: 
1. Verify AWS credentials in environment variables
2. Check IAM permissions for CloudWatch access
3. Review backend logs for authentication errors

### Issue: Stale Data
**Cause**: Auto-refresh disabled or API endpoint errors
**Solution**:
1. Enable auto-refresh checkbox
2. Manually refresh by changing time range
3. Check network connectivity to backend API

### Issue: Missing Deployments
**Cause**: Deployment not tagged or not in database
**Solution**:
1. Ensure deployment is tracked in system
2. Verify S3 bucket has website hosting enabled
3. Check deployment tags and metadata

## Future Enhancements

### Planned Features
1. **Custom Dashboards**: Create personalized metric views
2. **Alert Configuration**: Set custom thresholds and notifications
3. **Anomaly Detection**: ML-powered anomaly detection
4. **Cost Analysis**: Track cost metrics per deployment
5. **Multi-Cloud Support**: GCP and Azure observability
6. **Performance Baselines**: Automated baseline detection
7. **Incident Management**: Integrated incident tracking
8. **SLA Tracking**: Service level agreement monitoring

### Integration Roadmap
- [ ] Slack alert notifications
- [ ] PagerDuty integration
- [ ] Datadog forwarding
- [ ] Prometheus export
- [ ] Grafana dashboards
- [ ] Custom metric plugins

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/yourorg/promptops/issues
- **Documentation**: https://docs.promptops.com/observability
- **Email**: support@promptops.com

## License

This feature is part of the PromptOps platform and follows the same license terms.
