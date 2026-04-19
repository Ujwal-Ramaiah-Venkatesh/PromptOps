# PromptOps - Complete UI Design Specification

**Target Users:** Project Managers, Startup Founders (Non-technical)  
**Design Goal:** Simple, clean interface that feels safe and approachable  
**Mobile:** Fully responsive (3 AM on-call approvals)

---

## 🎨 Design System

### Color Palette
```
Primary Colors:
- Brand Blue: #1155CC (buttons, headers, links)
- Success Green: #34A853 (approved, complete)
- Warning Yellow: #F9AB00 (needs review, caution)
- Danger Red: #EA4335 (production, delete, critical)
- Neutral Gray: #5F6368 (text, borders)

Background Colors:
- White: #FFFFFF (main background)
- Light Gray: #F8F9FA (cards, panels)
- Dark Gray: #202124 (footer, dark mode)

Text Colors:
- Primary Text: #202124 (headings, body)
- Secondary Text: #5F6368 (metadata, labels)
- Disabled Text: #9AA0A6 (disabled states)
```

### Typography
```
Font Family: 'Inter', 'SF Pro', -apple-system, system-ui, sans-serif

Headings:
- H1: 32px, Bold, #202124
- H2: 24px, SemiBold, #202124
- H3: 18px, SemiBold, #5F6368

Body:
- Large: 16px, Regular, #202124
- Regular: 14px, Regular, #202124
- Small: 12px, Regular, #5F6368

Code/Monospace:
- Font: 'Fira Code', 'Monaco', monospace
- Size: 14px
```

### Spacing
```
- XS: 4px
- SM: 8px
- MD: 16px
- LG: 24px
- XL: 32px
- XXL: 48px
```

---

## 🖥️ Main Dashboard (Primary Screen)

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER                                                          │
│ PromptOps Logo    [Project: PromptOps]    [User: Ujwal] [⚙️]   │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     COMMAND INPUT PANEL                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ What would you like to do?                                │ │
│  │                                                           │ │
│  │ ┌─────────────────────────────────────────────────────┐  │ │
│  │ │ Deploy the API to production                        │  │ │
│  │ └─────────────────────────────────────────────────────┘  │ │
│  │                                                           │ │
│  │ Real-time Preview:                                        │ │
│  │ 🎯 Intent: Deploy                                         │ │
│  │ 📦 Service: API                                           │ │
│  │ 🌍 Environment: Production                                │ │
│  │ ⚠️  Requires Approval (High Risk)                         │ │
│  │                                                           │ │
│  │              [Continue] or [Clear]                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
┌──────────────────────┬──────────────────────┬──────────────────┐
│                      │                      │                  │
│   RECENT ACTIONS     │   INCIDENT CARDS     │   AUDIT TRAIL    │
│                      │                      │                  │
│ ✅ Scaled API (2h)   │ 🔴 503 Errors       │ Apr 19 10:00 PM │
│ ✅ Deploy (4h)       │    Prod API          │ Deploy API      │
│ ⏳ Monitoring (5h)   │    Impact: High      │ by: Ujwal       │
│                      │    [Investigate]     │ Status: Success │
│                      │                      │                  │
│ [View All]           │ [View All]           │ [View All]       │
│                      │                      │                  │
└──────────────────────┴──────────────────────┴──────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                         QUICK ACTIONS                           │
│  [📊 View Metrics] [💰 Cost Analysis] [🔒 Security Scan]       │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Header Bar (Fixed Top)
```
Component: Header
Height: 64px
Background: White with bottom border
Shadow: 0 2px 4px rgba(0,0,0,0.1)

Left:
- PromptOps Logo (32x32px icon + text)

Center:
- Project Selector Dropdown: [Project: PromptOps ▼]

Right:
- User Avatar (32x32px circle)
- Username: "Ujwal"
- Settings Icon (⚙️)
- Notification Bell (🔔) with badge count
```

#### 2. Command Input Panel (Hero Section)
```
Component: CommandInput
Width: 100% (max 800px centered)
Padding: XL (32px)
Background: Linear gradient (light blue to white)
Border Radius: 12px
Shadow: 0 4px 12px rgba(0,0,0,0.08)

Elements:
- Label: "What would you like to do?"
  Font: H2 (24px SemiBold)
  Color: #202124

- Text Input:
  Height: 120px (expandable)
  Placeholder: "e.g., Deploy the API to production"
  Font: 16px Regular
  Border: 2px solid #E8EAED (focus: #1155CC)
  Border Radius: 8px
  Padding: 16px

- Real-time Preview Card:
  Background: #F8F9FA
  Border-left: 4px solid #1155CC
  Padding: MD (16px)
  
  Preview Fields:
  🎯 Intent: [intent_type] - Icon + Label
  📦 Service: [target_service]
  🌍 Environment: [target_env]
  ⚠️  Risk Level: [risk_level] with color coding
  
  Color Coding:
  - Low: Green (#34A853)
  - Medium: Yellow (#F9AB00)
  - High: Orange (#FF6D01)
  - Extreme: Red (#EA4335)

- Action Buttons:
  [Continue] - Primary button (Blue, 48px height)
  [Clear] - Secondary button (Gray outline)
```

#### 3. Three-Column Dashboard (Below Input)
```
Grid Layout: 1fr 1fr 1fr (3 equal columns)
Gap: LG (24px)
Margin-top: XL (32px)

Each Panel:
- Background: White
- Border: 1px solid #E8EAED
- Border Radius: 8px
- Padding: LG (24px)
- Shadow: 0 1px 3px rgba(0,0,0,0.08)
```

**Left Panel: Recent Actions**
```
Header: "Recent Actions"
Font: H3 (18px SemiBold)

List Items:
┌─────────────────────────┐
│ ✅ Scaled API           │
│    2 hours ago          │
│    Status: Complete     │
├─────────────────────────┤
│ ✅ Deploy Frontend      │
│    4 hours ago          │
│    Status: Complete     │
├─────────────────────────┤
│ ⏳ Set up monitoring    │
│    5 hours ago          │
│    Status: In Progress  │
└─────────────────────────┘

Each item:
- Status icon (✅ ⏳ ❌)
- Action description (14px Regular)
- Timestamp (12px, gray)
- Status badge with color

Footer:
[View All] - Link (14px, blue)
```

**Center Panel: Incident Cards**
```
Header: "Incident Cards"
Font: H3 (18px SemiBold)

Card:
┌─────────────────────────┐
│ 🔴 Constant 503 Errors  │
│                         │
│ Service: Prod API       │
│ Impact: High            │
│ Started: 10 min ago     │
│                         │
│ [Investigate] [Dismiss] │
└─────────────────────────┘

Severity Indicators:
- 🔴 Critical (Red border)
- 🟠 High (Orange border)
- 🟡 Medium (Yellow border)

Action Buttons:
[Investigate] - Primary (Blue)
[Dismiss] - Secondary (Gray)
```

**Right Panel: Audit Trail**
```
Header: "Audit Trail"
Font: H3 (18px SemiBold)

Timeline:
┌─────────────────────────┐
│ ● Apr 19 10:00 PM      │
│   Deploy API           │
│   by: Ujwal            │
│   Status: Success ✅   │
├─────────────────────────┤
│ ● Apr 19 08:30 PM      │
│   Scale Database       │
│   by: Ujwal            │
│   Status: Success ✅   │
├─────────────────────────┤
│ ● Apr 19 06:15 PM      │
│   Security Scan        │
│   by: System           │
│   Status: Pass ✅      │
└─────────────────────────┘

Each entry:
- Timeline bullet (●)
- Timestamp (12px, gray)
- Action (14px, bold)
- User (12px, gray)
- Status badge

Footer:
[View All] - Link
```

#### 4. Quick Actions Bar
```
Height: 80px
Background: #F8F9FA
Border Radius: 8px
Padding: LG (24px)
Margin-top: LG (24px)

Buttons (Horizontal):
┌────────────────┬────────────────┬────────────────┐
│ 📊 View       │ 💰 Cost       │ 🔒 Security   │
│    Metrics     │    Analysis    │    Scan        │
└────────────────┴────────────────┴────────────────┘

Each button:
- Icon (24px)
- Label (14px)
- Border: 1px solid #E8EAED
- Hover: Background #FFFFFF, Shadow increase
```

---

## 🔍 Task Preview Screen (After Command Input)

### When PM clicks [Continue]
```
┌─────────────────────────────────────────────────────────────────┐
│                        TASK PREVIEW                             │
│                                                                 │
│  You asked: "Deploy the API to production"                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  Here's what will happen:                                       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Step 1 of 8: Create Production VPC                       │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │ Action: Create VPC in us-east-1                          │ │
│  │ Resource: vpc-prod-api                                   │ │
│  │ Risk: Medium ⚠️                                           │ │
│  │ Rollback: Delete VPC                                     │ │
│  │ [Details ▼]                                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Step 2 of 8: Configure Security Groups                   │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │ Action: Create security group with ports 80, 443        │ │
│  │ Resource: sg-api-prod                                    │ │
│  │ Risk: High ⚠️                                             │ │
│  │ Rollback: Delete security group                          │ │
│  │ [Details ▼]                                              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ... (6 more steps collapsed)                                  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Step 8 of 8: Health Check & Verification                 │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │ Action: Run health checks on API endpoints              │ │
│  │ Resource: All production endpoints                       │ │
│  │ Risk: Low ✅                                              │ │
│  │ Rollback: N/A (diagnostic only)                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  ⚠️  HIGH RISK: This action affects PRODUCTION                 │
│                                                                 │
│  To confirm, type the service name: [________________]         │
│                                                                 │
│  Expected: "api"                                               │
│                                                                 │
│            [❌ Cancel]          [✅ Approve & Execute]          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Details

**Step Card (Collapsible)**
```
Component: StepCard
Width: 100%
Background: White
Border: 1px solid #E8EAED
Border-left: 4px solid [Risk Color]
Border Radius: 8px
Padding: LG (24px)
Margin-bottom: MD (16px)

Header:
- Step Number: "Step X of Y" (14px, gray)
- Title: Action description (16px, bold)
- Risk Badge: [Risk Level] with color

Body (Collapsed):
- 4 lines summary
- [Details ▼] button

Body (Expanded):
- Full parameters
- Resources affected
- Dependencies
- Estimated time
- Rollback procedure
```

**Confirmation Section (High Risk)**
```
Background: #FFF4E5 (light orange)
Border: 2px solid #F9AB00
Border Radius: 8px
Padding: XL (32px)

Warning Icon: ⚠️ (32px)
Message: "HIGH RISK: This action affects PRODUCTION"
Font: 18px SemiBold

Input Field:
- Label: "To confirm, type the service name:"
- Placeholder: "Type here..."
- Expected value shown below
- Must match exactly (case-insensitive)

Buttons:
[Cancel] - Secondary (Gray, left-aligned)
[Approve & Execute] - Primary (Green, right-aligned, disabled until correct input)
```

---

## 💬 Clarification Card (Ambiguity Detected)

### When Confidence < 85%
```
┌─────────────────────────────────────────────────────────────────┐
│                    CLARIFICATION NEEDED                         │
│                                                                 │
│  Your command: "Restart the service"                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  🤔 I found multiple services. Which one did you mean?         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ○ API Service                                            │ │
│  │   prod-api.promptops.com                                 │ │
│  │   Status: Running | Last deployed: 2h ago               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ○ Frontend Service                                       │ │
│  │   frontend.promptops.com                                 │ │
│  │   Status: Running | Last deployed: 4h ago               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ○ Database Service                                       │ │
│  │   postgres-prod.promptops.com                            │ │
│  │   Status: Running | Last deployed: 1d ago               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│             [Cancel]          [Continue with Selection]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Details

**Option Card (Selectable)**
```
Component: SelectableCard
Width: 100%
Background: White (#FFFFFF)
Border: 2px solid #E8EAED
Border Radius: 8px
Padding: LG (24px)
Margin-bottom: MD (16px)
Cursor: pointer

States:
- Default: Border #E8EAED
- Hover: Border #1155CC, Shadow increase
- Selected: Border #1155CC (thick), Background #E8F0FE (light blue), Radio filled

Layout:
- Radio button (left, 20px)
- Service Name (16px Bold)
- Service URL (14px, gray)
- Metadata (12px, gray)
  Format: "Status: X | Last deployed: Y"
```

**Question Section**
```
Icon: 🤔 (32px emoji)
Text: Clarification question
Font: 18px SemiBold
Color: #202124

Background: #F8F9FA (light gray)
Padding: LG (24px)
Border Radius: 8px
Margin-bottom: LG (24px)
```

---

## 📊 Execution Progress Screen

### Real-time Execution View
```
┌─────────────────────────────────────────────────────────────────┐
│                     EXECUTING: Deploy API                       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ✅ Step 1/8: Create VPC                   Complete (2s)   │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │ Resource created: vpc-prod-api-2026                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ⏳ Step 2/8: Configure Security Groups    In Progress...  │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │ Creating security group sg-api-prod...                    │ │
│  │ [████████████████░░░░░░░░░░░░] 65%                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ○ Step 3/8: Deploy Application             Waiting...     │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │ Dependencies: Step 1, 2                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ... (Steps 4-8 collapsed, waiting)                            │
│                                                                 │
│  Overall Progress: [████████████░░░░░░░░░░░░░░░░░░] 25%        │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  📊 Live Logs (Last 5 lines):                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ [14:32:15] VPC created successfully                       │ │
│  │ [14:32:17] Starting security group configuration...       │ │
│  │ [14:32:20] Inbound rules: ports 80, 443 configured        │ │
│  │ [14:32:22] Outbound rules: all traffic allowed            │ │
│  │ [14:32:24] Applying security group to VPC...              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [View Full Logs] [Cancel Execution]                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Status Icons & Colors
```
✅ Complete - Green (#34A853)
⏳ In Progress - Blue (#4285F4) with spinner
❌ Failed - Red (#EA4335)
○ Waiting - Gray (#9AA0A6)
⚠️ Warning - Yellow (#F9AB00)
```

---

## ✅ Success Screen

### Completion View
```
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ DEPLOYMENT SUCCESSFUL                     │
│                                                                 │
│  All 8 steps completed successfully!                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  📋 Summary:                                                    │
│  • Action: Deploy API to Production                           │
│  • Duration: 3 minutes 42 seconds                             │
│  • Resources Created: 8                                        │
│  • Started: Apr 19, 2026 2:30 PM                              │
│  • Completed: Apr 19, 2026 2:34 PM                            │
│  • Executed by: Ujwal                                          │
│                                                                 │
│  🔗 Service URL:                                               │
│  https://api.promptops.com                                     │
│  [Copy Link]                                                   │
│                                                                 │
│  📊 Health Check: ✅ All systems operational                    │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  What's next?                                                  │
│  • [📊 View Metrics]    Monitor API performance               │
│  • [🔔 Set Up Alerts]   Get notified of issues               │
│  • [📝 View Audit Log]  See what changed                      │
│                                                                 │
│                     [Back to Dashboard]                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ❌ Error Screen

### Failure View
```
┌─────────────────────────────────────────────────────────────────┐
│                    ❌ DEPLOYMENT FAILED                         │
│                                                                 │
│  Step 2/8 failed: Configure Security Groups                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  ⚠️ Error Details:                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Error Code: SecurityGroupLimitExceeded                    │ │
│  │ Message: You've reached the limit of 500 security        │ │
│  │ groups in us-east-1                                       │ │
│  │                                                           │ │
│  │ Timestamp: Apr 19, 2026 2:32:18 PM                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  🔄 Automatic Rollback:                                        │
│  ✅ Step 1: VPC deleted                                         │
│  ✅ All changes reverted                                        │
│                                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  💡 Suggested Actions:                                         │
│  1. Clean up unused security groups in us-east-1              │
│  2. Request limit increase from AWS                           │
│  3. Try deploying to different region                         │
│                                                                 │
│  [📞 Contact Support] [🔄 Retry] [🏠 Back to Dashboard]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📱 Mobile View (Responsive)

### Mobile Dashboard (320px - 768px)
```
┌──────────────────────┐
│ ☰  PromptOps    👤   │
├──────────────────────┤
│                      │
│ What would you like  │
│ to do?               │
│ ┌──────────────────┐ │
│ │ Deploy the API   │ │
│ │ to production    │ │
│ └──────────────────┘ │
│                      │
│ 🎯 Deploy            │
│ 📦 API               │
│ 🌍 Production        │
│ ⚠️  High Risk        │
│                      │
│    [Continue]        │
│                      │
├──────────────────────┤
│ Recent Actions ▼     │
│ ✅ Scaled API (2h)   │
│ ✅ Deploy (4h)       │
├──────────────────────┤
│ Incidents ▼          │
│ 🔴 503 Errors        │
│    [Investigate]     │
├──────────────────────┤
│ Audit Trail ▼        │
│ • 10:00 PM Deploy   │
│ • 08:30 PM Scale    │
└──────────────────────┘
```

### Mobile Features
- **Hamburger Menu** (☰) - Collapsible navigation
- **Single Column** - Stack all panels vertically
- **Touch-Friendly** - 48px minimum touch targets
- **Swipe Gestures** - Swipe to dismiss cards
- **Bottom Sheet** - Approval UI slides up from bottom

---

## 🎨 Component Library

### Buttons
```
Primary Button:
- Background: #1155CC
- Text: White, 14px SemiBold
- Height: 48px
- Border Radius: 8px
- Padding: 0 24px
- Hover: Background #0D47A1
- Active: Background #0A3D8F

Secondary Button:
- Background: Transparent
- Border: 2px solid #E8EAED
- Text: #5F6368, 14px SemiBold
- Hover: Border #1155CC, Text #1155CC

Danger Button:
- Background: #EA4335
- Text: White, 14px SemiBold
- Hover: Background #D33B2C
```

### Input Fields
```
Text Input:
- Height: 48px
- Border: 2px solid #E8EAED
- Border Radius: 8px
- Padding: 0 16px
- Font: 14px Regular
- Focus: Border #1155CC, Shadow 0 0 0 3px rgba(17,85,204,0.1)

Textarea:
- Min Height: 120px
- Padding: 16px
- Resize: vertical

Dropdown:
- Same as text input
- Chevron icon (▼) on right
```

### Cards
```
Card:
- Background: White
- Border: 1px solid #E8EAED
- Border Radius: 8px
- Padding: LG (24px)
- Shadow: 0 1px 3px rgba(0,0,0,0.08)
- Hover: Shadow 0 4px 12px rgba(0,0,0,0.12)
```

### Badges
```
Status Badge:
- Height: 24px
- Border Radius: 12px
- Padding: 0 12px
- Font: 12px SemiBold
- Colors:
  Success: Background #E6F4EA, Text #137333
  Warning: Background #FEF7E0, Text #B06000
  Error: Background #FCE8E6, Text #C5221F
  Info: Background #E8F0FE, Text #174EA6
```

---

## 🔐 Security & Trust Elements

### Trust Indicators
```
1. Approval Required Badge:
   ⚠️  REQUIRES APPROVAL
   Color: Orange background, dark text
   Always visible on high-risk actions

2. Production Warning:
   🔴 PRODUCTION
   Color: Red, bold
   Appears next to environment selector

3. Confirmation Input:
   "Type [resource name] to confirm"
   Must match exactly
   Prevents accidental clicks

4. Audit Trail Always Visible:
   Every action logged with:
   - Timestamp
   - User who approved
   - What changed
   - Result (success/failure)

5. Rollback Information:
   Every action shows how to undo it
   Automatic rollback on failure
```

---

## 🎯 User Flows

### Flow 1: Simple Deploy (Happy Path)
```
1. PM types: "Deploy the API to production"
2. Real-time preview shows: Deploy | API | Production | High Risk
3. PM clicks [Continue]
4. Task preview shows 8 steps
5. Confirmation: Type "api" to confirm
6. PM types "api" and clicks [Approve & Execute]
7. Progress screen shows live execution
8. Success screen with service URL
9. PM clicks [Back to Dashboard]
```

### Flow 2: Ambiguous Command (Clarification)
```
1. PM types: "Restart the service"
2. Parser confidence: 65% (below 85% threshold)
3. Clarification card shows 3 options:
   - API Service
   - Frontend Service
   - Database Service
4. PM selects "API Service"
5. Continues to task preview (normal flow)
```

### Flow 3: Failed Execution (Error Handling)
```
1. PM approves deployment
2. Steps 1-2 complete successfully
3. Step 3 fails (e.g., quota exceeded)
4. System shows error screen
5. Automatic rollback of steps 1-2
6. Error details + suggested actions shown
7. PM clicks [Retry] or [Back to Dashboard]
```

---

## 📐 Layout Specifications

### Desktop (1920x1080)
```
Header: 64px fixed top
Main Content: Center-aligned, max 1400px wide
Sidebar: 280px (if navigation grows)
Footer: 80px
Padding: 32px horizontal, 24px vertical
```

### Tablet (768x1024)
```
Header: 64px fixed top
Main Content: Full width with 24px padding
Single column layout
Collapsible panels
```

### Mobile (375x667)
```
Header: 56px fixed top
Main Content: Full width with 16px padding
Stack all elements vertically
Bottom navigation (optional)
Floating action button for quick actions
```

---

## 🚀 Animations & Interactions

### Microinteractions
```
Button Click:
- Scale: 0.98 (press down effect)
- Duration: 100ms

Card Hover:
- Shadow increase
- Border color change
- Duration: 200ms, ease-out

Success Animation:
- Checkmark draws in (SVG animation)
- Green circle expands
- Duration: 600ms

Progress Bar:
- Smooth fill animation
- Pulse effect while loading
- Duration: 300ms per update

Toast Notifications:
- Slide in from top
- Auto-dismiss after 5s
- Can be manually dismissed
```

### Loading States
```
Skeleton Screens:
- Show layout structure while loading
- Animated shimmer effect
- Replace with real content

Spinners:
- Use for <2s waits
- Blue circular spinner
- 32px size

Progress Bars:
- Use for >2s operations
- Show percentage
- Indeterminate if time unknown
```

---

## 🎨 Dark Mode (Future)

### Dark Color Palette
```
Background: #1A1A1A
Cards: #2D2D2D
Text Primary: #E8EAED
Text Secondary: #9AA0A6
Borders: #3C4043
Accent: #8AB4F8 (lighter blue)
```

---

## ✅ Complete - Design Specification Ready

This design creates:
✅ **Simplicity** - PMs can operate without technical knowledge
✅ **Safety** - Multiple confirmation steps for risky actions
✅ **Transparency** - Always shows what will happen before executing
✅ **Trust** - Audit trail, rollback info, clear risk indicators
✅ **Mobile-Ready** - Works on phone at 3 AM during incidents

**Next:** Build these components in Week 9-10 using React + v0.dev for rapid prototyping!
