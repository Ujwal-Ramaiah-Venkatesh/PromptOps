# Corner Cases & IT Industry Problems Analysis

**Document Purpose:** Comprehensive list of edge cases and real-world problems that PromptOps parser MUST handle

---

## 🚨 **Critical IT Industry Problems**

### **Category 1: Ambiguous Commands**

**Problem:** PM uses vague language that could mean multiple things

| Command | Ambiguity | Risk | How to Handle |
|---------|-----------|------|---------------|
| "Deploy the API" | Which API? (payment, auth, user, order) | HIGH | Ask clarification: "Which API? (payment-api, auth-api, user-api)" |
| "Scale up the backend" | Which backend service? By how much? | HIGH | Ask: "Which service?" and "Scale to how many instances?" |
| "Fix the database" | What's broken? Which database? | CRITICAL | Too vague - require more info: "What issue are you seeing?" |
| "Update production" | Update what? Code? Config? Infrastructure? | HIGH | Ask: "Update what? (code, config, infrastructure)" |
| "Deploy to prod" | Which service? Which version? | HIGH | Require: service name + version |
| "Make it faster" | What is 'it'? How much faster? | MEDIUM | Ask: "Which service/resource?" |
| "Reduce costs" | By how much? Which resources? | MEDIUM | Ask: "Target budget?" or auto-optimize with approval |
| "Check the logs" | Which service? What timeframe? | LOW | Default: all services, last 1 hour, but ask if unclear |

**Rule:** If confidence score < 85%, ALWAYS ask for clarification

---

### **Category 2: Multi-Environment Confusion**

**Problem:** PM accidentally targets wrong environment (deploys to prod instead of staging)

| Scenario | Risk | Prevention |
|----------|------|------------|
| "Deploy API v2.0" (no env specified) | CRITICAL | Default to staging, require explicit "production" keyword for prod |
| "Deploy to prod" (typo: meant staging) | CRITICAL | Show preview: "You are deploying to PRODUCTION", require 2-stage approval |
| Multiple envs: "prod", "production", "live", "prd" | MEDIUM | Normalize all variations to "production" |
| Environment abbreviations: "stg", "dev", "qa", "uat" | MEDIUM | Recognize all common abbreviations |
| Non-standard env names: "demo", "sandbox", "hotfix" | LOW | Ask: "Is this production or non-production?" |

**Rules:**
1. Explicit prod deployment ALWAYS requires approval
2. Show environment name in BIG BOLD text in preview
3. Normalize env names: prod/production/live → "production"
4. Non-prod can auto-execute (low risk)

---

### **Category 3: Version Confusion**

**Problem:** Incorrect or non-existent version specified

| Scenario | Risk | How to Handle |
|----------|------|---------------|
| "Deploy API v2.0" (v2.0 doesn't exist) | HIGH | Error: "v2.0 not found. Available: v1.9.5, v1.9.6, v2.0.1" |
| "Deploy API latest" | MEDIUM | Resolve "latest" to specific version: "v2.0.1 (latest)" |
| "Deploy API v2" (ambiguous: v2.0? v2.1? v2.0.1?) | HIGH | Ask: "Did you mean v2.0.0, v2.0.1, or v2.1.0?" |
| No version specified: "Deploy API" | HIGH | Ask: "Which version?" or suggest latest stable |
| "Deploy API to staging then prod" | MEDIUM | Decompose into 2 tasks with dependency |
| "Rollback API" (to which version?) | HIGH | Show last 5 versions, ask which to rollback to |

**Rules:**
1. Always validate version exists in registry BEFORE showing preview
2. Resolve "latest", "stable", "rc" to specific version
3. Show version changelog in preview if available

---

### **Category 4: Security & Access Control**

**Problem:** Unauthorized access or dangerous operations

| Scenario | Risk | Prevention |
|----------|------|------------|
| Junior PM tries to deploy to prod | CRITICAL | Check user role, require manager approval |
| "Delete production database" | CRITICAL | Block completely, require manual confirmation outside PromptOps |
| "Open port 22 to 0.0.0.0/0" | CRITICAL | Security policy violation - block and alert security team |
| Prompt injection: "Ignore previous instructions" | HIGH | Input sanitization layer blocks malicious patterns |
| "Deploy to prod at 2 AM" | MEDIUM | Allow but flag: "Off-hours deployment, ensure on-call coverage" |
| Cross-account access attempt | CRITICAL | Validate user has AWS/GCP credentials for target account |
| "Grant admin access to intern" | HIGH | Require security team approval for IAM changes |

**Rules:**
1. RBAC (Role-Based Access Control) enforced at parser level
2. Destructive operations require multi-stage approval
3. Security policy violations auto-blocked
4. All actions logged immutably for audit

---

### **Category 5: Cost & Budget Implications**

**Problem:** Commands that cause unexpected cost spikes

| Scenario | Risk | How to Handle |
|----------|------|---------------|
| "Scale to 1000 instances" | CRITICAL | Calculate cost: "$50K/month", require CFO approval if >$10K |
| "Deploy to 10 regions" | HIGH | Estimate: "This will cost $25K/month" |
| "Enable verbose logging" | MEDIUM | Warn: "This increases CloudWatch costs by $500/month" |
| "Create 500 test environments" | HIGH | Block: "Exceeds budget. Max 10 test environments allowed" |
| "Provision GPUs for ML workload" | HIGH | Show cost: "$15/hour per GPU", ask for duration |

**Rules:**
1. Calculate cost impact for every infrastructure change
2. Require approval if monthly cost increase >$1K
3. Show cost estimate in preview
4. Block if exceeds monthly budget

---

### **Category 6: Dependency & Order of Operations**

**Problem:** Commands that depend on other steps

| Scenario | Risk | How to Handle |
|----------|------|---------------|
| "Deploy API v2.0" (requires DB migration first) | CRITICAL | Detect dependency: "Requires DB migration first. Run migration?" |
| "Rollback API" (database already migrated forward) | CRITICAL | Warn: "Cannot rollback - DB schema mismatch" |
| "Scale down to 2 instances" (current load needs 10) | HIGH | Warn: "Current load is 1,200 req/s, 2 instances = overload" |
| "Deploy frontend" (depends on new API version) | MEDIUM | Check API version compatibility |
| "Delete S3 bucket" (still has objects) | HIGH | Require: "Empty bucket first?" or auto-empty with approval |

**Rules:**
1. Dependency detection: Check if prerequisites met
2. Suggest correct order: "Run X first, then Y"
3. Show warnings for risky order of operations

---

### **Category 7: Typos & Misspellings**

**Problem:** PM makes typing mistakes

| Typo | Likely Intent | How to Handle |
|------|---------------|---------------|
| "Depoly API" | Deploy API | Auto-correct: "Did you mean 'Deploy API'?" |
| "api-serivce" | api-service | Fuzzy match service names (Levenshtein distance) |
| "proudction" | production | Recognize common typos for environments |
| "scal up" | scale up | Auto-correct verb typos |
| "v2.0.0.1" | v2.0.1 | Validate version format, suggest correction |
| "AWS ECS" vs "ECS" | Same thing | Normalize: both mean AWS ECS |

**Rules:**
1. Fuzzy matching with 80% similarity threshold
2. Always show "Did you mean X?" for corrections
3. Never auto-execute corrected commands without confirmation

---

### **Category 8: Time-Sensitive Operations**

**Problem:** Commands with timing implications

| Scenario | Risk | How to Handle |
|----------|------|---------------|
| "Deploy now" (during Black Friday traffic spike) | CRITICAL | Warn: "Traffic is 5x normal. Deploy during maintenance window?" |
| "Schedule deployment for 2 AM" | MEDIUM | Validate: timezone clarification needed? |
| "Deploy in 5 minutes" | MEDIUM | Set up delayed execution, allow cancellation |
| "Rollback immediately" | HIGH | Fast-track approval, skip optional steps |
| "Scale up before launch" (launch in 10 min) | HIGH | Prioritize, show ETA: "Scaling will take 3 minutes" |

**Rules:**
1. Detect high-traffic periods (holidays, launches, peak hours)
2. Warn before deploying during risky times
3. Support scheduled deployments with timezone awareness

---

### **Category 9: Incomplete Information**

**Problem:** Command missing required parameters

| Incomplete Command | Missing Info | How to Handle |
|--------------------|--------------|---------------|
| "Deploy" | Service, version, environment | Ask all 3: "Which service? Version? Environment?" |
| "Scale up" | Service, target size | Ask: "Which service? Scale to how many instances?" |
| "Check errors" | Service, timeframe | Default: all services, last 1 hour |
| "How much did we spend?" | Timeframe, service | Default: current month, all services |
| "Rollback" | Service, target version | Ask: "Rollback which service to which version?" |

**Rules:**
1. Identify required parameters for each intent
2. Ask for missing parameters before proceeding
3. Use smart defaults where safe

---

### **Category 10: Conflicting Parameters**

**Problem:** Command contains contradictory instructions

| Conflicting Command | Issue | How to Handle |
|---------------------|-------|---------------|
| "Deploy v2.0 and v2.1 to prod" | Can't deploy 2 versions | Ask: "Which version: v2.0 or v2.1?" |
| "Scale up and scale down" | Contradictory | Error: "Conflicting instructions" |
| "Deploy to prod and staging" | Needs 2 separate operations | Decompose: "Deploy to staging first, then prod?" |
| "Reduce costs but add 50 instances" | Contradictory | Flag conflict, ask which priority |

**Rules:**
1. Detect contradictions in parsed parameters
2. Ask user to clarify priority
3. Never guess when conflicting instructions present

---

### **Category 11: Multi-Step Complex Commands**

**Problem:** PM combines multiple operations in one command

| Complex Command | Decomposition | How to Handle |
|-----------------|---------------|---------------|
| "Deploy API v2.0 to staging, test for 1 hour, then prod" | 3 steps | Break into: 1) Deploy staging, 2) Monitor 1hr, 3) Deploy prod |
| "Create new environment for demo with API and frontend" | 5+ steps | Decompose: VPC, subnets, deploy API, deploy frontend, configure DNS |
| "Migrate database and deploy new schema" | 2 steps with dependency | Sequence: 1) DB migration, 2) Deploy code |
| "Scale up, test load, then scale back down" | 3 steps | Decompose with timing: 1) Scale up, 2) Test (manual), 3) Scale down |

**Rules:**
1. Task Decomposition Engine handles this (Week 5-6)
2. Show step-by-step plan before execution
3. Support dependencies between steps

---

### **Category 12: Compliance & Regulatory**

**Problem:** Actions that violate compliance requirements

| Scenario | Compliance Risk | How to Handle |
|----------|----------------|---------------|
| "Delete customer data" | GDPR violation risk | Require: documented deletion request + legal approval |
| "Disable encryption" | SOC2/HIPAA violation | Block: "Encryption required by compliance policy" |
| "Grant access without MFA" | Security violation | Block: "MFA required for production access" |
| "Export logs to personal email" | Data leak risk | Block: "Use approved export destinations only" |
| "Deploy without security scan" | Vulnerability risk | Require: vulnerability scan must pass first |

**Rules:**
1. Compliance policies enforced at parser level
2. Audit trail for all compliance-related actions
3. Cannot override compliance blocks

---

### **Category 13: Performance & Resource Limits**

**Problem:** Commands that exceed system limits

| Scenario | Limit | How to Handle |
|----------|-------|---------------|
| "Scale to 10,000 instances" | AWS account limit: 500 | Error: "Exceeds account limit (500). Request limit increase?" |
| "Create 100TB RDS database" | Max RDS size: 64TB | Error: "Exceeds RDS limit. Use Aurora or shard database" |
| "Deploy 500 Lambda functions" | AWS Lambda limit: 1,000 | Warn: "You have 700/1,000 functions used" |
| "Enable debug mode on 500 instances" | Log volume too high | Warn: "This generates 50GB logs/hour. Cost: $1,200/day" |

**Rules:**
1. Check AWS/GCP/Azure quotas before executing
2. Suggest alternatives when limits exceeded
3. Offer to request limit increases

---

### **Category 14: State & Context Awareness**

**Problem:** Commands that conflict with current state

| Scenario | Current State | How to Handle |
|----------|---------------|---------------|
| "Deploy API v2.0" | v2.0 already deployed | Info: "v2.0 is already deployed. No action needed." |
| "Scale to 10 instances" | Already 10 instances | Info: "Already at 10 instances" |
| "Rollback API" | No previous version | Error: "No previous version to rollback to" |
| "Delete staging environment" | Active deployments running | Warn: "Environment has 5 active services. Stop services first?" |
| "Enable auto-scaling" | Already enabled | Info: "Auto-scaling already enabled" |

**Rules:**
1. Context Layer (Week 7-8) provides current state
2. Check current state before executing
3. Avoid no-op operations

---

### **Category 15: Error Recovery & Rollback**

**Problem:** What happens when operations fail?

| Failure Scenario | Risk | How to Handle |
|------------------|------|---------------|
| Deployment fails at step 5 of 8 | Partial state | Auto-rollback to previous state |
| Database migration fails | Data corruption risk | Restore from backup snapshot |
| Scaling up fails (no capacity) | Service degradation | Keep existing instances, alert PM |
| Network partition during deploy | Split-brain risk | Pause, wait for resolution, don't proceed |
| API rate limit hit | Operation incomplete | Retry with exponential backoff |

**Rules:**
1. Every operation has rollback plan
2. Automatic rollback on critical failures
3. Manual rollback option always available
4. Never leave system in partial state

---

## 🎯 **Summary: Parser Requirements**

### **Must Handle:**

1. ✅ Ambiguous commands (confidence scoring, clarification)
2. ✅ Multi-environment confusion (prod vs staging)
3. ✅ Version validation (exists in registry?)
4. ✅ Security & access control (RBAC, dangerous ops)
5. ✅ Cost implications (calculate before executing)
6. ✅ Dependencies (DB migrations, service dependencies)
7. ✅ Typos & misspellings (fuzzy matching)
8. ✅ Time-sensitive operations (traffic spikes, schedules)
9. ✅ Incomplete information (missing parameters)
10. ✅ Conflicting parameters (contradictions)
11. ✅ Multi-step commands (task decomposition)
12. ✅ Compliance violations (GDPR, SOC2, HIPAA)
13. ✅ Resource limits (AWS quotas, account limits)
14. ✅ State awareness (already deployed? already scaled?)
15. ✅ Error recovery (rollback plans, retries)

### **Parser Output Must Include:**

```json
{
  "intent_type": "deploy",
  "confidence_score": 0.96,
  "target_service": "api",
  "target_env": "production",
  "parameters": {
    "version": "v2.1.0",
    "strategy": "canary"
  },
  "requires_approval": true,
  "risk_level": "high",
  "estimated_cost_impact": "+$500/month",
  "dependencies": ["database_migration_v2.1"],
  "warnings": ["Deploy during high traffic period"],
  "security_checks": ["IAM permissions validated"],
  "rollback_plan": "Revert to v2.0.9",
  "ambiguity_detected": false,
  "clarification_questions": [],
  "estimated_duration": "7-8 minutes"
}
```

---

**Next:** Write comprehensive system prompt that handles all 15 categories
