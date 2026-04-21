/**
 * Task Preview Component for PromptOps
 * =====================================
 *
 * Displays decomposed sub-tasks before execution with:
 * - Task list with dependencies
 * - Dependency graph visualization
 * - Execution timeline
 * - Risk indicators
 * - Approval workflow
 *
 * Shows users exactly what will happen before autonomous execution begins.
 *
 * Author: PromptOps Team - Week 5-6
 * Date: 2026-04-21
 */

import React, { useState } from 'react';
import './TaskPreview.css';

// ============================================================================
// Types
// ============================================================================

export interface SubTask {
  task_id: string;
  sequence: number;
  phase: string;
  action: string;
  target: string;
  parameters: Record<string, any>;
  dependencies: string[];
  can_run_parallel: boolean;
  estimated_duration: string;
  rollback_action: string | null;
  rollback_note?: string;
  validation_criteria: {
    expected_status: string;
    timeout: number;
  };
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  approval_required: boolean;
}

export interface ExecutionPhase {
  phase_number: number;
  phase_name: string;
  task_ids: string[];
  execution_mode: 'parallel' | 'sequential';
  estimated_duration: string;
}

export interface Decomposition {
  decomposition_id: string;
  timestamp: string;
  original_intent: {
    original_command: string;
    intent_type: string;
    target_service: string;
    target_env: string;
  };
  total_sub_tasks: number;
  estimated_duration: string;
  execution_strategy: string;
  sub_tasks: SubTask[];
  execution_plan: {
    phases: ExecutionPhase[];
    critical_path: string[];
    total_sequential_time: string;
    total_parallel_time: string;
  };
  rollback_plan?: {
    rollback_sequence: Array<{
      step: number;
      task_id: string;
      rollback_action: string | null;
    }>;
    estimated_rollback_duration: string;
    irreversible_tasks: string[];
  };
  risk_assessment?: {
    overall_risk: 'low' | 'medium' | 'high' | 'critical';
    risk_factors: Array<{
      factor: string;
      severity: string;
      mitigation: string;
    }>;
    requires_approval: boolean;
    blast_radius: string;
  };
}

export interface TaskPreviewProps {
  decomposition: Decomposition;
  onApprove: () => void;
  onReject: () => void;
  onModify?: () => void;
  showDependencyGraph?: boolean;
}

// ============================================================================
// Main Component
// ============================================================================

export const TaskPreview: React.FC<TaskPreviewProps> = ({
  decomposition,
  onApprove,
  onReject,
  onModify,
  showDependencyGraph = true
}) => {
  const [activeTab, setActiveTab] = useState<'tasks' | 'timeline' | 'graph' | 'rollback'>('tasks');
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  const toggleTask = (taskId: string) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedTasks(newExpanded);
  };

  const getRiskColor = (risk: string): string => {
    switch (risk) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const requiresApproval = decomposition.risk_assessment?.requires_approval ||
    decomposition.sub_tasks.some(t => t.approval_required);

  return (
    <div className="task-preview">
      {/* Header */}
      <div className="task-preview__header">
        <div className="task-preview__header-content">
          <h2 className="task-preview__title">Task Decomposition Preview</h2>
          <p className="task-preview__command">
            "{decomposition.original_intent.original_command}"
          </p>
        </div>

        <div className="task-preview__header-meta">
          <div className="task-preview__meta-item">
            <span className="task-preview__meta-label">Total Tasks:</span>
            <span className="task-preview__meta-value">{decomposition.total_sub_tasks}</span>
          </div>
          <div className="task-preview__meta-item">
            <span className="task-preview__meta-label">Duration:</span>
            <span className="task-preview__meta-value">{decomposition.estimated_duration}</span>
          </div>
          <div className="task-preview__meta-item">
            <span className="task-preview__meta-label">Risk:</span>
            <span
              className="task-preview__risk-badge"
              style={{ backgroundColor: getRiskColor(decomposition.risk_assessment?.overall_risk || 'medium') }}
            >
              {decomposition.risk_assessment?.overall_risk || 'medium'}
            </span>
          </div>
        </div>
      </div>

      {/* Risk Warning */}
      {requiresApproval && (
        <div className="task-preview__warning">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <strong>Manual Approval Required</strong>
            <p>This operation requires your approval before execution. Please review all tasks carefully.</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="task-preview__tabs">
        <button
          className={`task-preview__tab ${activeTab === 'tasks' ? 'task-preview__tab--active' : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          Tasks ({decomposition.total_sub_tasks})
        </button>
        <button
          className={`task-preview__tab ${activeTab === 'timeline' ? 'task-preview__tab--active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          Timeline
        </button>
        {showDependencyGraph && (
          <button
            className={`task-preview__tab ${activeTab === 'graph' ? 'task-preview__tab--active' : ''}`}
            onClick={() => setActiveTab('graph')}
          >
            Dependency Graph
          </button>
        )}
        <button
          className={`task-preview__tab ${activeTab === 'rollback' ? 'task-preview__tab--active' : ''}`}
          onClick={() => setActiveTab('rollback')}
        >
          Rollback Plan
        </button>
      </div>

      {/* Tab Content */}
      <div className="task-preview__content">
        {activeTab === 'tasks' && (
          <TaskList
            subTasks={decomposition.sub_tasks}
            expandedTasks={expandedTasks}
            onToggleTask={toggleTask}
            getRiskColor={getRiskColor}
          />
        )}

        {activeTab === 'timeline' && (
          <Timeline
            phases={decomposition.execution_plan.phases}
            subTasks={decomposition.sub_tasks}
            criticalPath={decomposition.execution_plan.critical_path}
          />
        )}

        {activeTab === 'graph' && showDependencyGraph && (
          <DependencyGraph
            subTasks={decomposition.sub_tasks}
            criticalPath={decomposition.execution_plan.critical_path}
          />
        )}

        {activeTab === 'rollback' && (
          <RollbackPlan
            rollbackPlan={decomposition.rollback_plan}
            subTasks={decomposition.sub_tasks}
          />
        )}
      </div>

      {/* Summary Stats */}
      <div className="task-preview__summary">
        <div className="task-preview__summary-item">
          <span className="task-preview__summary-label">Execution Strategy:</span>
          <span className="task-preview__summary-value">{decomposition.execution_strategy}</span>
        </div>
        <div className="task-preview__summary-item">
          <span className="task-preview__summary-label">Sequential Time:</span>
          <span className="task-preview__summary-value">{decomposition.execution_plan.total_sequential_time}</span>
        </div>
        <div className="task-preview__summary-item">
          <span className="task-preview__summary-label">Parallel Time:</span>
          <span className="task-preview__summary-value">{decomposition.execution_plan.total_parallel_time}</span>
        </div>
        <div className="task-preview__summary-item">
          <span className="task-preview__summary-label">Speedup:</span>
          <span className="task-preview__summary-value">
            {calculateSpeedup(
              decomposition.execution_plan.total_sequential_time,
              decomposition.execution_plan.total_parallel_time
            )}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="task-preview__actions">
        <button
          className="task-preview__button task-preview__button--reject"
          onClick={onReject}
        >
          Cancel
        </button>
        {onModify && (
          <button
            className="task-preview__button task-preview__button--modify"
            onClick={onModify}
          >
            Modify
          </button>
        )}
        <button
          className="task-preview__button task-preview__button--approve"
          onClick={onApprove}
        >
          {requiresApproval ? 'Approve & Execute' : 'Execute'}
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// Task List Component
// ============================================================================

const TaskList: React.FC<{
  subTasks: SubTask[];
  expandedTasks: Set<string>;
  onToggleTask: (taskId: string) => void;
  getRiskColor: (risk: string) => string;
}> = ({ subTasks, expandedTasks, onToggleTask, getRiskColor }) => {
  // Group by phase
  const tasksByPhase = subTasks.reduce((acc, task) => {
    if (!acc[task.phase]) acc[task.phase] = [];
    acc[task.phase].push(task);
    return acc;
  }, {} as Record<string, SubTask[]>);

  return (
    <div className="task-list">
      {Object.entries(tasksByPhase).map(([phase, tasks]) => (
        <div key={phase} className="task-list__phase">
          <h3 className="task-list__phase-title">
            {phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            <span className="task-list__phase-count">({tasks.length} tasks)</span>
          </h3>

          <div className="task-list__tasks">
            {tasks.map(task => (
              <div
                key={task.task_id}
                className={`task-card ${expandedTasks.has(task.task_id) ? 'task-card--expanded' : ''}`}
              >
                <div className="task-card__header" onClick={() => onToggleTask(task.task_id)}>
                  <div className="task-card__header-left">
                    <span className="task-card__id">{task.task_id}</span>
                    <span className="task-card__action">{task.action.replace(/_/g, ' ')}</span>
                    {task.can_run_parallel && (
                      <span className="task-card__parallel-badge">⚡ Parallel</span>
                    )}
                  </div>

                  <div className="task-card__header-right">
                    <span className="task-card__duration">{task.estimated_duration}</span>
                    <span
                      className="task-card__risk"
                      style={{ backgroundColor: getRiskColor(task.risk_level) }}
                    >
                      {task.risk_level}
                    </span>
                    <svg
                      className="task-card__expand-icon"
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="currentColor"
                    >
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L8 6.586l2.293-2.293a1 1 0 111.414 1.414L9.414 8l2.293 2.293a1 1 0 01-1.414 1.414L8 9.414l-2.293 2.293a1 1 0 01-1.414-1.414L6.586 8 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>

                {expandedTasks.has(task.task_id) && (
                  <div className="task-card__details">
                    <div className="task-card__detail-row">
                      <span className="task-card__label">Target:</span>
                      <span className="task-card__value">{task.target}</span>
                    </div>

                    {task.dependencies.length > 0 && (
                      <div className="task-card__detail-row">
                        <span className="task-card__label">Dependencies:</span>
                        <span className="task-card__value">{task.dependencies.join(', ')}</span>
                      </div>
                    )}

                    {Object.keys(task.parameters).length > 0 && (
                      <div className="task-card__detail-row">
                        <span className="task-card__label">Parameters:</span>
                        <code className="task-card__code">
                          {JSON.stringify(task.parameters, null, 2)}
                        </code>
                      </div>
                    )}

                    <div className="task-card__detail-row">
                      <span className="task-card__label">Validation:</span>
                      <span className="task-card__value">
                        {task.validation_criteria.expected_status}
                        (timeout: {task.validation_criteria.timeout}s)
                      </span>
                    </div>

                    {task.rollback_action && (
                      <div className="task-card__detail-row">
                        <span className="task-card__label">Rollback:</span>
                        <span className="task-card__value task-card__value--rollback">
                          {task.rollback_action}
                        </span>
                      </div>
                    )}

                    {!task.rollback_action && task.rollback_note && (
                      <div className="task-card__detail-row task-card__detail-row--warning">
                        <span className="task-card__label">⚠️ Irreversible:</span>
                        <span className="task-card__value">{task.rollback_note}</span>
                      </div>
                    )}

                    {task.approval_required && (
                      <div className="task-card__approval-badge">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                          <path d="M8 1a2 2 0 012 2v1h1a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2h1V3a2 2 0 012-2zm0 5a1 1 0 100 2 1 1 0 000-2z"/>
                        </svg>
                        Manual Approval Required
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// ============================================================================
// Timeline Component
// ============================================================================

const Timeline: React.FC<{
  phases: ExecutionPhase[];
  subTasks: SubTask[];
  criticalPath: string[];
}> = ({ phases, subTasks, criticalPath }) => {
  const taskMap = subTasks.reduce((acc, task) => {
    acc[task.task_id] = task;
    return acc;
  }, {} as Record<string, SubTask>);

  return (
    <div className="timeline">
      <div className="timeline__header">
        <h3>Execution Timeline</h3>
        <p>Tasks grouped by execution phase. Parallel tasks run concurrently.</p>
      </div>

      <div className="timeline__phases">
        {phases.map((phase, index) => (
          <div key={phase.phase_number} className="timeline__phase">
            <div className="timeline__phase-header">
              <div className="timeline__phase-number">{phase.phase_number}</div>
              <div className="timeline__phase-info">
                <h4 className="timeline__phase-name">{phase.phase_name}</h4>
                <div className="timeline__phase-meta">
                  <span className="timeline__phase-mode">
                    {phase.execution_mode === 'parallel' ? '⚡ Parallel' : '→ Sequential'}
                  </span>
                  <span className="timeline__phase-duration">{phase.estimated_duration}</span>
                  <span className="timeline__phase-tasks">{phase.task_ids.length} tasks</span>
                </div>
              </div>
            </div>

            <div className={`timeline__phase-tasks ${phase.execution_mode === 'parallel' ? 'timeline__phase-tasks--parallel' : ''}`}>
              {phase.task_ids.map(taskId => {
                const task = taskMap[taskId];
                const isOnCriticalPath = criticalPath.includes(taskId);

                return (
                  <div
                    key={taskId}
                    className={`timeline__task ${isOnCriticalPath ? 'timeline__task--critical' : ''}`}
                  >
                    <div className="timeline__task-id">{taskId}</div>
                    <div className="timeline__task-action">{task.action.replace(/_/g, ' ')}</div>
                    <div className="timeline__task-duration">{task.estimated_duration}</div>
                  </div>
                );
              })}
            </div>

            {index < phases.length - 1 && (
              <div className="timeline__phase-arrow">↓</div>
            )}
          </div>
        ))}
      </div>

      <div className="timeline__legend">
        <div className="timeline__legend-item">
          <div className="timeline__legend-box timeline__legend-box--critical"></div>
          <span>Critical Path</span>
        </div>
        <div className="timeline__legend-item">
          <div className="timeline__legend-box timeline__legend-box--normal"></div>
          <span>Normal Task</span>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Dependency Graph Component
// ============================================================================

const DependencyGraph: React.FC<{
  subTasks: SubTask[];
  criticalPath: string[];
}> = ({ subTasks, criticalPath }) => {
  return (
    <div className="dependency-graph">
      <div className="dependency-graph__header">
        <h3>Dependency Graph</h3>
        <p>Visual representation of task dependencies. Critical path highlighted in orange.</p>
      </div>

      <div className="dependency-graph__content">
        <svg className="dependency-graph__svg" viewBox="0 0 800 600">
          {/* Simplified graph visualization - in production, use a library like react-flow or d3 */}
          <text x="400" y="300" textAnchor="middle" fill="#6b7280" fontSize="14">
            Graph visualization placeholder
          </text>
          <text x="400" y="320" textAnchor="middle" fill="#9ca3af" fontSize="12">
            (Use react-flow or d3 for production implementation)
          </text>
        </svg>
      </div>

      <div className="dependency-graph__stats">
        <div className="dependency-graph__stat">
          <span className="dependency-graph__stat-label">Total Tasks:</span>
          <span className="dependency-graph__stat-value">{subTasks.length}</span>
        </div>
        <div className="dependency-graph__stat">
          <span className="dependency-graph__stat-label">Critical Path Length:</span>
          <span className="dependency-graph__stat-value">{criticalPath.length}</span>
        </div>
        <div className="dependency-graph__stat">
          <span className="dependency-graph__stat-label">Parallelizable Tasks:</span>
          <span className="dependency-graph__stat-value">
            {subTasks.filter(t => t.can_run_parallel).length}
          </span>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Rollback Plan Component
// ============================================================================

const RollbackPlan: React.FC<{
  rollbackPlan?: Decomposition['rollback_plan'];
  subTasks: SubTask[];
}> = ({ rollbackPlan, subTasks }) => {
  if (!rollbackPlan) {
    return (
      <div className="rollback-plan rollback-plan--empty">
        <p>No rollback plan available</p>
      </div>
    );
  }

  const taskMap = subTasks.reduce((acc, task) => {
    acc[task.task_id] = task;
    return acc;
  }, {} as Record<string, SubTask>);

  return (
    <div className="rollback-plan">
      <div className="rollback-plan__header">
        <h3>Rollback Plan</h3>
        <p>Tasks will be rolled back in reverse order if execution fails.</p>
        <div className="rollback-plan__duration">
          Estimated rollback time: {rollbackPlan.estimated_rollback_duration}
        </div>
      </div>

      <div className="rollback-plan__sequence">
        {rollbackPlan.rollback_sequence.map((item, index) => {
          const task = taskMap[item.task_id];

          return (
            <div key={item.task_id} className="rollback-plan__step">
              <div className="rollback-plan__step-number">{item.step}</div>
              <div className="rollback-plan__step-content">
                <div className="rollback-plan__step-header">
                  <span className="rollback-plan__task-id">{item.task_id}</span>
                  <span className="rollback-plan__task-action">{task.action.replace(/_/g, ' ')}</span>
                </div>
                <div className="rollback-plan__step-rollback">
                  {item.rollback_action || (
                    <span className="rollback-plan__irreversible">
                      ⚠️ Irreversible - cannot be rolled back
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {rollbackPlan.irreversible_tasks.length > 0 && (
        <div className="rollback-plan__warning">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <strong>Irreversible Tasks:</strong>
            <p>{rollbackPlan.irreversible_tasks.join(', ')}</p>
            <p>These tasks cannot be automatically rolled back and may require manual intervention.</p>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Utility Functions
// ============================================================================

function calculateSpeedup(sequential: string, parallel: string): string {
  const parseTime = (timeStr: string): number => {
    const parts = timeStr.toLowerCase().split(' ');
    let totalSeconds = 0;

    for (let i = 0; i < parts.length; i += 2) {
      const value = parseInt(parts[i]);
      const unit = parts[i + 1];

      if (unit.includes('hour')) totalSeconds += value * 3600;
      else if (unit.includes('minute')) totalSeconds += value * 60;
      else if (unit.includes('second')) totalSeconds += value;
    }

    return totalSeconds;
  };

  const seqSeconds = parseTime(sequential);
  const parSeconds = parseTime(parallel);

  if (parSeconds === 0) return '1.0x';

  const speedup = seqSeconds / parSeconds;
  return `${speedup.toFixed(1)}x`;
}

// ============================================================================
// Example Usage
// ============================================================================

export const TaskPreviewExample: React.FC = () => {
  const exampleDecomposition: Decomposition = {
    decomposition_id: 'decomp-2026-05-05-abc123',
    timestamp: '2026-05-05T14:30:00Z',
    original_intent: {
      original_command: 'Deploy API v2.1.0 to production with canary rollout',
      intent_type: 'deploy',
      target_service: 'api',
      target_env: 'production'
    },
    total_sub_tasks: 12,
    estimated_duration: '8-10 minutes',
    execution_strategy: 'sequential_with_parallel_phases',
    sub_tasks: [
      // Example tasks (simplified)
      {
        task_id: 'task-001',
        sequence: 1,
        phase: 'pre_validation',
        action: 'validate_version_exists',
        target: 'docker_registry',
        parameters: { version: 'v2.1.0' },
        dependencies: [],
        can_run_parallel: true,
        estimated_duration: '10 seconds',
        rollback_action: null,
        validation_criteria: {
          expected_status: 'image_found',
          timeout: 30
        },
        risk_level: 'low',
        approval_required: false
      }
      // ... more tasks
    ],
    execution_plan: {
      phases: [
        {
          phase_number: 1,
          phase_name: 'Pre-validation',
          task_ids: ['task-001', 'task-002'],
          execution_mode: 'parallel',
          estimated_duration: '15 seconds'
        }
      ],
      critical_path: ['task-001', 'task-003', 'task-005'],
      total_sequential_time: '12 minutes',
      total_parallel_time: '8 minutes'
    },
    risk_assessment: {
      overall_risk: 'high',
      risk_factors: [
        {
          factor: 'Production deployment',
          severity: 'high',
          mitigation: 'Canary rollout with monitoring'
        }
      ],
      requires_approval: true,
      blast_radius: 'single_service'
    }
  };

  return (
    <TaskPreview
      decomposition={exampleDecomposition}
      onApprove={() => console.log('Approved')}
      onReject={() => console.log('Rejected')}
      onModify={() => console.log('Modify')}
    />
  );
};

export default TaskPreview;
