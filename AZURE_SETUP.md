# Azure Free Trial Setup Guide

**Date:** 2026-05-01  
**Phase:** 3 - Multi-Cloud Support  
**Cost:** $0 ($200 free credit for 30 days)

---

## 🎯 Overview

This guide sets up Microsoft Azure for PromptOps Phase 3 multi-cloud support.

**Benefits:**
- ✅ **$200 FREE CREDIT** (30 days)
- ✅ 25+ always-free services
- ✅ No charges after credit expires (requires opt-in)
- ✅ All Azure services available
- ✅ Real production environment

---

## 🚀 Step-by-Step Setup

### **Step 1: Create Azure Account**

1. **Go to:** https://azure.microsoft.com/free
2. **Click:** "Start free"
3. **Sign in** with Microsoft account (or create one)
4. **Country & Phone:** Select your country, verify phone number
5. **Identity Verification:** Verify with credit card (for verification only)
6. **Agreement:** Accept customer agreement and privacy statement
7. **Payment Method:** 
   - Credit card required (for verification only)
   - **No charges without explicit upgrade**
   - $200 credit applied automatically

**Result:** ✅ Azure account created with $200 credit

---

### **Step 2: Create Resource Group**

A resource group is a container for Azure resources.

**Via Portal:**
1. Go to: https://portal.azure.com/
2. Click "Resource groups" in left menu
3. Click "+ Create"
4. **Subscription:** Azure subscription 1 (default)
5. **Resource group:** `promptops-dev-rg`
6. **Region:** East US (or your preferred region)
7. Click "Review + create"
8. Click "Create"

**Via CLI:**
```bash
# Will set up CLI in Step 4
az group create --name promptops-dev-rg --location eastus
```

**Result:** ✅ Resource group `promptops-dev-rg` created

---

### **Step 3: Create Service Principal**

Service principal = credentials for programmatic access.

**Via Portal:**
1. Go to Azure Active Directory
2. Click "App registrations"
3. Click "+ New registration"
4. **Name:** `promptops-service-principal`
5. **Supported account types:** Single tenant
6. Click "Register"
7. **Copy Application (client) ID**
8. **Copy Directory (tenant) ID**
9. Go to "Certificates & secrets"
10. Click "+ New client secret"
11. **Description:** `promptops-dev-secret`
12. **Expires:** 90 days (or longer)
13. Click "Add"
14. **Copy the secret value** (won't be shown again!)

**Via CLI:**
```bash
# Create service principal
az ad sp create-for-rbac --name promptops-sp --role="Reader" --scopes="/subscriptions/{subscription-id}"

# Output will include:
# - appId (client ID)
# - password (client secret)
# - tenant (tenant ID)
```

**Result:** ✅ Service principal created with credentials

---

### **Step 4: Install Azure CLI**

**Windows:**
```bash
# Download MSI installer
# https://aka.ms/installazurecliwindows

# Or use Chocolatey
choco install azure-cli
```

**Mac:**
```bash
brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**Verify:**
```bash
az --version
```

**Result:** ✅ Azure CLI installed

---

### **Step 5: Authenticate**

**Interactive Login:**
```bash
# Login to Azure
az login

# Set default subscription
az account set --subscription "Azure subscription 1"

# Verify
az account show
```

**Service Principal Login:**
```bash
# Login with service principal
az login --service-principal \
  --username <client-id> \
  --password <client-secret> \
  --tenant <tenant-id>
```

**Result:** ✅ Authenticated with Azure

---

### **Step 6: Assign IAM Permissions**

Grant service principal read access to resources.

**Via Portal:**
1. Go to "Subscriptions"
2. Click your subscription
3. Click "Access control (IAM)"
4. Click "+ Add" → "Add role assignment"
5. **Role:** Reader
6. **Assign access to:** User, group, or service principal
7. **Select:** promptops-service-principal
8. Click "Save"

**Via CLI:**
```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Assign Reader role
az role assignment create \
  --assignee <client-id> \
  --role "Reader" \
  --scope "/subscriptions/${SUBSCRIPTION_ID}"

# Also add Cost Management Reader for cost data
az role assignment create \
  --assignee <client-id> \
  --role "Cost Management Reader" \
  --scope "/subscriptions/${SUBSCRIPTION_ID}"
```

**Result:** ✅ Service principal has read-only access

---

### **Step 7: Set Environment Variables**

```bash
# In .env file
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_RESOURCE_GROUP="promptops-dev-rg"
export AZURE_REGION="eastus"
```

Or for Windows PowerShell:
```powershell
$env:AZURE_SUBSCRIPTION_ID="your-subscription-id"
$env:AZURE_TENANT_ID="your-tenant-id"
$env:AZURE_CLIENT_ID="your-client-id"
$env:AZURE_CLIENT_SECRET="your-client-secret"
```

**Result:** ✅ Environment configured

---

## 🧪 Test Azure Connection

### **Python Test:**

```python
# test_azure_connection.py
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
import os

def test_authentication():
    """Test Azure authentication."""
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    print("✅ Azure credentials created")
    return credential

def test_compute(credential, subscription_id):
    """Test Compute Management access."""
    compute_client = ComputeManagementClient(credential, subscription_id)
    
    vms = list(compute_client.virtual_machines.list_all())
    print(f"✅ Compute API working")
    print(f"   Virtual Machines found: {len(vms)}")
    
    return True

def test_storage(credential, subscription_id):
    """Test Storage Management access."""
    storage_client = StorageManagementClient(credential, subscription_id)
    
    accounts = list(storage_client.storage_accounts.list())
    print(f"✅ Storage API working")
    print(f"   Storage Accounts found: {len(accounts)}")
    
    return True

def test_resource_groups(credential, subscription_id):
    """Test Resource Management access."""
    resource_client = ResourceManagementClient(credential, subscription_id)
    
    groups = list(resource_client.resource_groups.list())
    print(f"✅ Resource Management API working")
    print(f"   Resource Groups found: {len(groups)}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  Azure Connection Test")
    print("=" * 60)
    
    try:
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        
        credential = test_authentication()
        test_resource_groups(credential, subscription_id)
        test_compute(credential, subscription_id)
        test_storage(credential, subscription_id)
        
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
```

**Run test:**
```bash
python test_azure_connection.py
```

---

## 💰 Free Tier Details

### **$200 Credit (30 days):**
- Valid for 30 days from signup
- Applies to all Azure services
- No charges after credit expires (unless you upgrade)

### **Always Free (12 months):**
- **Virtual Machines:** 750 hours/month B1S instance
- **Storage:** 5 GB LRS storage
- **Database:** 250 GB SQL Database
- **Bandwidth:** 15 GB outbound data transfer
- **App Service:** 10 web, mobile, or API apps

### **Always Free (no expiration):**
- **Functions:** 1 million requests/month
- **Container Instances:** 20 vCPU seconds/day
- **Service Bus:** 750 hours
- **Computer Vision:** 5,000 transactions/month
- **Cosmos DB:** 1000 RU/s provisioned throughput

**Source:** https://azure.microsoft.com/free

---

## 📦 Create Test Resources

### **1. Virtual Machine:**

```bash
# Create VM (B1s is free tier eligible)
az vm create \
  --resource-group promptops-dev-rg \
  --name promptops-test-vm \
  --image UbuntuLTS \
  --size Standard_B1s \
  --admin-username azureuser \
  --generate-ssh-keys \
  --tags environment=test project=promptops

# List VMs
az vm list --resource-group promptops-dev-rg --output table
```

### **2. Storage Account:**

```bash
# Create storage account
az storage account create \
  --name promptopsteststorage \
  --resource-group promptops-dev-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --tags environment=test project=promptops

# Create blob container
az storage container create \
  --name test-container \
  --account-name promptopsteststorage

# List storage accounts
az storage account list --resource-group promptops-dev-rg --output table
```

### **3. SQL Database (optional):**

```bash
# Create SQL server
az sql server create \
  --name promptops-test-sql \
  --resource-group promptops-dev-rg \
  --location eastus \
  --admin-user sqladmin \
  --admin-password YourStrongPassword123!

# Create database (Basic tier is cheapest)
az sql db create \
  --resource-group promptops-dev-rg \
  --server promptops-test-sql \
  --name promptops-test-db \
  --service-objective Basic

# List databases
az sql db list --resource-group promptops-dev-rg --server promptops-test-sql --output table
```

**These will be discovered by PromptOps!**

---

## 🔐 Security Best Practices

### **1. Use Least Privilege:**

Service principal should have minimal permissions:
- `Reader` - Read all resources
- `Cost Management Reader` - Read cost data
- Avoid `Contributor` or `Owner` roles

### **2. Rotate Secrets Regularly:**

```bash
# Create new secret
az ad sp credential reset --name promptops-sp

# Old secret remains valid until expiry
# Update your .env with new secret
```

### **3. Never Commit Credentials:**

Add to `.gitignore`:
```
# Azure credentials
.azure/
*credentials.json
azure-secrets.env
```

### **4. Enable Activity Logs:**

```bash
# View activity logs
az monitor activity-log list --resource-group promptops-dev-rg

# Create diagnostic settings for monitoring
az monitor diagnostic-settings create \
  --name promptops-diagnostics \
  --resource <resource-id> \
  --logs '[{"category": "Administrative", "enabled": true}]'
```

### **5. Set Up Budget Alerts:**

**Via Portal:**
1. Go to "Cost Management + Billing"
2. Click "Cost Management" → "Budgets"
3. Click "+ Add"
4. **Budget name:** promptops-monthly-budget
5. **Amount:** $50 (or your limit)
6. **Alert conditions:** 80%, 100%
7. **Alert recipients:** your email
8. Click "Create"

---

## 🐛 Troubleshooting

### **Issue: "Authentication failed"**

```bash
# Check credentials
az account show

# Re-login
az logout
az login

# Verify service principal
az ad sp show --id <client-id>
```

### **Issue: "Insufficient permissions"**

```bash
# Check role assignments
az role assignment list --assignee <client-id>

# Add missing roles
az role assignment create \
  --assignee <client-id> \
  --role "Reader" \
  --scope "/subscriptions/${SUBSCRIPTION_ID}"
```

### **Issue: "Subscription not found"**

```bash
# List all subscriptions
az account list --output table

# Set correct subscription
az account set --subscription "subscription-name-or-id"
```

### **Issue: "Resource provider not registered"**

```bash
# Register required providers
az provider register --namespace Microsoft.Compute
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.Sql

# Check registration status
az provider show --namespace Microsoft.Compute
```

---

## ✅ Setup Checklist

- [ ] Azure account created ($200 credit applied)
- [ ] Resource group `promptops-dev-rg` created
- [ ] Service principal created
- [ ] Service principal credentials saved securely
- [ ] Azure CLI installed
- [ ] Authenticated with `az login`
- [ ] IAM roles assigned (Reader, Cost Management Reader)
- [ ] Environment variables set
- [ ] Test connection successful
- [ ] Test resources created (optional)

---

## 📚 Resources

- **Azure Free Account:** https://azure.microsoft.com/free
- **Azure Portal:** https://portal.azure.com/
- **Azure CLI Docs:** https://docs.microsoft.com/cli/azure/
- **Python SDK Docs:** https://docs.microsoft.com/python/api/overview/azure/
- **Pricing Calculator:** https://azure.microsoft.com/pricing/calculator/

---

## 🎯 Next Steps

1. ✅ Complete this Azure setup
2. → Install Azure SDK for Python
3. → Create Azure discovery module
4. → Add Azure cost tracking
5. → Test with real Azure resources
6. → Integrate into unified multi-cloud API

---

## 💡 Cost Optimization Tips

### **1. Use Free Tier Resources:**
- B1s VM instances (750 hours/month free)
- Standard_LRS storage (5 GB free)
- Basic SQL Database tier

### **2. Auto-Shutdown VMs:**
```bash
# Schedule VM auto-shutdown
az vm auto-shutdown \
  --resource-group promptops-dev-rg \
  --name promptops-test-vm \
  --time 1900
```

### **3. Delete Unused Resources:**
```bash
# Delete VM
az vm delete --resource-group promptops-dev-rg --name promptops-test-vm

# Delete storage account
az storage account delete --name promptopsteststorage --resource-group promptops-dev-rg

# Delete entire resource group (careful!)
az group delete --name promptops-dev-rg
```

### **4. Monitor Costs:**
```bash
# View current costs
az consumption usage list --output table

# View budget
az consumption budget list --resource-group promptops-dev-rg
```

### **5. Use Reserved Instances:**
- Save up to 72% with 1-3 year commitments
- Best for predictable workloads

---

## 🔄 Comparison: AWS vs GCP vs Azure

| Feature | AWS | GCP | Azure |
|---------|-----|-----|-------|
| **Free Credit** | $0 (but 12mo free tier) | $300 (90 days) | $200 (30 days) |
| **Always Free** | Yes (limited services) | Yes (limited) | Yes (25+ services) |
| **VM Free Tier** | 750 hrs t2.micro | 1 f1-micro | 750 hrs B1s |
| **Storage Free** | 5 GB S3 | 5 GB Standard | 5 GB LRS |
| **CLI Tool** | aws | gcloud | az |
| **Python SDK** | boto3 | google-cloud | azure-mgmt |
| **IAM** | IAM Users | Service Accounts | Service Principals |

---

**Status:** 📝 Ready for Phase 3 Azure integration

**Estimated Setup Time:** 30-45 minutes  
**Total Cost:** $0 (with free credit)
