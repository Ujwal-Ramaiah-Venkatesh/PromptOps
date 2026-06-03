# Java 17 Installation - Manual Steps

The automated installation encountered issues. Here's the manual installation guide.

## ✅ Quick Manual Install (5 minutes)

### Option 1: Use Existing Java (If Available)

Check if you have Java 17 or 11 already:

```bash
# Check all Java versions
where java

# If you see multiple versions, try setting JAVA_HOME manually
```

### Option 2: Download & Install Java 17 Manually

**Step 1: Download**
1. Go to: https://adoptium.net/teapot/
2. Click "Download" for **Java 17 LTS**
3. Choose: Windows x64 MSI

**Step 2: Install**
1. Run the downloaded `.msi` file
2. ✅ Check: "Set JAVA_HOME variable"
3. ✅ Check: "Add to PATH"
4. Click "Install"

**Step 3: Verify (Open NEW terminal)**
```bash
java -version
# Should show: openjdk version "17.x.x"
```

**Step 4: Set for Current Session**
```bash
# PowerShell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.x"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Verify
java -version
```

---

## 🚀 Alternative: Use Pre-Built APK (No Java Needed!)

**If you can build the APK on another machine:**

1. On a machine with Java 17:
```bash
git clone https://github.com/kirankumarhs29/netSenseAI
cd netSenseAI
gradlew.bat :androidApp:assembleDebug
```

2. Copy APK file:
```
netSenseAI\androidApp\build\outputs\apk\debug\androidApp-debug.apk
```

3. Deploy from PromptOps (NO JAVA NEEDED):
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

## 🎯 Recommended: Pre-Built APK Upload

Since you have AWS credentials and boto3 working, the **fastest solution** is to:

1. Build APK on a machine with Java 17 (or ask a colleague)
2. Transfer the APK file to this machine
3. Use PromptOps to upload and deploy (2 minutes)

**This avoids all Java version issues!**

---

## Need Help?

Let me know which approach you'd like to try:
1. Manual Java 17 install
2. Pre-built APK upload
3. Try a different repository that builds successfully
