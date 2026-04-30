/**
 * Audit Trail Component
 * ======================
 *
 * Immutable log of all commands and actions with filtering,
 * search, and export capabilities.
 *
 * Features:
 * - Chronological list (newest first)
 * - Full-text search
 * - Multi-filter (user, env, type, status, date range)
 * - Expandable details
 * - Status indicators
 * - Export to CSV/JSON
 * - Pagination
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import './AuditTrail.css';

// ============================================================================
// Type Definitions
// ============================================================================

export type AuditStatus = 'pending' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed' | 'rolled_back';

export interface AuditEntry {
  id: string;
  timestamp: string;
  user: string;
  command: string;
  intent_type: string;
  target_service: string;
  target_env: string;
  status: AuditStatus;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  duration?: number; // seconds
  error_message?: string;
  task_plan?: any;
  execution_log?: string[];
}

export interface AuditTrailProps {
  entries?: AuditEntry[];
  limit?: number;
  onViewAll?: () => void;
  onRefresh?: () => void;
  showFilters?: boolean;
  showSearch?: boolean;
  showExport?: boolean;
  compact?: boolean;
}

export interface AuditFilters {
  search: string;
  user: string;
  environment: string;
  intentType: string;
  status: string;
  dateFrom: string;
  dateTo: string;
}

// ============================================================================
// Audit Trail Component
// ============================================================================

export function AuditTrail({
  entries = [],
  limit,
  onViewAll,
  onRefresh,
  showFilters = true,
  showSearch = true,
  showExport = true,
  compact = false
}: AuditTrailProps): JSX.Element {
  const [filters, setFilters] = useState<AuditFilters>({
    search: '',
    user: '',
    environment: '',
    intentType: '',
    status: '',
    dateFrom: '',
    dateTo: ''
  });
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set());
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  // Filter entries
  const filteredEntries = useMemo(() => {
    let result = [...entries];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(entry =>
        entry.command.toLowerCase().includes(searchLower) ||
        entry.user.toLowerCase().includes(searchLower) ||
        entry.target_service.toLowerCase().includes(searchLower) ||
        entry.intent_type.toLowerCase().includes(searchLower)
      );
    }

    // User filter
    if (filters.user) {
      result = result.filter(entry => entry.user === filters.user);
    }

    // Environment filter
    if (filters.environment) {
      result = result.filter(entry => entry.target_env === filters.environment);
    }

    // Intent type filter
    if (filters.intentType) {
      result = result.filter(entry => entry.intent_type === filters.intentType);
    }

    // Status filter
    if (filters.status) {
      result = result.filter(entry => entry.status === filters.status);
    }

    // Date range filter
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      result = result.filter(entry => new Date(entry.timestamp) >= fromDate);
    }
    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59, 999); // End of day
      result = result.filter(entry => new Date(entry.timestamp) <= toDate);
    }

    return result;
  }, [entries, filters]);

  // Apply limit
  const displayedEntries = limit ? filteredEntries.slice(0, limit) : filteredEntries;
  const hasMore = limit && filteredEntries.length > limit;

  // Toggle expanded entry
  const toggleExpand = useCallback((entryId: string) => {
    setExpandedEntries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(entryId)) {
        newSet.delete(entryId);
      } else {
        newSet.add(entryId);
      }
      return newSet;
    });
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      user: '',
      environment: '',
      intentType: '',
      status: '',
      dateFrom: '',
      dateTo: ''
    });
  }, []);

  // Export to CSV
  const exportToCSV = useCallback(() => {
    const headers = ['Timestamp', 'User', 'Command', 'Type', 'Service', 'Environment', 'Status', 'Risk', 'Duration'];
    const rows = filteredEntries.map(entry => [
      entry.timestamp,
      entry.user,
      entry.command,
      entry.intent_type,
      entry.target_service,
      entry.target_env,
      entry.status,
      entry.risk_level,
      entry.duration ? `${entry.duration}s` : ''
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredEntries]);

  // Export to JSON
  const exportToJSON = useCallback(() => {
    const json = JSON.stringify(filteredEntries, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-trail-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filteredEntries]);

  // Get unique filter options
  const uniqueUsers = useMemo(() => [...new Set(entries.map(e => e.user))], [entries]);
  const uniqueEnvs = useMemo(() => [...new Set(entries.map(e => e.target_env))], [entries]);
  const uniqueTypes = useMemo(() => [...new Set(entries.map(e => e.intent_type))], [entries]);

  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  return (
    <div className={`audit-trail ${compact ? 'audit-trail--compact' : ''}`}>
      {/* Header */}
      <div className="audit-trail-header">
        <div className="audit-trail-title">
          <h3>Audit Trail</h3>
          <span className="audit-count">
            {filteredEntries.length} {filteredEntries.length === 1 ? 'entry' : 'entries'}
            {hasActiveFilters && ' (filtered)'}
          </span>
        </div>

        <div className="audit-trail-actions">
          {showSearch && (
            <input
              type="text"
              className="audit-search-input"
              placeholder="Search commands..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          )}

          {showFilters && (
            <button
              className={`audit-action-button ${showFilterPanel ? 'audit-action-button--active' : ''}`}
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              title="Toggle filters"
            >
              🔍
            </button>
          )}

          {onRefresh && (
            <button
              className="audit-action-button"
              onClick={onRefresh}
              title="Refresh"
            >
              🔄
            </button>
          )}

          {showExport && (
            <div className="audit-export-buttons">
              <button
                className="audit-action-button"
                onClick={exportToCSV}
                title="Export to CSV"
              >
                CSV
              </button>
              <button
                className="audit-action-button"
                onClick={exportToJSON}
                title="Export to JSON"
              >
                JSON
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Filter Panel */}
      {showFilterPanel && showFilters && (
        <div className="audit-filter-panel">
          <div className="audit-filter-grid">
            <select
              className="audit-filter-select"
              value={filters.user}
              onChange={(e) => setFilters({ ...filters, user: e.target.value })}
            >
              <option value="">All Users</option>
              {uniqueUsers.map(user => (
                <option key={user} value={user}>{user}</option>
              ))}
            </select>

            <select
              className="audit-filter-select"
              value={filters.environment}
              onChange={(e) => setFilters({ ...filters, environment: e.target.value })}
            >
              <option value="">All Environments</option>
              {uniqueEnvs.map(env => (
                <option key={env} value={env}>{env}</option>
              ))}
            </select>

            <select
              className="audit-filter-select"
              value={filters.intentType}
              onChange={(e) => setFilters({ ...filters, intentType: e.target.value })}
            >
              <option value="">All Types</option>
              {uniqueTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <select
              className="audit-filter-select"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="executing">Executing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="rolled_back">Rolled Back</option>
            </select>

            <input
              type="date"
              className="audit-filter-input"
              placeholder="From date"
              value={filters.dateFrom}
              onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
            />

            <input
              type="date"
              className="audit-filter-input"
              placeholder="To date"
              value={filters.dateTo}
              onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
            />
          </div>

          {hasActiveFilters && (
            <button className="audit-clear-filters" onClick={clearFilters}>
              Clear All Filters
            </button>
          )}
        </div>
      )}

      {/* Entries List */}
      <div className="audit-trail-body">
        {displayedEntries.length === 0 ? (
          <div className="audit-empty-state">
            <span className="empty-state-icon">📋</span>
            <p>No audit entries found</p>
            {hasActiveFilters && (
              <button className="empty-state-action" onClick={clearFilters}>
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="audit-entries">
            {displayedEntries.map(entry => (
              <AuditEntryRow
                key={entry.id}
                entry={entry}
                expanded={expandedEntries.has(entry.id)}
                onToggle={() => toggleExpand(entry.id)}
                compact={compact}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {(hasMore || onViewAll) && (
        <div className="audit-trail-footer">
          {hasMore && (
            <p className="audit-trail-footer-text">
              Showing {displayedEntries.length} of {filteredEntries.length} entries
            </p>
          )}
          {onViewAll && (
            <button className="audit-view-all-button" onClick={onViewAll}>
              View All Entries →
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Audit Entry Row Component
// ============================================================================

interface AuditEntryRowProps {
  entry: AuditEntry;
  expanded: boolean;
  onToggle: () => void;
  compact: boolean;
}

function AuditEntryRow({ entry, expanded, onToggle, compact }: AuditEntryRowProps): JSX.Element {
  const statusIcons = {
    pending: '⏳',
    approved: '✅',
    rejected: '❌',
    executing: '⚙️',
    completed: '✓',
    failed: '⚠️',
    rolled_back: '↩️'
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className={`audit-entry audit-entry--${entry.status} audit-entry--risk-${entry.risk_level}`}>
      <div className="audit-entry-header" onClick={onToggle}>
        <div className="audit-entry-main">
          <div className="audit-entry-status">
            <span className={`status-icon status-icon--${entry.status}`}>
              {statusIcons[entry.status]}
            </span>
          </div>

          <div className="audit-entry-info">
            <div className="audit-entry-command">{entry.command}</div>
            <div className="audit-entry-meta">
              <span className="audit-meta-item">
                <span className="audit-meta-label">User:</span>
                <span className="audit-meta-value">{entry.user}</span>
              </span>
              <span className="audit-meta-separator">•</span>
              <span className="audit-meta-item">
                <span className="audit-meta-label">Type:</span>
                <span className="audit-meta-value">{entry.intent_type}</span>
              </span>
              <span className="audit-meta-separator">•</span>
              <span className="audit-meta-item">
                <span className="audit-meta-label">Service:</span>
                <span className="audit-meta-value">{entry.target_service}</span>
              </span>
              <span className="audit-meta-separator">•</span>
              <span className={`audit-meta-item audit-meta-env audit-meta-env--${entry.target_env}`}>
                {entry.target_env}
              </span>
            </div>
          </div>
        </div>

        <div className="audit-entry-right">
          <div className="audit-entry-timestamp">
            {formatTimestamp(entry.timestamp)}
          </div>
          {entry.duration && (
            <div className="audit-entry-duration">
              {formatDuration(entry.duration)}
            </div>
          )}
          <button className="audit-expand-button" aria-label={expanded ? 'Collapse' : 'Expand'}>
            <span className={`expand-icon ${expanded ? 'expand-icon--open' : ''}`}>▼</span>
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="audit-entry-details">
          {entry.error_message && (
            <div className="audit-detail-section audit-detail-error">
              <strong>Error:</strong>
              <p>{entry.error_message}</p>
            </div>
          )}

          {entry.task_plan && (
            <div className="audit-detail-section">
              <strong>Task Plan:</strong>
              <div className="audit-task-summary">
                <div className="task-summary-item">
                  <span className="task-summary-label">Sub-tasks:</span>
                  <span className="task-summary-value">{entry.task_plan.total_sub_tasks || 0}</span>
                </div>
                <div className="task-summary-item">
                  <span className="task-summary-label">Risk Level:</span>
                  <span className={`task-summary-value task-summary-risk--${entry.risk_level}`}>
                    {entry.risk_level.toUpperCase()}
                  </span>
                </div>
                {entry.task_plan.estimated_duration && (
                  <div className="task-summary-item">
                    <span className="task-summary-label">Est. Duration:</span>
                    <span className="task-summary-value">
                      {Math.floor(entry.task_plan.estimated_duration / 60)}min
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {entry.execution_log && entry.execution_log.length > 0 && (
            <div className="audit-detail-section">
              <strong>Execution Log:</strong>
              <div className="audit-execution-log">
                {entry.execution_log.map((log, index) => (
                  <div key={index} className="log-entry">
                    <span className="log-index">{index + 1}.</span>
                    <span className="log-text">{log}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="audit-detail-footer">
            <span className="audit-detail-id">ID: {entry.id}</span>
            <span className="audit-detail-timestamp">
              {new Date(entry.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default AuditTrail;
