#!/bin/bash

# PromptOps AWS EC2 Quick Deployment Script
# This script automates the entire deployment process

set -e  # Exit on error

echo "🚀 PromptOps AWS EC2 Deployment Script"
echo "======================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="us-east-1"
INSTANCE_TYPE="t3.medium"
KEY_NAME="promptops-key"
SECURITY_GROUP="promptops-sg"
INSTANCE_NAME="promptops-server"
AMI_ID="ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS in us-east-1

echo -e "${YELLOW}Step 1: Checking AWS CLI installation...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Please install it first.${NC}"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"
echo ""

echo -e "${YELLOW}Step 2: Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account ID: $ACCOUNT_ID${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating EC2 key pair (if not exists)...${NC}"
if aws ec2 describe-key-pairs --key-names $KEY_NAME --region $AWS_REGION &> /dev/null; then
    echo -e "${GREEN}✓ Key pair '$KEY_NAME' already exists${NC}"
else
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text \
        --region $AWS_REGION > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    echo -e "${GREEN}✓ Key pair created and saved as ${KEY_NAME}.pem${NC}"
fi
echo ""

echo -e "${YELLOW}Step 4: Creating security group...${NC}"
if aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $AWS_REGION &> /dev/null; then
    echo -e "${GREEN}✓ Security group '$SECURITY_GROUP' already exists${NC}"
    SG_ID=$(aws ec2 describe-security-groups --group-names $SECURITY_GROUP --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)
else
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP \
        --description "PromptOps security group" \
        --region $AWS_REGION \
        --query 'GroupId' \
        --output text)

    # Add inbound rules
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION

    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION

    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION

    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 3003 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION

    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION

    echo -e "${GREEN}✓ Security group created: $SG_ID${NC}"
fi
echo ""

echo -e "${YELLOW}Step 5: Launching EC2 instance...${NC}"
# Check if instance already exists
EXISTING_INSTANCE=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text \
    --region $AWS_REGION)

if [ "$EXISTING_INSTANCE" != "None" ] && [ -n "$EXISTING_INSTANCE" ]; then
    echo -e "${GREEN}✓ Instance already running: $EXISTING_INSTANCE${NC}"
    INSTANCE_ID=$EXISTING_INSTANCE
else
    # Create user data script for automatic setup
    USER_DATA=$(cat <<'EOF'
#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
apt-get install -y git

# Create deployment directory
mkdir -p /home/ubuntu/promptops
chown ubuntu:ubuntu /home/ubuntu/promptops

echo "✅ Server setup complete!" > /home/ubuntu/setup-complete.txt
EOF
)

    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id $AMI_ID \
        --instance-type $INSTANCE_TYPE \
        --key-name $KEY_NAME \
        --security-group-ids $SG_ID \
        --user-data "$USER_DATA" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
        --region $AWS_REGION \
        --query 'Instances[0].InstanceId' \
        --output text)

    echo -e "${GREEN}✓ Instance launched: $INSTANCE_ID${NC}"
    echo -e "${YELLOW}Waiting for instance to start...${NC}"
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION
    echo -e "${GREEN}✓ Instance is running${NC}"
fi
echo ""

echo -e "${YELLOW}Step 6: Getting instance public IP...${NC}"
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region $AWS_REGION)
echo -e "${GREEN}✓ Public IP: $PUBLIC_IP${NC}"
echo ""

echo -e "${YELLOW}Step 7: Waiting for instance to be fully ready (SSH)...${NC}"
echo "This may take 2-3 minutes..."
RETRY_COUNT=0
MAX_RETRIES=30
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP "echo 'SSH Ready'" &> /dev/null; then
        echo -e "${GREEN}✓ SSH connection successful${NC}"
        break
    fi
    echo -n "."
    sleep 10
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}Failed to connect via SSH after $MAX_RETRIES attempts${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 8: Deploying PromptOps application...${NC}"

# Create deployment script
cat > /tmp/deploy-promptops.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

echo "Installing dependencies..."
# Wait for user data script to complete
while [ ! -f /home/ubuntu/setup-complete.txt ]; do
    echo "Waiting for initial setup to complete..."
    sleep 5
done

cd /home/ubuntu/promptops

# Clone or update repository
if [ -d "PromptOps" ]; then
    echo "Updating existing repository..."
    cd PromptOps
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
    cd PromptOps
fi

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
PORT=8000
FRONTEND_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3003
EOF

# Build and start containers
echo "Building and starting containers..."
docker-compose down || true
docker-compose up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check status
docker-compose ps

echo "✅ Deployment complete!"
DEPLOY_SCRIPT

# Copy and execute deployment script
scp -o StrictHostKeyChecking=no -i ${KEY_NAME}.pem /tmp/deploy-promptops.sh ubuntu@$PUBLIC_IP:/tmp/
ssh -o StrictHostKeyChecking=no -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP "chmod +x /tmp/deploy-promptops.sh && /tmp/deploy-promptops.sh"

echo -e "${GREEN}✓ Application deployed successfully${NC}"
echo ""

echo "======================================"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "📍 Your application is now running:"
echo ""
echo "🌐 Frontend:  http://$PUBLIC_IP:3003"
echo "🔧 Backend:   http://$PUBLIC_IP:8000"
echo "📚 API Docs:  http://$PUBLIC_IP:8000/docs"
echo ""
echo "🔑 SSH Access:"
echo "   ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo ""
echo "👤 Login Credentials:"
echo "   Admin: admin@promptops.com / admin123"
echo "   PM:    pm@promptops.com / pm123"
echo ""
echo "📊 View Logs:"
echo "   ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo "   cd /home/ubuntu/promptops/PromptOps"
echo "   docker-compose logs -f"
echo ""
echo "💰 Estimated Cost: ~$0.04/hour (~$30/month for t3.medium)"
echo ""
echo "⚠️  Don't forget to stop the instance when not in use:"
echo "   aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "🗑️  To delete everything:"
echo "   aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo "   aws ec2 delete-security-group --group-id $SG_ID --region $AWS_REGION"
echo ""

# Save connection info
cat > connection-info.txt << EOF
PromptOps AWS Deployment Information
====================================

Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Security Group: $SG_ID
Region: $AWS_REGION

Application URLs:
- Frontend: http://$PUBLIC_IP:3003
- Backend: http://$PUBLIC_IP:8000
- API Docs: http://$PUBLIC_IP:8000/docs

SSH Command:
ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP

Login Credentials:
- Admin: admin@promptops.com / admin123
- PM: pm@promptops.com / pm123

Deployed: $(date)
EOF

echo -e "${GREEN}✓ Connection info saved to connection-info.txt${NC}"
echo ""
