# PromptOps Production Deployment Guide

**Version:** 5.0.0  
**Status:** Production Ready  
**Cost:** $0/month (using free tiers)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Deployment Options](#deployment-options)
5. [Configuration](#configuration)
6. [Monitoring Setup](#monitoring-setup)
7. [Backup & Recovery](#backup--recovery)
8. [Security Hardening](#security-hardening)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## Overview

This guide covers deploying PromptOps to production using Docker containers with full monitoring, logging, and backup capabilities.

### Architecture

```
┌─────────────────────────────────────────────┐
│              Load Balancer (Nginx)           │
│                   Port 80/443                │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
    ┌────▼────┐         ┌────▼────┐
    │ Frontend│         │ Backend │
    │  :3003  │         │  :8000  │
    └────┬────┘         └────┬────┘
         │                   │
         │              ┌────▼────┐
         │              │Postgres │
         │              │  :5432  │
         │              └─────────┘
         │
    ┌────▼──────────────────────────┐
    │     Monitoring Stack          │
    │  Prometheus | Grafana | Loki  │
    └───────────────────────────────┘
```

### Features

- ✅ Zero-downtime deployments
- ✅ Automated health checks
- ✅ Full observability (metrics + logs)
- ✅ Automated backups
- ✅ SSL/TLS support
- ✅ Resource limits and scaling
- ✅ $0 monthly cost

---

## Prerequisites

### System Requirements

**Minimum:**
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space
- Docker 20.10+
- Docker Compose 2.0+

**Recommended:**
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space
- SSD storage

### Software

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/promptops.git
cd promptops
```

### 2. Configure Environment

```bash
# Copy environment template
cp docker/.env.example docker/.env

# Generate secrets
export JWT_SECRET=$(openssl rand -hex 32)
export SESSION_SECRET=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Update .env file
nano docker/.env
```

**Required changes in `.env`:**
- `JWT_SECRET_KEY` - Generated above
- `SESSION_SECRET` - Generated above
- `POSTGRES_PASSWORD` - Generated above
- `GRAFANA_PASSWORD` - Generated above
- `CORS_ORIGINS` - Your domain(s)

### 3. Start Services

```bash
# Production deployment
docker-compose -f docker/docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker/docker-compose.prod.yml ps

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f
```

### 4. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3003

# Check Grafana
curl http://localhost:3000

# Check Prometheus
curl http://localhost:9090/-/healthy
```

### 5. Access Dashboards

- **Frontend:** http://localhost:3003
- **Backend API:** http://localhost:8000/docs
- **Grafana:** http://localhost:3000 (admin / [your-password])
- **Prometheus:** http://localhost:9090

---

## Deployment Options

### Option 1: Oracle Cloud (Free Tier) ✅ Recommended

**Cost:** $0/month

**Specifications:**
- 2x VM.Standard.E2.1.Micro (1 OCPU, 1 GB RAM each)
- 200 GB Block Storage
- 10 TB outbound data transfer/month

**Setup:**
```bash
# 1. Create Oracle Cloud account
# 2. Launch compute instance (Ubuntu 22.04)
# 3. Configure security list (open ports 22, 80, 443)
# 4. SSH into instance
ssh -i ~/.ssh/oracle_key ubuntu@your-instance-ip

# 5. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 6. Deploy PromptOps
git clone https://github.com/your-org/promptops.git
cd promptops
cp docker/.env.example docker/.env
# ... configure .env ...
docker-compose -f docker/docker-compose.prod.yml up -d
```

---

### Option 2: AWS Free Tier

**Cost:** $0/month (12 months free tier)

**Specifications:**
- t2.micro (1 vCPU, 1 GB RAM)
- 30 GB EBS storage
- 750 hours/month (1 instance full-time)

**Setup:**
```bash
# 1. Launch EC2 t2.micro instance (Ubuntu 22.04)
# 2. Configure security group (ports 22, 80, 443, 8000, 3003)
# 3. SSH into instance
ssh -i ~/.ssh/aws_key.pem ubuntu@ec2-instance.compute.amazonaws.com

# 4. Follow Quick Start steps above
```

---

### Option 3: Render.com (Free Tier)

**Cost:** $0/month

**Specifications:**
- 512 MB RAM
- Shared CPU
- 100 GB bandwidth/month
- Automatic deployments from Git

**Setup:**
1. Fork repository to GitHub
2. Connect Render.com to GitHub
3. Create Web Service (Backend)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python api_gateway/start_with_mock_db.py`
4. Create Static Site (Frontend)
   - Build Command: `cd frontend/dashboard && npm install && npm run build`
   - Publish Directory: `frontend/dashboard/build`

---

## Configuration

### Environment Variables

**Critical Settings:**

```bash
# Security (MUST CHANGE)
JWT_SECRET_KEY=<generated-secret>
SESSION_SECRET=<generated-secret>
POSTGRES_PASSWORD=<strong-password>

# Application
ENVIRONMENT=production
DEBUG=false

# CORS (YOUR DOMAINS)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Database
DATABASE_URL=postgresql://promptops:PASSWORD@postgres:5432/promptops
```

### Resource Limits

Edit `docker/docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

---

## Monitoring Setup

### Prometheus

**Access:** http://localhost:9090

**Key Metrics:**
- `up{job="backend"}` - Backend health
- `http_requests_total` - API request count
- `http_request_duration_seconds` - Response time
- `process_resident_memory_bytes` - Memory usage

### Grafana

**Access:** http://localhost:3000  
**Default Credentials:** admin / [your-password]

**Pre-configured Dashboards:**
1. Application Metrics
2. Infrastructure Metrics
3. Cost Analysis
4. ML Performance

**Setup:**
1. Login to Grafana
2. Navigate to Dashboards
3. Import dashboards from `monitoring/grafana/dashboards/`

### Loki (Logs)

**Access:** Through Grafana (Explore > Loki)

**Query Examples:**
```logql
# Backend errors
{job="backend"} |= "ERROR"

# High response time
{job="backend"} | json | response_time > 1000

# Cost anomalies
{job="backend"} |= "anomaly" | json | severity="critical"
```

---

## Backup & Recovery

### Automated Backups

**Schedule:** Daily at 2 AM

```bash
# Run manual backup
./scripts/backup.sh

# Configure automated backups (cron)
crontab -e
# Add: 0 2 * * * /path/to/promptops/scripts/backup.sh >> /var/log/promptops-backup.log 2>&1
```

**Backup Contents:**
- PostgreSQL database
- Configuration files
- ML models
- Backup manifest

**Retention:** 30 days (configurable)

### Restore from Backup

```bash
# List available backups
./scripts/restore.sh --list

# Restore from latest backup
./scripts/restore.sh --latest --backup-current

# Restore from specific backup
./scripts/restore.sh /path/to/backup.sql.gz
```

### Disaster Recovery

**Recovery Time Objective (RTO):** 15 minutes  
**Recovery Point Objective (RPO):** 24 hours

**Steps:**
1. Provision new infrastructure
2. Install Docker and dependencies
3. Clone repository
4. Restore from backup
5. Verify all services
6. Update DNS (if needed)

---

## Security Hardening

### 1. SSL/TLS Certificates

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 2. Firewall Configuration

```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Block direct access to internal ports
sudo ufw deny 8000/tcp  # Backend (access via nginx)
sudo ufw deny 5432/tcp  # PostgreSQL
```

### 3. Secure Secrets

```bash
# Use Docker secrets for sensitive data
echo "your-secret-value" | docker secret create jwt_secret -

# Update docker-compose.prod.yml
services:
  backend:
    secrets:
      - jwt_secret
secrets:
  jwt_secret:
    external: true
```

### 4. Database Security

```bash
# Connect to PostgreSQL
docker exec -it promptops-postgres psql -U promptops

# Create read-only user for monitoring
CREATE USER monitoring WITH PASSWORD 'secure-password';
GRANT CONNECT ON DATABASE promptops TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;

# Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### 5. Security Headers

Add to `nginx.conf`:

```nginx
# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check container logs
docker logs promptops-backend
docker logs promptops-frontend
docker logs promptops-postgres

# Check container status
docker ps -a

# Check resource usage
docker stats

# Restart services
docker-compose -f docker/docker-compose.prod.yml restart
```

### Database Connection Issues

```bash
# Test database connection
docker exec -it promptops-postgres psql -U promptops -c "SELECT version();"

# Check database logs
docker logs promptops-postgres

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

### High Memory Usage

```bash
# Check memory usage
docker stats promptops-backend

# Reduce memory limits in docker-compose.prod.yml
# Restart containers
docker-compose -f docker/docker-compose.prod.yml up -d --force-recreate
```

### Slow API Response

```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# Review backend logs
docker logs --tail 100 promptops-backend | grep "slow"

# Check database query performance
docker exec -it promptops-postgres psql -U promptops -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

---

## Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker/docker-compose.prod.yml build

# Rolling update (zero downtime)
docker-compose -f docker/docker-compose.prod.yml up -d --no-deps --build backend
docker-compose -f docker/docker-compose.prod.yml up -d --no-deps --build frontend
```

### Update Dependencies

```bash
# Update Python packages
pip list --outdated
pip install --upgrade -r requirements.txt

# Update Node packages
cd frontend/dashboard
npm outdated
npm update

# Rebuild containers
docker-compose -f docker/docker-compose.prod.yml build --no-cache
```

### Database Migrations

```bash
# Run migrations
docker exec -it promptops-backend alembic upgrade head

# Rollback migration
docker exec -it promptops-backend alembic downgrade -1
```

### Clean Up

```bash
# Remove unused Docker images
docker system prune -a

# Remove old backups (keeps last 30 days)
./scripts/backup.sh --retention-days 30

# Clean application logs
docker exec -it promptops-backend rm -rf /app/logs/*.log
```

---

## Performance Tuning

### PostgreSQL

```sql
-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '1GB';

-- Increase work_mem for sorting
ALTER SYSTEM SET work_mem = '64MB';

-- Enable query plan caching
ALTER SYSTEM SET plan_cache_mode = 'force_generic_plan';

-- Restart PostgreSQL
```

### Backend

```python
# Increase workers in start_with_mock_db.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4  # Increase workers
    )
```

---

## Cost Optimization

### Current Cost: $0/month

**Using:**
- Oracle Cloud Free Tier (compute)
- GitHub Actions Free Tier (CI/CD)
- Let's Encrypt (SSL certificates)
- Open-source monitoring stack

**Potential Paid Upgrades:**
- DigitalOcean Droplet: $6/month (2 GB RAM)
- Hetzner Cloud: $4/month (2 GB RAM)
- AWS RDS: ~$15/month (managed database)

---

## Support

**Documentation:** https://github.com/your-org/promptops/wiki  
**Issues:** https://github.com/your-org/promptops/issues  
**Discussions:** https://github.com/your-org/promptops/discussions

---

## License

MIT License - See LICENSE file

---

**Deployment Checklist:**

- [ ] Environment variables configured
- [ ] Secrets generated and secured
- [ ] SSL certificates obtained
- [ ] Firewall configured
- [ ] Monitoring dashboards set up
- [ ] Automated backups configured
- [ ] Health checks passing
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Team trained on maintenance

**Production Ready! 🚀**
