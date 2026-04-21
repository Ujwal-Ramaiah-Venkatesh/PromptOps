# Week 5-6: Task Decomposition Engine - Complete Plan
## Breaking Complex Commands into Atomic, Executable Sub-Tasks

**Timeline:** May 5-16, 2026 (2 weeks)  
**Goal:** Decompose each parsed intent into 5-15 ordered DevOps sub-tasks with dependencies, rollback actions, and parallel execution planning

---

## 🎯 Overview

### What We're Building

The **Task Decomposition Engine** takes a single parsed PM command and breaks it into atomic, executable sub-tasks that:
- Can be executed by specialized agents (Phase 2)
- Have clear dependencies and ordering
- Include rollback actions for each step
- Can execute in parallel where safe
- Cover all edge cases and failure scenarios

### Example

**Input (from Week 3-4 parser):**
```json
{
  "intent_type": "deploy",
  "target_service": "api",
  "target_env": "production",
  "parameters": { "version": "v2.1.0", "strategy": "canary" },
  "risk_level": "high"
}
```

**Output (Task Decomposition):**
```json
{
  "decomposition_id": "decomp-2026-05-05-a1b2c3",
  "original_intent": { ... },
  "total_sub_tasks": 12,
  "estimated_duration": "8-10 minutes",
  "execution_strategy": "sequential_with_parallel_phases",
  "sub_tasks": [
    {
      "task_id": "task-001",
      "sequence": 1,
      "phase": "pre-deployment",
      "action": "validate_version_exists",
      "target": "docker_registry",
      "parameters": { "image": "api:v2.1.0" },
      "dependencies": [],
      "can_run_parallel": false,
      "estimated_duration": "10s",
      "rollback_action": null,
      "validation_criteria": {
        "expected_status": "image_found",
        "timeout": 30
      }
    },
    {
      "task_id": "task-002",
      "sequence": 2,
      "phase": "pre-deployment",
      "action": "run_security_scan",
      "target": "api:v2.1.0",
      "parameters": { "scan_type": "vulnerability" },
      "dependencies": ["task-001"],
      "can_run_parallel": false,
      "estimated_duration": "45s",
      "rollback_action": null,
      "validation_criteria": {
        "expected_status": "no_critical_vulnerabilities",
        "timeout": 60
      }
    },
    // ... 10 more sub-tasks
  ]
}
```

---

## 📋 Week 5-6 Tasks Breakdown

### **Task DECOMP-001: Design Decomposition Prompt** (2 hours)
Create Claude Sonnet 4 system prompt that generates sub-task breakdowns.

**Deliverable:** `decomposition/decomposition_prompt.txt`

**Requirements:**
- Takes parsed intent JSON as input
- Outputs structured sub-task list (5-15 tasks)
- Includes dependencies, rollback actions, validation criteria
- Handles all 8 intent types (deploy, scale, rollback, monitor, audit, cost, security, diagnose)
- Comprehensive corner case handling

---

### **Task DECOMP-002: Build Sub-Task JSON Schema** (1 hour)
Define strict schema for decomposed sub-tasks.

**Deliverable:** `config/subtask_schema.json`

**Fields:**
- `task_id` - Unique identifier
- `sequence` - Execution order (1-based)
- `phase` - Logical grouping (pre-deployment, deployment, post-deployment, validation, rollback)
- `action` - What to do (validate_version, deploy_canary, run_health_check, etc.)
- `target` - What resource (service name, database, load balancer, etc.)
- `parameters` - Action-specific parameters
- `dependencies` - List of task_ids that must complete first
- `can_run_parallel` - Boolean (true if can run concurrently with other tasks)
- `estimated_duration` - Time estimate in seconds
- `rollback_action` - How to undo this step
- `validation_criteria` - Success conditions
- `risk_level` - low/medium/high/critical
- `approval_required` - Boolean

---

### **Task DECOMP-003: Implement Dependency Resolver** (3 hours)
Build graph-based dependency resolver.

**Deliverable:** `decomposition/dependency_resolver.py`

**Features:**
- Topological sort for task ordering
- Detects circular dependencies (error if found)
- Identifies parallelizable tasks (same dependencies, no conflicts)
- Validates all dependencies exist
- Calculates critical path (longest sequential chain)
- Estimates total execution time

**Corner Cases:**
- Circular dependencies (A depends on B, B depends on A)
- Missing dependencies (task references non-existent task)
- Orphan tasks (no dependencies, no dependents)
- Diamond dependencies (A→B, A→C, B→D, C→D)
- Long chains (>10 sequential dependencies)

---

### **Task DECOMP-004: Build Decomposition Engine** (4 hours)
Main engine that calls Claude API to decompose intents.

**Deliverable:** `decomposition/decomposition_engine.py`

**Features:**
- `DecompositionEngine` class
- `decompose()` method (takes parsed intent, returns sub-tasks)
- Claude API integration (reuse Week 3-4 patterns)
- Response validation (check all required fields)
- Retry logic (3 attempts)
- Cost tracking
- LangGraph integration node

**Validation:**
- All sub-tasks have valid task_ids
- Dependencies reference existing tasks
- No circular dependencies
- Rollback actions provided for risky tasks
- Estimated durations are reasonable
- Phase groupings are logical

---

### **Task DECOMP-005: Create Decomposition Test Suite** (3 hours)
Comprehensive test coverage for decomposition.

**Deliverable:** `tests/decomposition_tests.json` + `test_decomposition.py`

**Test Categories:**

1. **Simple Commands (5 tests)**
   - "Deploy API to staging"
   - "Scale backend to 10 instances"
   - "Rollback frontend to previous version"
   - "Show me API logs from last hour"
   - "How much are we spending on RDS?"

2. **Complex Multi-Step Commands (10 tests)**
   - "Deploy API v2.0 to production with canary rollout"
   - "Migrate database from SQLite to PostgreSQL"
   - "Set up complete ELK stack in production"
   - "Scale API to handle 2x traffic, ensure DB can handle load"
   - "Rollback production if error rate exceeds 5%"
   - "Deploy staging, run smoke tests, then deploy production"
   - "Set up blue-green deployment for zero-downtime"
   - "Implement disaster recovery: backups + multi-region replication"
   - "Optimize costs: downsize unused instances, archive old logs"
   - "Security audit: patch vulnerabilities, rotate secrets, update firewall rules"

3. **Dependency Edge Cases (5 tests)**
   - Parallel execution (multiple independent tasks)
   - Sequential dependencies (A→B→C→D)
   - Diamond dependencies (A→B/C→D)
   - Conditional execution ("deploy if tests pass")
   - Rollback chains (undo in reverse order)

4. **Failure Scenarios (5 tests)**
   - Ambiguous decomposition (can't break into sub-tasks)
   - Missing required information (no version specified)
   - Conflicting requirements ("scale up and scale down")
   - Impossible dependencies (circular)
   - Too complex (>20 sub-tasks needed)

**Total: 25 tests**

---

### **Task DECOMP-006: Build Task Preview UI Component** (2 hours)
React component showing decomposed tasks before execution.

**Deliverable:** `dashboard/components/TaskPreview.tsx`

**Features:**
- Display all sub-tasks in execution order
- Visual dependency graph (DAG visualization)
- Highlight parallel vs sequential tasks
- Show estimated duration per task + total
- Display rollback actions
- Risk indicators (color-coded)
- Approval button for high-risk tasks

---

### **Task DECOMP-007: End-to-End Integration Test** (2 hours)
Wire decomposition engine into LangGraph workflow.

**Deliverable:** `tests/integration/decomposition_integration_test.py`

**Flow:**
1. PM command → Parser (Week 3-4)
2. Parsed intent → Decomposition Engine (Week 5-6)
3. Sub-tasks → Dependency Resolver
4. Ordered tasks → Task Preview UI
5. Validate entire pipeline works

---

## 🚨 Corner Cases & Edge Scenarios

### 1. **Ambiguous Multi-Step Commands**

**Scenario:** "Deploy to staging then production"
- **Issue:** Unclear if production should wait for manual approval or auto-deploy
- **Handling:** 
  - Decompose with conditional dependency: `task-production.depends_on = [task-staging-validation]`
  - Insert approval task: `task-approval` between staging and prod
  - Set `approval_required: true` on production deployment task

**Test Case:**
```json
{
  "pm_input": "Deploy API v2.0 to staging, if tests pass deploy to production",
  "expected_sub_tasks": [
    { "task_id": "task-001", "action": "deploy_staging", "dependencies": [] },
    { "task_id": "task-002", "action": "run_smoke_tests", "dependencies": ["task-001"] },
    { "task_id": "task-003", "action": "conditional_gate", "dependencies": ["task-002"], "condition": "tests_passed" },
    { "task_id": "task-004", "action": "deploy_production", "dependencies": ["task-003"] }
  ]
}
```

---

### 2. **Circular Dependencies**

**Scenario:** Decomposition generates invalid dependency graph
- **Issue:** Task A depends on B, Task B depends on A (impossible to execute)
- **Handling:**
  - Dependency resolver detects cycles using graph traversal
  - Reject decomposition with clear error
  - Retry with stricter prompt guidance
  - If retries fail, ask PM for clarification

**Test Case:**
```python
def test_circular_dependency_detection():
    sub_tasks = [
        {"task_id": "A", "dependencies": ["B"]},
        {"task_id": "B", "dependencies": ["A"]}
    ]
    
    resolver = DependencyResolver()
    result = resolver.validate_dependencies(sub_tasks)
    
    assert result.is_valid == False
    assert "circular dependency" in result.error.lower()
    assert "A → B → A" in result.error
```

---

### 3. **Database Migration Complex Dependencies**

**Scenario:** "Migrate database from SQLite to PostgreSQL"
- **Issue:** Multiple sequential steps, requires backup, data migration, validation, cutover
- **Handling:**
  - Break into 10-15 sub-tasks
  - Each task has validation criteria
  - Rollback action for every step
  - Estimated duration ~30-60 minutes

**Expected Sub-Tasks:**
1. Backup SQLite database (rollback: none, this is the safety net)
2. Provision PostgreSQL instance (rollback: delete instance)
3. Create schema in PostgreSQL (rollback: drop schema)
4. Test write to PostgreSQL (rollback: none, read-only test)
5. Migrate data in batches (rollback: truncate tables)
6. Validate row counts match (rollback: none, validation only)
7. Set up replication SQLite→PostgreSQL (rollback: disable replication)
8. Enable dual-write mode (rollback: disable dual-write)
9. Validate data consistency (rollback: none, validation only)
10. Cutover: point app to PostgreSQL (rollback: point back to SQLite)
11. Monitor for 15 minutes (rollback: automatic if errors detected)
12. Decommission SQLite (rollback: re-enable SQLite)

**Dependencies:**
- Tasks 1-4: sequential
- Task 5: depends on 4
- Task 6: depends on 5
- Tasks 7-12: sequential

---

### 4. **Parallel Execution Opportunities**

**Scenario:** "Set up monitoring: Prometheus, Grafana, and alerting"
- **Issue:** Can Prometheus and Grafana be deployed in parallel? What dependencies exist?
- **Handling:**
  - Analyze which tasks share no resources
  - Mark `can_run_parallel: true` for independent tasks
  - Identify critical path (longest sequential chain)

**Expected Sub-Tasks:**
```json
{
  "sub_tasks": [
    { "task_id": "task-001", "action": "deploy_prometheus", "dependencies": [], "can_run_parallel": true },
    { "task_id": "task-002", "action": "deploy_grafana", "dependencies": [], "can_run_parallel": true },
    { "task_id": "task-003", "action": "configure_prometheus_datasource", "dependencies": ["task-001"], "can_run_parallel": false },
    { "task_id": "task-004", "action": "configure_grafana_dashboards", "dependencies": ["task-002", "task-003"], "can_run_parallel": false },
    { "task_id": "task-005", "action": "setup_alertmanager", "dependencies": ["task-001"], "can_run_parallel": true },
    { "task_id": "task-006", "action": "test_alerts", "dependencies": ["task-004", "task-005"], "can_run_parallel": false }
  ],
  "execution_plan": {
    "phase_1_parallel": ["task-001", "task-002"],
    "phase_2_sequential": ["task-003"],
    "phase_3_parallel": ["task-004", "task-005"],
    "phase_4_sequential": ["task-006"]
  }
}
```

---

### 5. **Rollback Chain Complexity**

**Scenario:** "Deploy API v2.0 with database migration"
- **Issue:** If deployment fails mid-way, rollback must undo steps in reverse order
- **Handling:**
  - Generate rollback plan as part of decomposition
  - Rollback actions in reverse sequence
  - Some actions can't be rolled back (e.g., sent emails, deleted data)

**Rollback Strategy:**
```json
{
  "original_execution": ["task-001", "task-002", "task-003", "task-004"],
  "rollback_sequence": [
    {
      "trigger": "task-004 failed",
      "rollback_order": ["task-004-rollback", "task-003-rollback", "task-002-rollback"],
      "note": "task-001 (backup) has no rollback - it's the safety net"
    }
  ]
}
```

---

### 6. **Resource Contention**

**Scenario:** "Scale API to 20 instances AND deploy new version"
- **Issue:** Can't deploy while actively scaling (resource locks)
- **Handling:**
  - Detect conflicting actions on same resource
  - Serialize conflicting tasks
  - Add explicit dependency: `deploy.dependencies = [scale_complete]`

**Test Case:**
```python
def test_resource_contention():
    pm_input = "Scale API to 20 instances and deploy v2.0"
    
    decomposition = engine.decompose(pm_input)
    
    # Ensure scale completes before deploy starts
    scale_tasks = [t for t in decomposition.sub_tasks if t.action == "scale"]
    deploy_tasks = [t for t in decomposition.sub_tasks if t.action == "deploy"]
    
    for deploy_task in deploy_tasks:
        assert any(scale_task.task_id in deploy_task.dependencies for scale_task in scale_tasks)
```

---

### 7. **Conditional Execution**

**Scenario:** "Deploy to production if staging tests pass"
- **Issue:** How to represent conditional logic in task graph?
- **Handling:**
  - Insert conditional gate task
  - Gate evaluates condition (tests_passed == true)
  - Production deployment depends on gate

**Expected Sub-Tasks:**
```json
[
  { "task_id": "task-001", "action": "deploy_staging" },
  { "task_id": "task-002", "action": "run_tests", "dependencies": ["task-001"] },
  { 
    "task_id": "task-003", 
    "action": "conditional_gate", 
    "dependencies": ["task-002"],
    "parameters": {
      "condition": "tests_passed",
      "if_true": "continue",
      "if_false": "abort_with_notification"
    }
  },
  { "task_id": "task-004", "action": "deploy_production", "dependencies": ["task-003"] }
]
```

---

### 8. **Time-Based Dependencies**

**Scenario:** "Deploy at 2 AM UTC to avoid peak traffic"
- **Issue:** Task has time constraint, not just logical dependency
- **Handling:**
  - Add `scheduled_time` parameter
  - Task waits until scheduled time
  - Validate scheduled time is in the future

**Expected Sub-Tasks:**
```json
{
  "task_id": "task-001",
  "action": "wait_until_scheduled_time",
  "parameters": { "scheduled_time": "2026-05-06T02:00:00Z" },
  "dependencies": []
}
```

---

### 9. **Approval Gates**

**Scenario:** "Scale database to larger instance (production)"
- **Issue:** High-risk action requires human approval before execution
- **Handling:**
  - Insert approval gate task
  - Execution pauses until PM approves
  - Timeout after 24 hours (auto-reject)

**Expected Sub-Tasks:**
```json
[
  { "task_id": "task-001", "action": "validate_new_instance_size" },
  { "task_id": "task-002", "action": "calculate_cost_impact", "dependencies": ["task-001"] },
  { 
    "task_id": "task-003", 
    "action": "approval_gate", 
    "dependencies": ["task-002"],
    "parameters": {
      "approval_type": "human_required",
      "risk_level": "high",
      "timeout": "24h",
      "approvers": ["pm", "engineering_manager"]
    }
  },
  { "task_id": "task-004", "action": "scale_database", "dependencies": ["task-003"] }
]
```

---

### 10. **Too Many Sub-Tasks**

**Scenario:** "Set up complete production infrastructure from scratch"
- **Issue:** Decomposition would generate 100+ sub-tasks (unmanageable)
- **Handling:**
  - Detect when sub-task count > 20
  - Suggest breaking into multiple high-level commands
  - Return error with recommendation

**Example Response:**
```json
{
  "status": "too_complex",
  "sub_task_count": 47,
  "recommendation": "This command is too complex to decompose in one step. Please break it into smaller commands:",
  "suggested_commands": [
    "Set up VPC and networking",
    "Deploy database infrastructure",
    "Deploy application services",
    "Configure monitoring and alerting",
    "Set up backups and disaster recovery"
  ]
}
```

---

## 📊 Decomposition Prompt Strategy

### Prompt Structure

```
You are a DevOps task decomposition expert. Your job is to break down high-level 
infrastructure commands into atomic, executable sub-tasks.

INPUT:
You will receive a parsed PM command as JSON with these fields:
- intent_type: deploy | scale | rollback | monitor | audit | cost | security | diagnose
- target_service: The service/resource being acted upon
- target_env: The environment (production, staging, dev, etc.)
- parameters: Action-specific parameters
- risk_level: low | medium | high | critical

OUTPUT:
Generate a JSON object with these fields:
{
  "decomposition_id": "decomp-YYYY-MM-DD-XXXX",
  "total_sub_tasks": <number>,
  "estimated_duration": "<X-Y minutes>",
  "execution_strategy": "sequential | parallel | sequential_with_parallel_phases",
  "sub_tasks": [ ... ],
  "rollback_plan": { ... }
}

RULES:
1. Generate 5-15 sub-tasks (if >20, return "too_complex" error)
2. Each sub-task MUST have: task_id, sequence, action, target, dependencies
3. Include rollback_action for all state-changing tasks
4. Identify tasks that can run in parallel (same dependencies, no resource conflicts)
5. Add validation tasks after critical operations
6. Insert approval gates for high-risk actions
7. Estimate realistic durations (don't underestimate)
8. Detect and reject circular dependencies

INTENT-SPECIFIC GUIDELINES:

DEPLOY:
- Pre-deployment: validate version, run security scan, check resource availability
- Deployment: execute deployment strategy (canary, blue-green, rolling)
- Post-deployment: health checks, smoke tests, monitoring setup
- Rollback: revert to previous version if validation fails

SCALE:
- Pre-scaling: check quota limits, calculate cost impact
- Scaling: adjust instance count, update load balancer
- Post-scaling: validate all instances healthy, update monitoring thresholds

ROLLBACK:
- Pre-rollback: identify previous stable version, validate it's still available
- Rollback: execute rollback strategy
- Post-rollback: validate system health, notify stakeholders

[... Continue for all 8 intent types ...]

EXAMPLES:

[Provide 5-10 detailed examples covering common and complex scenarios]
```

---

## 📈 Success Metrics

### Week 5-6 Exit Criteria

- ✅ Decomposition engine complete (4 core classes)
- ✅ Sub-task JSON schema defined (15 required fields)
- ✅ Dependency resolver working (handles 10 edge cases)
- ✅ 25 decomposition tests passing (>90% accuracy)
- ✅ Task Preview UI component complete
- ✅ End-to-end integration test passing
- ✅ API costs <$20 for Week 5-6

### Quality Metrics

- **Decomposition Accuracy:** >85% of sub-tasks are correct and executable
- **Dependency Correctness:** 100% of dependency graphs are valid (no cycles)
- **Rollback Completeness:** >90% of risky tasks have rollback actions
- **Parallel Detection:** Correctly identifies >80% of parallelizable tasks
- **Duration Estimates:** Within 30% of actual execution time (when measured in Phase 2)

---

## 🗂️ File Structure

```
phase1-nlp/decomposition/
├── WEEK5-6_PLAN.md                      ✅ This file
├── decomposition_prompt.txt             🔴 TODO
├── decomposition_engine.py              🔴 TODO
├── dependency_resolver.py               🔴 TODO
├── execution_planner.py                 🔴 TODO
├── CORNER_CASES_DECOMPOSITION.md        🔴 TODO
└── README.md                            🔴 TODO

config/
└── subtask_schema.json                  🔴 TODO

tests/
├── decomposition_tests.json             🔴 TODO
├── test_decomposition.py                🔴 TODO
└── integration/
    └── decomposition_integration_test.py 🔴 TODO

dashboard/components/
└── TaskPreview.tsx                      🔴 TODO
```

---

## ⏰ Timeline

### Week 5 (May 5-9)
- **Day 1 (Mon):** DECOMP-001 (prompt) + DECOMP-002 (schema)
- **Day 2 (Tue):** DECOMP-003 (dependency resolver)
- **Day 3 (Wed):** DECOMP-004 (decomposition engine) - Part 1
- **Day 4 (Thu):** DECOMP-004 (decomposition engine) - Part 2
- **Day 5 (Fri):** DECOMP-005 (test suite) - Part 1

### Week 6 (May 12-16)
- **Day 1 (Mon):** DECOMP-005 (test suite) - Part 2
- **Day 2 (Tue):** DECOMP-006 (Task Preview UI)
- **Day 3 (Wed):** DECOMP-007 (integration tests)
- **Day 4 (Thu):** Bug fixes, edge case handling
- **Day 5 (Fri):** Documentation, Week 5-6 completion report

---

## 🚀 Ready to Start

All requirements documented. Let's begin with **DECOMP-001: Design Decomposition Prompt**.

**Next Step:** Create `decomposition_prompt.txt` with comprehensive instructions for Claude Sonnet 4.
