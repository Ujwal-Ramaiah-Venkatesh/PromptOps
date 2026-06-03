# 📱 NetSenseAI Android CI/CD Deployment Guide

Complete guide for deploying the NetSenseAI Android application with automated CI/CD pipeline.

---

## 🚀 Overview

This guide sets up GitHub Actions to automatically build your Android APK on every code change.

**Repository**: https://github.com/kirankumarhs29/netSenseAI

### What Gets Automated
- ✅ Debug APK builds on every push/PR
- ✅ Release APK builds on main/master branch
- ✅ Code quality lint checks
- ✅ APK artifacts available for download
- ✅ Build caching for speed
- ✅ Manual workflow triggers

---

## 📋 Tech Stack

- **Language**: Kotlin 75%, C++ 24%
- **Framework**: Kotlin Multiplatform (KMP)
- **UI**: Jetpack Compose
- **Android SDK**: Min 26, Target 34
- **Build Tool**: Gradle 8.3.0
- **Java**: JDK 17

---

## 🔧 Step-by-Step Setup

### Step 1: Add CI/CD Workflow File

Create `.github/workflows/android-build.yml` in the repository with this content:

```yaml
name: Android CI/CD

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  workflow_dispatch:

jobs:
  build:
    name: Build Android APK
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'gradle'
      
      - name: Grant execute permission for gradlew
        run: chmod +x gradlew
      
      - name: Build with Gradle
        run: ./gradlew :androidApp:assembleDebug --stacktrace
      
      - name: Upload Debug APK
        uses: actions/upload-artifact@v4
        with:
          name: netSenseAI-debug-apk
          path: androidApp/build/outputs/apk/debug/*.apk
          retention-days: 30

  lint:
    name: Run Lint Checks
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'gradle'
      
      - name: Grant execute permission for gradlew
        run: chmod +x gradlew
      
      - name: Run Lint
        run: ./gradlew :androidApp:lint --stacktrace

  release:
    name: Build Release APK
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    needs: [build, lint]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'gradle'
      
      - name: Grant execute permission for gradlew
        run: chmod +x gradlew
      
      - name: Build Release APK
        run: ./gradlew :androidApp:assembleRelease --stacktrace
      
      - name: Upload Release APK
        uses: actions/upload-artifact@v4
        with:
          name: netSenseAI-release-apk
          path: androidApp/build/outputs/apk/release/*.apk
          retention-days: 90
```

### Step 2: Commit and Push

```bash
cd netSenseAI
mkdir -p .github/workflows
# Copy the workflow file above to .github/workflows/android-build.yml

git add .github/workflows/android-build.yml
git commit -m "ci: Add GitHub Actions workflow for automated Android builds"
git push origin main
```

### Step 3: Verify Workflow

1. Go to https://github.com/kirankumarhs29/netSenseAI/actions
2. You should see "Android CI/CD" workflow
3. It will auto-trigger on the push in Step 2

---

## 📦 How It Works

### Build Triggers

| Event | Debug Build | Release Build | Lint |
|-------|-------------|---------------|------|
| Push to main/master | ✅ | ✅ | ✅ |
| Push to develop | ✅ | ❌ | ✅ |
| Pull Request | ✅ | ❌ | ✅ |
| Manual Trigger | ✅ | ✅ | ✅ |

### Build Times

- **Debug Build**: ~5-8 minutes
- **Release Build**: ~5-8 minutes
- **Lint Check**: ~3-5 minutes

Builds run in parallel when possible.

---

## 📥 Downloading APKs

### From GitHub Actions Artifacts

1. Navigate to: https://github.com/kirankumarhs29/netSenseAI/actions
2. Click on a completed workflow run (green checkmark)
3. Scroll to **Artifacts** section at the bottom
4. Download:
   - `netSenseAI-debug-apk` - For testing (30-day retention)
   - `netSenseAI-release-apk` - For production (90-day retention)

### APK Locations in Build

- Debug: `androidApp/build/outputs/apk/debug/androidApp-debug.apk`
- Release: `androidApp/build/outputs/apk/release/androidApp-release.apk`

---

## 📱 Installing on Android Device

### Method 1: USB Install (ADB)

```bash
# Enable USB debugging on your device:
# Settings → About Phone → Tap "Build Number" 7 times
# Settings → Developer Options → Enable "USB Debugging"

# Connect device and install
adb devices
adb install netSenseAI-debug.apk

# Force reinstall if already installed
adb install -r netSenseAI-debug.apk
```

### Method 2: Direct Install

1. Download APK from GitHub Actions
2. Transfer to your Android device (USB, cloud, email)
3. Open the APK file on your device
4. Allow "Install from unknown sources" when prompted
5. Tap "Install"

### Method 3: Emulator Install

```bash
# Start Android emulator
# Then install
adb install netSenseAI-debug.apk
```

---

## 🧪 Testing the App

After installation:

1. **Grant Permissions**
   - Settings → Apps → NetSenseAI
   - Enable Bluetooth permission
   - Enable Location permission (required for BLE)

2. **Enable Services**
   - Turn on Bluetooth
   - Enable Location services

3. **Test Discovery**
   - Open app on two devices
   - Tap "Start Discovery" on both
   - Wait for peer discovery (should see RSSI signal strength)

4. **Test Messaging**
   - Tap on a discovered peer to connect
   - Send a test message
   - Verify message appears on other device

---

## 🔐 Production Release Signing (Optional)

For production releases to Play Store, you need a signed APK.

### Generate Keystore

```bash
keytool -genkey -v -keystore netSenseAI-release.keystore \
  -alias netSenseAI -keyalg RSA -keysize 2048 -validity 10000

# Follow prompts to set passwords
```

### Add GitHub Secrets

1. Go to: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these secrets:
   - `KEYSTORE_PASSWORD` - Your keystore password
   - `KEY_PASSWORD` - Your key password
   - `KEYSTORE_FILE` - Base64 encoded keystore:

```bash
# Encode keystore to base64
base64 netSenseAI-release.keystore > keystore.base64
# Copy contents of keystore.base64 and paste as secret
```

### Update build.gradle.kts

Add signing config to `androidApp/build.gradle.kts`:

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("../release.keystore")
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = "netSenseAI"
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }
    
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

---

## 📊 Monitoring & Status

### Add Build Badge to README

Add this to your README.md:

```markdown
[![Android CI/CD](https://github.com/kirankumarhs29/netSenseAI/actions/workflows/android-build.yml/badge.svg)](https://github.com/kirankumarhs29/netSenseAI/actions/workflows/android-build.yml)
```

Result: ![Android CI/CD](https://github.com/kirankumarhs29/netSenseAI/actions/workflows/android-build.yml/badge.svg)

### Email Notifications

GitHub automatically sends emails for:
- Failed builds
- First successful build after failures

Configure: Settings → Notifications → Actions

---

## 🐛 Troubleshooting

### Build Fails: "Permission Denied"

**Problem**: gradlew doesn't have execute permissions

**Solution**: Workflow includes this step automatically:
```yaml
- name: Grant execute permission for gradlew
  run: chmod +x gradlew
```

### Build Fails: SDK Version Issues

**Problem**: Incompatible SDK versions

**Solution**: 
- Ensure JDK 17 is used (handled by workflow)
- Check `compileSdk = 34` in build.gradle.kts
- Verify `minSdk = 26`

### APK Not Found in Artifacts

**Problem**: Build succeeded but no APK

**Solution**: Check the artifact path matches:
```yaml
path: androidApp/build/outputs/apk/debug/*.apk
```

### App Won't Install on Device

**Solutions**:
1. Device must be Android 8.0 (API 26) or higher
2. Enable "Install Unknown Apps" for your file manager
3. Uninstall previous version first if signature mismatch
4. Check device has Bluetooth LE support

### Gradle Build Cache Issues

**Solution**: Clear cache in workflow:
```yaml
- name: Clear Gradle cache
  run: rm -rf ~/.gradle/caches
```

Or manually: Actions → Caches → Delete gradle cache

---

## 🚀 Advanced Deployment Options

### Firebase App Distribution

For beta testing with Firebase:

1. Create Firebase project
2. Add `FIREBASE_APP_ID` and `FIREBASE_TOKEN` secrets
3. Add to workflow:

```yaml
- name: Upload to Firebase
  uses: wzieba/Firebase-Distribution-Github-Action@v1
  with:
    appId: ${{ secrets.FIREBASE_APP_ID }}
    token: ${{ secrets.FIREBASE_TOKEN }}
    groups: testers
    file: androidApp/build/outputs/apk/release/*.apk
```

### Google Play Store

For automatic Play Store uploads:

1. Create service account in Play Console
2. Add `PLAY_STORE_JSON_KEY` secret
3. Add to workflow:

```yaml
- name: Upload to Play Store
  uses: r0adkll/upload-google-play@v1
  with:
    serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_JSON_KEY }}
    packageName: com.netsense.meshapp
    releaseFiles: androidApp/build/outputs/apk/release/*.apk
    track: internal
```

### GitHub Releases

Auto-create releases with APK attachments:

```yaml
- name: Create Release
  uses: softprops/action-gh-release@v1
  with:
    files: androidApp/build/outputs/apk/release/*.apk
    tag_name: v1.0.0
    name: NetSenseAI v1.0.0
```

---

## 📝 Version Management

Update versions in `androidApp/build.gradle.kts`:

```kotlin
defaultConfig {
    versionCode = 1      // Increment for each release
    versionName = "1.0"  // Semantic versioning
}
```

Version strategy:
- **versionCode**: Integer, increment by 1 for each build
- **versionName**: String, use semantic versioning (e.g., "1.2.3")

---

## ✅ Deployment Checklist

- [ ] Create `.github/workflows/android-build.yml`
- [ ] Commit and push workflow file
- [ ] Verify workflow appears in Actions tab
- [ ] Wait for first build to complete
- [ ] Download debug APK from artifacts
- [ ] Install APK on test device
- [ ] Grant Bluetooth and Location permissions
- [ ] Test peer discovery with 2 devices
- [ ] Test messaging between devices
- [ ] Add build status badge to README
- [ ] (Optional) Set up release signing
- [ ] (Optional) Configure Firebase/Play Store deployment

---

## 📞 Support & Resources

### Repository
- **GitHub**: https://github.com/kirankumarhs29/netSenseAI
- **Issues**: https://github.com/kirankumarhs29/netSenseAI/issues

### Documentation
- [GitHub Actions](https://docs.github.com/en/actions)
- [Android Build Guide](https://developer.android.com/studio/build)
- [Kotlin Multiplatform](https://kotlinlang.org/docs/multiplatform.html)
- [Jetpack Compose](https://developer.android.com/jetpack/compose)

---

## 🎯 Next Steps

1. **For Development**: 
   - Push changes to develop branch
   - PR builds will auto-trigger
   - Download and test debug APKs

2. **For Release**:
   - Merge to main branch
   - Release APK builds automatically
   - Download from artifacts or set up Play Store deployment

3. **For Distribution**:
   - Set up Firebase App Distribution for beta testers
   - Configure Google Play Store for public release
   - Use GitHub Releases for open-source distribution

---

**Created**: 2026-05-16  
**Workflow Version**: 1.0  
**App Version**: 1.0 (versionCode 1)

**Ready to deploy! 🚀**
