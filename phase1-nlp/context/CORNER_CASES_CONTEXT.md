# Context Layer Corner Cases & Edge Scenarios

**Week 7-8 Documentation**  
**Author:** PromptOps Team  
**Date:** 2026-04-28

---

## Overview

This document catalogs 50+ corner cases for the Context & Memory Layer, covering context freshness, resource conflicts, drift detection edge cases, and AWS API failures.

---

## Categories

1. [Context Freshness](#1-context-freshness)
2. [Resource Not Found](#2-resource-not-found)
3. [Multiple Matches](#3-multiple-matches)
4. [Context Overload](#4-context-overload)
5. [AWS API Failures](#5-aws-api-failures)
6. [Drift False Positives](#6-drift-false-positives)
7. [Multi-Region Resources](#7-multi-region-resources)
8. [Zero Context](#8-zero-context)
9. [Drift During Execution](#9-drift-during-execution)
10. [Cost Optimization](#10-cost-optimization)

---

## 1. Context Freshness

### 1.1 Stale Context (>20 minutes old)

**Scenario:** Context snapshot is 25 minutes old, but PM expects current state.

**Example:**
```
PM Command: "Scale frontend to 10"
Context: frontend @ 5 instances (collected 25 mins ago)
Reality: frontend currently @ 8 instances (manual scale happened)
```

**Handling:**
- Show context age in UI: "Context: 25 mins old"
- Warning if >15 minutes: "⚠️ Context may be stale"
- Trigger immediate refresh if >30 minutes
- Validate current state before execution

**Test:**
```python
def test_stale_context():
    # Create 25-minute-old snapshot
    old_snapshot = create_snapshot(timestamp=now - timedelta(minutes=25))
    
    # Parse should warn
    result = parser.parse_with_context(command)
    assert 'stale_context_warning' in result['warnings']
```

---

### 1.2 Context Changes During Parsing

**Scenario:** Resource state changes while PM is reviewing task preview.

**Example:**
```
T0: PM issues "Scale to 10"
T1: Context shows 5 instances
T2: Manual scale to 7 happens
T3: PM approves (expects 5→10, but actually 7→10)
```

**Handling:**
- Re-validate context before execution
- Show diff: "Context changed: 5→7 instances detected"
- Require re-approval if drift detected
- Lock resource during execution

**Implementation:**
```python
def execute_with_validation(task):
    current_state = fetch_current_state(task.resource_id)
    if current_state != task.assumed_state:
        return ValidationError("Resource state changed since approval")
```

---

### 1.3 No Recent Context Available

**Scenario:** Polling service down, last snapshot is 2 hours old.

**Handling:**
- Display prominent warning
- Offer to trigger immediate refresh
- Disable auto-fill of current values
- Require manual confirmation

---

## 2. Resource Not Found

### 2.1 Service Doesn't Exist in Context

**Scenario:** PM references a service that isn't in context store.

**Example:**
```
PM: "Deploy new-service v1.0"
Context: [frontend, api, worker]  # new-service not tracked
```

**Handling:**
- Parse still succeeds (don't block new services)
- Warning: "Service 'new-service' not found in context"
- Suggestion: "Is this a new service? Context will update after deployment."
- Disable smart defaults (no current state to reference)

**Test:**
```python
def test_unknown_service():
    result = parser.parse("Deploy unknown-service")
    assert result.success == True
    assert 'unknown_service_warning' in result.warnings
```

---

### 2.2 Deleted Resource Still in Snapshot

**Scenario:** Resource was deleted manually, but snapshot hasn't updated yet.

**Example:**
```
Context: staging-frontend (deleted 10 mins ago)
Snapshot: Still shows staging-frontend @ 3 instances
PM: "Scale staging-frontend to 5"
```

**Handling:**
- Detect via AWS API call before execution
- Error: "Resource deleted externally (not found in AWS)"
- Suggest: "Remove from context or trigger refresh"
- Next poll will mark as deleted

---

### 2.3 Resource Name Changed

**Scenario:** Service renamed externally (frontend → web-app).

**Handling:**
- Detect as: 1 deleted resource + 1 new resource
- Drift report shows both events
- Manual mapping required (can't auto-detect renames)

---

## 3. Multiple Matches

### 3.1 Ambiguous Service Name

**Scenario:** "frontend" matches multiple resources.

**Example:**
```
Context:
- frontend-prod (us-east-1, 10 instances)
- frontend-staging (us-east-1, 3 instances)
- frontend-prod (eu-west-1, 8 instances)

PM: "Scale frontend to 15"
```

**Handling:**
- **Strategy 1:** Prioritize production over staging
- **Strategy 2:** If multiple prod, require disambiguation
- **Strategy 3:** Show options to PM

**Implementation:**
```python
def disambiguate_resources(matches):
    # Priority: production > staging > development
    if len(prod_matches) == 1:
        return prod_matches[0]
    else:
        return AmbiguityError(f"Multiple matches: {[m.id for m in matches]}")
```

---

### 3.2 Same Service in Multiple Regions

**Scenario:** Multi-region deployment.

**Example:**
```
Context:
- frontend-prod-us-east-1 @ 10 instances
- frontend-prod-eu-west-1 @ 8 instances

PM: "Scale frontend to 15"
```

**Handling:**
- Default: Apply to all regions (if not specified)
- OR: Require region specification
- Show intent: "Will scale in 2 regions: us-east-1, eu-west-1"
- Confirmation required for multi-region ops

---

### 3.3 Service Name Substring Match

**Scenario:** "api" matches "api", "payment-api", "external-api".

**Handling:**
- Prioritize exact matches
- If no exact match, show all partial matches
- Require confirmation for ambiguous matches

---

## 4. Context Overload

### 4.1 Too Many Resources (>100)

**Scenario:** Large AWS account with 200+ tracked resources.

**Handling:**
- Filter by relevance (service name matching)
- Limit to top 10 most relevant resources
- Token budget enforcement (<2000 tokens)
- Summarize instead of full details

**Trimming Strategy:**
```python
def trim_context(resources, max_resources=10):
    # Score by relevance
    scored = [(score_relevance(r, pm_command), r) for r in resources]
    sorted_resources = sorted(scored, reverse=True)
    return [r for score, r in sorted_resources[:max_resources]]
```

---

### 4.2 Context Exceeds Token Budget

**Scenario:** 15 relevant resources = 3500 tokens (exceeds 2000 limit).

**Handling:**
- Prioritize: exact matches > dependencies > same environment
- Trim least relevant resources
- Show warning: "Context trimmed (15 → 8 resources)"
- Include summary: "8 resources shown, 7 omitted"

---

### 4.3 Deep Dependency Chains

**Scenario:** Service A depends on B, B depends on C, C depends on D...

**Handling:**
- Limit dependency depth to 2 levels
- Show transitive dependencies only if critical
- Summarize deep chains: "frontend → 5 dependencies"

---

## 5. AWS API Failures

### 5.1 Throttling During Collection

**Scenario:** AWS API rate limit exceeded (5 requests/sec).

**Handling:**
- Exponential backoff: 1s → 2s → 4s → 8s
- Batch requests where possible
- Partial results: "Collected 45/50 resource types"
- Retry failed resource types

**Implementation:**
```python
def collect_with_retry(collector, max_retries=3):
    for attempt in range(max_retries):
        try:
            return collector.fetch()
        except ThrottlingException:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
    return PartialResult(error="Throttled")
```

---

### 5.2 Network Timeout

**Scenario:** AWS API call times out after 30 seconds.

**Handling:**
- Fail gracefully: continue with other resource types
- Log error: "EC2 collection timed out"
- Show in snapshot errors: `{resource_type: 'ec2', error: 'timeout'}`
- Next poll will retry

---

### 5.3 Insufficient IAM Permissions

**Scenario:** Missing `ecs:DescribeServices` permission.

**Handling:**
- Detect via `AccessDeniedException`
- Skip that resource type
- Log warning: "ECS collection skipped (permission denied)"
- Show in UI: "⚠️ Partial context (missing ECS permissions)"

**Required Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "ecs:List*",
      "ecs:Describe*",
      "ec2:Describe*",
      "rds:Describe*",
      "lambda:List*",
      "lambda:Get*",
      "elasticloadbalancing:Describe*"
    ],
    "Resource": "*"
  }]
}
```

---

### 5.4 AWS Service Outage

**Scenario:** ECS API is down (503 Service Unavailable).

**Handling:**
- Detect and log
- Use cached context (previous snapshot)
- Warning: "Using cached context (AWS API unavailable)"
- Retry on next poll cycle

---

## 6. Drift False Positives

### 6.1 ECS Task Restarts (Expected)

**Scenario:** ECS tasks restart normally, causing transient `pending_count` changes.

**Example:**
```
T0: running=5, pending=0
T1: running=4, pending=1  # Task restarting
T2: running=5, pending=0  # Restart complete
```

**Handling:**
- Ignore transient `pending_count` changes
- Only alert if sustained >5 minutes
- Mark field as "expected_transient" in config

**Configuration:**
```python
EXPECTED_CHANGES = {
    'ecs_service': {
        'pending_count',  # Ignore short-term changes
        'running_count'   # Only alert if >10% change
    }
}
```

---

### 6.2 Auto-Scaling Events

**Scenario:** Auto-scaler increases instances from 5 → 7.

**Handling:**
- Detect change source: `auto_scaling`
- Severity: `info` (not warning)
- Don't alert (expected behavior)
- Log for audit: "Auto-scaled 5 → 7 (within policy)"

---

### 6.3 Scheduled Maintenance Windows

**Scenario:** Database backup changes `status` to `backing-up`.

**Handling:**
- Whitelist expected maintenance states
- Check schedule: if within maintenance window, don't alert
- Log: "Expected backup operation"

---

### 6.4 Tag Changes (Low Priority)

**Scenario:** Someone updates `CostCenter` tag.

**Handling:**
- Severity: `info`
- Don't alert unless critical tags (`Environment`, `Managed`)
- Group multiple tag changes into single event

---

## 7. Multi-Region Resources

### 7.1 Same Service, Different Regions

**Scenario:** `frontend-prod` in us-east-1 and eu-west-1.

**Handling:**
- Store with region-specific IDs
- Parse command: default to all regions or prompt for region
- Execution: apply to specified region(s) only
- Drift: detect per-region independently

---

### 7.2 Cross-Region Dependencies

**Scenario:** us-east-1 frontend → eu-west-1 database.

**Handling:**
- Track cross-region dependencies in context
- Validate before execution
- Warning: "Cross-region dependency detected"

---

### 7.3 Region-Specific Drift

**Scenario:** us-east-1 has drift, eu-west-1 doesn't.

**Handling:**
- Report drift per-region
- UI shows: "us-east-1: 3 drift events | eu-west-1: No drift"
- Allow per-region acceptance

---

## 8. Zero Context

### 8.1 No Resources Tagged

**Scenario:** Fresh AWS account, no resources with `Managed=PromptOps`.

**Handling:**
- Parser works without context (backward compatible)
- Show notice: "No context available. Tag resources to enable smart features."
- Instructions: `aws ecs tag-resource --resource-arn arn:... --tags Managed=PromptOps`

---

### 8.2 First-Time Setup

**Scenario:** PromptOps just installed.

**Handling:**
- Run initial discovery scan
- Suggest: "Tag existing resources to import context"
- Offer bulk tagging tool

---

## 9. Drift During Execution

### 9.1 Resource State Changes Mid-Execution

**Scenario:** Task plan assumes 5 instances, but manual scale to 7 happens during execution.

**Handling:**
- **Strategy 1:** Validate before each sub-task
- **Strategy 2:** Lock resource during execution
- **Strategy 3:** Abort if drift detected mid-execution

**Implementation:**
```python
def execute_subtask(subtask):
    current_state = get_current_state(subtask.resource_id)
    if current_state != subtask.assumed_state:
        if subtask.drift_tolerance == 'abort':
            raise DriftError("State changed during execution")
        elif subtask.drift_tolerance == 'adapt':
            subtask.update_assumptions(current_state)
```

---

### 9.2 Concurrent Executions

**Scenario:** Two PMs issue overlapping commands.

**Example:**
```
PM1: "Scale frontend to 10"
PM2: "Scale frontend to 8"
Both execute simultaneously
```

**Handling:**
- Resource locking (distributed lock via DynamoDB)
- Queue commands serially
- Detect conflict: "Another operation in progress"

---

## 10. Cost Optimization

### 10.1 Minimize AWS API Calls

**Scenario:** Frequent polling → high AWS API costs.

**Strategy:**
- Cache context for 15 minutes
- Batch API calls (describe multiple resources at once)
- Incremental updates (only changed resources)
- Use CloudWatch Events for real-time updates (instead of polling)

**Cost Comparison:**
```
Polling (every 15 min):
  96 collections/day × 50 API calls = 4,800 calls/day
  Cost: ~$0.50/month

CloudWatch Events:
  Real-time updates only when changes occur
  Cost: ~$0.10/month (80% reduction)
```

---

### 10.2 DynamoDB Storage Costs

**Scenario:** Large context store → high storage costs.

**Strategy:**
- TTL on old snapshots (auto-delete after 7 days)
- Compress snapshots (gzip)
- Use on-demand pricing (not provisioned)
- Archive to S3 after 30 days (cheaper storage)

---

### 10.3 CloudTrail Costs

**Scenario:** Change attribution requires CloudTrail lookups.

**Strategy:**
- Cache CloudTrail results (same user likely makes multiple changes)
- Batch lookups (query once per poll cycle)
- Only lookup for critical/warning drift (not info)
- Optional: disable for staging/dev environments

---

## Testing Recommendations

### Unit Tests
- Mock AWS API responses
- Test each corner case independently
- Verify error handling

### Integration Tests
- Use LocalStack for AWS simulation
- Test full pipeline with real boto3 calls
- Verify snapshot persistence

### Load Tests
- 100+ resources
- Concurrent polling
- API throttling simulation

---

## Monitoring & Alerting

### Key Metrics
- Context collection duration (target: <30s)
- Drift detection rate (events per poll)
- Parser ambiguity reduction (target: >50%)
- API failure rate (target: <1%)
- Stale context rate (target: <5%)

### Alerts
- Critical: Context collection failed 3 times
- Warning: Context >30 minutes old
- Info: High drift rate (>10 events/poll)

---

## Appendix: Example Scenarios

### Scenario A: Production Emergency During Drift

```
Situation:
  - PM issued "Scale api to 20" at 10:00
  - Drift detected at 10:05: manual scale to 15
  - Production incident: need immediate scale to 50

Handling:
  1. Cancel pending task (scale to 20)
  2. Issue emergency scale to 50
  3. Log drift acceptance: "Emergency override"
  4. Audit trail: "Manual intervention during incident XYZ"
```

### Scenario B: Multi-Environment Confusion

```
Situation:
  - PM intends staging, but production is default
  - Command: "Deploy v2.0" (missing environment)
  - Context shows production has 50 active connections

Handling:
  1. Auto-fill: environment=production (most common)
  2. Warning: "⚠️ Will deploy to PRODUCTION"
  3. Require explicit confirmation
  4. Option to change environment before approval
```

---

## Conclusion

These 50+ corner cases represent real-world scenarios encountered in production environments. The Context & Memory Layer is designed to handle them gracefully, with clear error messages, smart defaults, and safety checks.

**Key Principles:**
1. **Fail Gracefully:** Partial results better than complete failure
2. **Be Transparent:** Always show context age and confidence
3. **Validate Aggressively:** Check state before execution
4. **Prioritize Safety:** Require confirmation for risky operations

**Target Metrics:**
- Context collection success rate: >99%
- Ambiguity reduction: >50%
- Drift detection accuracy: >95%
- Parser uptime: >99.9%

---

*Document Version: 1.0*  
*Last Updated: 2026-04-28*  
*Week 7-8 Context & Memory Layer*
