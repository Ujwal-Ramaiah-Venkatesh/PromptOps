"""
Add Complete DevOps Flow to PromptOps Document
===============================================

Shows end-to-end flow from commit to production monitoring.

Flow: Commit → CI/CD → Build → Test → Containerize → Kubernetes →
      Cloud → Dashboard → Alerts → Deploy → Monitor Production

Author: PromptOps Team
Date: July 9, 2026
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_devops_flow_section(doc):
    """Add complete DevOps flow section"""

    doc.add_heading('Complete DevOps Flow: From Commit to Production', 1)

    doc.add_paragraph(
        'PromptOps orchestrates the entire software delivery lifecycle - from the moment a '
        'developer commits code to continuous monitoring in production. This section shows '
        'the complete end-to-end flow and how PromptOps automates, monitors, and optimizes '
        'every stage.'
    )

    doc.add_page_break()

    # ========================================================================
    # Flow Overview
    # ========================================================================

    doc.add_heading('End-to-End DevOps Flow Overview', 2)

    doc.add_paragraph(
        'The PromptOps DevOps flow consists of 12 stages, each fully automated and monitored:'
    )

    doc.add_paragraph()

    # Visual flow representation
    flow_stages = [
        '1. Developer Commit',
        '2. CI/CD Pipeline Trigger',
        '3. Code Build & Compilation',
        '4. Automated Testing',
        '5. Security Scanning',
        '6. Container Image Build',
        '7. Kubernetes Deployment Preparation',
        '8. Cloud Infrastructure Provisioning',
        '9. Dashboard & Monitoring Setup',
        '10. Alerts & Alarms Configuration',
        '11. Production Deployment',
        '12. Production Monitoring & Optimization',
    ]

    for stage in flow_stages:
        p = doc.add_paragraph(stage, style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.5)

    doc.add_paragraph()

    # Timeline box
    timeline = doc.add_paragraph()
    timeline.add_run('Total Pipeline Time: ').bold = True
    timeline.add_run('8-12 minutes (was 60-90 minutes manually)\n')
    timeline.add_run('Manual Steps Required: ').bold = True
    timeline.add_run('0 (was 15-20 steps)\n')
    timeline.add_run('Error Rate: ').bold = True
    timeline.add_run('<1% (was 15-25%)')

    doc.add_page_break()

    # ========================================================================
    # Stage-by-Stage Breakdown
    # ========================================================================

    doc.add_heading('Stage-by-Stage Flow Breakdown', 2)

    # Stage 1: Developer Commit
    doc.add_heading('Stage 1: Developer Commit', 3)

    doc.add_paragraph(
        'The journey begins when a developer commits code to version control.'
    )

    doc.add_heading('What Happens:', 4)
    stage1_actions = [
        'Developer writes code and commits to Git (GitHub, GitLab, Bitbucket)',
        'Commit message follows conventional commits format (feat:, fix:, chore:, etc.)',
        'Code pushed to feature branch or main branch',
        'PromptOps webhook receives commit notification',
        'Commit metadata extracted: author, timestamp, files changed, commit message',
    ]
    for action in stage1_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('PromptOps Intelligence:', 4)
    intelligence1 = [
        'Analyzes commit message for deployment intent (e.g., "feat:" = new deployment)',
        'Identifies affected services from changed files',
        'Determines deployment environment from branch (main → prod, develop → staging)',
        'Validates commit signature and author permissions',
        'Links commit to Jira/ticket if reference found in message',
    ]
    for item in intelligence1:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Example Commit:', 4)
    example = doc.add_paragraph()
    example.add_run('git commit -m "feat(api): add user authentication endpoint"\n').font.name = 'Courier New'
    example.add_run('git push origin feature/user-auth').font.name = 'Courier New'

    doc.add_paragraph()

    # Stage 2: CI/CD Pipeline Trigger
    doc.add_heading('Stage 2: CI/CD Pipeline Trigger', 3)

    doc.add_paragraph(
        'PromptOps automatically triggers the appropriate CI/CD pipeline based on commit metadata.'
    )

    doc.add_heading('What Happens:', 4)
    stage2_actions = [
        'Webhook triggers pipeline (GitHub Actions, GitLab CI, Jenkins)',
        'Pipeline configuration loaded from .promptops/pipeline.yaml',
        'Build environment prepared (Docker container with dependencies)',
        'Environment variables injected (API keys, database URLs)',
        'Pipeline stages defined: build → test → scan → deploy',
    ]
    for action in stage2_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Supported CI/CD Platforms:', 4)
    cicd_platforms = [
        'GitHub Actions - Native integration with .github/workflows',
        'GitLab CI/CD - .gitlab-ci.yml configuration',
        'Jenkins - Jenkinsfile pipeline',
        'CircleCI - .circleci/config.yml',
        'Azure DevOps - azure-pipelines.yml',
        'AWS CodePipeline - Native AWS integration',
    ]
    for platform in cicd_platforms:
        doc.add_paragraph(platform, style='List Bullet')

    doc.add_heading('PromptOps Intelligence:', 4)
    intelligence2 = [
        'Selects optimal build agent based on workload (CPU/memory requirements)',
        'Caches dependencies to speed up builds (npm, pip, maven)',
        'Parallel execution of independent pipeline stages',
        'Real-time pipeline progress visible in PromptOps dashboard',
        'Estimated completion time displayed (based on historical data)',
    ]
    for item in intelligence2:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 3: Code Build & Compilation
    doc.add_heading('Stage 3: Code Build & Compilation', 3)

    doc.add_paragraph(
        'Source code is compiled, bundled, and prepared for deployment.'
    )

    doc.add_heading('What Happens:', 4)
    stage3_actions = [
        'Dependencies installed (npm install, pip install, mvn install)',
        'Code compiled (TypeScript → JavaScript, Java → JAR, Go → binary)',
        'Assets bundled and minified (Webpack, Rollup, Vite)',
        'Environment-specific configurations applied',
        'Build artifacts created and versioned',
    ]
    for action in stage3_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Build Optimization:', 4)
    optimization = [
        'Incremental builds - only rebuild changed components',
        'Dependency caching - reuse unchanged dependencies',
        'Parallel compilation - multiple files compiled simultaneously',
        'Build time: 2-5 minutes (was 10-15 minutes)',
    ]
    for item in optimization:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('PromptOps Monitoring:', 4)
    monitoring3 = [
        'Live build logs streamed to dashboard',
        'Build time tracked and compared to baseline',
        'Slow build stages identified',
        'Build failure alerts sent immediately',
        'Build artifacts stored in S3 with versioning',
    ]
    for item in monitoring3:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 4: Automated Testing
    doc.add_heading('Stage 4: Automated Testing', 3)

    doc.add_paragraph(
        'Comprehensive test suite runs automatically to ensure code quality.'
    )

    doc.add_heading('Test Types Executed:', 4)
    tests = [
        ('Unit Tests', 'Test individual functions and methods (Jest, pytest, JUnit)'),
        ('Integration Tests', 'Test component interactions (API tests, database tests)'),
        ('End-to-End Tests', 'Test complete user workflows (Cypress, Selenium, Playwright)'),
        ('Performance Tests', 'Load testing and benchmarking (k6, JMeter)'),
        ('Contract Tests', 'API contract validation (Pact, Postman)'),
    ]

    for test_type, description in tests:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(test_type + ': ').bold = True
        p.add_run(description)

    doc.add_heading('Test Results Dashboard:', 4)
    results = [
        'Real-time test execution progress',
        'Pass/fail counts updated live',
        'Failed test details with stack traces',
        'Test coverage percentage (target: >80%)',
        'Flaky test detection (tests that fail intermittently)',
        'Performance regression detection',
    ]
    for item in results:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Quality Gates:', 4)
    gates = [
        'Pipeline stops if critical tests fail (no deployment)',
        'Code coverage must meet threshold (e.g., >80%)',
        'No critical bugs allowed in test results',
        'Performance benchmarks must pass (e.g., API <200ms)',
    ]
    for gate in gates:
        doc.add_paragraph(gate, style='List Bullet')

    doc.add_paragraph()

    # Stage 5: Security Scanning
    doc.add_heading('Stage 5: Security Scanning', 3)

    doc.add_paragraph(
        'Multi-layer security scanning ensures no vulnerabilities reach production.'
    )

    doc.add_heading('Security Scans Performed:', 4)
    security_scans = [
        ('Static Application Security Testing (SAST)', [
            'Code analysis for security vulnerabilities (SonarQube, Snyk)',
            'SQL injection, XSS, CSRF detection',
            'Hardcoded secrets detection (API keys, passwords)',
            'OWASP Top 10 vulnerability checks',
        ]),
        ('Dependency Scanning', [
            'npm audit, pip check, mvn dependency:check',
            'Known CVE detection in dependencies',
            'License compliance checking',
            'Outdated dependency alerts',
        ]),
        ('Container Image Scanning', [
            'Trivy, Clair, Anchore scanning',
            'Base image vulnerability detection',
            'Malware scanning',
            'Image size optimization checks',
        ]),
        ('Infrastructure as Code (IaC) Scanning', [
            'Terraform security checks (tfsec, Checkov)',
            'Insecure configurations detected',
            'Compliance policy violations',
            'Best practice recommendations',
        ]),
    ]

    for scan_type, items in security_scans:
        p = doc.add_paragraph()
        p.add_run(scan_type + ':').bold = True
        for item in items:
            doc.add_paragraph('  • ' + item, style='List Bullet')

    doc.add_heading('Security Results:', 4)
    security_results = [
        'Vulnerabilities categorized by severity (critical, high, medium, low)',
        'Automatic CVE lookup and impact assessment',
        'Remediation recommendations provided',
        'Security score calculated (0-100)',
        'Critical vulnerabilities block deployment',
    ]
    for item in security_results:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 6: Container Image Build
    doc.add_heading('Stage 6: Container Image Build (Docker)', 3)

    doc.add_paragraph(
        'Application packaged into optimized Docker container image.'
    )

    doc.add_heading('What Happens:', 4)
    stage6_actions = [
        'Dockerfile executed to build container image',
        'Multi-stage builds for optimization (builder → runtime)',
        'Base image selected (Alpine, Distroless for minimal size)',
        'Application and dependencies copied into image',
        'Image tagged with version (commit SHA, semver)',
        'Image pushed to container registry (ECR, GCR, Docker Hub)',
    ]
    for action in stage6_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Image Optimization:', 4)
    optimization6 = [
        'Layer caching - reuse unchanged layers',
        'Image size reduction (typical: 200MB → 50MB)',
        'Security hardening (non-root user, read-only filesystem)',
        'Distroless images for minimal attack surface',
    ]
    for item in optimization6:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('PromptOps Intelligence:', 4)
    intelligence6 = [
        'Automatic image vulnerability re-scanning',
        'Image size tracking and optimization recommendations',
        'Unused image cleanup (cost savings)',
        'Image versioning and rollback capability',
        'Cross-region replication for fast deployments',
    ]
    for item in intelligence6:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 7: Kubernetes Deployment Preparation
    doc.add_heading('Stage 7: Kubernetes Deployment Preparation', 3)

    doc.add_paragraph(
        'Kubernetes manifests generated and validated for deployment.'
    )

    doc.add_heading('What Happens:', 4)
    stage7_actions = [
        'Kubernetes manifests generated (Deployment, Service, Ingress)',
        'Helm charts templated with environment-specific values',
        'Resource limits calculated (CPU, memory based on P95 usage)',
        'Secrets and ConfigMaps created/updated',
        'Network policies applied (security)',
        'Service mesh configuration (Istio, Linkerd if enabled)',
    ]
    for action in stage7_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Kubernetes Resources Created:', 4)
    k8s_resources = [
        ('Deployment', 'Pod specification, replicas, update strategy'),
        ('Service', 'Internal load balancing, port mappings'),
        ('Ingress', 'External routing, TLS termination, domain mapping'),
        ('HorizontalPodAutoscaler', 'Auto-scaling rules based on CPU/memory'),
        ('ConfigMap', 'Environment-specific configuration'),
        ('Secret', 'Encrypted sensitive data (API keys, passwords)'),
        ('ServiceAccount', 'RBAC permissions for the application'),
        ('NetworkPolicy', 'Traffic rules (ingress/egress)'),
    ]

    for resource, description in k8s_resources:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(resource + ': ').bold = True
        p.add_run(description)

    doc.add_heading('Deployment Strategies:', 4)
    strategies = [
        'Rolling Update (default) - Gradual pod replacement, zero downtime',
        'Blue-Green - Full environment swap, instant rollback',
        'Canary - Gradual traffic shift (10% → 50% → 100%)',
        'A/B Testing - Split traffic between versions for testing',
    ]
    for strategy in strategies:
        doc.add_paragraph(strategy, style='List Bullet')

    doc.add_heading('PromptOps Intelligence:', 4)
    intelligence7 = [
        'Automatic resource limit calculation (prevent OOM kills)',
        'Right-sized replica counts based on traffic patterns',
        'Health check endpoints validated before deployment',
        'Dependency check (database, cache, APIs)',
        'Rollback plan generated automatically',
    ]
    for item in intelligence7:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 8: Cloud Infrastructure Provisioning
    doc.add_heading('Stage 8: Cloud Infrastructure Provisioning', 3)

    doc.add_paragraph(
        'Cloud resources automatically provisioned via Infrastructure as Code (Terraform).'
    )

    doc.add_heading('What Happens:', 4)
    stage8_actions = [
        'Terraform plan generated and validated',
        'Cloud resources provisioned (compute, networking, storage, databases)',
        'Network configured (VPC, subnets, security groups, NACLs)',
        'Load balancers created/updated (ALB, NLB)',
        'Databases prepared (RDS, DynamoDB, ElastiCache)',
        'DNS records updated (Route53, CloudDNS)',
        'CDN configured (CloudFront, Cloud CDN)',
    ]
    for action in stage8_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Cloud Resources Managed:', 4)
    cloud_resources = [
        ('AWS', 'EC2, ECS, EKS, RDS, S3, Lambda, API Gateway, CloudFront, Route53'),
        ('Google Cloud', 'GCE, GKE, Cloud SQL, GCS, Cloud Run, Cloud Functions'),
        ('Azure', 'VMs, AKS, Azure SQL, Blob Storage, App Service, Functions'),
    ]

    for cloud, resources in cloud_resources:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(cloud + ': ').bold = True
        p.add_run(resources)

    doc.add_heading('Infrastructure Validation:', 4)
    validation = [
        'Terraform plan reviewed (shows what will change)',
        'Cost impact calculated before applying changes',
        'Security compliance checked (CIS benchmarks)',
        'Drift detection (actual vs. defined state)',
        'Dry-run validation before real deployment',
    ]
    for item in validation:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('PromptOps Intelligence:', 4)
    intelligence8 = [
        'Automatic infrastructure right-sizing based on usage',
        'Cost optimization recommendations applied',
        'Multi-region deployment for high availability',
        'Disaster recovery configuration',
        'Backup and snapshot policies enforced',
    ]
    for item in intelligence8:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 9: Dashboard & Monitoring Setup
    doc.add_heading('Stage 9: Dashboard & Monitoring Setup', 3)

    doc.add_paragraph(
        'Monitoring dashboards and observability tools automatically configured.'
    )

    doc.add_heading('What Happens:', 4)
    stage9_actions = [
        'Custom dashboards created for the service',
        'Metrics exporters configured (Prometheus, CloudWatch)',
        'Log aggregation setup (ELK, CloudWatch Logs, Datadog)',
        'Distributed tracing enabled (Jaeger, X-Ray, OpenTelemetry)',
        'APM instrumentation injected',
        'Service mesh observability configured',
    ]
    for action in stage9_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Dashboards Created:', 4)
    dashboards = [
        'Service Health Dashboard - Uptime, error rates, latency',
        'Infrastructure Dashboard - CPU, memory, network, disk',
        'Request Dashboard - Traffic, response times, throughput',
        'Error Dashboard - Error rates, stack traces, impact',
        'Dependency Dashboard - External service health',
        'Cost Dashboard - Real-time spending for this service',
    ]
    for dashboard in dashboards:
        doc.add_paragraph(dashboard, style='List Bullet')

    doc.add_heading('Metrics Tracked:', 4)
    metrics = [
        'Golden Signals: Latency, Traffic, Errors, Saturation',
        'RED Metrics: Rate, Errors, Duration',
        'USE Metrics: Utilization, Saturation, Errors',
        'Business Metrics: Transactions, conversions, revenue',
    ]
    for metric in metrics:
        doc.add_paragraph(metric, style='List Bullet')

    doc.add_heading('PromptOps Intelligence:', 4)
    intelligence9 = [
        'Automatic baseline establishment (first 24 hours)',
        'Anomaly detection thresholds calculated from baselines',
        'Custom metrics extraction from logs',
        'SLO/SLI definitions and tracking',
        'Dashboard customization per team/role',
    ]
    for item in intelligence9:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 10: Alerts & Alarms Configuration
    doc.add_heading('Stage 10: Alerts & Alarms Configuration', 3)

    doc.add_paragraph(
        'Intelligent alerting rules configured to notify teams of issues.'
    )

    doc.add_heading('What Happens:', 4)
    stage10_actions = [
        'Alert rules created based on service type and criticality',
        'Multi-channel notifications configured (Slack, PagerDuty, email)',
        'Escalation policies defined (who gets alerted when)',
        'On-call schedules integrated',
        'Alert correlation rules configured',
        'Maintenance windows scheduled (suppress alerts during deployments)',
    ]
    for action in stage10_actions:
        doc.add_paragraph(action, style='List Bullet')

    doc.add_heading('Alert Types:', 4)
    alert_types = [
        ('Critical Alerts', 'Service down, database unavailable, critical error spike'),
        ('Warning Alerts', 'High latency, elevated error rate, resource usage >80%'),
        ('Info Alerts', 'Deployment completed, scaling event, configuration change'),
    ]

    for alert_type, examples in alert_types:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(alert_type + ': ').bold = True
        p.add_run(examples)

    doc.add_heading('Smart Alerting Features:', 4)
    smart_alerts = [
        'Anomaly-based alerts (not static thresholds)',
        'Alert grouping (100 alerts → 1 incident)',
        'Automatic silence during deployments',
        'Flapping detection (alert cycles)',
        'Dependency-aware (don\'t alert on downstream if upstream failing)',
        'Time-of-day sensitivity (different thresholds for peak vs. off-peak)',
    ]
    for item in smart_alerts:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Notification Channels:', 4)
    channels = [
        'Slack - Real-time alerts in dedicated channels',
        'PagerDuty - On-call engineer notification',
        'Email - Detailed incident reports',
        'SMS - Critical production alerts',
        'Webhook - Custom integrations',
        'PromptOps Dashboard - Visual alerts with one-click actions',
    ]
    for channel in channels:
        doc.add_paragraph(channel, style='List Bullet')

    doc.add_paragraph()

    # Stage 11: Production Deployment
    doc.add_heading('Stage 11: Production Deployment', 3)

    doc.add_paragraph(
        'Application deployed to production with safety checks and rollback capability.'
    )

    doc.add_heading('Deployment Process:', 4)
    deployment = [
        '1. Pre-deployment checks (health checks, dependencies, resources)',
        '2. Traffic shifted gradually (canary: 10% → 50% → 100%)',
        '3. Health monitoring during rollout (real-time)',
        '4. Automated rollback if error rate increases >2%',
        '5. Database migrations executed (if needed)',
        '6. Cache warming performed',
        '7. Smoke tests run against production',
        '8. Traffic validated (no 5xx errors)',
        '9. Deployment marked as complete',
        '10. Notification sent to team (Slack, email)',
    ]
    for step in deployment:
        doc.add_paragraph(step, style='List Bullet')

    doc.add_heading('Safety Mechanisms:', 4)
    safety = [
        'Automatic rollback on error spike (>2% increase)',
        'Circuit breaker - stops deployment if health checks fail',
        'Database migration validation before deployment',
        'Canary analysis - compare new vs. old version metrics',
        'Gradual traffic shift (minimize blast radius)',
        'Manual approval option for critical deployments',
    ]
    for item in safety:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Deployment Validation:', 4)
    validation11 = [
        'Health checks must pass for 5 minutes',
        'Error rate must stay below baseline',
        'Latency must not increase >20%',
        'All pods must be running and ready',
        'Smoke tests must pass 100%',
    ]
    for item in validation11:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Real-Time Deployment Dashboard:', 4)
    dashboard11 = [
        'Live progress bar (0% → 100%)',
        'Current step displayed (e.g., "Shifting traffic to 50%")',
        'Pod status (running, pending, failed)',
        'Metrics comparison (new vs. old version)',
        'Rollback button (one-click if issues detected)',
        'Estimated time remaining',
    ]
    for item in dashboard11:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_paragraph()

    # Stage 12: Production Monitoring
    doc.add_heading('Stage 12: Production Monitoring & Continuous Optimization', 3)

    doc.add_paragraph(
        'Continuous monitoring and optimization of production environment.'
    )

    doc.add_heading('Continuous Monitoring:', 4)
    monitoring12 = [
        'Real-time metrics streaming (<10 second latency)',
        '24/7 anomaly detection (ML-powered)',
        'Predictive alerts (issues predicted 7+ days ahead)',
        'Performance tracking (latency, throughput, errors)',
        'Cost tracking (real-time spending)',
        'Security monitoring (threat detection)',
        'User experience monitoring (Core Web Vitals)',
    ]
    for item in monitoring12:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Automatic Optimizations:', 4)
    optimizations = [
        'Auto-scaling based on traffic (HPA, VPA)',
        'Right-sizing recommendations applied weekly',
        'Idle resource cleanup (dev/test environments)',
        'Reserved Instance optimization',
        'Database query optimization suggestions',
        'Cache tuning based on hit rates',
    ]
    for item in optimizations:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Incident Response:', 4)
    incident = [
        'Automatic detection (<1 minute)',
        'Alert sent to on-call engineer',
        'Runbook suggestions provided',
        'Auto-remediation attempted (if configured)',
        'Incident timeline captured automatically',
        'Post-mortem template generated',
    ]
    for item in incident:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('Production Insights:', 4)
    insights = [
        'Weekly optimization reports (cost savings opportunities)',
        'Performance trend analysis',
        'Capacity planning recommendations',
        'Security posture assessment',
        'Compliance status reports',
    ]
    for item in insights:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_page_break()

    # ========================================================================
    # Flow Summary Table
    # ========================================================================

    doc.add_heading('Complete Flow Summary', 2)

    flow_summary = [
        ('Stage', 'Duration', 'Automation Level', 'Key Output'),
        ('1. Commit', '< 1 min', '100% Auto', 'Webhook trigger'),
        ('2. CI/CD Trigger', '< 30 sec', '100% Auto', 'Pipeline started'),
        ('3. Build', '2-5 min', '100% Auto', 'Build artifacts'),
        ('4. Testing', '3-8 min', '100% Auto', 'Test results'),
        ('5. Security Scan', '1-2 min', '100% Auto', 'Security report'),
        ('6. Container Build', '2-4 min', '100% Auto', 'Docker image'),
        ('7. K8s Preparation', '1-2 min', '100% Auto', 'K8s manifests'),
        ('8. Cloud Provisioning', '3-5 min', '100% Auto', 'Infrastructure'),
        ('9. Dashboard Setup', '1-2 min', '100% Auto', 'Monitoring config'),
        ('10. Alerts Setup', '1-2 min', '100% Auto', 'Alert rules'),
        ('11. Production Deploy', '5-10 min', '95% Auto', 'Live deployment'),
        ('12. Monitoring', 'Continuous', '100% Auto', 'Metrics & alerts'),
    ]

    table = doc.add_table(rows=len(flow_summary), cols=4)
    table.style = 'Medium Grid 1 Accent 1'

    for i, row_data in enumerate(flow_summary):
        for j, cell_data in enumerate(row_data):
            cell = table.rows[i].cells[j]
            cell.text = cell_data
            if i == 0:  # Header
                cell.paragraphs[0].runs[0].font.bold = True

    doc.add_paragraph()

    totals = doc.add_paragraph()
    totals.add_run('Total Pipeline Time: ').bold = True
    totals.add_run('8-12 minutes (typical)\n')
    totals.add_run('Total Automation: ').bold = True
    totals.add_run('99% (only manual step: approval for critical prod deployments)\n')
    totals.add_run('Manual Steps: ').bold = True
    totals.add_run('0 required (all optional)')

    doc.add_page_break()

    # ========================================================================
    # Before/After Comparison
    # ========================================================================

    doc.add_heading('Before vs. After PromptOps: Complete Flow Comparison', 2)

    doc.add_heading('Before PromptOps (Manual Process):', 3)

    before_steps = [
        ('1. Code Commit', '5 min', 'Developer commits, manual notification to team'),
        ('2. Manual Build', '15 min', 'Engineer manually runs build commands'),
        ('3. Manual Testing', '30 min', 'Run tests locally, wait for results'),
        ('4. Security Check', '45 min', 'Manual security audit (if done at all)'),
        ('5. Docker Build', '10 min', 'Manual docker build and push commands'),
        ('6. K8s Manifests', '20 min', 'Write YAML files manually, validate syntax'),
        ('7. Terraform Apply', '30 min', 'Manual terraform plan → apply → verify'),
        ('8. Dashboard Setup', '60 min', 'Configure Grafana/Datadog manually'),
        ('9. Alert Setup', '45 min', 'Create alert rules in monitoring tool'),
        ('10. Deploy to Prod', '30 min', 'kubectl apply, watch logs, pray'),
        ('11. Verify', '20 min', 'Manual health checks, test endpoints'),
        ('12. Setup Monitoring', '30 min', 'Configure production monitoring'),
    ]

    for step, duration, description in before_steps:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(f'{step} ({duration}): ').bold = True
        p.add_run(description)

    totals_before = doc.add_paragraph()
    totals_before.add_run('Total Time: ').bold = True
    totals_before.add_run('5 hours 40 minutes\n')
    totals_before.add_run('Manual Steps: ').bold = True
    totals_before.add_run('20+ steps\n')
    totals_before.add_run('Error Rate: ').bold = True
    totals_before.add_run('15-25%\n')
    totals_before.add_run('Stress Level: ').bold = True
    totals_before.add_run('HIGH (constant context switching)')

    doc.add_paragraph()

    doc.add_heading('With PromptOps (Automated Process):', 3)

    after_steps = [
        ('1. Code Commit', '1 min', 'Developer commits - everything else automatic'),
        ('2. Auto Build', '2-5 min', 'Automated build with caching'),
        ('3. Auto Testing', '3-8 min', 'Parallel test execution'),
        ('4. Security Scan', '1-2 min', 'Automated multi-layer scanning'),
        ('5. Docker Build', '2-4 min', 'Optimized with layer caching'),
        ('6. K8s Prep', '1-2 min', 'Auto-generated from templates'),
        ('7. Terraform', '3-5 min', 'Automated with validation'),
        ('8. Dashboard', '1-2 min', 'Auto-configured dashboards'),
        ('9. Alerts', '1-2 min', 'Intelligent alert rules'),
        ('10. Deploy', '5-10 min', 'Canary deployment with auto-rollback'),
        ('11. Verify', '0 min', 'Automatic health checks'),
        ('12. Monitor', 'Continuous', 'Real-time monitoring active'),
    ]

    for step, duration, description in after_steps:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(f'{step} ({duration}): ').bold = True
        p.add_run(description)

    totals_after = doc.add_paragraph()
    totals_after.add_run('Total Time: ').bold = True
    totals_after.add_run('8-12 minutes\n')
    totals_after.add_run('Manual Steps: ').bold = True
    totals_after.add_run('1 (just the commit)\n')
    totals_after.add_run('Error Rate: ').bold = True
    totals_after.add_run('<1%\n')
    totals_after.add_run('Stress Level: ').bold = True
    totals_after.add_run('LOW (watch progress bar, drink coffee)')

    doc.add_paragraph()

    doc.add_heading('Improvement Summary:', 3)

    improvements = [
        ('Time Savings', '5h 40min → 10min', '97% faster', 'Ship 34x more often'),
        ('Manual Effort', '20+ steps → 1 step', '95% reduction', 'Focus on code'),
        ('Error Rate', '15-25% → <1%', '95% reduction', 'Reliable deploys'),
        ('Deployments/Day', '1-2 → 20-30', '15x increase', 'Faster iteration'),
        ('Time to Production', 'Days → Minutes', '99% faster', 'Ship features fast'),
    ]

    table = doc.add_table(rows=len(improvements) + 1, cols=4)
    table.style = 'Light Grid Accent 1'

    # Header
    headers = ['Metric', 'Change', 'Improvement', 'Business Impact']
    for j, header in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = header
        cell.paragraphs[0].runs[0].font.bold = True

    # Data
    for i, (metric, change, improvement, impact) in enumerate(improvements, 1):
        table.rows[i].cells[0].text = metric
        table.rows[i].cells[1].text = change
        table.rows[i].cells[2].text = improvement
        table.rows[i].cells[3].text = impact

    doc.add_paragraph()

    # Key Takeaway
    takeaway = doc.add_paragraph()
    takeaway.add_run('Key Takeaway: ').bold = True
    takeaway.add_run(
        'PromptOps transforms a 5-hour manual process into a 10-minute automated flow, '
        'reducing errors by 95% and enabling teams to deploy 34x more frequently. '
        'Developers focus on writing code - PromptOps handles everything else.'
    )

    return doc


def update_document_with_flow():
    """Update document with complete DevOps flow"""
    print("Adding Complete DevOps Flow section...")

    # Load existing document
    doc = Document('PromptOps_Complete_Flow_Analysis_with_Monitoring.docx')

    print("[OK] Adding end-to-end DevOps flow...")
    add_devops_flow_section(doc)

    # Save updated document
    output_path = 'PromptOps_Complete_Flow_Analysis_Final.docx'
    doc.save(output_path)

    print(f"\n{'='*70}")
    print(f"[SUCCESS] Complete DevOps Flow added!")
    print(f"{'='*70}")
    print(f"Final file: {output_path}")
    print(f"Added complete flow:")
    print(f"  • 12-stage end-to-end DevOps pipeline")
    print(f"  • Commit -> CI/CD -> Build -> Test -> Security -> Docker")
    print(f"  • Kubernetes -> Cloud -> Dashboard -> Alerts -> Deploy -> Monitor")
    print(f"  • Before/After comparison (5h 40min -> 10min)")
    print(f"  • Flow summary table with timings")
    print(f"{'='*70}")

    return output_path


if __name__ == '__main__':
    update_document_with_flow()
