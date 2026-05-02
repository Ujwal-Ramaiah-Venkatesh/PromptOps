# GCP Free Trial Setup Guide

**Date:** 2026-05-01  
**Phase:** 3 - Multi-Cloud Support  
**Cost:** $0 ($300 free credit for 90 days)

---

## 🎯 Overview

This guide sets up Google Cloud Platform (GCP) for PromptOps Phase 3 multi-cloud support.

**Benefits:**
- ✅ **$300 FREE CREDIT** (90 days)
- ✅ No charges after credit expires (requires opt-in)
- ✅ All GCP services available
- ✅ Real production environment

---

## 🚀 Step-by-Step Setup

### **Step 1: Create GCP Account**

1. **Go to:** https://cloud.google.com/free
2. **Click:** "Get started for free"
3. **Sign in** with Google account
4. **Country & Terms:** Select your country, accept terms
5. **Account Type:** Choose "Individual" or "Business"
6. **Payment Method:** 
   - Credit card required (for verification only)
   - **No charges without explicit upgrade**
   - $300 credit applied automatically

**Result:** ✅ GCP account created with $300 credit

---

### **Step 2: Create Project**

1. Go to: https://console.cloud.google.com/
2. Click project dropdown (top left)
3. Click "New Project"
4. **Project Name:** `promptops-dev`
5. **Project ID:** `promptops-dev-123456` (must be unique)
6. Click "Create"

**Result:** ✅ Project `promptops-dev` created

---

### **Step 3: Enable APIs**

Enable required APIs for resource discovery:

```bash
# Install gcloud CLI first (see step 4)

# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage-api.googleapis.com

# Enable Cloud Billing API
gcloud services enable cloudbilling.googleapis.com

# Enable Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com
```

Or enable via Console:
1. Go to: https://console.cloud.google.com/apis/library
2. Search and enable:
   - Compute Engine API
   - Cloud Storage API
   - Cloud Billing API
   - Cloud Resource Manager API

**Result:** ✅ APIs enabled

---

### **Step 4: Install gcloud CLI**

**Windows:**
```bash
# Download installer
# https://cloud.google.com/sdk/docs/install

# Or use Chocolatey
choco install gcloudsdk
```

**Mac:**
```bash
brew install --cask google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Verify:**
```bash
gcloud --version
```

**Result:** ✅ gcloud CLI installed

---

### **Step 5: Authenticate**

```bash
# Login to GCP
gcloud auth login

# Set default project
gcloud config set project promptops-dev-123456

# Set application default credentials
gcloud auth application-default login

# Verify
gcloud auth list
```

**Result:** ✅ Authenticated and project set

---

### **Step 6: Create Service Account**

For programmatic access (PromptOps backend):

```bash
# Create service account
gcloud iam service-accounts create promptops-sa \
  --display-name="PromptOps Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding promptops-dev-123456 \
  --member="serviceAccount:promptops-sa@promptops-dev-123456.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"

gcloud projects add-iam-policy-binding promptops-dev-123456 \
  --member="serviceAccount:promptops-sa@promptops-dev-123456.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding promptops-dev-123456 \
  --member="serviceAccount:promptops-sa@promptops-dev-123456.iam.gserviceaccount.com" \
  --role="roles/billing.viewer"

# Create and download key
gcloud iam service-accounts keys create ~/gcp-credentials.json \
  --iam-account=promptops-sa@promptops-dev-123456.iam.gserviceaccount.com

echo "✅ Service account key saved to ~/gcp-credentials.json"
```

**Result:** ✅ Service account created with read-only access

---

### **Step 7: Set Environment Variables**

```bash
# In .env file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-credentials.json"
export GCP_PROJECT_ID="promptops-dev-123456"
export GCP_REGION="us-central1"
```

Or for Windows:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\gcp-credentials.json"
```

**Result:** ✅ Environment configured

---

## 🧪 Test GCP Connection

### **Python Test:**

```python
# test_gcp_connection.py
from google.cloud import compute_v1
from google.cloud import storage
import os

def test_compute():
    """Test Compute Engine access."""
    project = os.getenv('GCP_PROJECT_ID', 'promptops-dev-123456')
    
    client = compute_v1.InstancesClient()
    
    # List instances in all zones
    zones_client = compute_v1.ZonesClient()
    zones = zones_client.list(project=project)
    
    print(f"✅ Compute Engine API working")
    print(f"   Available zones: {len(list(zones))}")
    
    return True

def test_storage():
    """Test Cloud Storage access."""
    client = storage.Client()
    
    buckets = list(client.list_buckets())
    print(f"✅ Cloud Storage API working")
    print(f"   Buckets found: {len(buckets)}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  GCP Connection Test")
    print("=" * 60)
    
    try:
        test_compute()
        test_storage()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
```

**Run test:**
```bash
python test_gcp_connection.py
```

---

## 💰 Free Tier Details

### **$300 Credit (90 days):**
- Valid for 90 days from signup
- Applies to all GCP services
- No charges after credit expires (unless you upgrade)

### **Always Free (after trial):**
- **Compute Engine:** 1 f1-micro instance/month (US regions)
- **Cloud Storage:** 5 GB standard storage
- **Cloud Functions:** 2 million invocations/month
- **Cloud Build:** 120 build-minutes/day

**Source:** https://cloud.google.com/free

---

## 📦 Create Test Resources

### **1. Compute Engine VM:**

```bash
# Create f1-micro instance (free tier)
gcloud compute instances create promptops-test-vm \
  --zone=us-central1-a \
  --machine-type=f1-micro \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --tags=test,promptops

# List instances
gcloud compute instances list
```

### **2. Cloud Storage Bucket:**

```bash
# Create bucket
gcloud storage buckets create gs://promptops-test-bucket-20260501 \
  --location=us-central1 \
  --uniform-bucket-level-access

# Upload test file
echo "test" > test.txt
gcloud storage cp test.txt gs://promptops-test-bucket-20260501/

# List buckets
gcloud storage buckets list
```

### **3. Cloud SQL Instance (optional):**

```bash
# Create Cloud SQL instance (db-f1-micro is free tier eligible)
gcloud sql instances create promptops-test-db \
  --tier=db-f1-micro \
  --region=us-central1 \
  --database-version=POSTGRES_14

# List instances
gcloud sql instances list
```

**These will be discovered by PromptOps!**

---

## 🔐 Security Best Practices

### **1. Use Least Privilege:**

Service account should have minimal permissions:
- `roles/compute.viewer` - Read Compute Engine
- `roles/storage.objectViewer` - Read Storage
- `roles/billing.viewer` - Read billing data

### **2. Rotate Keys Regularly:**

```bash
# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=promptops-sa@promptops-dev-123456.iam.gserviceaccount.com

# Create new key
gcloud iam service-accounts keys create ~/gcp-credentials-new.json \
  --iam-account=promptops-sa@promptops-dev-123456.iam.gserviceaccount.com
```

### **3. Never Commit Credentials:**

Add to `.gitignore`:
```
# GCP credentials
gcp-credentials.json
*-credentials.json
.gcp/
```

### **4. Enable Audit Logging:**

```bash
# View audit logs
gcloud logging read "protoPayload.serviceName=compute.googleapis.com" \
  --limit 10
```

---

## 🐛 Troubleshooting

### **Issue: "Permission denied"**

```bash
# Check current account
gcloud auth list

# Check project
gcloud config get-value project

# Check service account permissions
gcloud projects get-iam-policy promptops-dev-123456 \
  --flatten="bindings[].members" \
  --filter="bindings.members:promptops-sa@*"
```

### **Issue: "API not enabled"**

```bash
# List enabled APIs
gcloud services list --enabled

# Enable missing API
gcloud services enable compute.googleapis.com
```

### **Issue: "Credentials not found"**

```bash
# Check environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Set explicitly
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-credentials.json"
```

---

## ✅ Setup Checklist

- [ ] GCP account created ($300 credit applied)
- [ ] Project `promptops-dev` created
- [ ] Required APIs enabled
- [ ] gcloud CLI installed
- [ ] Authenticated with `gcloud auth login`
- [ ] Service account created
- [ ] Service account key downloaded
- [ ] Environment variables set
- [ ] Test connection successful
- [ ] Test resources created (optional)

---

## 📚 Resources

- **GCP Free Tier:** https://cloud.google.com/free
- **GCP Console:** https://console.cloud.google.com/
- **gcloud CLI Docs:** https://cloud.google.com/sdk/gcloud
- **Python Client Libraries:** https://cloud.google.com/python/docs/reference
- **Pricing Calculator:** https://cloud.google.com/products/calculator

---

## 🎯 Next Steps

1. ✅ Complete this GCP setup
2. → Create GCP discovery module
3. → Add GCP cost tracking
4. → Test with real GCP resources
5. → Move to Azure setup

---

**Status:** 📝 Ready for Phase 3 GCP integration
