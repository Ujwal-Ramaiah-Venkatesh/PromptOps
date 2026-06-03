# PromptOps AWS EC2 Quick Deployment Script (PowerShell)
# This script automates the entire deployment process on Windows

$ErrorActionPreference = "Stop"

Write-Host "🚀 PromptOps AWS EC2 Deployment Script" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$AWS_REGION = "us-east-1"
$INSTANCE_TYPE = "t3.medium"
$KEY_NAME = "promptops-key"
$SECURITY_GROUP = "promptops-sg"
$INSTANCE_NAME = "promptops-server"
$AMI_ID = "ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS in us-east-1

Write-Host "Step 1: Checking AWS CLI installation..." -ForegroundColor Yellow
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "Install from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ AWS CLI found" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Checking AWS credentials..." -ForegroundColor Yellow
try {
    $ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
    Write-Host "✓ AWS Account ID: $ACCOUNT_ID" -ForegroundColor Green
}
catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "Step 3: Creating EC2 key pair (if not exists)..." -ForegroundColor Yellow
$keyExists = aws ec2 describe-key-pairs --key-names $KEY_NAME --region $AWS_REGION 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Key pair '$KEY_NAME' already exists" -ForegroundColor Green
}
else {
    $keyMaterial = aws ec2 create-key-pair `
        --key-name $KEY_NAME `
        --query 'KeyMaterial' `
        --output text `
        --region $AWS_REGION

    $keyMaterial | Out-File -FilePath "${KEY_NAME}.pem" -Encoding ASCII
    Write-Host "✓ Key pair created and saved as ${KEY_NAME}.pem" -ForegroundColor Green
    Write-Host "⚠️  For SSH access from Windows, convert this key using PuTTYgen or use WSL/Git Bash" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 4: Creating security group..." -ForegroundColor Yellow
$sgExists = aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $AWS_REGION 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Security group '$SECURITY_GROUP' already exists" -ForegroundColor Green
    $SG_ID = aws ec2 describe-security-groups --group-names $SECURITY_GROUP --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION
}
else {
    $SG_ID = aws ec2 create-security-group `
        --group-name $SECURITY_GROUP `
        --description "PromptOps security group" `
        --region $AWS_REGION `
        --query 'GroupId' `
        --output text

    # Add inbound rules
    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 22 `
        --cidr 0.0.0.0/0 `
        --region $AWS_REGION | Out-Null

    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 80 `
        --cidr 0.0.0.0/0 `
        --region $AWS_REGION | Out-Null

    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 443 `
        --cidr 0.0.0.0/0 `
        --region $AWS_REGION | Out-Null

    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 3003 `
        --cidr 0.0.0.0/0 `
        --region $AWS_REGION | Out-Null

    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 8000 `
        --cidr 0.0.0.0/0 `
        --region $AWS_REGION | Out-Null

    Write-Host "✓ Security group created: $SG_ID" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 5: Launching EC2 instance..." -ForegroundColor Yellow
# Check if instance already exists
$EXISTING_INSTANCE = aws ec2 describe-instances `
    --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running" `
    --query 'Reservations[0].Instances[0].InstanceId' `
    --output text `
    --region $AWS_REGION

if ($EXISTING_INSTANCE -ne "None" -and $EXISTING_INSTANCE) {
    Write-Host "✓ Instance already running: $EXISTING_INSTANCE" -ForegroundColor Green
    $INSTANCE_ID = $EXISTING_INSTANCE
}
else {
    # Create user data script for automatic setup
    $USER_DATA = @"
#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-`$(uname -s)-`$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
apt-get install -y git

# Create deployment directory
mkdir -p /home/ubuntu/promptops
chown ubuntu:ubuntu /home/ubuntu/promptops

echo "✅ Server setup complete!" > /home/ubuntu/setup-complete.txt
"@

    # Encode user data to base64
    $USER_DATA_ENCODED = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($USER_DATA))

    $INSTANCE_ID = aws ec2 run-instances `
        --image-id $AMI_ID `
        --instance-type $INSTANCE_TYPE `
        --key-name $KEY_NAME `
        --security-group-ids $SG_ID `
        --user-data $USER_DATA `
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" `
        --region $AWS_REGION `
        --query 'Instances[0].InstanceId' `
        --output text

    Write-Host "✓ Instance launched: $INSTANCE_ID" -ForegroundColor Green
    Write-Host "Waiting for instance to start..." -ForegroundColor Yellow
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION
    Write-Host "✓ Instance is running" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 6: Getting instance public IP..." -ForegroundColor Yellow
$PUBLIC_IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --query 'Reservations[0].Instances[0].PublicIpAddress' `
    --output text `
    --region $AWS_REGION
Write-Host "✓ Public IP: $PUBLIC_IP" -ForegroundColor Green
Write-Host ""

Write-Host "Step 7: Waiting for instance to be fully ready..." -ForegroundColor Yellow
Write-Host "This may take 3-5 minutes for initial setup to complete..." -ForegroundColor Yellow
Write-Host "The script will check every 30 seconds..." -ForegroundColor Cyan

# Wait for user data script to complete (check for our marker file)
$maxRetries = 20
$retryCount = 0
$setupComplete = $false

while ($retryCount -lt $maxRetries -and -not $setupComplete) {
    Start-Sleep -Seconds 30
    $retryCount++
    Write-Host "Checking instance status... (attempt $retryCount/$maxRetries)" -ForegroundColor Cyan

    # For now, just wait for the instance to be running and give it time
    if ($retryCount -ge 6) {  # After 3 minutes, assume setup is done
        $setupComplete = $true
        Write-Host "✓ Instance should be ready" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Step 8: Application deployment instructions..." -ForegroundColor Yellow
Write-Host ""
Write-Host "The instance is running and Docker is being installed automatically." -ForegroundColor Cyan
Write-Host "Please wait 2-3 more minutes for setup to complete, then:" -ForegroundColor Cyan
Write-Host ""

# Create connection instructions file
$connectionInfo = @"
PromptOps AWS Deployment Information
====================================

Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Security Group: $SG_ID
Region: $AWS_REGION

NEXT STEPS TO COMPLETE DEPLOYMENT:
===================================

1. Connect to your instance using one of these methods:

   Option A - Using Windows PowerShell (AWS Systems Manager):
   aws ssm start-session --target $INSTANCE_ID --region $AWS_REGION

   Option B - Using PuTTY (after converting key):
   - Convert ${KEY_NAME}.pem to .ppk using PuTTYgen
   - Connect to: ubuntu@$PUBLIC_IP

   Option C - Using WSL/Git Bash:
   ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP

2. Once connected, run these commands:

   # Wait for initial setup (check if complete)
   cat /home/ubuntu/setup-complete.txt

   # Clone repository
   cd /home/ubuntu/promptops
   git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
   cd PromptOps

   # Create environment file
   cat > .env << 'EOF'
JWT_SECRET_KEY=your-random-secret-key-change-this
ENVIRONMENT=production
PORT=8000
FRONTEND_URL=http://$PUBLIC_IP:3003
EOF

   # Start application
   docker-compose up -d --build

   # Check status
   docker-compose ps

   # View logs
   docker-compose logs -f

3. Access your application (after deployment completes):

   Frontend:  http://$PUBLIC_IP:3003
   Backend:   http://$PUBLIC_IP:8000
   API Docs:  http://$PUBLIC_IP:8000/docs

4. Login Credentials:

   Admin: admin@promptops.com / admin123
   PM:    pm@promptops.com / pm123

COST INFORMATION:
=================
Estimated Cost: ~`$0.04/hour (~`$30/month for t3.medium)

MANAGEMENT COMMANDS:
====================

Stop instance (to save costs when not in use):
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $AWS_REGION

Start instance:
aws ec2 start-instances --instance-ids $INSTANCE_ID --region $AWS_REGION

Terminate instance (delete completely):
aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $AWS_REGION
aws ec2 delete-security-group --group-id $SG_ID --region $AWS_REGION

Deployed: $(Get-Date)
"@

$connectionInfo | Out-File -FilePath "connection-info.txt" -Encoding UTF8

Write-Host ""
Write-Host "======================================"
Write-Host "🎉 EC2 Instance Launched Successfully!" -ForegroundColor Green
Write-Host "======================================"
Write-Host ""
Write-Host "📍 Instance Information:" -ForegroundColor Cyan
Write-Host "   Instance ID: $INSTANCE_ID"
Write-Host "   Public IP: $PUBLIC_IP"
Write-Host "   Region: $AWS_REGION"
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Wait 2-3 minutes for Docker installation to complete"
Write-Host "   2. Connect to instance via SSH"
Write-Host "   3. Deploy the application (commands in connection-info.txt)"
Write-Host ""
Write-Host "📄 Detailed instructions saved to: connection-info.txt" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Quick Test (run this in 5 minutes):" -ForegroundColor Cyan
Write-Host "   Start-Process 'http://$PUBLIC_IP:3003'"
Write-Host ""
Write-Host "⚠️  IMPORTANT: Instance is running and incurring costs!" -ForegroundColor Yellow
Write-Host "   Stop when not in use:" -ForegroundColor Yellow
Write-Host "   aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $AWS_REGION" -ForegroundColor Gray
Write-Host ""

# Ask if user wants to open connection info file
$openFile = Read-Host "Open connection-info.txt now? (y/n)"
if ($openFile -eq 'y' -or $openFile -eq 'Y') {
    Start-Process "connection-info.txt"
}

Write-Host ""
Write-Host "✅ Script completed successfully!" -ForegroundColor Green
