# PromptOps Deployment Fix - Complete Guide

⚠️ **UPDATE**: This issue has been **FIXED**. See [DEPLOYMENT_ISSUE_FIXED.md](DEPLOYMENT_ISSUE_FIXED.md) for the solution.

## Current Status (Verified ✅)

### Backend API
- **Status**: ✅ Running
- **Port**: 3800
- **Health**: http://localhost:3800/health
- **Deploy Endpoint**: http://localhost:3800/api/v1/deploy/aws
- **Test Result**: Endpoint responding correctly

```bash
# Test command (successful):
curl http://localhost:3800/health
# Result: {"status":"healthy","version":"1.0.0",...}

curl -X POST http://localhost:3800/api/v1/deploy/aws -H "Content-Type: application/json" -d '{"source_path":"test","bucket_name":"test"}'
# Result: {"detail":"Source directory not found: test"} - Expected, endpoint is working!
```

### Frontend Configuration
- ✅ `.env` updated to port 3800
- ✅ `.env.development` updated to port 3800
- ⚠️ **ISSUE**: Frontend dev server NOT restarted - still using old cached config

## Root Cause Analysis

The error in your screenshot shows:
```
Failed to fetch at APIClient.request (http://localhost:3804/src/api/client.ts:38:28)
```

**Problem**: The frontend is using **cached/stale** configuration. Environment variables are only loaded when Vite starts.

## Solution Steps (YOU MUST DO)

### Step 1: Kill Any Running Frontend Process
```bash
# Windows - Find and kill node processes
taskkill /F /IM node.exe

# Or close the terminal window running npm run dev
```

### Step 2: Clear Vite Cache
```bash
cd frontend/dashboard
rm -rf node_modules/.vite
rm -rf dist
```

### Step 3: Start Frontend Fresh
```bash
cd frontend/dashboard
npm run dev
```

### Step 4: Verify Configuration
Once the dev server starts, check the browser console:
```javascript
// In browser console:
console.log(import.meta.env.VITE_API_BASE_URL)
// Should show: http://localhost:3800
```

### Step 5: Test Deployment Again
1. Go to the deployment page
2. Fill in the form with jewelry-vault repo
3. Click "Approve & Execute"
4. Watch the enhanced error logs

## Alternative: Use Production Build

If dev server issues persist, use the production build:

```bash
cd frontend/dashboard
npm run build
npm run preview
```

Then access at http://localhost:4173

## Backend Stability

To keep backend running permanently:

```bash
cd api_gateway

# Windows (PowerShell):
Start-Process python -ArgumentList "-m","uvicorn","main:app","--host","0.0.0.0","--port","3800" -WindowStyle Hidden

# Or use nohup (Git Bash):
nohup python -m uvicorn main:app --host 0.0.0.0 --port 3800 > ../backend.log 2>&1 &
```

## Verification Checklist

Before trying deployment again:

- [ ] Backend health check passes: `curl http://localhost:3800/health`
- [ ] Deploy endpoint exists: `curl http://localhost:3800/api/v1/deploy/status`
- [ ] Frontend dev server restarted (NEW terminal session)
- [ ] Browser shows correct API URL in console
- [ ] Browser has no cached service workers (F12 > Application > Clear storage)

## Expected Deployment Flow

When working correctly:

1. ✅ Pre-flight checks started
2. ✅ PM approval and security review validated
3. ✅ Deployment plan prepared
4. ✅ AWS credential mode verified
5. ✅ Calling deployment API
6. Then either:
   - ✅ Success: Files uploaded to S3
   - ❌ AWS Error: Detailed logs show credential/permission issues

## Common Issues & Solutions

### Issue: "Failed to fetch"
- **Cause**: Backend not running OR wrong port
- **Solution**: Check backend with `curl http://localhost:3800/health`

### Issue: "Source directory not found"
- **Cause**: Invalid source_path in request
- **Solution**: Ensure source path exists: `C:\Users\pqm847\Documents\jewelry-vault`

### Issue: "AWS credentials invalid"
- **Cause**: No AWS credentials configured
- **Solution**: Either:
  1. Configure AWS CLI: `aws configure`
  2. Or use manual credentials in the deployment form

### Issue: "Permission denied"
- **Cause**: AWS credentials lack S3 permissions
- **Solution**: Verify IAM permissions include:
  - s3:CreateBucket
  - s3:PutObject
  - s3:PutBucketPolicy
  - s3:PutBucketWebsite

## Current Configuration Files

### frontend/dashboard/.env
```
VITE_API_BASE_URL=http://localhost:3800
```

### frontend/dashboard/.env.development
```
VITE_API_BASE_URL=http://localhost:3800
VITE_DRIFT_POLLING_INTERVAL=60000
VITE_AUDIT_REFRESH_INTERVAL=30000
VITE_ENABLE_AUTO_REFRESH=true
```

## Next Actions

**YOU MUST DO THESE STEPS:**

1. Stop the frontend dev server (Ctrl+C or close terminal)
2. Clear Vite cache: `rm -rf frontend/dashboard/node_modules/.vite`
3. Start fresh: `cd frontend/dashboard && npm run dev`
4. Open browser in incognito mode (to avoid cache)
5. Try deployment again

**CRITICAL**: The frontend MUST be restarted to pick up the new environment variables!
