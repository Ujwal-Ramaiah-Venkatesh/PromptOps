# PromptOps Mobile Deployment - Quick Start Guide

**Version:** 1.0.0  
**Date:** May 11, 2026  
**Status:** Production Ready

---

## 🚀 Quick Deploy (30 seconds)

Deploy your Android app in 3 commands:

```bash
# 1. Install dependencies
pip install boto3

# 2. Configure AWS (optional - works in mock mode without this)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 3. Deploy!
python mobile-deployment/deploy_android_app.py \
  --repo-url https://github.com/your/android-app \
  --app-name "My App" \
  --option A \
  --aws-bucket my-apps
```

**Result:** Download page URL with your APK ready to share!

---

## 📱 Supported Repositories

### ✅ Ready to Deploy

```bash
# AdaptiveRTC PTT - Kotlin Multiplatform app
python mobile-deployment/deploy_android_app.py \
  --repo-url https://github.com/kirankumarhs29/AdaptiveRTC_PTT \
  --app-name "AdaptiveRTC PTT" \
  --option A \
  --aws-bucket adaptive-rtc-apps

# netSenseAI - Network monitoring app
python mobile-deployment/deploy_android_app.py \
  --repo-url https://github.com/kirankumarhs29/netSenseAI \
  --app-name "netSenseAI" \
  --option A \
  --aws-bucket netsense-apps
```

---

## 🎯 Deployment Options

### Option A: AWS S3 + CloudFront (✅ Ready Now)

**Best for:** Beta testing, internal distribution, quick sharing

**Features:**
- ✅ Global CDN (CloudFront)
- ✅ Custom download page
- ✅ Free tier eligible
- ✅ 5-15 minute deployment
- ✅ No app store review needed

**Cost:**
- Free tier: $0/month (first 12 months)
- After: ~$2-3/month for 1,000 downloads

**Usage:**
```bash
python mobile-deployment/deploy_android_app.py \
  --repo-url <github-url> \
  --app-name "Your App" \
  --option A \
  --aws-bucket your-bucket
```

---

### Option B: Firebase App Distribution (⏳ Coming Soon)

**Best for:** Beta testing with tester management

**Features:**
- Tester email management
- Release notes
- Feedback collection
- Analytics
- Automatic updates

**Status:** Architecture ready, Firebase CLI integration pending

---

### Option C: Google Play Store (⏳ Coming Soon)

**Best for:** Production public release

**Features:**
- Store presence
- Automatic updates
- Monetization
- Store optimization
- Review system

**Status:** Architecture ready, Play Console API integration pending

---

## 📋 Prerequisites

### Required
- Python 3.8+
- Git
- Android SDK (for building APKs)
- Java JDK 11+ (for Gradle)

### Optional (for real AWS deployment)
- AWS account
- AWS credentials configured
- boto3 installed: `pip install boto3`

### Works Without AWS!
The system automatically uses **mock mode** if:
- boto3 is not installed
- AWS credentials are not configured
- You set `use_mock=True`

---

## 🔧 Installation

### Step 1: Clone PromptOps

```bash
git clone https://github.com/your/promptops
cd promptops
```

### Step 2: Install Python Dependencies

```bash
# Core dependencies
pip install fastapi uvicorn pydantic

# Mobile deployment (Option A)
pip install boto3

# Optional: Firebase (Option B - future)
# pip install firebase-admin

# Optional: Play Store (Option C - future)
# pip install google-api-python-client google-auth
```

### Step 3: Configure AWS (Optional)

**Method 1: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Method 2: AWS CLI**
```bash
aws configure
# Enter: Access Key, Secret Key, Region, Output format
```

**Method 3: IAM Role (EC2/Lambda)**
Automatically configured if running on AWS infrastructure.

---

## 💻 Usage Examples

### Example 1: CLI Deployment

```bash
python mobile-deployment/deploy_android_app.py \
  --repo-url https://github.com/kirankumarhs29/AdaptiveRTC_PTT \
  --branch main \
  --app-name "AdaptiveRTC PTT" \
  --option A \
  --aws-bucket adaptive-rtc-apps \
  --aws-region us-east-1
```

**Output:**
```
======================================================================
  PromptOps Android App Deployment
======================================================================

App Name:     AdaptiveRTC PTT
Repository:   https://github.com/kirankumarhs29/AdaptiveRTC_PTT
Branch:       main
Option:       A

======================================================================

[Cloning repository...]
[Building APK...]
[Uploading to S3...]
[Creating CloudFront...]
[Generating download page...]

======================================================================
  Deployment Result
======================================================================

✅ Deployment Successful!

📥 Download Page: https://adaptive-rtc-apps.s3.us-east-1.amazonaws.com/apps/AdaptiveRTC_PTT/1.0.0/index.html
📱 Direct APK: https://adaptive-rtc-apps.s3.us-east-1.amazonaws.com/apps/AdaptiveRTC_PTT/1.0.0/app-debug.apk
```

---

### Example 2: Python SDK

```python
from mobile-deployment.deploy_android_app import AndroidDeploymentOrchestrator

# Create orchestrator
orchestrator = AndroidDeploymentOrchestrator()

# Deploy
result = orchestrator.deploy_from_git(
    repo_url="https://github.com/kirankumarhs29/AdaptiveRTC_PTT",
    app_name="AdaptiveRTC PTT",
    deployment_option="A",
    aws_config={"bucket_name": "adaptive-rtc-apps"}
)

# Cleanup
orchestrator.cleanup()

# Results
print(f"Status: {result['status']}")
print(f"Download: {result.get('download_url')}")
```

---

### Example 3: REST API

```bash
# Start PromptOps API server
python api_gateway/start_with_mock_db.py

# Deploy via API
curl -X POST http://localhost:8000/api/v1/cicd/mobile/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/kirankumarhs29/AdaptiveRTC_PTT",
    "app_name": "AdaptiveRTC PTT",
    "deployment_option": "A",
    "aws_bucket": "adaptive-rtc-apps"
  }'
```

---

### Example 4: Upload Pre-built APK

```bash
# Build APK first (if needed)
cd /path/to/android/project
./gradlew assembleDebug

# Upload to AWS
python mobile-deployment/deploy_android_app.py \
  --apk-path app/build/outputs/apk/debug/app-debug.apk \
  --app-name "My App" \
  --version "1.0.0" \
  --option A \
  --aws-bucket my-apps
```

---

## 🧪 Testing Without AWS

### Mock Mode Testing

```bash
# Test deployment without AWS credentials
python mobile-deployment/example_usage.py
```

**Mock mode provides:**
- ✅ Full workflow simulation
- ✅ Realistic response structures
- ✅ No AWS API calls
- ✅ No AWS charges
- ✅ Perfect for development/testing

---

## 📊 API Endpoints

### Mobile Deployment APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/cicd/mobile/deploy` | POST | Deploy from Git |
| `/api/v1/cicd/mobile/upload-apk` | POST | Upload pre-built APK |
| `/api/v1/cicd/mobile/build` | POST | Build APK only |
| `/api/v1/cicd/mobile/version-info` | GET | Get app version |
| `/api/v1/cicd/mobile/aws/create-bucket` | POST | Create S3 bucket |
| `/api/v1/cicd/mobile/aws/create-cdn` | POST | Create CloudFront |
| `/api/v1/cicd/health` | GET | Health check |

### API Documentation

```bash
# Start server
python api_gateway/start_with_mock_db.py

# View interactive docs
open http://localhost:8000/docs
```

---

## 🔒 Security Best Practices

### AWS Security

1. **Use IAM Roles** (preferred)
   ```bash
   # Attach IAM role to EC2 instance
   # No need to configure credentials
   ```

2. **Use AWS Secrets Manager**
   ```bash
   aws secretsmanager create-secret \
     --name promptops/mobile/aws-credentials \
     --secret-string '{"key":"value"}'
   ```

3. **Use Environment Variables** (development)
   ```bash
   export AWS_ACCESS_KEY_ID=xxx
   export AWS_SECRET_ACCESS_KEY=xxx
   ```

4. **Never commit credentials**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "credentials.json" >> .gitignore
   ```

### S3 Bucket Security

✅ **Enabled by default:**
- Server-side encryption (AES256)
- Versioning
- Public access limited to `/apps/*` only
- CORS configured
- Bucket policy with least privilege

---

## 💰 Cost Estimation

### AWS Free Tier (First 12 Months)

| Service | Free Tier | Typical Usage | Status |
|---------|-----------|---------------|--------|
| S3 Storage | 5 GB | 10 APKs × 25 MB = 250 MB | ✅ FREE |
| S3 GET Requests | 20,000/month | 1,000 downloads | ✅ FREE |
| S3 PUT Requests | 2,000/month | 10 uploads | ✅ FREE |
| CloudFront Transfer | 1 TB/month | 1,000 × 25 MB = 25 GB | ✅ FREE |
| CloudFront Requests | 10M/month | 1,000 requests | ✅ FREE |

### After Free Tier

**Small Scale (1,000 downloads/month):**
- S3 Storage (250 MB): $0.01
- S3 Requests: $0.01
- CloudFront (25 GB): $2.13
- **Total: ~$2.15/month**

**Medium Scale (10,000 downloads/month):**
- CloudFront (250 GB): $21.25
- **Total: ~$21.50/month**

**Large Scale (100,000 downloads/month):**
- CloudFront (2.5 TB): $212.50
- **Total: ~$215/month**

---

## 🐛 Troubleshooting

### Issue: `gradlew not found`

**Cause:** Repository doesn't have gradlew wrapper

**Solution:**
```bash
# Generate gradlew in your project
gradle wrapper
git add gradlew gradlew.bat gradle/
git commit -m "Add Gradle wrapper"
```

---

### Issue: `Build timeout after 600 seconds`

**Cause:** Large project or slow build

**Solution:** Increase timeout in code
```python
# In android_builder.py, line ~92
result = subprocess.run(
    cmd,
    cwd=self.project_path,
    capture_output=True,
    text=True,
    timeout=1200  # Increase to 20 minutes
)
```

---

### Issue: `NoCredentialsError`

**Cause:** AWS credentials not configured

**Solution:**
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Option 3: Use mock mode (no AWS needed)
python example_usage.py
```

---

### Issue: `BucketAlreadyExists`

**Cause:** S3 bucket names are globally unique

**Solution:** Choose a different bucket name
```bash
# Bad: my-app (too common)
# Good: mycompany-myapp-2026
# Better: mycompany-myapp-prod-us-east-1
```

---

### Issue: `APK file not found after build`

**Cause:** Build failed or APK in unexpected location

**Solution:**
```bash
# Check build output manually
./gradlew assembleDebug
find . -name "*.apk"

# Check Gradle logs
./gradlew assembleDebug --info
```

---

## 📚 Next Steps

### 1. Deploy Your First App

```bash
python mobile-deployment/deploy_android_app.py \
  --repo-url https://github.com/kirankumarhs29/AdaptiveRTC_PTT \
  --app-name "AdaptiveRTC PTT" \
  --option A \
  --aws-bucket test-adaptive-rtc
```

### 2. Share the Download Page

Send the download URL to testers:
```
https://your-bucket.s3.us-east-1.amazonaws.com/apps/YourApp/1.0.0/index.html
```

### 3. Monitor Downloads

```bash
# View S3 access logs
aws s3 ls s3://your-bucket/logs/

# CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name NumberOfObjects \
  --dimensions Name=BucketName,Value=your-bucket
```

### 4. Set Up CI/CD

Add to GitHub Actions:
```yaml
- name: Deploy Android App
  run: |
    python mobile-deployment/deploy_android_app.py \
      --repo-url ${{ github.repository }} \
      --app-name "My App" \
      --option A \
      --aws-bucket my-apps
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## 📖 Additional Resources

### Documentation
- [Complete README](mobile-deployment/README.md)
- [Architecture Overview](MOBILE_DEPLOYMENT_COMPLETE.md)
- [API Reference](http://localhost:8000/docs)

### Example Code
- [Usage Examples](mobile-deployment/example_usage.py)
- [API Integration](api_gateway/cicd_routes.py)

### Support
- GitHub Issues: [Report a bug](https://github.com/promptops/issues)
- Email: devops@promptops.ai

---

## ✅ Checklist

Before deploying to production:

- [ ] AWS credentials configured
- [ ] Bucket name chosen (globally unique)
- [ ] boto3 installed
- [ ] Test deployment in mock mode
- [ ] Test deployment with real AWS
- [ ] Verify download page loads
- [ ] Test APK installation on device
- [ ] Set up CloudWatch monitoring
- [ ] Configure S3 access logging
- [ ] Review security settings
- [ ] Document for team

---

**Ready to deploy?** Run the quick start command at the top! 🚀

**Need help?** Check the troubleshooting section or open an issue.

**Want more features?** Options B and C coming soon!
