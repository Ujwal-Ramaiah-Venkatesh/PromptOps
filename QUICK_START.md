# PromptOps - Quick Start Guide

🚀 **NEW**: GitHub deployment is now fully working! Deploy any static site from GitHub to AWS S3.

## ✨ Fresh Clean Start

Everything has been cleaned and reset. Follow these simple steps:

## Method 1: Automated Start (Recommended)

### Windows:
```bash
START_FRESH.bat
```

### Linux/Mac:
```bash
chmod +x START_FRESH.sh
./START_FRESH.sh
```

## Method 2: Manual Start

### Terminal 1 - Backend:
```bash
cd api_gateway
python -m uvicorn main:app --host 0.0.0.0 --port 3800 --reload
```

### Terminal 2 - Frontend:
```bash
cd frontend/dashboard
npm run dev
```

## Access
- Frontend: http://localhost:3000
- Backend: http://localhost:3800
- API Docs: http://localhost:3800/docs

## Features ✓

### Deployment
- ✅ GitHub Repository Deployment - Deploy from any public GitHub repo
- ✅ Local File Deployment - Deploy from local directories
- ✅ AWS S3 Static Hosting - Automatic bucket creation and configuration
- ✅ Valid S3 Bucket Names - Smart sanitization for compliance
- ✅ Android App Deployment - Mobile artifact hosting
- ✅ Intelligent Routing - Auto-detects deployment type

### Post-Deployment Monitoring 🆕
- ✅ Health Checks - Continuous uptime and response time monitoring
- ✅ Security Scanning - Automated vulnerability detection (5 checks)
- ✅ Performance Metrics - Response time, error rate, traffic analysis
- ✅ Auto-Scaling Recommendations - Intelligent capacity suggestions
- ✅ Real-time Alerts - Immediate notification of issues

## Example Deployments

### Deploy from GitHub:
```
Deploy jewelry vault from https://github.com/ashi100sh/jewelry-vault
```

### Deploy local app:
```
Deploy my-awesome-app
```

## Documentation

### Deployment
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - Full deployment guide
- [S3_BUCKET_NAME_FIX.md](S3_BUCKET_NAME_FIX.md) - Bucket naming details
- [test_bucket_names.html](test_bucket_names.html) - Test suite (open in browser)

### Monitoring 🆕
- [MONITORING_SYSTEM_COMPLETE.md](MONITORING_SYSTEM_COMPLETE.md) - Complete monitoring guide
- [POST_DEPLOYMENT_MONITORING.md](POST_DEPLOYMENT_MONITORING.md) - API documentation
- [test_monitoring.bat](test_monitoring.bat) / [test_monitoring.sh](test_monitoring.sh) - Test scripts

## Quick Test Monitoring

```bash
# Windows
test_monitoring.bat

# Linux/Mac
chmod +x test_monitoring.sh
./test_monitoring.sh
```
