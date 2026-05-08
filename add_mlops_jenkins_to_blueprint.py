"""
Script to add MLOps (Phase 5) and Jenkins Hybrid CI/CD (Phase 6) to the main blueprint
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def update_blueprint_with_enhancements():
    """Add Phase 5 (MLOps) and Phase 6 (Jenkins CI/CD) to the main blueprint"""

    print("Reading original blueprint...")
    doc = Document('PromptOps_Development_Blueprint.docx')

    # Update Executive Summary to mention 5-agent architecture
    print("Updating Executive Summary...")
    for para in doc.paragraphs[:20]:  # Check first 20 paragraphs
        if 'Triple-Agent Architecture' in para.text:
            para.text = para.text.replace(
                'Triple-Agent Architecture — the Architect Agent, SRE Agent, and Security Agent',
                'Multi-Agent Architecture — the Architect Agent, SRE Agent, Security Agent, MLOps Agent, and CI/CD Agent'
            )
        if 'April 2026 — January 2027  |  9-Month' in para.text:
            para.text = 'April 2026 — August 2027  |  16-Month End-to-End Roadmap'
        if 'Version 1.0' in para.text:
            para.text = 'Version 2.0  |  Includes MLOps & CI/CD Enhancements'

    # Find the end of Phase 4 content
    print("Finding insertion point after Phase 4...")
    phase4_end_index = None
    for i, para in enumerate(doc.paragraphs):
        if 'Week 38–39' in para.text or 'Phase 4 Deliverables' in para.text:
            phase4_end_index = i + 20  # Add buffer for Phase 4 content

    if not phase4_end_index:
        print("Could not find Phase 4 end marker, appending to end of document")

    # Add page break before Phase 5
    doc.add_page_break()

    print("Adding Phase 5: MLOps Agent...")

    # Phase 5 Title
    heading = doc.add_heading('Phase 5: MLOps Agent — ML Lifecycle Automation', level=1)
    heading.runs[0].font.color.rgb = RGBColor(0, 102, 204)

    doc.add_heading('January 27 — April 18, 2027 | 12 Weeks | Sprint 20–25', level=2)

    # Phase 5 Objective
    doc.add_heading('Phase 5 Objective', level=2)
    objective_text = """Build the MLOps Agent that allows PMs to manage the complete ML lifecycle through plain English commands. By the end of Phase 5, a PM must be able to:
• Train models: "Train a churn prediction model using last 90 days of user data"
• Deploy models: "Deploy the fraud model v2.3 to production with 99.9% SLA"
• Monitor models: "Alert me if the recommendation model accuracy drops below 85%"
• Retrain models: "Retrain the pricing model weekly using the latest transaction data"
"""
    doc.add_paragraph(objective_text)

    # Phase 5 Entry Criteria
    doc.add_heading('Phase 5 Entry Criteria', level=2)
    entry_criteria = [
        'Phase 1–4 complete with all exit criteria met',
        'AWS SageMaker or equivalent ML platform access provisioned',
        'ML Engineer hired or assigned to the project',
        'Sample ML datasets prepared for testing (classification, regression, NLP tasks)',
        'Model registry infrastructure (MLflow or SageMaker Model Registry) set up'
    ]
    for criteria in entry_criteria:
        doc.add_paragraph(f'• {criteria}')

    # Phase 5 Week-by-Week Plan
    doc.add_heading('Phase 5 Week-by-Week Plan', level=2)

    weeks = [
        {
            'title': 'Week 40–41 (Jan 27–Feb 7): ML Intent Parser & Command Library',
            'goal': 'Extend the NLP Parser to understand ML-specific commands and build the ML Command Library.',
            'tasks': [
                'Collect 100+ real ML engineer requests from MLOps forums (Research Lead, Claude Sonnet 4, 3 days)',
                'Classify ML commands into 6 intent categories: train_model, deploy_model, monitor_model, retrain_model, tune_hyperparameters, explain_prediction (ML Engineer, Claude Sonnet 4, 2 days)',
                'Build ML Command Library JSON schema (Backend Engineer, Cursor Agent Mode, 2 days)',
                'Write 30 "golden test" ML commands (QA Engineer, Claude Sonnet 4, 2 days)',
                'Extend LangGraph agent framework with ML-specific nodes (Backend Engineer, LangGraph + Cursor, 3 days)'
            ]
        },
        {
            'title': 'Week 42–43 (Feb 10–21): Model Training Pipeline Generator',
            'goal': 'Build the training pipeline that converts PM commands into executable ML training jobs.',
            'tasks': [
                'Build SageMaker training job generator (ML Engineer, Claude Sonnet 4 + AWS SDK, 4 days)',
                'Implement training data validator using Great Expectations (ML Engineer, 3 days)',
                'Build experiment tracking integration with MLflow (ML Engineer, MLflow SDK, 2 days)',
                'Implement training job cost estimator (Backend Engineer, AWS Pricing API + Claude Sonnet 4, 3 days)',
                'Test: generate training jobs for 5 model types (QA Engineer, Claude Sonnet 4 eval, 3 days)'
            ]
        },
        {
            'title': 'Week 44–45 (Feb 24–Mar 7): Model Deployment & Shadow Testing',
            'goal': 'Deploy models with shadow testing and gradual rollout — no model goes live without validation.',
            'tasks': [
                'Build model deployment pipeline with SageMaker endpoints (ML Engineer, AWS SDK + Terraform, 4 days)',
                'Implement shadow deployment: 24-hour parallel testing (ML Engineer, Python + SageMaker, 3 days)',
                'Build prediction quality comparator (ML Engineer, Python + Claude Sonnet 4, 3 days)',
                'Implement canary deployment: 5% → 25% → 50% → 100% (ML Engineer, AWS SDK + Python, 3 days)',
                'Test: deploy 5 test models through shadow → canary → production pipeline (QA Engineer, AWS Fault Injection, 3 days)'
            ]
        },
        {
            'title': 'Week 46–47 (Mar 10–21): Model Monitoring & Drift Detection',
            'goal': 'Monitor deployed models 24/7 and detect when they need retraining.',
            'tasks': [
                'Build model performance dashboard (Frontend Engineer, Cursor Agent Mode + Grafana, 3 days)',
                'Implement prediction drift detector using KL-divergence (ML Engineer, Evidently AI + Python, 4 days)',
                'Implement concept drift detector (ML Engineer, Evidently AI + Python, 3 days)',
                'Build auto-retrain trigger when drift detected (ML Engineer, LangGraph + AWS SDK, 3 days)',
                'Test drift detection with historical data replay (QA Engineer, Python + historical data, 3 days)'
            ]
        },
        {
            'title': 'Week 48–49 (Mar 24–Apr 4): Hyperparameter Tuning & AutoML',
            'goal': 'Automate model optimization so PMs can say "Find the best hyperparameters for this model."',
            'tasks': [
                'Integrate SageMaker Automatic Model Tuning (ML Engineer, SageMaker Tuning API, 3 days)',
                'Build tuning budget enforcer (Backend Engineer, OPA + AWS Pricing API, 2 days)',
                'Implement AutoML integration (H2O.ai or SageMaker Autopilot) (ML Engineer, 4 days)',
                'Build tuning result explainer (ML Engineer, Claude Sonnet 4, 2 days)',
                'Test: run hyperparameter tuning on 3 different model types (QA Engineer, SageMaker, 3 days)'
            ]
        },
        {
            'title': 'Week 50–51 (Apr 7–18): ML Governance, Model Registry & Explainability',
            'goal': 'Ensure all ML operations are compliant, auditable, and explainable.',
            'tasks': [
                'Build model approval workflow: production requires 2 approvals (ML Engineer, Python + DynamoDB, 3 days)',
                'Implement model registry with versioning (ML Engineer, MLflow Model Registry, 2 days)',
                'Build model explainability integration with SHAP (ML Engineer, SHAP + Python, 3 days)',
                'Implement bias detection (ML Engineer, Fairlearn + Python, 3 days)',
                'Build ML audit trail (Backend Engineer, AWS S3 + DynamoDB, 2 days)',
                'Test: attempt to deploy unapproved model, test bias detection (QA Engineer, 3 days)'
            ]
        }
    ]

    for week_data in weeks:
        doc.add_heading(week_data['title'], level=3)
        doc.add_paragraph(f"Goal: {week_data['goal']}")
        for task in week_data['tasks']:
            doc.add_paragraph(f'• {task}')
        doc.add_paragraph()  # Add spacing

    # Phase 5 AI Tool Summary
    doc.add_heading('Phase 5 AI Tool Summary', level=2)
    ai_tools = [
        ('Claude Sonnet 4', 'ML intent parsing, training config generation, tuning result explanation, cost estimation'),
        ('LangGraph', 'Orchestrates multi-step ML workflows: train → validate → deploy → monitor with state tracking'),
        ('MLflow', 'Experiment tracking and model registry. Logs every training run'),
        ('Evidently AI', 'Drift detection engine. Monitors prediction drift and concept drift in real-time'),
        ('SHAP', 'Model explainability. Generates feature importance and prediction explanations'),
        ('H2O.ai / SageMaker Autopilot', 'AutoML for automated algorithm selection and hyperparameter tuning'),
        ('Great Expectations', 'Training data validation. Checks schema, quality, and anomalies before training'),
        ('Fairlearn', 'Bias detection in training data and model predictions'),
        ('Cursor Agent Mode', 'Builds ML dashboard components and monitoring interfaces')
    ]
    for tool, purpose in ai_tools:
        para = doc.add_paragraph()
        para.add_run(f'{tool}: ').bold = True
        para.add_run(purpose)

    # Phase 5 Deliverables
    doc.add_heading('Phase 5 Deliverables (Exit Criteria)', level=2)
    deliverables = [
        'MLOps Agent correctly parses and executes 30 ML golden test commands with >90% accuracy',
        'Model training pipeline successfully trains 5 different model types',
        'Shadow deployment tested successfully: new models validated against production for 24 hours',
        'Drift detection fires correctly in 90% of simulated drift scenarios',
        'Hyperparameter tuning finds optimal parameters within budget for 3 different model types',
        'Model approval workflow blocks unapproved models from production deployment — 100% of tests',
        'ML audit trail captures every training run, deployment, and prediction decision immutably',
        'Bias detection correctly identifies bias in 3 intentionally biased test datasets',
        'Model explainability (SHAP) generates interpretable explanations for all deployed models'
    ]
    for item in deliverables:
        doc.add_paragraph(f'- {item}')

    # Phase 5 Risks & Mitigations
    doc.add_heading('Phase 5 Risks & Mitigations', level=2)
    risks = [
        ('Model training on wrong dataset', 'Extreme', 'Every training command requires explicit data_source parameter. Data validator checks schema. PM approval for production data.'),
        ('Deployed model has catastrophic accuracy drop', 'Extreme', 'Shadow deployment mandatory for 24 hours. Canary rollout over 48 hours. Real-time accuracy monitoring. Auto-rollback if accuracy drops >10%.'),
        ('Model drift goes undetected', 'High', 'Dual drift detection: prediction drift + concept drift. Alerts fire if either metric degrades for 3 consecutive days.'),
        ('Hyperparameter tuning exhausts budget', 'High', 'Cost ceiling enforced before tuning starts. Max tuning jobs and max cost per session set in OPA policy.'),
        ('Biased model deployed to production', 'Extreme', 'Bias detection runs on every trained model before deployment approval. Models with >15% disparity flagged for manual review.'),
        ('Training data contains PII or sensitive data', 'Extreme', 'Data validator scans for PII patterns before training. Flagged datasets require legal/compliance approval.')
    ]

    # Create table for risks
    table = doc.add_table(rows=1, cols=3)
    header_cells = table.rows[0].cells
    header_cells[0].text = 'Risk / Corner Case'
    header_cells[1].text = 'Severity'
    header_cells[2].text = 'Mitigation Strategy'

    for risk, severity, mitigation in risks:
        row_cells = table.add_row().cells
        row_cells[0].text = risk
        row_cells[1].text = severity
        row_cells[2].text = mitigation

    doc.add_paragraph()  # Add spacing after table

    # Add page break before Phase 6
    doc.add_page_break()

    print("Adding Phase 6: CI/CD Agent (Jenkins Hybrid)...")

    # Phase 6 Title
    heading = doc.add_heading('Phase 6: CI/CD Agent — Jenkins Hybrid Integration', level=1)
    heading.runs[0].font.color.rgb = RGBColor(0, 102, 204)

    doc.add_heading('May 4 — July 27, 2027 | 12 Weeks | Sprint 26–31', level=2)

    # Phase 6 Objective
    doc.add_heading('Phase 6 Objective', level=2)
    objective_text = """Build the CI/CD Agent that allows PMs to deploy applications using plain English commands with intelligent routing between GitHub Actions and Jenkins based on deployment requirements. Implement 6 modern deployment strategies (blue-green, canary, rolling, feature flags, recreate, shadow) with automatic rollback and compliance audit trails.

By the end of Phase 6, a PM must be able to:
• "Deploy fraud-detection v2.3 to production with canary rollout"
• "Roll back the API service to the last stable version"
• "Enable the new checkout feature for 10% of users"
• "Show me why the last Jenkins build failed"
"""
    doc.add_paragraph(objective_text)

    # Phase 6 Entry Criteria
    doc.add_heading('Phase 6 Entry Criteria', level=2)
    entry_criteria = [
        'Phase 1–5 complete with all exit criteria met',
        'Jenkins server provisioned (on-premise or cloud) with admin access',
        'Jenkins plugins installed: Pipeline, Blue Ocean, Git, Docker, Kubernetes',
        'AWS Application Load Balancer configured with two target groups (blue/green)',
        'LaunchDarkly or Split.io account for feature flag management',
        'DevOps Engineer with Jenkins expertise hired or assigned',
        'Compliance requirements documented (SOX, HIPAA, PCI-DSS if applicable)'
    ]
    for criteria in entry_criteria:
        doc.add_paragraph(f'• {criteria}')

    # Phase 6 Week-by-Week Plan
    doc.add_heading('Phase 6 Week-by-Week Plan', level=2)

    weeks_phase6 = [
        {
            'title': 'Week 52–53 (May 4–15): CI/CD Intent Parser & Jenkins Integration Foundation',
            'goal': 'Extend the NLP Parser to understand deployment commands and build the Jenkins API integration layer.',
            'tasks': [
                'Collect 100+ real deployment commands from DevOps forums (Research Lead, Claude Sonnet 4, 3 days)',
                'Classify deployment commands into 8 intent categories (Backend Engineer, Claude Sonnet 4, 2 days)',
                'Build Jenkins REST API client in Python (Backend Engineer, Claude Sonnet 4 + Jenkins API docs, 4 days)',
                'Implement Jenkins authentication with Vault integration (Security Engineer, HashiCorp Vault SDK, 2 days)',
                'Build Pipeline Decision Engine (Backend Engineer, Claude Sonnet 4, 3 days)',
                'Write 30 "golden test" deployment commands (QA Engineer, Claude Sonnet 4, 2 days)',
                'Extend LangGraph with CI/CD-specific nodes (Backend Engineer, LangGraph + Cursor, 3 days)'
            ]
        },
        {
            'title': 'Week 54–55 (May 18–29): Deployment Strategy Implementation — Blue-Green & Canary',
            'goal': 'Implement zero-downtime blue-green and intelligent canary deployments with automatic rollback.',
            'tasks': [
                'Build Blue-Green deployment executor (DevOps Engineer, Terraform + AWS SDK, 5 days)',
                'Implement Canary deployment executor with gradual traffic shift (DevOps Engineer, AWS SDK + CloudWatch, 5 days)',
                'Build deployment health checker (SRE Engineer, Prometheus + CloudWatch, 3 days)',
                'Implement automatic rollback (SRE Engineer, Python + CloudWatch Alarms, 3 days)',
                'Build Jenkins Declarative Pipeline templates (DevOps Engineer, Groovy + Jenkins DSL, 4 days)',
                'Test: run 10 canary deployments with simulated error spikes (QA Engineer, AWS Fault Injection Simulator, 3 days)',
                'Build deployment visualization dashboard (Frontend Engineer, React + D3.js + Cursor, 3 days)'
            ]
        },
        {
            'title': 'Week 56–57 (Jun 1–12): Rolling Deployment, Feature Flags & Shadow Testing',
            'goal': 'Implement cost-efficient rolling deployments, feature flag integration, and shadow testing.',
            'tasks': [
                'Build Rolling deployment executor (DevOps Engineer, AWS SDK + ECS API, 4 days)',
                'Integrate LaunchDarkly for feature flag management (Backend Engineer, LaunchDarkly SDK, 3 days)',
                'Build Feature Flag deployment executor (Backend Engineer, LaunchDarkly SDK, 3 days)',
                'Implement Shadow deployment executor (Backend Engineer, AWS App Mesh (Envoy), 4 days)',
                'Build feature flag dashboard (Frontend Engineer, React + LaunchDarkly UI, 3 days)',
                'Test: deploy 5 applications using rolling strategy (QA Engineer, 3 days)',
                'Test: enable feature for 10% of users, monitor and expand (QA Engineer, LaunchDarkly + Datadog, 2 days)'
            ]
        },
        {
            'title': 'Week 58–59 (Jun 15–26): Build Intelligence — Failure Analysis & Auto-Retry',
            'goal': 'Implement AI-powered build failure analysis and intelligent auto-retry with root cause fixes.',
            'tasks': [
                'Build Jenkins log parser (Backend Engineer, Regex + Python, 3 days)',
                'Implement AI-powered failure analyzer (ML Engineer, Claude Sonnet 4 API, 4 days)',
                'Build intelligent retry engine (Backend Engineer, Python retry logic, 3 days)',
                'Implement failure pattern recognition (ML Engineer, Claude Sonnet 4 + vector DB, 4 days)',
                'Build failure notification system (Backend Engineer, Slack/Email integration, 2 days)',
                'Build build time optimizer (Backend Engineer, Claude Sonnet 4, 3 days)',
                'Test: run 20 intentionally failing builds (QA Engineer, Custom test suite, 3 days)'
            ]
        },
        {
            'title': 'Week 60–61 (Jun 29–Jul 10): Multi-Platform Support & Compliance Pipelines',
            'goal': 'Extend beyond Jenkins to support GitLab CI, Azure DevOps, CircleCI. Build SOC2/ISO27001 compliant pipeline templates.',
            'tasks': [
                'Build GitLab CI integration (Backend Engineer, GitLab API, 4 days)',
                'Build Azure DevOps integration (Backend Engineer, Azure DevOps REST API, 4 days)',
                'Build unified CI/CD abstraction layer (Backend Engineer, Python abstract classes, 3 days)',
                'Build SOC2 compliant pipeline template (Compliance Engineer, Jenkins + OPA, 4 days)',
                'Build HIPAA compliant pipeline template (Compliance Engineer, Jenkins + AWS KMS, 4 days)',
                'Implement change approval workflow (Backend Engineer, ServiceNow REST API, 3 days)',
                'Test: deploy same app through 4 different CI platforms (QA Engineer, Multi-platform test suite, 3 days)'
            ]
        },
        {
            'title': 'Week 62–63 (Jul 13–27): Integration Testing, Documentation & Launch Preparation',
            'goal': 'End-to-end testing of all deployment strategies, compliance validation, documentation, team training.',
            'tasks': [
                'Build comprehensive E2E test suite: 50 test scenarios (QA Engineer, Pytest + Selenium, 5 days)',
                'Run chaos testing on canary deployments (QA Engineer, AWS Fault Injection, 3 days)',
                'Validate compliance pipelines with external auditor (Compliance Engineer, External audit firm, 5 days)',
                'Build PM training dashboard (Frontend Engineer, React + Cursor, 3 days)',
                'Write CI/CD Agent documentation (Technical Writer, Claude Sonnet 4, 4 days)',
                'Conduct team training: 4-hour workshop (Training Lead, Live workshop, 2 days)',
                'Build deployment analytics dashboard (Frontend Engineer, React + Grafana, 3 days)',
                'Security audit: penetration testing (Security Engineer, External pentest firm, 5 days)'
            ]
        }
    ]

    for week_data in weeks_phase6:
        doc.add_heading(week_data['title'], level=3)
        doc.add_paragraph(f"Goal: {week_data['goal']}")
        for task in week_data['tasks']:
            doc.add_paragraph(f'• {task}')
        doc.add_paragraph()  # Add spacing

    # Phase 6 AI Tool Summary
    doc.add_heading('Phase 6 AI Tool Summary', level=2)
    ai_tools_phase6 = [
        ('Claude Sonnet 4', 'Deployment intent parsing, build failure root cause analysis, cost estimation, Jenkins log analysis'),
        ('LangGraph', 'Orchestrates multi-step deployment workflows: decision → deploy → monitor → rollback with state tracking'),
        ('Jenkins', 'Enterprise CI/CD pipeline execution with compliance audit trails'),
        ('GitHub Actions', 'Fast-path CI/CD for simple deployments and feature branches'),
        ('LaunchDarkly', 'Feature flag management for gradual rollout and A/B testing'),
        ('Prometheus + CloudWatch', 'Real-time metrics monitoring during canary stages'),
        ('Terraform', 'Infrastructure provisioning for blue-green environments'),
        ('Cursor Agent Mode', 'Builds CI/CD dashboards, deployment progress visualizations'),
        ('AWS Fault Injection Simulator', 'Chaos testing of canary deployments under failure conditions')
    ]
    for tool, purpose in ai_tools_phase6:
        para = doc.add_paragraph()
        para.add_run(f'{tool}: ').bold = True
        para.add_run(purpose)

    # Phase 6 Deliverables
    doc.add_heading('Phase 6 Deliverables (Exit Criteria)', level=2)
    deliverables_phase6 = [
        'CI/CD Agent parses 30 deployment golden test commands with >90% accuracy',
        'Pipeline Decision Engine correctly routes 100% of test deployments to appropriate platform',
        'Blue-green deployment achieves zero-downtime switchover in 100% of tests',
        'Canary deployment auto-rolls back within 2 minutes of error spike detection (95% accuracy)',
        'Rolling deployment completes without downtime for 10 consecutive tests',
        'Feature flags can be enabled for specific users, then expanded gradually',
        'AI failure analysis identifies root cause for 90% of build failures within 3 minutes',
        'Multi-platform support: same app deploys successfully via GitHub Actions, Jenkins, GitLab CI',
        'SOC2 compliant pipeline receives external auditor approval',
        '50 E2E tests pass with 100% success rate',
        'Canary deployments survive 10 different chaos scenarios without data loss',
        'All PMs trained and certified on CI/CD Agent usage'
    ]
    for item in deliverables_phase6:
        doc.add_paragraph(f'- {item}')

    # Phase 6 Risks & Mitigations
    doc.add_heading('Phase 6 Risks & Mitigations', level=2)
    risks_phase6 = [
        ('Jenkins server unavailable during deployment', 'High', 'Automatic fallback to GitHub Actions. Health check before routing. PM notified of fallback.'),
        ('Canary rollout stalls due to flaky metrics', 'Medium', 'Require 3 consecutive failures before rollback. Smooth metrics over 5-minute window.'),
        ('Blue-green smoke tests fail', 'High', 'Block traffic switch. Preserve Green environment for debugging. Detailed failure report to PM.'),
        ('Deployment approval stuck (approver unavailable)', 'Medium', '4-hour timeout → escalate to backup approvers. Executive escalation after 6 hours.'),
        ('Rollback fails due to incompatible database schema', 'Extreme', 'Pre-deployment schema compatibility check. Block rollback if breaking migrations detected.'),
        ('Two teams deploy same service simultaneously', 'High', 'Redis distributed lock per app+environment. Conflict detection with current deployment details.'),
        ('Jenkins build stuck in queue (resource exhaustion)', 'Medium', 'Monitor queue position. Alert if stuck >2 minutes. Offer GitHub Actions fallback.')
    ]

    # Create table for risks
    table = doc.add_table(rows=1, cols=3)
    header_cells = table.rows[0].cells
    header_cells[0].text = 'Risk / Corner Case'
    header_cells[1].text = 'Severity'
    header_cells[2].text = 'Mitigation Strategy'

    for risk, severity, mitigation in risks_phase6:
        row_cells = table.add_row().cells
        row_cells[0].text = risk
        row_cells[1].text = severity
        row_cells[2].text = mitigation

    doc.add_paragraph()  # Add spacing after table

    # Update Master Timeline
    doc.add_page_break()
    doc.add_heading('Updated Master Timeline at a Glance', level=1)

    timeline_table = doc.add_table(rows=1, cols=4)
    header_cells = timeline_table.rows[0].cells
    header_cells[0].text = 'Phase'
    header_cells[1].text = 'Period'
    header_cells[2].text = 'Duration'
    header_cells[3].text = 'Primary Deliverable'

    timeline_data = [
        ('Phase 1', 'Apr 7 – Jun 27, 2026', '12 weeks', 'NLP Parser + Command Library'),
        ('Phase 2', 'Jun 30 – Sep 26, 2026', '13 weeks', 'Architect Agent (IaC)'),
        ('Phase 3', 'Sep 29 – Nov 21, 2026', '8 weeks', 'SRE Agent (Monitoring)'),
        ('Phase 4', 'Nov 24 – Dec 26, 2026', '5 weeks', 'Chaos Testing + Launch Prep'),
        ('Launch', 'January 2027', '—', 'First customer onboarded'),
        ('Phase 5', 'Jan 27 – Apr 18, 2027', '12 weeks', 'MLOps Agent (ML Lifecycle)'),
        ('Phase 6', 'May 4 – Jul 27, 2027', '12 weeks', 'CI/CD Agent (Jenkins Hybrid)'),
        ('v2.0 Launch', 'August 2027', '—', 'Full DevOps + MLOps + CI/CD Platform')
    ]

    for phase, period, duration, deliverable in timeline_data:
        row_cells = timeline_table.add_row().cells
        row_cells[0].text = phase
        row_cells[1].text = period
        row_cells[2].text = duration
        row_cells[3].text = deliverable

    # Add deployment strategies section
    doc.add_page_break()
    doc.add_heading('Modern Deployment Strategies (Phase 6)', level=1)

    strategies = [
        {
            'name': 'Blue-Green Deployment',
            'description': 'Two identical production environments (Blue = current, Green = new). Traffic switches instantly.',
            'when': 'Zero-downtime deployments required, instant rollback needed',
            'downtime': '0 seconds',
            'duration': '15 minutes',
            'cost': '2x infrastructure (10-15 minutes)'
        },
        {
            'name': 'Canary Deployment',
            'description': 'Gradual rollout: 5% → 25% → 50% → 100% with monitoring at each stage.',
            'when': 'High-risk production changes, user-facing applications',
            'downtime': '0 seconds',
            'duration': '90 minutes',
            'cost': '1.5x infrastructure (90 minutes)'
        },
        {
            'name': 'Rolling Deployment',
            'description': 'Update servers one-by-one or in small batches. No extra infrastructure.',
            'when': 'Cost-sensitive deployments, non-critical applications',
            'downtime': '0 seconds',
            'duration': '10-20 minutes',
            'cost': '1x infrastructure (same as running)'
        },
        {
            'name': 'Feature Flag Deployment',
            'description': 'Deploy code but hide behind flags. Enable for specific users/teams first.',
            'when': 'A/B testing, gradual feature rollout, beta testing',
            'downtime': '0 seconds',
            'duration': 'Variable',
            'cost': '1x infrastructure'
        },
        {
            'name': 'Shadow Deployment',
            'description': 'New version runs alongside production. Receives traffic but responses not served.',
            'when': 'Testing with real production traffic, performance testing',
            'downtime': '0 seconds',
            'duration': '24 hours',
            'cost': '2x infrastructure (24 hours)'
        },
        {
            'name': 'Recreate Deployment',
            'description': 'Shut down all old instances, then start new instances.',
            'when': 'Development/Staging only, breaking changes',
            'downtime': '2-5 minutes',
            'duration': '5-10 minutes',
            'cost': '1x infrastructure'
        }
    ]

    for strategy in strategies:
        doc.add_heading(strategy['name'], level=2)

        para = doc.add_paragraph()
        para.add_run('Description: ').bold = True
        para.add_run(strategy['description'])

        para = doc.add_paragraph()
        para.add_run('When to use: ').bold = True
        para.add_run(strategy['when'])

        para = doc.add_paragraph()
        para.add_run('Downtime: ').bold = True
        para.add_run(strategy['downtime'])

        para = doc.add_paragraph()
        para.add_run('Duration: ').bold = True
        para.add_run(strategy['duration'])

        para = doc.add_paragraph()
        para.add_run('Cost: ').bold = True
        para.add_run(strategy['cost'])

        doc.add_paragraph()  # Spacing

    # Save the updated document
    output_file = 'PromptOps_Development_Blueprint_Complete_v2.docx'
    print(f"Saving updated blueprint as {output_file}...")
    doc.save(output_file)

    print(f"\nSuccessfully updated blueprint!")
    print(f"\nNew file created: {output_file}")
    print(f"\nWhat was added:")
    print(f"   - Phase 5: MLOps Agent (12 weeks, Jan-Apr 2027)")
    print(f"      * 6 weeks of detailed implementation")
    print(f"      * ML training, deployment, monitoring, governance")
    print(f"      * 9 AI tool integrations")
    print(f"      * 9 exit criteria")
    print(f"      * 6 risk mitigations")
    print(f"   - Phase 6: CI/CD Agent - Jenkins Hybrid (12 weeks, May-Jul 2027)")
    print(f"      * 6 weeks of detailed implementation")
    print(f"      * Blue-green, canary, rolling, feature flags deployments")
    print(f"      * Jenkins + GitHub Actions + GitLab + Azure DevOps")
    print(f"      * 9 AI tool integrations")
    print(f"      * 12 exit criteria")
    print(f"      * 7 risk mitigations")
    print(f"   - Updated Master Timeline (Apr 2026 - Aug 2027)")
    print(f"   - 6 Modern Deployment Strategies documented")
    print(f"   - Updated Executive Summary (5-agent architecture)")
    print(f"\nTotal project timeline: 16 months (was 9 months)")
    print(f"Total agents: 5 (was 3)")
    print(f"Total phases: 6 (was 4)")

if __name__ == '__main__':
    try:
        update_blueprint_with_enhancements()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
