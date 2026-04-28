/**
 * Main Dashboard Layout
 * =====================
 *
 * Primary interface for PMs to issue commands, review task plans,
 * approve operations, and view audit history.
 *
 * Layout Structure:
 * - Top Bar: Command Input + Drift Alert
 * - Center Panel: Task Preview (largest area)
 * - Bottom Left: Approval Flow (when needed)
 * - Bottom Right: Audit Trail
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import React, { useState, useEffect, useCallback } from 'react';
import CommandInput from '../components/CommandInput';
import { TaskPreview } from '../../components/TaskPreview';
import { DriftAlert } from '../../components/DriftAlert';
import ApprovalFlow from '../components/ApprovalFlow';
import AuditTrail from '../components/AuditTrail';
import './MainDashboard.css';

// ============================================================================
// Type Definitions
// ============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'pm' | 'admin' | 'viewer';
}

export interface ParsedIntent {
  intent_type: string;
  target_service: string;
  target_env?: string;
  parameters: Record<string, any>;
  confidence: number;
  ambiguity_score: number;
  missing_params: string[];
  requires_approval: boolean;
}

export interface Decomposition {
  decomposition_id: string;
  timestamp: string;
  original_intent: ParsedIntent;
  total_sub_tasks: number;
  estimated_duration: number;
  execution_strategy: string;
  sub_tasks: Array<any>;
  execution_plan: any;
  rollback_plan: any;
  risk_assessment: RiskAssessment;
}

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  estimated_cost_impact: number;
  affected_users: number;
  requires_approval: boolean;
  approval_level: string;
}

export interface DriftEvent {
  drift_id: string;
  resource_id: string;
  resource_type: string;
  field_changed: string;
  old_value: any;
  new_value: any;
  severity: 'critical' | 'warning' | 'info';
  detected_at: string;
  change_source: string;
  changed_by?: string;
  reason?: string;
}

export interface AuditEntry {
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

export interface MainDashboardProps {
  user: User;
  onCommandSubmit?: (command: string) => void;
  onApprove?: (decomposition: Decomposition) => void;
  onReject?: (reason: string) => void;
}

// ============================================================================
// Main Dashboard Component
// ============================================================================

export function MainDashboard({ user, onCommandSubmit, onApprove, onReject }: MainDashboardProps): JSX.Element {
  // State management
  const [currentCommand, setCurrentCommand] = useState<string>('');
  const [parsedIntent, setParsedIntent] = useState<ParsedIntent | null>(null);
  const [decomposition, setDecomposition] = useState<Decomposition | null>(null);
  const [showApproval, setShowApproval] = useState<boolean>(false);
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch drift events on mount
  useEffect(() => {
    fetchDriftEvents();

    // Poll for drift every 60 seconds
    const interval = setInterval(fetchDriftEvents, 60000);
    return () => clearInterval(interval);
  }, []);

  // ========================================================================
  // API Functions
  // ========================================================================

  const fetchDriftEvents = async () => {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/drift/current');
      // const data = await response.json();
      // setDriftEvents(data.drift_events);

      // Mock data for now
      console.log('Fetching drift events...');
    } catch (err) {
      console.error('Failed to fetch drift events:', err);
    }
  };

  const parseCommand = async (command: string): Promise<ParsedIntent | null> => {
    try {
      setIsLoading(true);
      setError(null);

      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/parse', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ command })
      // });
      // const data = await response.json();
      // return data.intent;

      // Mock parsing for now
      return {
        intent_type: 'deploy',
        target_service: 'frontend',
        target_env: 'staging',
        parameters: { version: 'v2.0' },
        confidence: 0.92,
        ambiguity_score: 0.15,
        missing_params: [],
        requires_approval: false
      };
    } catch (err) {
      setError('Failed to parse command');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const decomposeTask = async (intent: ParsedIntent): Promise<Decomposition | null> => {
    try {
      setIsLoading(true);
      setError(null);

      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/decompose', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ intent })
      // });
      // const data = await response.json();
      // return data.decomposition;

      // Mock decomposition for now
      return {
        decomposition_id: 'decomp-001',
        timestamp: new Date().toISOString(),
        original_intent: intent,
        total_sub_tasks: 8,
        estimated_duration: 240,
        execution_strategy: 'sequential_with_gates',
        sub_tasks: [],
        execution_plan: { phases: [] },
        rollback_plan: {},
        risk_assessment: {
          overall_risk: 'low',
          risk_factors: [],
          estimated_cost_impact: 50,
          affected_users: 100,
          requires_approval: false,
          approval_level: 'none'
        }
      };
    } catch (err) {
      setError('Failed to decompose task');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // ========================================================================
  // Event Handlers
  // ========================================================================

  const handleCommandChange = useCallback((value: string) => {
    setCurrentCommand(value);
  }, []);

  const handleCommandSubmit = async (command: string) => {
    if (!command.trim()) return;

    // Step 1: Parse command
    const intent = await parseCommand(command);
    if (!intent) return;

    setParsedIntent(intent);

    // Step 2: Decompose
    const decomp = await decomposeTask(intent);
    if (!decomp) return;

    setDecomposition(decomp);

    // Step 3: Check if approval needed
    if (decomp.risk_assessment.requires_approval) {
      setShowApproval(true);
    }

    // Callback
    if (onCommandSubmit) {
      onCommandSubmit(command);
    }
  };

  const handleApprove = () => {
    if (!decomposition) return;

    setShowApproval(false);

    // Execute task
    if (onApprove) {
      onApprove(decomposition);
    }

    // Reset for next command
    setCurrentCommand('');
    setParsedIntent(null);
    setDecomposition(null);
  };

  const handleReject = (reason: string) => {
    setShowApproval(false);
    setDecomposition(null);
    setParsedIntent(null);

    if (onReject) {
      onReject(reason);
    }
  };

  const handleApprovalCancel = () => {
    setShowApproval(false);
  };

  const handleAcceptDrift = (resourceId: string, driftId: string) => {
    console.log('Accept drift:', resourceId, driftId);
    // TODO: API call to accept drift
    setDriftEvents(prev => prev.filter(e => e.drift_id !== driftId));
  };

  const handleRevertDrift = (resourceId: string, driftId: string) => {
    console.log('Revert drift:', resourceId, driftId);
    // TODO: API call to revert drift
  };

  const handleDriftDismiss = () => {
    console.log('Drift dismissed');
  };

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <div className="main-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-branding">
          <h1>PromptOps</h1>
          <span className="dashboard-subtitle">Infrastructure Control Plane</span>
        </div>

        <div className="dashboard-user">
          <span className="user-name">{user.name}</span>
          <span className="user-role">{user.role}</span>
        </div>
      </header>

      {/* Top Bar */}
      <div className="dashboard-top-bar">
        <div className="command-section">
          <CommandInput
            value={currentCommand}
            onChange={handleCommandChange}
            onSubmit={handleCommandSubmit}
            parsedIntent={parsedIntent}
            isLoading={isLoading}
          />
        </div>

        {driftEvents.length > 0 && (
          <div className="drift-section">
            <DriftAlert
              driftEvents={driftEvents}
              onAcceptDrift={handleAcceptDrift}
              onRevertDrift={handleRevertDrift}
              onDismiss={handleDriftDismiss}
            />
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="dashboard-error">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{error}</span>
          <button className="error-dismiss" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Main Content */}
      <main className="dashboard-main">
        {decomposition ? (
          <div className="task-preview-section">
            <TaskPreview
              decomposition={decomposition}
              onApprove={handleApprove}
              onReject={() => handleReject('User rejected')}
            />
          </div>
        ) : (
          <div className="dashboard-empty-state">
            <div className="empty-state-icon">💬</div>
            <h2>Ready to Execute</h2>
            <p>Enter a command above to get started</p>
            <div className="empty-state-examples">
              <h3>Example Commands:</h3>
              <ul>
                <li>Deploy frontend v2.0 to staging</li>
                <li>Scale backend to 10 instances</li>
                <li>Rollback API to previous version</li>
                <li>Show me current AWS spending</li>
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="dashboard-footer">
        {/* Approval Flow (conditional) */}
        {showApproval && decomposition && (
          <div className="approval-section">
            <ApprovalFlow
              taskPlan={decomposition}
              onConfirm={handleApprove}
              onCancel={handleApprovalCancel}
              timeoutMinutes={5}
            />
          </div>
        )}

        {/* Audit Trail */}
        <div className="audit-section">
          <AuditTrail
            limit={10}
            onViewAll={() => console.log('View all audit logs')}
          />
        </div>
      </footer>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="dashboard-loading-overlay">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Processing command...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default MainDashboard;
