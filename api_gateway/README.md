<div align="center">
  <img src="../assets/promptops-logo.png" alt="PromptOps Logo" width="200"/>
  
  # PromptOps API Gateway
  
  **Week 11-12 Deliverable**: Unified REST API layer connecting React dashboard to Python backend services.
</div>

---

## Overview

The API Gateway provides a single entry point for all frontend requests, routing them to appropriate backend services (parser, decomposer, context layer, drift detector).

**Technology Stack:**
- **Framework**: FastAPI (async, type-safe, auto-docs)
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic models
- **Database**: PostgreSQL (via SQLAlchemy)
- **Cache**: Redis (future)
- **Auth**: JWT tokens (future)

---

## Quick Start

### 1. Install Dependencies

```bash
cd api_gateway
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/promptops
```

### 3. Run Server

```bash
# Development (with auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8000
```

### 4. Access API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-16T10:30:00Z",
  "services": {
    "parser": "ok",
    "decomposer": "ok",
    "database": "ok"
  }
}
```

---

### Parse Intent

```http
POST /api/v1/parse-intent
Content-Type: application/json

{
  "command": "Deploy frontend v2.0 to staging",
  "user": "pm@company.com"
}
```

**Response:**
```json
{
  "intent": {
    "intent_type": "deploy",
    "target_service": "frontend",
    "target_env": "staging",
    "parameters": { "version": "v2.0" },
    "confidence": 0.95,
    "ambiguity_score": 0.05,
    "missing_params": [],
    "requires_approval": false
  },
  "parse_time_ms": 342
}
```

---

### Decompose Task

```http
POST /api/v1/decompose
Content-Type: application/json

{
  "intent": {
    "intent_type": "deploy",
    "target_service": "frontend",
    "target_env": "staging",
    "parameters": { "version": "v2.0" }
  },
  "user": "pm@company.com"
}
```

**Response:**
```json
{
  "decomposition": {
    "decomposition_id": "decomp-abc123",
    "operation_id": "op-xyz789",
    "timestamp": "2026-06-16T10:30:00Z",
    "total_sub_tasks": 6,
    "estimated_duration": 300,
    "risk_assessment": {
      "overall_risk": "medium",
      "risk_factors": ["Staging deployment", "New version"],
      "estimated_cost_impact": 100,
      "affected_users": 50,
      "requires_approval": false,
      "approval_level": "none"
    },
    "sub_tasks": [...],
    "rollback_plan": {...}
  },
  "decompose_time_ms": 1850
}
```

---

### Execute Task

```http
POST /api/v1/execute
Content-Type: application/json

{
  "decomposition_id": "decomp-abc123",
  "user": "pm@company.com",
  "approved": true,
  "approval_phrase": "APPROVE xyz789"
}
```

**Response:**
```json
{
  "execution_id": "exec-def456",
  "status": "queued",
  "started_at": "2026-06-16T10:35:00Z",
  "message": "Task execution started"
}
```

---

### Get Execution Status

```http
GET /api/v1/execution/{execution_id}
```

**Response:**
```json
{
  "execution_id": "exec-def456",
  "status": "in_progress",
  "completed_tasks": 3,
  "total_tasks": 6,
  "current_task": "Update ECS service",
  "logs": [
    "Task 1: Validate version - COMPLETED",
    "Task 2: Create task definition - COMPLETED",
    "Task 3: Update ECS service - IN_PROGRESS"
  ],
  "started_at": "2026-06-16T10:35:00Z",
  "completed_at": null
}
```

---

### Get Audit Trail

```http
GET /api/v1/audit?limit=50&user=pm@company.com&env=production&status=completed
```

**Response:**
```json
{
  "entries": [
    {
      "id": "audit-123",
      "timestamp": "2026-06-16T10:30:00Z",
      "user": "pm@company.com",
      "command": "Deploy frontend v2.0 to production",
      "intent_type": "deploy",
      "target_service": "frontend",
      "target_env": "production",
      "status": "completed",
      "risk_level": "high",
      "duration": 420
    }
  ],
  "total": 245,
  "page": 1,
  "page_size": 50
}
```

---

### Export Audit

```http
GET /api/v1/audit/export?format=csv
```

Downloads CSV file with audit entries.

---

### Get Recent Drift

```http
GET /api/v1/drift/recent
```

**Response:**
```json
{
  "events": [
    {
      "id": "drift-1",
      "timestamp": "2026-06-16T10:25:00Z",
      "resource_type": "ecs_service",
      "resource_id": "frontend-prod",
      "field": "desired_count",
      "expected_value": 5,
      "actual_value": 3,
      "severity": "critical",
      "auto_fixable": true
    }
  ],
  "unacknowledged_count": 1,
  "last_check": "2026-06-16T10:30:00Z"
}
```

---

### Acknowledge Drift

```http
POST /api/v1/drift/{drift_id}/acknowledge
Content-Type: application/json

{
  "user": "pm@company.com"
}
```

---

### Revert Drift

```http
POST /api/v1/drift/{drift_id}/revert
Content-Type: application/json

{
  "user": "pm@company.com"
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Success
- **400 Bad Request**: Invalid input
- **403 Forbidden**: Approval required or invalid approval phrase
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Backend service unavailable

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## CORS Configuration

Allowed origins:
- `http://localhost:3000` (React dev)
- `http://localhost:3001` (Alternative port)
- `https://dashboard.promptops.com` (Production)

---

## Testing

### Run Unit Tests

```bash
pytest tests/ --cov=api_gateway
```

### Test API Manually

```bash
# Health check
curl http://localhost:8000/health

# Parse intent
curl -X POST http://localhost:8000/api/v1/parse-intent \
  -H "Content-Type: application/json" \
  -d '{"command": "Deploy frontend to staging", "user": "test@test.com"}'
```

### Load Testing

```bash
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## Architecture

```
┌─────────────┐
│   React     │
│  Dashboard  │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────┐
│  FastAPI    │◀── CORS, Validation, Auth
│  Gateway    │
└──────┬──────┘
       │
       ├──▶ ContextAwareParser (Week 7-8)
       │
       ├──▶ DecompositionEngine (Week 5-6)
       │
       ├──▶ DriftDetector (Week 7-8)
       │
       └──▶ PostgreSQL Database
```

---

## Performance

**Target Metrics:**
- Intent parsing: <500ms p95
- Decomposition: <2s p95
- Audit query: <200ms p95
- Throughput: 100 req/s

**Optimization:**
- Request validation (Pydantic)
- Async handlers
- Connection pooling (SQLAlchemy)
- Redis caching (planned)
- Rate limiting (planned)

---

## Security

**Current:**
- Input validation (Pydantic)
- CORS restrictions
- SQL injection prevention (ORM)
- Approval phrase verification

**Planned:**
- JWT authentication
- Role-based access control
- API rate limiting
- Request signing

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=promptops
      - POSTGRES_USER=promptops
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
```

---

## Monitoring

**Health Endpoint**: `/health`

**Metrics** (Prometheus):
- Request count by endpoint
- Response time percentiles
- Error rate
- Active connections

**Logs**:
- Structured JSON logging
- Request/response logging
- Error tracking

---

## Roadmap

**Phase 2 (Current):**
- ✅ All endpoints functional
- ✅ Pydantic validation
- ✅ CORS configured
- ✅ Error handling

**Phase 3 (Next):**
- PostgreSQL integration
- JWT authentication
- Redis caching
- Rate limiting
- Background task execution

**Phase 4 (Future):**
- WebSocket support (real-time updates)
- GraphQL endpoint
- Metrics dashboard
- Request tracing

---

## Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Email**: support@promptops.com

---

**Author**: PromptOps Team  
**Date**: 2026-04-28  
**Version**: 1.0.0
