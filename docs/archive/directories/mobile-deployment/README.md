# PromptOps Mobile App Deployment

Automated mobile application deployment for Android (and iOS in future).

## Deployment Options

### Option A: AWS S3 + CloudFront (✅ Implemented)
Direct APK hosting with CDN distribution. Perfect for:
- Beta testing
- Internal distribution
- Quick app sharing
- Free tier eligible

### Option B: Firebase App Distribution (⏳ Planned)
Beta testing platform. Perfect for:
- Tester management
- Release notes
- Feedback collection
- Analytics

### Option C: Google Play Store (⏳ Planned)
Production deployment. Perfect for:
- Public release
- Monetization
- Play Console integration
- Store optimization

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required:**
- `boto3` - AWS SDK for S3 and CloudFront

**Optional:**
- `firebase-admin` - For Option B (future)
- `google-api-python-client` - For Option C (future)

### 2. Configure AWS Credentials

Option A: Environment variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Option B: AWS CLI
```bash
aws configure
```

### 3. Deploy Your App

```bash
python deploy_android_app.py \
  --repo-url https://github.com/yourusername/your-android-app \
  --app-name "My Android App" \
  --option A \
  --aws-bucket my-app-bucket \
  --aws-region us-east-1
```

---

## Usage Examples

### Deploy from Git Repository

```bash
python deploy_android_app.py \
  --repo-url https://github.com/kirankumarhs29/AdaptiveRTC_PTT \
  --app-name "AdaptiveRTC PTT" \
  --branch main \
  --option A \
  --aws-bucket adaptive-rtc-apps
```

### Build APK Locally

```python
from android_builder import AndroidBuilder

builder = AndroidBuilder("/path/to/android/project")
result = builder.build_debug_apk(module="app")
print(f"APK Path: {result['apk_path']}")
```

### Upload Pre-built APK

```python
from aws_mobile_deploy import AWSMobileDeployer

deployer = AWSMobileDeployer(
    bucket_name="my-app-bucket",
    region="us-east-1"
)

result = deployer.deploy_app(
    apk_path="/path/to/app-debug.apk",
    app_name="My App",
    version="1.0.0"
)

print(f"Download URL: {result['download_page_url']}")
```

---

## API Integration

### REST API Endpoints

Add to your FastAPI application:

```python
from api_gateway.cicd_routes import router

app.include_router(router)
```

### Available Endpoints

**Deploy from Git:**
```bash
POST /api/v1/cicd/mobile/deploy
{
  "repo_url": "https://github.com/user/repo",
  "app_name": "My App",
  "deployment_option": "A",
  "aws_bucket": "my-bucket"
}
```

**Upload APK:**
```bash
POST /api/v1/cicd/mobile/upload-apk
{
  "apk_path": "/path/to/app.apk",
  "app_name": "My App",
  "version": "1.0.0",
  "aws_bucket": "my-bucket"
}
```

**Build APK:**
```bash
POST /api/v1/cicd/mobile/build?project_path=/path&build_type=debug
```

**Get Version Info:**
```bash
GET /api/v1/cicd/mobile/version-info?project_path=/path&module=app
```

---

## Architecture

### Deployment Workflow

```
┌─────────────────────────────────────────────────┐
│  1. Clone Git Repository                        │
│     └─> git clone --depth 1 <repo-url>         │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  2. Analyze Project Structure                   │
│     └─> Find gradlew, module, version          │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  3. Build APK                                   │
│     └─> ./gradlew :app:assembleDebug           │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  4. Deploy to Target Platform                   │
│     ├─> Option A: AWS S3 + CloudFront          │
│     ├─> Option B: Firebase (planned)           │
│     └─> Option C: Play Store (planned)         │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  5. Generate Download Page (Option A)           │
│     └─> Responsive HTML with install guide     │
└─────────────────────────────────────────────────┘
```

### AWS Infrastructure

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   S3 Bucket  │─────>│  CloudFront  │─────>│    Users     │
│              │      │     CDN      │      │              │
│ - Apps       │      │              │      │ Download APK │
│ - Metadata   │      │ Global Edge  │      │ Install App  │
│ - HTML Pages │      │ Locations    │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

---

## Components

### 1. AndroidBuilder (`android_builder.py`)

Gradle-based Android APK builder.

**Features:**
- Debug and release builds
- APK signing support
- Version extraction
- Kotlin Multiplatform support

**Methods:**
- `build_debug_apk()` - Build debug APK
- `build_release_apk()` - Build signed release APK
- `get_version_info()` - Extract version from build.gradle
- `clean_build()` - Clean build artifacts

### 2. AWSMobileDeployer (`aws_mobile_deploy.py`)

AWS S3 + CloudFront deployment manager.

**Features:**
- S3 bucket creation with versioning & encryption
- APK upload with SHA256 verification
- CloudFront CDN distribution
- Responsive HTML download page
- CORS configuration
- Public read access for downloads

**Methods:**
- `create_bucket()` - Create/configure S3 bucket
- `upload_apk()` - Upload APK to S3
- `create_cloudfront_distribution()` - Setup CDN
- `generate_download_page()` - Create HTML page
- `deploy_app()` - Complete workflow

### 3. AndroidDeploymentOrchestrator (`deploy_android_app.py`)

End-to-end deployment orchestrator with CLI.

**Features:**
- Git repository cloning
- Automatic project analysis
- APK building
- Multi-option deployment
- Progress tracking
- Error handling

**Methods:**
- `deploy_from_git()` - Deploy from Git repository
- `_clone_repository()` - Clone Git repo
- `_analyze_project()` - Detect project structure
- `_build_apk()` - Build Android APK
- `_deploy_to_aws()` - Deploy to AWS (Option A)
- `_deploy_to_firebase()` - Deploy to Firebase (Option B - mock)
- `_deploy_to_playstore()` - Deploy to Play Store (Option C - mock)

---

## AWS Free Tier Compatibility

✅ **S3 Storage:** 5 GB free (first 12 months)
✅ **S3 Requests:** 20,000 GET, 2,000 PUT (monthly)
✅ **CloudFront:** 1 TB data transfer out (first 12 months)
✅ **CloudFront Requests:** 10M HTTP/HTTPS requests (monthly)

**Estimated Costs (after free tier):**
- S3 Storage: ~$0.023 per GB/month
- CloudFront: ~$0.085 per GB (first 10 TB)
- APK downloads: ~$0.01 per 100 downloads (25 MB APK)

---

## Mock Mode

If `boto3` is not installed or AWS credentials are not configured, the system automatically falls back to **mock mode**.

**Mock mode provides:**
- Full workflow simulation
- Realistic response structures
- No actual AWS API calls
- Perfect for testing and development

**Enable mock mode explicitly:**
```python
deployer = AWSMobileDeployer(
    bucket_name="test-bucket",
    use_mock=True
)
```

---

## Security

### S3 Bucket Security
- ✅ Versioning enabled
- ✅ Server-side encryption (AES256)
- ✅ Public access limited to `/apps/*` path only
- ✅ CORS configured for download page
- ✅ Bucket policy with least privilege

### APK Security
- ✅ SHA256 hash calculation
- ✅ Metadata tracking (version, upload date)
- ✅ Content-Type validation
- ✅ Content-Disposition headers

### Best Practices
1. Use IAM roles instead of access keys
2. Enable S3 bucket logging
3. Set up CloudWatch alarms
4. Implement download rate limiting
5. Regular security audits

---

## Troubleshooting

### Build Failures

**Issue:** `gradlew not found`
**Solution:** Ensure repository has `gradlew` or `gradlew.bat`

**Issue:** `Build timeout`
**Solution:** Increase timeout in `_build_apk()` or check build errors

### AWS Errors

**Issue:** `NoCredentialsError`
**Solution:** Configure AWS credentials (see Quick Start)

**Issue:** `BucketAlreadyExists`
**Solution:** Choose a unique bucket name (globally unique)

**Issue:** `AccessDenied`
**Solution:** Verify IAM permissions for S3 and CloudFront

### APK Errors

**Issue:** `APK file not found after build`
**Solution:** Check build output path and Gradle configuration

**Issue:** `Invalid APK`
**Solution:** Verify Android SDK installation and build.gradle

---

## Future Enhancements

### Option B: Firebase App Distribution
- [ ] Firebase CLI integration
- [ ] Tester management API
- [ ] Release notes automation
- [ ] Feedback collection
- [ ] Analytics integration

### Option C: Google Play Store
- [ ] Play Console API integration
- [ ] Upload AAB bundles
- [ ] Track management (internal, alpha, beta, production)
- [ ] Staged rollouts
- [ ] Store listing updates

### Additional Features
- [ ] iOS app deployment (IPA files)
- [ ] App signing automation
- [ ] Multi-APK support (different architectures)
- [ ] Version comparison
- [ ] Rollback capability
- [ ] Download analytics
- [ ] Custom domain support for download pages

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

---

## License

Copyright © 2026 PromptOps DevOps Team

---

## Support

For issues, questions, or contributions:
- GitHub Issues: [Report a bug](https://github.com/promptops/issues)
- Documentation: [Full docs](https://docs.promptops.ai)
- Email: devops@promptops.ai
