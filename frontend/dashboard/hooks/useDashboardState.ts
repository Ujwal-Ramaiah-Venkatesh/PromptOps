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
    apiBaseUrl = '/api',
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
          const response = await fetch(`${apiBaseUrl}/parse-intent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, user })
          });

          if (!response.ok) {
            throw new Error('Failed to parse intent');
          }

          const data = await response.json();
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
            parsedIntent: null
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
        const parseResponse = await fetch(`${apiBaseUrl}/parse-intent`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: state.currentCommand, user })
        });

        if (!parseResponse.ok) {
          throw new Error('Failed to parse command');
        }

        const parseData = await parseResponse.json();
        intent = parseData.intent;
      }

      // Step 2: Decompose into tasks
      const decomposeResponse = await fetch(`${apiBaseUrl}/decompose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent, user })
      });

      if (!decomposeResponse.ok) {
        throw new Error('Failed to decompose command');
      }

      const decomposeData = await decomposeResponse.json();

      setState(prev => ({
        ...prev,
        isDecomposing: false,
        decomposition: decomposeData.decomposition,
        showApproval: decomposeData.decomposition.risk_assessment.requires_approval,
        lastSuccessfulCommand: prev.currentCommand
      }));

      // Add to audit trail (pending)
      await addAuditEntry({
        command: state.currentCommand,
        intent,
        decomposition: decomposeData.decomposition,
        status: 'pending'
      });

    } catch (error: any) {
      console.error('Command submission error:', error);
      setState(prev => ({
        ...prev,
        isDecomposing: false,
        error: error.message || 'Failed to process command'
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
      const response = await fetch(`${apiBaseUrl}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decomposition_id: state.decomposition.decomposition_id,
          user,
          approved: true
        })
      });

      if (!response.ok) {
        throw new Error('Failed to execute task');
      }

      const data = await response.json();

      // Update audit entry to approved/executing
      await updateAuditEntry(state.decomposition.decomposition_id, {
        status: 'executing',
        approved_by: user,
        approved_at: new Date().toISOString()
      });

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
        error: error.message || 'Failed to execute task'
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
      const response = await fetch(`${apiBaseUrl}/drift/recent`);

      if (!response.ok) {
        throw new Error('Failed to load drift events');
      }

      const data = await response.json();

      setState(prev => ({
        ...prev,
        driftEvents: data.events,
        unacknowledgedDriftCount: data.unacknowledged_count || 0,
        isLoadingDrift: false
      }));
    } catch (error) {
      console.error('Drift loading error:', error);
      setState(prev => ({ ...prev, isLoadingDrift: false }));
    }
  }, [apiBaseUrl]);

  const acknowledgeDrift = useCallback(async (driftId: string) => {
    try {
      await fetch(`${apiBaseUrl}/drift/${driftId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user })
      });

      setState(prev => ({
        ...prev,
        driftEvents: prev.driftEvents.filter(d => d.id !== driftId),
        unacknowledgedDriftCount: Math.max(0, prev.unacknowledgedDriftCount - 1)
      }));
    } catch (error) {
      console.error('Drift acknowledgement error:', error);
    }
  }, [apiBaseUrl, user]);

  const revertDrift = useCallback(async (driftId: string) => {
    try {
      await fetch(`${apiBaseUrl}/drift/${driftId}/revert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user })
      });

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
        error: 'Failed to revert drift'
      }));
    }
  }, [apiBaseUrl, user]);

  // ============================================================================
  // Audit Actions
  // ============================================================================

  const refreshAudit = useCallback(async () => {
    setState(prev => ({ ...prev, isLoadingAudit: true }));

    try {
      const response = await fetch(`${apiBaseUrl}/audit?limit=50`);

      if (!response.ok) {
        throw new Error('Failed to load audit trail');
      }

      const data = await response.json();

      setState(prev => ({
        ...prev,
        auditEntries: data.entries,
        isLoadingAudit: false
      }));
    } catch (error) {
      console.error('Audit loading error:', error);
      setState(prev => ({ ...prev, isLoadingAudit: false }));
    }
  }, [apiBaseUrl]);

  const addAuditEntry = async (entry: any) => {
    try {
      await fetch(`${apiBaseUrl}/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...entry,
          user,
          timestamp: new Date().toISOString()
        })
      });

      await refreshAudit();
    } catch (error) {
      console.error('Failed to add audit entry:', error);
    }
  };

  const updateAuditEntry = async (id: string, updates: any) => {
    try {
      await fetch(`${apiBaseUrl}/audit/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      await refreshAudit();
    } catch (error) {
      console.error('Failed to update audit entry:', error);
    }
  };

  const exportAudit = useCallback(async (format: 'csv' | 'json') => {
    try {
      const response = await fetch(`${apiBaseUrl}/audit/export?format=${format}`);

      if (!response.ok) {
        throw new Error('Failed to export audit trail');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Audit export error:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to export audit trail'
      }));
    }
  }, [apiBaseUrl]);

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
