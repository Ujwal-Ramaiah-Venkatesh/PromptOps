# 🛡️ Security Monitor - Quick Usage Guide

## Where to Access

1. **Open your browser**: http://localhost:3000
2. **Look at the top navigation** - You'll see tabs like:
   ```
   [Home] [Autonomy] [Discovery] [Ingestion] [Observability] [🛡️ Security Monitor]
   ```
3. **Click on**: **🛡️ Security Monitor**

---

## What You'll See

### Page Layout:

```
┌─────────────────────────────────────────────────────────────────┐
│  🛡️ Security & Performance Monitoring                          │
│  Real-time monitoring, load testing, security scanning...       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Overview] [Tests] [Alerts] [Remediation]  ☑ Auto-refresh(10s)│
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 💻       │  │ 🧠       │  │ 💾       │  │ 🔄       │       │
│  │CPU Usage │  │Memory    │  │Disk      │  │Threads   │       │
│  │  12.5%   │  │  80.2%   │  │  36.9%   │  │   20     │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  🚨 Active Alerts                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │
│  │    0    │  │    0    │  │    0    │                         │
│  │Critical │  │  High   │  │  Total  │                         │
│  └─────────┘  └─────────┘  └─────────┘                         │
├─────────────────────────────────────────────────────────────────┤
│  ⚡ Quick Actions                                               │
│                                                                  │
│  Target URL:                                                    │
│  [https://jewelry-vault-deploy.s3-website-us-east-1.amazona...] │
│                                                                  │
│  S3 Bucket Name:                                                │
│  [jewelry-vault-deploy________________________________]          │
│                                                                  │
│  [🚀 Run Load Test] [🔒 Security Scan]                          │
│  [💥 Test High Load] [📈 Test CPU Spike]                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: Running Your First Test

### 1️⃣ **Enter Your App Details**

**In the "Target URL" field, type:**
```
https://jewelry-vault-deploy.s3-website-us-east-1.amazonaws.com
```

**In the "S3 Bucket Name" field, type:**
```
jewelry-vault-deploy
```

---

### 2️⃣ **Choose a Test to Run**

Click on any of these buttons:

#### **🚀 Run Load Test**
- **What it does**: Sends 100 requests/second for 60 seconds
- **Tests**: Response time, error rate, throughput
- **Duration**: ~60 seconds
- **Good for**: Checking if your app can handle normal traffic

#### **🔒 Security Scan**
- **What it does**: Checks for security vulnerabilities
- **Tests**: HTTPS, security headers, S3 bucket security
- **Duration**: ~30 seconds
- **Good for**: Finding security issues before hackers do

#### **💥 Test High Load**
- **What it does**: Simulates sudden traffic spike (500+ requests/sec)
- **Tests**: System resilience, error handling
- **Duration**: ~30 seconds
- **Good for**: Seeing if your app crashes under pressure

#### **📈 Test CPU Spike**
- **What it does**: Creates CPU-intensive operations
- **Tests**: CPU handling, performance degradation
- **Duration**: ~30 seconds
- **Good for**: Testing if high CPU usage affects your app

---

### 3️⃣ **Monitor the Test Progress**

After clicking a button, you'll see:
```
Alert: Load test started: LOAD-1717459200
Monitor the Tests tab for results.
```

**Now click on the "Tests" tab** (at the top) to see:
```
┌─────────────────────────────────────────────────────────────┐
│ 🧪 Test Results                                             │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ LOAD-1717459200                        [Running]        │ │
│ │ load_test                                               │ │
│ │                                                         │ │
│ │ Started: 6/3/2026, 10:30:00 AM                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Wait for it to show "[Completed]"**, then you'll see results like:
```json
{
  "total_requests": 6000,
  "successful_requests": 5980,
  "error_rate_percent": 0.33,
  "avg_response_time_ms": 145.2,
  "throughput_rps": 99.8
}
```

---

### 4️⃣ **Check for Alerts**

Click on the **"Alerts"** tab to see any issues found:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Monitoring Alerts                                        │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [HIGH] Missing Security Header                          │ │
│ │                                                         │ │
│ │ The Strict-Transport-Security security header is not   │ │
│ │ set                                                     │ │
│ │                                                         │ │
│ │ Resource: https://jewelry-vault-deploy...              │ │
│ │ Detected: 6/3/2026, 10:30 AM                           │ │
│ │                                                         │ │
│ │ [🔧 Auto-Remediate]                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Click "🔧 Auto-Remediate"** to automatically fix the issue!

---

### 5️⃣ **View Auto-Remediation**

Click on the **"Remediation"** tab to see:

```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Auto-Remediation                                         │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────┬─────────────────┐                          │
│ │  Total       │  Success Rate   │                          │
│ │  Actions     │                 │                          │
│ │              │                 │                          │
│ │    15        │     93.3%       │                          │
│ └──────────────┴─────────────────┘                          │
│                                                              │
│ Auto-Remediation Capabilities:                              │
│ • 🔄 Automatic service restarts on failures                 │
│ • 📈 Auto-scaling based on load patterns                    │
│ • 🧹 Cache clearing for memory issues                       │
│ • 🔒 Resource isolation for security threats                │
│ • 📧 Team alerts for critical issues                        │
│ • ⏪ Rollback deployments on errors                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Example: Full Test Workflow

### **Scenario: Test if your jewelry-vault app can handle traffic**

1. **Navigate to**: http://localhost:3000 → Click **🛡️ Security Monitor**

2. **Fill in the fields**:
   - Target URL: `https://jewelry-vault-deploy.s3-website-us-east-1.amazonaws.com`
   - Bucket: `jewelry-vault-deploy`

3. **Click**: **🚀 Run Load Test**

4. **Wait**: 60 seconds (the test will show as "Running")

5. **Click**: **Tests** tab to see results

6. **Check results**:
   - ✅ Error rate < 1% = **Good!** Your app is stable
   - ❌ Error rate > 5% = **Problem!** Your app can't handle the load

7. **If there are issues**, click **Alerts** tab to see what went wrong

8. **Click**: **🔧 Auto-Remediate** to automatically fix issues

---

## Troubleshooting

### **"Dashboard is empty" or "Loading..."**

1. Check if backend is running:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy"...}`

2. Check if frontend is running:
   ```bash
   curl http://localhost:3000
   ```
   Should return HTML

3. **Refresh your browser** (Ctrl+R or F5)

4. **Open browser console** (F12) to see any errors

---

### **"Failed to fetch dashboard data"**

- The backend is not running
- Start it with: `cd api_gateway && python main.py`

---

### **"Test failed to start"**

- Check if target URL is correct and accessible
- Make sure bucket name matches your S3 bucket
- Check browser console (F12) for errors

---

## Quick Reference

| Action | Location | What to Enter |
|--------|----------|---------------|
| **Access Dashboard** | http://localhost:3000 → 🛡️ Security Monitor | - |
| **Run Load Test** | Overview tab → Quick Actions | Target URL + Bucket |
| **Security Scan** | Overview tab → Quick Actions | Target URL + Bucket |
| **View Results** | Tests tab | - |
| **See Alerts** | Alerts tab | - |
| **Auto-Fix** | Alerts tab → Click 🔧 | - |
| **Stats** | Remediation tab | - |

---

## API Endpoints (Advanced Users)

If you want to test via API directly:

```bash
# Get system metrics
curl http://localhost:8000/api/v1/advanced-monitoring/metrics/system

# Run load test
curl -X POST http://localhost:8000/api/v1/advanced-monitoring/tests/load \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://jewelry-vault-deploy.s3-website-us-east-1.amazonaws.com",
    "duration_seconds": 60,
    "concurrent_users": 20,
    "requests_per_second": 100
  }'

# Get alerts
curl http://localhost:8000/api/v1/advanced-monitoring/alerts
```

---

## Next Steps

1. ✅ Run a **Load Test** first
2. ✅ Run a **Security Scan** second
3. ✅ Test **High Load** to see if it crashes
4. ✅ Review **Alerts** and use Auto-Remediation
5. ✅ Monitor the **Remediation** tab for fix statistics

**You're all set! Start testing your deployed application now! 🚀**
