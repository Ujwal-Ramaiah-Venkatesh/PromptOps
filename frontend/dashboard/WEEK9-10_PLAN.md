# Week 9-10: PM Dashboard Shell - Implementation Plan

**Timeline:** June 2 – June 13, 2026 (10 working days)  
**Status:** 🚧 IN PROGRESS  
**Owner:** PromptOps Team

---

## Executive Summary

Build the **PM Dashboard Shell** - the primary interface PMs will use to issue commands, review task plans, approve high-risk operations, and view audit logs. This is the user-facing culmination of Weeks 1-8 work.

### Core Problem

PMs need a simple, intuitive interface to:
- Issue plain-English commands
- See real-time intent preview
- Review decomposed task plans
- Approve risky operations with explicit confirmation
- Monitor execution status
- View audit history

---

## Goals

1. **Main Dashboard Layout**: 4-panel interface design
2. **Command Input Component**: Real-time intent preview as PM types
3. **Approval Flow UI**: Typed confirmation for risky actions
4. **Audit Trail View**: Immutable log of all commands
5. **Mobile Responsive**: Usable on phone for 3 AM on-call

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PM Dashboard Shell                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                         Main Dashboard                            │
│  ┌────────────────────┬────────────────────┐                     │
│  │   Command Input    │   Drift Alert      │  ← Top Bar          │
│  └────────────────────┴────────────────────┘                     │
│  ┌──────────────────────────────────────────┐                    │
│  │          Task Preview                    │  ← Center Panel    │
│  │   - Sub-tasks                            │                    │
│  │   - Timeline                             │                    │
│  │   - Dependencies                         │                    │
│  │   - Rollback Plan                        │                    │
│  └──────────────────────────────────────────┘                    │
│  ┌────────────────────┬────────────────────┐                     │
│  │   Approval Flow    │   Audit Trail      │  ← Bottom Panels   │
│  └────────────────────┴────────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘

User Journey:
1. PM types command → CommandInput
2. Real-time parsing → Intent preview
3. Click "Decompose" → TaskPreview shows
4. Review tasks → Approve/Reject
5. If risky → ApprovalFlow (typed confirmation)
6. Execute → Monitor status
7. View history → AuditTrail
```

---

## Task Breakdown

### DASHBOARD-001: Main Dashboard Layout ⏱️ Day 1-2

**Goal:** Design the 4-panel dashboard structure.

**Layout Specifications:**
- **Top Bar**: Command input + drift alerts
- **Center Panel**: Task preview (largest area)
- **Bottom Left**: Approval flow (when needed)
- **Bottom Right**: Recent audit trail

**Deliverable:** `frontend/dashboard/layouts/MainDashboard.tsx`

**Component Structure:**
```tsx
interface DashboardProps {
  user: User;
  onCommandSubmit: (command: string) => void;
  onApprove: (taskPlan: TaskPlan) => void;
  onReject: (reason: string) => void;
}

export function MainDashboard(props: DashboardProps): JSX.Element {
  const [currentCommand, setCurrentCommand] = useState('');
  const [parsedIntent, setParsedIntent] = useState(null);
  const [decomposition, setDecomposition] = useState(null);
  const [showApproval, setShowApproval] = useState(false);
  const [driftEvents, setDriftEvents] = useState([]);
  
  return (
    <div className="main-dashboard">
      <header className="dashboard-header">
        <CommandInput
          value={currentCommand}
          onChange={setCurrentCommand}
          onSubmit={handleCommandSubmit}
          parsedIntent={parsedIntent}
        />
        <DriftAlert
          driftEvents={driftEvents}
          onAcceptDrift={handleAcceptDrift}
          onRevertDrift={handleRevertDrift}
        />
      </header>
      
      <main className="dashboard-main">
        {decomposition && (
          <TaskPreview
            decomposition={decomposition}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        )}
      </main>
      
      <footer className="dashboard-footer">
        {showApproval && (
          <ApprovalFlow
            taskPlan={decomposition}
            onConfirm={handleApprovalConfirm}
            onCancel={handleApprovalCancel}
          />
        )}
        <AuditTrail
          limit={10}
          onViewAll={handleViewAllAudit}
        />
      </footer>
    </div>
  );
}
```

**Success Criteria:**
- 4-panel layout renders correctly
- Responsive breakpoints defined
- State management functional
- Component integration working

---

### DASHBOARD-002: Command Input Component ⏱️ Day 2-3

**Goal:** Build command input with real-time intent preview.

**Features:**
1. **Auto-complete**: Suggest commands as PM types
2. **Intent Preview**: Show parsed intent in real-time
3. **Confidence Indicator**: Visual confidence score
4. **Ambiguity Warnings**: Highlight missing parameters
5. **Quick Actions**: Recent commands, templates

**Deliverable:** `frontend/dashboard/components/CommandInput.tsx`

**Component Behavior:**
```tsx
interface CommandInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (command: string) => void;
  parsedIntent: ParsedIntent | null;
  autoComplete?: boolean;
}

export function CommandInput(props: CommandInputProps): JSX.Element {
  const [suggestions, setSuggestions] = useState([]);
  const [intentPreview, setIntentPreview] = useState(null);
  
  // Debounced parsing (500ms delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (props.value.length > 3) {
        parseCommandPreview(props.value);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [props.value]);
  
  return (
    <div className="command-input">
      <div className="input-wrapper">
        <textarea
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder="Enter command (e.g., 'Deploy frontend v2.0 to staging')"
          rows={2}
        />
        <button onClick={() => props.onSubmit(props.value)}>
          Decompose
        </button>
      </div>
      
      {intentPreview && (
        <IntentPreview
          intent={intentPreview}
          confidence={intentPreview.confidence}
        />
      )}
      
      {suggestions.length > 0 && (
        <Suggestions
          suggestions={suggestions}
          onSelect={(cmd) => props.onChange(cmd)}
        />
      )}
    </div>
  );
}
```

**Intent Preview Display:**
```
┌────────────────────────────────────────────────────────┐
│ Intent Preview                               [92% ✓]   │
├────────────────────────────────────────────────────────┤
│ Type: deploy                                           │
│ Service: frontend                                      │
│ Environment: staging                                   │
│ Version: v2.0                                          │
│                                                        │
│ ✓ All required parameters present                     │
└────────────────────────────────────────────────────────┘
```

**Auto-complete Sources:**
- Recent commands (last 10)
- Common templates ("Deploy {service} to {env}")
- Context-aware suggestions (services from context store)

**Success Criteria:**
- Real-time parsing with 500ms debounce
- Intent preview updates as PM types
- Confidence score displayed
- Auto-complete functional
- Enter key submits

---

### DASHBOARD-003: Approval Flow UI ⏱️ Day 3-4

**Goal:** Build approval flow with typed confirmation for risky operations.

**Features:**
1. **Risk Assessment Display**: Show why approval is needed
2. **Typed Confirmation**: PM must type exact phrase
3. **Impact Summary**: What will change
4. **Rollback Plan**: Show undo strategy
5. **Time Limit**: Approval expires after 5 minutes

**Deliverable:** `frontend/dashboard/components/ApprovalFlow.tsx`

**Approval Triggers:**
- Production deployments
- Scaling >50% change
- Database migrations
- Deletions/rollbacks
- Cost impact >$1000/month

**Component Structure:**
```tsx
interface ApprovalFlowProps {
  taskPlan: TaskPlan;
  onConfirm: () => void;
  onCancel: () => void;
  timeoutMinutes?: number;
}

export function ApprovalFlow(props: ApprovalFlowProps): JSX.Element {
  const [confirmationText, setConfirmationText] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(300); // 5 min
  
  const requiredPhrase = `APPROVE ${props.taskPlan.operation_id}`;
  const isConfirmed = confirmationText === requiredPhrase;
  
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          props.onCancel(); // Auto-cancel on timeout
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);
  
  return (
    <div className="approval-flow">
      <div className="approval-header">
        <h3>⚠️ Approval Required</h3>
        <div className="approval-timer">
          Expires in {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
        </div>
      </div>
      
      <RiskAssessment risk={props.taskPlan.risk_assessment} />
      
      <ImpactSummary
        before={props.taskPlan.current_state}
        after={props.taskPlan.target_state}
      />
      
      <RollbackPlan plan={props.taskPlan.rollback_plan} />
      
      <div className="approval-confirmation">
        <label>
          Type <code>{requiredPhrase}</code> to confirm:
        </label>
        <input
          type="text"
          value={confirmationText}
          onChange={(e) => setConfirmationText(e.target.value)}
          placeholder="Type confirmation phrase..."
          autoComplete="off"
        />
      </div>
      
      <div className="approval-actions">
        <button onClick={props.onCancel} className="btn-cancel">
          Cancel
        </button>
        <button
          onClick={props.onConfirm}
          disabled={!isConfirmed}
          className="btn-approve"
        >
          Approve & Execute
        </button>
      </div>
    </div>
  );
}
```

**Risk Assessment Display:**
```
┌────────────────────────────────────────────────────────┐
│ Risk Assessment: HIGH                                  │
├────────────────────────────────────────────────────────┤
│ ⚠️ This operation will:                                │
│   • Deploy to PRODUCTION environment                   │
│   • Impact 10 running instances                        │
│   • Affect 500+ active users                           │
│   • Cost estimate: +$250/month                         │
│                                                        │
│ Rollback available: Yes (v2.3.1 → v2.4.0)             │
│ Estimated rollback time: 3 minutes                     │
└────────────────────────────────────────────────────────┘
```

**Success Criteria:**
- Typed confirmation required
- Timer countdown functional
- Auto-cancel on timeout
- Risk assessment clear
- Rollback plan visible

---

### DASHBOARD-004: Audit Trail View ⏱️ Day 4-5

**Goal:** Immutable log of all commands and actions.

**Features:**
1. **Chronological List**: Newest first
2. **Filterable**: By user, environment, intent type, date range
3. **Searchable**: Full-text search
4. **Expandable Details**: Show full task plan
5. **Export**: CSV/JSON export

**Deliverable:** `frontend/dashboard/components/AuditTrail.tsx`

**Audit Log Entry:**
```typescript
interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  command: string;
  intent_type: string;
  target_service: string;
  target_env: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | 'failed';
  approval_required: boolean;
  approved_by?: string;
  approved_at?: string;
  execution_duration?: number;
  error_message?: string;
  task_count: number;
  cost_impact?: number;
}
```

**Component Structure:**
```tsx
interface AuditTrailProps {
  limit?: number;
  onViewAll?: () => void;
  filters?: AuditFilters;
}

export function AuditTrail(props: AuditTrailProps): JSX.Element {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [filter, setFilter] = useState<AuditFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  
  return (
    <div className="audit-trail">
      <div className="audit-header">
        <h3>Recent Activity</h3>
        <div className="audit-filters">
          <input
            type="search"
            placeholder="Search commands..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <select onChange={(e) => setFilter({...filter, env: e.target.value})}>
            <option value="">All Environments</option>
            <option value="production">Production</option>
            <option value="staging">Staging</option>
          </select>
        </div>
      </div>
      
      <div className="audit-entries">
        {entries.map(entry => (
          <AuditEntry
            key={entry.id}
            entry={entry}
            onExpand={() => showDetails(entry)}
          />
        ))}
      </div>
      
      {props.onViewAll && (
        <button onClick={props.onViewAll} className="btn-view-all">
          View All History
        </button>
      )}
    </div>
  );
}
```

**Audit Entry Display:**
```
┌────────────────────────────────────────────────────────┐
│ 🟢 Deploy frontend v2.4.0 to production                │
│ user@company.com • 2 mins ago • 8 tasks • Completed    │
├────────────────────────────────────────────────────────┤
│ Environment: production                                │
│ Approved by: manager@company.com                       │
│ Duration: 4m 23s                                       │
│ [View Details]                                         │
└────────────────────────────────────────────────────────┘
```

**Status Colors:**
- 🟡 Pending: Yellow
- 🟢 Completed: Green
- 🔴 Failed: Red
- ⚪ Rejected: Gray

**Success Criteria:**
- Shows last 10 entries by default
- Real-time updates (new entries appear)
- Search functional
- Filters work
- Export button available

---

### DASHBOARD-005: Mobile Responsiveness ⏱️ Day 5-6

**Goal:** Ensure dashboard is usable on mobile (for 3 AM on-call).

**Breakpoints:**
- Desktop: >1200px (4-panel layout)
- Tablet: 768-1200px (2-panel stacked)
- Mobile: <768px (single column)

**Deliverable:** `frontend/dashboard/styles/mobile.css`

**Mobile Adaptations:**

1. **Command Input**: Larger touch targets, full-width
2. **Task Preview**: Collapsible sections, swipe gestures
3. **Approval Flow**: Modal overlay (full screen)
4. **Audit Trail**: Simplified view, expandable cards

**Mobile Layout:**
```
┌─────────────────────┐
│  Command Input      │  ← Full width
├─────────────────────┤
│  Drift Alert        │  ← Banner (if any)
├─────────────────────┤
│  Task Preview       │  ← Scrollable
│  [Expand/Collapse]  │
├─────────────────────┤
│  Approval Flow      │  ← Modal when needed
├─────────────────────┤
│  Recent Activity    │  ← Last 3 entries
│  [View More]        │
└─────────────────────┘
```

**Touch Optimizations:**
- Minimum touch target: 44x44px
- Swipe to dismiss notifications
- Pull to refresh
- Haptic feedback on approve/reject

**Success Criteria:**
- Usable on iPhone/Android
- No horizontal scrolling
- Touch targets large enough
- Critical actions accessible
- Offline mode (view cached data)

---

### DASHBOARD-006: State Management & API Integration ⏱️ Day 6-7

**Goal:** Wire dashboard to backend APIs and manage state.

**State Management Options:**
- **React Context API**: For simple state
- **Redux Toolkit**: For complex state
- **React Query**: For API data fetching

**API Endpoints Required:**
```typescript
// Command parsing
POST /api/v1/parse
Body: { command: string }
Response: { success: bool, intent: ParsedIntent }

// Task decomposition
POST /api/v1/decompose
Body: { intent: ParsedIntent }
Response: { success: bool, decomposition: Decomposition }

// Task execution
POST /api/v1/execute
Body: { task_plan: TaskPlan, approval: Approval }
Response: { success: bool, execution_id: string }

// Drift events
GET /api/v1/drift/current
Response: { drift_events: DriftEvent[] }

// Audit trail
GET /api/v1/audit?limit=50&offset=0
Response: { entries: AuditEntry[], total: number }

// WebSocket for real-time updates
WS /api/v1/ws
Events: task_update, drift_detected, approval_required
```

**State Structure:**
```typescript
interface DashboardState {
  user: User;
  currentCommand: string;
  parsedIntent: ParsedIntent | null;
  decomposition: Decomposition | null;
  executionStatus: ExecutionStatus | null;
  driftEvents: DriftEvent[];
  auditEntries: AuditEntry[];
  loading: boolean;
  error: string | null;
}
```

**Success Criteria:**
- API integration functional
- Real-time updates via WebSocket
- Error handling implemented
- Loading states shown
- Optimistic updates for better UX

---

### DASHBOARD-007: Error Handling & User Feedback ⏱️ Day 7-8

**Goal:** Comprehensive error handling and user feedback.

**Error Types:**

1. **Parsing Errors**: Ambiguous commands
2. **Validation Errors**: Missing parameters
3. **Execution Errors**: Task failures
4. **Network Errors**: API timeouts
5. **Permission Errors**: Unauthorized actions

**User Feedback Components:**

```tsx
// Toast notifications
<Toast
  message="Command executed successfully"
  type="success"
  duration={3000}
/>

// Error banner
<ErrorBanner
  error="Failed to connect to AWS. Please check credentials."
  onRetry={handleRetry}
  onDismiss={handleDismiss}
/>

// Loading states
<Skeleton /> // While loading
<Spinner /> // During execution

// Empty states
<EmptyState
  icon="📋"
  title="No recent activity"
  description="Your commands will appear here"
/>
```

**Success Criteria:**
- All error types handled
- Clear error messages
- Retry buttons where applicable
- Loading states smooth
- Success feedback immediate

---

### DASHBOARD-008: Keyboard Shortcuts & Accessibility ⏱️ Day 8-9

**Goal:** Power-user features and accessibility compliance.

**Keyboard Shortcuts:**
- `Cmd/Ctrl + K`: Focus command input
- `Cmd/Ctrl + Enter`: Submit command
- `Esc`: Cancel approval flow
- `Cmd/Ctrl + /`: Show shortcuts help
- `Arrow keys`: Navigate audit trail

**Accessibility Features:**
- **ARIA labels**: All interactive elements
- **Keyboard navigation**: Full keyboard support
- **Screen reader**: Announcements for state changes
- **Focus management**: Logical tab order
- **Color contrast**: WCAG AA compliant
- **Reduced motion**: Respect prefers-reduced-motion

**Deliverable:** `frontend/dashboard/components/KeyboardShortcuts.tsx`

**Success Criteria:**
- All actions keyboard accessible
- Screen reader functional
- WCAG AA compliance
- Focus indicators visible
- Shortcuts help modal

---

### DASHBOARD-009: Testing & Polish ⏱️ Day 9-10

**Goal:** Comprehensive testing and final polish.

**Test Coverage:**

1. **Unit Tests**: Individual components
2. **Integration Tests**: Component interactions
3. **E2E Tests**: Full user flows
4. **Visual Regression**: Screenshot comparison
5. **Accessibility Tests**: Automated a11y checks

**Test Framework:**
- Jest + React Testing Library
- Cypress for E2E
- Axe for accessibility

**Polish Items:**
- Animations smooth (60fps)
- Micro-interactions polished
- Error messages helpful
- Loading states consistent
- Dark mode complete

**Success Criteria:**
- >80% test coverage
- All E2E flows passing
- No accessibility errors
- Performance optimized
- Ready for user testing

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Component Count | 5+ | React components |
| Test Coverage | >80% | Jest coverage |
| Accessibility | WCAG AA | Axe audit |
| Mobile Support | Yes | Responsive breakpoints |
| Performance | <200ms render | Chrome DevTools |
| User Satisfaction | >4/5 | Internal testing |

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | React 18 + TypeScript | Type safety, modern React |
| State | React Context + React Query | Simple, efficient |
| Styling | CSS Modules + Tailwind | Scoped styles + utility |
| Testing | Jest + React Testing Library | Industry standard |
| E2E | Cypress | Reliable, good DX |
| Real-time | WebSocket | Low latency |

---

## Exit Criteria

Week 9-10 is complete when:

- ✅ Main dashboard layout functional (4 panels)
- ✅ Command input with real-time preview
- ✅ Approval flow with typed confirmation
- ✅ Audit trail with filtering
- ✅ Mobile responsive (<768px usable)
- ✅ State management integrated
- ✅ Error handling comprehensive
- ✅ Keyboard shortcuts working
- ✅ >80% test coverage
- ✅ Accessibility compliant

---

## Timeline

```
Week 9 (Jun 2-6):
  Day 1-2: DASHBOARD-001 (Main Layout)
  Day 3-4: DASHBOARD-002 (Command Input) + DASHBOARD-003 (Approval Flow)
  Day 5:   DASHBOARD-004 (Audit Trail)

Week 10 (Jun 9-13):
  Day 6-7: DASHBOARD-005 (Mobile) + DASHBOARD-006 (State Management)
  Day 8:   DASHBOARD-007 (Error Handling)
  Day 9:   DASHBOARD-008 (Accessibility)
  Day 10:  DASHBOARD-009 (Testing & Polish)
```

---

## Next Steps

After Week 9-10 completion:
- **Week 11-12**: Integration & Testing (E2E, performance, security)
- **Phase 1 Complete**: Ready for stakeholder demo

---

**Status**: 🚧 **READY TO START**  
**First Task**: DASHBOARD-001 - Main Dashboard Layout  
**Est. Time**: 2-3 hours

---

*Created: 2026-04-28*  
*Week 9-10 PM Dashboard Shell*
