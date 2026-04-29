# PromptOps Database

**Week 11-12 Deliverable**: PostgreSQL database schema and SQLAlchemy ORM for persistent storage.

---

## Overview

The database stores all PromptOps operational data including audit logs, decompositions, executions, context snapshots, and drift events.

**Technology:**
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic (planned)

---

## Quick Start

### 1. Install PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu
sudo apt-get install postgresql-15

# Docker
docker run --name promptops-db \
  -e POSTGRES_DB=promptops \
  -e POSTGRES_USER=promptops \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE promptops;
CREATE USER promptops WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE promptops TO promptops;
```

### 3. Initialize Schema

```bash
# From database directory
psql -U promptops -d promptops -f schema.sql
```

### 4. Verify

```bash
psql -U promptops -d promptops

# List tables
\dt

# Check schema version
SELECT * FROM schema_version;
```

---

## Schema Overview

### Tables

| Table | Purpose | Records |
|-------|---------|---------|
| `audit_log` | Immutable audit trail | All commands and operations |
| `decompositions` | Task plans | Decomposed sub-tasks with risk assessment |
| `executions` | Execution tracking | Real-time status and logs |
| `context_snapshots` | Infrastructure state | Periodic snapshots for drift detection |
| `drift_events` | Drift tracking | Detected configuration drift |
| `users` | User accounts | Authentication and authorization |
| `api_keys` | Service credentials | Encrypted API keys |
| `schema_version` | Schema tracking | Migration history |

---

## Using SQLAlchemy Models

### Setup

```python
from database import init_db, get_db, AuditLogDB

# Initialize schema (one-time)
init_db()

# Get database session
with next(get_db()) as db:
    # Your queries here
    pass
```

### Create Audit Entry

```python
from database import AuditLogDB

with next(get_db()) as db:
    entry = AuditLogDB.create(db, {
        "user_email": "pm@company.com",
        "command": "Deploy frontend v2.0 to staging",
        "intent_type": "deploy",
        "target_service": "frontend",
        "target_env": "staging",
        "status": "pending",
        "risk_level": "medium"
    })
    print(f"Created audit entry: {entry.id}")
```

### Query Recent Audit

```python
from database import AuditLogDB

with next(get_db()) as db:
    entries, total = AuditLogDB.get_recent(
        db,
        limit=50,
        user="pm@company.com",
        env="production",
        status="completed"
    )

    print(f"Found {total} entries, showing {len(entries)}")
    for entry in entries:
        print(f"  {entry.timestamp}: {entry.command}")
```

### Create Decomposition

```python
from database import DecompositionDB

with next(get_db()) as db:
    decomp = DecompositionDB.create(db, {
        "operation_id": "op-abc123",
        "user_email": "pm@company.com",
        "original_command": "Deploy frontend v2.0",
        "parsed_intent": {"intent_type": "deploy", ...},
        "total_sub_tasks": 6,
        "estimated_duration": 300,
        "risk_assessment": {"overall_risk": "medium", ...},
        "sub_tasks": [...]
    })
```

### Track Execution

```python
from database import ExecutionDB

with next(get_db()) as db:
    # Create execution
    execution = ExecutionDB.create(db, {
        "execution_id": "exec-xyz789",
        "decomposition_id": decomp.id,
        "status": "queued",
        "started_at": datetime.utcnow()
    })

    # Update status
    ExecutionDB.update_status(
        db,
        execution.execution_id,
        status="in_progress",
        completed_tasks=2,
        current_task="Update ECS service"
    )

    # Add log
    ExecutionDB.add_log_entry(
        db,
        execution.execution_id,
        "Task 2 completed successfully"
    )
```

### Drift Detection

```python
from database import DriftEventDB

with next(get_db()) as db:
    # Create drift event
    drift = DriftEventDB.create(db, {
        "drift_id": "drift-001",
        "snapshot_id": "snapshot-123",
        "resource_type": "ecs_service",
        "resource_id": "frontend-prod",
        "field": "desired_count",
        "expected_value": "5",
        "actual_value": "3",
        "severity": "critical",
        "auto_fixable": True
    })

    # Get unacknowledged drift
    unacked = DriftEventDB.get_recent(
        db,
        acknowledged=False,
        severity="critical"
    )
    print(f"Unacknowledged critical drift: {len(unacked)}")

    # Acknowledge drift
    DriftEventDB.acknowledge(
        db,
        drift.drift_id,
        user="pm@company.com"
    )
```

---

## Views

### recent_activity

Shows last 100 commands with execution details:

```sql
SELECT * FROM recent_activity
WHERE user_email = 'pm@company.com'
ORDER BY timestamp DESC
LIMIT 10;
```

### critical_drift

Shows unacknowledged critical drift:

```sql
SELECT * FROM critical_drift;
```

### execution_stats

Daily execution statistics:

```sql
SELECT * FROM execution_stats
ORDER BY date DESC
LIMIT 30;
```

---

## Functions

### add_audit_entry()

```sql
SELECT add_audit_entry(
    'pm@company.com',
    'Deploy frontend v2.0 to staging',
    'deploy',
    'frontend',
    'staging',
    'pending',
    'medium'
);
```

### get_unacknowledged_drift_count()

```sql
SELECT get_unacknowledged_drift_count();
```

---

## Indexes

All tables have appropriate indexes for fast queries:

- `audit_log`: user_email, target_env, status, timestamp
- `decompositions`: user_email, operation_id, timestamp
- `executions`: execution_id, decomposition_id, status, started_at
- `drift_events`: drift_id, snapshot_id, severity, resource_type/id

---

## Materialized Views

### audit_summary_by_user

Aggregated user statistics (refresh daily):

```sql
-- Refresh
SELECT refresh_materialized_views();

-- Query
SELECT * FROM audit_summary_by_user
WHERE total_commands > 10
ORDER BY last_activity DESC;
```

---

## Maintenance

### Archive Old Logs

```sql
-- Archive audit logs older than 1 year
SELECT archive_old_audit_logs();
```

### Refresh Stats

```sql
-- Refresh materialized views
SELECT refresh_materialized_views();
```

### Vacuum

```bash
# Schedule weekly
psql -U promptops -d promptops -c "VACUUM ANALYZE;"
```

---

## Backup & Restore

### Backup

```bash
# Full backup
pg_dump -U promptops promptops > backup_$(date +%Y%m%d).sql

# Schema only
pg_dump -U promptops -s promptops > schema_backup.sql

# Data only
pg_dump -U promptops -a promptops > data_backup.sql
```

### Restore

```bash
psql -U promptops -d promptops < backup_20260429.sql
```

---

## Connection String

```bash
# Development
DATABASE_URL=postgresql://promptops:password@localhost:5432/promptops

# Production (with SSL)
DATABASE_URL=postgresql://user:pass@prod-db.aws.com:5432/promptops?sslmode=require
```

---

## Performance Tuning

### Connection Pooling

SQLAlchemy already configured with:
- Pool size: 10
- Max overflow: 20
- Pre-ping: True

### Query Optimization

```python
# Use select() for better performance
from sqlalchemy import select

stmt = select(AuditLog).where(AuditLog.user_email == "pm@company.com")
results = db.execute(stmt).scalars().all()
```

### Batch Operations

```python
# Bulk insert
db.bulk_save_objects([
    AuditLog(...),
    AuditLog(...),
    AuditLog(...)
])
db.commit()
```

---

## Monitoring

### Check Database Size

```sql
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'promptops';
```

### Check Table Sizes

```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Active Connections

```sql
SELECT
    count(*),
    state
FROM pg_stat_activity
WHERE datname = 'promptops'
GROUP BY state;
```

---

## Migrations (Future)

Using Alembic for schema migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Security

### Encryption

- API keys encrypted at rest
- SSL/TLS for connections
- Prepared statements (SQL injection prevention)

### Access Control

```sql
-- Read-only user for reporting
CREATE USER promptops_readonly WITH PASSWORD 'readonly_pass';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO promptops_readonly;
```

### Audit Trail

The `audit_log` table is **immutable** - no updates or deletes allowed in production.

---

## Troubleshooting

### Can't Connect

```bash
# Check PostgreSQL is running
ps aux | grep postgres

# Check port
lsof -i :5432

# Test connection
psql -U promptops -d promptops -h localhost
```

### Slow Queries

```sql
-- Enable slow query logging
ALTER DATABASE promptops SET log_min_duration_statement = 1000;

-- Find slow queries
SELECT
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Support

- **Schema**: `database/schema.sql`
- **Models**: `database/models.py`
- **CRUD**: `database/db.py`
- **Issues**: GitHub Issues

---

**Author**: PromptOps Team  
**Date**: 2026-04-29  
**Version**: 1.0.0
