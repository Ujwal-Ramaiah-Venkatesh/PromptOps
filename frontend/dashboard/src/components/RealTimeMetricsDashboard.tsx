/**
 * Real-Time Metrics Dashboard Component
 * ======================================
 *
 * Live infrastructure metrics visualization.
 *
 * Features:
 * - Real-time metrics updates via WebSocket
 * - CPU, Memory, Network usage
 * - Request rate and latency
 * - Visual progress bars
 * - Threshold indicators
 *
 * @author PromptOps Team - Q3 2026
 * @date July 8, 2026
 */

import React from 'react';
import { useRealTimeMetrics } from '../hooks/useWebSocket';

interface MetricCardProps {
  title: string;
  value: number;
  unit: string;
  threshold?: { warning: number; critical: number };
  icon?: string;
  isPercentage?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  threshold,
  icon = '📊',
  isPercentage = false,
}) => {
  const getStatusColor = () => {
    if (!threshold) return '#3b82f6';

    if (value >= threshold.critical) return '#ef4444';
    if (value >= threshold.warning) return '#f59e0b';
    return '#10b981';
  };

  const getStatusText = () => {
    if (!threshold) return 'Normal';

    if (value >= threshold.critical) return 'Critical';
    if (value >= threshold.warning) return 'Warning';
    return 'Healthy';
  };

  const color = getStatusColor();
  const percentage = isPercentage ? value : threshold ? (value / threshold.critical) * 100 : 0;

  return (
    <div style={{
      backgroundColor: 'white',
      padding: '20px',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '24px' }}>{icon}</span>
          <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
            {title}
          </span>
        </div>
        <span style={{
          padding: '4px 8px',
          backgroundColor: `${color}20`,
          color: color,
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: '600',
        }}>
          {getStatusText()}
        </span>
      </div>

      {/* Value */}
      <div style={{
        fontSize: '32px',
        fontWeight: '700',
        color: '#1f2937',
        marginBottom: '12px',
      }}>
        {value.toFixed(isPercentage ? 1 : 0)}
        <span style={{ fontSize: '18px', color: '#6b7280', marginLeft: '4px' }}>
          {unit}
        </span>
      </div>

      {/* Progress bar */}
      {threshold && (
        <div style={{
          width: '100%',
          height: '8px',
          backgroundColor: '#e5e7eb',
          borderRadius: '4px',
          overflow: 'hidden',
          marginBottom: '8px',
        }}>
          <div
            style={{
              width: `${Math.min(percentage, 100)}%`,
              height: '100%',
              backgroundColor: color,
              transition: 'all 0.3s ease-out',
            }}
          />
        </div>
      )}

      {/* Threshold info */}
      {threshold && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: '#6b7280',
        }}>
          <span>Warning: {threshold.warning}{unit}</span>
          <span>Critical: {threshold.critical}{unit}</span>
        </div>
      )}
    </div>
  );
};

export const RealTimeMetricsDashboard: React.FC = () => {
  const { metrics, lastUpdate, isConnected } = useRealTimeMetrics();

  if (!isConnected) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔌</div>
        <div style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
          Connecting to Real-Time Metrics...
        </div>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          Establishing WebSocket connection
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
        <div style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
          Waiting for Metrics...
        </div>
        <div style={{ fontSize: '14px', color: '#6b7280' }}>
          Live metrics will appear here
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
      }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#1f2937', margin: 0 }}>
            Real-Time Metrics
          </h2>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>
            Live infrastructure monitoring
          </div>
        </div>

        {/* Connection status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 16px',
          backgroundColor: isConnected ? '#dcfce7' : '#fee2e2',
          color: isConnected ? '#15803d' : '#b91c1c',
          borderRadius: '6px',
          fontSize: '14px',
          fontWeight: '500',
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#10b981' : '#ef4444',
            animation: isConnected ? 'pulse 2s infinite' : 'none',
          }} />
          {isConnected ? 'Live' : 'Disconnected'}
        </div>
      </div>

      {/* Last update time */}
      {lastUpdate && (
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          marginBottom: '16px',
        }}>
          Last updated: {new Date(lastUpdate).toLocaleTimeString()}
        </div>
      )}

      {/* Metrics grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '20px',
      }}>
        {/* CPU Usage */}
        {metrics.cpu_usage !== undefined && (
          <MetricCard
            title="CPU Usage"
            value={metrics.cpu_usage}
            unit="%"
            threshold={{ warning: 70, critical: 90 }}
            icon="⚙️"
            isPercentage={true}
          />
        )}

        {/* Memory Usage */}
        {metrics.memory_usage !== undefined && (
          <MetricCard
            title="Memory Usage"
            value={metrics.memory_usage}
            unit="%"
            threshold={{ warning: 75, critical: 90 }}
            icon="💾"
            isPercentage={true}
          />
        )}

        {/* Request Rate */}
        {metrics.request_count !== undefined && (
          <MetricCard
            title="Request Rate"
            value={metrics.request_count}
            unit=" req/s"
            icon="📈"
          />
        )}

        {/* Response Time */}
        {metrics.response_time !== undefined && (
          <MetricCard
            title="Avg Response Time"
            value={metrics.response_time}
            unit=" ms"
            threshold={{ warning: 500, critical: 1000 }}
            icon="⏱️"
          />
        )}

        {/* Error Rate */}
        {metrics.error_rate !== undefined && (
          <MetricCard
            title="Error Rate"
            value={metrics.error_rate}
            unit="%"
            threshold={{ warning: 1, critical: 5 }}
            icon="⚠️"
            isPercentage={true}
          />
        )}

        {/* Network I/O */}
        {metrics.network_io !== undefined && (
          <MetricCard
            title="Network I/O"
            value={metrics.network_io}
            unit=" MB/s"
            icon="🌐"
          />
        )}

        {/* Disk Usage */}
        {metrics.disk_usage !== undefined && (
          <MetricCard
            title="Disk Usage"
            value={metrics.disk_usage}
            unit="%"
            threshold={{ warning: 80, critical: 95 }}
            icon="💿"
            isPercentage={true}
          />
        )}

        {/* Active Connections */}
        {metrics.active_connections !== undefined && (
          <MetricCard
            title="Active Connections"
            value={metrics.active_connections}
            unit=""
            icon="🔗"
          />
        )}
      </div>

      {/* Inline styles for animation */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.5;
            }
          }
        `}
      </style>
    </div>
  );
};

export default RealTimeMetricsDashboard;
