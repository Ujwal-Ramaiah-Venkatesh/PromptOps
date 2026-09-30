/**
 * Drift Alert Toast Component
 * ============================
 *
 * Real-time infrastructure drift notifications.
 *
 * Features:
 * - Instant drift alerts via WebSocket
 * - Severity-based color coding
 * - Auto-fix suggestions
 * - Dismissible notifications
 * - Action buttons
 *
 * @author PromptOps Team - Q3 2026
 * @date July 8, 2026
 */

import React from 'react';
import { useDriftAlerts } from '../hooks/useWebSocket';

interface DriftAlertToastProps {
  onFixDrift?: (alert: any) => void;
  onViewDetails?: (alert: any) => void;
  autoHideDelay?: number;
}

export const DriftAlertToast: React.FC<DriftAlertToastProps> = ({
  onFixDrift,
  onViewDetails,
  autoHideDelay = 0,
}) => {
  const { alerts, clearAlert, clearAll, isConnected } = useDriftAlerts();

  // Auto-hide alerts after delay (if configured)
  React.useEffect(() => {
    if (autoHideDelay > 0 && alerts.length > 0) {
      const timers = alerts.map((alert) => {
        return setTimeout(() => {
          clearAlert(alert.id);
        }, autoHideDelay);
      });

      return () => {
        timers.forEach(timer => clearTimeout(timer));
      };
    }
  }, [alerts, autoHideDelay, clearAlert]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { bg: '#fee2e2', border: '#ef4444', text: '#b91c1c' };
      case 'high':
        return { bg: '#fed7aa', border: '#f97316', text: '#c2410c' };
      case 'medium':
        return { bg: '#fef3c7', border: '#f59e0b', text: '#d97706' };
      case 'low':
        return { bg: '#dbeafe', border: '#3b82f6', text: '#1d4ed8' };
      default:
        return { bg: '#f3f4f6', border: '#9ca3af', text: '#4b5563' };
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return '⚠';
      case 'medium':
        return '⚡';
      case 'low':
        return 'ℹ';
      default:
        return '•';
    }
  };

  if (alerts.length === 0) {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      width: '400px',
      maxHeight: '80vh',
      overflow: 'auto',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
    }}>
      {/* Clear all button */}
      {alerts.length > 1 && (
        <button
          onClick={clearAll}
          style={{
            padding: '8px 16px',
            backgroundColor: 'white',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          }}
        >
          Clear All ({alerts.length})
        </button>
      )}

      {/* Alert cards */}
      {alerts.map((alert) => {
        const colors = getSeverityColor(alert.severity);

        return (
          <div
            key={alert.id}
            style={{
              backgroundColor: 'white',
              border: `2px solid ${colors.border}`,
              borderRadius: '8px',
              padding: '16px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
              animation: 'slideIn 0.3s ease-out',
            }}
          >
            {/* Header */}
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              marginBottom: '12px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>
                  {getSeverityIcon(alert.severity)}
                </span>
                <div>
                  <div style={{
                    fontWeight: '600',
                    fontSize: '14px',
                    color: colors.text,
                  }}>
                    Infrastructure Drift Detected
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>

              {/* Close button */}
              <button
                onClick={() => clearAlert(alert.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '20px',
                  color: '#9ca3af',
                  padding: 0,
                  width: '24px',
                  height: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                ×
              </button>
            </div>

            {/* Alert details */}
            <div style={{
              padding: '12px',
              backgroundColor: colors.bg,
              borderRadius: '6px',
              marginBottom: '12px',
              fontSize: '13px',
            }}>
              <div style={{ marginBottom: '8px' }}>
                <strong>Resource:</strong> {alert.resource_type} / {alert.resource_id}
              </div>
              <div style={{ marginBottom: '8px' }}>
                <strong>Field:</strong> {alert.field}
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '8px',
              }}>
                <div>
                  <div style={{ color: '#6b7280', fontSize: '12px' }}>Expected</div>
                  <div style={{ fontWeight: '600' }}>{String(alert.expected_value)}</div>
                </div>
                <div>
                  <div style={{ color: '#6b7280', fontSize: '12px' }}>Actual</div>
                  <div style={{ fontWeight: '600', color: colors.text }}>
                    {String(alert.actual_value)}
                  </div>
                </div>
              </div>
            </div>

            {/* Severity badge */}
            <div style={{ marginBottom: '12px' }}>
              <span style={{
                display: 'inline-block',
                padding: '4px 12px',
                backgroundColor: colors.bg,
                color: colors.text,
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: '600',
                textTransform: 'uppercase',
              }}>
                {alert.severity} Severity
              </span>
              {alert.auto_fixable && (
                <span style={{
                  display: 'inline-block',
                  marginLeft: '8px',
                  padding: '4px 12px',
                  backgroundColor: '#dcfce7',
                  color: '#15803d',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '600',
                }}>
                  Auto-fixable
                </span>
              )}
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: '8px' }}>
              {alert.auto_fixable && onFixDrift && (
                <button
                  onClick={() => onFixDrift(alert)}
                  style={{
                    flex: 1,
                    padding: '8px',
                    backgroundColor: colors.border,
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '500',
                  }}
                >
                  Auto-Fix
                </button>
              )}
              {onViewDetails && (
                <button
                  onClick={() => onViewDetails(alert)}
                  style={{
                    flex: 1,
                    padding: '8px',
                    backgroundColor: 'white',
                    color: colors.text,
                    border: `1px solid ${colors.border}`,
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '500',
                  }}
                >
                  View Details
                </button>
              )}
            </div>
          </div>
        );
      })}

      {/* Connection status indicator */}
      {!isConnected && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fee2e2',
          border: '1px solid #ef4444',
          borderRadius: '6px',
          textAlign: 'center',
          fontSize: '13px',
          color: '#b91c1c',
        }}>
          Disconnected - Real-time alerts paused
        </div>
      )}

      {/* Inline styles for animation */}
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
};

export default DriftAlertToast;
