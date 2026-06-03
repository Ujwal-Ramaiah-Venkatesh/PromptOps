# 🚀 Quick AWS Deployment - PromptOps

## ONE-COMMAND DEPLOYMENT (Windows)

### Prerequisites (5 minutes):
1. **AWS Account** - https://aws.amazon.com/free/
2. **AWS CLI** - Download: https://awscli.amazonaws.com/AWSCLIV2.msi
3. **Configure AWS**:
   ```powershell
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Region: us-east-1
   # Output: json
   ```

---

## 🎯 DEPLOY NOW (Choose One Method)

### Method 1: PowerShell Script (EASIEST - Recommended)

```powershell
# Navigate to project directory
cd C:\Users\pqm847\Documents\PromptOps

# Run deployment script
.\deploy-to-aws-ec2.ps1
```

**This script will:**
- ✅ Create EC2 instance (t3.medium)
- ✅ Configure security groups
- ✅ Install Docker automatically
- ✅ Give you the public IP
- ✅ Takes ~5 minutes

**After script completes:**
1. Wait 2-3 more minutes for Docker installation
2. SSH to instance and deploy app (commands provided)
3. Access at http://YOUR-IP:3003

---

### Method 2: Manual AWS Console (20 minutes)

#### Step 1: Launch EC2 Instance
1. Go to https://console.aws.amazon.com/ec2/
2. Click "Launch Instance"
3. Choose:
   - Name: `promptops-server`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.medium
   - Create new key pair: `promptops-key` (download .pem file)
   - Allow HTTP, HTTPS, SSH, Custom TCP 3003, 8000
4. Click "Launch Instance"

#### Step 2: Connect to Instance
```powershell
# Wait 2 minutes, then get public IP from EC2 console

# Option A: Use AWS Systems Manager (no SSH needed)
aws ssm start-session --target i-YOUR-INSTANCE-ID

# Option B: Use Git Bash/WSL
ssh -i promptops-key.pem ubuntu@YOUR-PUBLIC-IP
```

#### Step 3: Install Docker and Deploy
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=production
PORT=8000
EOF

# Deploy
docker-compose up -d --build

# Check status
docker-compose ps
```

#### Step 4: Access Application
- Frontend: http://YOUR-PUBLIC-IP:3003
- Backend API: http://YOUR-PUBLIC-IP:8000
- API Docs: http://YOUR-PUBLIC-IP:8000/docs

**Login:**
- Admin: admin@promptops.com / admin123

---

### Method 3: AWS CloudShell (Browser-Based, No Install)

1. Go to https://console.aws.amazon.com/cloudshell/
2. Click "CloudShell" icon (top right)
3. Run these commands:

```bash
# Clone deployment repo
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps

# Make script executable
chmod +x deploy-to-aws-ec2.sh

# Run deployment
./deploy-to-aws-ec2.sh
```

---

## 📊 Cost Estimate

| Resource | Cost/Hour | Cost/Month | Notes |
|----------|-----------|------------|-------|
| t3.medium EC2 | $0.042 | ~$30 | 2 vCPU, 4GB RAM |
| Data Transfer | ~$0.09/GB | ~$5-10 | First 100GB/month free |
| **TOTAL** | **~$0.05/hr** | **~$35-40** | Stop when not in use! |

**💡 Cost Saving Tips:**
- Stop instance when not in use: **$0/hour**
- Use t3.small instead: **Save 50%** (may be slower)
- Use AWS Free Tier: **750 hours/month free** (first 12 months)

---

## ⚡ Super Quick Test (After Deployment)

```powershell
# Check if application is running (replace with your IP)
curl http://YOUR-PUBLIC-IP:8000/health

# Expected response: {"status":"healthy"}

# Open in browser
Start-Process "http://YOUR-PUBLIC-IP:3003"
```

---

## 🔧 Troubleshooting

### Issue: Can't access http://YOUR-IP:3003
**Solution:**
```bash
# SSH to instance
ssh -i promptops-key.pem ubuntu@YOUR-PUBLIC-IP

# Check if Docker is running
docker ps

# If containers not running
cd PromptOps
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Issue: AWS CLI not configured
**Solution:**
```powershell
# Create AWS access keys
# 1. Go to: https://console.aws.amazon.com/iam/
# 2. Users → Your User → Security Credentials
# 3. Create Access Key → CLI
# 4. Download credentials

# Configure
aws configure
```

### Issue: SSH connection refused
**Solution:**
- Wait 2-3 minutes after instance launch
- Check security group allows port 22
- Verify you're using correct .pem file
- Try AWS Systems Manager instead: `aws ssm start-session --target INSTANCE-ID`

---

## 🎯 Deployment Status Checklist

After running deployment, verify:

- [ ] EC2 instance is running
- [ ] Security group allows ports 22, 80, 443, 3003, 8000
- [ ] Docker is installed (`docker --version`)
- [ ] Docker Compose is installed (`docker-compose --version`)
- [ ] Application containers are running (`docker-compose ps`)
- [ ] Backend responds to health check (`curl http://localhost:8000/health`)
- [ ] Frontend is accessible in browser
- [ ] Can login with test credentials

---

## 📱 Access URLs (After Deployment)

Replace `YOUR-PUBLIC-IP` with your instance's public IP from AWS console or script output:

```
🌐 Frontend:     http://YOUR-PUBLIC-IP:3003
🔧 Backend API:  http://YOUR-PUBLIC-IP:8000
📚 API Docs:     http://YOUR-PUBLIC-IP:8000/docs
📊 Health Check: http://YOUR-PUBLIC-IP:8000/health
```

**Test Credentials:**
```
Admin:  admin@promptops.com / admin123
PM:     pm@promptops.com / pm123
```

---

## 🛑 Stop/Start/Delete Instance

### Stop (saves cost, preserves data)
```powershell
aws ec2 stop-instances --instance-ids i-YOUR-INSTANCE-ID
```

### Start (resume after stop)
```powershell
aws ec2 start-instances --instance-ids i-YOUR-INSTANCE-ID
# Get new public IP (changes after stop/start)
aws ec2 describe-instances --instance-ids i-YOUR-INSTANCE-ID --query 'Reservations[0].Instances[0].PublicIpAddress'
```

### Delete (removes everything)
```powershell
aws ec2 terminate-instances --instance-ids i-YOUR-INSTANCE-ID
aws ec2 delete-security-group --group-name promptops-sg
aws ec2 delete-key-pair --key-name promptops-key
```

---

## 🚀 Next Steps After Deployment

1. **Test the Application**
   - Login with test credentials
   - Try creating a command
   - Explore the dashboard

2. **Configure Monitoring**
   - Setup CloudWatch alarms
   - Monitor CPU/Memory usage
   - Track API response times

3. **Setup Custom Domain** (Optional)
   - Register domain in Route 53
   - Create A record pointing to EC2 IP
   - Setup SSL certificate

4. **Production Hardening**
   - Change JWT_SECRET_KEY to random value
   - Restrict SSH access to your IP only
   - Enable automated backups
   - Setup database (RDS PostgreSQL)
   - Configure Redis for sessions

---

## 📞 Getting Help

### Check Instance Status
```powershell
aws ec2 describe-instance-status --instance-ids i-YOUR-INSTANCE-ID
```

### View System Logs
```bash
# SSH to instance
ssh -i promptops-key.pem ubuntu@YOUR-PUBLIC-IP

# View application logs
cd PromptOps
docker-compose logs -f

# View system logs
sudo journalctl -u docker -f
```

### CloudWatch Logs
1. Go to https://console.aws.amazon.com/cloudwatch/
2. Logs → Log groups
3. Find `/aws/ec2/promptops-server`

---

## 🎉 Success Indicators

Your deployment is successful when:

✅ EC2 instance shows "running" status  
✅ `docker-compose ps` shows all containers "Up"  
✅ http://YOUR-IP:8000/health returns `{"status":"healthy"}`  
✅ http://YOUR-IP:3003 loads the frontend  
✅ You can login with admin@promptops.com / admin123  
✅ Dashboard shows autonomy settings, discovery, and ingestion tabs  

---

## 📈 Performance Benchmarks

Expected performance on t3.medium:

| Metric | Value |
|--------|-------|
| Backend Response Time | 100-300ms |
| Frontend Load Time | 1-2 seconds |
| API Throughput | 100+ req/s |
| Concurrent Users | 50-100 |
| Memory Usage | 1-2GB |
| CPU Usage | 10-30% idle |

---

## 💡 Pro Tips

1. **Use Elastic IP** to keep same IP after stop/start
   ```powershell
   aws ec2 allocate-address
   aws ec2 associate-address --instance-id i-YOUR-ID --allocation-id eipalloc-YOUR-EIP
   ```

2. **Setup Automated Backups** with EBS snapshots
   ```powershell
   aws ec2 create-snapshot --volume-id vol-YOUR-VOLUME-ID --description "PromptOps Backup"
   ```

3. **Monitor Costs** with AWS Budgets
   - Go to AWS Budgets console
   - Create alert when cost > $50/month

4. **Use Parameter Store** for secrets
   ```powershell
   aws ssm put-parameter --name "/promptops/jwt-secret" --value "your-secret" --type SecureString
   ```

---

## 🎯 Quick Commands Reference

```powershell
# Get instance public IP
aws ec2 describe-instances --filters "Name=tag:Name,Values=promptops-server" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

# Get instance ID
aws ec2 describe-instances --filters "Name=tag:Name,Values=promptops-server" --query 'Reservations[0].Instances[0].InstanceId' --output text

# Get instance state
aws ec2 describe-instances --instance-ids i-YOUR-ID --query 'Reservations[0].Instances[0].State.Name' --output text

# SSH to instance
ssh -i promptops-key.pem ubuntu@$(aws ec2 describe-instances --filters "Name=tag:Name,Values=promptops-server" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# View CloudWatch logs
aws logs tail /aws/ec2/promptops-server --follow

# Create AMI backup
aws ec2 create-image --instance-id i-YOUR-ID --name "PromptOps-Backup-$(date +%Y%m%d)"
```

---

**🎊 Ready to deploy? Run the PowerShell script now!**

```powershell
cd C:\Users\pqm847\Documents\PromptOps
.\deploy-to-aws-ec2.ps1
```

**Time to live application: ~10 minutes**  
**Monthly cost: ~$35-40** (stop when not in use to save)  
**Result: Production-ready PromptOps running on AWS** ✅
