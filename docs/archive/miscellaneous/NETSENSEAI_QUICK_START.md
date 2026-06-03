# 🚀 NetSenseAI - Quick Deployment Start

**Repository**: https://github.com/kirankumarhs29/netSenseAI

Fast-track guide to get your Android app building automatically with CI/CD.

---

## ⚡ 3-Step Setup

### Step 1: Add Workflow File (2 minutes)

In the netSenseAI repository, create this file structure:

```
netSenseAI/
└── .github/
    └── workflows/
        └── android-build.yml
```

Copy the contents from `netsenseai-android-build.yml` (in this directory) to that file.

### Step 2: Commit & Push (1 minute)

```bash
cd netSenseAI
git add .github/workflows/android-build.yml
git commit -m "ci: Add GitHub Actions workflow for Android builds"
git push origin main
```

### Step 3: Download APK (5-8 minutes)

1. Go to: https://github.com/kirankumarhs29/netSenseAI/actions
2. Wait for workflow to complete (~5-8 minutes)
3. Click the completed workflow run
4. Scroll to "Artifacts" section
5. Download `netSenseAI-debug-apk`

---

## 📱 Install on Android Device

### Quick Install (USB)

```bash
adb install netSenseAI-debug.apk
```

### Manual Install

1. Transfer APK to your Android device
2. Open APK file on device
3. Allow "Install from unknown sources"
4. Tap "Install"

---

## 🧪 Test the App

1. **Grant permissions**: Bluetooth + Location
2. **Enable services**: Bluetooth ON, Location ON  
3. **Open app on 2 devices**
4. **Tap "Start Discovery"** on both
5. **Connect and message** between devices

---

## 📊 What Happens Automatically

| Event | Build Type | Where to Get APK |
|-------|-----------|------------------|
| Push to main | Debug + Release | GitHub Actions → Artifacts |
| Push to develop | Debug only | GitHub Actions → Artifacts |
| Pull Request | Debug only | GitHub Actions → Artifacts |
| Manual trigger | Debug + Release | GitHub Actions → Artifacts |

**Build Time**: 5-8 minutes  
**Retention**: Debug (30 days), Release (90 days)

---

## 📚 Files Created

In this PromptOps directory:

1. **NETSENSEAI_DEPLOYMENT_GUIDE.md** - Complete deployment documentation
2. **netsenseai-android-build.yml** - GitHub Actions workflow file (copy this!)
3. **NETSENSEAI_QUICK_START.md** - This file

---

## 🎯 Next Actions

### For netSenseAI Repository Owner:

1. **Copy workflow file**:
   ```bash
   mkdir -p .github/workflows
   cp netsenseai-android-build.yml netSenseAI/.github/workflows/android-build.yml
   ```

2. **Commit to netSenseAI repo**:
   ```bash
   cd netSenseAI
   git add .github/workflows/
   git commit -m "ci: Add automated Android build pipeline"
   git push origin main
   ```

3. **Monitor first build**:
   - Visit: https://github.com/kirankumarhs29/netSenseAI/actions
   - Watch the workflow run
   - Download APK when complete

### Optional Enhancements:

- [ ] Add build status badge to README
- [ ] Set up release signing for Play Store
- [ ] Configure Firebase App Distribution
- [ ] Add automated testing
- [ ] Set up GitHub Releases

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check JDK version (should be 17) |
| APK won't install | Device must be Android 8.0+ |
| No BLE discovery | Grant Location + Bluetooth permissions |
| Can't find APK | Check Actions → Workflow → Artifacts section |

---

## 📞 Support

- **Full Guide**: See NETSENSEAI_DEPLOYMENT_GUIDE.md
- **Repository**: https://github.com/kirankumarhs29/netSenseAI
- **Issues**: https://github.com/kirankumarhs29/netSenseAI/issues

---

**Ready to deploy!** Copy the workflow file and commit to start building automatically. 🚀

---

**Created**: 2026-05-16  
**Workflow**: GitHub Actions  
**Build Tool**: Gradle  
**Language**: Kotlin + C++
