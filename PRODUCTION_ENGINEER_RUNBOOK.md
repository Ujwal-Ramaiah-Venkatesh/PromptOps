# PromptOps Production Engineer Runbook

## Purpose

This runbook defines what a production engineer does when PromptOps manages a new application or an application that is already live. It covers CI/CD, deployment, Kubernetes, EKS, AKS, GKE, monitoring, alerting, AIOps, auto-fixing, rollback, security, and evidence.

## Operating Principles

1. Observe before changing an existing production system.
2. Plan before executing.
3. Require approval for production mutations.
4. Use least-privilege identities and short-lived credentials.
5. Make every change reversible.
6. Keep an immutable audit trail.
7. Prefer alert-only mode when provider state is uncertain.
8. Never expose secrets in prompts, logs, manifests, screenshots, or reports.

## 1. Daily Readiness Check

```powershell
# From the repository root
.\.venv\Scripts\Activate.ps1
python -m pytest tests --ignore=tests\performance -q
Push-Location frontend\dashboard
npm test -- --run
npm run build
Pop-Location
```

Confirm:

- Backend health returns `200`.
- CI/CD router is registered.
- Deployment router is registered.
- Kubernetes router is registered.
- Monitoring and AIOps routes are registered.
- Database, queue, metrics, logs, and WebSocket dependencies are healthy.
- No critical alerts are open.
- No unapproved production deployment is running.

## 2. Required Environment Variables

Use secret-manager or CI secret storage. Do not commit values.

```text
PROMPTOPS_API_BASE_URL
JWT_SECRET_KEY
ANTHROPIC_API_KEY
AWS_ROLE_ARN
AWS_REGION
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
AZURE_CLIENT_ID
GCP_PROJECT_ID
GCP_REGION
KUBERNETES_CONTEXT
PROMETHEUS_URL
ALERT_WEBHOOK_URL
```

For live enterprise access, use separate identities for discovery, deployment, monitoring, and remediation.

## 3. New Application Procedure

### 3.1 Intake

1. Record repository URL, commit/branch, owner, business criticality, data classification, RTO, RPO, region, budget, and maintenance window.
2. Run repository detection.
3. Confirm build, tests, Dockerfile, ports, health endpoint, dependencies, and artifact strategy.
4. Select target: AWS, Azure, GCP, generic Kubernetes, EKS, AKS, or GKE.
5. Generate cost, security, reliability, and operations comparison.

### 3.2 Plan Review

1. Inspect the generated infrastructure and deployment plan.
2. Verify network, identity, secrets, encryption, ingress, egress, DNS, backups, and observability.
3. Verify Kubernetes resource requests/limits, probes, security context, PDB, topology spread, and autoscaling.
4. Confirm the plan is idempotent.
5. Confirm rollback and cleanup steps.
6. Assign risk and obtain approval for staging or production as required.

### 3.3 CI/CD Execution

1. Run checkout and dependency installation.
2. Run lint, type checks, unit tests, contract tests, and security scanning.
3. Build the artifact or container image.
4. Generate and store the immutable artifact digest.
5. Sign the artifact and verify the signature.
6. Deploy to development.
7. Run smoke, integration, and security tests.
8. Promote to staging after approval.
9. Run load, failure, rollback, and monitoring tests.
10. Promote to production only after the release gate passes.

### 3.4 Deployment Verification

Verify:

- Deployment status and rollout history.
- Health and readiness probes.
- Logs without secrets or unexpected errors.
- CPU, memory, latency, traffic, and error rate.
- Database and external dependency connectivity.
- Alert rules and notification delivery.
- Audit event with actor, approval, commit, artifact digest, and result.

## 4. Existing Live Application Procedure

### 4.1 Read-Only Discovery

1. Select provider and environment.
2. Verify read-only identity.
3. Discover accounts, subscriptions, projects, regions, resource groups, clusters, namespaces, workloads, storage, databases, IAM, networking, and monitoring.
4. Import the application as a managed target.
5. Record the baseline inventory and timestamp.
6. Do not apply changes during discovery.

### 4.2 Baseline

Capture:

- Current artifact/image digest.
- Current Kubernetes version and node pools.
- Workload replicas, resource requests, limits, and probes.
- Current routes, certificates, DNS, and ingress.
- SLOs, dashboards, alerts, and open incidents.
- Cost by provider, service, resource, and environment.
- Existing drift and unowned resources.

### 4.3 Controlled Change

1. Create a change plan from the baseline.
2. Generate a diff and remediation preview.
3. Review blast radius and rollback path.
4. Obtain owner and change-window approval.
5. Apply the smallest reversible change.
6. Watch rollout, logs, metrics, and alerts.
7. Verify SLOs and dependencies.
8. Close the change only after evidence is attached.

## 5. Kubernetes Operations

### Cluster Discovery

Use the PromptOps Kubernetes API:

```text
GET /api/v1/kubernetes/providers
GET /api/v1/kubernetes/clusters?provider=all
GET /api/v1/kubernetes/clusters/{provider-cluster-id}
GET /api/v1/kubernetes/clusters/{provider-cluster-id}/nodes
GET /api/v1/kubernetes/clusters/{provider-cluster-id}/workloads
```

Cluster IDs are normalized as:

```text
eks:<region>/<cluster>
aks:<resource-group>/<cluster>
gke:<location>/<cluster>
```

### EKS

1. Verify AWS role and region.
2. Verify EKS control-plane status, Kubernetes version, endpoint access, logging, encryption, add-ons, and node groups.
3. Verify IAM roles for service accounts or EKS Pod Identity.
4. Verify VPC, security groups, subnets, NAT, and private endpoint requirements.
5. Verify CloudWatch Container Insights or Prometheus/Grafana integration.
6. For changes, use a maintenance window and PodDisruptionBudgets.

### AKS

1. Verify Entra identity and subscription scope.
2. Verify AKS SKU, node pools, zones, networking, CNI, network policy, and private API configuration.
3. Verify workload identity and Key Vault CSI integration.
4. Verify Azure Policy, Defender for Containers, Container Insights, Managed Prometheus, and Grafana.
5. Verify upgrade channel, maintenance window, and rollback strategy.
6. For changes, preserve system pool capacity and topology spread.

### GKE

1. Verify GCP project, location, service accounts, and required APIs.
2. Verify cluster mode, release channel, node pools, private control plane, network policy, and workload identity.
3. Verify Cloud Logging, Cloud Monitoring, managed Prometheus, and alert policies.
4. Verify Binary Authorization or image policy where required.
5. Verify upgrade, surge, disruption, and rollback settings.
6. For changes, validate quota, regional capacity, and maintenance window.

## 6. Monitoring and Alerting

Every managed application must have:

- Availability and health checks.
- Latency, traffic, errors, and saturation metrics.
- CPU, memory, disk, network, and pod restart metrics.
- Deployment/rollout status.
- Kubernetes API, node, scheduler, and control-plane signals where available.
- Application logs, audit logs, and security events.
- Cost and usage signals.
- Alert routing, deduplication, escalation, and acknowledgement.

### Alert Severity

| Severity | Response |
|---|---|
| Critical | Page immediately; stop risky automation; begin incident process. |
| High | Page owner; investigate within the service objective. |
| Medium | Create work item; monitor trend and schedule remediation. |
| Low/Info | Record and aggregate; no automatic mutation. |

## 7. AIOps and Auto-Fix

### AIOps Decision Flow

```text
Signal -> correlate -> classify -> explain -> recommend -> approve -> act -> verify -> learn
```

Before enabling auto-fix:

1. Confirm the fix is allowlisted.
2. Confirm it is reversible.
3. Confirm resource and budget limits.
4. Confirm cooldown and retry limits.
5. Confirm an owner and notification channel.
6. Confirm audit logging.
7. Run the fix in a disposable or staging environment.

### Safe Auto-Fix Examples

- Restart a failed stateless pod after CrashLoopBackOff classification.
- Roll back a failed deployment to the last healthy artifact.
- Scale within an approved replica range.
- Clear a known-safe cache.
- Re-run a failed idempotent pipeline stage.
- Open a ticket and attach evidence when automation is not safe.

### Human Approval Required

- IAM or RBAC changes.
- Network, firewall, DNS, certificate, or public exposure changes.
- Database schema or data changes.
- Cluster upgrades or node-pool replacement.
- Production scaling beyond budget limits.
- Data deletion or resource termination.
- Security isolation or incident containment with service impact.

## 8. Incident Response

1. Acknowledge the alert.
2. Freeze risky automation if the incident is uncertain.
3. Identify affected provider, cluster, namespace, workload, and dependency.
4. Review recent deployment, drift, cost, and security events.
5. Use AIOps recommendation as evidence, not unquestioned authority.
6. Choose rollback, remediation, scale, failover, or alert-only mode.
7. Execute with approval where required.
8. Verify health, SLOs, logs, and customer impact.
9. Communicate status and next update time.
10. Preserve evidence and write a post-incident review.

## 9. Rollback Procedure

1. Stop further promotion.
2. Identify the last known-good artifact/configuration.
3. Confirm database compatibility and data safety.
4. Generate rollback preview.
5. Obtain approval if production policy requires it.
6. Roll back workload or infrastructure.
7. Verify health probes, metrics, logs, and dependencies.
8. Confirm alerts clear or are understood.
9. Mark the failed release and preserve artifacts.
10. Create follow-up remediation work.

## 10. Security and Compliance

- Use short-lived credentials and workload identity.
- Store secrets only in approved secret managers.
- Enforce MFA and least privilege.
- Scan dependencies and images.
- Block privileged or unsafe Kubernetes manifests.
- Maintain tenant, environment, and provider isolation.
- Log all reads of sensitive inventory and all mutations.
- Retain evidence according to policy.
- Test unauthorized access and secret leakage on every release.

## 11. Cost Controls

1. Set budget and quota limits before provisioning.
2. Track cost by provider, environment, service, cluster, namespace, and workload where possible.
3. Alert on forecast and anomaly thresholds.
4. Review idle nodes, over-provisioned pods, unused disks, public endpoints, and untagged resources.
5. Require approval for scale-up or expensive SKUs.
6. Use spot capacity only for interruptible workloads.
7. Verify cleanup after every ephemeral test.

## 12. Release Sign-Off

The production engineer signs off only when:

- Applicable test catalog cases are all `PASS`.
- No unowned `BLOCKED` or unexpected `SKIPPED` cases remain.
- New and existing application paths have both been tested.
- CI/CD, deployment, Kubernetes, monitoring, alerting, AIOps, and rollback evidence is attached.
- Security and cost gates pass.
- The on-call owner, rollback owner, and escalation contacts are recorded.
- The release has a monitoring window and post-release review time.

## 13. Handoff Checklist

```text
Application:
Owner:
Provider/region:
Cluster/namespace:
Commit/artifact digest:
Deployment window:
SLOs:
Dashboards:
Alert channels:
Rollback command/plan:
AIOps mode: alert-only | approval-required | allowlisted-auto-fix
On-call engineer:
Escalation contact:
Evidence location:
Final approval:
```
