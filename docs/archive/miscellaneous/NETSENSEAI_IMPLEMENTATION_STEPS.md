# 🎯 NetSenseAI CI/CD Implementation - Step by Step

**For Repository Owner**: kirankumarhs29

This document provides exact commands to implement the CI/CD pipeline for your netSenseAI Android app.

---

## 📦 What You Have

In your **PromptOps** directory, you now have:

1. **netsenseai-android-build.yml** - The GitHub Actions workflow file
2. **NETSENSEAI_DEPLOYMENT_GUIDE.md** - Complete documentation
3. **NETSENSEAI_QUICK_START.md** - Quick reference guide
4. **NETSENSEAI_IMPLEMENTATION_STEPS.md** - This file

---

## 🚀 Implementation Steps

### Prerequisites

- [ ] Access to https://github.com/kirankumarhs29/netSenseAI
- [ ] Git installed locally
- [ ] Repository cloned locally (or will clone now)

---

### Option 1: Local Repository Setup (Recommended)

If you have netSenseAI cloned locally:

```bash
# Navigate to netSenseAI repository
cd path/to/netSenseAI

# Create workflows directory
mkdir -p .github/workflows

# Copy the workflow file from PromptOps
cp path/to/PromptOps/netsenseai-android-build.yml .github/workflows/android-build.yml

# Verify file was copied
ls -la .github/workflows/

# Add to git
git add .github/workflows/android-build.yml

# Commit
git commit -m "ci: Add GitHub Actions workflow for automated Android builds

- Automated debug APK builds on push/PR
- Automated release APK builds on main branch
- Lint checks for code quality
- APK artifacts available for download (30-90 day retention)
- Gradle caching for faster builds
- Manual workflow triggers supported"

# Push to GitHub
git push origin main
```

---

### Option 2: Clone Fresh and Setup

If you don't have netSenseAI locally:

```bash
# Navigate to your projects directory
cd ~/projects  # or wherever you keep repos

# Clone the repository
git clone https://github.com/kirankumarhs29/netSenseAI.git
cd netSenseAI

# Create workflows directory
mkdir -p .github/workflows

# Copy workflow file (adjust path to your PromptOps directory)
cp ~/Documents/PromptOps/netsenseai-android-build.yml .github/workflows/android-build.yml

# Verify
cat .github/workflows/android-build.yml

# Add, commit, and push
git add .github/workflows/android-build.yml
git commit -m "ci: Add GitHub Actions workflow for automated Android builds"
git push origin main
```

---

### Option 3: GitHub Web Interface (No local clone needed)

1. Go to https://github.com/kirankumarhs29/netSenseAI
2. Click "Add file" → "Create new file"
3. Enter filename: `.github/workflows/android-build.yml`
   (GitHub will auto-create the directories)
4. Open `netsenseai-android-build.yml` from PromptOps
5. Copy entire contents
6. Paste into the GitHub editor
7. Scroll down to "Commit new file"
8. Commit message: `ci: Add GitHub Actions workflow for automated Android builds`
9. Click "Commit new file"

---

## ✅ Verification Steps

### Step 1: Check Workflow Appears

1. Go to: https://github.com/kirankumarhs29/netSenseAI/actions
2. You should see "Android CI/CD" in the workflows list
3. A workflow run should start automatically from your push

### Step 2: Monitor First Build

1. Click on the running workflow (yellow dot)
2. Watch the build progress:
   - **Build** job: ~5-8 minutes
   - **Lint** job: ~3-5 minutes (runs in parallel)
   - **Release** job: ~5-8 minutes (only if pushed to main)

### Step 3: Download APK

Once the workflow completes (green checkmark):

1. Click on the completed workflow run
2. Scroll down to **Artifacts** section
3. You'll see:
   - `netSenseAI-debug-apk` - Download this!
   - `netSenseAI-release-apk` - Only on main branch
   - `lint-reports` - If lint checks ran

4. Click to download (it's a ZIP file)
5. Extract the ZIP to get the APK file

---

## 📱 Testing the APK

### Install on Android Device

#### Via USB (ADB method):

```bash
# Connect Android device via USB
# Enable USB debugging on device:
# Settings → About Phone → Tap "Build Number" 7 times
# Settings → Developer Options → USB Debugging → ON

# Check device is connected
adb devices

# Install the APK
adb install path/to/netSenseAI-debug.apk

# Or force reinstall
adb install -r path/to/netSenseAI-debug.apk
```

#### Via Manual Transfer:

1. Extract APK from downloaded ZIP
2. Transfer APK to your Android device (USB, email, cloud)
3. On device: Open Files app
4. Navigate to APK file
5. Tap the APK
6. Allow "Install from unknown sources" if prompted
7. Tap "Install"

### Test the Application

1. **Open the app**
   - Find "NetSense Mesh" or "NetSenseAI" in app drawer
   - Open it

2. **Grant permissions**
   - Allow Bluetooth permission
   - Allow Location permission (required for BLE scanning)

3. **Enable services**
   - Enable Bluetooth if not already on
   - Enable Location services

4. **Test with 2 devices**
   - Install on a second Android device
   - Open app on both devices
   - Tap "Start Discovery" on both
   - Devices should discover each other
   - You'll see RSSI (signal strength) values
   - Tap a discovered peer to connect
   - Send messages between devices

---

## 🎨 Optional: Add Build Badge to README

To show build status in your repository:

1. Edit `README.md` in netSenseAI
2. Add this line at the top:

```markdown
[![Android CI/CD](https://github.com/kirankumarhs29/netSenseAI/actions/workflows/android-build.yml/badge.svg)](https://github.com/kirankumarhs29/netSenseAI/actions/workflows/android-build.yml)
```

3. Commit and push:

```bash
git add README.md
git commit -m "docs: Add build status badge"
git push origin main
```

The badge will show:
- ✅ Green "passing" if builds succeed
- ❌ Red "failing" if builds fail

---

## 🔄 How It Works Going Forward

### Automatic Builds

From now on, every time you:

- **Push to main/master**: 
  - Debug APK builds ✅
  - Release APK builds ✅
  - Lint checks run ✅
  
- **Push to develop**:
  - Debug APK builds ✅
  - Lint checks run ✅
  
- **Create a Pull Request**:
  - Debug APK builds ✅
  - Lint checks run ✅

### Manual Builds

You can trigger builds manually:

1. Go to: https://github.com/kirankumarhs29/netSenseAI/actions
2. Click "Android CI/CD" workflow
3. Click "Run workflow" button (top right)
4. Select branch (main/master)
5. Click "Run workflow"

---

## 📊 Build Artifacts Retention

- **Debug APKs**: Kept for 30 days
- **Release APKs**: Kept for 90 days
- **Lint reports**: Kept for 7 days

After retention period, artifacts are automatically deleted. Download important builds before they expire!

---

## 🐛 Troubleshooting

### Build Fails

1. Click on the failed workflow run
2. Click on the failed job (red X)
3. Read the error messages
4. Common issues:
   - Gradle dependency issues
   - Kotlin version mismatches
   - Android SDK version problems

### Can't Download Artifacts

- Artifacts only available for successful builds
- Must be logged into GitHub
- Artifacts expire after retention period

### APK Won't Install

- Device must be Android 8.0 (API 26) or higher
- Enable "Unknown sources" / "Install from unknown apps"
- Uninstall previous version if signature mismatch

---

## 📚 Next Enhancements

Once basic CI/CD is working, consider:

### 1. Release Signing

For Play Store deployment, set up APK signing:
- Generate keystore
- Add GitHub secrets
- Update build.gradle.kts
- See NETSENSEAI_DEPLOYMENT_GUIDE.md for details

### 2. Firebase App Distribution

For beta testing:
- Set up Firebase project
- Add Firebase credentials
- Update workflow to upload to Firebase
- Testers get automatic notifications

### 3. Google Play Store

For public release:
- Create Play Console account
- Generate service account key
- Update workflow for Play Store upload
- Automatic deployment to internal/beta/prod tracks

### 4. Automated Testing

Add test automation:
- Unit tests
- Integration tests
- UI tests (Espresso)
- Run tests in CI before building APK

---

## 📞 Getting Help

### If Build Fails

1. Check build logs in GitHub Actions
2. Review error messages carefully
3. Check NETSENSEAI_DEPLOYMENT_GUIDE.md troubleshooting section
4. Open issue in repository

### If App Doesn't Work

1. Check Android version (must be 8.0+)
2. Verify Bluetooth permissions granted
3. Verify Location permissions granted
4. Check Bluetooth and Location are enabled
5. Check logs with `adb logcat`

### Resources

- **Full Guide**: NETSENSEAI_DEPLOYMENT_GUIDE.md
- **Quick Reference**: NETSENSEAI_QUICK_START.md
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Android Docs**: https://developer.android.com/studio/build

---

## ✅ Implementation Checklist

Use this to track your progress:

- [ ] Copy workflow file to netSenseAI repository
- [ ] Commit workflow to `.github/workflows/android-build.yml`
- [ ] Push to GitHub main branch
- [ ] Verify workflow appears in Actions tab
- [ ] Monitor first build (wait ~5-8 minutes)
- [ ] Build completes successfully (green checkmark)
- [ ] Download debug APK from artifacts
- [ ] Install APK on Android device
- [ ] Grant Bluetooth + Location permissions
- [ ] Enable Bluetooth and Location services
- [ ] Test discovery with 2 devices
- [ ] Test messaging between devices
- [ ] (Optional) Add build badge to README
- [ ] (Optional) Set up release signing
- [ ] (Optional) Configure advanced deployment

---

## 🎉 Success!

Once you complete the checklist:

✅ Your Android app builds automatically  
✅ APKs are available for download  
✅ Builds run on every code change  
✅ You can deploy to testers or users anytime  

**You now have a production-ready CI/CD pipeline!** 🚀

---

**Created**: 2026-05-16  
**Repository**: https://github.com/kirankumarhs29/netSenseAI  
**Workflow**: GitHub Actions  
**Status**: Ready to implement
