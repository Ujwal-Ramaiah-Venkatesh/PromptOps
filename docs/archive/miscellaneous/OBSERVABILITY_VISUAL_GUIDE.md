# CloudWatch Observability - Visual Guide

## Dashboard Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  PromptOps                                    👤 PM MANAGER   [Logout]│
├─────────────────────────────────────────────────────────────────────┤
│  [🏠 Home] [⚙️ Autonomy] [🔍 Discovery] [📥 Ingestion] [📊 Observability]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  🔍 CloudWatch Observability                                         │
│  Real-time monitoring and health checks for deployed applications    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Select Deployment: [jewelry-vault (production) - AWS ▼]         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  ✓  jewelry-vault                              99.95%  [View App]││
│  │     production • us-east-1 • v1.2.3           Uptime            ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ [1h] [6h] [24h] [7d]              ☑ Auto-refresh (30s)          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ CPU Usage    │ │ Memory Usage │ │ Request Rate │                │
│  │              │ │              │ │              │                │
│  │   35.42%     │ │   52.18%     │ │  245/min     │                │
│  │ ╱───╲        │ │ ╱────        │ │  ╱╲  ╱╲     │                │
│  │╱     ╲───    │ │╱             │ │ ╱  ╲╱  ╲    │                │
│  │ Min: 22.15   │ │ Min: 41.30   │ │ Min: 120     │                │
│  │ Max: 48.90   │ │ Max: 59.85   │ │ Max: 310     │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                       │
│  ┌──────────────┐ ┌──────────────┐                                 │
│  │ Error Rate   │ │ Response Time│                                 │
│  │              │ │ (p95)        │                                 │
│  │    0 /min    │ │   95.2 ms    │                                 │
│  │ ────────     │ │   ╱╲         │                                 │
│  │              │ │  ╱  ╲────    │                                 │
│  │ Min: 0       │ │ Min: 52.10   │                                 │
│  │ Max: 2       │ │ Max: 142.50  │                                 │
│  └──────────────┘ └──────────────┘                                 │
│                                                                       │
│  🚨 Active Alerts                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  No active alerts - All systems healthy ✅                       ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  📋 Recent Logs                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ [2026-06-03T07:30:00] Application started successfully          ││
│  │ [2026-06-03T07:30:01] Serving static content from S3           ││
│  │ [2026-06-03T07:30:02] CloudFront distribution active           ││
│  │ [2026-06-03T07:30:05] Request processed: GET /index.html       ││
│  │ [2026-06-03T07:30:06] Request processed: GET /assets/app.js    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Navigation Bar
```
┌─────────────────────────────────────────────────────────────────────┐
│  [🏠 Home] [⚙️ Autonomy] [🔍 Discovery] [📥 Ingestion] [📊 Observability]│
└─────────────────────────────────────────────────────────────────────┘
                                                        ↑
                                              Click here to access
```
**Features**:
- Clean, modern design
- Active state highlighting
- Emoji icons for quick recognition
- Consistent with existing PromptOps UI

### 2. Deployment Selector
```
┌─────────────────────────────────────────────────────────────────────┐
│ Select Deployment: [jewelry-vault (production) - AWS ▼]            │
└─────────────────────────────────────────────────────────────────────┘
```
**Features**:
- Dropdown showing all deployments
- Shows environment (production/staging)
- Shows cloud provider (AWS/GCP/Azure)
- Auto-loads metrics on selection

### 3. Health Status Card
```
┌─────────────────────────────────────────────────────────────────────┐
│  ✓  jewelry-vault                              99.95%  [View App→] │
│     production • us-east-1 • v1.2.3           Uptime               │
└─────────────────────────────────────────────────────────────────────┘
```
**Status Indicators**:
- ✓ Green = Healthy
- ⚠ Yellow = Degraded  
- ✕ Red = Critical

**Information Shown**:
- Deployment name and version
- Environment and region
- Current uptime percentage
- Direct link to live application

### 4. Time Range & Controls
```
┌─────────────────────────────────────────────────────────────────────┐
│ [1h] [6h] [24h] [7d]              ☑ Auto-refresh (30s)             │
└─────────────────────────────────────────────────────────────────────┘
```
**Time Range Options**:
- **1h**: Real-time monitoring (5-min intervals)
- **6h**: Short-term trends
- **24h**: Daily patterns
- **7d**: Weekly trends

**Auto-Refresh**:
- Checkbox to enable/disable
- Refreshes every 30 seconds
- Updates all metrics automatically

### 5. Metrics Grid

#### CPU Usage Card
```
┌──────────────┐
│ CPU Usage    │
│              │
│   35.42%     │  ← Current value
│ ╱───╲        │  ← Trend chart
│╱     ╲───    │
│ Min: 22.15   │  ← Range indicators
│ Max: 48.90   │
└──────────────┘
```

#### Memory Usage Card
```
┌──────────────┐
│ Memory Usage │
│              │
│   52.18%     │
│ ╱────        │
│╱             │
│ Min: 41.30   │
│ Max: 59.85   │
└──────────────┘
```

#### Request Rate Card
```
┌──────────────┐
│ Request Rate │
│              │
│  245/min     │
│  ╱╲  ╱╲     │
│ ╱  ╲╱  ╲    │
│ Min: 120     │
│ Max: 310     │
└──────────────┘
```

#### Error Rate Card
```
┌──────────────┐
│ Error Rate   │
│              │
│    0 /min    │  ← Healthy: 0 errors
│ ────────     │
│              │
│ Min: 0       │
│ Max: 2       │
└──────────────┘
```

#### Response Time Card
```
┌──────────────┐
│ Response Time│
│ (p95)        │
│   95.2 ms    │  ← 95th percentile
│   ╱╲         │
│  ╱  ╲────    │
│ Min: 52.10   │
│ Max: 142.50  │
└──────────────┘
```

### 6. Alerts Section

**When No Alerts**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🚨 Active Alerts                                                    │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │  No active alerts - All systems healthy ✅                      │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**When Alerts Present**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🚨 Active Alerts                                                    │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ 🔴 High Error Rate                                             │  │
│ │    Error rate exceeded threshold of 10 errors/min              │  │
│ │    2026-06-03 07:25:00                                         │  │
│ └───────────────────────────────────────────────────────────────┘  │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ 🟡 Elevated Latency                                            │  │
│ │    Response time above 200ms threshold                          │  │
│ │    2026-06-03 07:22:00                                         │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Alert Colors**:
- 🔴 Red = Critical severity
- 🟡 Yellow = Warning severity

### 7. Logs Viewer
```
┌─────────────────────────────────────────────────────────────────────┐
│ 📋 Recent Logs                                                      │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ [2026-06-03T07:30:00] Application started successfully        │  │
│ │ [2026-06-03T07:30:01] Serving static content from S3         │  │
│ │ [2026-06-03T07:30:02] CloudFront distribution active         │  │
│ │ [2026-06-03T07:30:05] Request processed: GET /index.html     │  │
│ │ [2026-06-03T07:30:06] Request processed: GET /assets/app.js  │  │
│ │ [2026-06-03T07:30:10] Cache hit: /assets/style.css           │  │
│ │ [2026-06-03T07:30:12] User session started: user_12345       │  │
│ │ [2026-06-03T07:30:15] Database query executed in 23ms        │  │
│ │ [2026-06-03T07:30:18] API response sent: 200 OK              │  │
│ │ ▼ Scroll for more logs...                                     │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Terminal-style dark theme
- Scrollable log window
- Timestamp on each entry
- Auto-refresh with new logs
- Color-coded log levels (future)

## Color Scheme

### Status Colors
```
✅ Healthy   = Green  (#10b981)
⚠️  Degraded = Yellow (#f59e0b)
❌ Critical  = Red    (#ef4444)
ℹ️  Unknown  = Gray   (#6b7280)
```

### Metric Colors
```
CPU Usage      = Blue   (#3b82f6)
Memory Usage   = Purple (#8b5cf6)
Request Rate   = Green  (#10b981)
Error Rate     = Red    (#ef4444)
Response Time  = Orange (#f59e0b)
```

### UI Elements
```
Background     = Light Gray (#f9fafb)
Cards          = White      (#ffffff)
Text Primary   = Dark Gray  (#111827)
Text Secondary = Gray       (#6b7280)
Border         = Light Gray (#d1d5db)
Active Button  = Blue       (#3b82f6)
```

## Responsive Design

### Desktop View (> 1200px)
```
┌─────────────────────────────────────────────────────────────┐
│  Navigation Bar (full width)                                │
├─────────────────────────────────────────────────────────────┤
│  Health Card (full width)                                   │
├─────────────────────────────────────────────────────────────┤
│  Controls (full width)                                      │
├─────────────────┬──────────────┬─────────────┬─────────────┤
│  CPU Chart      │ Memory Chart │ Request Ch. │ Error Chart │
│                 │              │             │ Response Ch.│
├─────────────────┴──────────────┴─────────────┴─────────────┤
│  Alerts Section (full width)                                │
├─────────────────────────────────────────────────────────────┤
│  Logs Section (full width)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Tablet View (768px - 1200px)
```
┌───────────────────────────────────────────────────┐
│  Navigation Bar (compact)                         │
├───────────────────────────────────────────────────┤
│  Health Card                                      │
├───────────────────────────────────────────────────┤
│  Controls                                         │
├───────────────────────┬───────────────────────────┤
│  CPU Chart            │  Memory Chart             │
├───────────────────────┼───────────────────────────┤
│  Request Chart        │  Error Chart              │
├───────────────────────┼───────────────────────────┤
│  Response Chart       │                           │
├───────────────────────┴───────────────────────────┤
│  Alerts Section                                   │
├───────────────────────────────────────────────────┤
│  Logs Section                                     │
└───────────────────────────────────────────────────┘
```

### Mobile View (< 768px)
```
┌─────────────────────────────┐
│  Nav (hamburger)            │
├─────────────────────────────┤
│  Health Card                │
├─────────────────────────────┤
│  Controls (stacked)         │
├─────────────────────────────┤
│  CPU Chart                  │
├─────────────────────────────┤
│  Memory Chart               │
├─────────────────────────────┤
│  Request Chart              │
├─────────────────────────────┤
│  Error Chart                │
├─────────────────────────────┤
│  Response Chart             │
├─────────────────────────────┤
│  Alerts                     │
├─────────────────────────────┤
│  Logs                       │
└─────────────────────────────┘
```

## User Interactions

### Click Actions
1. **Navigation Button** → Navigate to page
2. **Deployment Selector** → Switch deployment
3. **Time Range Button** → Change time range
4. **Auto-refresh Checkbox** → Toggle auto-refresh
5. **View App Button** → Open app in new tab
6. **Alert Card** → Show alert details (future)
7. **Log Entry** → Show log details (future)

### Hover Effects
- Buttons: Slight background color change
- Chart Lines: Show tooltip with value (future)
- Cards: Subtle shadow enhancement
- Links: Underline and color change

### Loading States
```
┌──────────────┐
│ CPU Usage    │
│              │
│   Loading... │
│              │
│  ⟳ ⟳ ⟳      │  ← Spinner animation
│              │
│              │
└──────────────┘
```

## Empty States

### No Deployments
```
┌─────────────────────────────────────────────────────────────┐
│  📊 No Deployments Found                                    │
│                                                              │
│  Deploy your first application to see metrics here.         │
│                                                              │
│  [Deploy New App →]                                         │
└─────────────────────────────────────────────────────────────┘
```

### No Data Available
```
┌──────────────┐
│ CPU Usage    │
│              │
│  No data     │
│  available   │
│              │
│  Try:        │
│  • Checking  │
│    AWS creds │
│  • Different │
│    time range│
└──────────────┘
```

## Accessibility Features

### Keyboard Navigation
- Tab: Move through interactive elements
- Enter/Space: Activate buttons
- Arrow Keys: Navigate time range buttons
- Escape: Close modals (future)

### Screen Reader Support
- Descriptive alt text for all icons
- ARIA labels for all interactive elements
- Semantic HTML structure
- Proper heading hierarchy

### Color Contrast
- All text meets WCAG AA standards (4.5:1 ratio)
- Status indicators have text labels
- Icons paired with text descriptions

## Animation & Transitions

### Chart Updates
- Smooth line transitions (300ms ease-in-out)
- Fade-in for new data points
- No jarring jumps in visualization

### Status Changes
- Subtle color transition (200ms)
- Pulse animation for critical alerts
- Smooth slide-in for new logs

### Loading
- Skeleton screens during initial load
- Subtle spinner for refresh
- Progress indicators for long operations

---

## Usage Examples

### Checking Application Health
1. Click **📊 Observability** button
2. Select your deployment from dropdown
3. Verify green ✓ status indicator
4. Review uptime percentage (should be > 99%)

### Investigating Performance Issue
1. Select **24h** time range
2. Look for spikes in **Response Time** chart
3. Cross-reference with **CPU** and **Memory** charts
4. Check **Logs** section for errors at spike time
5. Review **Alerts** for any triggered alarms

### Monitoring During Deployment
1. Enable ☑ **Auto-refresh**
2. Select **1h** time range for real-time view
3. Watch **Error Rate** for any spikes
4. Monitor **Response Time** for degradation
5. Check **Logs** for deployment events

### Setting Up for Demo
1. Ensure backend is running
2. Open dashboard and navigate to Observability
3. Mock data will display automatically
4. Show all 5 metric charts
5. Explain each metric's purpose
6. Demonstrate time range switching
7. Show auto-refresh in action

---

This visual guide provides a complete picture of what users will see and interact with in the CloudWatch Observability dashboard.
