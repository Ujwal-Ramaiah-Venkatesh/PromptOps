<div align="center">
  <img src="assets/promptops-logo.png" alt="PromptOps Logo" width="200"/>
  
  # PromptOps Deployment Guide
  
  **Version:** 1.0.0-rc1  
  **Date:** 2026-04-30
</div>

---

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Start All Services
```bash
# Clone repository
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Access:**
- Frontend: http://localhost:3003
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📦 Deployment Options

### Option 1: Docker Compose (Recommended)

**Production deployment:**
```bash
# Set environment variables
export JWT_SECRET_KEY="your-production-secret-key"

# Build and start
docker-compose up -d --build

# Scale services
docker-compose up -d --scale backend=3

# Stop services
docker-compose down
```

**Update deployment:**
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Clean up old images
docker image prune -f
```

---

### Option 2: Manual Deployment

**Backend:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend
python api_gateway/start_with_mock_db.py

# Or with gunicorn (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    api_gateway.start_with_mock_db:app
```

**Frontend:**
```bash
cd frontend/dashboard

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or any static server
npx serve -s dist -p 3003
```

---

### Option 3: Kubernetes

**Deploy to Kubernetes:**
```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n promptops

# View logs
kubectl logs -f deployment/promptops-backend -n promptops

# Scale
kubectl scale deployment promptops-backend --replicas=5 -n promptops
```

---

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```bash
# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3003,https://your-domain.com

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/promptops

# AWS (optional for real discovery)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1

# Logging
LOG_LEVEL=INFO
```

**Frontend (.env.production):**
```bash
VITE_API_BASE_URL=https://api.your-domain.com
VITE_DRIFT_POLLING_INTERVAL=60000
VITE_AUDIT_REFRESH_INTERVAL=30000
VITE_ENABLE_AUTO_REFRESH=true
```

---

## 🌐 Production Deployment

### AWS Deployment

**Using ECS + Fargate:**
```bash
# Build and push images
docker build -t promptops-backend:latest -f Dockerfile.backend .
docker build -t promptops-frontend:latest -f Dockerfile.frontend .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
docker tag promptops-backend:latest $ECR_URL/promptops-backend:latest
docker push $ECR_URL/promptops-backend:latest

# Deploy to ECS
aws ecs update-service --cluster promptops --service backend --force-new-deployment
```

**Using EC2:**
```bash
# SSH to instance
ssh -i your-key.pem ec2-user@your-instance

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start

# Clone and run
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps
docker-compose up -d
```

---

### Google Cloud Platform

**Using Cloud Run:**
```bash
# Build and submit
gcloud builds submit --tag gcr.io/PROJECT_ID/promptops-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/promptops-frontend

# Deploy
gcloud run deploy promptops-backend \
    --image gcr.io/PROJECT_ID/promptops-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated

gcloud run deploy promptops-frontend \
    --image gcr.io/PROJECT_ID/promptops-frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

---

### Azure

**Using App Service:**
```bash
# Create resource group
az group create --name promptops-rg --location eastus

# Create App Service plan
az appservice plan create --name promptops-plan --resource-group promptops-rg --sku B1 --is-linux

# Deploy backend
az webapp create --resource-group promptops-rg --plan promptops-plan --name promptops-backend --deployment-container-image-name promptops-backend:latest

# Deploy frontend
az webapp create --resource-group promptops-rg --plan promptops-plan --name promptops-frontend --deployment-container-image-name promptops-frontend:latest
```

---

## 🔒 Security Checklist

**Before Production:**
- [ ] Change default JWT_SECRET_KEY
- [ ] Update default passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Configure CORS properly
- [ ] Set up monitoring/alerts
- [ ] Enable backup strategy
- [ ] Review IAM permissions
- [ ] Scan for vulnerabilities
- [ ] Enable audit logging

---

## 📊 Monitoring

### Health Checks

**Backend:**
```bash
curl http://localhost:8000/health
```

**Frontend:**
```bash
curl http://localhost:3003/
```

### Logs

**Docker Compose:**
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

**Kubernetes:**
```bash
kubectl logs -f deployment/promptops-backend -n promptops
```

---

## 🔄 CI/CD

### GitHub Actions (Configured)

**Workflows:**
- `backend-tests.yml` - Run backend tests on push
- `frontend-tests.yml` - Run frontend tests on push
- `full-test-suite.yml` - Complete test suite (daily)
- `lint.yml` - Code quality checks

**Trigger:**
- Push to main/develop
- Pull requests
- Manual trigger
- Daily schedule

**Status badges:**
```markdown
![Backend Tests](https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps/actions/workflows/backend-tests.yml/badge.svg)
![Frontend Tests](https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps/actions/workflows/frontend-tests.yml/badge.svg)
```

---

## 🔧 Troubleshooting

### Backend Issues

**Container won't start:**
```bash
# Check logs
docker logs promptops-backend

# Check port conflicts
netstat -an | grep 8000

# Rebuild image
docker-compose build --no-cache backend
docker-compose up -d backend
```

**Database connection errors:**
```bash
# Use mock database (default)
# No action needed - mock DB is in-memory

# Or connect to PostgreSQL
export DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Frontend Issues

**Build failures:**
```bash
cd frontend/dashboard

# Clean install
rm -rf node_modules package-lock.json
npm install

# Build
npm run build
```

**API connection errors:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings
# Ensure backend CORS_ORIGINS includes frontend URL
```

---

## 📈 Performance Tuning

### Backend

**Gunicorn workers:**
```bash
# Formula: (2 x CPU cores) + 1
gunicorn -w 9 -k uvicorn.workers.UvicornWorker api_gateway.start_with_mock_db:app
```

**Database connection pooling:**
```python
# In production, use connection pooling
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
```

### Frontend

**Nginx optimization:**
```nginx
# Enable caching
proxy_cache_valid 200 1h;
proxy_cache_use_stale error timeout updating;

# Enable compression
gzip_comp_level 6;
```

---

## 🔄 Updates

### Rolling Updates

**Zero-downtime deployment:**
```bash
# Docker Compose
docker-compose up -d --no-deps --build backend

# Kubernetes
kubectl set image deployment/promptops-backend backend=promptops-backend:v2
kubectl rollout status deployment/promptops-backend
```

### Rollback

**If issues occur:**
```bash
# Docker Compose
docker-compose down
git checkout <previous-commit>
docker-compose up -d --build

# Kubernetes
kubectl rollout undo deployment/promptops-backend
```

---

## 📦 Backup & Recovery

### Backup

**Database (if using PostgreSQL):**
```bash
# Backup
pg_dump -U postgres promptops > backup_$(date +%Y%m%d).sql

# Automated backups
0 2 * * * pg_dump -U postgres promptops > /backups/promptops_$(date +\%Y\%m\%d).sql
```

**Configuration:**
```bash
# Backup env files
tar -czf config_backup.tar.gz .env* *.yml
```

### Restore

```bash
# Restore database
psql -U postgres promptops < backup_20260430.sql

# Restore configuration
tar -xzf config_backup.tar.gz
```

---

## 🎯 Production Checklist

**Infrastructure:**
- [ ] DNS configured
- [ ] SSL certificates installed
- [ ] Load balancer configured
- [ ] CDN enabled (optional)
- [ ] Backup strategy implemented

**Security:**
- [ ] Firewall rules configured
- [ ] Security groups set up
- [ ] Secrets management configured
- [ ] WAF enabled (optional)

**Monitoring:**
- [ ] Health checks configured
- [ ] Logging centralized
- [ ] Alerts set up
- [ ] Metrics dashboard created

**Testing:**
- [ ] Smoke tests passed
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Penetration testing done (optional)

---

## 📞 Support

**Issues:**
- GitHub: https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps/issues
- Email: support@promptops.com (if available)

**Documentation:**
- [QUICK_START.md](QUICK_START.md)
- [READY_TO_SHIP.md](READY_TO_SHIP.md)
- [FINAL_STATUS.md](FINAL_STATUS.md)

---

**Deployment Status:** ✅ Ready for Production  
**Docker Support:** ✅ Full  
**CI/CD:** ✅ GitHub Actions Configured  
**Monitoring:** ✅ Health Checks Enabled
