# netSenseAI Deployment Issue & Solution

**Date:** May 11, 2026  
**Status:** Build Failed - Java Version Incompatibility  
**Root Cause:** Java 26 incompatible with Kotlin 1.9.10

---

## 🔍 Issue Diagnosis

### What Happened

Both Android repositories failed to build:

1. **AdaptiveRTC PTT**
   - ❌ Missing `gradlew` (Gradle wrapper)
   - Cannot build without wrapper files

2. **netSenseAI** ✅ Has gradlew
   - ❌ Build failed with error: `java.lang.IllegalArgumentException: 26`
   - **Root cause:** Kotlin 1.9.10 doesn't support Java 26

### Technical Details

**Your System:**
- Java version: 26 (2026-03-17)
- Python: 3.14
- Platform: Windows 11

**Project Requirements:**
- netSenseAI uses Kotlin 1.9.10
- Kotlin 1.9.10 max supported Java: 21
- Your Java 26 is too new for the Kotlin compiler

---

## ✅ Solutions (Choose One)

### Solution 1: Install Java 17 LTS (Recommended) ⭐

This is the best long-term solution for Android development.

**Step 1: Download Java 17**
```
https://adoptium.net/teapot/
```
- Select: Java 17 (LTS)
- Platform: Windows x64
- Package Type: JDK

**Step 2: Install Java 17**
- Run the installer
- Important: Check "Set JAVA_HOME variable"
- Important: Check "Add to PATH"

**Step 3: Verify Installation**
```bash
java -version
# Should show: openjdk version "17.x.x"
```

**Step 4: Deploy netSenseAI**
```bash
cd C:\Users\pqm847\Documents\PromptOps

python mobile-deployment\deploy_android_app.py ^
  --repo-url https://github.com/kirankumarhs29/netSenseAI ^
  --app-name "netSenseAI" ^
  --option A ^
  --aws-bucket netsense-ai-2026 ^
  --aws-region us-east-1
```

---

### Solution 2: Set JAVA_HOME to Java 17 (If Already Installed)

If you already have Java 17 installed somewhere:

**Find Java 17:**
```bash
# Windows
where java /R C:\ 2>nul | findstr "17"
```

**Set JAVA_HOME temporarily:**
```bash
# PowerShell
$env:JAVA_HOME="C:\path\to\java17"
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"

# CMD
set JAVA_HOME=C:\path\to\java17
set PATH=%JAVA_HOME%\bin;%PATH%
```

**Verify:**
```bash
java -version
```

**Deploy:**
```bash
python mobile-deployment\deploy_android_app.py ^
  --repo-url https://github.com/kirankumarhs29/netSenseAI ^
  --app-name "netSenseAI" ^
  --option A ^
  --aws-bucket netsense-ai-2026
```

---

### Solution 3: Build APK Locally with Correct Java

If you can build the APK on another machine with Java 17:

**On machine with Java 17:**
```bash
git clone https://github.com/kirankumarhs29/netSenseAI
cd netSenseAI
gradlew.bat :androidApp:assembleDebug
```

**Copy APK to this machine:**
```
netSenseAI\androidApp\build\outputs\apk\debug\androidApp-debug.apk
```

**Upload to AWS:**
```bash
cd C:\Users\pqm847\Documents\PromptOps

python mobile-deployment\deploy_android_app.py ^
  --apk-path "C:\path\to\androidApp-debug.apk" ^
  --app-name "netSenseAI" ^
  --version "1.0.0" ^
  --option A ^
  --aws-bucket netsense-ai-2026
```

This bypasses the build step completely!

---

### Solution 4: Use Docker with Correct Java Version

Create a Docker container with Java 17 for builds:

**Create Dockerfile:**
```dockerfile
FROM eclipse-temurin:17-jdk

WORKDIR /app
RUN apt-get update && apt-get install -y git

# Clone and build
RUN git clone https://github.com/kirankumarhs29/netSenseAI .
RUN ./gradlew :androidApp:assembleDebug

# APK will be in: androidApp/build/outputs/apk/debug/
```

**Build and extract APK:**
```bash
docker build -t netsense-builder .
docker create --name netsense-container netsense-builder
docker cp netsense-container:/app/androidApp/build/outputs/apk/debug/androidApp-debug.apk .
docker rm netsense-container
```

**Upload APK:**
```bash
python mobile-deployment\deploy_android_app.py ^
  --apk-path androidApp-debug.apk ^
  --app-name "netSenseAI" ^
  --version "1.0.0" ^
  --option A ^
  --aws-bucket netsense-ai-2026
```

---

### Solution 5: Demo Deployment (Mock Mode)

For testing the deployment workflow without actually deploying:

```bash
cd C:\Users\pqm847\Documents\PromptOps\mobile-deployment

python example_usage.py
```

This shows you the complete workflow in mock mode (no AWS charges, no builds).

---

## 🎯 Recommended Path

**For Quick Deployment:**
1. ✅ Install Java 17 LTS (~10 minutes)
2. ✅ Deploy netSenseAI (~5-10 minutes)
3. ✅ Share download URL with testers

**Total time:** ~20 minutes

---

## 📋 After Installing Java 17

Once Java 17 is installed and verified, run:

```bash
cd C:\Users\pqm847\Documents\PromptOps

python mobile-deployment\deploy_android_app.py ^
  --repo-url https://github.com/kirankumarhs29/netSenseAI ^
  --app-name "netSenseAI" ^
  --option A ^
  --aws-bucket netsense-ai-2026 ^
  --aws-region us-east-1
```

**Expected output:**
```
======================================================================
  PromptOps Android App Deployment
======================================================================

App Name:     netSenseAI
Repository:   https://github.com/kirankumarhs29/netSenseAI
Branch:       main
Option:       A

======================================================================

[Cloning repository...]
[Building APK with Java 17...]
[Uploading to S3...]
[Creating CloudFront...]
[Generating download page...]

======================================================================
  Deployment Result
======================================================================

[OK] Deployment Successful!

Download Page: https://netsense-ai-2026.s3.us-east-1.amazonaws.com/...
Direct APK: https://netsense-ai-2026.s3.us-east-1.amazonaws.com/...
```

---

## 🔧 Troubleshooting

### After Installing Java 17, still seeing Java 26?

**Close and reopen terminal** - PATH changes require new terminal session

### Multiple Java versions?

Use **JAVA_HOME** to control which version:
```bash
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.x.x
```

### Can't install Java 17?

Use **Solution 3** (pre-built APK upload) - no Java needed!

---

## 📊 Comparison

| Solution | Time | Complexity | Best For |
|----------|------|------------|----------|
| Install Java 17 | 20 min | Easy | Long-term use |
| Set JAVA_HOME | 5 min | Easy | Already have Java 17 |
| Upload pre-built APK | 2 min | Very Easy | One-time deployment |
| Docker | 30 min | Medium | CI/CD automation |
| Mock Mode | 1 min | Very Easy | Testing workflow |

---

## ✅ Next Steps

1. **Choose a solution above**
2. **Follow the steps**
3. **Run the deployment command**
4. **Get your download URL**
5. **Share with testers!**

---

**Need help?** Let me know which solution you'd like to try!
