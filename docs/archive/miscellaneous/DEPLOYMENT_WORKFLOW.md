# PromptOps Deployment Workflow

## Overview
The PM-driven deployment workflow now requires the PM to enter deployment details before proceeding to the approval page.

## Workflow Steps

### Step 1: Click "Deploy Application"
**Location**: Home Dashboard → "Start Here" section → "Deploy Application" card

**Action**: PM clicks on the Deploy Application button

---

### Step 2: Fill Deployment Form (NEW!)
A modal form appears with the following fields:

#### Required Fields:
1. **Deployment Command** *
   - What to deploy and where
   - Must include the word "deploy"
   - Examples provided:
     - "Deploy my frontend to AWS production"
     - "Deploy backend service to staging"
     - "Deploy mobile app to AWS S3"

2. **GitHub Repository URL** *
   - Full GitHub repository URL
   - Format: `https://github.com/username/repository`
   - Validated to ensure correct GitHub URL format

#### Form Features:
- ✅ Real-time validation
- ✅ Example commands (click to auto-fill)
- ✅ Error messages for invalid inputs
- ✅ Clean, modern UI with gradient buttons

#### Buttons:
- **Cancel**: Close the form and return to dashboard
- **Continue to Approval**: Proceed to PM approval page (only enabled when form is valid)

---

### Step 3: PM Approval Page
After submitting the form, the system shows a comprehensive deployment review:

#### Sections Displayed:

1. **Cloud Recommendation**
   - Recommended cloud provider (AWS/GCP/Azure)
   - Confidence score (e.g., 96%)
   - Reasoning for the recommendation

2. **Provider Comparison**
   - Side-by-side comparison of AWS vs GCP vs Azure
   - Price, Security, and Fit ratings
   - Key reasons for choosing AWS

3. **Domain & Mail Service Recommendation**
   - AWS services needed (Route 53, ACM, SES, etc.)
   - Why each service is recommended

4. **Deployment Target Details**
   - Application name
   - Environment (production/staging)
   - Strategy (e.g., AWS S3 static website hosting)
   - AWS Region
   - S3 Bucket name
   - Planned public URL
   - Repository URL (from form)
   - Source path

5. **Execution Plan**
   - Step-by-step deployment process
   - 6-8 steps showing exactly what will happen

6. **AWS Credentials**
   - Choose between configured credentials or manual entry
   - Option to provide AWS Access Key, Secret Key, Session Token

7. **Security Review Checklist**
   - ☐ "I reviewed target AWS account, region, and public access implications"
   - ☐ "I approve this deployment as PM"

#### Action Buttons:
- **Cancel**: Abort the deployment
- **Approve & Execute**: Start the deployment (only enabled when both checkboxes are checked)

---

### Step 4: Deployment Execution
After PM approval:

1. **Progress Display**
   - Real-time progress bar
   - Current step indicator (e.g., "Step 5 of 8")
   - Status messages

2. **Live Logs**
   - Terminal-style log viewer
   - Timestamped entries
   - Color-coded output

3. **Completion**
   - Success/failure status
   - Public URL (if successful)
   - Deployment details

---

## Validation Rules

### Deployment Command:
- ✅ Cannot be empty
- ✅ Must contain the word "deploy"
- ✅ Free-form text (can describe any deployment)

### GitHub Repository URL:
- ✅ Cannot be empty
- ✅ Must be a valid GitHub URL
- ✅ Format: `https://github.com/username/repository`
- ✅ Can include optional trailing slash

---

## Example Flow

### Scenario: Deploying a Frontend Application

1. **PM clicks "Deploy Application"**

2. **PM fills the form:**
   - Command: "Deploy my frontend to AWS production"
   - Repo URL: "https://github.com/mycompany/frontend-app"
   - Clicks "Continue to Approval"

3. **Review page shows:**
   - Recommendation: AWS (96% confidence)
   - Target: frontend-app
   - Environment: production
   - Region: us-east-1
   - Bucket: frontend-app-promptops-123456
   - URL: http://frontend-app-promptops-123456.s3-website-us-east-1.amazonaws.com

4. **PM reviews and approves:**
   - ✅ Checks security review
   - ✅ Checks PM approval
   - Clicks "Approve & Execute"

5. **Deployment runs:**
   - Step 1: Pre-flight validation ✓
   - Step 2: PM approval validated ✓
   - Step 3: Deployment plan prepared ✓
   - Step 4: AWS access checked ✓
   - Step 5: Executing deployment ✓
   - Step 6: Verifying upload ✓
   - Step 7: Smoke checks ✓
   - Step 8: Finalized ✓

6. **Success!**
   - Public URL displayed
   - Deployment marked complete

---

## User Experience Improvements

### Before (Old Flow):
❌ Click "Deploy" → Blank page or auto-deploy with no input

### After (New Flow):
✅ Click "Deploy" → Form appears → Enter details → Review page → PM approval → Execution

### Key Benefits:
1. **PM Control**: PM explicitly enters what to deploy and from where
2. **Validation**: Ensures correct GitHub URL format
3. **Transparency**: Full visibility into what will be deployed
4. **Approval Gate**: Nothing deploys without PM approval
5. **Audit Trail**: All deployment details captured

---

## Technical Implementation

### New Component:
- **File**: `frontend/dashboard/src/components/DeploymentForm.tsx`
- **Type**: Modal form component
- **Features**:
  - React functional component
  - State management with hooks
  - Real-time validation
  - Inline error messages
  - Example command suggestions

### Updated Components:
- **PremiumHomeDashboard.tsx**: Added `onDeployClick` prop
- **App.tsx**: 
  - Added `showDeploymentForm` state
  - Added `handleDeploymentFormSubmit` handler
  - Added `handleDeploymentFormCancel` handler
  - Integrated DeploymentForm modal

---

## Testing Checklist

### Form Validation:
- [ ] Empty command shows error
- [ ] Command without "deploy" shows error
- [ ] Empty GitHub URL shows error
- [ ] Invalid GitHub URL shows error (e.g., "https://google.com")
- [ ] Valid inputs enable "Continue to Approval" button

### Form UX:
- [ ] Click example command auto-fills field
- [ ] Cancel button closes form
- [ ] Form appears as modal overlay
- [ ] Form is responsive on different screen sizes

### Workflow:
- [ ] "Deploy Application" button opens form
- [ ] Submitting form closes modal and shows approval page
- [ ] Approval page displays entered command and repo URL
- [ ] PM can approve and execute deployment
- [ ] Deployment progress shows live updates

---

## Future Enhancements

### Potential Additions:
1. **Branch Selection**: Allow PM to specify Git branch
2. **Environment Selection**: Dropdown for prod/staging/dev
3. **Region Selection**: Choose AWS region from dropdown
4. **Recent Deployments**: Show history of past deployments
5. **Template Commands**: Save frequently used deployment commands
6. **Multi-Repo Support**: Deploy multiple repos at once
7. **Rollback Option**: Quick rollback to previous version

---

## Summary

The new deployment workflow ensures that:
- ✅ PM enters deployment details explicitly
- ✅ GitHub repository URL is validated
- ✅ Full transparency in deployment plan
- ✅ PM approval required before execution
- ✅ Clear audit trail of all deployments

**No automatic deployments happen without PM input and approval!**

---

**Last Updated**: June 3, 2026  
**Version**: 2.0.0
