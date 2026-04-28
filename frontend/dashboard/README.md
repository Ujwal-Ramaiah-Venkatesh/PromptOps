# PM Dashboard Shell

**Week 9-10 Deliverable**: User interface for Product Managers to issue commands, review task plans, approve high-risk operations, and monitor execution.

---

## Overview

The PM Dashboard is the primary interface for PromptOps. It provides:

- **Command Input**: Natural language command entry with real-time intent preview
- **Task Preview**: Visualization of decomposed tasks with timeline and dependencies
- **Approval Flow**: Typed confirmation for high-risk operations
- **Audit Trail**: Immutable log of all commands and actions
- **Drift Monitoring**: Real-time infrastructure drift alerts

---

## Architecture

```
frontend/dashboard/
├── layouts/
│   ├── MainDashboard.tsx          # Main 4-panel layout
│   └── MainDashboard.css          # Layout styling
├── components/
│   ├── CommandInput.tsx           # Command input with autocomplete
│   ├── CommandInput.css
│   ├── ApprovalFlow.tsx           # Typed confirmation UI
│   ├── ApprovalFlow.css
│   ├── AuditTrail.tsx             # Audit log with filtering
│   ├── AuditTrail.css
│   ├── ErrorBoundary.tsx          # Error handling & toasts
│   └── ErrorBoundary.css
├── hooks/
│   ├── useDashboardState.ts       # State management & API integration
│   ├── useKeyboardShortcuts.ts    # Keyboard shortcuts
│   └── KeyboardShortcuts.css      # Shortcuts modal styling
├── tests/
│   ├── Dashboard.test.tsx         # Unit tests (Jest + RTL)
│   └── Dashboard.e2e.test.ts      # E2E tests (Cypress)
├── WEEK9-10_PLAN.md               # Implementation plan
└── README.md                      # This file
```

---

## Components

### 1. MainDashboard

**File**: `layouts/MainDashboard.tsx`

4-panel responsive layout:

- **Top Bar**: Command input + Drift alerts
- **Center**: Task preview (largest area)
- **Bottom Left**: Approval flow (when needed)
- **Bottom Right**: Recent audit trail

**Props**:
```typescript
interface MainDashboardProps {
  user: User;
  onCommandSubmit: (command: string) => void;
  onApprove: (taskPlan: TaskPlan) => void;
  onReject: (reason: string) => void;
}
```

**State Management**: Uses `useDashboardState` hook for centralized state.

---

### 2. CommandInput

**File**: `components/CommandInput.tsx`

Real-time command parsing with autocomplete and intent preview.

**Features**:
- 500ms debounced parsing
- Auto-complete suggestions (recent + templates)
- Confidence indicator (circular progress)
- Intent preview with validation status
- Keyboard shortcuts (Enter to submit, Tab for suggestions)

**Props**:
```typescript
interface CommandInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (command: string) => void;
  parsedIntent?: ParsedIntent | null;
  isLoading?: boolean;
  autoComplete?: boolean;
}
```

---

### 3. ApprovalFlow

**File**: `components/ApprovalFlow.tsx`

Typed confirmation for high-risk operations.

**Features**:
- Risk assessment display (low/medium/high/critical)
- Typed confirmation (must match exact phrase)
- 5-minute countdown timer with urgency levels
- Impact summary (before/after comparison)
- Rollback plan preview (collapsible)
- Auto-cancel on timeout

**Props**:
```typescript
interface ApprovalFlowProps {
  taskPlan: TaskPlan;
  onConfirm: () => void;
  onCancel: () => void;
  timeoutMinutes?: number;
}
```

**Approval Triggers**:
- Production deployments
- Scaling >50% change
- Database migrations
- Deletions/rollbacks
- Cost impact >$1000/month

---

### 4. AuditTrail

**File**: `components/AuditTrail.tsx`

Immutable log with filtering and export.

**Features**:
- Chronological list (newest first)
- Full-text search
- Multi-filter (user, env, type, status, date range)
- Expandable details
- Status indicators (pending/approved/rejected/completed/failed)
- Export to CSV/JSON
- Pagination

**Props**:
```typescript
interface AuditTrailProps {
  entries?: AuditEntry[];
  limit?: number;
  onViewAll?: () => void;
  onRefresh?: () => void;
  showFilters?: boolean;
  showSearch?: boolean;
  showExport?: boolean;
  compact?: boolean;
}
```

---

### 5. ErrorBoundary

**File**: `components/ErrorBoundary.tsx`

Error handling with user feedback.

**Features**:
- React error boundary
- User-friendly error messages
- Error stack traces (dev mode)
- Automatic error reporting
- Toast notifications (success/error/warning/info)
- Loading overlay with progress

**Components**:
- `<ErrorBoundary>` - Catch React errors
- `<ToastNotification>` - Individual toast
- `<ToastContainer>` - Toast manager
- `<LoadingOverlay>` - Loading indicator

**Hooks**:
- `useToast()` - Toast management

---

## Hooks

### useDashboardState

**File**: `hooks/useDashboardState.ts`

Central state management with API integration.

**Usage**:
```typescript
const [state, actions] = useDashboardState({
  user: 'pm@company.com',
  apiBaseUrl: '/api',
  pollingInterval: 60000, // 60s for drift
  enableAutoRefresh: true
});

// State
state.currentCommand
state.parsedIntent
state.decomposition
state.showApproval
state.auditEntries
state.driftEvents
state.error

// Actions
actions.setCommand('Deploy frontend')
actions.submitCommand()
actions.approveTask()
actions.rejectTask('Not ready')
actions.acknowledgeDrift(driftId)
actions.refreshAudit()
actions.clearError()
```

**Features**:
- Debounced intent parsing (500ms)
- Drift polling (60s)
- Error handling
- Loading states
- API integration

---

### useKeyboardShortcuts

**File**: `hooks/useKeyboardShortcuts.ts`

Keyboard shortcut management.

**Usage**:
```typescript
const shortcuts = getDashboardShortcuts({
  focusCommandInput: () => {...},
  submitCommand: () => {...},
  approveTask: () => {...},
  // ... other actions
});

useKeyboardShortcuts(shortcuts);
```

**Default Shortcuts**:
- `/` - Focus command input
- `Cmd/Ctrl+K` - Focus command input
- `Cmd/Ctrl+Enter` - Submit command
- `Cmd/Ctrl+Shift+A` - Approve task
- `Cmd/Ctrl+Shift+X` - Reject task
- `Cmd/Ctrl+H` - View audit trail
- `Cmd/Ctrl+E` - Export audit
- `Esc` - Clear command / Close modal
- `Shift+?` - Show keyboard shortcuts help

---

## Styling

All components include comprehensive CSS with:

- **Responsive Design**: Breakpoints at 768px (mobile) and 1024px (tablet)
- **Dark Mode**: `prefers-color-scheme: dark` media queries
- **Accessibility**: Focus indicators, reduced motion support, high contrast mode
- **Touch Optimization**: 44x44px minimum touch targets for mobile

---

## Testing

### Unit Tests

**File**: `tests/Dashboard.test.tsx`

- Component rendering
- User interactions
- State management
- Error handling
- Keyboard shortcuts

**Run**:
```bash
npm test
```

### E2E Tests

**File**: `tests/Dashboard.e2e.test.ts`

- Full user workflows
- Command submission → Approval → Execution
- Drift handling
- Mobile responsiveness
- Accessibility (axe-core)

**Run**:
```bash
npm run cypress:open
```

---

## API Integration

The dashboard expects the following API endpoints:

### Parse Intent
```
POST /api/parse-intent
Body: { command: string, user: string }
Response: { intent: ParsedIntent }
```

### Decompose Task
```
POST /api/decompose
Body: { intent: ParsedIntent, user: string }
Response: { decomposition: Decomposition }
```

### Execute Task
```
POST /api/execute
Body: { decomposition_id: string, user: string, approved: boolean }
Response: { status: string, execution_id: string }
```

### Get Audit Trail
```
GET /api/audit?limit=50
Response: { entries: AuditEntry[] }
```

### Export Audit
```
GET /api/audit/export?format=csv|json
Response: Blob (CSV or JSON file)
```

### Get Drift Events
```
GET /api/drift/recent
Response: { events: DriftEvent[], unacknowledged_count: number }
```

### Acknowledge Drift
```
POST /api/drift/:id/acknowledge
Body: { user: string }
Response: { success: boolean }
```

### Revert Drift
```
POST /api/drift/:id/revert
Body: { user: string }
Response: { success: boolean }
```

---

## Usage Example

```tsx
import React from 'react';
import { MainDashboard } from './layouts/MainDashboard';

function App() {
  const user = {
    name: 'Product Manager',
    email: 'pm@company.com',
    role: 'PM'
  };

  const handleCommandSubmit = async (command: string) => {
    console.log('Command submitted:', command);
  };

  const handleApprove = async (taskPlan: any) => {
    console.log('Task approved:', taskPlan);
  };

  const handleReject = async (reason: string) => {
    console.log('Task rejected:', reason);
  };

  return (
    <MainDashboard
      user={user}
      onCommandSubmit={handleCommandSubmit}
      onApprove={handleApprove}
      onReject={handleReject}
    />
  );
}

export default App;
```

---

## Deployment

### Build for Production

```bash
npm run build
```

### Environment Variables

```env
REACT_APP_API_BASE_URL=https://api.promptops.com
REACT_APP_POLLING_INTERVAL=60000
REACT_APP_ENABLE_AUTO_REFRESH=true
```

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari 14+, Chrome Mobile 90+)

---

## Accessibility

All components follow WCAG 2.1 Level AA standards:

- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Focus indicators
- ✅ ARIA labels
- ✅ Color contrast ratios >4.5:1
- ✅ Reduced motion support
- ✅ High contrast mode

---

## Performance

- Initial load: <3s
- Time to interactive: <5s
- Lighthouse score: >90
- Bundle size: ~200KB gzipped

---

## Roadmap

### Completed ✅
- Main dashboard layout
- Command input with autocomplete
- Approval flow with typed confirmation
- Audit trail with filtering
- Mobile responsiveness
- Error handling & toasts
- Keyboard shortcuts
- Comprehensive testing

### Future Enhancements 🔮
- Real-time WebSocket updates
- Offline mode with service workers
- Advanced visualizations (dependency graph rendering)
- Custom themes
- Multi-language support
- Voice commands
- AI-powered command suggestions

---

## Support

For issues or questions:
- GitHub: https://github.com/promptops/dashboard/issues
- Email: support@promptops.com
- Slack: #promptops-dashboard

---

**Author**: PromptOps Team  
**Date**: 2026-04-28  
**Version**: 1.0.0
