/**
 * Dashboard State Management Hook
 * =================================
 *
 * Central state management for the PM Dashboard with API integration.
 *
 * Features:
 * - Command submission and parsing
 * - Task decomposition
 * - Approval workflow
 * - Audit trail
 * - Drift monitoring
 * - Error handling
 * - Loading states
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient, { handleAPIError } from '../utils/api';

// ============================================================================
// Type Definitions
// ============================================================================

export interface ParsedIntent {
  intent_type: string;
  target_service: string;
  target_env?: string;
  parameters: Record<string, any>;
  confidence: number;
  ambiguity_score: number;
  missing_params: string[];
  requires_approval: boolean;
  warnings?: string[];
}

export interface Decomposition {
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

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: string[];
  estimated_cost_impact: number;
  affected_users: number;
  requires_approval: boolean;
  approval_level: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  command: string;
  intent_type: string;
  target_service: string;
  target_env: string;
  status: 'pending' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed' | 'rolled_back';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  duration?: number;
  error_message?: string;
  task_plan?: any;
  execution_log?: string[];
}

export interface DriftEvent {
  id: string;
  timestamp: string;
  resource_type: string;
  resource_id: string;
  field: string;
  expected_value: any;
  actual_value: any;
  severity: 'critical' | 'warning' | 'info';
  auto_fixable: boolean;
}

export interface DashboardState {
  // Command & Intent
  currentCommand: string;
  parsedIntent: ParsedIntent | null;
  isParsingIntent: boolean;

  // Decomposition
  decomposition: Decomposition | null;
  isDecomposing: boolean;

  // Approval
  showApproval: boolean;
  isExecuting: boolean;

  // Audit Trail
  auditEntries: AuditEntry[];
  isLoadingAudit: boolean;

  // Drift Monitoring
  driftEvents: DriftEvent[];
  unacknowledgedDriftCount: number;
  isLoadingDrift: boolean;

  // Error Handling
  error: string | null;
  lastSuccessfulCommand: string | null;
}

export interface DashboardActions {
  // Command actions
  setCommand: (command: string) => void;
  submitCommand: () => Promise<void>;
  clearCommand: () => void;

  // Approval actions
  approveTask: () => Promise<void>;
  rejectTask: (reason: string) => Promise<void>;

  // Drift actions
  acknowledgeDrift: (driftId: string) => Promise<void>;
  revertDrift: (driftId: string) => Promise<void>;

  // Audit actions
  refreshAudit: () => Promise<void>;
  exportAudit: (format: 'csv' | 'json') => Promise<void>;

  // Error handling
  clearError: () => void;
}

export interface UseDashboardStateOptions {
  user: string;
  apiBaseUrl?: string;
  pollingInterval?: number; // Drift polling interval (ms)
  enableAutoRefresh?: boolean;
}

// ============================================================================
// Main Hook
// ============================================================================

export function useDashboardState(
  options: UseDashboardStateOptions
): [DashboardState, DashboardActions] {
  const {
    user,
    apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
    pollingInterval = 60000, // 60s for drift
    enableAutoRefresh = true
  } = options;

  // ============================================================================
  // State
  // ============================================================================

  const [state, setState] = useState<DashboardState>({
    currentCommand: '',
    parsedIntent: null,
    isParsingIntent: false,
    decomposition: null,
    isDecomposing: false,
    showApproval: false,
    isExecuting: false,
    auditEntries: [],
    isLoadingAudit: false,
    driftEvents: [],
    unacknowledgedDriftCount: 0,
    isLoadingDrift: false,
    error: null,
    lastSuccessfulCommand: null
  });

  // Refs for cleanup
  const intentParseTimerRef = useRef<NodeJS.Timeout | null>(null);
  const driftPollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // ============================================================================
  // Command Actions
  // ============================================================================

  const setCommand = useCallback((command: string) => {
    setState(prev => ({
      ...prev,
      currentCommand: command,
      error: null
    }));

    // Debounced intent parsing (500ms)
    if (intentParseTimerRef.current) {
      clearTimeout(intentParseTimerRef.current);
    }

    if (command.length > 3) {
      setState(prev => ({ ...prev, isParsingIntent: true }));

      intentParseTimerRef.current = setTimeout(async () => {
        try {
          const data = await apiClient.parseIntent(command, user);
          setState(prev => ({
            ...prev,
            parsedIntent: data.intent,
            isParsingIntent: false
          }));
        } catch (error) {
          console.error('Intent parsing error:', error);
          setState(prev => ({
            ...prev,
            isParsingIntent: false,
            parsedIntent: null,
            error: handleAPIError(error)
          }));
        }
      }, 500);
    } else {
      setState(prev => ({
        ...prev,
        parsedIntent: null,
        isParsingIntent: false
      }));
    }
  }, [apiBaseUrl, user]);

  const submitCommand = useCallback(async () => {
    if (!state.currentCommand.trim()) {
      setState(prev => ({ ...prev, error: 'Command cannot be empty' }));
      return;
    }

    setState(prev => ({
      ...prev,
      isDecomposing: true,
      error: null,
      decomposition: null,
      showApproval: false
    }));

    try {
      // Step 1: Parse intent (if not already parsed)
      let intent = state.parsedIntent;
      if (!intent) {
        const parseData = await apiClient.parseIntent(state.currentCommand, user);
        intent = parseData.intent;
      }

      // Step 2: Decompose into tasks
      const decomposeData = await apiClient.decompose(intent, user);

      setState(prev => ({
        ...prev,
        isDecomposing: false,
        decomposition: decomposeData.decomposition,
        showApproval: decomposeData.decomposition.risk_assessment.requires_approval,
        lastSuccessfulCommand: prev.currentCommand
      }));

      // Refresh audit trail to show new entry
      await refreshAudit();

    } catch (error: any) {
      console.error('Command submission error:', error);
      setState(prev => ({
        ...prev,
        isDecomposing: false,
        error: handleAPIError(error)
      }));
    }
  }, [state.currentCommand, state.parsedIntent, apiBaseUrl, user]);

  const clearCommand = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentCommand: '',
      parsedIntent: null,
      decomposition: null,
      showApproval: false,
      error: null
    }));
  }, []);

  // ============================================================================
  // Approval Actions
  // ============================================================================

  const approveTask = useCallback(async () => {
    if (!state.decomposition) {
      setState(prev => ({ ...prev, error: 'No task to approve' }));
      return;
    }

    setState(prev => ({ ...prev, isExecuting: true, error: null }));

    try {
      const approvalPhrase = `APPROVE ${state.decomposition.operation_id}`;
      const data = await apiClient.execute(
        state.decomposition.decomposition_id,
        user,
        true,
        approvalPhrase
      );

      setState(prev => ({
        ...prev,
        isExecuting: false,
        showApproval: false,
        decomposition: null,
        currentCommand: ''
      }));

      // Refresh audit trail
      await refreshAudit();

    } catch (error: any) {
      console.error('Task execution error:', error);
      setState(prev => ({
        ...prev,
        isExecuting: false,
        error: handleAPIError(error)
      }));
    }
  }, [state.decomposition, apiBaseUrl, user]);

  const rejectTask = useCallback(async (reason: string) => {
    if (!state.decomposition) return;

    try {
      await updateAuditEntry(state.decomposition.decomposition_id, {
        status: 'rejected',
        error_message: reason
      });

      setState(prev => ({
        ...prev,
        showApproval: false,
        decomposition: null,
        currentCommand: ''
      }));

      await refreshAudit();

    } catch (error: any) {
      console.error('Task rejection error:', error);
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to reject task'
      }));
    }
  }, [state.decomposition]);

  // ============================================================================
  // Drift Actions
  // ============================================================================

  const loadDriftEvents = useCallback(async () => {
    setState(prev => ({ ...prev, isLoadingDrift: true }));

    try {
      const data = await apiClient.getDrift();

      setState(prev => ({
        ...prev,
        driftEvents: data.events,
        unacknowledgedDriftCount: data.unacknowledged_count || 0,
        isLoadingDrift: false
      }));
    } catch (error) {
      console.error('Drift loading error:', error);
      setState(prev => ({
        ...prev,
        isLoadingDrift: false,
        error: handleAPIError(error)
      }));
    }
  }, []);

  const acknowledgeDrift = useCallback(async (driftId: string) => {
    try {
      await apiClient.acknowledgeDrift(driftId, user);

      setState(prev => ({
        ...prev,
        driftEvents: prev.driftEvents.filter(d => d.id !== driftId),
        unacknowledgedDriftCount: Math.max(0, prev.unacknowledgedDriftCount - 1)
      }));
    } catch (error) {
      console.error('Drift acknowledgement error:', error);
      setState(prev => ({
        ...prev,
        error: handleAPIError(error)
      }));
    }
  }, [user]);

  const revertDrift = useCallback(async (driftId: string) => {
    try {
      await apiClient.revertDrift(driftId, user);

      setState(prev => ({
        ...prev,
        driftEvents: prev.driftEvents.filter(d => d.id !== driftId),
        unacknowledgedDriftCount: Math.max(0, prev.unacknowledgedDriftCount - 1)
      }));

      await refreshAudit();
    } catch (error) {
      console.error('Drift revert error:', error);
      setState(prev => ({
        ...prev,
        error: handleAPIError(error)
      }));
    }
  }, [user]);

  // ============================================================================
  // Audit Actions
  // ============================================================================

  const refreshAudit = useCallback(async () => {
    setState(prev => ({ ...prev, isLoadingAudit: true }));

    try {
      const data = await apiClient.getAudit({ limit: 50 });

      setState(prev => ({
        ...prev,
        auditEntries: data.entries,
        isLoadingAudit: false
      }));
    } catch (error) {
      console.error('Audit loading error:', error);
      setState(prev => ({
        ...prev,
        isLoadingAudit: false,
        error: handleAPIError(error)
      }));
    }
  }, []);

  const exportAudit = useCallback(async (format: 'csv' | 'json') => {
    try {
      const data = await apiClient.exportAudit(format);

      if (format === 'csv') {
        const blob = new Blob([data], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Audit export error:', error);
      setState(prev => ({
        ...prev,
        error: handleAPIError(error)
      }));
    }
  }, []);

  // ============================================================================
  // Error Handling
  // ============================================================================

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  // Initial data load
  useEffect(() => {
    refreshAudit();
    loadDriftEvents();
  }, []);

  // Drift polling
  useEffect(() => {
    if (!enableAutoRefresh) return;

    driftPollingTimerRef.current = setInterval(() => {
      loadDriftEvents();
    }, pollingInterval);

    return () => {
      if (driftPollingTimerRef.current) {
        clearInterval(driftPollingTimerRef.current);
      }
    };
  }, [enableAutoRefresh, pollingInterval, loadDriftEvents]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (intentParseTimerRef.current) {
        clearTimeout(intentParseTimerRef.current);
      }
      if (driftPollingTimerRef.current) {
        clearInterval(driftPollingTimerRef.current);
      }
    };
  }, []);

  // ============================================================================
  // Return
  // ============================================================================

  const actions: DashboardActions = {
    setCommand,
    submitCommand,
    clearCommand,
    approveTask,
    rejectTask,
    acknowledgeDrift,
    revertDrift,
    refreshAudit,
    exportAudit,
    clearError
  };

  return [state, actions];
}

export default useDashboardState;
