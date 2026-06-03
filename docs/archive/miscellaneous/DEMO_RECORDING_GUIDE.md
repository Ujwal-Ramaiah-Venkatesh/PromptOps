# 🎬 PromptOps Demo Recording Guide

## ✅ Current Status
- **Frontend**: Running on http://localhost:5173 ✅
- **Backend**: Needs manual start

---

## 🚀 Quick Start Demo Recording

### Step 1: Start Backend (Manual)

Open a **new terminal** and run:

```bash
cd C:\Users\pqm847\Documents\PromptOps
cd api_gateway
python start_with_mock_db.py
```

**Wait for:**
```
============================================================
  PromptOps API Gateway with Authentication
  Database: In-Memory Mock
============================================================

  Test Users:
    Admin: admin@promptops.com / admin123
    PM:    pm@promptops.com / pm123

  Starting server...
  API: http://localhost:8000
  Docs: http://localhost:8000/docs
```

### Step 2: Verify Both Servers Running

- Frontend: http://localhost:5173 ✅ (Already running)
- Backend: http://localhost:8000/docs (Check this opens)

---

## 🎥 Screen Recording Setup

### Recommended Tool: **OBS Studio** (Free)

1. **Download**: https://obsproject.com/download
2. **Install** OBS Studio
3. **Setup Scene:**
   - Source → Display Capture (full screen)
   - OR Source → Window Capture (browser only)
   - Resolution: 1920x1080
   - FPS: 30

### Alternative: **Windows Game Bar** (Built-in)

- Press `Win + G` to open
- Click Record button
- Records active window

---

## 🎬 Demo Script (Record This Flow)

### PART 1: Login (15 seconds)

1. **Open** http://localhost:5173
2. **Show** clean login page
3. **Type** credentials:
   - Email: `admin@promptops.com`
   - Password: `admin123`
4. **Click** "Sign In"
5. **Show** successful login → dashboard loads

---

### PART 2: Natural Language Command (30 seconds)

1. **Click** "Command Interface" tab
2. **Type slowly** (so it's visible on video):
   ```
   Deploy body-worn camera evidence storage infrastructure with encryption and 99.9% uptime
   ```
3. **Click** "Parse Command" or Submit
4. **Show** AI parsing result:
   - Intent detected
   - Resources identified (S3, RDS, Lambda, KMS)
   - Risk level assessment

---

### PART 3: Autonomy Tiers Demo (25 seconds)

1. **Navigate** to "Autonomy Settings" tab
2. **Show** 4-tier system:
   - LOW (green)
   - MEDIUM (yellow)
   - HIGH (orange)
   - CRITICAL (red)
3. **Highlight** current risk level
4. **Show** approval workflow
5. **Click** approval button

---

### PART 4: Infrastructure Ingestion (20 seconds)

1. **Click** "Infrastructure Ingestion" tab
2. **Show** drift detection feature
3. **Display** "5 resources changed outside Terraform"
4. **Show** auto-generated Terraform code
5. **Highlight** diff visualization

---

### PART 5: Discovery Dashboard (25 seconds)

1. **Click** "Discovery Dashboard" tab
2. **Show** AWS resource scanning
3. **Display** discovered resources table:
   - EC2 instances
   - S3 buckets
   - RDS databases
4. **Show** inferred tags
5. **Show** dependency graph visualization

---

### PART 6: Security & Audit (15 seconds)

1. **Click** "Audit Log" tab
2. **Show** activity log scrolling
3. **Highlight**:
   - User actions
   - Timestamps
   - Risk levels
4. **Show** RBAC permissions matrix

---

### PART 7: Statistics Dashboard (15 seconds)

1. **Show** execution statistics:
   - Total commands processed
   - Auto-executed vs Manual approval
   - Success rate
   - Average execution time
2. **Show** charts/graphs if available

---

## 📝 Recording Tips

### Do's ✅
- **Move mouse slowly** - easier to follow
- **Pause briefly** on each screen - let viewers absorb
- **Type slowly** - makes it readable
- **Highlight** key features with mouse movement
- **Keep browser fullscreen** - no distractions

### Don'ts ❌
- Don't rush through screens
- Don't show errors or failed attempts
- Don't show other tabs/apps
- Don't include personal information
- Don't show URL bar if it has sensitive paths

---

## 🎞️ Post-Recording

### Export Settings (OBS):
- **Format**: MP4
- **Resolution**: 1920x1080
- **FPS**: 30
- **Quality**: High
- **Length**: Aim for 2-3 minutes of usable footage

### File Location:
Save as: `PromptOps_Demo_Recording.mp4`

---

## 🔧 Troubleshooting

### Backend Won't Start?

```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# If occupied, kill the process or use different port
```

### Frontend Shows Blank Page?

1. Check console (F12) for errors
2. Clear browser cache
3. Hard refresh (Ctrl + Shift + R)

### Can't Login?

**Test Users:**
- Admin: `admin@promptops.com` / `admin123`
- PM: `pm@promptops.com` / `pm123`

---

## ✅ Demo Recording Checklist

Before starting recording:

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Browser in fullscreen (F11)
- [ ] OBS/recording software ready
- [ ] Close unnecessary programs
- [ ] Disable notifications
- [ ] Clean browser (no bookmarks bar, close other tabs)
- [ ] Test login works
- [ ] Rehearse the flow once

---

## 🎯 Next Steps After Recording

Once you have the screen recording:

1. **Send me the video file** or upload to Google Drive
2. I'll create:
   - Opening crisis scene (AI generated)
   - Closing future vision scene (AI generated)
   - Text overlays and animations
   - Voiceover script and audio
   - Final edited 3-minute video

---

## 💡 Pro Tips

1. **Record in 4K if possible** - scales down better
2. **Record multiple takes** - pick the best one
3. **Record each section separately** - easier to edit
4. **Leave 2-3 seconds** before and after each action
5. **Speak your actions** (optional) - helps with timing

---

**Ready to record? Open http://localhost:5173 and follow the script above!** 🎬

When you have the recording, we'll combine it with AI-generated scenes for the final hackathon video.
