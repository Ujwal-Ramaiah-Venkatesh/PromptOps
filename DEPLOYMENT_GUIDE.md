# PromptOps Deployment Guide

**Week 11-12 Deliverable**: Complete deployment and operations runbook.

**Version**: 1.0.0  
**Last Updated**: 2026-04-29

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Operations Runbook](#operations-runbook)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Troubleshooting](#troubleshooting)
9. [Disaster Recovery](#disaster-recovery)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                       Internet                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │    CloudFront CDN          │
              │  (Frontend Distribution)   │
              └─────────────┬──────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
    ┌────▼─────┐                         ┌────▼─────┐
    │  S3      │                         │   ALB    │
    │ Frontend │                         │  + WAF   │
    └──────────┘                         └────┬─────┘
                                              │
                               ┌──────────────┴──────────────┐
                               │      ECS Cluster            │
                               │  ┌─────────────────┐        │
                               │  │  API Gateway    │        │
                               │  │  (FastAPI)      │        │
                               │  └────────┬────────┘        │
                               │           │                 │
                               │  ┌────────▼────────┐        │
                               │  │ Context         │        │
                               │  │ Collector       │        │
                               │  └────────┬────────┘        │
                               └───────────┼─────────────────┘
                                           │
                              ┌────────────▼──────────────┐
                              │   RDS PostgreSQL 15      │
                              │   (Multi-AZ)             │
                              └───────────────────────────┘
```

### Infrastructure Stack

**Frontend**:
- React 18.2.0 SPA
- Hosted on S3
- Distributed via CloudFront CDN
- HTTPS with ACM certificate

**Backend**:
- FastAPI 0.109.0 (API Gateway)
- Python 3.11
- ECS Fargate (serverless containers)
- Application Load Balancer

**Database**:
- PostgreSQL 15 on RDS
- Multi-AZ for high availability
- Automated backups (7-day retention)

**AI Integration**:
- Anthropic Claude API (Sonnet 4.5)
- Context-aware parsing
- Task decomposition

**Monitoring**:
- CloudWatch Logs & Metrics
- CloudWatch Alarms
- SNS for notifications

---

## Prerequisites

### AWS Account Setup

1. **AWS Account**:
   - Production account
   - Staging account (recommended)
   - IAM user with deployment permissions

2. **Required AWS Services**:
   - ECS (Elastic Container Service)
   - RDS (Relational Database Service)
   - S3 (Simple Storage Service)
   - CloudFront
   - Application Load Balancer
   - VPC (Virtual Private Cloud)
   - IAM (Identity and Access Management)
   - Secrets Manager
   - CloudWatch

3. **Domain & SSL**:
   - Domain name (e.g., promptops.com)
   - ACM certificate for HTTPS

---

### Required Credentials

1. **Anthropic API Key**:
   ```bash
   # Get from: https://console.anthropic.com/
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   ```

2. **AWS Credentials**:
   ```bash
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-east-1
   ```

3. **Database Password**:
   ```bash
   # Generate secure password
   DB_PASSWORD=$(openssl rand -base64 32)
   ```

4. **Docker Hub** (for CI/CD):
   ```bash
   DOCKER_USERNAME=your-username
   DOCKER_PASSWORD=your-password
   ```

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_ORG/PromptOps.git
cd PromptOps
```

---

### 2. Backend Setup

```bash
# Install Python 3.11
python --version  # Should be 3.11.x

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-xxxxx
export DATABASE_URL=postgresql://promptops:password@localhost:5432/promptops

# Initialize database
createdb promptops
psql -d promptops -f database/schema.sql

# Start API Gateway
cd api_gateway
python main.py

# API available at: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

### 3. Frontend Setup

```bash
# Install Node.js 18+
node --version  # Should be 18.x or higher

# Install dependencies
cd frontend/dashboard
npm install

# Configure environment
cp .env.development .env.local
# Edit .env.local if needed

# Start development server
npm start

# Dashboard available at: http://localhost:3000
```

---

### 4. Verify Local Setup

```bash
# Test API connection
cd frontend/dashboard
node scripts/test-api-connection.js

# Should see:
# ✅ Health check passed
# ✅ Parse intent passed
# ✅ Audit trail passed
# ✅ Drift endpoint passed
```

---

## Staging Deployment

### Infrastructure Setup (One-time)

#### 1. Create VPC

```bash
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=promptops-staging}]'

# Note VPC ID: vpc-xxxxx
```

#### 2. Create Subnets

```bash
# Public subnet (ALB)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=staging-public-1a}]'

# Private subnet (ECS)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=staging-private-1a}]'

# Database subnet
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.20.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=staging-db-1a}]'
```

#### 3. Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier promptops-staging-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.5 \
  --master-username promptops \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name staging-db-subnet-group \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --storage-encrypted \
  --tags Key=Environment,Value=staging

# Wait for available status (~10 minutes)
aws rds wait db-instance-available \
  --db-instance-identifier promptops-staging-db

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier promptops-staging-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

#### 4. Initialize Database Schema

```bash
# Get RDS endpoint from previous step
export DB_HOST=promptops-staging-db.xxxxx.us-east-1.rds.amazonaws.com
export DB_PASSWORD=your-secure-password

# Initialize schema
psql -h $DB_HOST -U promptops -d postgres -f database/schema.sql
```

#### 5. Store Secrets

```bash
# Store database credentials
aws secretsmanager create-secret \
  --name promptops/staging/database \
  --secret-string "{\"username\":\"promptops\",\"password\":\"$DB_PASSWORD\",\"host\":\"$DB_HOST\",\"port\":\"5432\",\"database\":\"promptops\"}"

# Store Anthropic API key
aws secretsmanager create-secret \
  --name promptops/staging/anthropic-key \
  --secret-string "{\"api_key\":\"$ANTHROPIC_API_KEY\"}"
```

#### 6. Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name promptops-staging \
  --tags key=Environment,value=staging
```

#### 7. Create Task Definitions

**API Gateway**:
```bash
cat > api-gateway-task.json <<EOF
{
  "family": "api-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "api-gateway",
      "image": "promptops/api-gateway:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "staging"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:promptops/staging/database"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:promptops/staging/anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/api-gateway",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "staging"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://api-gateway-task.json
```

#### 8. Create ECS Service

```bash
aws ecs create-service \
  --cluster promptops-staging \
  --service-name api-gateway \
  --task-definition api-gateway \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:ACCOUNT_ID:targetgroup/api-gateway/xxxxx,containerName=api-gateway,containerPort=8000" \
  --health-check-grace-period-seconds 60
```

#### 9. Create S3 Bucket for Frontend

```bash
# Create bucket
aws s3 mb s3://promptops-staging-frontend

# Configure for static website hosting
aws s3 website s3://promptops-staging-frontend \
  --index-document index.html \
  --error-document index.html

# Block public access (CloudFront will serve)
aws s3api put-public-access-block \
  --bucket promptops-staging-frontend \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

#### 10. Create CloudFront Distribution

```bash
cat > cloudfront-config.json <<EOF
{
  "CallerReference": "promptops-staging-$(date +%s)",
  "Comment": "PromptOps Staging Frontend",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-promptops-staging-frontend",
        "DomainName": "promptops-staging-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/xxxxx"
        }
      }
    ]
  },
  "DefaultRootObject": "index.html",
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-promptops-staging-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "Compress": true,
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  }
}
EOF

aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

---

### Deployment via CI/CD

**Automatic** (on push to main):
```bash
git push origin main

# GitHub Actions will:
# 1. Run tests
# 2. Build Docker images
# 3. Push to Docker Hub
# 4. Deploy to staging
# 5. Run smoke tests
```

---

### Manual Deployment

**Build and push Docker image**:
```bash
# Build
docker build -f Dockerfile.api -t promptops/api-gateway:v1.0.0 .

# Push
docker push promptops/api-gateway:v1.0.0
```

**Update ECS service**:
```bash
# Update task definition with new image tag
aws ecs register-task-definition \
  --cli-input-json file://api-gateway-task-v1.0.0.json

# Update service
aws ecs update-service \
  --cluster promptops-staging \
  --service api-gateway \
  --task-definition api-gateway:v1.0.0 \
  --force-new-deployment

# Wait for deployment
aws ecs wait services-stable \
  --cluster promptops-staging \
  --services api-gateway
```

**Deploy frontend**:
```bash
# Build
cd frontend/dashboard
REACT_APP_API_BASE_URL=https://staging-api.promptops.com/api/v1 npm run build

# Deploy to S3
aws s3 sync build/ s3://promptops-staging-frontend/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

---

## Production Deployment

### Differences from Staging

1. **High Availability**:
   - RDS Multi-AZ deployment
   - ECS service: 3+ tasks across AZs
   - ALB with health checks

2. **Performance**:
   - Larger instance types (db.t3.medium, ECS 1vCPU/2GB)
   - Read replicas for database
   - CloudFront with more cache rules

3. **Security**:
   - WAF rules enabled
   - VPC Flow Logs
   - GuardDuty enabled
   - All secrets in Secrets Manager

4. **Backups**:
   - 30-day RDS backup retention
   - Daily S3 bucket snapshots
   - Database exports to S3

---

### Production Checklist

Before deploying to production:

- [ ] Security audit complete
- [ ] Load testing passed
- [ ] All E2E tests passing
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Runbook reviewed
- [ ] Rollback plan ready
- [ ] Stakeholders notified
- [ ] Maintenance window scheduled
- [ ] Backup verified

---

### Production Deployment Steps

**1. Pre-deployment**:
```bash
# Verify staging is stable
curl -f https://staging-api.promptops.com/health

# Run final load test
cd tests/performance
locust -f load_test.py --host=https://staging-api.promptops.com \
  --users 100 --run-time 10m --headless

# Create deployment tag
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0
```

**2. Trigger deployment**:
```bash
# Via GitHub Actions (requires manual approval)
gh workflow run ci-cd.yml --ref main

# GitHub will:
# 1. Build and test
# 2. Deploy to staging
# 3. Wait for manual approval
# 4. Deploy to production
```

**3. Monitor deployment**:
```bash
# Watch ECS service
watch -n 5 'aws ecs describe-services \
  --cluster promptops-production \
  --services api-gateway \
  --query "services[0].deployments" \
  --output table'

# Check CloudWatch logs
aws logs tail /ecs/api-gateway --follow --filter-pattern "ERROR"
```

**4. Post-deployment verification**:
```bash
# Smoke tests
curl -f https://api.promptops.com/health

# Parse intent test
curl -X POST https://api.promptops.com/api/v1/parse-intent \
  -H "Content-Type: application/json" \
  -d '{"command": "Deploy frontend to staging", "user": "test@example.com"}'

# Check metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=api-gateway \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average
```

---

## Operations Runbook

### Daily Operations

#### Morning Checks

```bash
# 1. Check service health
curl https://api.promptops.com/health

# 2. Check ECS task count
aws ecs describe-services \
  --cluster promptops-production \
  --services api-gateway \
  --query 'services[0].runningCount'

# 3. Check CloudWatch alarms
aws cloudwatch describe-alarms \
  --state-value ALARM

# 4. Review error logs (last hour)
aws logs filter-log-events \
  --log-group-name /ecs/api-gateway \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"

# 5. Check drift events
curl https://api.promptops.com/api/v1/drift/recent
```

---

### Scaling

#### Manual Scaling

```bash
# Scale up
aws ecs update-service \
  --cluster promptops-production \
  --service api-gateway \
  --desired-count 5

# Scale down
aws ecs update-service \
  --cluster promptops-production \
  --service api-gateway \
  --desired-count 2
```

#### Auto-scaling (Configure once)

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/promptops-production/api-gateway \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/promptops-production/api-gateway \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

### Database Maintenance

#### Backup

```bash
# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier promptops-production-db \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d-%H%M%S)

# Export to S3
aws rds start-export-task \
  --export-task-identifier export-$(date +%Y%m%d) \
  --source-arn arn:aws:rds:us-east-1:ACCOUNT_ID:snapshot:manual-backup-xxxxx \
  --s3-bucket-name promptops-db-exports \
  --iam-role-arn arn:aws:iam::ACCOUNT_ID:role/rds-s3-export \
  --kms-key-id arn:aws:kms:us-east-1:ACCOUNT_ID:key/xxxxx
```

#### Restore

```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier promptops-production-db-restored \
  --db-snapshot-identifier manual-backup-20260429-120000

# Point-in-time restore
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier promptops-production-db \
  --target-db-instance-identifier promptops-production-db-restored \
  --restore-time 2026-04-29T12:00:00Z
```

---

### Log Analysis

#### Common Queries

**Error rate**:
```bash
aws logs filter-log-events \
  --log-group-name /ecs/api-gateway \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR" \
  | jq '.events | length'
```

**Slow requests** (>2s):
```bash
aws logs filter-log-events \
  --log-group-name /ecs/api-gateway \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --filter-pattern '[time, level, msg, duration > 2000]'
```

**Failed deployments**:
```bash
aws logs filter-log-events \
  --log-group-name /ecs/api-gateway \
  --filter-pattern "\"deploy\" \"failed\""
```

---

## Monitoring & Alerts

### CloudWatch Alarms

#### CPU Utilization

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-gateway-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=api-gateway \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:ops-alerts
```

#### Memory Utilization

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-gateway-high-memory \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 85 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=api-gateway \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:ops-alerts
```

#### Error Rate

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-gateway-high-errors \
  --metric-name Errors \
  --namespace PromptOps \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:ops-alerts
```

---

### Dashboards

**CloudWatch Dashboard**:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name PromptOps-Production \
  --dashboard-body file://dashboard-config.json
```

**Grafana** (optional):
- Install Grafana
- Configure CloudWatch data source
- Import dashboard templates

---

## Troubleshooting

### API Gateway Not Responding

**Symptoms**: Health check failing, 503 errors

**Diagnosis**:
```bash
# Check ECS tasks
aws ecs list-tasks --cluster promptops-production --service-name api-gateway

# Check task logs
aws logs tail /ecs/api-gateway --follow

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:ACCOUNT_ID:targetgroup/api-gateway/xxxxx
```

**Solutions**:
1. Restart tasks:
   ```bash
   aws ecs update-service \
     --cluster promptops-production \
     --service api-gateway \
     --force-new-deployment
   ```

2. Check secrets:
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id promptops/production/anthropic-key
   ```

3. Check database connectivity:
   ```bash
   # From ECS task
   psql -h $DB_HOST -U promptops -d promptops -c "SELECT 1"
   ```

---

### High Latency

**Symptoms**: Slow API responses, timeouts

**Diagnosis**:
```bash
# Check database query performance
psql -h $DB_HOST -U promptops -d promptops -c "
  SELECT query, calls, mean_exec_time, stddev_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;
"

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=promptops-production-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum
```

**Solutions**:
1. Add database indexes
2. Enable RDS read replicas
3. Scale up ECS tasks
4. Optimize Claude API calls (caching)

---

### Database Connection Pool Exhausted

**Symptoms**: `psycopg2.pool.PoolError`

**Diagnosis**:
```bash
# Check active connections
psql -h $DB_HOST -U promptops -d promptops -c "
  SELECT count(*) FROM pg_stat_activity WHERE datname='promptops';
"
```

**Solutions**:
```python
# Increase pool size in database/db.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,      # Increase
    max_overflow=40    # Increase
)
```

---

## Disaster Recovery

### RTO/RPO Targets

- **RTO** (Recovery Time Objective): 1 hour
- **RPO** (Recovery Point Objective): 15 minutes

---

### Backup Strategy

**Automated**:
- RDS automated backups (daily, 30-day retention)
- RDS transaction logs (continuous, 5-minute RPO)
- S3 versioning enabled
- Database exports to S3 (daily)

**Manual**:
- Pre-deployment snapshots
- Monthly full exports

---

### Recovery Procedures

#### Scenario 1: Database Failure

**Recovery**:
```bash
# 1. Restore from latest snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier promptops-production-db-new \
  --db-snapshot-identifier rds:promptops-production-db-2026-04-29-00-00

# 2. Update DNS or connection string
# 3. Verify data integrity
psql -h new-host -U promptops -d promptops -c "SELECT MAX(timestamp) FROM audit_log;"
```

**Estimated Time**: 15-30 minutes

---

#### Scenario 2: Region Failure

**Recovery**:
1. Failover to secondary region (if configured)
2. Restore from cross-region snapshot
3. Update DNS to secondary region
4. Deploy application to new region

**Estimated Time**: 1-2 hours

---

#### Scenario 3: Accidental Data Deletion

**Recovery**:
```bash
# Point-in-time restore
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier promptops-production-db \
  --target-db-instance-identifier promptops-production-db-pitr \
  --restore-time 2026-04-29T10:00:00Z

# Recover specific table
pg_dump -h restored-host -U promptops -d promptops -t audit_log > audit_log_backup.sql
psql -h production-host -U promptops -d promptops < audit_log_backup.sql
```

**Estimated Time**: 30 minutes - 1 hour

---

## Cost Optimization

### Monthly Cost Estimate

**Staging**:
- ECS: $30 (2 tasks × 0.5 vCPU)
- RDS: $25 (db.t3.micro)
- S3 + CloudFront: $5
- ALB: $20
- **Total**: ~$80/month

**Production**:
- ECS: $100 (3 tasks × 1 vCPU)
- RDS: $150 (db.t3.medium, Multi-AZ)
- S3 + CloudFront: $30
- ALB: $20
- CloudWatch: $10
- **Total**: ~$310/month

---

### Cost Reduction Tips

1. **Use Reserved Instances** for predictable load
2. **Enable auto-scaling** to scale down during off-hours
3. **Use S3 Intelligent-Tiering** for logs
4. **Enable CloudWatch Logs retention** (7-30 days)
5. **Stop staging environment** when not in use

---

## Support Contacts

- **On-call Engineer**: oncall@promptops.com
- **Slack**: #promptops-ops
- **PagerDuty**: https://promptops.pagerduty.com
- **AWS Support**: Premium support enabled

---

**Author**: PromptOps Team  
**Reviewed By**: DevOps Team  
**Next Review**: Quarterly  
**Status**: Production-Ready
