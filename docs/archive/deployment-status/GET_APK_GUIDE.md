# Get netSenseAI APK - Complete Guide

**Goal:** Build the APK file so you can deploy it to AWS  
**Current Issue:** Java 26 incompatible with project  

---

## ✅ Option 1: GitHub Actions (Recommended - Cloud Build)

Use GitHub's free cloud builders with Java 17.

### Step 1: Fork the Repository (Optional)

If you have access to the original repo, skip this. Otherwise:
1. Go to: https://github.com/kirankumarhs29/netSenseAI
2. Click "Fork" (top right)

### Step 2: Add GitHub Actions Workflow

Create file: `.github/workflows/build.yml`

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
    
    - name: Grant execute permission for gradlew
      run: chmod +x gradlew
    
    - name: Build Debug APK
      run: ./gradlew :androidApp:assembleDebug
    
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: app-debug
        path: androidApp/build/outputs/apk/debug/*.apk
```

### Step 3: Trigger Build

1. Push the workflow file to GitHub
2. Go to "Actions" tab
3. Click "Run workflow"
4. Wait 5-10 minutes
5. Download APK from artifacts

**Pros:** ✅ Free, ✅ Cloud-based, ✅ No local setup  
**Cons:** Requires GitHub access

---

## ✅ Option 2: Docker (If You Install Docker Desktop)

### Step 1: Install Docker Desktop

1. Download: https://www.docker.com/products/docker-desktop
2. Install (requires restart)
3. Start Docker Desktop

### Step 2: Build with Docker

Run this script I created:

```bash
cd C:\Users\pqm847\Documents\PromptOps\mobile-deployment
build_with_docker.bat
```

Or manually:

```bash
# Clone repo
git clone --depth 1 https://github.com/kirankumarhs29/netSenseAI C:\Temp\netSenseAI

# Build with Docker (Java 17)
docker run --rm ^
    -v "C:\Temp\netSenseAI:/app" ^
    -w /app ^
    eclipse-temurin:17-jdk ^
    bash -c "chmod +x gradlew && ./gradlew :androidApp:assembleDebug"

# APK will be at:
# C:\Temp\netSenseAI\androidApp\build\outputs\apk\debug\androidApp-debug.apk
```

**Pros:** ✅ Isolated, ✅ Clean, ✅ Repeatable  
**Cons:** Requires Docker Desktop (~2 GB download)

---

## ✅ Option 3: Online Build Services

### Codemagic (Free Tier)

1. Go to: https://codemagic.io/
2. Sign up with GitHub
3. Add netSenseAI repository
4. Configure: Android, Gradle
5. Build
6. Download APK

**Pros:** ✅ Free tier, ✅ No installation  
**Cons:** Requires account setup

### AppCenter (Microsoft)

1. Go to: https://appcenter.ms/
2. Create free account
3. Add Android app
4. Connect GitHub
5. Build
6. Download

**Pros:** ✅ Professional, ✅ Free for open source  
**Cons:** Account required

---

## ✅ Option 4: Ask Repository Owner

If kirankumarhs29 has access:

**Email Template:**

```
Subject: Request: netSenseAI APK Build

Hi,

Could you help build the netSenseAI APK? I need it for deployment testing.

Requirements:
- Build: Debug APK
- Command: ./gradlew :androidApp:assembleDebug
- Location: androidApp/build/outputs/apk/debug/

The build requires Java 17 (my system has Java 26 which is incompatible).

Could you:
1. Build the APK with Java 17
2. Share the APK file (or upload to GitHub Releases)

Thanks!
```

**Pros:** ✅ Simple, ✅ Fast  
**Cons:** Depends on availability

---

## ✅ Option 5: Use Another Machine

If you have access to another machine with Java 17:

### On Machine with Java 17:

```bash
# Clone
git clone https://github.com/kirankumarhs29/netSenseAI
cd netSenseAI

# Build
gradlew.bat :androidApp:assembleDebug

# Find APK
# Location: androidApp\build\outputs\apk\debug\androidApp-debug.apk
```

### Transfer APK:

- USB drive
- Email (if < 25 MB)
- Cloud storage (Google Drive, Dropbox)
- Network share

**Pros:** ✅ Works if Java 17 available  
**Cons:** Needs access to another machine

---

## ✅ Option 6: Install Java 17 Manually

If you want to fix the Java issue:

### Step 1: Download Java 17

1. Go to: https://adoptium.net/teapot/
2. Select: **Java 17 (LTS)**
3. Platform: **Windows x64**
4. Package Type: **JDK**
5. Download MSI installer (~180 MB)

### Step 2: Install

1. Run the `.msi` file
2. ✅ Check: "Set JAVA_HOME variable"
3. ✅ Check: "Add to PATH"
4. ✅ Check: "JavaSoft (Oracle) registry keys"
5. Click "Install"
6. Restart computer (important!)

### Step 3: Verify

Open **NEW** terminal:

```bash
java -version
# Should show: openjdk version "17.x.x"
```

### Step 4: Build

```bash
cd C:\Temp
git clone https://github.com/kirankumarhs29/netSenseAI
cd netSenseAI
gradlew.bat :androidApp:assembleDebug

# APK at: androidApp\build\outputs\apk\debug\androidApp-debug.apk
```

**Pros:** ✅ Permanent fix, ✅ Full control  
**Cons:** Requires restart, system changes

---

## ✅ Option 7: Cloud Development Environment

### Gitpod (Free Tier)

1. Go to: https://gitpod.io/
2. Sign up with GitHub
3. Open: https://gitpod.io/#https://github.com/kirankumarhs29/netSenseAI
4. Wait for environment to load
5. Run in terminal:
   ```bash
   ./gradlew :androidApp:assembleDebug
   ```
6. Download APK from workspace

**Pros:** ✅ Cloud-based, ✅ No installation, ✅ Java 17 included  
**Cons:** 50 hours/month free tier

---

## 🎯 Recommended Order

**Fastest (if you have access):**
1. ✅ **GitHub Actions** (5 min setup, free, cloud)
2. ✅ **Ask repository owner** (0 setup, depends on availability)
3. ✅ **Gitpod** (instant cloud environment)

**Most Reliable:**
1. ✅ **Docker** (one-time setup, works always)
2. ✅ **Install Java 17** (permanent fix)

**External Services:**
1. ✅ **Codemagic/AppCenter** (professional CI/CD)

---

## 💡 My Recommendation

**Try these in order:**

1. **GitHub Actions (5 minutes)**
   - If you have GitHub access
   - Add workflow file
   - Get APK from artifacts

2. **Gitpod (instant)**
   - Zero installation
   - Cloud IDE with Java 17
   - Build and download

3. **Docker (30 minutes)**
   - Install Docker Desktop
   - Run my script
   - Gets APK reliably

---

## 🚀 After You Get the APK

Once you have the APK file:

```bash
cd C:\Users\pqm847\Documents\PromptOps

python mobile-deployment\deploy_prebuilt_apk.py ^
  --apk-path "C:\path\to\netSenseAI-debug.apk" ^
  --app-name "netSenseAI" ^
  --version "1.0.0" ^
  --aws-bucket netsense-ai-2026
```

**Deployment takes 2 minutes!** ✅

---

## ❓ Need Help Deciding?

**Quick questions:**

1. **Do you have GitHub access to the repo?**
   - YES → Use GitHub Actions
   - NO → Continue

2. **Can you install Docker Desktop (2 GB)?**
   - YES → Use Docker method
   - NO → Continue

3. **Can you ask the repository owner?**
   - YES → Ask for APK
   - NO → Continue

4. **Can you install Java 17 permanently?**
   - YES → Install Java 17 manually
   - NO → Use Gitpod (cloud)

---

**Which option would you like to try first?**
