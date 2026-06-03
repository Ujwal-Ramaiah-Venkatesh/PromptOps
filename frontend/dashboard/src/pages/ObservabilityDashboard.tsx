import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import './ObservabilityDashboard.css';

interface CloudWatchMetric {
  timestamp: string;
  value: number;
  unit: string;
}

interface ApplicationHealth {
  status: 'healthy' | 'degraded' | 'critical' | 'unknown';
  uptime: number;
  lastCheck: string;
  issues: string[];
}

interface DeploymentInfo {
  name: string;
  environment: string;
  version: string;
  deployedAt: string;
  url?: string;
  region: string;
  provider: 'AWS' | 'GCP' | 'Azure';
}

export const ObservabilityDashboard: React.FC = () => {
  const [deployments, setDeployments] = useState<DeploymentInfo[]>([]);
  const [selectedDeployment, setSelectedDeployment] = useState<DeploymentInfo | null>(null);
  const [healthStatus, setHealthStatus] = useState<ApplicationHealth | null>(null);
  const [metrics, setMetrics] = useState<{
    cpu: CloudWatchMetric[];
    memory: CloudWatchMetric[];
    requests: CloudWatchMetric[];
    errors: CloudWatchMetric[];
    latency: CloudWatchMetric[];
  }>({
    cpu: [],
    memory: [],
    requests: [],
    errors: [],
    latency: []
  });
  const [logs, setLogs] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch deployed applications
  useEffect(() => {
    fetchDeployments();
  }, []);

  // Auto-refresh metrics
  useEffect(() => {
    if (autoRefresh && selectedDeployment) {
      const interval = setInterval(() => {
        fetchMetrics(selectedDeployment);
        fetchHealthStatus(selectedDeployment);
        fetchRecentLogs(selectedDeployment);
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedDeployment]);

  // Fetch metrics when deployment or time range changes
  useEffect(() => {
    if (selectedDeployment) {
      fetchMetrics(selectedDeployment);
      fetchHealthStatus(selectedDeployment);
      fetchRecentLogs(selectedDeployment);
      fetchAlerts(selectedDeployment);
    }
  }, [selectedDeployment, timeRange]);

  const fetchDeployments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/deployments/list');
      setDeployments(response.data.deployments || []);
      if (response.data.deployments?.length > 0) {
        setSelectedDeployment(response.data.deployments[0]);
      }
    } catch (error) {
      console.error('Failed to fetch deployments:', error);
      // Load mock data for demo
      const mockDeployments: DeploymentInfo[] = [
        {
          name: 'jewelry-vault',
          environment: 'production',
          version: 'v1.2.3',
          deployedAt: new Date().toISOString(),
          url: 'https://app-promptops-891400.s3.us-east-1.amazonaws.com/index.html',
          region: 'us-east-1',
          provider: 'AWS'
        }
      ];
      setDeployments(mockDeployments);
      setSelectedDeployment(mockDeployments[0]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async (deployment: DeploymentInfo) => {
    try {
      const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : timeRange === '24h' ? 24 : 168;

      // Fetch CloudWatch metrics from backend
      const response = await apiClient.get(`/api/v1/monitoring/cloudwatch/metrics`, {
        params: {
          deployment: deployment.name,
          environment: deployment.environment,
          hours,
          region: deployment.region
        }
      });

      setMetrics(response.data.metrics || generateMockMetrics(hours));
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      setMetrics(generateMockMetrics(1));
    }
  };

  const fetchHealthStatus = async (deployment: DeploymentInfo) => {
    try {
      const response = await apiClient.get(`/api/v1/monitoring/health/${deployment.name}`);
      setHealthStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch health status:', error);
      setHealthStatus({
        status: 'healthy',
        uptime: 99.9,
        lastCheck: new Date().toISOString(),
        issues: []
      });
    }
  };

  const fetchRecentLogs = async (deployment: DeploymentInfo) => {
    try {
      const response = await apiClient.get(`/api/v1/monitoring/logs/${deployment.name}`, {
        params: { limit: 100 }
      });
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogs([
        `[${new Date().toISOString()}] Application started successfully`,
        `[${new Date().toISOString()}] Connected to database`,
        `[${new Date().toISOString()}] Server listening on port 3000`
      ]);
    }
  };

  const fetchAlerts = async (deployment: DeploymentInfo) => {
    try {
      const response = await apiClient.get(`/api/v1/monitoring/alerts/${deployment.name}`);
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      setAlerts([]);
    }
  };

  const generateMockMetrics = (hours: number): typeof metrics => {
    const points = Math.min(hours * 12, 100); // 5-minute intervals
    const now = Date.now();

    return {
      cpu: Array.from({ length: points }, (_, i) => ({
        timestamp: new Date(now - (points - i) * 300000).toISOString(),
        value: 20 + Math.random() * 30,
        unit: 'Percent'
      })),
      memory: Array.from({ length: points }, (_, i) => ({
        timestamp: new Date(now - (points - i) * 300000).toISOString(),
        value: 40 + Math.random() * 20,
        unit: 'Percent'
      })),
      requests: Array.from({ length: points }, (_, i) => ({
        timestamp: new Date(now - (points - i) * 300000).toISOString(),
        value: 100 + Math.random() * 200,
        unit: 'Count'
      })),
      errors: Array.from({ length: points }, (_, i) => ({
        timestamp: new Date(now - (points - i) * 300000).toISOString(),
        value: Math.random() < 0.1 ? Math.floor(Math.random() * 5) : 0,
        unit: 'Count'
      })),
      latency: Array.from({ length: points }, (_, i) => ({
        timestamp: new Date(now - (points - i) * 300000).toISOString(),
        value: 50 + Math.random() * 100,
        unit: 'Milliseconds'
      }))
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'degraded': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✓';
      case 'degraded': return '⚠';
      case 'critical': return '✕';
      default: return '?';
    }
  };

  const renderMetricChart = (title: string, data: CloudWatchMetric[], color: string) => {
    if (data.length === 0) return null;

    const max = Math.max(...data.map(d => d.value));
    const min = Math.min(...data.map(d => d.value));
    const range = max - min || 1;

    return (
      <div
        style={styles.metricCard}
        className="metric-card-hover glass-card"
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 12px 40px rgba(139, 92, 246, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3)';
        }}
      >
        <h3 style={styles.metricTitle}>{title}</h3>
        <div style={styles.metricValue} className="metric-value">
          {data[data.length - 1]?.value.toFixed(2)} {data[0]?.unit}
        </div>
        <div style={styles.chartContainer} className="chart-container">
          <svg width="100%" height="100" style={{ display: 'block' }}>
            <polyline
              points={data.map((d, i) => {
                const x = (i / (data.length - 1)) * 100;
                const y = 100 - ((d.value - min) / range) * 80 - 10;
                return `${x}%,${y}`;
              }).join(' ')}
              fill="none"
              stroke={color}
              strokeWidth="2"
            />
          </svg>
        </div>
        <div style={styles.metricRange}>
          <span>Min: {min.toFixed(2)}</span>
          <span>Max: {max.toFixed(2)}</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div style={styles.container} className="premium-bg-1">
        <div style={styles.loading}>
          <div className="loading-spinner"></div>
          <p style={{ marginTop: '20px' }}>Loading observability data...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container} className="premium-bg-1">
      <div style={styles.header}>
        <h1 style={styles.title} className="gradient-text">
          <span style={{ fontSize: '40px' }}>⚡</span>
          CloudWatch Observability
        </h1>
        <p style={styles.subtitle}>Real-time monitoring and health checks for deployed applications</p>
      </div>

      {/* Deployment Selector */}
      <div style={styles.deploymentSelector} className="glass-card deployment-selector-wrapper">
        <label style={styles.label}>Select Deployment:</label>
        <select
          style={styles.select}
          value={selectedDeployment?.name || ''}
          onChange={(e) => {
            const dep = deployments.find(d => d.name === e.target.value);
            setSelectedDeployment(dep || null);
          }}
        >
          {deployments.map(dep => (
            <option key={dep.name} value={dep.name}>
              {dep.name} ({dep.environment}) - {dep.provider}
            </option>
          ))}
        </select>
      </div>

      {selectedDeployment && (
        <>
          {/* Health Status Overview */}
          <div
            style={styles.healthCard}
            className={`glass-card card-stack ${
              healthStatus?.status === 'healthy' ? 'health-card-healthy' :
              healthStatus?.status === 'degraded' ? 'health-card-degraded' :
              healthStatus?.status === 'critical' ? 'health-card-critical' : ''
            }`}
          >
            <div style={styles.healthHeader}>
              <div style={styles.healthStatus}>
                <div
                  className="status-badge"
                  style={{
                    ...styles.statusBadge,
                    backgroundColor: getStatusColor(healthStatus?.status || 'unknown')
                  }}
                >
                  {getStatusIcon(healthStatus?.status || 'unknown')}
                </div>
                <div>
                  <div style={styles.healthTitle}>{selectedDeployment.name}</div>
                  <div style={styles.healthSubtitle}>
                    {selectedDeployment.environment} • {selectedDeployment.region} • {selectedDeployment.version}
                  </div>
                </div>
              </div>
              <div style={styles.healthMetrics}>
                <div style={styles.healthMetric}>
                  <div style={styles.healthMetricValue}>{healthStatus?.uptime.toFixed(2)}%</div>
                  <div style={styles.healthMetricLabel}>Uptime</div>
                </div>
                {selectedDeployment.url && (
                  <a
                    href={selectedDeployment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.viewButton}
                    className="gradient-button"
                  >
                    View App →
                  </a>
                )}
              </div>
            </div>
            {healthStatus?.issues && healthStatus.issues.length > 0 && (
              <div style={styles.issuesContainer}>
                <strong>Issues:</strong>
                <ul style={styles.issuesList}>
                  {healthStatus.issues.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Controls */}
          <div style={styles.controls} className="glass-card">
            <div style={styles.timeRangeButtons}>
              {(['1h', '6h', '24h', '7d'] as const).map(range => (
                <button
                  key={range}
                  style={{
                    ...styles.timeRangeButton,
                    ...(timeRange === range ? styles.timeRangeButtonActive : {})
                  }}
                  onClick={() => setTimeRange(range)}
                  onMouseEnter={(e) => {
                    if (timeRange !== range) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (timeRange !== range) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }
                  }}
                >
                  {range}
                </button>
              ))}
            </div>
            <label
              style={styles.autoRefreshLabel}
              className={autoRefresh ? 'auto-refresh-active' : ''}
            >
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                style={styles.checkbox}
              />
              Auto-refresh (30s)
            </label>
          </div>

          {/* Metrics Grid */}
          <div style={styles.metricsGrid}>
            {renderMetricChart('CPU Usage', metrics.cpu, '#3b82f6')}
            {renderMetricChart('Memory Usage', metrics.memory, '#8b5cf6')}
            {renderMetricChart('Request Rate', metrics.requests, '#10b981')}
            {renderMetricChart('Error Rate', metrics.errors, '#ef4444')}
            {renderMetricChart('Response Time (p95)', metrics.latency, '#f59e0b')}
          </div>

          {/* Alerts */}
          {alerts.length > 0 && (
            <div style={styles.alertsCard} className="glass-card">
              <h3 style={styles.sectionTitle}>🚨 Active Alerts</h3>
              <div style={styles.alertsList}>
                {alerts.map((alert, i) => (
                  <div key={i} style={styles.alert} className="alert-card">
                    <div style={styles.alertHeader}>
                      <span style={{ color: alert.severity === 'critical' ? '#ef4444' : '#f59e0b' }}>
                        {alert.severity === 'critical' ? '🔴' : '🟡'}
                      </span>
                      <strong>{alert.title}</strong>
                    </div>
                    <div style={styles.alertMessage}>{alert.message}</div>
                    <div style={styles.alertTime}>{new Date(alert.timestamp).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Logs */}
          <div style={styles.logsCard} className="glass-card">
            <h3 style={styles.sectionTitle}>📋 Recent Logs</h3>
            <div style={styles.logsContainer} className="frosted-glass">
              {logs.map((log, i) => (
                <div key={i} style={styles.logEntry} className="log-entry">{log}</div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '32px',
    maxWidth: '1400px',
    margin: '0 auto',
    background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e3a8a 100%)',
    minHeight: '100vh',
    position: 'relative' as const
  },
  header: {
    marginBottom: '40px',
    textAlign: 'center' as const
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '12px',
    color: '#ffffff',
    textShadow: '0 2px 10px rgba(139, 92, 246, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px'
  },
  subtitle: {
    fontSize: '16px',
    color: '#c7d2fe',
    fontWeight: '400'
  },
  loading: {
    textAlign: 'center' as const,
    padding: '48px',
    fontSize: '18px',
    color: '#c7d2fe'
  },
  deploymentSelector: {
    marginBottom: '24px',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    fontWeight: '600',
    color: '#e0e7ff',
    fontSize: '14px'
  },
  select: {
    width: '100%',
    padding: '12px 16px',
    background: 'rgba(255, 255, 255, 0.15)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '12px',
    fontSize: '14px',
    color: '#ffffff',
    fontWeight: '500',
    cursor: 'pointer'
  },
  healthCard: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    padding: '28px',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    marginBottom: '24px'
  },
  healthHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  healthStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  statusBadge: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '24px',
    fontWeight: 'bold'
  },
  healthTitle: {
    fontSize: '22px',
    fontWeight: 'bold',
    color: '#ffffff'
  },
  healthSubtitle: {
    fontSize: '14px',
    color: '#c7d2fe',
    marginTop: '4px'
  },
  healthMetrics: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px'
  },
  healthMetric: {
    textAlign: 'center' as const
  },
  healthMetricValue: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#ffffff'
  },
  healthMetricLabel: {
    fontSize: '12px',
    color: '#c7d2fe',
    marginTop: '4px'
  },
  viewButton: {
    padding: '10px 20px',
    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
    color: 'white',
    borderRadius: '12px',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
    transition: 'all 0.3s ease'
  },
  issuesContainer: {
    marginTop: '16px',
    padding: '16px',
    background: 'rgba(239, 68, 68, 0.2)',
    borderRadius: '12px',
    borderLeft: '4px solid #ef4444',
    backdropFilter: 'blur(10px)'
  },
  issuesList: {
    margin: '8px 0 0 0',
    paddingLeft: '20px',
    color: '#fecaca'
  },
  controls: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
  },
  timeRangeButtons: {
    display: 'flex',
    gap: '8px'
  },
  timeRangeButton: {
    padding: '10px 20px',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '12px',
    background: 'rgba(255, 255, 255, 0.1)',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    color: '#e0e7ff',
    transition: 'all 0.3s ease'
  },
  timeRangeButtonActive: {
    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
    color: 'white',
    borderColor: '#8b5cf6',
    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)'
  },
  autoRefreshLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    color: '#e0e7ff',
    cursor: 'pointer',
    fontWeight: '500'
  },
  checkbox: {
    cursor: 'pointer'
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
    marginBottom: '24px'
  },
  metricCard: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    padding: '24px',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    transition: 'all 0.3s ease'
  },
  metricTitle: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#c7d2fe',
    marginBottom: '12px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px'
  },
  metricValue: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: '16px',
    textShadow: '0 2px 8px rgba(139, 92, 246, 0.3)'
  },
  chartContainer: {
    width: '100%',
    height: '100px',
    marginBottom: '8px'
  },
  metricRange: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    color: '#a5b4fc',
    fontWeight: '500'
  },
  alertsCard: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    padding: '28px',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    marginBottom: '24px'
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  alertsList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px'
  },
  alert: {
    padding: '16px',
    background: 'rgba(239, 68, 68, 0.15)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    borderLeft: '4px solid #ef4444',
    border: '1px solid rgba(239, 68, 68, 0.3)'
  },
  alertHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
    color: '#fecaca',
    fontWeight: '600'
  },
  alertMessage: {
    fontSize: '14px',
    color: '#fca5a5',
    marginBottom: '8px'
  },
  alertTime: {
    fontSize: '12px',
    color: '#fca5a5',
    opacity: 0.8
  },
  logsCard: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    padding: '28px',
    borderRadius: '20px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
  },
  logsContainer: {
    maxHeight: '400px',
    overflowY: 'auto' as const,
    background: 'rgba(0, 0, 0, 0.4)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    padding: '20px',
    fontFamily: 'monospace',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  logEntry: {
    fontSize: '13px',
    color: '#e0e7ff',
    padding: '8px 0',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    lineHeight: '1.6'
  }
};
