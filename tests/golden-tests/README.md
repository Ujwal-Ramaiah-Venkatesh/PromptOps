# Golden Test Commands

## Purpose
50 real-world PM commands that the NLP Parser must parse correctly. This is the permanent regression test suite that gates all Phase 1 progress.

## Exit Criteria
**>92% accuracy** on all 50 golden tests before Phase 2 begins.

## Test Structure
Each test includes:
- `test_id`: Unique identifier
- `pm_input`: Raw PM command text
- `expected_intent_type`: One of 8 categories
- `expected_target_service`: Service being acted upon
- `expected_target_env`: Environment (dev/staging/prod)
- `expected_parameters`: Action-specific params
- `expected_confidence_floor`: Minimum acceptable confidence (default 0.85)
- `notes`: Edge case explanation or rationale

## Coverage Requirements
- All 8 intent categories represented
- All 3 environments (dev, staging, prod)
- Simple commands (1-step)
- Complex commands (multi-step)
- Ambiguous commands (should trigger clarification)
- Edge cases (contradictory, incomplete, unclear)

## Test Categories

### 1. Deploy (8 tests)
- Simple deploy to single environment
- Multi-tier application deployment
- Deploy with specific version/tag
- Deploy with rollback plan

### 2. Scale (8 tests)
- Scale up by absolute number
- Scale down by percentage
- Auto-scaling configuration
- Scale with cost constraints

### 3. Rollback (6 tests)
- Rollback to previous version
- Rollback specific service
- Partial rollback (one tier of multi-tier app)

### 4. Monitor (6 tests)
- Set up basic monitoring
- Create alert rules
- Build dashboard
- Configure log aggregation

### 5. Audit (6 tests)
- Security audit
- Cost audit
- Compliance check
- Access review

### 6. Cost (6 tests)
- Cost analysis for time period
- Cost optimization recommendations
- Budget alert setup

### 7. Security (6 tests)
- Security patching
- IAM policy changes
- Encryption setup
- Vulnerability scan

### 8. Diagnose (4 tests)
- Troubleshoot service outage
- Investigate high latency
- Debug failed deployment
- Root cause analysis

## Running Tests
```bash
# Run all golden tests
npm run test:golden

# Run specific category
npm run test:golden -- --category=deploy

# Run with verbose output
npm run test:golden -- --verbose
```

## Adding New Tests
New tests are added when:
1. Parser fails on a real PM command in production
2. New PM linguistic pattern discovered
3. Edge case not covered by existing tests

Tests are NEVER deleted — only added to.
