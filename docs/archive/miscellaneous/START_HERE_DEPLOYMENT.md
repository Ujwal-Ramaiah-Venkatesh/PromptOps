# 🎯 START HERE: Deploy PromptOps to AWS

## ⚡ Quick Decision Tree

```
Do you have 10 minutes to deploy PromptOps?
│
├─ YES → Go to "FASTEST PATH" below ✅
│
└─ NO → Bookmark this page and come back when ready
```

---

## 🚀 FASTEST PATH (10 Minutes Total)

### Step 1: Open PowerShell (1 minute)
```powershell
# Right-click Windows Start menu
# Click "Windows PowerShell (Admin)"
```

### Step 2: Check AWS Setup (2 minutes)
```powershell
# Test AWS CLI
aws --version

# If not found, install:
# Download: https://awscli.amazonaws.com/AWSCLIV2.msi
# Then run: aws configure
```

### Step 3: Run Deployment (2 minutes)
```powershell
cd C:\Users\pqm847\Documents\PromptOps
.\deploy-to-aws-ec2.ps1
```

### Step 4: Wait for Instance (3 minutes)
**The script will:**
- Create EC2 instance
- Configure security
- Install Docker
- Give you the public IP

### Step 5: Deploy Application (2 minutes)
**Follow instructions in `connection-info.txt` that the script creates**

```bash
# Commands will look like this:
ssh -i promptops-key.pem ubuntu@YOUR-IP
cd /home/ubuntu/promptops
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps
docker-compose up -d --build
```

### Step 6: Access Application (Immediate)
**Open in browser:**
```
http://YOUR-PUBLIC-IP:3003
```

**Login with:**
```
Email: admin@promptops.com
Password: admin123
```

---

## ✅ Success! What You'll See

### In Browser (http://YOUR-IP:3003)
```
┌────────────────────────────────────────┐
│  PromptOps Dashboard                   │
├────────────────────────────────────────┤
│                                        │
│  👤 Logged in as: Admin                │
│                                        │
│  📊 Tabs:                              │
│  ┌──────────────────────────────────┐ │
│  │ • Autonomy Settings              │ │
│  │ • Discovery Dashboard            │ │
│  │ • Infrastructure Ingestion       │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ✅ All systems operational           │
│                                        │
└────────────────────────────────────────┘
```

---

## 📊 What Gets Created

```
AWS Account
    │
    ├─ EC2 Instance
    │   ├─ Type: t3.medium
    │   ├─ OS: Ubuntu 22.04
    │   ├─ RAM: 4GB
    │   ├─ CPU: 2 vCPU
    │   └─ Storage: 30GB
    │
    ├─ Security Group
    │   ├─ Port 22 (SSH)
    │   ├─ Port 80 (HTTP)
    │   ├─ Port 443 (HTTPS)
    │   ├─ Port 3003 (Frontend)
    │   └─ Port 8000 (Backend)
    │
    └─ Key Pair
        └─ promptops-key.pem
```

---

## 💰 Cost Information

### Running Costs
```
┌────────────────────────────┬──────────────┐
│ Per Hour                   │ $0.04        │
│ Per Day (24 hours)         │ $0.96        │
│ Per Week                   │ $6.72        │
│ Per Month                  │ $30.37       │
└────────────────────────────┴──────────────┘
```

### How to Save Money
```
✅ Stop instance when not testing:    Save $30/month
✅ Use AWS Free Tier:                 750 hours FREE
✅ Use t3.small instead:              Save 50%
```

**Stop Command:**
```powershell
aws ec2 stop-instances --instance-ids i-YOUR-ID
# Cost while stopped: $3/month (storage only)
```

---

## 🎯 Testing Checklist

After deployment, test these:

```
□ Can access http://YOUR-IP:3003
□ Login page loads
□ Can login with admin@promptops.com
□ Dashboard shows 3 tabs
□ Autonomy Settings page works
□ Discovery Dashboard loads
□ Ingestion workflow accessible
□ API docs at http://YOUR-IP:8000/docs
□ Health check: http://YOUR-IP:8000/health
```

---

## 🔧 Common Issues & Fixes

### Issue 1: "AWS CLI not found"
```powershell
# Download and install:
https://awscli.amazonaws.com/AWSCLIV2.msi

# After install, configure:
aws configure
```

### Issue 2: "AWS credentials not configured"
```
1. Go to: https://console.aws.amazon.com/iam/
2. Click: Users → Your User → Security Credentials
3. Click: Create Access Key → CLI
4. Run: aws configure
5. Enter: Access Key ID and Secret
```

### Issue 3: "Can't access http://YOUR-IP:3003"
```bash
# SSH to instance
ssh -i promptops-key.pem ubuntu@YOUR-IP

# Check containers
docker-compose ps

# If not running, start them
cd PromptOps
docker-compose up -d

# View logs
docker-compose logs -f
```

### Issue 4: "Script execution blocked"
```powershell
# Run as Admin:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then retry:
.\deploy-to-aws-ec2.ps1
```

---

## 📱 Quick Access Card

**Print or save this for reference:**

```
╔═══════════════════════════════════════════╗
║   PromptOps AWS Deployment Quick Card    ║
╠═══════════════════════════════════════════╣
║                                           ║
║  DEPLOY:                                  ║
║  .\deploy-to-aws-ec2.ps1                  ║
║                                           ║
║  FRONTEND:                                ║
║  http://YOUR-IP:3003                      ║
║                                           ║
║  BACKEND:                                 ║
║  http://YOUR-IP:8000                      ║
║                                           ║
║  LOGIN:                                   ║
║  admin@promptops.com / admin123           ║
║                                           ║
║  STOP (save money):                       ║
║  aws ec2 stop-instances --instance-ids ID ║
║                                           ║
║  SSH:                                     ║
║  ssh -i promptops-key.pem ubuntu@IP       ║
║                                           ║
║  LOGS:                                    ║
║  docker-compose logs -f                   ║
║                                           ║
╚═══════════════════════════════════════════╝
```

---

## 📚 Complete Documentation

If you need more details:

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **THIS FILE** | Quick start, get running fast | 5 min |
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | Complete overview | 10 min |
| [QUICK_AWS_DEPLOY.md](QUICK_AWS_DEPLOY.md) | Step-by-step guide | 15 min |
| [AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md) | Full reference | 30 min |

---

## 🎬 Visual Deployment Flow

```
START
  │
  ├─ Prerequisites Setup
  │   ├─ AWS Account ✅
  │   ├─ AWS CLI Installed ✅
  │   └─ AWS Configured ✅
  │
  ├─ Run PowerShell Script
  │   ├─ Creates EC2 Instance
  │   ├─ Configures Security
  │   └─ Installs Docker
  │
  ├─ Deploy Application
  │   ├─ Clone Repository
  │   ├─ Build Containers
  │   └─ Start Services
  │
  └─ ACCESS APPLICATION ✅
      ├─ Frontend: http://IP:3003
      ├─ Backend: http://IP:8000
      └─ Login: admin@promptops.com
```

---

## ⏱️ Time Breakdown

```
┌─────────────────────────┬──────────┐
│ Activity                │ Time     │
├─────────────────────────┼──────────┤
│ AWS Setup (one-time)    │ 5 min    │
│ Run deployment script   │ 2 min    │
│ Wait for instance       │ 3 min    │
│ Deploy application      │ 3 min    │
│ Access and verify       │ 2 min    │
├─────────────────────────┼──────────┤
│ TOTAL                   │ 15 min   │
└─────────────────────────┴──────────┘
```

---

## 🎯 Decision Matrix

**Choose your deployment method:**

```
Need it working in 10 minutes?
└─ YES → Use deploy-to-aws-ec2.ps1 ✅

Want complete control?
└─ YES → See AWS_DEPLOYMENT_GUIDE.md

Need production-grade setup?
└─ YES → Use ECS Fargate (see guide)

Just testing frontend?
└─ YES → Use AWS Amplify (5 min)

Want to learn AWS deeply?
└─ YES → Manual EC2 setup (45 min)
```

---

## 🚦 Status Indicators

**After deployment, check these URLs:**

```
✅ Backend Health:
   http://YOUR-IP:8000/health
   Should return: {"status":"healthy"}

✅ Frontend Status:
   http://YOUR-IP:3003
   Should show: Login page

✅ API Documentation:
   http://YOUR-IP:8000/docs
   Should show: Swagger UI

✅ Docker Status:
   SSH: docker-compose ps
   Should show: 2 containers Up
```

---

## 💡 Pro Tips

### Tip 1: Use Elastic IP
```powershell
# Keeps same IP after stop/start
aws ec2 allocate-address
aws ec2 associate-address --instance-id i-YOUR-ID --allocation-id eipalloc-ID
```

### Tip 2: Auto-start on Reboot
```bash
# SSH to instance
ssh -i promptops-key.pem ubuntu@YOUR-IP

# Setup auto-start
cd PromptOps
docker-compose up -d --restart always
```

### Tip 3: Monitor Costs
```
1. Go to: https://console.aws.amazon.com/billing/
2. Create budget alert
3. Set limit: $50/month
4. Get email alerts
```

### Tip 4: Backup Before Changes
```powershell
# Create snapshot
aws ec2 create-snapshot \
  --volume-id vol-YOUR-ID \
  --description "PromptOps Backup"
```

---

## 🎊 You're Ready!

**Everything you need is prepared:**

✅ 4 deployment guides created  
✅ Automated PowerShell script ready  
✅ Step-by-step instructions provided  
✅ Troubleshooting guide included  
✅ Cost estimates calculated  
✅ Security configured  
✅ Monitoring setup documented  

**Just run:**

```powershell
cd C:\Users\pqm847\Documents\PromptOps
.\deploy-to-aws-ec2.ps1
```

**And in 10 minutes, PromptOps will be live on AWS!** 🚀

---

## 📞 Need Help?

### During Deployment
1. Check `connection-info.txt` (created by script)
2. Read troubleshooting section above
3. Check AWS Console for instance status
4. Review CloudWatch logs

### After Deployment
1. SSH to instance: `ssh -i promptops-key.pem ubuntu@YOUR-IP`
2. Check logs: `docker-compose logs -f`
3. Verify health: `curl http://localhost:8000/health`
4. Test frontend: Open browser to `http://YOUR-IP:3003`

---

## 🎯 Next Actions

**Now (10 minutes):**
- [ ] Run deployment script
- [ ] Verify application is accessible
- [ ] Login and explore features
- [ ] Test all dashboard tabs

**Later Today:**
- [ ] Setup monitoring alerts
- [ ] Document your instance ID
- [ ] Test stopping/starting instance
- [ ] Review AWS costs

**This Week:**
- [ ] Configure custom domain (optional)
- [ ] Setup SSL certificate (optional)
- [ ] Implement automated backups
- [ ] Review security settings

---

## 🔖 Bookmark These URLs

After deployment, bookmark:

```
AWS Console:
https://console.aws.amazon.com/ec2/

Your Application:
http://YOUR-PUBLIC-IP:3003

API Documentation:
http://YOUR-PUBLIC-IP:8000/docs

GitHub Repository:
https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps
```

---

**🎉 Ready to test PromptOps on AWS?**

**Open PowerShell and run:**
```powershell
cd C:\Users\pqm847\Documents\PromptOps
.\deploy-to-aws-ec2.ps1
```

**See you on the cloud! ☁️** ✨
