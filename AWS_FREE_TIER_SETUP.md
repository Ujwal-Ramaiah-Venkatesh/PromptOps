# AWS Free Tier Setup Guide for PromptOps Phase 2

**Date:** 2026-04-30  
**Phase:** Phase 2 - Real AWS Integration  
**Cost:** $0 (using AWS Free Tier)

---

## 🎯 Overview

This guide walks you through setting up AWS Free Tier for PromptOps Phase 2 development at **zero cost** for 12 months.

---

## 📋 What's Included in AWS Free Tier

### **Free for 12 Months:**

| Service | Free Tier Limit | Perfect For |
|---------|----------------|-------------|
| **EC2** | 750 hours/month t2.micro | Testing PromptOps deployments |
| **RDS** | 750 hours/month db.t2.micro | Testing database operations |
| **S3** | 5 GB storage + 20,000 GET requests | Testing file storage |
| **Lambda** | 1M requests/month | Testing serverless functions |
| **CloudWatch** | 10 custom metrics | Testing monitoring |
| **DynamoDB** | 25 GB storage | Testing NoSQL database |
| **SNS** | 1M publishes | Testing notifications |
| **SQS** | 1M requests | Testing queues |

### **Always Free:**

| Service | Limit | Usage |
|---------|-------|-------|
| **Lambda** | 1M requests/month | Always free |
| **API Gateway** | 1M API calls/month | Always free |
| **CloudWatch Logs** | 5 GB ingestion | Always free |

**Source:** https://aws.amazon.com/free/

---

## 🚀 Step-by-Step Setup

### **Step 1: Create AWS Account**

1. **Go to:** https://aws.amazon.com/free/
2. **Click:** "Create a Free Account"
3. **Provide:**
   - Email address
   - Password
   - AWS account name (e.g., "promptops-dev")
4. **Contact Information:**
   - Choose "Personal" account type
   - Fill in your details
5. **Payment Method:**
   - **⚠️ IMPORTANT:** Credit card required (for verification only)
   - **No charges** if you stay within Free Tier limits
   - Set up billing alerts (Step 3) to avoid surprises
6. **Identity Verification:**
   - Phone verification (automated call/SMS)
7. **Select Support Plan:**
   - Choose "Basic Support - Free"

**Result:** ✅ AWS account created

---

### **Step 2: Create IAM User (Best Practice)**

**⚠️ Never use root account for development!**

1. **Open IAM Console:** https://console.aws.amazon.com/iam/
2. **Click:** "Users" → "Add users"
3. **User Details:**
   - User name: `promptops-dev`
   - Access type: ☑️ Programmatic access + ☑️ AWS Management Console access
4. **Permissions:**
   - Click "Attach existing policies directly"
   - Select these policies:
     - ☑️ `AmazonEC2ReadOnlyAccess`
     - ☑️ `AmazonRDSReadOnlyAccess`
     - ☑️ `AmazonS3ReadOnlyAccess`
     - ☑️ `AWSLambdaReadOnlyAccess`
     - ☑️ `CloudWatchReadOnlyAccess`
     - ☑️ `AWSCostExplorerReadOnlyAccess`
5. **Tags (optional):**
   - Key: `Project`, Value: `PromptOps`
6. **Review & Create**
7. **⚠️ SAVE CREDENTIALS:**
   ```
   Access Key ID: AKIA...
   Secret Access Key: ...
   ```
   **Download CSV and store securely!**

**Result:** ✅ IAM user `promptops-dev` created with read-only access

---

### **Step 3: Set Up Billing Alerts (CRITICAL!)**

**Prevent accidental charges:**

1. **Open Billing Console:** https://console.aws.amazon.com/billing/
2. **Click:** "Billing preferences"
3. **Enable:**
   - ☑️ "Receive Free Tier Usage Alerts"
   - Email: your-email@example.com
4. **Create Budget:**
   - Go to "Budgets" → "Create budget"
   - Type: "Cost budget"
   - Name: "PromptOps Free Tier Alert"
   - Budgeted amount: **$5/month**
   - Alert threshold: **$1 (20%)**
   - Email notification: your-email@example.com
5. **Click:** "Create budget"

**Result:** ✅ You'll get email alerts if costs exceed $1/month

---

### **Step 4: Configure AWS CLI Locally**

**Install AWS CLI:**

```bash
# Windows
winget install Amazon.AWSCLI

# Or download from: https://aws.amazon.com/cli/
```

**Configure credentials:**

```bash
aws configure

# Enter when prompted:
AWS Access Key ID: <Your Access Key from Step 2>
AWS Secret Access Key: <Your Secret Key from Step 2>
Default region name: us-east-1
Default output format: json
```

**Verify setup:**

```bash
# Test connection
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/promptops-dev"
}
```

**Result:** ✅ AWS CLI configured and working

---

### **Step 5: Install boto3 in PromptOps**

```bash
cd c:\Users\pqm847\Documents\PromptOps

# Install boto3
pip install boto3

# Add to requirements.txt
echo boto3==1.28.0 >> requirements.txt
```

**Test boto3:**

```python
# test_aws_connection.py
import boto3

def test_connection():
    try:
        # Create EC2 client
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # List regions (read-only operation, no cost)
        regions = ec2.describe_regions()
        
        print("✅ AWS Connection Successful!")
        print(f"Found {len(regions['Regions'])} AWS regions")
        
        return True
    except Exception as e:
        print(f"❌ AWS Connection Failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

**Run test:**

```bash
python test_aws_connection.py
```

**Result:** ✅ boto3 installed and connected to AWS

---

## 🔒 Security Best Practices

### **1. Never Commit Credentials**

Add to `.gitignore`:

```
# AWS credentials
.aws/
aws_credentials.json
*.pem
*.key

# Environment variables
.env
.env.local
```

### **2. Use Environment Variables**

Create `.env` file (already in `.gitignore`):

```bash
# .env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

Load in Python:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# boto3 automatically reads these environment variables
ec2 = boto3.client('ec2')
```

### **3. Use Read-Only Access First**

Start with read-only IAM policies:
- Test discovery and scanning (no writes)
- Add write permissions only when needed
- Use principle of least privilege

---

## 💰 Staying Within Free Tier

### **Monitor Usage:**

1. **AWS Free Tier Dashboard:** https://console.aws.amazon.com/billing/home#/freetier
2. **Check Daily:** Look for "Free tier usage alerts"
3. **Track Services:**
   - EC2: Don't exceed 750 hours/month (1 t2.micro instance)
   - RDS: Don't exceed 750 hours/month (1 db.t2.micro)
   - S3: Keep under 5 GB storage

### **Tips to Avoid Charges:**

✅ **Stop resources when not in use:**
```bash
# Stop EC2 instance
aws ec2 stop-instances --instance-ids i-1234567890abcdef0

# Stop RDS instance (not delete, just stop)
aws rds stop-db-instance --db-instance-identifier my-test-db
```

✅ **Use t2.micro (free tier) not t3.micro (paid)**

✅ **Set up auto-shutdown for dev instances:**
- Use AWS Lambda to stop instances at 6 PM daily
- Start manually when needed

✅ **Delete unused resources:**
```bash
# Delete old snapshots
aws ec2 describe-snapshots --owner-ids self

# Delete unused EBS volumes
aws ec2 describe-volumes --filters "Name=status,Values=available"
```

---

## 📊 Phase 2 AWS Usage Estimate

### **For PromptOps Development:**

| Service | Usage | Free Tier | Cost |
|---------|-------|-----------|------|
| EC2 (t2.micro) | 1 instance 24/7 | 750 hours | $0 ✅ |
| RDS (db.t2.micro) | 1 instance 24/7 | 750 hours | $0 ✅ |
| S3 | <5 GB | 5 GB free | $0 ✅ |
| Lambda | <100K invocations | 1M free | $0 ✅ |
| CloudWatch | 10 metrics | 10 free | $0 ✅ |

**Total Phase 2 Cost:** **$0/month** ✅

---

## 🧪 Testing Resources to Create

Once AWS is set up, create these test resources:

### **1. Test EC2 Instances:**

```bash
# Launch t2.micro (free tier)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t2.micro \
  --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=promptops-test-web},{Key=Environment,Value=staging},{Key=Project,Value=PromptOps}]'
```

### **2. Test RDS Instance:**

```bash
# Create db.t2.micro (free tier)
aws rds create-db-instance \
  --db-instance-identifier promptops-test-db \
  --db-instance-class db.t2.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password ChangeMe123! \
  --allocated-storage 20 \
  --tags Key=Project,Value=PromptOps
```

### **3. Test S3 Bucket:**

```bash
# Create bucket
aws s3 mb s3://promptops-test-bucket-20260430

# Add test file
echo "test" > test.txt
aws s3 cp test.txt s3://promptops-test-bucket-20260430/
```

**These will be scanned by PromptOps discovery!**

---

## ✅ Setup Checklist

- [ ] AWS account created
- [ ] IAM user `promptops-dev` created with read-only access
- [ ] Credentials saved securely (CSV downloaded)
- [ ] Billing alerts configured ($5 budget, $1 alert)
- [ ] AWS CLI installed and configured
- [ ] boto3 installed in PromptOps project
- [ ] Test connection successful
- [ ] `.env` file created with credentials
- [ ] `.gitignore` updated to exclude credentials
- [ ] Test resources created (optional: EC2, RDS, S3)

---

## 🆘 Troubleshooting

### **Issue: "Credentials not found"**

**Solution:**
```bash
# Check credentials file
cat ~/.aws/credentials

# Should show:
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

### **Issue: "Access Denied"**

**Solution:** Check IAM permissions:
```bash
# Verify your user
aws iam get-user

# List attached policies
aws iam list-attached-user-policies --user-name promptops-dev
```

### **Issue: "Region not found"**

**Solution:** Set region explicitly:
```bash
export AWS_DEFAULT_REGION=us-east-1
# Or in Python:
ec2 = boto3.client('ec2', region_name='us-east-1')
```

---

## 📚 Resources

- **AWS Free Tier:** https://aws.amazon.com/free/
- **boto3 Documentation:** https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **AWS CLI Reference:** https://docs.aws.amazon.com/cli/latest/reference/
- **IAM Best Practices:** https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

---

## 🎯 Next Steps

Once AWS is set up:

1. ✅ Complete this setup guide
2. → Install boto3 dependencies
3. → Create AWS resource discovery module
4. → Replace mock discovery with real boto3 scanning
5. → Test with your real AWS resources

---

**Ready to proceed?** Follow this guide to set up AWS Free Tier, then we'll move to implementing boto3 integration!

**Estimated setup time:** 20-30 minutes

---

**Status:** 📝 Setup guide created, ready for implementation
