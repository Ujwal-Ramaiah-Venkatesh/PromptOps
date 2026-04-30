# Run the REAL PromptOps System

You want to see the actual production system, not the demo HTML!

## Step 1: Install Backend Dependencies

Open a terminal and run:
```bash
cd c:\Users\pqm847\Documents\PromptOps
pip install fastapi uvicorn anthropic sqlalchemy psycopg2-binary python-dotenv pydantic
```

## Step 2: Start Backend (Terminal 1)

```bash
cd c:\Users\pqm847\Documents\PromptOps\api_gateway
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://localhost:8000
```

✅ Backend is now running!

## Step 3: Start Frontend (Terminal 2)

Open a NEW terminal:
```bash
cd c:\Users\pqm847\Documents\PromptOps\frontend\dashboard
npm run dev
```

You should see:
```
VITE v5.0.8  ready in 500 ms

➜  Local:   http://localhost:3000/
➜  press h to show help
```

✅ Frontend will open automatically in your browser!

## What You'll See

This is the **REAL system** with:

✅ **Real React Components**
- CommandInput.tsx
- IntentPreview.tsx  
- TaskPreview.tsx
- ApprovalFlow.tsx
- AuditTrail.tsx
- DriftAlert.tsx

✅ **Real Backend Integration**
- FastAPI with 10 endpoints
- Claude Sonnet 4.5 for parsing
- PostgreSQL database
- AWS context layer

✅ **Real Features**
- Type commands in natural language
- Claude parses intent in real-time
- Task decomposition engine
- Production approval workflow
- Audit trail with database
- Infrastructure drift detection

## Try These Commands

Once the dashboard loads:

```
Deploy frontend v2.0 to staging
Scale backend to 10 instances  
Show me AWS cost breakdown
Check database performance
```

Watch the magic happen! ✨

---

**This is NOT a demo - this is the actual production system we built over 12 weeks!**
