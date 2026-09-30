# PromptOps UI Testing Guide - Video Clip Scenarios
## Test Each Video Clip Scenario in the Live Dashboard

---

## 🎯 Overview
This guide maps each video clip from `VIDEO_PROMPTS_CLIP_BY_CLIP.md` to actual PromptOps UI features you can test and demonstrate.

**Total Testing Time:** ~25-30 minutes  
**Dashboard URL:** `http://localhost:3000` (after starting frontend)  
**Backend API:** `http://localhost:8000` (must be running)

---

## 📋 Pre-Testing Checklist

### 1. Start Backend API
```bash
cd api_gateway
python main.py
```
**Expected:** API running on `http://localhost:8000`

### 2. Start Frontend Dashboard
```bash
cd frontend/dashboard
npm install  # if first time
npm start
```
**Expected:** Dashboard opens at `http://localhost:3000`

### 3. Login Credentials
- **Email:** `pm@promptops.com`
- **Password:** `pm123`
- **Role:** Product Manager

---

## 🎬 CLIP 1 (0-8s) - Cloud Complexity
### Video Requirement:
- "1,000+ Cloud Resources"
- "3 Clouds, One View Needed"

### UI Test Path:
1. **Navigate:** Home Dashboard → **Discovery** tab
2. **Test Feature:** Multi-cloud resource discovery
3. **Visual Elements to Capture:**
   - Cloud provider logos (AWS, Azure, GCP)
   - Resource count metrics
   - Multi-cloud unified view

### Commands to Test:
```
Start AWS discovery scan for this account
```

### Expected UI Output:
- Discovery dashboard showing:
  - Resource inventory across clouds
  - Service distribution chart
  - Region-wise breakdown
  - Total resource count display

### Screenshot Points:
- ✅ Discovery Dashboard header showing cloud logos
- ✅ Resource count cards
- ✅ Multi-cloud resource table

---

## 🎬 CLIP 2 (8-16s) - Operational Challenges
### Video Requirement:
- "80% Time on Incidents"
- "6-8 hours detection time"

### UI Test Path:
1. **Navigate:** Home → **Security Monitoring** tab
2. **Test Feature:** Incident detection and monitoring

### Visual Elements:
- System health metrics
- Alert detection dashboard
- Response time metrics
- Incident timeline

### Commands to Test:
```
Show me active incidents and detection times
```

### Expected UI Output:
- **Security Monitoring Dashboard:**
  - CPU/Memory/Disk usage cards
  - Active alerts count (Critical, High, Total)
  - Auto-refresh status (10s intervals)
  - Alert detection timestamps

### Screenshot Points:
- ✅ System health cards showing resource usage
- ✅ Alert summary (Critical: X, High: Y, Total: Z)
- ✅ Alert list with timestamps

---

## 🎬 CLIP 3 (16-24s) - Cost Impact
### Video Requirement:
- "$5,600 Per Minute Downtime"
- "35-40% Optimization Opportunity"

### UI Test Path:
1. **Navigate:** Home → **Observability** tab
2. **Test Feature:** Cost tracking and downtime impact

### Visual Elements:
- Uptime percentage
- Response time metrics
- Error rate monitoring
- Cost impact indicators

### Expected UI Output:
- **Observability Dashboard:**
  - Health status card with uptime % (99.9%)
  - Response time metrics (p95 latency)
  - Error rate tracking
  - CloudWatch metrics visualization

### Screenshot Points:
- ✅ Uptime metric card (top of dashboard)
- ✅ Response time chart
- ✅ Error rate graph
- ✅ Cost optimization indicators

---

## 🎬 CLIP 4 (24-32s) - Resource Management
### Video Requirement:
- "$2.4M Potential Savings"
- "70% From Configuration Gaps"
- "UNUSED - 89 DAYS" idle resources

### UI Test Path:
1. **Navigate:** Home → **Discovery** tab
2. **Test Feature:** Resource optimization recommendations

### Commands to Test:
```
Show me unused resources and optimization opportunities
```

### Expected UI Output:
- Discovery results showing:
  - Idle resource identification
  - Configuration gap analysis
  - Cost savings recommendations
  - Resource age tracking

### Screenshot Points:
- ✅ Resource optimization summary
- ✅ Idle resource list
- ✅ Cost savings projections
- ✅ Configuration recommendations

---

## 🎬 CLIP 5 (32-40s) - Unexpected Traffic Spike
### Video Requirement:
- "6:00 PM: Normal Traffic"
- "6:30 PM: Spike 10X - Systems Strain"

### UI Test Path:
1. **Navigate:** Security Monitoring → **Tests** tab
2. **Test Feature:** Load testing and traffic simulation

### Test Actions:
1. Enter target URL: `http://your-deployed-app.s3-website-us-east-1.amazonaws.com`
2. Click **"🚀 Run Load Test"**
3. Monitor real-time metrics

### Expected UI Output:
- Load test running status
- Real-time metrics:
  - Request rate spike
  - Response time increase
  - System resource strain
  - Error rate changes

### Screenshot Points:
- ✅ Load test configuration form
- ✅ Test running status
- ✅ Real-time metrics during load
- ✅ System strain indicators

---

## 🎬 CLIP 6 (40-48s) - Multi-Cloud Coordination
### Video Requirement:
- "2.5 Hours Impact = $840K"
- "Better Coordination Needed"
- "Proactive Approach Possible"

### UI Test Path:
1. **Navigate:** Home → **Autonomy** tab
2. **Test Feature:** Proactive policy configuration

### Commands to Test:
```
Configure medium-risk autonomy policy
```

### Expected UI Output:
- **Autonomy Settings Dashboard:**
  - Risk level configuration (Low/Medium/High)
  - Approval thresholds
  - Auto-remediation settings
  - Multi-cloud coordination options

### Screenshot Points:
- ✅ Autonomy policy selector
- ✅ Risk threshold controls
- ✅ Auto-remediation settings
- ✅ Multi-cloud coordination toggle

---

## 🎬 CLIP 7 (48-50s) - Solution Introduction
### Video Requirement:
- "What If Operations Were Proactive?"
- "PromptOps" logo and tagline
- "AI-Powered Cloud Operations"

### UI Test Path:
1. **Navigate:** Home Dashboard (landing page)
2. **Showcase:** Premium home dashboard features

### Visual Elements:
- PromptOps logo and branding
- "Manage Cloud Infrastructure in Plain English"
- DevOps animated icons (Cloud, Security, CI/CD, Deploy, Monitor, Automate)
- Quick action cards
- System overview stats

### Screenshot Points:
- ✅ Welcome card with animated DevOps icons
- ✅ "Plain English" tagline
- ✅ Quick action cards (Deploy, Autonomy, Discovery, Ingestion)
- ✅ System stats (99.9% Uptime, 10x Faster, 24/7 Support)

---

## 🎯 Complete End-to-End Demo Flow (50 seconds)

### Scenario: Deploy → Monitor → Remediate

#### Step 1: Deploy Application (0-10s)
1. Home Dashboard → Click **"Deploy Application"** card
2. Fill deployment form:
   - Repo: `https://github.com/your-username/your-app`
   - Bucket: `my-app-promptops-123456`
   - Region: `us-east-1`
3. Check security review ✅
4. Check PM approval ✅
5. Click **"Approve & Execute"**

**Expected:**
- Deployment progress (8 steps)
- Live logs scrolling
- Success modal with public URL

#### Step 2: Monitor Health (10-20s)
1. Navigate to **Observability** tab
2. Select deployed application
3. View real-time metrics:
   - CPU usage chart
   - Memory usage chart
   - Request rate
   - Error rate
   - Response time (p95)

**Expected:**
- CloudWatch metrics updating
- Health status: Healthy ✓
- Uptime: 99.9%
- Auto-refresh active (30s)

#### Step 3: Run Security Tests (20-30s)
1. Navigate to **Security Monitoring** tab
2. Enter target URL
3. Click **"🔒 Security Scan"**
4. Monitor test results

**Expected:**
- Security scan running
- Vulnerability checks
- SSL certificate validation
- Security headers analysis

#### Step 4: Auto-Remediation (30-40s)
1. Check **Alerts** tab
2. Review detected issues
3. Click **"🔧 Auto-Remediate"** on any alert

**Expected:**
- Remediation triggered
- Auto-fix applied
- Alert status updated to "✅ Auto-remediated"

#### Step 5: Load Testing (40-50s)
1. Return to Security Monitoring
2. Enter target URL
3. Click **"🚀 Run Load Test"**
4. Watch system handle traffic spike

**Expected:**
- Load test simulation
- 10X traffic increase
- System metrics spike
- Performance under load

---

## 📊 Key Metrics to Capture for Each Clip

### Clip 1 - Cloud Complexity
- ✅ Multi-cloud resource count
- ✅ AWS + Azure + GCP icons visible
- ✅ Unified inventory view

### Clip 2 - Operational Challenges
- ✅ Alert detection time < 8 hours
- ✅ 80% time on incidents indicator
- ✅ Real-time monitoring active

### Clip 3 - Cost Impact
- ✅ Downtime cost calculation
- ✅ 35-40% optimization opportunity
- ✅ Response time metrics

### Clip 4 - Resource Management
- ✅ Idle resource list (89+ days)
- ✅ $2.4M savings projection
- ✅ Configuration gap analysis

### Clip 5 - Traffic Spike
- ✅ Normal traffic baseline (6:00 PM)
- ✅ 10X spike simulation (6:30 PM)
- ✅ System strain indicators

### Clip 6 - Multi-Cloud Coordination
- ✅ 2.5 hour incident recovery time
- ✅ Proactive policy configuration
- ✅ Auto-remediation success rate

### Clip 7 - Solution Introduction
- ✅ PromptOps branding
- ✅ "Plain English" commands
- ✅ AI-powered automation demo

---

## 🎥 Screen Recording Tips

### Browser Setup
1. **Full Screen:** F11 (Windows) or Cmd+Ctrl+F (Mac)
2. **Zoom Level:** 100% (Ctrl+0 / Cmd+0)
3. **Resolution:** 1920x1080 (1080p HD)
4. **Browser:** Chrome or Edge (best performance)

### Recording Software
- **OBS Studio** (Free): https://obsproject.com/
- **ScreenFlow** (Mac): https://www.telestream.net/screenflow/
- **Camtasia** (Paid): https://www.techsmith.com/video-editor.html

### Recording Settings
- **Resolution:** 1920x1080 (Full HD)
- **FPS:** 30fps (standard) or 60fps (smooth)
- **Bitrate:** 5000-8000 kbps
- **Format:** MP4 (H.264 codec)

### Audio Setup
- **Voiceover:** Record separately for clarity
- **Background Music:** Low volume (10-15%)
- **Sound Effects:** Subtle transitions

---

## 🔧 Troubleshooting

### Issue: Backend API Not Responding
**Solution:**
```bash
cd api_gateway
# Check if port 8000 is available
netstat -ano | findstr :8000
# Kill existing process if needed
taskkill /PID <process_id> /F
# Restart API
python main.py
```

### Issue: Frontend Not Loading
**Solution:**
```bash
cd frontend/dashboard
# Clear cache
npm cache clean --force
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
# Start fresh
npm start
```

### Issue: No Deployed Applications in Observability
**Solution:**
1. Deploy an application first via Home → Deploy
2. Check localStorage: Open DevTools → Application → Local Storage → Look for `promptops_recent_deployments`
3. Manually add test data if needed

### Issue: Security Monitoring Tests Failing
**Solution:**
1. Ensure backend monitoring routes are active
2. Check `/api/v1/advanced-monitoring/dashboard/summary` endpoint
3. Verify target URL is reachable

---

## ✅ Testing Checklist

### Pre-Recording
- [ ] Backend API running (http://localhost:8000)
- [ ] Frontend dashboard loaded (http://localhost:3000)
- [ ] Logged in as PM user
- [ ] Browser in full-screen mode (1920x1080)
- [ ] Recording software configured (30fps, MP4)
- [ ] Audio levels tested

### During Recording (Per Clip)
- [ ] Navigate to correct dashboard tab
- [ ] Execute relevant command
- [ ] Wait for UI response (2-3 seconds)
- [ ] Highlight key metrics on screen
- [ ] Capture smooth transitions

### Post-Recording
- [ ] Review each clip for clarity
- [ ] Check text overlays are readable
- [ ] Verify metrics match clip requirements
- [ ] Add voiceover or captions
- [ ] Export at 1080p, 30fps

---

## 🎬 Final Video Assembly

### Editing Workflow
1. **Import all clips** (7 clips total)
2. **Trim to exact durations:**
   - Clip 1: 8s
   - Clip 2: 8s
   - Clip 3: 8s
   - Clip 4: 8s
   - Clip 5: 8s
   - Clip 6: 8s
   - Clip 7: 2-3s (or extend to 8s)
3. **Add transitions:** 0.3s cross-dissolve between clips
4. **Add text overlays** (per clip specifications):
   - Font: Bold, 72-100pt
   - Color: White with black shadow
   - Position: Lower third or center
   - Duration: 3+ seconds each
5. **Add background music:** Professional, uplifting tech music
6. **Normalize audio levels**
7. **Export:** 1080p, 30fps, MP4

### Final Output
- **Resolution:** 1920x1080 (Full HD)
- **Duration:** 50 seconds (total)
- **Format:** MP4 (H.264)
- **Bitrate:** 8000 kbps
- **Audio:** AAC, 192 kbps

---

## 📞 Support

### Issues or Questions?
- **GitHub:** https://github.com/promptops/promptops/issues
- **Documentation:** Check `COMPLETE_DEMO_GUIDE.md`
- **Demo Scripts:** See `DEMO_QUICK_REFERENCE.txt`

---

**Happy Testing! 🚀**
