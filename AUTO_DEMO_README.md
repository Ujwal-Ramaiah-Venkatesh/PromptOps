# 🎬 Automated Demo Recording

## What This Does

The **auto_demo_recording.py** script automatically:

1. ✅ Opens PromptOps UI in a browser
2. ✅ Logs in automatically
3. ✅ Navigates through all features
4. ✅ Fills forms with deployment info
5. ✅ Runs security scans and load tests
6. ✅ **Records video** of the entire process
7. ✅ Takes screenshots at each step

**Zero manual interaction required!**

---

## 🚀 Quick Start

### Option 1: Run the Batch File (Easiest)
```bash
# Double-click or run:
RECORD_DEMO.bat
```

This will:
- Check if backend/frontend are running
- Start them if needed
- Run the automated demo
- Save video to `demo_recordings/`

### Option 2: Run Python Directly
```bash
python auto_demo_recording.py
```

---

## 📁 Output

After running, you'll find in **`demo_recordings/`**:

### Video File:
```
promptops_demo_20260603_110530.webm
```
- Full screen recording of the demo
- 1920x1080 resolution
- WebM format (convertible to MP4)

### Screenshots:
```
01_login_page.png
02_dashboard.png
03_home_dashboard.png
04_security_monitor.png
05_system_metrics.png
06_deployment_form.png
07_security_scan.png
08_load_test.png
09_alerts.png
10_remediation.png
11_final_overview.png
```

---

## 🎯 Demo Flow

The script automatically performs these steps:

### 1. Login (10 seconds)
- Navigates to http://localhost:3000
- Fills email: admin@promptops.com
- Fills password: admin123
- Clicks login button
- Waits for dashboard

### 2. Dashboard Tour (5 seconds)
- Shows home page
- Scrolls to display content
- Captures overview

### 3. Security Monitor (5 seconds)
- Clicks Security Monitor tab
- Shows system metrics
- Displays CPU, Memory, Disk usage

### 4. Configuration (10 seconds)
- Fills target URL field
- Fills bucket name field
- Shows configured deployment

### 5. Security Scan (15 seconds)
- Clicks "Security Scan" button
- Waits for scan to complete
- Shows results in Tests tab

### 6. Load Test (10 seconds)
- Clicks "Run Load Test" button
- Shows test progress
- Displays results

### 7. Alerts (5 seconds)
- Navigates to Alerts tab
- Shows detected issues
- Displays severity levels

### 8. Remediation (5 seconds)
- Navigates to Remediation tab
- Shows auto-remediation stats
- Displays capabilities

### 9. Final Overview (5 seconds)
- Returns to Overview tab
- Shows complete dashboard
- Captures final state

**Total Duration: ~60-70 seconds**

---

## ⚙️ Configuration

Edit **auto_demo_recording.py** to customize:

```python
# URLs
PROMPTOPS_URL = "http://localhost:3000"

# Login credentials
LOGIN_EMAIL = "admin@promptops.com"
LOGIN_PASSWORD = "admin123"

# Deployment info
DEPLOYMENT_CONFIG = {
    "app_name": "jewelry-vault-demo",
    "repo_url": "https://github.com/ashi100sh/jewelry-vault",
    "branch": "main",
    "region": "us-east-1",
    "bucket_name": "jewelry-vault-demo"
}

# Timing (in seconds)
TYPING_DELAY = 100  # milliseconds between keystrokes
WAIT_SHORT = 2      # short pauses
WAIT_MEDIUM = 5     # medium pauses
WAIT_LONG = 10      # long pauses
```

---

## 🎨 Customization Options

### Speed Up Recording
```python
# Make it faster
TYPING_DELAY = 50
WAIT_SHORT = 1
WAIT_MEDIUM = 2
WAIT_LONG = 5

# Launch browser
slow_mo=100  # Reduce from 500
```

### Higher Quality Video
```python
viewport={'width': 2560, 'height': 1440}  # 2K resolution
record_video_size={'width': 2560, 'height': 1440}
```

### Headless Mode (No Browser Window)
```python
self.browser = await self.playwright.chromium.launch(
    headless=True  # Change to True
)
```

### Different Output Location
```python
OUTPUT_DIR = Path("C:/Users/YourName/Videos/PromptOps")
```

---

## 🔧 Troubleshooting

### Issue: "Backend not running"
**Solution:**
```bash
cd api_gateway
python main.py
```

### Issue: "Frontend not running"
**Solution:**
```bash
cd frontend/dashboard
npm run dev
```

### Issue: "Playwright not found"
**Solution:**
```bash
pip install playwright playwright-stealth
playwright install chromium
```

### Issue: "Login fails"
**Check:**
- Backend is responding: `curl http://localhost:8000/health`
- Frontend is loading: `curl http://localhost:3000`
- Credentials are correct in script

### Issue: "Elements not found"
**The script will:**
- Continue despite missing elements
- Take error screenshots
- Complete what it can

### Issue: "Video file too large"
**Compress it:**
```bash
# Using ffmpeg
ffmpeg -i input.webm -c:v libx264 -crf 23 output.mp4
```

---

## 📹 Converting Video

### Convert WebM to MP4:
```bash
# Install ffmpeg first
ffmpeg -i promptops_demo.webm -c:v libx264 -c:a aac output.mp4
```

### Add Audio Narration:
```bash
# Record audio separately, then:
ffmpeg -i video.webm -i narration.mp3 -c:v copy -c:a aac output.mp4
```

### Trim Video:
```bash
# Start at 5 seconds, duration 60 seconds
ffmpeg -ss 00:00:05 -i input.webm -t 00:01:00 -c copy output.webm
```

---

## 🎬 Post-Production Tips

### 1. Add Title Slide
- Use video editor to add 3-second intro
- Show: "PromptOps - Automated Demo"

### 2. Add Captions/Subtitles
- Use YouTube auto-captions
- Or add SRT file manually

### 3. Speed Up Boring Parts
- Speed up form filling to 1.5x
- Keep scan results at normal speed

### 4. Add Highlights
- Circle important buttons
- Zoom in on key metrics
- Add arrows to guide viewer

### 5. Background Music
- Use royalty-free music
- Keep volume low (20-30%)
- Fade in/out

---

## 🚀 Advanced: CI/CD Integration

Run this script in CI/CD for automated demo videos:

```yaml
# .github/workflows/demo-video.yml
name: Generate Demo Video

on:
  push:
    branches: [main]

jobs:
  record-demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install playwright playwright-stealth
          playwright install chromium

      - name: Start services
        run: |
          python api_gateway/main.py &
          npm run dev --prefix frontend/dashboard &
          sleep 10

      - name: Record demo
        run: python auto_demo_recording.py

      - name: Upload video
        uses: actions/upload-artifact@v2
        with:
          name: demo-video
          path: demo_recordings/
```

---

## 📊 What Gets Recorded

### ✅ Captured:
- All mouse movements
- All typing/input
- Page navigation
- Button clicks
- Form submissions
- Modal dialogs
- Tab switches
- Scroll actions
- Data loading
- Progress indicators

### ❌ Not Captured:
- Audio (add separately)
- Mouse cursor (can be enabled)
- System notifications outside browser
- Other windows/apps

---

## 💡 Pro Tips

1. **Clean Browser Profile**: Script uses fresh profile for consistency

2. **Network Speed**: Ensure good internet for GitHub repo access

3. **Multiple Takes**: Run script multiple times to get best result

4. **Test First**: Do a test run before important recordings

5. **Monitor Progress**: Watch the browser window while recording

6. **Backup**: Keep multiple recordings in case one fails

7. **Naming**: Use descriptive filenames with dates

8. **Storage**: Video files are ~10-50MB each

---

## 📝 Checklist Before Recording

- [ ] Backend running and healthy
- [ ] Frontend running and accessible
- [ ] AWS credentials configured (if deploying)
- [ ] Login credentials correct
- [ ] Enough disk space (~100MB)
- [ ] No other resource-heavy apps running
- [ ] Internet connection stable
- [ ] Screen resolution set to 1920x1080

---

## 🎉 Success!

Your automated demo is ready!

**To start recording:**
```bash
RECORD_DEMO.bat
```

**Or:**
```bash
python auto_demo_recording.py
```

The browser will open, navigate automatically, and save the video!

**Check output in:** `demo_recordings/`

---

## 📧 Support

Issues with the script?
1. Check the error screenshots in `demo_recordings/`
2. Review console output
3. Verify services are running
4. Check browser console (F12) if needed

**Happy Recording! 🎬🚀**
