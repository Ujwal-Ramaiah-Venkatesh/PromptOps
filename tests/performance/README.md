# Performance & Load Testing

**Week 11-12 Deliverable**: Load testing infrastructure with Locust.

---

## Overview

Performance testing for PromptOps API Gateway to validate response times under load and identify breaking points.

**Performance Targets**:
- Parse Intent: <500ms (p95)
- Decompose Task: <2s (p95)
- Audit Queries: <200ms (p95)
- Health Check: <100ms (p95)

---

## Prerequisites

### 1. Install Locust

```bash
cd tests/performance
pip install -r requirements.txt
```

### 2. Backend Running

```bash
cd api_gateway
python main.py
```

### 3. Database Initialized

```bash
psql -d promptops -f database/schema.sql
```

---

## Quick Start

### Basic Load Test (Web UI)

```bash
cd tests/performance
locust -f load_test.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Enter: 50 users, spawn rate 10, run time 5m
```

### Headless Mode (Command Line)

```bash
locust -f load_test.py --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless
```

### Export Results

```bash
locust -f load_test.py --host=http://localhost:8000 \
  --users 50 \
  --run-time 5m \
  --html report.html \
  --csv results
```

---

## User Classes

### 1. DashboardUser (Default)

Simulates typical PM using the dashboard.

**Behavior**:
- Wait time: 1-3 seconds between requests
- Tasks (weighted):
  - Parse intent (5x) - Most common operation
  - Decompose task (2x) - After parsing
  - Query audit trail (3x) - Monitoring
  - Check drift (1x) - Periodic check
  - Health check (1x) - Periodic monitoring

**Usage**:
```bash
locust -f load_test.py --host=http://localhost:8000 --users 50
```

---

### 2. HeavyLoadUser

Simulates heavy load with minimal wait time for stress testing.

**Behavior**:
- Wait time: 0.1-0.5 seconds (very short)
- Task: Rapid-fire intent parsing
- Purpose: Find breaking point

**Usage**:
```bash
locust -f load_test.py --host=http://localhost:8000 \
  --user-classes HeavyLoadUser \
  --users 100 \
  --spawn-rate 20
```

---

### 3. ReadOnlyUser

Simulates read-only users (reporting, monitoring).

**Behavior**:
- Wait time: 2-5 seconds
- Tasks:
  - Query audit with various filters (5x)
  - Check drift events (2x)
  - Export audit to CSV (1x)

**Usage**:
```bash
locust -f load_test.py --host=http://localhost:8000 \
  --user-classes ReadOnlyUser \
  --users 50
```

---

## Load Shapes

### Step Load (Find Breaking Point)

Gradually increase users to find system capacity.

**Configuration** (in `load_test.py`):
- Step time: 60 seconds per step
- Step load: Add 10 users per step
- Spawn rate: 2 users per second
- Time limit: 10 minutes total

**Steps**:
- Minute 0-1: 10 users
- Minute 1-2: 20 users
- Minute 2-3: 30 users
- ...
- Minute 9-10: 100 users

**Usage**:
```bash
locust -f load_test.py --host=http://localhost:8000 --headless
```

The `StepLoadShape` class will automatically control user count.

---

## Test Scenarios

### Scenario 1: Normal Load

Simulate typical weekday usage.

```bash
locust -f load_test.py --host=http://localhost:8000 \
  --users 20 \
  --spawn-rate 5 \
  --run-time 10m
```

**Expected**:
- All requests <1s response time
- 0% failure rate
- Throughput: ~10-15 req/s

---

### Scenario 2: Peak Load

Simulate end-of-sprint rush (multiple teams deploying).

```bash
locust -f load_test.py --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 20 \
  --run-time 10m
```

**Expected**:
- Parse intent: <1s p95
- Decompose: <3s p95
- Some Claude API rate limiting possible
- Throughput: ~50-80 req/s

---

### Scenario 3: Stress Test

Find breaking point.

```bash
locust -f load_test.py --host=http://localhost:8000 \
  --user-classes HeavyLoadUser \
  --users 200 \
  --spawn-rate 50 \
  --run-time 5m
```

**Expected**:
- System degradation at 150-200 concurrent users
- Claude API rate limits hit
- Database connection pool exhaustion
- Increased error rates

---

### Scenario 4: Mixed Workload

Simulate realistic mix of user types.

```bash
# Terminal 1: Dashboard users
locust -f load_test.py --host=http://localhost:8000 \
  --user-classes DashboardUser \
  --users 30 \
  --spawn-rate 5 \
  --master

# Terminal 2: Read-only users
locust -f load_test.py --host=http://localhost:8000 \
  --user-classes ReadOnlyUser \
  --users 20 \
  --spawn-rate 5 \
  --worker
```

---

## Custom Metrics

The test suite tracks custom metrics beyond Locust's built-in stats.

**Metrics Tracked**:
- Parse intent latency (from API response)
- Decompose latency (from API response)
- Audit query latency

**Output** (printed at test end):
```
==========================================
Custom Performance Metrics
==========================================

PARSE:
  Count:   1247
  Min:     182 ms
  Max:     1834 ms
  Avg:     342 ms
  P50:     298 ms
  P95:     456 ms
  P99:     721 ms

DECOMPOSE:
  Count:   498
  Min:     892 ms
  Max:     4234 ms
  Avg:     1456 ms
  P50:     1298 ms
  P95:     1892 ms
  P99:     2456 ms

AUDIT:
  Count:   752
  Min:     23 ms
  Max:     234 ms
  Avg:     67 ms
  P50:     58 ms
  P95:     112 ms
  P99:     178 ms

==========================================
Performance Target Status:
==========================================
PARSE        Target: 500ms | Actual: 456ms | ✓ PASS
DECOMPOSE    Target: 2000ms | Actual: 1892ms | ✓ PASS
AUDIT        Target: 200ms | Actual: 112ms | ✓ PASS
==========================================

🎉 All performance targets met!
```

---

## Performance Targets

| Endpoint | Target (p95) | Critical (p99) |
|----------|-------------|----------------|
| Parse Intent | <500ms | <1s |
| Decompose | <2s | <5s |
| Audit Query | <200ms | <500ms |
| Drift Check | <100ms | <300ms |
| Health Check | <100ms | <200ms |

**Target Definitions**:
- **Target**: 95% of requests must be faster than this
- **Critical**: 99% of requests must be faster than this

---

## Interpreting Results

### Locust Web UI

Key metrics to watch:

1. **Requests/s**: Throughput
   - Good: 10-50 req/s
   - Stress: 100+ req/s

2. **Failure Rate**:
   - Good: <1%
   - Acceptable: 1-5%
   - Bad: >5%

3. **Response Time (p95)**:
   - Parse: <500ms
   - Decompose: <2s
   - Audit: <200ms

4. **Number of Users**:
   - Normal: 20-50
   - Peak: 50-100
   - Stress: 100+

---

### Charts

**Response Time Chart**:
- Should be relatively flat during normal load
- Expect increase during spawn phase
- Watch for exponential growth (indicates bottleneck)

**Requests per Second**:
- Should scale linearly with user count
- Plateau indicates max throughput

**Number of Users**:
- Smooth ramp-up curve
- Step pattern for StepLoadShape

---

## Troubleshooting

### High failure rate

**Problem**: >5% requests failing

**Possible causes**:
1. Claude API rate limiting
2. Database connection pool exhausted
3. Memory leak
4. Network issues

**Solution**:
```bash
# Check API Gateway logs
cd api_gateway
tail -f logs/api.log

# Check database connections
psql -d promptops -c "SELECT count(*) FROM pg_stat_activity WHERE datname='promptops';"

# Monitor memory
top -p $(pgrep -f "python main.py")
```

---

### Response times degrading

**Problem**: p95 increasing over time

**Possible causes**:
1. Memory leak (Python not releasing)
2. Database query performance
3. Claude API slowdown
4. Connection pool exhaustion

**Solution**:
```bash
# Check memory growth
watch -n 5 'ps aux | grep "python main.py"'

# Check slow queries
psql -d promptops -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Enable query logging
# In database/db.py, add:
# engine = create_engine(DATABASE_URL, echo=True)
```

---

### Claude API rate limiting

**Problem**: 429 errors from Anthropic API

**Cause**: Exceeded rate limits (10 req/s default)

**Solution**:
1. Reduce user count
2. Increase wait times
3. Implement request queuing:

```python
# In api_gateway/main.py
from asyncio import Semaphore

claude_limiter = Semaphore(5)  # Max 5 concurrent Claude requests

@app.post("/api/v1/parse-intent")
async def parse_intent(request: ParseIntentRequest):
    async with claude_limiter:
        # Parse with Claude
        pass
```

---

### Database connection errors

**Problem**: `psycopg2.pool.PoolError: connection pool exhausted`

**Cause**: Too many concurrent connections

**Solution** (in `database/db.py`):
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Increase from 10
    max_overflow=40,     # Increase from 20
    pool_pre_ping=True   # Verify connections before use
)
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2am
  workflow_dispatch:

jobs:
  load-test:
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
          pip install -r tests/performance/requirements.txt

      - name: Initialize database
        run: psql -h localhost -U promptops -d promptops -f database/schema.sql

      - name: Start API Gateway
        run: |
          cd api_gateway
          python main.py &
          sleep 10

      - name: Run load test
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd tests/performance
          locust -f load_test.py --host=http://localhost:8000 \
            --users 50 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html report.html

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: tests/performance/report.html

      - name: Check performance targets
        run: |
          # Parse Locust output and fail if targets not met
          # (Custom script needed)
```

---

## Best Practices

### 1. Baseline First

Run baseline test with 1 user to establish single-user performance:

```bash
locust -f load_test.py --host=http://localhost:8000 --users 1 --run-time 2m
```

### 2. Gradual Ramp-Up

Always use spawn rate to gradually add users:

```bash
# Good: Spawn 10 users over 10 seconds
locust --users 100 --spawn-rate 10

# Bad: Spawn all 100 users immediately
locust --users 100 --spawn-rate 100
```

### 3. Realistic Wait Times

Match production user behavior:
- Dashboard users: 1-3s between actions
- Automated systems: 0.1-1s
- Monitoring: 5-60s

### 4. Monitor Everything

During load tests, monitor:
- API Gateway CPU/Memory
- Database connections
- Claude API quota
- Network bandwidth
- Disk I/O

### 5. Test in Isolation

- Stop other services on test machine
- Use dedicated test database
- Clear caches before test
- Run during off-hours

---

## Performance Optimization Tips

### API Gateway

1. **Enable response caching** (Redis)
2. **Use connection pooling** (already implemented)
3. **Add request queuing** for Claude API
4. **Enable gzip compression**
5. **Implement rate limiting per user**

### Database

1. **Add indexes** for common queries
2. **Use materialized views** for audit summaries
3. **Partition audit_log** by month
4. **Enable query result caching**
5. **Tune connection pool** based on load test results

### Frontend

1. **Enable debouncing** (already implemented)
2. **Implement request caching** (service worker)
3. **Use pagination** for large result sets
4. **Lazy load** audit trail
5. **Reduce polling frequency**

---

## Expected Results

### Baseline (No Load)

- Parse: ~300ms
- Decompose: ~1.2s
- Audit: ~50ms
- Throughput: 1 req/s

### Normal Load (20 users)

- Parse: ~350ms (p95: ~450ms)
- Decompose: ~1.5s (p95: ~1.8s)
- Audit: ~60ms (p95: ~100ms)
- Throughput: 10-15 req/s
- Failure rate: <0.1%

### Peak Load (100 users)

- Parse: ~500ms (p95: ~800ms)
- Decompose: ~2s (p95: ~2.5s)
- Audit: ~100ms (p95: ~180ms)
- Throughput: 50-80 req/s
- Failure rate: 1-3%

### Breaking Point (200+ users)

- Response times >5s
- Failure rate >10%
- Database connection errors
- Claude API rate limiting

---

## Support

- **Locust Docs**: https://docs.locust.io/
- **Dashboard**: http://localhost:8089 (when running with Web UI)
- **API Docs**: http://localhost:8000/docs
- **Logs**: `api_gateway/logs/`

---

**Author**: PromptOps Team  
**Date**: 2026-04-29  
**Status**: Performance Testing Ready
