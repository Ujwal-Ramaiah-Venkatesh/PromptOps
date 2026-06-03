# 🚀 AWS Deployment Guide - PromptOps Testing

**Goal:** Deploy PromptOps web application to AWS to demonstrate product capabilities

**Deployment Options:**
1. **AWS Elastic Beanstalk** (Easiest - Recommended for quick demo)
2. **AWS ECS with Fargate** (Container-based, scalable)
3. **AWS EC2 with Docker** (Traditional, full control)
4. **AWS Amplify** (Frontend only, fastest)

---

## 🎯 RECOMMENDED: Option 1 - AWS Elastic Beanstalk (Fastest)

**Why:** Simplest AWS deployment, automatic scaling, monitoring included, perfect for demo.

**Cost:** ~$25-50/month (includes EC2 t3.small, RDS t3.micro, Load Balancer)

**Time:** 30-45 minutes

---

## 📋 Prerequisites

### 1. AWS Account Setup
```bash
# Install AWS CLI
# Windows (PowerShell):
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version

# Configure AWS credentials
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

### 2. Create AWS Access Keys
```
1. Go to: https://console.aws.amazon.com/iam/
2. Click "Users" → Your username → "Security credentials"
3. Click "Create access key"
4. Choose "CLI" use case
5. Download credentials (save securely!)
```

---

## 🚀 OPTION 1: AWS Elastic Beanstalk Deployment

### Architecture:
```
Internet → Application Load Balancer → EC2 Instances → (Backend + Frontend)
                                              ↓
                                        RDS PostgreSQL (optional)
```

### Step-by-Step Deployment:

#### Step 1: Prepare Application for Beanstalk

Create `Dockerrun.aws.json` in project root:

```json
{
  "AWSEBDockerrunVersion": 2,
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "promptops-backend:latest",
      "essential": true,
      "memory": 512,
      "portMappings": [
        {
          "hostPort": 8000,
          "containerPort": 8000
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ]
    },
    {
      "name": "frontend",
      "image": "promptops-frontend:latest",
      "essential": true,
      "memory": 256,
      "portMappings": [
        {
          "hostPort": 80,
          "containerPort": 80
        }
      ],
      "links": ["backend"]
    }
  ]
}
```

#### Step 2: Create `.ebextensions` Configuration

Create `.ebextensions/01_environment.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONUNBUFFERED: "1"
    PORT: "8000"
  aws:elasticbeanstalk:container:python:
    WSGIPath: api_gateway.app:app
  aws:autoscaling:launchconfiguration:
    InstanceType: t3.small
    IamInstanceProfile: aws-elasticbeanstalk-ec2-role
  aws:elasticbeanstalk:environment:
    ServiceRole: aws-elasticbeanstalk-service-role
    LoadBalancerType: application
```

#### Step 3: Deploy to Elastic Beanstalk

```bash
# Navigate to project directory
cd c:\Users\pqm847\Documents\PromptOps

# Install EB CLI
pip install awsebcli

# Initialize Elastic Beanstalk application
eb init -p docker promptops-app --region us-east-1

# Create environment and deploy
eb create promptops-production --instance-type t3.small

# Wait 5-10 minutes for deployment...

# Check status
eb status

# Open application in browser
eb open
```

#### Step 4: Configure Environment Variables

```bash
# Set environment variables
eb setenv \
  JWT_SECRET_KEY="your-super-secret-key-change-in-production" \
  ENVIRONMENT="production" \
  FRONTEND_URL="https://your-app.elasticbeanstalk.com"

# Deploy changes
eb deploy
```

---

## 🚀 OPTION 2: AWS ECS with Fargate (Container-Based)

### Architecture:
```
Internet → ALB → ECS Fargate Tasks → (Backend + Frontend containers)
                         ↓
                   RDS PostgreSQL
                         ↓
                   ElastiCache Redis
```

### Step 1: Build and Push Docker Images to ECR

```bash
# Create ECR repositories
aws ecr create-repository --repository-name promptops-backend --region us-east-1
aws ecr create-repository --repository-name promptops-frontend --region us-east-1

# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build images
docker build -t promptops-backend:latest -f Dockerfile.backend .
docker build -t promptops-frontend:latest -f Dockerfile.frontend .

# Tag images
docker tag promptops-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/promptops-backend:latest
docker tag promptops-frontend:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/promptops-frontend:latest

# Push to ECR
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/promptops-backend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/promptops-frontend:latest
```

### Step 2: Create ECS Infrastructure with Terraform

Create `terraform/ecs-deployment.tf`:

```hcl
# terraform/ecs-deployment.tf

provider "aws" {
  region = "us-east-1"
}

# VPC and Networking
resource "aws_vpc" "promptops_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "promptops-vpc"
  }
}

resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.promptops_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "promptops-public-1"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.promptops_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "promptops-public-2"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.promptops_vpc.id

  tags = {
    Name = "promptops-igw"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.promptops_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "promptops-public-rt"
  }
}

resource "aws_route_table_association" "public_rta_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_rta_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# Security Groups
resource "aws_security_group" "alb_sg" {
  name        = "promptops-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.promptops_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "promptops-alb-sg"
  }
}

resource "aws_security_group" "ecs_sg" {
  name        = "promptops-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.promptops_vpc.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  ingress {
    from_port       = 3003
    to_port         = 3003
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "promptops-ecs-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "promptops_alb" {
  name               = "promptops-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

  tags = {
    Name = "promptops-alb"
  }
}

resource "aws_lb_target_group" "backend_tg" {
  name        = "promptops-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.promptops_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
    matcher             = "200"
  }
}

resource "aws_lb_target_group" "frontend_tg" {
  name        = "promptops-frontend-tg"
  port        = 3003
  protocol    = "HTTP"
  vpc_id      = aws_vpc.promptops_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.promptops_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}

resource "aws_lb_listener_rule" "api_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/docs", "/openapi.json"]
    }
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "promptops_cluster" {
  name = "promptops-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "promptops-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend_logs" {
  name              = "/ecs/promptops-backend"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "frontend_logs" {
  name              = "/ecs/promptops-frontend"
  retention_in_days = 7
}

# ECS Task Definition - Backend
resource "aws_ecs_task_definition" "backend" {
  family                   = "promptops-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/promptops-backend:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = "production"
        },
        {
          name  = "PORT"
          value = "8000"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "backend"
        }
      }
    }
  ])
}

# ECS Task Definition - Frontend
resource "aws_ecs_task_definition" "frontend" {
  family                   = "promptops-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name  = "frontend"
      image = "<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/promptops-frontend:latest"
      
      portMappings = [
        {
          containerPort = 3003
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "VITE_API_URL"
          value = "http://${aws_lb.promptops_alb.dns_name}/api"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "frontend"
        }
      }
    }
  ])
}

# ECS Service - Backend
resource "aws_ecs_service" "backend" {
  name            = "promptops-backend-service"
  cluster         = aws_ecs_cluster.promptops_cluster.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend_tg.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}

# ECS Service - Frontend
resource "aws_ecs_service" "frontend" {
  name            = "promptops-frontend-service"
  cluster         = aws_ecs_cluster.promptops_cluster.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend_tg.arn
    container_name   = "frontend"
    container_port   = 3003
  }

  depends_on = [aws_lb_listener.http]
}

# Outputs
output "alb_dns_name" {
  value       = aws_lb.promptops_alb.dns_name
  description = "DNS name of the Application Load Balancer"
}

output "application_url" {
  value       = "http://${aws_lb.promptops_alb.dns_name}"
  description = "URL to access the application"
}

output "backend_api_url" {
  value       = "http://${aws_lb.promptops_alb.dns_name}/api"
  description = "Backend API URL"
}
```

### Step 3: Deploy with Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (type 'yes' when prompted)
terraform apply

# Get application URL (wait 3-5 minutes after apply)
terraform output application_url
```

---

## 🚀 OPTION 3: Simple EC2 with Docker (Quick & Easy)

### Step 1: Launch EC2 Instance

```bash
# Create security group
aws ec2 create-security-group \
  --group-name promptops-sg \
  --description "PromptOps security group" \
  --region us-east-1

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name promptops-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0  # SSH (restrict to your IP in production)

aws ec2 authorize-security-group-ingress \
  --group-name promptops-sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0  # HTTP

aws ec2 authorize-security-group-ingress \
  --group-name promptops-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0  # HTTPS

# Launch EC2 instance (Ubuntu 22.04)
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups promptops-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=promptops-server}]' \
  --region us-east-1

# Get instance public IP
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=promptops-server" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

### Step 2: SSH and Install Docker

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@<INSTANCE_PUBLIC_IP>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Step 3: Deploy Application

```bash
# Clone repository (or upload files)
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=your-super-secret-key-change-me
ENVIRONMENT=production
PORT=8000
EOF

# Build and start containers
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Application should be available at http://<INSTANCE_PUBLIC_IP>:3003
```

### Step 4: Setup Nginx Reverse Proxy (Optional but Recommended)

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/promptops

# Add this configuration:
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or use public IP

    # Frontend
    location / {
        proxy_pass http://localhost:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/promptops /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Application now available at http://<INSTANCE_PUBLIC_IP>
```

---

## 🚀 OPTION 4: AWS Amplify (Frontend Only - Fastest)

**Best for:** Quick demo of frontend, backend runs locally or on separate server

### Step 1: Build Frontend for Production

```bash
cd frontend/dashboard

# Update API URL in .env
echo "VITE_API_URL=http://your-backend-url.com/api" > .env.production

# Build
npm run build

# Output is in frontend/dashboard/dist/
```

### Step 2: Deploy to AWS Amplify

**Via AWS Console:**
1. Go to https://console.aws.amazon.com/amplify/
2. Click "New app" → "Host web app"
3. Choose "Deploy without Git provider"
4. Upload `frontend/dashboard/dist` folder as ZIP
5. Wait 2-3 minutes
6. Get Amplify URL

**Via AWS CLI:**
```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting

# Choose "Hosting with Amplify Console (Managed hosting with custom domains, Continuous deployment)"

# Publish
amplify publish

# Get URL
amplify status
```

---

## 📊 Cost Comparison

| Option | Monthly Cost | Setup Time | Scalability | Best For |
|--------|--------------|------------|-------------|----------|
| **Elastic Beanstalk** | $25-50 | 30 min | Auto | Quick demo |
| **ECS Fargate** | $40-80 | 60 min | High | Production |
| **EC2 + Docker** | $15-30 | 45 min | Manual | Testing |
| **Amplify (Frontend)** | $1-5 | 10 min | Auto | Frontend demo |

---

## 🎯 RECOMMENDED QUICK START

### For Testing PromptOps NOW (Fastest - 20 minutes):

```bash
# 1. Launch EC2 instance (t3.medium)
# 2. SSH and run these commands:

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# Clone and deploy
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps
docker-compose up -d

# Wait 2-3 minutes, then access:
# http://<EC2-PUBLIC-IP>:3003
```

**Done! Your application is live on AWS.** ✅

---

## 🔒 Production Checklist

Before going to production:

- [ ] Change JWT_SECRET_KEY to strong random value
- [ ] Setup SSL/TLS certificate (AWS Certificate Manager + CloudFront/ALB)
- [ ] Configure custom domain name (Route 53)
- [ ] Enable CloudWatch monitoring
- [ ] Setup automated backups
- [ ] Configure auto-scaling policies
- [ ] Implement rate limiting
- [ ] Setup AWS WAF for security
- [ ] Enable CloudTrail logging
- [ ] Configure RDS PostgreSQL (don't use in-memory DB)
- [ ] Setup Redis for session management
- [ ] Configure S3 for file uploads
- [ ] Enable AWS Secrets Manager for sensitive data
- [ ] Setup CI/CD pipeline (CodePipeline)
- [ ] Configure health checks
- [ ] Setup alerting (SNS + CloudWatch Alarms)

---

## 🐛 Troubleshooting

### Issue: Can't connect to application
**Solution:**
- Check security group allows port 80/443
- Verify containers are running: `docker-compose ps`
- Check logs: `docker-compose logs`

### Issue: Backend API not accessible
**Solution:**
- Verify backend container health: `docker logs promptops-backend`
- Check backend is listening on correct port: `curl http://localhost:8000/health`
- Ensure firewall allows traffic

### Issue: Frontend can't reach backend
**Solution:**
- Check VITE_API_URL in frontend environment
- Verify CORS settings in backend
- Check network connectivity between containers

---

## 📈 Monitoring & Observability

### CloudWatch Setup

```bash
# Install CloudWatch agent on EC2
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure CloudWatch
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
```

### Key Metrics to Monitor

- CPU Utilization
- Memory Usage
- Disk I/O
- Network Traffic
- Response Time (p50, p95, p99)
- Error Rate
- Request Count
- Active Connections

---

## 🚀 Next Steps

After deployment:

1. **Test the application** thoroughly
2. **Configure monitoring** and alerting
3. **Setup CI/CD pipeline** for automatic deployments
4. **Add custom domain** and SSL certificate
5. **Scale horizontally** based on traffic
6. **Implement caching** (CloudFront, Redis)
7. **Add database** (RDS PostgreSQL)
8. **Configure backups** and disaster recovery

---

## 📞 Support

If you encounter issues:

1. Check CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/
2. Review ECS Task logs (if using ECS)
3. SSH into EC2 and check Docker logs
4. Verify security group rules
5. Check IAM permissions

---

**🎉 Congratulations! Your PromptOps application is now running on AWS!**

**Access your application:**
- Frontend: http://<YOUR-URL>
- Backend API: http://<YOUR-URL>/api
- API Docs: http://<YOUR-URL>/docs

**Test credentials:**
- Admin: admin@promptops.com / admin123
- PM: pm@promptops.com / pm123
