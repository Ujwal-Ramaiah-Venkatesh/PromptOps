# CI/CD Pipeline

**Week 11-12 Deliverable**: GitHub Actions workflow for automated testing and deployment.

---

## Overview

Automated CI/CD pipeline with 10 jobs covering linting, security scanning, testing, building, and deployment.

**Pipeline Flow**:
```
Push to main/develop
    ↓
┌───────────────────────────────────────────┐
│  Lint & Type Check                        │
│  Security Scan                            │
└───────────┬───────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│  Backend Tests                            │
│  Frontend Tests                           │
└───────────┬───────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│  Integration Tests                        │
│  Build Frontend                           │
│  Build Docker Images                      │
└───────────┬───────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│  Deploy to Staging                        │
└───────────┬───────────────────────────────┘
            ↓
    Manual Approval Required
            ↓
┌───────────────────────────────────────────┐
│  Deploy to Production                     │
└───────────────────────────────────────────┘
```

---

## Jobs

### 1. Lint & Type Check

**Runs**: On every push/PR  
**Duration**: ~2 minutes

**Checks**:
- Python: Black, isort, Flake8, Bandit
- TypeScript: ESLint, tsc --noEmit

**Failure means**: Code style violations or type errors

---

### 2. Security Scan

**Runs**: On every push/PR  
**Duration**: ~1 minute

**Checks**:
- Python: pip-audit, Safety
- JavaScript: npm audit

**Failure means**: Known CVEs in dependencies

---

### 3. Backend Unit Tests

**Runs**: On every push/PR  
**Duration**: ~3 minutes

**Environment**:
- PostgreSQL 15 service container
- Python 3.11

**Coverage**: Uploaded to Codecov

---

### 4. Frontend Tests

**Runs**: On every push/PR  
**Duration**: ~2 minutes

**Tests**: Jest + React Testing Library

**Coverage**: Uploaded to Codecov

---

### 5. Integration Tests

**Runs**: On every push/PR (excluding slow tests)  
**Duration**: ~5 minutes

**Setup**:
1. PostgreSQL service
2. API Gateway started
3. E2E workflow tests

**Note**: Slow tests (>30s) skipped in CI

---

### 6. Build Frontend

**Runs**: On main branch only  
**Duration**: ~2 minutes

**Output**: Production-optimized React bundle

**Artifacts**: Uploaded for deployment jobs

---

### 7. Build Docker Images

**Runs**: On main branch only  
**Duration**: ~5 minutes

**Images**:
- `promptops/api-gateway:latest`
- `promptops/api-gateway:<sha>`
- `promptops/context-collector:latest`
- `promptops/context-collector:<sha>`

**Registry**: Docker Hub (requires secrets)

---

### 8. Deploy to Staging

**Runs**: On main branch only  
**Duration**: ~3 minutes

**Steps**:
1. Deploy frontend to S3
2. Invalidate CloudFront cache
3. Update ECS service (force new deployment)
4. Wait for stable deployment
5. Run smoke tests

**Environment**: staging  
**URL**: https://staging.promptops.com

---

### 9. Performance Tests

**Runs**: Nightly (cron) or manual  
**Duration**: ~10 minutes

**Load test**:
- 50 concurrent users
- 10 users/second spawn rate
- 5 minute duration

**Report**: HTML artifact uploaded

---

### 10. Deploy to Production

**Runs**: Main branch with manual approval  
**Duration**: ~3 minutes

**Approval**: GitHub environment protection rules

**Steps**:
1. Manual approval required
2. Deploy frontend to S3
3. Invalidate CloudFront cache
4. Update ECS service
5. Wait for stable deployment
6. Run smoke tests
7. Notify Slack channel

**Environment**: production  
**URL**: https://promptops.com

---

## Required Secrets

### GitHub Secrets

Add these in **Settings → Secrets → Actions**:

#### AWS Credentials
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

#### Docker Hub
```
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password
```

#### Anthropic API
```
ANTHROPIC_API_KEY=sk-ant-...
```

#### CloudFront Distribution IDs
```
CLOUDFRONT_DISTRIBUTION_ID_STAGING=E1234567890ABC
CLOUDFRONT_DISTRIBUTION_ID_PROD=E0987654321XYZ
```

#### Slack Webhook
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## Environment Protection Rules

### Staging

**Settings → Environments → staging**:
- ✅ Required reviewers: None (auto-deploy)
- ⏱️ Wait timer: 0 minutes
- 🔒 Deployment branches: main only

### Production

**Settings → Environments → production**:
- ✅ Required reviewers: 1-2 team leads
- ⏱️ Wait timer: 5 minutes (optional)
- 🔒 Deployment branches: main only
- 🔔 Notifications: Slack webhook

---

## Triggering Workflows

### Automatic Triggers

**On push to main/develop**:
```bash
git push origin main
# Triggers: Full pipeline → Staging deployment
```

**On pull request**:
```bash
gh pr create --base main
# Triggers: Lint, test, build (no deployment)
```

**Nightly (2am UTC)**:
```yaml
# In ci-cd.yml
on:
  schedule:
    - cron: '0 2 * * *'  # Performance tests
```

---

### Manual Triggers

**Via GitHub UI**:
1. Go to **Actions** tab
2. Select **PromptOps CI/CD Pipeline**
3. Click **Run workflow**
4. Select branch
5. Click **Run**

**Via GitHub CLI**:
```bash
gh workflow run ci-cd.yml --ref main
```

---

## Monitoring Workflows

### GitHub UI

**View all runs**:
- https://github.com/YOUR_ORG/PromptOps/actions

**View specific run**:
- Click on workflow run
- Expand jobs to see logs
- Download artifacts

---

### Status Badges

Add to README.md:

```markdown
![CI/CD](https://github.com/YOUR_ORG/PromptOps/actions/workflows/ci-cd.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_ORG/PromptOps/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/PromptOps)
```

---

## Troubleshooting

### Job Failures

#### Lint job fails

**Problem**: Black/ESLint formatting issues

**Solution**:
```bash
# Python
black api_gateway/ phase1-nlp/ phase2-decomposition/
isort api_gateway/ phase1-nlp/ phase2-decomposition/

# TypeScript
cd frontend/dashboard
npm run lint -- --fix
```

---

#### Security scan fails

**Problem**: Vulnerable dependencies

**Solution**:
```bash
# Python
pip-audit --fix

# JavaScript
cd frontend/dashboard
npm audit fix
```

---

#### Tests fail

**Problem**: Test failures or low coverage

**Solution**:
1. Run tests locally: `pytest tests/ -v`
2. Check logs in GitHub Actions
3. Fix failing tests
4. Push fix

---

#### Docker build fails

**Problem**: Missing dependencies or build context

**Solution**:
1. Test build locally:
   ```bash
   docker build -f Dockerfile.api -t test-api .
   ```
2. Check Dockerfile paths
3. Ensure requirements.txt includes all deps

---

#### Deployment fails

**Problem**: AWS credentials or ECS issues

**Solution**:
1. Verify secrets are set in GitHub
2. Check AWS permissions (IAM policy)
3. Verify ECS cluster/service names
4. Check CloudWatch logs for ECS tasks

---

### Debugging Tips

**Enable debug logging**:
```yaml
# In ci-cd.yml job
- name: Debug step
  run: echo "Debug info"
  env:
    ACTIONS_STEP_DEBUG: true
```

**SSH into runner** (for debugging):
```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
```

---

## Performance

### Typical Run Times

| Job | Duration | Can Run Parallel |
|-----|----------|------------------|
| Lint | 2 min | ✅ |
| Security | 1 min | ✅ |
| Backend Tests | 3 min | ✅ |
| Frontend Tests | 2 min | ✅ |
| Integration Tests | 5 min | ❌ (depends on tests) |
| Build Frontend | 2 min | ✅ |
| Build Docker | 5 min | ✅ |
| Deploy Staging | 3 min | ❌ (depends on build) |
| Deploy Production | 3 min | ❌ (manual approval) |

**Total pipeline time** (push to staging): ~15 minutes  
**Total time to production**: ~20 minutes + approval time

---

### Optimization Tips

**1. Cache dependencies**:
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

**2. Use matrix strategy** (parallel Python versions):
```yaml
strategy:
  matrix:
    python-version: [3.10, 3.11]
```

**3. Skip jobs** when not needed:
```yaml
if: contains(github.event.head_commit.message, '[skip ci]')
```

---

## Best Practices

### Commit Messages

**Skip CI for docs**:
```bash
git commit -m "docs: Update README [skip ci]"
```

**Force full CI run**:
```bash
git commit -m "feat: Add feature [ci full]"
```

---

### Branch Protection

**Enable in Settings → Branches → main**:
- ✅ Require status checks to pass
  - lint
  - security
  - test-backend
  - test-frontend
  - test-integration
- ✅ Require branches to be up to date
- ✅ Require pull request reviews (1-2)
- ✅ Dismiss stale reviews
- ✅ Require signed commits (optional)

---

### Notifications

**Slack notifications** on:
- ✅ Production deployments
- ❌ Failed deployments
- ⚠️ Security vulnerabilities

**Add to ci-cd.yml**:
```yaml
- name: Notify failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "❌ CI/CD pipeline failed on ${{ github.ref }}"
      }
```

---

## Rollback Procedure

### Rollback Staging

**Via ECS**:
```bash
aws ecs update-service \
  --cluster promptops-staging \
  --service api-gateway \
  --task-definition api-gateway:<previous-revision>
```

**Via GitHub**:
1. Revert commit: `git revert HEAD`
2. Push: `git push origin main`
3. Wait for auto-deploy

---

### Rollback Production

**Manual approval required**:

1. Identify last good commit:
   ```bash
   git log --oneline
   ```

2. Create rollback PR:
   ```bash
   git revert <bad-commit-sha>
   git push origin rollback-branch
   gh pr create --base main --title "Rollback: Description"
   ```

3. Get approval and merge

4. Or emergency rollback (bypass CI):
   ```bash
   aws ecs update-service \
     --cluster promptops-production \
     --service api-gateway \
     --task-definition api-gateway:<previous-revision>
   ```

---

## Cost Optimization

### GitHub Actions Minutes

**Free tier**: 2,000 minutes/month for private repos

**Estimated usage**:
- Per pipeline run: ~20 minutes
- Daily commits: 5 runs = 100 min/day
- Monthly: ~3,000 minutes

**Recommendation**: Use public repo or upgrade plan

---

### AWS Costs

**S3**: ~$5/month (frontend hosting)  
**CloudFront**: ~$10/month (CDN)  
**ECS**: ~$50/month (2 services)  
**RDS**: ~$30/month (PostgreSQL)  
**Total**: ~$95/month for staging + production

---

## Future Enhancements

1. **Blue-Green Deployment**: Zero-downtime deploys
2. **Canary Releases**: Gradual rollout (10% → 50% → 100%)
3. **Automated Rollback**: Rollback on failed smoke tests
4. **A/B Testing**: Deploy multiple variants
5. **Performance Budgets**: Fail if bundle size increases
6. **Visual Regression Tests**: Screenshot comparison
7. **Load Test Gates**: Block deploy if perf degrades

---

## Support

- **GitHub Actions Docs**: https://docs.github.com/actions
- **Workflow Runs**: https://github.com/YOUR_ORG/PromptOps/actions
- **Slack**: #promptops-deployments

---

**Author**: PromptOps Team  
**Date**: 2026-04-29  
**Status**: CI/CD Pipeline Ready
