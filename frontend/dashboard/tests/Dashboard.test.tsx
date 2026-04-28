/**
 * Dashboard Component Tests
 * ==========================
 *
 * Unit and integration tests for PM Dashboard components.
 *
 * Test Coverage:
 * - Component rendering
 * - User interactions
 * - State management
 * - API integration
 * - Error handling
 * - Keyboard shortcuts
 * - Accessibility
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import { MainDashboard } from '../layouts/MainDashboard';
import { CommandInput } from '../components/CommandInput';
import { ApprovalFlow } from '../components/ApprovalFlow';
import { AuditTrail } from '../components/AuditTrail';
import { ErrorBoundary, useToast } from '../components/ErrorBoundary';
import { useDashboardState } from '../hooks/useDashboardState';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

// ============================================================================
// Mock Data
// ============================================================================

const mockUser = {
  name: 'Test User',
  email: 'test@company.com',
  role: 'PM'
};

const mockParsedIntent = {
  intent_type: 'deploy',
  target_service: 'frontend',
  target_env: 'staging',
  parameters: { version: 'v2.0' },
  confidence: 0.95,
  ambiguity_score: 0.05,
  missing_params: [],
  requires_approval: false
};

const mockDecomposition = {
  decomposition_id: 'decomp-12345',
  operation_id: '12345',
  timestamp: new Date().toISOString(),
  total_sub_tasks: 5,
  estimated_duration: 300,
  risk_assessment: {
    overall_risk: 'medium' as const,
    risk_factors: ['Production deployment', 'Multiple services'],
    estimated_cost_impact: 500,
    affected_users: 1000,
    requires_approval: true,
    approval_level: 'senior-pm'
  },
  original_intent: mockParsedIntent,
  sub_tasks: [],
  rollback_plan: {
    total_steps: 3,
    estimated_duration: 120,
    irreversible_tasks: []
  },
  current_state: { version: 'v1.9' },
  target_state: { version: 'v2.0' }
};

const mockAuditEntries = [
  {
    id: 'audit-1',
    timestamp: new Date().toISOString(),
    user: 'test@company.com',
    command: 'Deploy frontend v2.0 to staging',
    intent_type: 'deploy',
    target_service: 'frontend',
    target_env: 'staging',
    status: 'completed' as const,
    risk_level: 'medium' as const,
    duration: 240
  }
];

// ============================================================================
// CommandInput Tests
// ============================================================================

describe('CommandInput', () => {
  test('renders command input', () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn();

    render(
      <CommandInput
        value=""
        onChange={onChange}
        onSubmit={onSubmit}
      />
    );

    expect(screen.getByPlaceholderText(/Enter command/i)).toBeInTheDocument();
  });

  test('handles text input', async () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn();

    render(
      <CommandInput
        value=""
        onChange={onChange}
        onSubmit={onSubmit}
      />
    );

    const input = screen.getByPlaceholderText(/Enter command/i);
    await userEvent.type(input, 'Deploy frontend');

    expect(onChange).toHaveBeenCalledTimes(15); // Each character
  });

  test('shows intent preview when parsed', () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn();

    render(
      <CommandInput
        value="Deploy frontend to staging"
        onChange={onChange}
        onSubmit={onSubmit}
        parsedIntent={mockParsedIntent}
      />
    );

    expect(screen.getByText('Intent Preview')).toBeInTheDocument();
    expect(screen.getByText('deploy')).toBeInTheDocument();
    expect(screen.getByText('frontend')).toBeInTheDocument();
  });

  test('submits command on button click', async () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn();

    render(
      <CommandInput
        value="Deploy frontend"
        onChange={onChange}
        onSubmit={onSubmit}
      />
    );

    const submitButton = screen.getByLabelText('Submit command');
    await userEvent.click(submitButton);

    expect(onSubmit).toHaveBeenCalledWith('Deploy frontend');
  });

  test('disables submit when loading', () => {
    const onChange = jest.fn();
    const onSubmit = jest.fn();

    render(
      <CommandInput
        value="Deploy frontend"
        onChange={onChange}
        onSubmit={onSubmit}
        isLoading={true}
      />
    );

    const submitButton = screen.getByLabelText('Submit command');
    expect(submitButton).toBeDisabled();
  });
});

// ============================================================================
// ApprovalFlow Tests
// ============================================================================

describe('ApprovalFlow', () => {
  test('renders approval flow with risk assessment', () => {
    const onConfirm = jest.fn();
    const onCancel = jest.fn();

    render(
      <ApprovalFlow
        taskPlan={mockDecomposition}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    expect(screen.getByText('Approval Required')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });

  test('requires typed confirmation', async () => {
    const onConfirm = jest.fn();
    const onCancel = jest.fn();

    render(
      <ApprovalFlow
        taskPlan={mockDecomposition}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    const approveButton = screen.getByText('Approve & Execute');
    expect(approveButton).toBeDisabled();

    const input = screen.getByPlaceholderText(/Type confirmation phrase/i);
    await userEvent.type(input, 'APPROVE 12345');

    expect(approveButton).not.toBeDisabled();
  });

  test('calls onConfirm when confirmed', async () => {
    const onConfirm = jest.fn();
    const onCancel = jest.fn();

    render(
      <ApprovalFlow
        taskPlan={mockDecomposition}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    const input = screen.getByPlaceholderText(/Type confirmation phrase/i);
    await userEvent.type(input, 'APPROVE 12345');

    const approveButton = screen.getByText('Approve & Execute');
    await userEvent.click(approveButton);

    expect(onConfirm).toHaveBeenCalled();
  });

  test('calls onCancel when cancelled', async () => {
    const onConfirm = jest.fn();
    const onCancel = jest.fn();

    render(
      <ApprovalFlow
        taskPlan={mockDecomposition}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await userEvent.click(cancelButton);

    expect(onCancel).toHaveBeenCalled();
  });

  test('shows countdown timer', () => {
    const onConfirm = jest.fn();
    const onCancel = jest.fn();

    render(
      <ApprovalFlow
        taskPlan={mockDecomposition}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    expect(screen.getByText(/Expires in/i)).toBeInTheDocument();
  });
});

// ============================================================================
// AuditTrail Tests
// ============================================================================

describe('AuditTrail', () => {
  test('renders audit entries', () => {
    render(<AuditTrail entries={mockAuditEntries} />);

    expect(screen.getByText('Audit Trail')).toBeInTheDocument();
    expect(screen.getByText('Deploy frontend v2.0 to staging')).toBeInTheDocument();
  });

  test('filters entries by search', async () => {
    render(
      <AuditTrail
        entries={mockAuditEntries}
        showSearch={true}
      />
    );

    const searchInput = screen.getByPlaceholderText(/Search commands/i);
    await userEvent.type(searchInput, 'backend');

    // Should not show frontend entry
    expect(screen.queryByText('Deploy frontend v2.0 to staging')).not.toBeInTheDocument();
  });

  test('expands entry details', async () => {
    render(<AuditTrail entries={mockAuditEntries} />);

    const entry = screen.getByText('Deploy frontend v2.0 to staging');
    await userEvent.click(entry);

    // Check for expanded details
    await waitFor(() => {
      expect(screen.getByText(/Duration:/i)).toBeInTheDocument();
    });
  });

  test('shows empty state when no entries', () => {
    render(<AuditTrail entries={[]} />);

    expect(screen.getByText('No audit entries found')).toBeInTheDocument();
  });
});

// ============================================================================
// ErrorBoundary Tests
// ============================================================================

describe('ErrorBoundary', () => {
  // Suppress console.error for these tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = jest.fn();
  });
  afterAll(() => {
    console.error = originalError;
  });

  test('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Test Content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('catches errors and shows fallback', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  test('shows error ID', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Error ID:/i)).toBeInTheDocument();
  });

  test('allows retry', async () => {
    let shouldThrow = true;
    const TestComponent = () => {
      if (shouldThrow) throw new Error('Test error');
      return <div>Success</div>;
    };

    const { rerender } = render(
      <ErrorBoundary>
        <TestComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    shouldThrow = false;
    const retryButton = screen.getByText('Try Again');
    await userEvent.click(retryButton);

    rerender(
      <ErrorBoundary>
        <TestComponent />
      </ErrorBoundary>
    );

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
    });
  });
});

// ============================================================================
// useToast Tests
// ============================================================================

describe('useToast', () => {
  function ToastTestComponent() {
    const toast = useToast();

    return (
      <div>
        <button onClick={() => toast.success('Success', 'Test success')}>
          Success
        </button>
        <button onClick={() => toast.error('Error', 'Test error')}>
          Error
        </button>
        {toast.toasts.map(t => (
          <div key={t.id} data-testid={`toast-${t.type}`}>
            {t.title}
          </div>
        ))}
      </div>
    );
  }

  test('adds success toast', async () => {
    render(<ToastTestComponent />);

    const successButton = screen.getByText('Success');
    await userEvent.click(successButton);

    expect(screen.getByTestId('toast-success')).toBeInTheDocument();
    expect(screen.getByText('Success')).toBeInTheDocument();
  });

  test('adds error toast', async () => {
    render(<ToastTestComponent />);

    const errorButton = screen.getByText('Error');
    await userEvent.click(errorButton);

    expect(screen.getByTestId('toast-error')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });
});

// ============================================================================
// Keyboard Shortcuts Tests
// ============================================================================

describe('useKeyboardShortcuts', () => {
  test('triggers shortcut on key press', () => {
    const handler = jest.fn();
    const shortcuts = [
      {
        key: 'k',
        meta: true,
        description: 'Test shortcut',
        handler
      }
    ];

    function TestComponent() {
      useKeyboardShortcuts(shortcuts);
      return <div>Test</div>;
    }

    render(<TestComponent />);

    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    expect(handler).toHaveBeenCalled();
  });

  test('does not trigger when disabled', () => {
    const handler = jest.fn();
    const shortcuts = [
      {
        key: 'k',
        meta: true,
        description: 'Test shortcut',
        handler,
        enabled: false
      }
    ];

    function TestComponent() {
      useKeyboardShortcuts(shortcuts);
      return <div>Test</div>;
    }

    render(<TestComponent />);

    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    expect(handler).not.toHaveBeenCalled();
  });
});

// ============================================================================
// Integration Tests
// ============================================================================

describe('Dashboard Integration', () => {
  test('full workflow: command → decompose → approve', async () => {
    const onCommandSubmit = jest.fn();
    const onApprove = jest.fn();
    const onReject = jest.fn();

    render(
      <MainDashboard
        user={mockUser}
        onCommandSubmit={onCommandSubmit}
        onApprove={onApprove}
        onReject={onReject}
      />
    );

    // Type command
    const input = screen.getByPlaceholderText(/Enter command/i);
    await userEvent.type(input, 'Deploy frontend to staging');

    // Submit command
    const submitButton = screen.getByLabelText('Submit command');
    await userEvent.click(submitButton);

    expect(onCommandSubmit).toHaveBeenCalledWith('Deploy frontend to staging');
  });
});
