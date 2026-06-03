# Frontend Testing Checklist

Quick checklist to verify all frontend features work correctly.

---

## Prerequisites

Before testing, ensure both servers are running:

**Terminal 1 - Backend:**
```bash
cd api_gateway
python start_with_mock_db.py
```
Should see: `✅ Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend/dashboard
npm run dev
```
Should see: `➜  Local:   http://localhost:5173/`

---

## Test Plan

### 1. Authentication Flow ✅

**Test Login:**
- [ ] Open http://localhost:5173
- [ ] Should see login page
- [ ] Enter: `admin@promptops.com` / `admin123`
- [ ] Click "Login"
- [ ] Should redirect to Home Dashboard
- [ ] Top nav should show "System Administrator" and avatar "A"

**Test Logout:**
- [ ] Click "Logout" button in top right
- [ ] Should redirect to login page
- [ ] Browser localStorage should be cleared

**Test Invalid Login:**
- [ ] Enter: `wrong@email.com` / `wrongpass`
- [ ] Should see error message
- [ ] Should remain on login page

---

### 2. Home Dashboard ✅

**Test Layout:**
- [ ] Welcome card displays "Welcome to PromptOps! 👋"
- [ ] Command input field with "Send" button
- [ ] 4 quick action buttons visible
- [ ] 4 stats cards (Deployments, Success Rate, Avg Response, Monthly Cost)
- [ ] 3 enhancement cards (Autonomy, Discovery, Ingestion)
- [ ] System status showing 5 services

**Test Navigation:**
- [ ] Click "Autonomy" in top nav → should navigate to Autonomy Settings
- [ ] Click "Home" in top nav → should return to Home Dashboard
- [ ] Click "Discovery" in top nav → should navigate to Discovery Dashboard
- [ ] Click logo → should return to Home Dashboard
- [ ] Click enhancement card → should navigate to corresponding page

---

### 3. Autonomy Settings Dashboard ✅

**Access Page:**
- [ ] Navigate to Autonomy page (via nav or enhancement card)
- [ ] Should see "⚙️ Autonomy Settings" header
- [ ] 4 stats cards should display (Total Actions, Auto-Executed, Manual Approved, Auto Rate)

**Test Settings Tab:**
- [ ] Should see 4 risk tier cards (LOW, MEDIUM, HIGH, CRITICAL)
- [ ] Each card shows risk icon and color coding
- [ ] HIGH and CRITICAL show "Locked by policy"
- [ ] LOW and MEDIUM have toggle switches

**Test Toggle Switches:**
- [ ] Click LOW tier toggle switch
- [ ] Should animate (slide left/right)
- [ ] Background color should change (gray ↔ green)
- [ ] Stats should update (may take a moment)
- [ ] Try toggling MEDIUM tier
- [ ] HIGH/CRITICAL toggles should be disabled (not clickable)

**Test Actions Tab:**
- [ ] Click "Actions" tab
- [ ] Should see list of action types
- [ ] Each action shows: name, description, risk level badge, example
- [ ] Risk badges color-coded (LOW=green, MEDIUM=yellow, HIGH=red, CRITICAL=dark red)
- [ ] Should see ~23 action types total

**Test History Tab:**
- [ ] Click "History" tab
- [ ] Should see placeholder message (not yet implemented)

**Test Reset:**
- [ ] Click "Reset to Defaults" button
- [ ] Confirmation dialog should appear
- [ ] Click "OK" → settings should reset
- [ ] Click "Cancel" → nothing should change

---

### 4. Discovery Dashboard ✅

**Access Page:**
- [ ] Navigate to Discovery page
- [ ] Should see "🔍 Discovery & Onboarding" header

**Test Scan Configuration:**
- [ ] Should see "Scan" tab active
- [ ] Region checkboxes: us-east-1, us-west-2, eu-west-1, ap-southeast-1
- [ ] Resource type checkboxes: EC2, RDS, S3, VPC, Subnet, Security Groups
- [ ] All should be checkable
- [ ] "Start Discovery Scan" button should be enabled when regions + types selected

**Test Scan Execution:**
- [ ] Select "us-east-1" region
- [ ] Select "EC2 Instances" and "S3 Buckets"
- [ ] Click "🔍 Start Discovery Scan"
- [ ] Should switch to "Results" tab automatically
- [ ] Scan status card should appear showing "RUNNING"
- [ ] Progress bar should show percentage (updates every 2 seconds)
- [ ] Wait for scan to complete (status changes to "COMPLETED")

**Test Results Tab:**
- [ ] Should see 4 stats cards (Total Resources, High Confidence, Tagged, Tag Consistency)
- [ ] Resource table should populate with discovered resources
- [ ] Each resource shows:
  - Resource name/ID
  - Resource type and region
  - Inferred environment/project badges (if available)
  - Confidence score percentage
  - Checkbox for selection

**Test Resource Selection:**
- [ ] Click on a resource card → should toggle checkbox
- [ ] Checkbox should show checked/unchecked state
- [ ] Card background should change color when selected (blue border)
- [ ] Click "Select All" → all checkboxes should check
- [ ] Click "Clear" → all checkboxes should uncheck
- [ ] Import button should show count: "Import (N)"

**Test Import:**
- [ ] Select 1-2 resources
- [ ] Click "Import (2)" button
- [ ] Should switch to "Import" tab
- [ ] Should see "Ready to import 2 resources"
- [ ] Click "✓ Import 2 Resources"
- [ ] Confirmation dialog should appear
- [ ] Click "OK" → import should execute
- [ ] Success message should appear

---

### 5. Ingestion Workflow ✅

**Access Page:**
- [ ] Navigate to Ingestion page
- [ ] Should see "📥 Infrastructure Ingestion" header

**Test Drift Events Tab:**
- [ ] Should see "Drift Events" tab active
- [ ] Left panel: Drift event list (1 demo event)
- [ ] Right panel: "Select a drift event to preview" message

**Test Preview:**
- [ ] Click on the drift event (i-abc123)
- [ ] Left panel: Event should highlight (blue border)
- [ ] Right panel: Should show "Import Preview"
- [ ] "Detected Changes" section should show 2 changes:
  - instance_type: t3.medium → t3.large
  - tags: Environment → Environment + Owner
- [ ] "Generated Terraform" section should appear
- [ ] Code block with Terraform HCL syntax
- [ ] Validation status: "✓ Validation Passed" or "✗ Validation Failed"

**Test Import:**
- [ ] Click "✓ Import Change" button
- [ ] Confirmation dialog: "Import this change into Terraform state?"
- [ ] Click "OK" → import should execute
- [ ] Success alert should appear
- [ ] Preview should clear

**Test History Tab:**
- [ ] Click "History" tab
- [ ] Should see "Import History" header
- [ ] If imports exist, should show list with:
  - Resource ID and type
  - Imported by (user email)
  - Timestamp
  - Status badge
  - Expandable Terraform code (click "View Terraform Code")
- [ ] If leads/admin role: "Rollback" button should appear

---

## Browser Compatibility Testing

Test on multiple browsers:

- [ ] **Chrome** - All features work
- [ ] **Firefox** - All features work
- [ ] **Safari** (Mac) - All features work
- [ ] **Edge** - All features work

---

## Responsive Design Testing

Test on different screen sizes:

- [ ] **Desktop (1920x1080)** - Layout looks good
- [ ] **Laptop (1366x768)** - Layout adapts correctly
- [ ] **Tablet (768x1024)** - Cards stack properly
- [ ] **Mobile (375x667)** - Navigation accessible, cards single column

**How to test:**
1. Open DevTools (F12)
2. Click responsive design mode (Ctrl+Shift+M)
3. Select different device sizes
4. Verify layout adapts

---

## Performance Testing

**Load Times:**
- [ ] Home page loads in <1 second
- [ ] Navigation between pages is instant (<100ms)
- [ ] API calls complete in <1 second
- [ ] No console errors or warnings

**How to test:**
1. Open DevTools → Network tab
2. Reload page
3. Check "DOMContentLoaded" and "Load" times
4. Open Console tab → should see no red errors

---

## Error Handling Testing

**Test Network Errors:**
1. Stop backend server (Ctrl+C in Terminal 1)
2. Try to login → should see error message
3. Try to navigate pages → should see error alerts
4. Restart backend → errors should clear

**Test Invalid Data:**
1. Clear localStorage (DevTools → Application → Local Storage → Clear)
2. Try to access protected pages → should redirect to login
3. Login with valid credentials → should work again

---

## API Integration Testing

**Verify Backend Endpoints:**
- [ ] Open http://localhost:8000/docs
- [ ] Should see Swagger UI with all endpoints
- [ ] Try "GET /health" → should return `{"status": "healthy"}`
- [ ] Try "POST /api/v1/auth/login" → should return JWT token
- [ ] Try authenticated endpoints with Bearer token

---

## Known Issues / Limitations

**Expected Behaviors:**
- Discovery scan uses mock data (not real AWS)
- Ingestion drift event is hardcoded demo data
- History tabs show placeholder or limited data
- Polling updates every 2 seconds (not real-time WebSocket)

**Not Bugs:**
- "Import Change" succeeds but doesn't show in History (history endpoint not fully implemented)
- Scan progress may jump (mock data, not real scanning)
- Some API calls return 404 (endpoints not yet implemented)

---

## Success Criteria

**All systems working if:**
- ✅ Login/logout works
- ✅ Navigation between all 4 pages works
- ✅ All tabs load without errors
- ✅ Toggle switches change and save
- ✅ Scan can be started and completes
- ✅ Resources can be selected and imported
- ✅ Drift preview shows Terraform code
- ✅ No console errors (except expected 404s)

---

## Troubleshooting

### Frontend won't start
```bash
cd frontend/dashboard
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend won't start
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic slowapi boto3 python-jose[cryptography] passlib[bcrypt]
cd api_gateway
python start_with_mock_db.py
```

### CORS errors
- Ensure backend is running on port 8000
- Check ALLOWED_ORIGINS in start_with_mock_db.py includes http://localhost:5173

### Login fails
- Check http://localhost:8000/health returns healthy
- Clear browser cache and localStorage
- Try incognito/private mode

---

## Report Results

After testing, create a report:

**Format:**
```
Test Date: [Date]
Tester: [Your Name]
Browser: [Chrome/Firefox/etc]
OS: [Windows/Mac/Linux]

Passed: [X/Y tests]
Failed: [list of failed tests]
Issues Found: [list any bugs]
Notes: [any observations]
```

---

**Good luck testing! 🧪**
