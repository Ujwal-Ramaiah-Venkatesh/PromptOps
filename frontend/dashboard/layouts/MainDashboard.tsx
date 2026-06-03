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

interface AwsDeployStep {
  step: string;
  title: string;
  detail: any;
  status: string;
}

interface AwsDeployResponse {
  app_name: string;
  bucket: string;
  region: string;
  website_url: string;
  files_uploaded: number;
  status: string;
  steps: AwsDeployStep[];
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
  const [success, setSuccess] = useState<string | null>(null);

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

  const isJewelryVaultAwsDeploy = (command: string): boolean => {
    const normalized = command.toLowerCase();
    return (
      normalized.includes('deploy') &&
      (normalized.includes('jewelry') || normalized.includes('vault')) &&
      (normalized.includes('aws') || normalized.includes('s3') || normalized.includes('cloudfront'))
    );
  };

  const buildDecompositionFromAwsDeploy = (command: string, intent: ParsedIntent, deploy: AwsDeployResponse): Decomposition => {
    const mappedTasks = deploy.steps.map((s, idx) => ({
      task_id: s.step,
      sequence: idx + 1,
      phase: 'deployment',
      action: s.title,
      target: deploy.bucket,
      parameters: {
        detail: s.detail,
        status: s.status,
      },
      dependencies: idx === 0 ? [] : [deploy.steps[idx - 1].step],
      can_run_parallel: false,
      estimated_duration: '5s',
      rollback_action: null,
      rollback_note: 'Manual rollback from AWS Console if needed',
      validation_criteria: {
        expected_status: 'done',
        timeout: 60,
      },
      risk_level: 'low' as const,
      approval_required: false,
    }));

    return {
      decomposition_id: `aws-deploy-${Date.now()}`,
      timestamp: new Date().toISOString(),
      original_intent: {
        original_command: command,
        intent_type: intent.intent_type,
        target_service: intent.target_service,
        target_env: intent.target_env || 'production',
      },
      total_sub_tasks: mappedTasks.length,
      estimated_duration: `${mappedTasks.length * 5}s`,
      execution_strategy: 'sequential',
      sub_tasks: mappedTasks,
      execution_plan: {
        phases: [
          {
            phase_number: 1,
            phase_name: 'AWS S3 Deployment',
            task_ids: mappedTasks.map((t: any) => t.task_id),
            execution_mode: 'sequential',
            estimated_duration: `${mappedTasks.length * 5}s`,
          },
        ],
        critical_path: mappedTasks.map((t: any) => t.task_id),
        total_sequential_time: `${mappedTasks.length * 5}s`,
        total_parallel_time: `${mappedTasks.length * 5}s`,
      },
      rollback_plan: {
        rollback_sequence: mappedTasks
          .slice()
          .reverse()
          .map((task: any, i: number) => ({
            step: i + 1,
            task_id: task.task_id,
            rollback_action: null,
          })),
        estimated_rollback_duration: '2m',
        irreversible_tasks: [],
      },
      risk_assessment: {
        overall_risk: 'low',
        risk_factors: [],
        estimated_cost_impact: 0,
        affected_users: 0,
        requires_approval: false,
        approval_level: 'none',
      },
    };
  };

  const deployJewelryVaultToAws = async (command: string, intent: ParsedIntent): Promise<void> => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/deploy/aws', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_name: 'jewelry-vault',
          source_path: 'C:\\Users\\pqm847\\Documents\\jewelry-vault',
          bucket_name: 'jewelry-vault-promptops-821589437061-20260523',
          region: 'us-east-1',
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Deployment failed with HTTP ${response.status}`);
      }

      const deployResult = data as AwsDeployResponse;
      const decomp = buildDecompositionFromAwsDeploy(command, intent, deployResult);
      setDecomposition(decomp);
      setSuccess(`Deployment completed. Public URL: ${deployResult.website_url}`);
    } catch (err: any) {
      setError(err.message || 'Failed to deploy jewelry-vault to AWS');
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

    setSuccess(null);

    // Step 1: Parse command
    const intent = await parseCommand(command);
    if (!intent) return;

    setParsedIntent(intent);

    // Step 2: Decompose
    const decomp = await decomposeTask(intent);
    if (!decomp) return;

    if (isJewelryVaultAwsDeploy(command)) {
      await deployJewelryVaultToAws(command, intent);
    } else {
      setDecomposition(decomp);
    }

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

      {/* Success Banner */}
      {success && (
        <div className="dashboard-error" style={{ background: '#f0fff4', borderColor: '#68d391' }}>
          <span className="error-icon">✅</span>
          <span className="error-message" style={{ color: '#22543d' }}>{success}</span>
          <button className="error-dismiss" onClick={() => setSuccess(null)}>×</button>
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
