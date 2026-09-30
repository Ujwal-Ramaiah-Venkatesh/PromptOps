/**
 * Live Log Viewer Component
 * =========================
 *
 * Real-time log streaming component with auto-scroll and filtering.
 *
 * Features:
 * - Live log streaming via WebSocket
 * - Auto-scroll to latest logs
 * - Log level filtering
 * - Search functionality
 * - Copy to clipboard
 *
 * @author PromptOps Team - Q3 2026
 * @date July 8, 2026
 */

import React, { useState, useEffect, useRef } from 'react';
import { useDeploymentLogs } from '../hooks/useWebSocket';

interface LiveLogViewerProps {
  deploymentId?: string;
  maxLogs?: number;
  autoScroll?: boolean;
}

export const LiveLogViewer: React.FC<LiveLogViewerProps> = ({
  deploymentId,
  maxLogs = 1000,
  autoScroll = true,
}) => {
  const { logs, clearLogs, isConnected } = useDeploymentLogs(deploymentId);
  const [filter, setFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [isAutoScroll, setIsAutoScroll] = useState(autoScroll);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (isAutoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll]);

  // Filter logs
  const filteredLogs = logs
    .filter(log => {
      if (levelFilter !== 'all' && log.level !== levelFilter) {
        return false;
      }
      if (filter && !log.message.toLowerCase().includes(filter.toLowerCase())) {
        return false;
      }
      return true;
    })
    .slice(-maxLogs);

  // Copy all logs to clipboard
  const copyToClipboard = () => {
    const text = filteredLogs
      .map(log => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`)
      .join('\n');

    navigator.clipboard.writeText(text);
  };

  // Get log level color
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return '#ef4444';
      case 'warning':
        return '#f59e0b';
      case 'info':
        return '#3b82f6';
      case 'debug':
        return '#6b7280';
      default:
        return '#9ca3af';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontFamily: 'monospace' }}>
      {/* Header */}
      <div style={{
        padding: '12px',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        backgroundColor: '#f9fafb',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: '600', fontSize: '14px' }}>Live Logs</span>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#10b981' : '#ef4444',
          }} />
        </div>

        {/* Level filter */}
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          style={{
            padding: '4px 8px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
            fontSize: '12px',
          }}
        >
          <option value="all">All Levels</option>
          <option value="error">Error</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>

        {/* Search filter */}
        <input
          type="text"
          placeholder="Filter logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            padding: '4px 8px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
            fontSize: '12px',
            flex: 1,
          }}
        />

        {/* Auto-scroll toggle */}
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
          <input
            type="checkbox"
            checked={isAutoScroll}
            onChange={(e) => setIsAutoScroll(e.target.checked)}
          />
          Auto-scroll
        </label>

        {/* Actions */}
        <button
          onClick={copyToClipboard}
          style={{
            padding: '4px 12px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          Copy
        </button>

        <button
          onClick={clearLogs}
          style={{
            padding: '4px 12px',
            borderRadius: '4px',
            border: '1px solid #d1d5db',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          Clear
        </button>
      </div>

      {/* Logs container */}
      <div
        ref={logContainerRef}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px',
          backgroundColor: '#1f2937',
          color: '#f3f4f6',
          fontSize: '12px',
          lineHeight: '1.5',
        }}
      >
        {filteredLogs.length === 0 ? (
          <div style={{ color: '#9ca3af', padding: '20px', textAlign: 'center' }}>
            {logs.length === 0 ? 'Waiting for logs...' : 'No logs match the current filter'}
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id}
              style={{
                padding: '4px 0',
                borderBottom: '1px solid #374151',
              }}
            >
              <span style={{ color: '#6b7280', marginRight: '8px' }}>
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span
                style={{
                  color: getLevelColor(log.level),
                  fontWeight: '600',
                  marginRight: '8px',
                }}
              >
                [{log.level.toUpperCase()}]
              </span>
              <span>{log.message}</span>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div style={{
        padding: '8px 12px',
        borderTop: '1px solid #e5e7eb',
        backgroundColor: '#f9fafb',
        fontSize: '12px',
        color: '#6b7280',
      }}>
        {filteredLogs.length} of {logs.length} logs
        {logs.length >= maxLogs && ` (limited to ${maxLogs})`}
      </div>
    </div>
  );
};

export default LiveLogViewer;
