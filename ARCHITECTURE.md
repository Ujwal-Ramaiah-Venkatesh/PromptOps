# PromptOps System Architecture

**Week 11-12 Deliverable**: Complete system architecture documentation.

**Version**: 1.0.0  
**Last Updated**: 2026-04-29

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Security Architecture](#security-architecture)
6. [Scalability & Performance](#scalability--performance)
7. [Technology Stack](#technology-stack)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React Dashboard (SPA)                                   │   │
│  │  - Command input with autocomplete                       │   │
│  │  - Real-time intent preview                              │   │
│  │  - Task decomposition view                               │   │
│  │  - Approval workflow                                     │   │
│  │  - Audit trail & drift monitoring                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/REST
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       API Gateway Layer                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI (Python 3.11)                                   │   │
│  │  - RESTful endpoints                                     │   │
│  │  - Input validation (Pydantic)                           │   │
│  │  - CORS handling                                         │   │
│  │  - Error handling                                        │   │
│  │  - Rate limiting                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────┬────────────────┬────────────────┬─────────────────┘
             │                │                │
    ┌────────▼────────┐  ┌───▼───────┐  ┌────▼────────┐
    │                 │  │           │  │             │
    │  Phase 1: NLP   │  │  Phase 2: │  │  Context    │
    │  - Parser       │  │  Decomp   │  │  Layer      │
    │  - Claude API   │  │  - Engine │  │  - AWS      │
    │  - Intent       │  │  - Tasks  │  │  - State    │
    │    extraction   │  │  - Risk   │  │  - Drift    │
    │                 │  │  - Deps   │  │             │
    └─────────────────┘  └───────────┘  └─────────────┘
             │                │                │
             └────────────────┼────────────────┘
                              │
              ┌───────────────▼──────────────┐
              │   Database Layer             │
              │   PostgreSQL 15              │
              │   - Audit log                │
              │   - Decompositions           │
              │   - Executions               │
              │   - Context snapshots        │
              │   - Drift events             │
              └──────────────────────────────┘
```

---

### Design Principles

1. **Separation of Concerns**: Each phase handles distinct functionality
2. **Stateless Services**: API Gateway is stateless (state in DB)
3. **Event-Driven**: Context layer polls AWS, publishes drift events
4. **Idempotent Operations**: All operations can be safely retried
5. **Audit Everything**: Immutable audit trail for compliance
6. **Fail-Safe Defaults**: Production operations require explicit approval

---

## Architecture Patterns

### 1. Layered Architecture

```
┌──────────────────────────────────────────┐
│  Presentation Layer (React Dashboard)   │
│  - UI components                         │
│  - State management (hooks)              │
│  - API client                            │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│  API Layer (FastAPI Gateway)             │
│  - Request validation                    │
│  - Business logic orchestration          │
│  - Response serialization                │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│  Business Logic Layer                    │
│  - NLP parsing (Phase 1)                 │
│  - Task decomposition (Phase 2)          │
│  - Context awareness                     │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│  Data Layer (PostgreSQL + SQLAlchemy)    │
│  - CRUD operations                       │
│  - Transactions                          │
│  - Constraints & validations             │
└──────────────────────────────────────────┘
```

---

### 2. Command Query Responsibility Segregation (CQRS)

**Commands** (state-changing):
- Parse intent → Write to decompositions table
- Execute task → Write to executions table
- Acknowledge drift → Update drift_events table

**Queries** (read-only):
- Get audit trail → Read from audit_log
- Get drift events → Read from drift_events
- Get execution status → Read from executions

**Benefits**:
- Separate read/write models
- Optimize queries independently
- Scale reads and writes separately

---

### 3. Repository Pattern

**Database abstraction layer**:

```python
# database/db.py
class AuditLogDB:
    @staticmethod
    def get_recent(db: Session, limit: int, filters: dict):
        """Query audit log with filters."""
        query = db.query(AuditLog)
        # Apply filters
        return query.limit(limit).all()
    
    @staticmethod
    def create(db: Session, entry: dict):
        """Create audit log entry."""
        audit = AuditLog(**entry)
        db.add(audit)
        db.commit()
        return audit
```

**Benefits**:
- Decouple business logic from data access
- Easy to mock for testing
- Consistent API across all tables

---

### 4. Dependency Injection

**FastAPI's dependency injection**:

```python
# api_gateway/main.py
def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/parse-intent")
async def parse_intent(
    request: ParseIntentRequest,
    db: Session = Depends(get_db)  # Injected
):
    # Use db session
    pass
```

**Benefits**:
- Testable (can inject mocks)
- Reusable across endpoints
- Automatic cleanup (finally block)

---

## Component Details

### Frontend: React Dashboard

**Location**: `frontend/dashboard/`

**Structure**:
```
frontend/dashboard/
├── src/
│   ├── components/
│   │   ├── CommandInput.tsx        # Natural language input
│   │   ├── IntentPreview.tsx       # Parsed intent display
│   │   ├── TaskPreview.tsx         # Decomposed tasks
│   │   ├── ApprovalFlow.tsx        # Production approval
│   │   ├── AuditTrail.tsx          # Historical operations
│   │   └── DriftAlert.tsx          # Drift notifications
│   ├── hooks/
│   │   └── useDashboardState.ts    # Centralized state logic
│   ├── utils/
│   │   └── api.ts                  # API client with retry logic
│   └── App.tsx                     # Main app
├── public/
└── package.json
```

**Key Features**:
- **Debounced intent parsing**: 500ms delay to reduce API calls
- **Real-time preview**: Shows intent while typing
- **Typed approval workflow**: User must type exact phrase
- **Drift polling**: Checks every 60 seconds
- **Error handling**: Unified error display with retries

**State Management**:
```typescript
// Custom hook manages all dashboard state
const [state, actions] = useDashboardState({
  user: 'pm@company.com',
  pollingInterval: 60000
});

// State includes:
// - command, parsedIntent, decomposition
// - auditEntries, driftEvents
// - loading states, errors

// Actions include:
// - handleCommandChange()
// - handleSubmit()
// - handleApprove()
// - refreshAudit()
```

---

### API Gateway

**Location**: `api_gateway/main.py`

**Endpoints**:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/api/v1/parse-intent` | Parse natural language |
| POST | `/api/v1/decompose` | Decompose into tasks |
| POST | `/api/v1/execute` | Execute task plan |
| GET | `/api/v1/execution/{id}` | Get execution status |
| POST | `/api/v1/execution/{id}/cancel` | Cancel execution |
| GET | `/api/v1/audit` | Query audit trail |
| GET | `/api/v1/audit/export` | Export audit to CSV |
| GET | `/api/v1/drift/recent` | Get recent drift |
| POST | `/api/v1/drift/{id}/acknowledge` | Acknowledge drift |
| POST | `/api/v1/drift/{id}/revert` | Revert drift |

**Middleware**:
- CORS (development: `*`, production: specific domains)
- Error handling (catch-all exception handler)
- Request logging (structured JSON logs)

**Validation**:
```python
from pydantic import BaseModel, EmailStr, constr

class ParseIntentRequest(BaseModel):
    command: constr(min_length=1, max_length=10000)
    user: EmailStr
    
    class Config:
        schema_extra = {
            "example": {
                "command": "Deploy frontend v2.0 to staging",
                "user": "pm@company.com"
            }
        }
```

---

### Phase 1: NLP Parser

**Location**: `phase1-nlp/parser/`

**Components**:

1. **Basic Parser** (`intent_parser.py`):
   - Claude API integration
   - Intent extraction (deploy, scale, rollback, query)
   - Confidence scoring
   - Parameter extraction

2. **Context-Aware Parser** (`context_aware_parser.py`):
   - Extends basic parser
   - Injects current AWS state
   - Enriches with environment info
   - Resolves ambiguities

**Flow**:
```
User command
    ↓
[1] Clean & normalize text
    ↓
[2] Get AWS context (if available)
    ↓
[3] Build Claude prompt with context
    ↓
[4] Call Claude API (Sonnet 4.5)
    ↓
[5] Parse JSON response
    ↓
[6] Validate intent structure
    ↓
[7] Calculate confidence score
    ↓
Return intent
```

**Intent Structure**:
```python
{
  "intent_type": "deploy",
  "target_service": "frontend",
  "target_env": "staging",
  "version": "v2.0.0",
  "confidence": 0.95,
  "parameters": {...},
  "missing_params": [],
  "context_used": {...}
}
```

---

### Phase 2: Task Decomposition

**Location**: `phase2-decomposition/engine/`

**Components**:

1. **Decomposition Engine** (`decomposition_engine.py`):
   - Intent → sub-tasks breakdown
   - Dependency resolution
   - Risk assessment
   - Rollback planning

2. **Risk Assessor** (`risk_assessor.py`):
   - Environment-based risk (production = high)
   - Operation type risk (deploy > scale)
   - Approvals required
   - Approval level (engineer/manager)

3. **Dependency Resolver** (`dependency_resolver.py`):
   - Task ordering
   - Parallel vs sequential
   - Circular dependency detection

**Flow**:
```
Intent
    ↓
[1] Load decomposition prompt
    ↓
[2] Build context (intent + AWS state)
    ↓
[3] Call Claude API
    ↓
[4] Parse sub-tasks
    ↓
[5] Resolve dependencies
    ↓
[6] Assess risk
    ↓
[7] Generate rollback plan
    ↓
[8] Store in database
    ↓
Return decomposition
```

**Decomposition Structure**:
```python
{
  "decomposition_id": "decomp-abc123",
  "operation_id": "op-xyz789",
  "total_sub_tasks": 6,
  "sub_tasks": [
    {
      "task_id": "task-1",
      "description": "Validate new version exists",
      "command": "aws ecr describe-images...",
      "dependencies": [],
      "estimated_time": 10,
      "can_fail": false
    },
    # ... more tasks
  ],
  "execution_order": [1, 2, 3, 4, 5, 6],
  "risk_assessment": {
    "overall_risk": "medium",
    "requires_approval": false,
    "approval_level": null,
    "risk_factors": [...]
  },
  "rollback_plan": {
    "total_steps": 3,
    "steps": [...]
  }
}
```

---

### Context Layer

**Location**: `phase1-nlp/context/`

**Components**:

1. **AWS Client** (`aws_client.py`):
   - Boto3 wrapper
   - Service inventory (ECS, RDS, S3)
   - Resource details
   - Current state

2. **Context Collector** (`context_collector.py`):
   - Periodic AWS polling (5 min)
   - State snapshots
   - Drift detection trigger

3. **Drift Detector** (`drift_detector.py`):
   - Compare expected vs actual
   - Classify drift severity
   - Determine auto-fixable
   - Store drift events

**Context Snapshot**:
```python
{
  "snapshot_id": "snap-abc123",
  "timestamp": "2026-04-29T10:30:00Z",
  "services": {
    "ecs": {
      "frontend": {
        "desired_count": 3,
        "running_count": 3,
        "task_definition": "frontend:42",
        "deployment_status": "active"
      }
    },
    "rds": {...},
    "s3": {...}
  },
  "metrics": {
    "cpu_utilization": 45.2,
    "memory_utilization": 62.8,
    "request_count": 1250
  }
}
```

**Drift Event**:
```python
{
  "id": "drift-xyz789",
  "detected_at": "2026-04-29T10:35:00Z",
  "resource_type": "ecs_service",
  "resource_id": "frontend",
  "field": "desired_count",
  "expected_value": 3,
  "actual_value": 2,
  "severity": "medium",
  "auto_fixable": true,
  "fix_command": "aws ecs update-service --desired-count 3",
  "acknowledged_by": null,
  "reverted_by": null
}
```

---

### Database Layer

**Location**: `database/`

**Schema** (`schema.sql`):

**Tables**:
1. `audit_log`: Immutable operation history
2. `decompositions`: Task plans
3. `executions`: Execution tracking
4. `execution_logs`: Granular step logs
5. `context_snapshots`: AWS state history
6. `drift_events`: Infrastructure drift
7. `users`: User profiles (future)
8. `api_keys`: API authentication (future)

**Key Design Choices**:

1. **UUIDs**: Globally unique IDs, no collisions
2. **JSONB**: Flexible schema for task plans, logs
3. **Timestamps**: Always UTC with timezone
4. **Indexes**: On all query columns (user, env, status, timestamp)
5. **Triggers**: Auto-update `updated_at` on changes
6. **Immutable**: Audit log cannot be updated/deleted

**ORM Models** (`models.py`):
```python
from sqlalchemy import Column, String, DateTime, JSON, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_email = Column(String(255), nullable=False, index=True)
    command = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    target_env = Column(String(50), index=True)
    task_plan = Column(JSON)
    # ... more fields
```

---

## Data Flow

### Flow 1: Command to Execution

```
┌─────────────────────────────────────────────────────────────┐
│  1. User Types Command                                      │
│     "Deploy frontend v2.0 to staging"                       │
└────────────┬────────────────────────────────────────────────┘
             │
             │ POST /api/v1/parse-intent
             │
┌────────────▼────────────────────────────────────────────────┐
│  2. API Gateway                                             │
│     - Validate request (Pydantic)                           │
│     - Call ContextAwareParser                               │
└────────────┬────────────────────────────────────────────────┘
             │
             │ parse_command_with_context()
             │
┌────────────▼────────────────────────────────────────────────┐
│  3. Context-Aware Parser                                    │
│     - Get AWS context (current frontend version)            │
│     - Build Claude prompt                                   │
│     - Call Claude API                                       │
│     - Extract intent                                        │
│     - Return: {intent_type: "deploy", ...}                  │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Return intent (200 OK)
             │
┌────────────▼────────────────────────────────────────────────┐
│  4. Dashboard Shows Intent Preview                          │
│     Intent Type: deploy                                     │
│     Service: frontend                                       │
│     Environment: staging                                    │
│     Version: v2.0.0                                         │
│     Confidence: 95%                                         │
│                                                             │
│     [Submit] button enabled                                 │
└────────────┬────────────────────────────────────────────────┘
             │
             │ User clicks Submit
             │ POST /api/v1/decompose
             │
┌────────────▼────────────────────────────────────────────────┐
│  5. Decomposition Engine                                    │
│     - Load decomposition prompt                             │
│     - Call Claude API with intent                           │
│     - Parse sub-tasks                                       │
│     - Resolve dependencies (task order)                     │
│     - Assess risk (staging = medium)                        │
│     - Generate rollback plan                                │
│     - Store in decompositions table                         │
│     - Return: {decomposition_id, sub_tasks, risk, ...}      │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Return decomposition (200 OK)
             │
┌────────────▼────────────────────────────────────────────────┐
│  6. Dashboard Shows Task Preview                            │
│     6 sub-tasks:                                            │
│     ✓ 1. Validate version exists                           │
│     ✓ 2. Create backup                                     │
│     ✓ 3. Update task definition                            │
│     ✓ 4. Deploy to ECS                                     │
│     ✓ 5. Wait for healthy                                  │
│     ✓ 6. Verify deployment                                 │
│                                                             │
│     Risk: MEDIUM (no approval required)                     │
│     [Execute] button enabled                                │
└────────────┬────────────────────────────────────────────────┘
             │
             │ User clicks Execute
             │ POST /api/v1/execute
             │
┌────────────▼────────────────────────────────────────────────┐
│  7. Execute Task Plan                                       │
│     - Create execution record in database                   │
│     - Start background execution (async)                    │
│     - Return execution_id immediately                       │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Return {execution_id: "exec-abc123"} (200 OK)
             │
┌────────────▼────────────────────────────────────────────────┐
│  8. Dashboard Polls Execution Status                        │
│     Every 5s: GET /api/v1/execution/exec-abc123             │
│                                                             │
│     Status: running (3/6 tasks completed)                   │
│     [Cancel] button enabled                                 │
└────────────┬────────────────────────────────────────────────┘
             │
             │ (Background: tasks executing)
             │
┌────────────▼────────────────────────────────────────────────┐
│  9. Execution Completes                                     │
│     - Update execution status = "completed"                 │
│     - Write to audit_log (immutable record)                 │
│     - Send notification (future)                            │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Final poll returns status = "completed"
             │
┌────────────▼────────────────────────────────────────────────┐
│  10. Dashboard Shows Success                                │
│      ✅ Deployment successful!                              │
│      All 6 tasks completed in 142 seconds                   │
│                                                             │
│      View in Audit Trail →                                  │
└─────────────────────────────────────────────────────────────┘
```

---

### Flow 2: Drift Detection & Revert

```
┌──────────────────────────────────────────────────────────┐
│  1. Context Collector (Background Service)              │
│     - Runs every 5 minutes                               │
│     - Polls AWS for current state                        │
│     - Stores snapshot in context_snapshots table         │
└────────────┬─────────────────────────────────────────────┘
             │
             │ trigger drift detection
             │
┌────────────▼─────────────────────────────────────────────┐
│  2. Drift Detector                                       │
│     - Compare latest snapshot to expected state          │
│     - Found: frontend desired_count = 2 (expected 3)     │
│     - Severity: MEDIUM                                   │
│     - Auto-fixable: YES                                  │
│     - Store drift event in drift_events table            │
└────────────┬─────────────────────────────────────────────┘
             │
             │ (Drift event stored)
             │
┌────────────▼─────────────────────────────────────────────┐
│  3. Dashboard Polls Drift Endpoint                       │
│     Every 60s: GET /api/v1/drift/recent                  │
│                                                          │
│     Response: 1 unacknowledged drift event               │
└────────────┬─────────────────────────────────────────────┘
             │
             │ Show drift alert banner
             │
┌────────────▼─────────────────────────────────────────────┐
│  4. Dashboard Shows Drift Alert                          │
│     ⚠️  Infrastructure Drift Detected!                   │
│                                                          │
│     frontend: desired_count                              │
│     Expected: 3, Actual: 2                               │
│                                                          │
│     [Acknowledge] [Revert]                               │
└────────────┬─────────────────────────────────────────────┘
             │
             │ User clicks Revert
             │ POST /api/v1/drift/{id}/revert
             │
┌────────────▼─────────────────────────────────────────────┐
│  5. Revert Drift                                         │
│     - Execute fix command:                               │
│       aws ecs update-service --desired-count 3           │
│     - Update drift event (reverted_by = user)            │
│     - Create audit log entry                             │
└────────────┬─────────────────────────────────────────────┘
             │
             │ Return success (200 OK)
             │
┌────────────▼─────────────────────────────────────────────┐
│  6. Dashboard Hides Alert                                │
│     ✅ Drift reverted successfully                       │
│     frontend back to desired_count = 3                   │
└──────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Authentication & Authorization

**Current**: No authentication (MVP phase)

**Future** (before production):

1. **OAuth 2.0 / OpenID Connect**:
   - SSO integration (Google Workspace, Okta)
   - JWT tokens
   - Refresh token rotation

2. **Role-Based Access Control (RBAC)**:
   ```
   Roles:
   - viewer: Read-only (audit trail, drift)
   - engineer: Deploy to staging, scale
   - lead: Deploy to production (with approval)
   - admin: All operations, user management
   ```

3. **Environment-Based Permissions**:
   ```python
   @require_permission("deploy:production")
   async def execute_task(...):
       pass
   ```

---

### Secrets Management

**Current**: `.env` files (development only)

**Production**:
- AWS Secrets Manager for all credentials
- Automatic rotation (30 days)
- IAM roles for ECS tasks (no long-lived credentials)

---

### Network Security

```
┌────────────────────────────────────────────┐
│  Internet                                  │
└─────────────┬──────────────────────────────┘
              │ HTTPS only
              │
    ┌─────────▼─────────┐
    │  CloudFront WAF   │
    │  - DDoS protection│
    │  - Rate limiting  │
    │  - IP filtering   │
    └─────────┬─────────┘
              │
    ┌─────────▼─────────┐
    │  ALB (public)     │
    │  - TLS termination│
    │  - Health checks  │
    └─────────┬─────────┘
              │
    ┌─────────▼─────────┐
    │  ECS (private)    │
    │  - No public IPs  │
    │  - Security groups│
    └─────────┬─────────┘
              │
    ┌─────────▼─────────┐
    │  RDS (private)    │
    │  - Encrypted      │
    │  - VPC only       │
    └───────────────────┘
```

---

## Scalability & Performance

### Horizontal Scaling

**ECS Auto-scaling**:
```yaml
Target CPU: 70%
Min tasks: 2
Max tasks: 10
Scale out: +2 tasks when CPU > 70% for 2 min
Scale in: -1 task when CPU < 50% for 5 min
```

**Database Read Replicas**:
- Primary: writes + reads
- Replica 1: audit queries
- Replica 2: context snapshots

---

### Caching Strategy

**Future enhancements**:

1. **Redis for Intent Parsing**:
   ```python
   cache_key = f"intent:{hash(command)}"
   cached = redis.get(cache_key)
   if cached:
       return json.loads(cached)
   # Parse and cache for 5 min
   ```

2. **CDN Caching** (frontend):
   - HTML: No cache
   - JS/CSS: 1 year (immutable, hashed filenames)
   - Images: 1 month

---

### Performance Targets

| Metric | Target (p95) | Critical (p99) |
|--------|--------------|----------------|
| Parse intent | <500ms | <1s |
| Decompose | <2s | <5s |
| Audit query | <200ms | <500ms |
| Drift check | <100ms | <300ms |
| UI load | <2s | <3s |

---

## Technology Stack

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.3.3
- **Build**: Vite
- **State**: React Hooks (custom)
- **HTTP**: Fetch API with retry logic
- **Styling**: CSS Modules

### Backend
- **Framework**: FastAPI 0.109.0
- **Language**: Python 3.11
- **ASGI**: Uvicorn
- **Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15

### AI/ML
- **LLM**: Anthropic Claude Sonnet 4.5
- **SDK**: anthropic-sdk-python 0.18.0
- **Context**: 200K tokens
- **Prompts**: Structured JSON output

### Infrastructure
- **Container**: Docker (multi-stage)
- **Orchestration**: ECS Fargate
- **Database**: RDS PostgreSQL 15 (Multi-AZ)
- **Storage**: S3
- **CDN**: CloudFront
- **Load Balancer**: ALB
- **Monitoring**: CloudWatch

### DevOps
- **CI/CD**: GitHub Actions
- **IaC**: AWS CLI (future: Terraform)
- **Secrets**: AWS Secrets Manager
- **Logging**: CloudWatch Logs
- **Metrics**: CloudWatch Metrics

---

## Future Enhancements

1. **Real-time Notifications**: WebSockets for execution progress
2. **Multi-region**: Active-active deployment
3. **A/B Testing**: Canary deployments
4. **Cost Optimization**: Reserved instances, spot instances
5. **Advanced Monitoring**: Grafana dashboards, custom metrics
6. **ML Improvements**: Fine-tuned models, prompt optimization
7. **Mobile App**: React Native dashboard

---

**Author**: PromptOps Team  
**Reviewed By**: Architecture Team  
**Status**: Production-Ready Architecture
