/**
 * Approval Flow Component
 * ========================
 *
 * Approval flow with typed confirmation for high-risk operations.
 *
 * Features:
 * - Risk assessment display
 * - Typed confirmation (must type exact phrase)
 * - Impact summary (before/after comparison)
 * - Rollback plan preview
 * - 5-minute timeout with countdown
 * - Auto-cancel on timeout
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import React, { useState, useEffect, useCallback } from 'react';
import './ApprovalFlow.css';

// ============================================================================
// Type Definitions
// ============================================================================

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  estimated_cost_impact: number;
  affected_users: number;
  requires_approval: boolean;
  approval_level: string;
}

export interface TaskPlan {
  decomposition_id: string;
  operation_id?: string;
  timestamp: string;
  total_sub_tasks: number;
  estimated_duration: number;
  risk_assessment: RiskAssessment;
  original_intent: any;
  sub_tasks?: Array<any>;
  rollback_plan?: any;
  current_state?: any;
  target_state?: any;
}

export interface ApprovalFlowProps {
  taskPlan: TaskPlan;
  onConfirm: () => void;
  onCancel: () => void;
  timeoutMinutes?: number;
}

// ============================================================================
// Approval Flow Component
// ============================================================================

export function ApprovalFlow({
  taskPlan,
  onConfirm,
  onCancel,
  timeoutMinutes = 5
}: ApprovalFlowProps): JSX.Element {
  const [confirmationText, setConfirmationText] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(timeoutMinutes * 60);
  const [showDetails, setShowDetails] = useState(false);

  const operationId = taskPlan.operation_id || taskPlan.decomposition_id.split('-')[1];
  const requiredPhrase = `APPROVE ${operationId}`;
  const isConfirmed = confirmationText.trim().toUpperCase() === requiredPhrase;

  // Countdown timer
  useEffect(() => {
    if (timeRemaining <= 0) {
      onCancel();
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          onCancel();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining, onCancel]);

  // Format time remaining
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get urgency level based on time remaining
  const getUrgencyLevel = (): 'normal' | 'warning' | 'critical' => {
    if (timeRemaining <= 30) return 'critical';
    if (timeRemaining <= 60) return 'warning';
    return 'normal';
  };

  const urgency = getUrgencyLevel();

  return (
    <div className={`approval-flow approval-flow--${taskPlan.risk_assessment.overall_risk}`}>
      {/* Header */}
      <div className="approval-flow-header">
        <div className="approval-flow-title">
          <span className="approval-icon">🔒</span>
          <h3>Approval Required</h3>
        </div>
        <div className={`approval-timer approval-timer--${urgency}`}>
          <span className="timer-icon">⏱️</span>
          <span className="timer-text">Expires in {formatTime(timeRemaining)}</span>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="approval-section">
        <RiskAssessmentDisplay risk={taskPlan.risk_assessment} />
      </div>

      {/* Impact Summary */}
      <div className="approval-section">
        <ImpactSummary
          intent={taskPlan.original_intent}
          taskCount={taskPlan.total_sub_tasks}
          duration={taskPlan.estimated_duration}
          currentState={taskPlan.current_state}
          targetState={taskPlan.target_state}
        />
      </div>

      {/* Rollback Plan (collapsible) */}
      {taskPlan.rollback_plan && (
        <div className="approval-section">
          <button
            className="approval-section-toggle"
            onClick={() => setShowDetails(!showDetails)}
          >
            <span>Rollback Plan</span>
            <span className={`toggle-icon ${showDetails ? 'toggle-icon--open' : ''}`}>
              ▼
            </span>
          </button>
          {showDetails && (
            <RollbackPlanPreview plan={taskPlan.rollback_plan} />
          )}
        </div>
      )}

      {/* Confirmation Input */}
      <div className="approval-confirmation">
        <label className="confirmation-label">
          Type <code className="confirmation-code">{requiredPhrase}</code> to confirm:
        </label>
        <input
          type="text"
          className={`confirmation-input ${isConfirmed ? 'confirmation-input--valid' : ''}`}
          value={confirmationText}
          onChange={(e) => setConfirmationText(e.target.value)}
          placeholder="Type confirmation phrase..."
          autoComplete="off"
          autoFocus
        />
        {isConfirmed && (
          <div className="confirmation-valid">
            ✓ Confirmation phrase correct
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="approval-actions">
        <button
          className="approval-button approval-button--cancel"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          className="approval-button approval-button--approve"
          onClick={onConfirm}
          disabled={!isConfirmed}
        >
          Approve & Execute
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Risk Assessment Display
// ============================================================================

interface RiskAssessmentDisplayProps {
  risk: RiskAssessment;
}

function RiskAssessmentDisplay({ risk }: RiskAssessmentDisplayProps): JSX.Element {
  const riskIcons = {
    low: '🟢',
    medium: '🟡',
    high: '🟠',
    critical: '🔴'
  };

  return (
    <div className="risk-assessment">
      <div className="risk-header">
        <span className="risk-icon">{riskIcons[risk.overall_risk]}</span>
        <h4>Risk Assessment</h4>
        <span className={`risk-badge risk-badge--${risk.overall_risk}`}>
          {risk.overall_risk.toUpperCase()}
        </span>
      </div>

      {risk.risk_factors.length > 0 && (
        <div className="risk-factors">
          <p className="risk-factors-title">⚠️ This operation will:</p>
          <ul className="risk-factors-list">
            {risk.risk_factors.map((factor, index) => (
              <li key={index}>{factor}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="risk-metrics">
        {risk.estimated_cost_impact > 0 && (
          <div className="risk-metric">
            <span className="metric-label">Cost Impact:</span>
            <span className="metric-value">
              ${risk.estimated_cost_impact}/month
            </span>
          </div>
        )}
        {risk.affected_users > 0 && (
          <div className="risk-metric">
            <span className="metric-label">Affected Users:</span>
            <span className="metric-value">{risk.affected_users.toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Impact Summary
// ============================================================================

interface ImpactSummaryProps {
  intent: any;
  taskCount: number;
  duration: number;
  currentState?: any;
  targetState?: any;
}

function ImpactSummary({
  intent,
  taskCount,
  duration,
  currentState,
  targetState
}: ImpactSummaryProps): JSX.Element {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    if (mins < 60) return `${mins} minute${mins !== 1 ? 's' : ''}`;
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}h ${remainingMins}m`;
  };

  return (
    <div className="impact-summary">
      <h4>Impact Summary</h4>

      <div className="impact-details">
        <div className="impact-row">
          <span className="impact-label">Operation:</span>
          <span className="impact-value">
            {intent.intent_type} {intent.target_service}
          </span>
        </div>

        <div className="impact-row">
          <span className="impact-label">Environment:</span>
          <span className={`impact-value impact-value--env impact-value--env-${intent.target_env}`}>
            {intent.target_env || 'N/A'}
          </span>
        </div>

        <div className="impact-row">
          <span className="impact-label">Sub-tasks:</span>
          <span className="impact-value">{taskCount} tasks</span>
        </div>

        <div className="impact-row">
          <span className="impact-label">Estimated Time:</span>
          <span className="impact-value">{formatDuration(duration)}</span>
        </div>
      </div>

      {/* Before/After comparison */}
      {currentState && targetState && (
        <div className="state-comparison">
          <div className="state-column">
            <div className="state-header">Before</div>
            <StateDisplay state={currentState} />
          </div>
          <div className="state-arrow">→</div>
          <div className="state-column">
            <div className="state-header">After</div>
            <StateDisplay state={targetState} />
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// State Display
// ============================================================================

interface StateDisplayProps {
  state: any;
}

function StateDisplay({ state }: StateDisplayProps): JSX.Element {
  return (
    <div className="state-display">
      {Object.entries(state).slice(0, 5).map(([key, value]) => (
        <div key={key} className="state-field">
          <span className="state-key">{key}:</span>
          <span className="state-value">{String(value)}</span>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// Rollback Plan Preview
// ============================================================================

interface RollbackPlanPreviewProps {
  plan: any;
}

function RollbackPlanPreview({ plan }: RollbackPlanPreviewProps): JSX.Element {
  const duration = plan.estimated_duration || 180;
  const steps = plan.total_steps || plan.sequence?.length || 0;
  const irreversible = plan.irreversible_tasks || [];

  return (
    <div className="rollback-preview">
      <div className="rollback-info">
        <div className="rollback-metric">
          <span className="rollback-metric-label">Steps:</span>
          <span className="rollback-metric-value">{steps}</span>
        </div>
        <div className="rollback-metric">
          <span className="rollback-metric-label">Time:</span>
          <span className="rollback-metric-value">
            ~{Math.floor(duration / 60)} min
          </span>
        </div>
      </div>

      {irreversible.length > 0 && (
        <div className="rollback-warning">
          <span className="warning-icon">⚠️</span>
          <div className="warning-content">
            <strong>Irreversible Actions:</strong>
            <ul>
              {irreversible.map((task: string, index: number) => (
                <li key={index}>{task}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="rollback-status">
        {irreversible.length === 0 ? (
          <span className="rollback-status--available">
            ✓ Full rollback available
          </span>
        ) : (
          <span className="rollback-status--partial">
            ⚠ Partial rollback only
          </span>
        )}
      </div>
    </div>
  );
}

export default ApprovalFlow;
