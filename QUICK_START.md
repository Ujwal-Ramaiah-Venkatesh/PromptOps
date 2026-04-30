# PromptOps - Quick Start Guide

Get PromptOps up and running in 5 minutes with all 3 enhancement UIs.

---

## Prerequisites

- **Python** 3.10+ ([Download](https://www.python.org/downloads/))
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads))

---

## 1. Clone Repository

```bash
git clone https://github.com/Ujwal-Ramaiah-Venkatesh/PromptOps.git
cd PromptOps
```

---

## 2. Start Backend (Terminal 1)

```bash
# Install Python dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic slowapi boto3 python-jose[cryptography] passlib[bcrypt]

# Start API server with mock database
cd api_gateway
python start_with_mock_db.py
```

**Expected Output:**
```
============================================================
  PromptOps API Gateway with Authentication
  Database: In-Memory Mock
============================================================

  Test Users:
    Admin: admin@promptops.com / admin123
    PM:    pm@promptops.com / pm123

  Starting server...
  API: http://localhost:8000
  Docs: http://localhost:8000/docs
```

**Verify:** Open http://localhost:8000/health in browser - should show `{"status": "healthy"}`

---

## 3. Start Frontend (Terminal 2)

```bash
# Navigate to frontend directory
cd frontend/dashboard

# Install Node dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
  VITE v5.0.8  ready in 423 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Verify:** Open http://localhost:5173 in browser - should see login page

---

## 4. Login & Explore

### Login Credentials

**Admin Account (Full Access):**
```
Email: admin@promptops.com
Password: admin123
Role: admin
```

**PM Account (Limited Production Access):**
```
Email: pm@promptops.com
Password: pm123
Role: pm
```

### Available Pages

1. **🏠 Home Dashboard**
   - Overview stats and metrics
   - Quick action buttons
   - Enhancement cards (click to navigate)
   - System status

2. **⚙️ Autonomy Settings**
   - Configure risk tier auto-execution
   - View action types (23 pre-populated)
   - Browse statistics
   - Toggle LOW/MEDIUM auto-execution

3. **🔍 Discovery Dashboard**
   - Start AWS resource scans
   - Select regions and resource types
   - View scan progress (real-time)
   - Import discovered resources

4. **📥 Ingestion Workflow**
   - View drift events
   - Preview Terraform code generation
   - Import manual AWS changes
   - View import history

---

## 5. Test Key Features

### Test Autonomy Settings

1. Navigate to **Autonomy** page
2. Toggle **LOW** risk tier to **enabled**
3. Notice stats update showing auto-execution rate
4. Click **Actions** tab to see 23 action types
5. Click **Reset to Defaults** (confirm dialog)

### Test Discovery Scan

1. Navigate to **Discovery** page
2. Select **us-east-1** region
3. Select **EC2 Instances** and **S3 Buckets**
4. Click **🔍 Start Discovery Scan**
5. Watch progress bar update (real-time polling)
6. View results in **Results** tab
7. Select resources and click **Import**

### Test Ingestion Workflow

1. Navigate to **Ingestion** page
2. View drift event in list (demo data)
3. Click drift event to preview
4. See side-by-side diff (Terraform vs AWS)
5. Review generated Terraform code
6. Click **✓ Import Change** (confirm)
7. Switch to **History** tab to see import

---

## 6. API Documentation

### Swagger UI (Interactive)
http://localhost:8000/docs

**Features:**
- Try all API endpoints
- See request/response schemas
- Test authentication
- View all available routes

### ReDoc (Clean Documentation)
http://localhost:8000/redoc

---

## Troubleshooting

### Backend Won't Start

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic slowapi boto3 python-jose[cryptography] passlib[bcrypt]
```

### Frontend Won't Start

**Problem:** `command not found: npm`

**Solution:** Install Node.js from https://nodejs.org/

**Problem:** `Port 5173 is already in use`

**Solution:**
```bash
# Kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <process_id> /F

# Or use different port
npm run dev -- --port 3000
```

### Login Fails

**Problem:** "Connection refused" or CORS error

**Solution:**
1. Ensure backend is running on port 8000
2. Check http://localhost:8000/health returns healthy
3. Clear browser cache and localStorage
4. Try incognito/private browsing mode

---

## What's Included

### ✅ Complete Features
- **Authentication:** JWT-based with role hierarchy
- **Autonomy Tiers:** Risk-based auto-execution (LOW/MEDIUM/HIGH/CRITICAL)
- **AWS Discovery:** Multi-region scanning with context inference
- **Infrastructure Ingestion:** Import manual changes into Terraform
- **Rate Limiting:** Prevents API abuse
- **Security Logging:** Complete audit trail
- **Secrets Management:** AWS Secrets Manager integration

### 🚧 Coming Soon
- Real AWS testing (requires boto3 + credentials)
- WebSocket for real-time updates (replacing polling)
- Cost tracking dashboard (ENHANCEMENT-004)
- Secret rotation UI (ENHANCEMENT-005)
- Multi-account AWS Organizations support

---

## Documentation

- **README.md** - Project overview
- **FRONTEND_SETUP.md** - Frontend setup guide
- **ENHANCEMENT-001_COMPLETE.md** - Autonomy implementation
- **ENHANCEMENT-002_COMPLETE.md** - Ingestion implementation
- **ENHANCEMENT-003_COMPLETE.md** - Discovery implementation

---

**Built with ❤️ by the PromptOps Team**

*Transform infrastructure management from complex DevOps workflows into simple conversational commands.*
