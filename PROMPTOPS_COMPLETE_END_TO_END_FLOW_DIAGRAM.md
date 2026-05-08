# PromptOps Complete End-to-End Flow Diagram
## All Application Deployments & DevOps Workflows

**Version 2.0 | May 2026**  
**Comprehensive System Architecture & Flow Documentation**

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Complete Agent Architecture](#complete-agent-architecture)
3. [End-to-End Flow by Deployment Type](#end-to-end-flow-by-deployment-type)
4. [Application-Specific Flows](#application-specific-flows)
5. [Decision Trees & Routing Logic](#decision-trees--routing-logic)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Integration Patterns](#integration-patterns)

---

## System Architecture Overview

### The Complete Five-Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PM Dashboard (Web UI)                                │
│                                                                              │
│  Plain English Commands:                                                     │
│  • "Deploy fraud detection v2.3 to production with canary"                  │
│  • "Train a churn model on last 90 days of data"                           │
│  • "Fix the high CPU alert on the API service"                             │
│  • "Show me why the last Jenkins build failed"                             │
│                                                                              │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │
                                 │ Raw Command Text
                                 ▼
                    ┌────────────────────────────┐
                    │     NLP Parser Engine       │
                    │     (Phase 1 - Core)        │
                    │                             │
                    │  • Claude Sonnet 4          │
                    │  • LangGraph Orchestration  │
                    │  • Spacy NLP                │
                    │  • 92%+ Intent Accuracy     │
                    │                             │
                    │  Input: Raw text            │
                    │  Output: Structured JSON    │
                    └────────────┬───────────────┘
                                 │
                                 │ JSON Intent
                                 │ {
                                 │   "intent": "deploy_application",
                                 │   "app": "fraud-detection",
                                 │   "version": "2.3",
                                 │   "environment": "production",
                                 │   "strategy": "canary",
                                 │   "compliance": ["sox"],
                                 │   "confidence": 0.98
                                 │ }
                                 ▼
                    ┌────────────────────────────┐
                    │  Agent Orchestration Layer  │
                    │  (Decision & Routing)       │
                    │                             │
                    │  • Intent Classification    │
                    │  • Agent Selection          │
                    │  • Pipeline Routing         │
                    │  • Compliance Validation    │
                    └────────────┬───────────────┘
                                 │
                                 │ Route to Appropriate Agents
                                 │
            ┌────────────────────┼────────────────────┬────────────────────┐
            │                    │                    │                    │
            ▼                    ▼                    ▼                    ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │  Architect    │   │   SRE Agent   │   │   Security    │   │   MLOps       │
    │  Agent        │   │               │   │   Agent       │   │   Agent       │
    │  (Phase 2)    │   │  (Phase 3)    │   │  (Phase 4)    │   │  (Phase 5)    │
    │               │   │               │   │               │   │               │
    │ • IaC Gen     │   │ • Monitoring  │   │ • OPA Rules   │   │ • Training    │
    │ • Terraform   │   │ • Metrics     │   │ • Policy      │   │ • Deploy      │
    │ • Pulumi      │   │ • Causal AI   │   │ • Audit       │   │ • Drift       │
    │ • Cost Est    │   │ • Auto-Heal   │   │ • Compliance  │   │ • Tune        │
    └───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
            │                   │                   │                   │
            └───────────────────┴───────────────────┴───────────────────┘
                                │
                                ▼
                    ┌────────────────────────────┐
                    │    CI/CD Agent (Phase 6)    │
                    │    Pipeline Orchestrator    │
                    │                             │
                    │  Decision Engine:           │
                    │  • GitHub Actions (Fast)    │
                    │  • Jenkins (Enterprise)     │
                    │  • GitLab CI               │
                    │  • Azure DevOps            │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        ┌─────────────────────┐   ┌─────────────────────┐
        │  GitHub Actions     │   │  Jenkins Pipeline    │
        │  (Fast Path)        │   │  (Enterprise Path)   │
        │                     │   │                      │
        │ • Feature deploys   │   │ • Prod deploys       │
        │ • Staging           │   │ • Blue-green         │
        │ • Simple builds     │   │ • Canary release     │
        │ • <30 min builds    │   │ • Compliance (SOX)   │
        │ • No approval req   │   │ • Multi-approval     │
        └──────────┬──────────┘   └──────────┬───────────┘
                   │                         │
                   └──────────┬──────────────┘
                              │
                              ▼
                ┌─────────────────────────────────┐
                │   Shadow Validation Sandbox     │
                │   (Safety Layer - Pre-Prod)     │
                │                                 │
                │  • Test in isolated env         │
                │  • No production impact         │
                │  • Rollback ready               │
                │  • Validates all changes        │
                └─────────────┬───────────────────┘
                              │
                              │ All Validations Passed ✓
                              ▼
                ┌─────────────────────────────────┐
                │    Deployment Strategies        │
                │    (Choose Based on Context)    │
                │                                 │
                │  1. Rolling (cost-efficient)    │
                │  2. Blue-Green (zero-downtime)  │
                │  3. Canary (gradual, safe)      │
                │  4. Feature Flag (A/B testing)  │
                │  5. Shadow (ML validation)      │
                │  6. Recreate (dev/staging only) │
                └─────────────┬───────────────────┘
                              │
                              ▼
                ┌─────────────────────────────────┐
                │     Live Cloud Execution        │
                │     (Multi-Cloud Support)       │
                │                                 │
                │  AWS: ECS, EKS, Lambda, RDS     │
                │  Azure: AKS, Functions, SQL     │
                │  GCP: GKE, Cloud Run, SQL       │
                │                                 │
                │  ML: SageMaker, Vertex AI       │
                └─────────────┬───────────────────┘
                              │
                              │ Real-time Monitoring & Feedback
                              ▼
                ┌─────────────────────────────────┐
                │    SRE Agent Monitoring         │
                │    (Continuous Observation)     │
                │                                 │
                │  • Prometheus metrics (60s)     │
                │  • CloudWatch alarms            │
                │  • Error rate tracking          │
                │  • Latency monitoring           │
                │  • Auto-remediation triggers    │
                └─────────────┬───────────────────┘
                              │
                              ▼
                ┌─────────────────────────────────┐
                │    PM Dashboard Update          │
                │    (Real-time Results)          │
                │                                 │
                │  ✅ Deployment Success          │
                │  Duration: 12m 34s              │
                │  Cost: $4.23                    │
                │  Health: Healthy ✓              │
                │  Error Rate: 0.02%              │
                │                                 │
                │  [View Details] [Rollback]      │
                └─────────────────────────────────┘
```

---

## Complete Agent Architecture

### Agent Responsibilities & Interactions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENT INTERACTION MAP                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ NLP Parser (Phase 1) - The Brain                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ Input:  "Deploy fraud detection model v2.3 to production with canary"        │
│                                                                               │
│ Process:                                                                      │
│ 1. Claude Sonnet 4 analyzes text                                            │
│ 2. LangGraph validates intent structure                                      │
│ 3. Spacy extracts entities (app, version, env, strategy)                    │
│ 4. Confidence scoring (must be >85%)                                         │
│ 5. Context retrieval (infrastructure state, past deployments)               │
│                                                                               │
│ Output: {                                                                     │
│   "intent": "deploy_ml_model",                                               │
│   "application": "fraud-detection",                                          │
│   "model_version": "2.3",                                                    │
│   "environment": "production",                                               │
│   "deployment_strategy": "canary",                                           │
│   "requires_approval": true,                                                 │
│   "risk_level": "critical",                                                  │
│   "estimated_duration": 120,                                                 │
│   "estimated_cost": 45,                                                      │
│   "agents_needed": ["MLOps", "Architect", "Security", "SRE", "CI/CD"],     │
│   "compliance_requirements": ["sox", "model_approval"]                       │
│ }                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Security Agent (Phase 4) - The Guardrail                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Runs FIRST - Blocks unsafe actions                                           │
│                                                                               │
│ Checks:                                                                       │
│ 1. OPA Policy Validation                                                     │
│    ✓ Model approved? (check model registry)                                  │
│    ✓ Bias testing passed? (check ML audit log)                              │
│    ✓ Required approvals obtained? (2-person rule for prod)                  │
│                                                                               │
│ 2. Compliance Validation                                                     │
│    ✓ SOX audit trail enabled                                                │
│    ✓ Change ticket created (ServiceNow)                                     │
│    ✓ External auditor notified                                              │
│                                                                               │
│ 3. IAM & Network Security                                                    │
│    ✓ Least privilege IAM role                                               │
│    ✓ No public internet access                                              │
│    ✓ Encryption at rest & in transit                                        │
│                                                                               │
│ Output: {"security_approved": true, "audit_log_id": "SEC-2026-05-04-001"}   │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ MLOps Agent (Phase 5) - ML Lifecycle Manager                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ ML-specific operations                                                        │
│                                                                               │
│ Actions:                                                                      │
│ 1. Model Validation                                                          │
│    • Retrieve model from registry (MLflow)                                   │
│    • Check model version exists (fraud-detection v2.3)                       │
│    • Validate model performance metrics (staging: 94% accuracy)              │
│    • Check for data drift alerts (none in last 7 days)                      │
│                                                                               │
│ 2. Shadow Deployment (24 hours)                                              │
│    • Deploy model to shadow endpoint (parallel to prod)                      │
│    • Mirror 100% of production traffic                                       │
│    • Compare predictions: shadow vs production                               │
│    • Alert if prediction diff rate >5%                                       │
│    • Collect performance metrics (latency, throughput)                       │
│                                                                               │
│ 3. Generate Deployment Config                                                │
│    • SageMaker endpoint config: ml.m5.xlarge, auto-scaling 2-20 instances   │
│    • API Gateway integration                                                 │
│    • CloudWatch metrics & alarms                                             │
│                                                                               │
│ Output: {"shadow_passed": true, "canary_config": {...}}                      │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Architect Agent (Phase 2) - Infrastructure Provisioner                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ Generates & applies Infrastructure-as-Code                                   │
│                                                                               │
│ Actions:                                                                      │
│ 1. Generate Terraform Code                                                   │
│    • SageMaker endpoint resource                                             │
│    • Auto-scaling policy (target: 70% CPU, 2-20 instances)                  │
│    • API Gateway + VPC Link                                                  │
│    • CloudWatch log group + alarms                                           │
│    • IAM role (least privilege)                                              │
│    • Security groups (private subnet only)                                   │
│                                                                               │
│ 2. Cost Estimation                                                           │
│    • ml.m5.xlarge: $0.23/hr × 8760 hrs/yr × 5 avg instances = $10,074/yr   │
│    • API Gateway: $3.50/million requests × 12M/yr = $42/yr                  │
│    • CloudWatch: $0.30/GB × 50GB/month × 12 = $180/yr                       │
│    • Total: $10,296/yr ($858/month)                                          │
│                                                                               │
│ 3. Shadow Validation (Sandbox)                                               │
│    • Apply Terraform in isolated sandbox environment                         │
│    • Verify resources created successfully                                   │
│    • Run smoke tests (health check, sample prediction)                       │
│    • If passed: Apply to production                                          │
│    • If failed: Destroy sandbox, report error                                │
│                                                                               │
│ Output: {"infrastructure_ready": true, "endpoint_url": "..."}                │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ CI/CD Agent (Phase 6) - Pipeline Orchestrator                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ Decides which pipeline & deployment strategy                                 │
│                                                                               │
│ Pipeline Decision:                                                            │
│ • Environment: production → Jenkins (compliance required)                    │
│ • Strategy: canary → Jenkins (advanced strategy)                             │
│ • Compliance: SOX → Jenkins (audit trail)                                    │
│ • Risk: critical → Jenkins (multi-stage approval)                            │
│ → Decision: Jenkins Canary Pipeline                                          │
│                                                                               │
│ Canary Stages:                                                                │
│ 1. Deploy 5% canary → Monitor 30 min → Auto-rollback if error rate >1%      │
│ 2. Deploy 25% canary → Monitor 30 min → Auto-rollback if latency spike      │
│ 3. Deploy 50% canary → Monitor 30 min → Auto-rollback if predictions drift  │
│ 4. Deploy 100% full rollout → Monitor 10 min → Complete                     │
│                                                                               │
│ Jenkins Job: "PromptOps-ML-Canary-Deploy"                                    │
│ • Build Docker image (model + inference code)                                │
│ • Run integration tests                                                      │
│ • Deploy to ECS/SageMaker with canary weights                               │
│ • Real-time monitoring with SRE Agent                                        │
│                                                                               │
│ Output: {"deployment_id": "fraud-v2.3-20260504-142", "jenkins_build": 142}  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ SRE Agent (Phase 3) - Continuous Monitoring & Auto-Healing                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ Monitors during & after deployment                                           │
│                                                                               │
│ Monitoring (every 60 seconds):                                                │
│ 1. Prometheus Metrics                                                        │
│    • http_requests_total (error rate)                                        │
│    • http_request_duration_seconds (latency p50/p95/p99)                    │
│    • model_predictions_total (throughput)                                    │
│    • model_prediction_accuracy (compared to labeled feedback)                │
│                                                                               │
│ 2. CloudWatch Metrics                                                        │
│    • SageMaker endpoint invocations                                          │
│    • Model latency                                                           │
│    • 4xx/5xx errors                                                          │
│    • Instance CPU/Memory utilization                                         │
│                                                                               │
│ 3. Canary Health Checks                                                      │
│    • Error rate: Current vs Baseline                                         │
│      - Baseline (v2.2): 0.12%                                                │
│      - Current (v2.3 @ 5%): 0.14% ✓ (within threshold)                      │
│    • Latency P95: Current vs Baseline                                       │
│      - Baseline: 285ms                                                       │
│      - Current: 298ms ✓ (within 150% threshold)                             │
│    • Prediction Drift: Shadow vs Production                                  │
│      - Prediction diff rate: 2.3% ✓ (threshold: 5%)                         │
│                                                                               │
│ 4. Auto-Remediation (if needed)                                              │
│    • High latency → Scale up instances                                       │
│    • Memory spike → Restart unhealthy tasks                                  │
│    • Error spike → Trigger rollback                                          │
│                                                                               │
│ Output: {"canary_health": "healthy", "continue_rollout": true}               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Flow by Deployment Type

### Flow 1: Simple Web App Deployment (Startup - GitHub Actions)

```
PM Types: "Deploy blog v1.2 to production"
        │
        ▼
NLP Parser (2s)
├─ Intent: deploy_application
├─ App: blog
├─ Version: 1.2
├─ Environment: production
├─ Confidence: 0.98
└─ Risk: low
        │
        ▼
Agent Selection (1s)
├─ CI/CD Agent (GitHub Actions - fast path)
├─ Architect Agent (minimal infra)
├─ Security Agent (basic checks)
└─ SRE Agent (skip - non-critical)
        │
        ▼
Security Check (3s)
├─ ✓ No public database exposure
├─ ✓ Secrets encrypted
└─ ✓ Least privilege IAM
        │
        ▼
GitHub Actions Pipeline (5 min)
├─ Checkout code (v1.2 tag)
├─ Install dependencies (npm ci)
├─ Run tests (23/23 passed)
├─ Build Docker image
└─ Push to ECR
        │
        ▼
Architect Agent (2 min)
├─ Generate Terraform: 1 ECS Fargate task
├─ Cost estimate: $15/month
├─ Shadow validation: passed
└─ Apply to production
        │
        ▼
Deployment (2 min)
├─ ECS rolling update (1 task → 1 task)
├─ Health check: 200 OK
├─ CloudFront cache invalidation
└─ DNS propagation
        │
        ▼
SRE Monitoring (1 min)
├─ Response time: 120ms (p95)
├─ Error rate: 0%
└─ Health: Healthy ✓
        │
        ▼
PM Dashboard
✅ Deployment Complete: blog v1.2 → production
Duration: 11m 42s
Cost: $0.14
URL: https://blog.yourcompany.com
```

---

### Flow 2: Enterprise Microservice (Jenkins Canary - 90 minutes)

```
PM Types: "Deploy payment-processor v3.5 to production with canary rollout and SOX compliance"
        │
        ▼
NLP Parser (2s)
├─ Intent: deploy_application
├─ App: payment-processor
├─ Version: 3.5
├─ Environment: production
├─ Strategy: canary
├─ Compliance: sox, pci-dss
├─ Risk: CRITICAL
└─ Confidence: 0.97
        │
        ▼
Agent Selection (1s)
├─ CI/CD Agent (Jenkins - enterprise path)
├─ Architect Agent (canary infra)
├─ Security Agent (strict mode)
├─ SRE Agent (enhanced monitoring)
└─ MLOps Agent (skip)
        │
        ▼
Approval Workflow (30 min - human delay)
├─ Email sent to: Sarah Chen (VP Eng), Mike Johnson (CISO)
├─ Sarah approves (15 min) ✓
├─ Mike approves (20 min) ✓
└─ All approvals received
        │
        ▼
Security Agent - Strict Mode (10s)
├─ ✓ SOX audit trail enabled
├─ ✓ PCI-DSS requirement 6.2 satisfied
├─ ✓ Payment card data encryption (AES-256-GCM)
├─ ✓ Database credentials rotated (28 days ago)
├─ ✓ IAM least privilege validated
├─ ✓ Network segmentation confirmed
└─ ✓ External auditor notified (Deloitte)
        │
        ▼
Jenkins Pipeline Triggered (job: PromptOps-Canary-Deploy-Pipeline)
        │
        ▼
Stage 1: Pre-Flight Checks (2 min)
├─ Verify approvals (2 received) ✓
├─ Verify change ticket (CHG-2026-05-04-001) ✓
├─ Docker image exists ✓
└─ OPA policy validation ✓
        │
        ▼
Stage 2: Build & Test (25 min)
├─ Maven build (10 min)
├─ SonarQube quality gate (2 min) ✓
├─ Unit tests: 2,456 passed
├─ Integration tests: 89 passed
├─ Load test: 50k TPS (5 min) ✓
├─ SAST (Checkmarx)
├─ DAST (OWASP ZAP)
├─ Container scan (Trivy)
└─ Dependency check (OWASP)
        │
        ▼
Stage 3: Baseline Metrics (1 min)
├─ Current error rate: 0.12%
├─ Current latency p95: 285ms
├─ Current throughput: 12,450 req/min
└─ Baseline established
        │
        ▼
Stage 4: Deploy 5% Canary (3 min)
├─ Update ECS service (desired-count-percentage: 5)
├─ Update ALB weights (v3.4: 95%, v3.5: 5%)
└─ Wait for services-stable
        │
        ▼
Stage 5: Monitor 5% Canary (30 min)
├─ Check every 60s:
│   ├─ Error rate: 0.14% ✓ (threshold: 1.12%)
│   ├─ Latency p95: 292ms ✓ (threshold: 428ms)
│   └─ Payment success: 98.6% ✓ (threshold: 98%)
├─ Notify PromptOps dashboard every minute
└─ After 30 min: Canary healthy ✓
        │
        ▼
Stage 6: Deploy 25% Canary (3 min)
├─ Update ALB weights (v3.4: 75%, v3.5: 25%)
└─ Wait for services-stable
        │
        ▼
Stage 7: Monitor 25% Canary (30 min)
├─ Same monitoring as 5% stage
└─ After 30 min: Canary healthy ✓
        │
        ▼
Stage 8: Deploy 50% Canary (3 min)
├─ Update ALB weights (v3.4: 50%, v3.5: 50%)
└─ Wait for services-stable
        │
        ▼
Stage 9: Monitor 50% Canary (30 min)
├─ Same monitoring as previous stages
└─ After 30 min: Canary healthy ✓
        │
        ▼
Stage 10: Full Rollout 100% (3 min)
├─ Update ALB weights (v3.5: 100%)
├─ Scale down old version (v3.4 → 0 tasks)
└─ Wait for services-stable
        │
        ▼
Stage 11: Post-Deployment (5 min)
├─ Smoke tests (pytest tests/smoke/)
├─ Final metrics check
├─ Log to SOX audit trail (S3)
├─ Notify external auditor (Deloitte)
└─ Update PM Dashboard
        │
        ▼
SRE Agent Monitoring (continuous)
├─ Enhanced monitoring for 24 hours
├─ Alert threshold lowered (more sensitive)
├─ Auto-remediation armed
└─ Post-mortem auto-generated if incident
        │
        ▼
PM Dashboard
✅ Deployment Complete: payment-processor v3.5 → production
Duration: 117m 32s (30m approval + 87m deployment)
Cost: $43.89
Downtime: 0 seconds
Transactions processed: 1,087,234
Revenue during deployment: $12,456,789
[View Jenkins Build] [View Audit Trail] [Rollback if Needed]
```

---

### Flow 3: ML Model Deployment (MLOps + SageMaker)

```
PM Types: "Deploy fraud detection model v2.3 to production with shadow testing"
        │
        ▼
NLP Parser (2s)
├─ Intent: deploy_ml_model
├─ App: fraud-detection
├─ Model: v2.3
├─ Environment: production
├─ Strategy: shadow → canary
├─ Risk: high
└─ Confidence: 0.96
        │
        ▼
Agent Selection (1s)
├─ MLOps Agent (primary)
├─ Architect Agent (SageMaker infra)
├─ Security Agent (model approval + bias check)
├─ SRE Agent (drift monitoring)
└─ CI/CD Agent (deployment orchestration)
        │
        ▼
Security Agent (5s)
├─ Check model approval status
│   └─ Model v2.3 approved by: Data Scientist (May 1) + PM (May 2) ✓
├─ Check bias testing
│   └─ Bias report: 3.2% disparity (threshold: 15%) ✓
├─ Check training data provenance
│   └─ Training data: s3://fraud-data/2026-04-01-to-2026-04-30 ✓
└─ Security approved
        │
        ▼
MLOps Agent - Model Validation (2 min)
├─ Retrieve model from MLflow registry
│   ├─ Model: fraud-detection v2.3
│   ├─ Trained: 2026-05-01
│   ├─ Algorithm: XGBoost
│   ├─ Training accuracy: 94.2%
│   └─ Staging accuracy: 93.8%
├─ Check data drift alerts
│   └─ No drift detected in last 7 days ✓
├─ Validate model artifacts
│   ├─ Model file: fraud_model_v2.3.pkl (45 MB)
│   ├─ Feature config: features.json
│   └─ Preprocessing pipeline: preprocessor.pkl
└─ Validation passed
        │
        ▼
Architect Agent - Infrastructure (5 min)
├─ Generate Terraform for SageMaker
│   ├─ SageMaker endpoint: fraud-detection-v2-3
│   ├─ Instance type: ml.m5.xlarge
│   ├─ Auto-scaling: 2-20 instances (target: 70% CPU)
│   ├─ API Gateway integration
│   ├─ VPC: private subnet only
│   └─ CloudWatch alarms (latency, errors, invocations)
├─ Cost estimate: $858/month
├─ Shadow validation in sandbox ✓
└─ Apply to production
        │
        ▼
MLOps Agent - Shadow Deployment (24 hours)
├─ Deploy model to shadow endpoint
│   └─ Endpoint: fraud-detection-shadow-v2-3
├─ Mirror production traffic (100%)
│   └─ AWS App Mesh (Envoy) traffic mirroring
├─ Collect predictions (both endpoints)
│   ├─ Production (v2.2): 1,234,567 predictions
│   └─ Shadow (v2.3): 1,234,567 predictions
├─ Compare predictions
│   ├─ Prediction diff rate: 2.3% (threshold: 5%) ✓
│   ├─ Average prediction change: 0.04 (fraud score)
│   └─ High-confidence predictions: 98.2% agreement
├─ Monitor performance
│   ├─ Latency: Production 120ms, Shadow 115ms ✓
│   ├─ Throughput: Both at 500 req/sec ✓
│   └─ Errors: Both at 0.01% ✓
└─ After 24 hours: Shadow test passed ✓
        │
        ▼
CI/CD Agent - Canary Deployment (48 hours)
├─ Stage 1: 5% Canary (24 hours)
│   ├─ Update API Gateway: 95% v2.2, 5% v2.3
│   ├─ Monitor metrics (SRE Agent)
│   │   ├─ Fraud detection rate: 4.2% (baseline: 4.0%) ✓
│   │   ├─ False positive rate: 0.8% (baseline: 1.0%) ✓
│   │   └─ Model latency: 118ms (baseline: 120ms) ✓
│   └─ After 24 hours: 5% canary healthy ✓
│
├─ Stage 2: 25% Canary (12 hours)
│   ├─ Update API Gateway: 75% v2.2, 25% v2.3
│   ├─ Monitor metrics
│   └─ After 12 hours: 25% canary healthy ✓
│
├─ Stage 3: 50% Canary (6 hours)
│   ├─ Update API Gateway: 50% v2.2, 50% v2.3
│   ├─ Monitor metrics
│   └─ After 6 hours: 50% canary healthy ✓
│
└─ Stage 4: 100% Rollout (6 hours)
    ├─ Update API Gateway: 100% v2.3
    ├─ Scale down old endpoint (v2.2 → 0 instances)
    └─ After 6 hours: Full rollout stable ✓
        │
        ▼
MLOps Agent - Post-Deployment (ongoing)
├─ Continuous drift monitoring
│   ├─ Prediction drift (KL-divergence)
│   ├─ Concept drift (accuracy degradation)
│   └─ Feature drift (input distribution shift)
├─ Model performance tracking
│   ├─ Collect labeled feedback (actual fraud outcomes)
│   ├─ Compute real accuracy: 93.5% ✓
│   └─ Alert if accuracy drops >5% for 3 consecutive days
└─ Auto-retrain trigger (if needed)
        │
        ▼
PM Dashboard
✅ ML Model Deployment Complete: fraud-detection v2.3 → production
Shadow testing: 24 hours (passed)
Canary rollout: 48 hours (5% → 25% → 50% → 100%)
Total duration: 72 hours
Zero incidents
Model accuracy: 93.5% (production validation)
Latency: 115ms (p95)
[View MLflow Experiment] [View Predictions] [Retrain Model]
```

---

## Application-Specific Flows

### Flow A: Static Website (S3 + CloudFront)

```
PM: "Deploy marketing-site v1.5 to production"
        │
        ▼
NLP Parser → {intent: "deploy_static_website", app: "marketing-site", version: "1.5"}
        │
        ▼
GitHub Actions (3 min)
├─ Build static site (npm run build)
├─ Upload to S3 (aws s3 sync)
├─ Invalidate CloudFront cache
└─ Verify homepage loads
        │
        ▼
✅ Done (3m 12s, $0.05 cost)
```

---

### Flow B: Serverless API (AWS Lambda + API Gateway)

```
PM: "Deploy user-api v2.1 to production"
        │
        ▼
NLP Parser → {intent: "deploy_serverless", app: "user-api", version: "2.1"}
        │
        ▼
Architect Agent (5 min)
├─ Package Lambda function (zip)
├─ Update Lambda function code
├─ Update API Gateway configuration
├─ Deploy to production stage
└─ Warm up Lambda (invoke 10 times)
        │
        ▼
SRE Agent (1 min)
├─ Test API endpoints (/health, /users)
├─ Monitor cold start latency
└─ Verify DynamoDB connection
        │
        ▼
✅ Done (6m 23s, $0.10 cost)
```

---

### Flow C: Database Migration (Blue-Green)

```
PM: "Deploy user-service v3.0 to production with database migration"
        │
        ▼
NLP Parser → {intent: "deploy_with_migration", migration: "0043_add_fraud_score"}
        │
        ▼
Security Agent (5s)
├─ Check migration is reversible
│   └─ ❌ Migration contains "DROP COLUMN legacy_score" (irreversible)
└─ Block deployment, suggest alternatives
        │
        ▼
PM Dashboard
❌ Deployment blocked - Database migration not reversible
Recommendation:
1. Create rollback migration (restore legacy_score column)
2. Or deploy with blue-green + database snapshot

PM: "Deploy with blue-green and database snapshot"
        │
        ▼
Architect Agent (10 min)
├─ Take RDS snapshot (production-db-20260504)
├─ Deploy green environment
├─ Run migration on green database
├─ Test green environment (smoke tests)
├─ Switch traffic (blue → green)
├─ Monitor for 10 minutes
└─ If healthy: Destroy blue; If unhealthy: Rollback to blue
        │
        ▼
✅ Done (25m 45s, $5 cost)
```

---

## Decision Trees & Routing Logic

### Decision Tree 1: Pipeline Selection (GitHub Actions vs Jenkins)

```
                    Deployment Request Received
                             │
                             ▼
                    ┌────────────────────┐
                    │ Compliance Required?│
                    │ (SOX, HIPAA, PCI)   │
                    └─────────┬───────────┘
                              │
                    ┌─────────┴──────────┐
                    │ YES                │ NO
                    ▼                    ▼
            ┌───────────────┐    ┌──────────────────┐
            │ JENKINS       │    │ Environment?      │
            │ (Audit Trail) │    └────────┬──────────┘
            └───────────────┘             │
                                ┌─────────┴──────────┐
                                │ Production         │ Staging
                                ▼                    ▼
                    ┌──────────────────┐    ┌────────────────┐
                    │ Deployment        │    │ GITHUB ACTIONS │
                    │ Strategy?         │    │ (Fast Path)    │
                    └────────┬──────────┘    └────────────────┘
                             │
                ┌────────────┴────────────┐
                │ Canary / Blue-Green     │ Rolling
                ▼                         ▼
        ┌───────────────┐         ┌────────────────┐
        │ JENKINS       │         │ Risk Level?    │
        │ (Advanced)    │         └────────┬───────┘
        └───────────────┘                  │
                                 ┌─────────┴──────────┐
                                 │ Critical           │ Low/Medium
                                 ▼                    ▼
                         ┌───────────────┐   ┌────────────────┐
                         │ JENKINS       │   │ GITHUB ACTIONS │
                         │ (Safety)      │   │ (Fast)         │
                         └───────────────┘   └────────────────┘
```

---

### Decision Tree 2: Deployment Strategy Selection

```
                    Production Deployment Requested
                             │
                             ▼
                    ┌────────────────────┐
                    │ High-risk change?   │
                    │ (Major refactor,    │
                    │  new architecture)  │
                    └─────────┬───────────┘
                              │
                    ┌─────────┴──────────┐
                    │ YES                │ NO
                    ▼                    ▼
            ┌───────────────┐    ┌──────────────────┐
            │ CANARY        │    │ Zero-downtime     │
            │ (90 min)      │    │ absolutely        │
            │ 5→25→50→100%  │    │ required?         │
            └───────────────┘    └────────┬──────────┘
                                           │
                                 ┌─────────┴──────────┐
                                 │ YES                │ NO
                                 ▼                    ▼
                         ┌───────────────┐   ┌────────────────┐
                         │ BLUE-GREEN    │   │ A/B testing or │
                         │ (15 min)      │   │ gradual rollout│
                         │ 0→100%        │   │ needed?        │
                         └───────────────┘   └────────┬───────┘
                                                       │
                                             ┌─────────┴──────────┐
                                             │ YES                │ NO
                                             ▼                    ▼
                                     ┌───────────────┐   ┌────────────────┐
                                     │ FEATURE FLAG  │   │ ML Model?      │
                                     │ (LaunchDarkly)│   └────────┬───────┘
                                     └───────────────┘            │
                                                        ┌─────────┴──────────┐
                                                        │ YES                │ NO
                                                        ▼                    ▼
                                                ┌───────────────┐   ┌────────────┐
                                                │ SHADOW →      │   │ ROLLING    │
                                                │ CANARY        │   │ (10 min)   │
                                                │ (72 hours)    │   │ Cost-eff   │
                                                └───────────────┘   └────────────┘
```

---

### Decision Tree 3: Agent Selection Based on Intent

```
                    NLP Parser Outputs Intent
                             │
                             ▼
                    ┌────────────────────┐
                    │ Intent Type?        │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┬────────────────┐
        │                     │                     │                │
        ▼                     ▼                     ▼                ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌──────────────┐
│ deploy_       │   │ heal_         │   │ train_model / │   │ analyze_     │
│ application   │   │ infrastructure│   │ deploy_model  │   │ build_failure│
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘   └──────┬───────┘
        │                   │                   │                  │
        ▼                   ▼                   ▼                  ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐
│ Agents Needed: │  │ Agents Needed: │  │ Agents Needed: │  │ Agents:      │
│ • CI/CD        │  │ • SRE (primary)│  │ • MLOps (prim) │  │ • CI/CD      │
│ • Architect    │  │ • Architect    │  │ • Architect    │  │ (analyzes    │
│ • Security     │  │ • Security     │  │ • Security     │  │ Jenkins logs │
│ • SRE (if prod)│  │                │  │ • SRE (drift)  │  │ with Claude) │
└────────────────┘  └────────────────┘  └────────────────┘  └──────────────┘
```

---

## Data Flow Diagrams

### Data Flow 1: Command to Execution

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         COMMAND PROCESSING PIPELINE                           │
└──────────────────────────────────────────────────────────────────────────────┘

Step 1: Raw Input
┌─────────────────────────────────────────────────────────────────┐
│ PM Dashboard                                                     │
│ Input: "Deploy fraud detection v2.3 to production with canary"  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  │ HTTP POST /api/v1/commands
                                  │ {
                                  │   "user_id": "pm-123",
                                  │   "command_text": "Deploy fraud detection...",
                                  │   "timestamp": "2026-05-04T14:23:45Z"
                                  │ }
                                  ▼
Step 2: NLP Parsing
┌─────────────────────────────────────────────────────────────────┐
│ api_gateway/parser_routes.py                                    │
│                                                                  │
│ 1. Sanitize input (SQL injection, prompt injection defense)     │
│ 2. Send to Claude Sonnet 4 API                                  │
│    Prompt: "Parse this DevOps command: <command>"               │
│ 3. LangGraph validation                                         │
│ 4. Confidence scoring                                           │
│ 5. Context retrieval (Infrastructure Context Store)             │
│    - Current infra state (what's running)                       │
│    - Past deployments (fraud-detection history)                 │
│    - Recent incidents (any issues with fraud-detection)         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  │ Structured JSON
                                  ▼
Step 3: Intent JSON
┌─────────────────────────────────────────────────────────────────┐
│ {                                                                │
│   "intent": "deploy_ml_model",                                  │
│   "application": "fraud-detection",                             │
│   "model_version": "2.3",                                       │
│   "environment": "production",                                  │
│   "deployment_strategy": "canary",                              │
│   "requires_approval": true,                                    │
│   "risk_level": "critical",                                     │
│   "estimated_duration_minutes": 120,                            │
│   "estimated_cost_usd": 45,                                     │
│   "agents_needed": [                                            │
│     "MLOps", "Architect", "Security", "SRE", "CI/CD"           │
│   ],                                                             │
│   "compliance_requirements": ["sox", "model_approval"],         │
│   "confidence": 0.97                                            │
│ }                                                                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
Step 4: Agent Orchestration
┌─────────────────────────────────────────────────────────────────┐
│ api_gateway/agent_orchestrator.py                               │
│                                                                  │
│ LangGraph Workflow:                                             │
│   SecurityCheckNode → MLOpsValidationNode →                     │
│   ArchitectProvisionNode → CICDDeployNode →                     │
│   SREMonitorNode → ResultAggregationNode                        │
│                                                                  │
│ State Management:                                                │
│   {                                                              │
│     "deployment_id": "fraud-v2.3-20260504-142",                 │
│     "current_stage": "mlops_shadow_deployment",                 │
│     "security_approved": true,                                  │
│     "shadow_test_passed": false,  # In progress                │
│     "infrastructure_ready": false,                              │
│     "deployment_started": false,                                │
│     "errors": []                                                │
│   }                                                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
Step 5: Agent Execution (Parallel)
┌──────────────────────┬───────────────────────┬─────────────────┐
│ Security Agent       │ MLOps Agent           │ Architect Agent │
│                      │                       │                 │
│ OPA Policy Check     │ Model Validation      │ Terraform Gen   │
│ ├─ Model approved? ✓ │ ├─ Retrieve from      │ ├─ SageMaker    │
│ ├─ Bias tested? ✓    │ │   MLflow ✓          │ │   endpoint    │
│ └─ Audit trail ✓     │ ├─ Check drift alerts │ ├─ Auto-scaling │
│                      │ │   ✓                 │ ├─ API Gateway  │
│ Output:              │ ├─ Shadow deploy (24h)│ └─ IAM roles    │
│ {"approved": true}   │ └─ Compare predictions│                 │
│                      │                       │ Output:          │
│                      │ Output:               │ {"infra_ready":  │
│                      │ {"shadow_passed": true│  true}           │
│                      │  "canary_config": {...│                 │
└──────────────────────┴───────────────────────┴─────────────────┘
                                  │
                                  ▼
Step 6: CI/CD Execution
┌─────────────────────────────────────────────────────────────────┐
│ Jenkins Pipeline (PromptOps-ML-Canary-Deploy)                   │
│                                                                  │
│ Triggered with parameters:                                       │
│   APP_NAME: fraud-detection                                      │
│   VERSION: 2.3                                                   │
│   ENVIRONMENT: production                                        │
│   DEPLOYMENT_STRATEGY: canary                                    │
│                                                                  │
│ Stages (90 minutes):                                             │
│   1. Pre-flight checks → 2. Build & test →                      │
│   3. Deploy 5% → 4. Monitor 30 min →                            │
│   5. Deploy 25% → 6. Monitor 30 min →                           │
│   7. Deploy 50% → 8. Monitor 30 min →                           │
│   9. Full rollout → 10. Post-deployment validation              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
Step 7: Real-time Monitoring (SRE Agent)
┌─────────────────────────────────────────────────────────────────┐
│ Every 60 seconds during deployment:                             │
│                                                                  │
│ Prometheus Query → Error rate, Latency, Throughput              │
│ CloudWatch Query → SageMaker metrics (invocations, latency)     │
│                                                                  │
│ Health Check Logic:                                              │
│   if error_rate > baseline + 1%:                                │
│       trigger_rollback()                                         │
│   if latency_p95 > baseline * 1.5:                              │
│       trigger_rollback()                                         │
│   if prediction_drift > 5%:                                      │
│       pause_and_alert()                                          │
│                                                                  │
│ Send update to PM Dashboard:                                     │
│   POST /api/v1/deployments/{id}/status                          │
│   {"stage": "50% canary", "health": "healthy", "metrics": {...}}│
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
Step 8: Result Aggregation
┌─────────────────────────────────────────────────────────────────┐
│ {                                                                │
│   "deployment_id": "fraud-v2.3-20260504-142",                   │
│   "status": "success",                                          │
│   "duration_minutes": 117,                                      │
│   "cost_usd": 43.89,                                            │
│   "downtime_seconds": 0,                                        │
│   "jenkins_build_url": "https://jenkins.../142",                │
│   "audit_trail_url": "s3://sox-audit/.../deployment.json",     │
│   "canary_stages": [                                            │
│     {"percentage": 5, "duration_min": 30, "health": "healthy"}, │
│     {"percentage": 25, "duration_min": 30, "health": "healthy"},│
│     {"percentage": 50, "duration_min": 30, "health": "healthy"},│
│     {"percentage": 100, "health": "healthy"}                    │
│   ],                                                             │
│   "final_metrics": {                                            │
│     "error_rate": 0.14,                                         │
│     "latency_p95_ms": 298,                                      │
│     "throughput_rps": 12450                                     │
│   }                                                              │
│ }                                                                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  │ WebSocket Push
                                  ▼
Step 9: PM Dashboard Update
┌─────────────────────────────────────────────────────────────────┐
│ ✅ Deployment Complete: fraud-detection v2.3 → production       │
│                                                                  │
│ Duration: 117m 32s (30m approval + 87m deployment)              │
│ Cost: $43.89                                                    │
│ Downtime: 0 seconds                                             │
│ Health: Healthy ✓                                               │
│                                                                  │
│ [View Jenkins Build] [View Metrics] [Rollback if Needed]        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Patterns

### Pattern 1: Multi-Agent Collaboration (Model Deployment)

```
Example: "Deploy fraud detection model v2.3 to production"

┌─────────────────────────────────────────────────────────────────┐
│ Sequential Agent Execution with State Handoff                   │
└─────────────────────────────────────────────────────────────────┘

Agent 1: Security Agent (10 seconds)
├─ Input: deployment_request
├─ Process:
│   ├─ Check OPA policies (model_approval_required)
│   ├─ Query model registry (MLflow)
│   └─ Validate compliance (SOX audit trail)
└─ Output:
    ├─ security_approved: true
    ├─ audit_log_id: "SEC-2026-05-04-001"
    └─ approvers: ["data-scientist@co.com", "pm@co.com"]
        │
        ▼
Agent 2: MLOps Agent (24 hours - shadow testing)
├─ Input: deployment_request + security_approval
├─ Process:
│   ├─ Retrieve model from MLflow (fraud-detection v2.3)
│   ├─ Validate model artifacts (pkl file, features.json)
│   ├─ Deploy to shadow endpoint (SageMaker)
│   ├─ Mirror production traffic (100%) for 24 hours
│   ├─ Compare predictions (shadow vs production)
│   └─ Collect performance metrics (latency, throughput)
└─ Output:
    ├─ shadow_test_passed: true
    ├─ prediction_diff_rate: 0.023 (2.3%, threshold: 5%)
    ├─ latency_ms: 115 (prod: 120ms)
    └─ canary_deployment_config: {
        "stages": [5, 25, 50, 100],
        "stage_duration_minutes": 30,
        "rollback_error_threshold": 0.01
      }
        │
        ▼
Agent 3: Architect Agent (5 minutes)
├─ Input: deployment_request + mlops_config
├─ Process:
│   ├─ Generate Terraform for SageMaker endpoint
│   │   ├─ Endpoint name: fraud-detection-prod-v2-3
│   │   ├─ Instance type: ml.m5.xlarge
│   │   ├─ Auto-scaling: min=2, max=20, target=70% CPU
│   │   └─ Network: private subnet, security group
│   ├─ Generate API Gateway config
│   │   ├─ Resource: /predict
│   │   ├─ Integration: SageMaker endpoint
│   │   └─ Stage: production
│   ├─ Cost estimation ($858/month)
│   ├─ Shadow validation (apply in sandbox)
│   └─ Apply to production (terraform apply)
└─ Output:
    ├─ infrastructure_provisioned: true
    ├─ endpoint_url: "https://api.co.com/fraud-detection/predict"
    ├─ endpoint_arn: "arn:aws:sagemaker:...:endpoint/fraud-v2-3"
    └─ api_gateway_stage: "production"
        │
        ▼
Agent 4: CI/CD Agent (90 minutes - canary deployment)
├─ Input: deployment_request + infra_config
├─ Process:
│   ├─ Pipeline Decision: Jenkins (canary required)
│   ├─ Trigger Jenkins job: PromptOps-ML-Canary-Deploy
│   ├─ Monitor job progress (real-time)
│   └─ Canary stages:
│       ├─ 5% canary → Monitor 30 min
│       ├─ 25% canary → Monitor 30 min
│       ├─ 50% canary → Monitor 30 min
│       └─ 100% full rollout
└─ Output:
    ├─ deployment_complete: true
    ├─ jenkins_build_number: 142
    ├─ jenkins_url: "https://jenkins.co.com/job/PromptOps-Canary/142"
    └─ deployment_duration_minutes: 87
        │
        ▼
Agent 5: SRE Agent (continuous monitoring)
├─ Input: deployed_endpoint_config
├─ Process:
│   ├─ Enhanced monitoring for 24 hours
│   ├─ Query Prometheus every 60 seconds
│   │   ├─ Error rate: http_requests_total{status=~"5.."}
│   │   ├─ Latency: http_request_duration_seconds{quantile="0.95"}
│   │   └─ Throughput: rate(http_requests_total[5m])
│   ├─ Query CloudWatch every 60 seconds
│   │   ├─ ModelInvocations
│   │   ├─ ModelLatency
│   │   └─ Model4XXErrors, Model5XXErrors
│   ├─ Drift detection (ongoing)
│   │   ├─ Prediction drift (KL-divergence)
│   │   └─ Concept drift (accuracy degradation)
│   └─ Auto-remediation triggers
│       ├─ High latency → Scale up instances
│       ├─ Memory leak → Restart endpoint
│       └─ Drift detected → Alert PM, prepare retraining
└─ Output (continuous):
    ├─ health_status: "healthy"
    ├─ current_metrics: {
    │     "error_rate": 0.0014,
    │     "latency_p95_ms": 115,
    │     "throughput_rps": 467
    │   }
    └─ drift_alerts: []

┌─────────────────────────────────────────────────────────────────┐
│ Final Result (sent to PM Dashboard)                             │
├─────────────────────────────────────────────────────────────────┤
│ ✅ ML Model Deployment Complete: fraud-detection v2.3           │
│                                                                  │
│ Shadow testing: 24 hours (passed)                               │
│ Canary rollout: 90 minutes (5% → 25% → 50% → 100%)             │
│ Total duration: 25 hours 30 minutes                             │
│ Zero incidents                                                   │
│ Model accuracy: 93.5% (production validation)                   │
│ Latency: 115ms (p95)                                            │
│                                                                  │
│ [View MLflow Experiment] [View Predictions] [Retrain Model]     │
└─────────────────────────────────────────────────────────────────┘
```

---

### Pattern 2: Auto-Remediation Flow (SRE Agent)

```
Incident: High CPU Alert on API Service

┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Alert Detection (60 seconds)                            │
└─────────────────────────────────────────────────────────────────┘

Prometheus Alert Manager
├─ Alert: HighCPUUsage
├─ Service: user-api
├─ Current CPU: 92% (threshold: 80%)
├─ Duration: 5 minutes (sustained)
└─ Severity: warning
        │
        │ Webhook POST /api/v1/incidents/alert
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: SRE Agent Receives Alert                                │
└─────────────────────────────────────────────────────────────────┘

SRE Agent (api_gateway/agents/sre_agent.py)
├─ Parse alert (service: user-api, metric: CPU, value: 92%)
├─ Classify incident type: "resource_exhaustion"
├─ Risk assessment: "medium" (not critical yet)
└─ Decision: Auto-remediate (no human approval needed)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Causal AI Root Cause Analysis (30 seconds)              │
└─────────────────────────────────────────────────────────────────┘

Causal AI Engine
├─ Collect time-series data (last 2 hours)
│   ├─ CPU utilization: steady increase from 40% → 92%
│   ├─ Request rate: 2,000 rps → 8,500 rps (4.25x increase)
│   ├─ Memory usage: 70% → 85% (normal increase)
│   └─ Database query time: 50ms → 180ms (3.6x slower)
│
├─ Correlation analysis
│   ├─ CPU spike correlates with request rate spike (0.95 correlation)
│   ├─ Request rate spike started at 14:15 UTC
│   └─ Source: Marketing campaign launched (email blast to 500k users)
│
└─ Root cause identified: "Traffic spike from marketing campaign"
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Auto-Remediation Action (2 minutes)                     │
└─────────────────────────────────────────────────────────────────┘

SRE Agent Auto-Remediation
├─ Remediation strategy: "scale_horizontally"
├─ Current ECS task count: 5
├─ Target ECS task count: 15 (3x scale-up)
│
├─ Execute:
│   ├─ AWS API call: ecs.update-service(desired-count=15)
│   ├─ Wait for tasks to launch (60 seconds)
│   └─ Wait for ALB health checks to pass (60 seconds)
│
└─ Verify:
    ├─ New task count: 15 ✓
    ├─ CPU utilization: 92% → 35% ✓
    ├─ Request rate distributed: 8,500 rps / 15 tasks = 567 rps/task ✓
    └─ Response time: 180ms → 65ms ✓
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Post-Remediation Monitoring (10 minutes)                │
└─────────────────────────────────────────────────────────────────┘

SRE Agent Monitoring
├─ Monitor metrics for 10 minutes to confirm stability
│   ├─ CPU: 30-35% (stable) ✓
│   ├─ Memory: 70-75% (stable) ✓
│   ├─ Request rate: 8,000-9,000 rps (stable) ✓
│   └─ Error rate: 0.02% (within baseline) ✓
│
└─ Remediation successful
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Auto-Generated RCA Report (2 minutes)                   │
└─────────────────────────────────────────────────────────────────┘

SRE Agent (Claude Sonnet 4)
├─ Generate plain-English RCA (3 sentences):
│
│   "High CPU usage detected on user-api at 14:20 UTC, reaching 92%.
│    Root cause: Marketing campaign launched at 14:15 caused traffic
│    spike from 2,000 to 8,500 requests per second. Auto-remediation
│    scaled ECS tasks from 5 to 15, reducing CPU to 35% within 2 minutes.
│    No user impact observed."
│
├─ Incident duration: 7 minutes (alert → resolution)
├─ MTTR: 2 minutes (detection → remediation)
└─ User impact: None (no errors during incident)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: PM Dashboard Notification                               │
└─────────────────────────────────────────────────────────────────┘

PM Dashboard
┌──────────────────────────────────────────────────────────────┐
│ 🔧 Incident Auto-Resolved: user-api High CPU                 │
│                                                              │
│ Time: 2026-05-04 14:20 UTC → 14:27 UTC (7 minutes)          │
│ Severity: Medium                                             │
│ Auto-remediation: Scaled ECS tasks (5 → 15)                  │
│                                                              │
│ Root Cause Analysis:                                         │
│ "High CPU usage detected on user-api at 14:20 UTC,          │
│  reaching 92%. Root cause: Marketing campaign launched       │
│  at 14:15 caused traffic spike from 2,000 to 8,500          │
│  requests per second. Auto-remediation scaled ECS tasks      │
│  from 5 to 15, reducing CPU to 35% within 2 minutes.        │
│  No user impact observed."                                   │
│                                                              │
│ Metrics:                                                      │
│ • CPU: 92% → 35%                                            │
│ • Latency: 180ms → 65ms                                     │
│ • Error rate: 0.02% (no change)                             │
│                                                              │
│ Action taken: Auto-scaled horizontally (no approval needed)  │
│ User impact: None                                            │
│                                                              │
│ [View Metrics] [View Logs] [Approve Scale-Down]             │
└──────────────────────────────────────────────────────────────┘

PM: No action needed (already resolved)
```

---

## Summary: Complete Flow Coverage

### PromptOps supports ALL these deployment types:

1. **Simple Web App** (GitHub Actions, 6-15 min)
   - Static sites, blogs, marketing pages
   - Rolling deployment, minimal infrastructure

2. **REST API / Microservice** (GitHub Actions or Jenkins, 15-90 min)
   - Node.js, Python, Java, Go services
   - Blue-green or canary deployment

3. **Enterprise Critical System** (Jenkins, 90-120 min)
   - Payment processors, financial services
   - Canary with SOX/PCI compliance
   - Multi-approval workflow

4. **ML Model** (MLOps Agent, 24-72 hours)
   - Training, shadow testing, canary rollout
   - Drift monitoring, auto-retraining

5. **Serverless** (GitHub Actions, 5-10 min)
   - AWS Lambda, Google Cloud Functions
   - Instant deployment, no infrastructure management

6. **Database Migration** (Jenkins, 20-30 min)
   - Blue-green with database snapshot
   - Rollback safety validation

7. **Multi-Region** (Jenkins, 45-60 min)
   - Deploy to AWS, Azure, GCP simultaneously
   - Region-by-region rollout with monitoring

8. **Batch Jobs** (GitHub Actions, 5-10 min)
   - ETL, data pipelines, scheduled tasks
   - AWS Batch, Spot instances

---

**PromptOps — Complete End-to-End Flow Diagram — Version 2.0 — May 2026**  
*This document provides comprehensive flow diagrams for all application deployment types and DevOps workflows.*

**Confidential — Internal Engineering Document**
