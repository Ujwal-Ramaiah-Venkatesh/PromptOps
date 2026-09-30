# PromptOps Production Test Case Catalog

**Purpose:** certify PromptOps for new applications and already deployed enterprise applications across AWS, Azure, GCP, Kubernetes, EKS, AKS, and GKE.

**Rule:** a release is green only when all applicable cases are `PASS`. `BLOCKED` requires an explicit environment reason, owner, and rerun date. A skipped test is never reported as passed.

## 1. Test Modes

| Mode | Scope | Mutation policy |
|---|---|---|
| Local contract | Mock cloud APIs, local FastAPI, local Kubernetes fixtures | Safe and repeatable |
| Ephemeral cloud | Disposable AWS account/project/subscription and cluster | Create, mutate, rollback, destroy |
| Enterprise read-only | Existing production accounts and clusters | Discovery and observation only |
| Enterprise controlled-change | Approved staging or maintenance window | Change with approval and rollback |

## 2. Required Test Evidence

Every run must retain:

- Git commit, PromptOps version, test-run ID, environment, provider, region, cluster ID.
- Deployment plan, risk score, approval record, generated manifests, Helm values, and IaC preview.
- API request/response status and correlation ID.
- CI/CD logs, build artifact digest, image scan result, deployment events, and rollout history.
- Metrics before/during/after change, alerts generated, AIOps recommendation, remediation action, and verification.
- Rollback result, final resource inventory, cost estimate, and cleanup confirmation.

## 3. Common Acceptance Rules

- Idempotent: repeating a plan does not duplicate resources or create conflicting workloads.
- Least privilege: credentials are scoped to the selected environment and operation.
- Approval: production mutation requires explicit approval and an approval phrase or signed approval record.
- Rollback: every mutating case has a tested rollback path.
- Observability: every deployment has health, logs, metrics, alerts, and audit events.
- Safety: destructive actions require confirmation, backup evidence, and a maintenance window.
- Reliability: transient cloud/API errors retry with bounded backoff and produce a useful failure reason.
- Cleanup: ephemeral resources are removed and the test proves that removal occurred.

## 4. New Application Test Matrix

### 4.1 Intake, discovery, and planning

| ID | Test | Expected result |
|---|---|---|
| NEW-001 | Register repository and branch | Repository is validated and immutable commit is recorded. |
| NEW-002 | Detect application type | Runtime, Dockerfile, package manager, ports, and health endpoint are detected. |
| NEW-003 | Missing Dockerfile | PromptOps generates or requests a container strategy; no silent deploy. |
| NEW-004 | Missing health endpoint | Plan reports readiness gap and blocks production deployment. |
| NEW-005 | Generate cloud recommendation | AWS, Azure, and GCP options include cost, security, reliability, and operational tradeoffs. |
| NEW-006 | Generate Kubernetes target plan | Target is explicitly EKS, AKS, GKE, or generic Kubernetes. |
| NEW-007 | Invalid region or cluster | Plan fails safely with an actionable correction. |
| NEW-008 | High-risk plan | Production plan requires approval and records risk factors. |

### 4.2 CI/CD pipeline

| ID | Test | Expected result |
|---|---|---|
| NEW-CI-001 | Commit triggers pipeline | Checkout, dependency install, lint, unit tests, build, scan, and artifact stages run. |
| NEW-CI-002 | Unit test failure | Pipeline stops before deployment; artifact is not promoted. |
| NEW-CI-003 | Lint/type failure | Pipeline fails; no continue-on-error for correctness gates. |
| NEW-CI-004 | Dependency vulnerability | Severity policy blocks release at configured threshold. |
| NEW-CI-005 | Build reproducibility | Same lockfiles and commit produce the same image/artifact digest. |
| NEW-CI-006 | Image scan | Critical image findings block promotion. |
| NEW-CI-007 | Artifact signing | Unsigned or untrusted artifact is rejected by deployment policy. |
| NEW-CI-008 | Environment promotion | Dev -> staging -> production requires environment-specific approval. |
| NEW-CI-009 | Pipeline retry | Retry is idempotent and does not duplicate deployment resources. |
| NEW-CI-010 | CI cancellation | Running deployment is safely cancelled or reaches a known terminal state. |

### 4.3 AWS deployment

| ID | Test | Expected result |
|---|---|---|
| NEW-AWS-001 | New S3/static deployment | Bucket, policy, encryption, website/CDN, and DNS plan are correct. |
| NEW-AWS-002 | New ECS/EC2 deployment | Compute, IAM, network, health checks, and logs are provisioned. |
| NEW-AWS-003 | New EKS deployment | EKS cluster/node pools/add-ons are provisioned or an existing target is selected. |
| NEW-AWS-004 | IAM least privilege | Deployment succeeds with scoped role and fails with unauthorized action. |
| NEW-AWS-005 | Deployment failure | Partial resources are recorded and cleanup/rollback plan is generated. |
| NEW-AWS-006 | AWS rollback | Previous artifact or infrastructure version is restored and healthy. |
| NEW-AWS-007 | CloudWatch integration | Metrics, logs, alarms, and dashboard data are available. |

### 4.4 Azure deployment

| ID | Test | Expected result |
|---|---|---|
| NEW-AZ-001 | New resource group/app deployment | Resource group and application resources match approved plan. |
| NEW-AZ-002 | AKS cluster deployment | Cluster identity, network, node pools, policy, and monitoring are configured. |
| NEW-AZ-003 | Workload identity | Pod obtains only its approved Azure permissions. |
| NEW-AZ-004 | Azure Policy violation | Non-compliant resource or image is blocked or alerted according to policy. |
| NEW-AZ-005 | AKS rollback | Workload returns to the previous image/configuration. |
| NEW-AZ-006 | Azure monitoring | Container Insights, logs, metrics, alerts, and activity events are visible. |

### 4.5 GCP deployment

| ID | Test | Expected result |
|---|---|---|
| NEW-GCP-001 | New project/resource deployment | Required APIs, service accounts, network, and resources are validated. |
| NEW-GCP-002 | GKE cluster deployment | Cluster mode, node pools, identity, network policy, and monitoring are configured. |
| NEW-GCP-003 | Workload identity | Kubernetes service account maps only to approved Google service account roles. |
| NEW-GCP-004 | Organization policy violation | Non-compliant deployment is rejected or alerted. |
| NEW-GCP-005 | GKE rollback | Previous workload version is restored and verified. |
| NEW-GCP-006 | Cloud Monitoring integration | Metrics, logs, uptime checks, and alerts are available. |

## 5. Kubernetes Test Matrix

Run for generic Kubernetes, EKS, AKS, and GKE.

| ID | Test | Expected result |
|---|---|---|
| K8S-001 | Cluster discovery | Cluster identity, provider, region, version, status, and endpoint metadata are normalized. |
| K8S-002 | Credential failure | API returns actionable `401/403/503`; no credentials are logged. |
| K8S-003 | Node inventory | Nodes, readiness, capacity, labels, taints, and zones are returned. |
| K8S-004 | Namespace inventory | Namespaces and policy status are returned. |
| K8S-005 | Deployment inventory | Desired, available, unavailable, and updated replicas are returned. |
| K8S-006 | Service/Ingress inventory | Endpoints, ports, ingress class, TLS, and external address are returned. |
| K8S-007 | Pod failure | CrashLoopBackOff, image pull, pending, and OOM states are classified. |
| K8S-008 | Rollout success | Rollout reaches desired replicas and health probes pass. |
| K8S-009 | Rollout timeout | Rollout is paused or rolled back according to policy. |
| K8S-010 | Helm deployment | Chart values are rendered, validated, applied, and recorded. |
| K8S-011 | Manifest deployment | Schema, policy, resource limits, probes, and security context are validated. |
| K8S-012 | HPA/VPA behavior | Scaling signal, bounds, cooldown, and stabilization are verified. |
| K8S-013 | Network policy | Allowed traffic succeeds and prohibited traffic is denied. |
| K8S-014 | Secret handling | Secrets never appear in logs, manifests, or API responses. |
| K8S-015 | Upgrade simulation | Version compatibility and disruption budget checks run before upgrade. |
| K8S-016 | Cluster rollback/restore | Workload and configuration restore from known-good state. |

## 6. Already Deployed Application Matrix

### 6.1 Read-only discovery and import

| ID | Test | Expected result |
|---|---|---|
| LIVE-001 | Discover AWS account | Inventory is complete, timestamped, and scoped to authorized regions. |
| LIVE-002 | Discover Azure subscription | Resource groups, AKS, apps, storage, databases, and policies are inventoried. |
| LIVE-003 | Discover GCP project | GKE, compute, storage, IAM, network, and monitoring resources are inventoried. |
| LIVE-004 | Discover EKS/AKS/GKE | Managed cluster details and workload access capabilities are reported. |
| LIVE-005 | Import existing application | Existing app becomes a managed target without changing resources. |
| LIVE-006 | Detect unmanaged resources | Resources outside desired state are flagged as drift. |
| LIVE-007 | Read-only permission test | Discovery works; mutation endpoints are denied. |

### 6.2 Existing application operations

| ID | Test | Expected result |
|---|---|---|
| LIVE-OPS-001 | Health check | HTTP, readiness, liveness, dependency, and uptime status are collected. |
| LIVE-OPS-002 | Log collection | Application, platform, audit, and Kubernetes logs are searchable. |
| LIVE-OPS-003 | Metrics collection | CPU, memory, latency, traffic, errors, saturation, and cost metrics are collected. |
| LIVE-OPS-004 | Alert routing | Critical alerts reach configured channels with deduplication. |
| LIVE-OPS-005 | SLO breach | Burn-rate alert fires and links to affected service/deployment. |
| LIVE-OPS-006 | Drift remediation plan | PromptOps explains drift and proposes a reversible plan without applying it. |
| LIVE-OPS-007 | Approved remediation | Remediation applies only after approval and emits audit evidence. |
| LIVE-OPS-008 | Failed remediation | Change is rolled back or marked for operator action with full context. |
| LIVE-OPS-009 | Cost anomaly | Cost spike is detected, explained, and linked to resource/change. |
| LIVE-OPS-010 | Security anomaly | Suspicious access, vulnerable image, or policy violation creates an alert. |

## 7. AIOps and Auto-Fix Matrix

| ID | Test | Expected result |
|---|---|---|
| AIOPS-001 | Alert correlation | Related alerts are grouped into one incident. |
| AIOPS-002 | Root-cause suggestion | Recommendation includes evidence, confidence, and affected resources. |
| AIOPS-003 | False-positive suppression | Duplicate/noise alerts are suppressed without hiding critical alerts. |
| AIOPS-004 | Safe auto-fix eligibility | Only allowlisted, reversible, low-risk fixes can auto-run. |
| AIOPS-005 | Approval-required fix | Medium/high/critical fixes pause for human approval. |
| AIOPS-006 | Restart unhealthy workload | Restart runs only within policy and verifies recovery. |
| AIOPS-007 | Scale remediation | Scaling respects limits, budget, cooldown, and approval policy. |
| AIOPS-008 | Rollback remediation | Rollback restores the last healthy version and verifies probes. |
| AIOPS-009 | Fix failure | Failed fix stops retries, preserves evidence, and pages the owner. |
| AIOPS-010 | Auto-fix loop prevention | Same incident cannot trigger an unbounded remediation loop. |
| AIOPS-011 | Auditability | Recommendation, decision, action, actor, timestamps, and result are immutable. |
| AIOPS-012 | Disaster mode | AIOps switches to alert-only mode during provider/API uncertainty. |

## 8. Resilience and Security Cases

- Provider API throttling, timeout, partial outage, and expired token.
- Kubernetes API outage, DNS failure, registry outage, and node failure.
- Duplicate webhook, replayed event, stale event, and out-of-order event.
- Database unavailable, queue unavailable, and WebSocket reconnect.
- Secret rotation during a deployment.
- Concurrent deployments to the same target.
- Unauthorized tenant access and cross-environment access attempts.
- Malicious manifest, privileged container, hostPath, unsigned image, and exposed secret.
- Backup restore, regional failure, and recovery-time objective measurement.

## 9. Release Gates

A production release is approved only when:

1. All applicable `NEW-*`, `LIVE-*`, `K8S-*`, and `AIOPS-*` cases pass.
2. No test is marked passed because it was skipped or blocked.
3. Any blocked live-provider test has an approved exception and expiration date.
4. Rollback and cleanup evidence is attached.
5. Security, cost, monitoring, and audit checks pass.
6. Production mutation occurred only in an approved window.

## 10. Test Run Record

```text
Run ID:
Commit:
PromptOps version:
Test mode: local | ephemeral-cloud | enterprise-read-only | controlled-change
Providers: AWS | Azure | GCP
Clusters: EKS | AKS | GKE | generic Kubernetes
Environment:
Owner:
Start/end time:
Passed:
Failed:
Blocked:
Skipped with reason:
Evidence location:
Release decision:
Approver:
```
