# Week 7-8: Context & Memory Layer - Implementation Plan

**Timeline:** May 19 – May 30, 2026 (10 working days)  
**Status:** 🚧 IN PROGRESS  
**Owner:** PromptOps Team

---

## Executive Summary

Build an **Infrastructure Context Store** that remembers the current state of all AWS resources, enabling context-aware command parsing and drift detection. This eliminates the need for PMs to repeatedly specify infrastructure details and catches configuration drift in real-time.

### Core Problem

**Without Context:**
```
PM: "Scale frontend to 10 instances"
System: "Which frontend? us-east-1 or eu-west-1? Currently at how many instances?"
```

**With Context:**
```
PM: "Scale frontend to 10 instances"
System: "Scaling frontend-prod (us-east-1) from 5 → 10 instances. Current version: v2.3.1"
```

---

## Goals

1. **Infrastructure Context Store**: Persistent state tracking for AWS resources
2. **Context Injection Pipeline**: Automatically inject relevant context into Claude prompts
3. **Drift Detection**: Real-time detection of manual changes (15-min polling)
4. **Context-Aware Parsing**: Enhanced parser that uses infrastructure state
5. **Drift Alert UI**: Dashboard component showing configuration drift

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Week 7-8 Architecture                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   AWS Cloud  │
│              │
│  • EC2       │
│  • ECS       │
│  • RDS       │
│  • Lambda    │
│  • ALB       │
└──────┬───────┘
       │
       │ boto3 SDK
       │ (every 15 min)
       ↓
┌──────────────────────────────────────┐
│   Context Collector                  │
│   - Fetch current infrastructure     │
│   - Detect drift vs. last snapshot   │
│   - Calculate resource metadata      │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│   Infrastructure Context Store       │
│   (DynamoDB / JSON file)             │
│                                      │
│   Resources:                         │
│   - service_name                     │
│   - environment                      │
│   - region                           │
│   - current_state (running/stopped)  │
│   - instance_count                   │
│   - version                          │
│   - last_modified                    │
│   - tags                             │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│   Context Injector                   │
│   - Filter relevant resources        │
│   - Format for Claude prompt         │
│   - Inject into system context       │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│   Enhanced NLP Parser                │
│   (Week 3-4 + Context)               │
│                                      │
│   Input: "Scale frontend to 10"     │
│   Context: frontend-prod @ 5 inst.  │
│   Output: Precise task plan          │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│   Task Decomposition Engine          │
│   (Week 5-6)                         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│   Drift Detector                     │
│   - Compare snapshots                │
│   - Identify manual changes          │
│   - Calculate drift severity         │
│   - Trigger alerts                   │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│   Drift Alert UI                     │
│   (Frontend Component)               │
│   - Show drift warnings              │
│   - "Accept drift" or "Revert"       │
│   - Drift history timeline           │
└──────────────────────────────────────┘
```

---

## Task Breakdown

### CONTEXT-001: Infrastructure Context Store Schema ⏱️ Day 1-2

**Goal:** Design the data model for tracking infrastructure state.

**Schema Requirements:**
- Support for 10+ AWS resource types (EC2, ECS, RDS, Lambda, ALB, S3, DynamoDB, SQS, SNS, CloudFront)
- Version history (last 7 days of snapshots)
- Drift metadata (what changed, when, by whom)
- Tag-based filtering
- Environment separation (dev/staging/production)

**Deliverable:** `config/context_store_schema.json`

**Example Structure:**
```json
{
  "resources": [
    {
      "resource_id": "ecs-frontend-prod-us-east-1",
      "service_name": "frontend",
      "resource_type": "ecs_service",
      "environment": "production",
      "region": "us-east-1",
      "current_state": {
        "status": "ACTIVE",
        "desired_count": 5,
        "running_count": 5,
        "task_definition": "frontend:42",
        "deployment_version": "v2.3.1",
        "load_balancer": "alb-frontend-prod",
        "cpu": "512",
        "memory": "1024",
        "last_deployment": "2026-05-18T14:23:00Z"
      },
      "tags": {
        "Team": "Platform",
        "CostCenter": "Engineering",
        "Managed": "PromptOps"
      },
      "metadata": {
        "created_at": "2026-01-15T10:00:00Z",
        "last_updated": "2026-05-18T14:23:00Z",
        "last_snapshot": "2026-05-19T09:15:00Z"
      },
      "drift_status": {
        "has_drift": false,
        "last_drift_detected": null,
        "drift_details": []
      }
    }
  ],
  "snapshots": [
    {
      "snapshot_id": "snap-2026-05-19-09-15",
      "timestamp": "2026-05-19T09:15:00Z",
      "resource_count": 47,
      "checksum": "abc123..."
    }
  ]
}
```

**Success Criteria:**
- Schema validates with JSON Schema validator
- Supports 10+ AWS resource types
- Includes drift tracking fields
- Versioned snapshot support

---

### CONTEXT-002: Context Collector ⏱️ Day 2-3

**Goal:** Build the AWS resource fetcher using boto3.

**Features:**
1. **Multi-Resource Collector**
   - ECS services (tasks, task definitions, deployments)
   - EC2 instances (state, instance type, AMI, tags)
   - RDS databases (status, instance class, version)
   - Lambda functions (runtime, memory, last modified)
   - ALB/ELB (listeners, target groups, health checks)
   - S3 buckets (versioning, encryption, public access)
   - DynamoDB tables (status, read/write capacity)
   - SQS queues (message count, visibility timeout)
   - SNS topics (subscriptions)
   - CloudFront distributions (status, origins)

2. **Intelligent Filtering**
   - Only collect resources with tag `Managed: PromptOps`
   - Ignore AWS-managed resources
   - Environment-based filtering

3. **Performance Optimization**
   - Parallel fetching (ThreadPoolExecutor)
   - Caching for 15 minutes
   - Pagination handling

**Deliverable:** `phase1-nlp/context/context_collector.py`

**Key Methods:**
```python
class ContextCollector:
    def __init__(self, aws_region: str = 'us-east-1')
    
    def collect_all_resources(self) -> Dict[str, Any]
    def collect_ecs_services(self) -> List[Dict]
    def collect_ec2_instances(self) -> List[Dict]
    def collect_rds_databases(self) -> List[Dict]
    def collect_lambda_functions(self) -> List[Dict]
    def collect_load_balancers(self) -> List[Dict]
    
    def save_snapshot(self, resources: Dict, snapshot_id: str)
    def get_latest_snapshot(self) -> Dict
    def calculate_checksum(self, resources: Dict) -> str
```

**Success Criteria:**
- Successfully fetches all 10 resource types
- Handles AWS pagination
- Completes collection in <30 seconds
- Saves snapshots to disk/DynamoDB

---

### CONTEXT-003: Context Injector ⏱️ Day 3-4

**Goal:** Build the pipeline that injects relevant context into Claude prompts.

**Features:**
1. **Relevance Filtering**
   - Extract service names from PM command
   - Match against context store
   - Include dependencies (e.g., ALB for ECS service)

2. **Context Formatting**
   - Concise, Claude-optimized format
   - Only include relevant fields
   - Token budget management (<2000 tokens for context)

3. **Smart Injection**
   - Inject into system prompt
   - Clearly delimited context section
   - Timestamp for freshness

**Deliverable:** `phase1-nlp/context/context_injector.py`

**Key Methods:**
```python
class ContextInjector:
    def __init__(self, context_store_path: str)
    
    def extract_relevant_resources(self, pm_command: str) -> List[Dict]
    def format_context_for_claude(self, resources: List[Dict]) -> str
    def inject_context(self, base_prompt: str, context: str) -> str
    def calculate_context_tokens(self, context: str) -> int
```

**Context Format Example:**
```
=== INFRASTRUCTURE CONTEXT (as of 2026-05-19 09:15 UTC) ===

SERVICE: frontend
- Type: ECS Service
- Environment: production
- Region: us-east-1
- Status: ACTIVE
- Instances: 5 running (desired: 5)
- Version: v2.3.1 (task definition: frontend:42)
- Load Balancer: alb-frontend-prod
- Last Deployment: 2026-05-18 14:23 UTC

SERVICE: api
- Type: ECS Service
- Environment: production
- Region: us-east-1
- Status: ACTIVE
- Instances: 10 running (desired: 10)
- Version: v3.5.0 (task definition: api:78)
- Dependencies: rds-main-db
- Last Deployment: 2026-05-17 11:00 UTC

DATABASE: rds-main-db
- Type: RDS (PostgreSQL 15.2)
- Environment: production
- Status: available
- Instance: db.r6g.xlarge
- Multi-AZ: true

=== END CONTEXT ===
```

**Success Criteria:**
- Correctly identifies relevant resources from command
- Formats context in <2000 tokens
- Injection doesn't break prompt structure
- Handles missing/outdated context gracefully

---

### CONTEXT-004: Drift Detector ⏱️ Day 4-5

**Goal:** Detect configuration drift between snapshots.

**Features:**
1. **Snapshot Comparison**
   - Compare current vs. previous snapshot
   - Field-level diff (instance count, version, config)
   - Ignore expected changes (e.g., ECS task restarts)

2. **Drift Categorization**
   - **Critical**: Production database down, security group open to 0.0.0.0/0
   - **Warning**: Unexpected instance count change, version rollback
   - **Info**: Tag changes, minor config updates

3. **Drift Attribution**
   - Check CloudTrail for who made the change
   - Manual vs. automated change detection
   - PromptOps-initiated vs. external change

4. **Alerting**
   - Log drift events
   - Trigger UI notification
   - Optional Slack/email alerts

**Deliverable:** `phase1-nlp/context/drift_detector.py`

**Key Methods:**
```python
class DriftDetector:
    def __init__(self, context_store_path: str)
    
    def detect_drift(self, current_snapshot: Dict, previous_snapshot: Dict) -> DriftReport
    def compare_resources(self, current: Dict, previous: Dict) -> List[DriftEvent]
    def categorize_drift(self, drift_event: DriftEvent) -> str  # critical/warning/info
    def get_drift_attribution(self, resource_id: str, timestamp: str) -> Dict
    def should_alert(self, drift_event: DriftEvent) -> bool
```

**DriftReport Structure:**
```python
@dataclass
class DriftEvent:
    resource_id: str
    resource_type: str
    field_changed: str
    old_value: Any
    new_value: Any
    severity: str  # critical, warning, info
    detected_at: str
    changed_by: Optional[str]
    change_source: str  # manual, console, api, promptops

@dataclass
class DriftReport:
    snapshot_id: str
    timestamp: str
    total_drift_events: int
    critical_count: int
    warning_count: int
    info_count: int
    drift_events: List[DriftEvent]
```

**Success Criteria:**
- Detects all resource state changes
- Correctly categorizes severity
- Identifies change source (CloudTrail integration)
- Generates human-readable drift report

---

### CONTEXT-005: Drift Polling Service ⏱️ Day 5-6

**Goal:** Background service that polls AWS every 15 minutes.

**Features:**
1. **Scheduled Polling**
   - Runs every 15 minutes
   - Configurable interval
   - Graceful shutdown

2. **Error Handling**
   - AWS API throttling
   - Network failures
   - Partial collection fallback

3. **State Persistence**
   - Save snapshots to disk/DynamoDB
   - Maintain 7 days of history
   - Auto-cleanup old snapshots

**Deliverable:** `phase1-nlp/context/drift_polling_service.py`

**Key Methods:**
```python
class DriftPollingService:
    def __init__(self, interval_minutes: int = 15)
    
    def start(self)
    def stop(self)
    def poll_once(self) -> bool
    def cleanup_old_snapshots(self, days_to_keep: int = 7)
```

**Deployment Options:**
1. **Local Development**: Python script with `schedule` library
2. **Production**: AWS Lambda (CloudWatch Events trigger every 15 min)
3. **Alternative**: ECS scheduled task

**Success Criteria:**
- Runs reliably every 15 minutes
- Handles AWS API errors gracefully
- Auto-cleans old snapshots
- Logs all polling activity

---

### CONTEXT-006: Enhanced Parser with Context ⏱️ Day 6-7

**Goal:** Upgrade Week 3-4 Parser to use infrastructure context.

**Features:**
1. **Context-Aware Prompt**
   - Inject infrastructure context before parsing
   - Reduce ambiguity with current state info

2. **Smart Defaults**
   - Auto-fill environment if only one exists
   - Use current version for rollback commands
   - Infer region from most common resource region

3. **Validation Against Context**
   - Verify service exists before decomposing
   - Check current state (can't scale stopped service)
   - Validate dependencies

**Deliverable:** `phase1-nlp/parser/context_aware_parser.py`

**Key Methods:**
```python
class ContextAwareParser(ClaudeParser):
    def __init__(self, api_key: str, context_injector: ContextInjector)
    
    def parse_command_with_context(self, pm_command: str) -> Tuple[bool, Dict, str]
    def validate_against_context(self, parsed_intent: Dict) -> ValidationResult
    def apply_smart_defaults(self, parsed_intent: Dict) -> Dict
```

**Example Enhancement:**

**Before (Week 3-4):**
```python
PM: "Scale frontend to 10"
Parser Output:
{
    "intent_type": "scale",
    "target_service": "frontend",
    "parameters": {"target_count": 10},
    "missing_params": ["environment", "region"],
    "requires_approval": false
}
```

**After (Week 7-8):**
```python
PM: "Scale frontend to 10"
Context Injected: frontend-prod is running 5 instances in us-east-1
Parser Output:
{
    "intent_type": "scale",
    "target_service": "frontend",
    "target_env": "production",  # Auto-filled from context
    "parameters": {
        "target_count": 10,
        "current_count": 5,  # From context
        "region": "us-east-1"  # From context
    },
    "missing_params": [],
    "requires_approval": true  # Production scaling
}
```

**Success Criteria:**
- Reduces ambiguity rate by >50%
- Auto-fills environment in >80% of cases
- Validates service existence before decomposition
- Maintains backward compatibility with Week 3-4

---

### CONTEXT-007: Drift Alert UI Component ⏱️ Day 7-8

**Goal:** Frontend component showing configuration drift.

**Features:**
1. **Drift Dashboard**
   - Real-time drift count (critical/warning/info)
   - Drift timeline (last 24 hours)
   - Filterable by service/severity

2. **Drift Detail View**
   - Before/after comparison
   - Change attribution (who/when)
   - "Accept Drift" or "Revert" actions

3. **Alert Banner**
   - Top-of-screen notification for critical drift
   - Dismissible warnings
   - Auto-refresh every 1 minute

**Deliverable:** `frontend/components/DriftAlert.tsx`

**Component Structure:**
```typescript
interface DriftEvent {
  resource_id: string;
  resource_type: string;
  field_changed: string;
  old_value: any;
  new_value: any;
  severity: 'critical' | 'warning' | 'info';
  detected_at: string;
  changed_by?: string;
  change_source: string;
}

interface DriftAlertProps {
  driftEvents: DriftEvent[];
  onAcceptDrift: (resourceId: string) => void;
  onRevertDrift: (resourceId: string) => void;
  onDismiss: () => void;
}

export function DriftAlert(props: DriftAlertProps): JSX.Element;
export function DriftTimeline(props: { events: DriftEvent[] }): JSX.Element;
export function DriftDetail(props: { event: DriftEvent }): JSX.Element;
```

**UI Wireframe:**
```
┌────────────────────────────────────────────────────────────┐
│ ⚠️ CONFIGURATION DRIFT DETECTED                            │
│                                                    [Dismiss]│
│ 2 critical changes detected in production environment      │
│ [View Details]                                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ Drift Events (Last 24 Hours)                               │
│ ┌──────────┬─────────┬─────────┐                          │
│ │ Critical │ Warning │  Info   │                          │
│ │    2     │    5    │    8    │                          │
│ └──────────┴─────────┴─────────┘                          │
│                                                            │
│ ● frontend-prod | Instance count 5→7 | 10 min ago         │
│   Manual change by user@company.com via AWS Console       │
│   [Accept Drift] [Revert to 5]                            │
│                                                            │
│ ● api-prod | Version v3.5.0→v3.4.2 | 1 hour ago           │
│   Manual rollback by ops@company.com via CLI              │
│   [Accept Drift] [Revert to v3.5.0]                       │
│                                                            │
│ ⓘ rds-main | Tags updated | 2 hours ago                   │
│   Automated change by CloudFormation                      │
│   [Dismiss]                                                │
└────────────────────────────────────────────────────────────┘
```

**Success Criteria:**
- Shows drift events in real-time
- Color-coded severity (red/yellow/blue)
- Accept/Revert actions functional
- Mobile-responsive
- Auto-refreshes every 60 seconds

---

### CONTEXT-008: Integration Tests ⏱️ Day 8-9

**Goal:** End-to-end tests for context layer.

**Test Scenarios:**
1. **Context Collection**
   - Fetch all resources successfully
   - Handle AWS API errors gracefully
   - Save snapshots correctly

2. **Context Injection**
   - Inject context for ambiguous commands
   - Handle missing context
   - Token budget management

3. **Drift Detection**
   - Detect instance count changes
   - Detect version changes
   - Categorize severity correctly

4. **Context-Aware Parsing**
   - Auto-fill environment from context
   - Validate service existence
   - Apply smart defaults

5. **Drift UI**
   - Render drift events
   - Accept/Revert actions
   - Real-time updates

**Deliverable:** `tests/integration/context_integration_test.py`

**Test Structure:**
```python
class TestContextIntegration(unittest.TestCase):
    def test_001_collect_resources(self)
    def test_002_inject_context_reduces_ambiguity(self)
    def test_003_detect_drift_instance_count(self)
    def test_004_detect_drift_version_change(self)
    def test_005_context_aware_parsing(self)
    def test_006_drift_severity_categorization(self)
    def test_007_full_pipeline_with_context(self)
```

**Success Criteria:**
- All 7 integration tests pass
- Context reduces parser ambiguity by >50%
- Drift detection accuracy >95%

---

### CONTEXT-009: Documentation & Corner Cases ⏱️ Day 9-10

**Goal:** Document all edge cases and usage patterns.

**Deliverable:** `phase1-nlp/context/CORNER_CASES_CONTEXT.md`

**Corner Cases to Document:**

1. **Context Freshness**
   - What if context is 20 minutes old?
   - PM command vs. stale context conflict

2. **Resource Not Found**
   - Service mentioned in command doesn't exist in context
   - Deleted resource still in snapshot

3. **Multiple Matches**
   - "frontend" matches frontend-prod, frontend-staging, frontend-dev
   - Disambiguation strategy

4. **Context Overload**
   - Too many resources (>100)
   - Token budget exceeded
   - Filtering strategy

5. **AWS API Failures**
   - Throttling during collection
   - Network timeout
   - Partial results handling

6. **Drift False Positives**
   - ECS task restarts (expected)
   - Auto-scaling events
   - Scheduled maintenance

7. **Multi-Region Resources**
   - Same service name in multiple regions
   - Cross-region dependencies

8. **Zero Context**
   - No resources tagged with `Managed: PromptOps`
   - Fresh AWS account

9. **Drift During Execution**
   - Context changes while task is executing
   - Validation before each sub-task

10. **Cost Optimization**
    - Minimize AWS API calls
    - Cache strategy
    - Incremental updates vs. full refresh

**Deliverable:** `phase1-nlp/context/CONTEXT_ARCHITECTURE.md`

**Documentation Sections:**
- Architecture diagram
- Data flow
- API reference
- Configuration options
- Deployment guide
- Monitoring & alerting
- Cost analysis

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context Collection Time | <30s for 100 resources | Load testing |
| Drift Detection Accuracy | >95% | Manual verification |
| Parser Ambiguity Reduction | >50% | Compare Week 3-4 vs. Week 7-8 |
| Context Token Budget | <2000 tokens | Token counting |
| Polling Reliability | >99.5% uptime | 7-day monitoring |
| UI Render Time | <200ms | Chrome DevTools |
| Integration Test Pass Rate | 100% (7/7) | Test runner |
| AWS API Cost | <$5/month | CloudWatch billing |

---

## Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Context Store | JSON files (dev) / DynamoDB (prod) | Flexible schema, fast writes |
| AWS SDK | boto3 (Python) | Official AWS SDK |
| Polling Service | Python `schedule` (dev) / Lambda (prod) | Simple, reliable |
| Drift Detection | Python difflib | Built-in, no dependencies |
| Frontend | React + TypeScript | Matches Week 5-6 UI |
| State Management | React Context API | Simple, no Redux needed |
| Real-time Updates | Polling (1 min interval) | WebSockets optional for v2 |

---

## Dependencies

### Upstream (Week 5-6)
- Parser output format (parsed_intent)
- Decomposition engine input

### Downstream (Week 9-10)
- PM Dashboard integration
- Drift Alert UI placement

### External
- AWS credentials (IAM role with read-only access)
- boto3 library
- CloudTrail (for change attribution)

---

## Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| AWS API rate limiting | High | Exponential backoff, caching, batch requests |
| Context becomes stale during execution | Medium | Re-validate before each sub-task |
| Too many drift false positives | Medium | Whitelist expected changes (auto-scaling, restarts) |
| DynamoDB costs for large context | Low | Use on-demand billing, TTL for old snapshots |
| Context injection exceeds token budget | Medium | Intelligent filtering, summarization |

---

## Deployment Strategy

### Development
- Local JSON file storage
- Manual polling (`python drift_polling_service.py`)
- Mock AWS responses for testing

### Production
- DynamoDB context store
- AWS Lambda for polling (CloudWatch Events trigger)
- IAM role with read-only AWS access
- CloudWatch Logs for monitoring

---

## Cost Estimate

### AWS Services
- **DynamoDB**: ~$2/month (on-demand, 1GB storage, 100K reads)
- **Lambda**: Free tier (96 invocations/day × 30s each)
- **CloudWatch**: ~$1/month (logs + events)
- **CloudTrail**: ~$2/month (change attribution lookups)

**Total**: ~$5/month

### Claude API
- Context injection adds ~500 tokens per request
- 100 requests/day × 500 tokens × $0.003/1K = $0.15/day
- **Monthly**: ~$4.50

**Grand Total**: ~$10/month

---

## Exit Criteria

Week 7-8 is complete when:

- ✅ Context store schema finalized and validated
- ✅ Context collector fetches 10+ AWS resource types
- ✅ Context injector reduces parser ambiguity by >50%
- ✅ Drift detector identifies changes with >95% accuracy
- ✅ Polling service runs reliably every 15 minutes
- ✅ Drift Alert UI renders real-time drift events
- ✅ All 7 integration tests pass
- ✅ Documentation complete (architecture, corner cases, API reference)

---

## Timeline

```
Week 7 (May 19-23):
  Day 1-2: CONTEXT-001 (Schema) + CONTEXT-002 (Collector)
  Day 3-4: CONTEXT-003 (Injector) + CONTEXT-004 (Drift Detector)
  Day 5:   CONTEXT-005 (Polling Service)

Week 8 (May 26-30):
  Day 6-7: CONTEXT-006 (Enhanced Parser) + CONTEXT-007 (Drift UI)
  Day 8-9: CONTEXT-008 (Integration Tests)
  Day 10:  CONTEXT-009 (Documentation)
```

---

## Next Steps

After Week 7-8 completion:
- **Week 9-10**: PM Dashboard Shell (integrate Drift Alert UI)
- **Week 11-12**: End-to-end integration & testing

---

**Status**: 🚧 **READY TO START**  
**First Task**: CONTEXT-001 - Infrastructure Context Store Schema  
**Est. Time**: 2-3 hours

---

*Created: 2026-04-28*  
*Week 7-8 Context & Memory Layer*
