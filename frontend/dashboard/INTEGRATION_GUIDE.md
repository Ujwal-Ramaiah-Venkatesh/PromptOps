# Dashboard Integration Guide

**Week 11-12 Deliverable**: Complete guide for connecting React dashboard to FastAPI backend.

---

## Overview

This guide shows how to connect the PM Dashboard (React) to the API Gateway (FastAPI) and test the integration.

---

## Prerequisites

1. **Backend running**: API Gateway must be running on port 8000
2. **Database ready**: PostgreSQL with schema initialized
3. **Node.js**: Version 18+ installed
4. **Environment variables**: `.env.development` configured

---

## Quick Start

### 1. Start Backend

```bash
# Terminal 1: Start API Gateway
cd api_gateway
python main.py

# API will be available at: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 2. Start Frontend

```bash
# Terminal 2: Start React dashboard
cd frontend/dashboard
npm install
npm start

# Dashboard will be available at: http://localhost:3000
```

### 3. Test Connection

```bash
# Terminal 3: Run connection test
cd frontend/dashboard
node scripts/test-api-connection.js
```

Expected output:
```
==========================================
  API Connection Test Suite
==========================================
  API Base URL: http://localhost:8000
==========================================

🔍 Testing health check endpoint...
✅ Health check passed
   Status: healthy
   Version: 1.0.0
   Services: {"parser": "ok", "decomposer": "ok", "database": "ok"}

🔍 Testing parse-intent endpoint...
✅ Parse intent passed
   Intent type: deploy
   Target service: frontend
   Target env: staging
   Confidence: 0.95
   Parse time: 342 ms

🔍 Testing audit trail endpoint...
✅ Audit trail passed
   Total entries: 0
   Returned: 0
   Page: 1

🔍 Testing drift endpoint...
✅ Drift endpoint passed
   Events: 0
   Unacknowledged: 0
   Last check: 2026-04-29T10:30:00Z

==========================================
  Test Results
==========================================
  Health Check: ✅
  Parse Intent: ✅
  Audit Trail: ✅
  Drift Events: ✅
==========================================

  Passed: 4/4 tests

  🎉 All tests passed! Dashboard is ready to connect.
```

---

## Configuration

### Frontend Environment Variables

**`.env.development`** (already configured):
```bash
REACT_APP_API_BASE_URL=http://localhost:8000/api/v1
REACT_APP_DRIFT_POLLING_INTERVAL=60000
REACT_APP_AUDIT_REFRESH_INTERVAL=30000
REACT_APP_ENABLE_AUTO_REFRESH=true
```

**`.env.production`**:
```bash
REACT_APP_API_BASE_URL=https://api.promptops.com/api/v1
REACT_APP_DRIFT_POLLING_INTERVAL=60000
REACT_APP_ENABLE_AUTO_REFRESH=true
REACT_APP_DEBUG=false
```

### Backend Environment Variables

**API Gateway** (`api_gateway/.env`):
```bash
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://promptops:password@localhost:5432/promptops
```

---

## API Integration Points

### 1. Parse Intent

**Frontend** (`useDashboardState.ts`):
```typescript
const data = await apiClient.parseIntent(command, user);
setState(prev => ({
  ...prev,
  parsedIntent: data.intent,
  isParsingIntent: false
}));
```

**Backend** (`api_gateway/main.py`):
```python
@app.post("/api/v1/parse-intent")
async def parse_intent(request: ParseIntentRequest):
    success, intent_dict, message = parser.parse_command_with_context(request.command)
    return {"intent": intent_dict, "parse_time_ms": parse_time}
```

**Flow**:
1. User types command in CommandInput
2. After 500ms debounce → API call
3. Backend parses with ContextAwareParser
4. Returns intent with confidence score
5. Dashboard shows intent preview

---

### 2. Decompose Task

**Frontend**:
```typescript
const data = await apiClient.decompose(intent, user);
setState(prev => ({
  ...prev,
  decomposition: data.decomposition,
  showApproval: data.decomposition.risk_assessment.requires_approval
}));
```

**Backend**:
```python
@app.post("/api/v1/decompose")
async def decompose_task(request: DecomposeRequest):
    success, decomposition_dict, message = decomposer.decompose(request.intent)
    return {"decomposition": decomposition_dict, "decompose_time_ms": decompose_time}
```

**Flow**:
1. User clicks "Submit" or presses Enter
2. Frontend calls decompose API
3. Backend uses DecompositionEngine
4. Returns task plan with sub-tasks
5. Dashboard shows TaskPreview component

---

### 3. Execute Task

**Frontend**:
```typescript
const approvalPhrase = `APPROVE ${operationId}`;
const data = await apiClient.execute(
  decompositionId,
  user,
  true,
  approvalPhrase
);
```

**Backend**:
```python
@app.post("/api/v1/execute")
async def execute_task(request: ExecuteRequest):
    # Verify approval phrase
    # Create execution record
    # Start background task execution
    return {"execution_id": execution_id, "status": "queued"}
```

**Flow**:
1. If high-risk → ApprovalFlow shown
2. User types exact approval phrase
3. Frontend sends execute request
4. Backend validates phrase
5. Creates execution record
6. Returns execution ID
7. Dashboard polls for status

---

### 4. Audit Trail

**Frontend**:
```typescript
const data = await apiClient.getAudit({ limit: 50 });
setState(prev => ({
  ...prev,
  auditEntries: data.entries
}));
```

**Backend**:
```python
@app.get("/api/v1/audit")
async def get_audit_trail(limit: int = 50, user: Optional[str] = None):
    # Query database with filters
    return {"entries": entries, "total": total}
```

**Flow**:
1. Dashboard loads → refreshAudit() called
2. Backend queries PostgreSQL
3. Returns filtered entries
4. AuditTrail component displays list

---

### 5. Drift Detection

**Frontend**:
```typescript
const data = await apiClient.getDrift();
setState(prev => ({
  ...prev,
  driftEvents: data.events,
  unacknowledgedDriftCount: data.unacknowledged_count
}));
```

**Backend**:
```python
@app.get("/api/v1/drift/recent")
async def get_recent_drift():
    # Get drift events from store
    unacknowledged = [e for e in drift_store if not e.get("acknowledged_by")]
    return {"events": drift_store[-10:], "unacknowledged_count": len(unacknowledged)}
```

**Flow**:
1. Dashboard polls every 60s
2. Backend returns recent drift events
3. DriftAlert shows banner if unacknowledged
4. User can acknowledge or revert

---

## Testing Integration

### Manual Testing

1. **Start servers**:
   ```bash
   # Terminal 1
   cd api_gateway && python main.py

   # Terminal 2
   cd frontend/dashboard && npm start
   ```

2. **Test command flow**:
   - Type: "Deploy frontend v2.0 to staging"
   - Wait for intent preview (should appear in <1s)
   - Check confidence score (should be >0.8)
   - Click "Submit"
   - Wait for task preview (should appear in <3s)
   - Verify sub-tasks shown
   - Click "Execute" (or "Approve" if high-risk)

3. **Test audit trail**:
   - Scroll to audit section
   - Verify your command appears
   - Check status (should be "pending" or "completed")
   - Test filters (by user, env, status)

4. **Test drift**:
   - (Requires AWS credentials and context collector running)
   - Check drift alert banner
   - Click to expand drift events
   - Test acknowledge/revert actions

### Automated Testing

```bash
# Run connection test
node scripts/test-api-connection.js

# Run unit tests
npm test

# Run E2E tests (requires both servers running)
npm run cypress:run
```

---

## Troubleshooting

### API Gateway not starting

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd api_gateway
pip install -r requirements.txt
```

---

### CORS errors in browser console

**Problem**: `Access-Control-Allow-Origin` error

**Solution**: API Gateway already configured for CORS. Check:
1. Backend is running on port 8000
2. Frontend is running on port 3000
3. `api_gateway/main.py` has correct CORS origins

---

### Cannot connect to database

**Problem**: `psycopg2.OperationalError: could not connect`

**Solution**:
1. Start PostgreSQL: `brew services start postgresql@15`
2. Create database: `createdb promptops`
3. Initialize schema: `psql -d promptops -f database/schema.sql`
4. Check DATABASE_URL in `.env`

---

### Parse intent fails

**Problem**: `503 Service Unavailable - Parser service unavailable`

**Solution**: Set ANTHROPIC_API_KEY:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

Or in `api_gateway/.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

---

### Intent preview not showing

**Problem**: Typing command but no preview appears

**Solution**:
1. Check browser console for errors
2. Verify API Gateway is running
3. Check network tab for failed requests
4. Ensure command is >3 characters (debounce trigger)
5. Wait 500ms after typing

---

### Decomposition timeout

**Problem**: Decompose request times out after 30s

**Solution**: Increase timeout in `utils/api.ts`:
```typescript
await fetchWithTimeout(`${API_BASE_URL}/decompose`, {
  method: 'POST',
  timeout: 60000 // Increase to 60s
});
```

---

## Performance Optimization

### Caching

Add Redis caching to API Gateway:

```python
import redis
r = redis.Redis(host='localhost', port=6379)

@app.post("/api/v1/parse-intent")
async def parse_intent(request: ParseIntentRequest):
    cache_key = f"intent:{request.command}"
    cached = r.get(cache_key)

    if cached:
        return json.loads(cached)

    # Parse and cache for 5 minutes
    result = parser.parse_command_with_context(request.command)
    r.setex(cache_key, 300, json.dumps(result))
    return result
```

### Debouncing

Already implemented (500ms) in `useDashboardState.ts`:

```typescript
intentParseTimerRef.current = setTimeout(async () => {
  const data = await apiClient.parseIntent(command, user);
  // ...
}, 500);
```

### Polling Optimization

Current settings:
- Drift: 60s interval
- Audit: Manual refresh only

To enable auto-refresh:
```typescript
const [state, actions] = useDashboardState({
  user: 'pm@company.com',
  pollingInterval: 60000, // 60s
  enableAutoRefresh: true
});
```

---

## Security

### HTTPS in Production

Update `.env.production`:
```bash
REACT_APP_API_BASE_URL=https://api.promptops.com/api/v1
```

### API Authentication (Future)

Add JWT tokens:

```typescript
// Login
const token = await apiClient.login(email, password);
localStorage.setItem('auth_token', token);

// Authenticated request
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

## Next Steps

1. ✅ **Backend running**: API Gateway operational
2. ✅ **Frontend configured**: Environment variables set
3. ✅ **Integration tested**: Connection test passes
4. ⏳ **E2E testing**: Run full workflow tests
5. ⏳ **Load testing**: Performance under concurrent users
6. ⏳ **Production deployment**: Deploy to staging/prod

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000
- **Logs**: Check browser console and terminal output
- **Issues**: GitHub Issues

---

**Author**: PromptOps Team  
**Date**: 2026-04-29  
**Status**: Integration Complete
