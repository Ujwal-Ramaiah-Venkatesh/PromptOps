# Integration & E2E Tests

**Week 11-12 Deliverable**: Comprehensive end-to-end workflow testing.

---

## Overview

Integration tests validate complete user workflows from command input through execution and audit logging.

**Test Coverage:**
- ✅ Staging deployment (no approval)
- ✅ Production deployment (with approval)
- ✅ Scaling with context awareness
- ✅ Drift detection and revert
- ✅ Error handling
- ✅ Audit trail queries

---

## Prerequisites

### 1. Backend Services Running

```bash
# Terminal 1: API Gateway
cd api_gateway
python main.py

# Terminal 2: Context Collector (optional, for drift tests)
cd phase1-nlp/context
python context_collector.py
```

### 2. Database Initialized

```bash
psql -d promptops -f database/schema.sql
```

### 3. Environment Variables

```bash
export ANTHROPIC_API_KEY=your_key_here
export DATABASE_URL=postgresql://promptops:password@localhost:5432/promptops
```

---

## Running Tests

### All Tests

```bash
cd tests/integration
pytest e2e_workflows_test.py -v
```

### Specific Test

```bash
# Deploy to staging
pytest e2e_workflows_test.py::test_deploy_to_staging_workflow -v -s

# Production with approval
pytest e2e_workflows_test.py::test_deploy_to_production_with_approval -v -s

# Error handling
pytest e2e_workflows_test.py::test_error_handling -v -s
```

### By Marker

```bash
# E2E tests only
pytest -m e2e -v

# Slow tests only
pytest -m slow -v

# Quick smoke tests
pytest -m smoke -v
```

### With Output

```bash
# Show print statements
pytest e2e_workflows_test.py -v -s

# Show detailed errors
pytest e2e_workflows_test.py -v --tb=long
```

---

## Test Scenarios

### Scenario 1: Deploy to Staging

**Command**: "Deploy frontend v2.4.0 to staging"

**Steps**:
1. Parse command → intent
2. Decompose → sub-tasks
3. Verify risk level (low/medium)
4. Execute without approval
5. Wait for completion
6. Verify audit log

**Expected**:
- ✓ Intent confidence >0.8
- ✓ 5-8 sub-tasks generated
- ✓ Risk: low or medium
- ✓ Execution completes in <5 min
- ✓ Audit status: completed

---

### Scenario 2: Production Deployment

**Command**: "Deploy api v3.1.0 to production"

**Steps**:
1. Parse command
2. Decompose
3. Verify CRITICAL risk
4. Verify approval required
5. Execute with approval phrase
6. Monitor execution
7. Verify completion and audit

**Expected**:
- ✓ Risk: high or critical
- ✓ Approval required: true
- ✓ Approval phrase validated
- ✓ Execution tracked
- ✓ Audit shows approved_by

---

### Scenario 3: Scale with Context

**Command**: "Scale backend to 10 instances"

**Steps**:
1. Parse command
2. Verify context injection (current count)
3. Decompose
4. Check before/after state
5. Verify rollback plan

**Expected**:
- ✓ Context aware (if collector running)
- ✓ Current state captured
- ✓ Target state defined
- ✓ Rollback plan available

---

### Scenario 4: Drift Detection

**Steps**:
1. Fetch drift events
2. Check auto-fixable
3. Revert drift
4. Verify handled

**Expected**:
- ✓ Drift events returned
- ✓ Revert initiated
- ✓ Drift marked as reverted

**Note**: Requires context collector and actual drift.

---

### Scenario 5: Error Handling

**Tests**:
1. Invalid command (gibberish)
2. Missing parameters
3. Invalid approval phrase
4. Non-existent resource

**Expected**:
- ✓ Low confidence for gibberish
- ✓ Missing params detected
- ✓ 403 for wrong approval phrase
- ✓ 404 for non-existent execution

---

### Scenario 6: Audit Queries

**Tests**:
1. Filter by user
2. Filter by environment
3. Filter by status
4. Pagination
5. CSV export

**Expected**:
- ✓ Filters work correctly
- ✓ Pagination returns different pages
- ✓ CSV export generates valid file

---

## Expected Test Output

```
tests/integration/e2e_workflows_test.py::test_deploy_to_staging_workflow 
============================================================
TEST: Deploy to Staging Workflow
============================================================

[1/6] Parsing command...
✓ Intent parsed: deploy frontend

[2/6] Decomposing into tasks...
✓ Decomposed into 6 sub-tasks

[3/6] Checking risk assessment...
✓ Risk level: MEDIUM (no approval required)

[4/6] Executing deployment...
✓ Execution started: exec-abc123

[5/6] Waiting for execution to complete...
✓ Execution completed: 6/6 tasks

[6/6] Verifying audit log...
✓ Audit log verified: Deploy frontend v2.4.0 to staging

============================================================
✅ TEST PASSED: Deploy to Staging
============================================================
PASSED
```

---

## Test Duration

| Test | Duration | Type |
|------|----------|------|
| Deploy to Staging | ~2-5 min | Slow |
| Production Approval | ~3-6 min | Slow |
| Scale with Context | ~30s | Fast |
| Drift Detection | ~10s | Fast |
| Error Handling | ~5s | Fast |
| Audit Queries | ~2s | Fast |

**Total**: ~10-15 minutes for full suite

---

## Troubleshooting

### Test hangs on execution

**Problem**: `wait_for_execution()` times out

**Cause**: Execution not progressing

**Solution**:
1. Check API Gateway logs
2. Verify ANTHROPIC_API_KEY set
3. Check execution status manually:
   ```bash
   curl http://localhost:8000/api/v1/execution/exec-abc123
   ```

---

### No drift events found

**Problem**: Test skipped with "No drift events available"

**Cause**: Context collector not running or no drift detected

**Solution**:
1. Start context collector
2. Wait for drift detection (15min interval)
3. Or manually trigger drift:
   ```bash
   python phase1-nlp/context/drift_detector.py
   ```

---

### Parse intent fails

**Problem**: 503 Service Unavailable

**Cause**: ANTHROPIC_API_KEY not set

**Solution**:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

---

### Database errors

**Problem**: `psycopg2.OperationalError`

**Cause**: PostgreSQL not running or schema not initialized

**Solution**:
```bash
# Start PostgreSQL
brew services start postgresql@15

# Initialize schema
psql -d promptops -f database/schema.sql
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: promptops
          POSTGRES_USER: promptops
          POSTGRES_PASSWORD: password
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest requests

      - name: Initialize database
        run: psql -h localhost -U promptops -d promptops -f database/schema.sql

      - name: Start API Gateway
        run: |
          cd api_gateway
          python main.py &
          sleep 5

      - name: Run tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd tests/integration
          pytest e2e_workflows_test.py -v --tb=short
```

---

## Adding New Tests

### Template

```python
@pytest.mark.e2e
def test_new_workflow():
    """
    Test description.

    Steps:
    1. ...
    2. ...
    """
    print("\n" + "="*60)
    print("TEST: New Workflow")
    print("="*60)

    # Step 1
    print("\n[1/3] Doing something...")
    # ... test code ...
    print("✓ Step 1 complete")

    # Step 2
    print("\n[2/3] Doing something else...")
    # ... test code ...
    print("✓ Step 2 complete")

    # Step 3
    print("\n[3/3] Verifying...")
    # ... assertions ...
    print("✓ Verified")

    print("\n" + "="*60)
    print("✅ TEST PASSED: New Workflow")
    print("="*60)
```

---

## Coverage Goals

- ✅ Command parsing (all intent types)
- ✅ Task decomposition (low/high risk)
- ✅ Approval workflow (typed confirmation)
- ✅ Execution tracking (status updates)
- ✅ Audit trail (filtering, export)
- ✅ Drift detection (acknowledge, revert)
- ✅ Error handling (4xx, 5xx responses)

---

## Support

- **Logs**: Check `api_gateway` terminal output
- **Debug**: Run with `-v -s --tb=long`
- **Issues**: GitHub Issues

---

**Author**: PromptOps Team  
**Date**: 2026-04-29  
**Status**: Integration Tests Complete
