# PostgreSQL Setup Guide for PromptOps Phase 2

**Date:** 2026-04-30  
**Phase:** Phase 2 - Database Persistence  
**Cost:** $0 (local PostgreSQL with Docker)

---

## 🎯 Overview

This guide sets up local PostgreSQL database for PromptOps Phase 2, replacing the in-memory mock database with persistent storage.

**Benefits:**
- ✅ **FREE** - No cloud database costs
- ✅ Data persistence across restarts
- ✅ Production-ready schema
- ✅ Easy migration to cloud PostgreSQL later (AWS RDS, etc.)

---

## 🚀 Quick Start

### **Option 1: Docker Compose (Recommended)**

```bash
# Start PostgreSQL + Vault + Backend + Frontend
docker-compose -f docker-compose-phase2.yml up -d

# Check services
docker-compose -f docker-compose-phase2.yml ps

# View logs
docker-compose -f docker-compose-phase2.yml logs -f postgres
```

**Database Connection:**
- **Host:** localhost
- **Port:** 5432
- **Database:** promptops
- **User:** promptops
- **Password:** promptops_dev_password

### **Option 2: Local PostgreSQL Installation**

**Windows:**
```bash
# Download and install PostgreSQL 15
# https://www.postgresql.org/download/windows/

# Or use winget
winget install PostgreSQL.PostgreSQL

# Or use Chocolatey
choco install postgresql

# Start service
net start postgresql-x64-15
```

**Create database:**
```bash
# Open PostgreSQL shell
psql -U postgres

# Create user and database
CREATE USER promptops WITH PASSWORD 'promptops_dev_password';
CREATE DATABASE promptops OWNER promptops;
GRANT ALL PRIVILEGES ON DATABASE promptops TO promptops;

# Exit
\q
```

---

## 📊 Database Schema

The Phase 2 schema includes these tables:

### **Core Tables:**

1. **users** - User accounts and authentication
   ```sql
   - id (UUID, primary key)
   - email (unique)
   - hashed_password
   - role (admin, pm, engineer, viewer, auditor)
   - is_active
   - created_at, updated_at
   ```

2. **resources** - Discovered AWS resources
   ```sql
   - id (UUID, primary key)
   - resource_id (e.g., i-1234567890abcdef0)
   - resource_type (ec2_instance, rds_instance, s3_bucket, etc.)
   - name
   - region
   - tags (JSONB)
   - metadata (JSONB)
   - discovered_at
   - last_seen_at
   ```

3. **scans** - Discovery scan history
   ```sql
   - id (UUID, primary key)
   - scan_id (unique)
   - region
   - status (running, completed, failed)
   - resources_found
   - started_at, completed_at
   - user_id (foreign key to users)
   ```

4. **autonomy_settings** - User autonomy preferences
   ```sql
   - id (UUID, primary key)
   - user_id (foreign key to users)
   - risk_level (LOW, MEDIUM, HIGH, CRITICAL)
   - auto_execute (boolean)
   - requires_2fa (boolean)
   - updated_at
   ```

5. **execution_history** - Action execution logs
   ```sql
   - id (UUID, primary key)
   - action_type
   - risk_level
   - status (auto_executed, approved, denied, failed)
   - user_id (foreign key to users)
   - executed_at
   - metadata (JSONB)
   ```

6. **secrets** - Secret rotation tracking (ENH-005)
   ```sql
   - id (UUID, primary key)
   - name
   - vault_path
   - rotation_enabled
   - rotation_interval_days
   - last_rotated_at
   - next_rotation_at
   ```

---

## 🔧 Setting Up with Alembic

### **1. Initialize Alembic (already configured)**

Alembic configuration is in `alembic.ini` and `alembic/` directory.

### **2. Environment Variables**

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://promptops:promptops_dev_password@localhost:5432/promptops

# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Vault
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=promptops-dev-token

# App
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```

### **3. Run Migrations**

```bash
# Run all migrations
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

### **4. Create New Migration (when schema changes)**

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new table"

# Create empty migration (manual)
alembic revision -m "Custom change"

# Edit the generated file in alembic/versions/
# Then apply it
alembic upgrade head
```

---

## 🧪 Testing Database Connection

### **Python Test Script:**

```python
# test_database.py
import psycopg2
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def test_psycopg2():
    """Test with psycopg2 (low-level)"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="promptops",
            user="promptops",
            password="promptops_dev_password"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ psycopg2 connection successful!")
        print(f"   PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ psycopg2 connection failed: {e}")
        return False

def test_sqlalchemy():
    """Test with SQLAlchemy (ORM)"""
    try:
        database_url = os.getenv('DATABASE_URL')
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user;"))
            db, user = result.fetchone()
            print(f"✅ SQLAlchemy connection successful!")
            print(f"   Database: {db}, User: {user}")
        
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  PostgreSQL Connection Test")
    print("=" * 60)
    
    print("\n[1] Testing psycopg2...")
    test_psycopg2()
    
    print("\n[2] Testing SQLAlchemy...")
    test_sqlalchemy()
    
    print("\n" + "=" * 60)
```

**Run test:**
```bash
python test_database.py
```

---

## 🔄 Migration from Mock DB to PostgreSQL

### **Steps:**

1. **Start PostgreSQL:**
   ```bash
   docker-compose -f docker-compose-phase2.yml up -d postgres
   ```

2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Update backend to use PostgreSQL:**
   - Database connection configured via `DATABASE_URL` env var
   - SQLAlchemy models replace mock classes
   - All CRUD operations use real database

4. **Migrate existing mock data (optional):**
   ```bash
   python scripts/migrate_mock_to_postgres.py
   ```

5. **Restart backend:**
   ```bash
   docker-compose -f docker-compose-phase2.yml restart backend
   ```

---

## 🎯 Database Management Commands

### **Backup Database:**
```bash
# Backup to file
docker exec promptops-postgres pg_dump -U promptops promptops > backup_$(date +%Y%m%d).sql

# Restore from file
docker exec -i promptops-postgres psql -U promptops promptops < backup_20260430.sql
```

### **Connect to Database:**
```bash
# Via Docker
docker exec -it promptops-postgres psql -U promptops -d promptops

# Via local psql
psql -h localhost -p 5432 -U promptops -d promptops
```

### **Useful SQL Commands:**
```sql
-- List all tables
\dt

-- Describe table
\d users

-- Show table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Count rows in all tables
SELECT 
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Active connections
SELECT * FROM pg_stat_activity;

-- Kill specific connection
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <pid>;
```

---

## 🔒 Security Best Practices

### **1. Change Default Password:**
```sql
ALTER USER promptops WITH PASSWORD 'new_secure_password_here';
```

Update `.env`:
```bash
DATABASE_URL=postgresql://promptops:new_secure_password_here@localhost:5432/promptops
```

### **2. Restrict Network Access:**
Edit `pg_hba.conf` (in Docker: `/var/lib/postgresql/data/pg_hba.conf`):
```
# Only allow local connections
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

### **3. Enable SSL (Production):**
```bash
# Generate SSL certificates
openssl req -new -x509 -days 365 -nodes -text -out server.crt -keyout server.key

# Configure PostgreSQL
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

---

## 📊 Performance Tuning

### **Recommended Settings (development):**

Edit `postgresql.conf`:
```ini
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
work_mem = 4MB

# Connections
max_connections = 100

# Logging
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'all'  # For debugging (remove in production)

# Performance
random_page_cost = 1.1  # For SSD
effective_io_concurrency = 200
```

Restart PostgreSQL:
```bash
docker-compose -f docker-compose-phase2.yml restart postgres
```

---

## 🐛 Troubleshooting

### **Issue: "Connection refused"**

**Check if PostgreSQL is running:**
```bash
docker ps | grep postgres
# Should show: promptops-postgres ... Up X minutes
```

**Check logs:**
```bash
docker logs promptops-postgres
```

**Restart service:**
```bash
docker-compose -f docker-compose-phase2.yml restart postgres
```

### **Issue: "Authentication failed"**

**Verify credentials:**
```bash
docker exec -it promptops-postgres psql -U promptops -d promptops
# If this works, credentials are correct
```

**Check `.env` file:**
```bash
cat .env | grep DATABASE_URL
# Should match: postgresql://promptops:promptops_dev_password@localhost:5432/promptops
```

### **Issue: "Database does not exist"**

**Create database:**
```bash
docker exec -it promptops-postgres psql -U promptops -c "CREATE DATABASE promptops;"
```

### **Issue: "Port 5432 already in use"**

**Find process using port:**
```bash
# Windows
netstat -ano | findstr :5432

# Linux/Mac
lsof -i :5432
```

**Kill process or change port:**
```yaml
# In docker-compose-phase2.yml
ports:
  - "5433:5432"  # Use 5433 externally
```

---

## ✅ Setup Checklist

- [ ] PostgreSQL installed or Docker running
- [ ] Database `promptops` created
- [ ] User `promptops` created with password
- [ ] `.env` file configured with `DATABASE_URL`
- [ ] Alembic migrations run (`alembic upgrade head`)
- [ ] Database connection tested successfully
- [ ] Backend service connects to PostgreSQL
- [ ] Sample data loaded (optional)

---

## 📚 Resources

- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **psycopg2 Docs:** https://www.psycopg.org/docs/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **Docker PostgreSQL:** https://hub.docker.com/_/postgres

---

**Ready to proceed?** Run the quick start commands to get PostgreSQL running!

**Next Steps:**
1. ✅ Start PostgreSQL with Docker Compose
2. → Create database schema with Alembic
3. → Update backend to use PostgreSQL
4. → Test end-to-end with persistent data
