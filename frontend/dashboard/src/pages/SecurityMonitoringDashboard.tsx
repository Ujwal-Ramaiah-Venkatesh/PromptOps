import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import './SecurityMonitoringDashboard.css';

interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  active_threads: number;
  status: 'healthy' | 'warning' | 'critical';
}

interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  detected_at: string;
  resource: string;
  auto_remediated: boolean;
  remediation_suggested?: string;
}

interface TestResult {
  test_id: string;
  test_type: string;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  duration_seconds?: number;
  metrics?: any;
  issues?: Alert[];
  recommendations?: string[];
}

interface DashboardSummary {
  system_health: SystemMetrics;
  alerts: {
    critical: number;
    high: number;
    total_active: number;
  };
  tests: {
    active: number;
    total: number;
    completed: number;
  };
  remediation: {
    total_actions: number;
    success_rate_percent: number;
  };
}

export const SecurityMonitoringDashboard: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [tests, setTests] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'tests' | 'alerts' | 'remediation'>('overview');

  // Test configuration states
  const [targetUrl, setTargetUrl] = useState('');
  const [bucketName, setBucketName] = useState('');
  const [testRunning, setTestRunning] = useState(false);

  useEffect(() => {
    fetchDashboardData();

    // Try to populate target URL from recent deployments
    const recentDeployments = localStorage.getItem('promptops_recent_deployments');
    if (recentDeployments && !targetUrl) {
      try {
        const parsed = JSON.parse(recentDeployments);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].website_url) {
          setTargetUrl(parsed[0].website_url);
          if (parsed[0].bucket) {
            setBucketName(parsed[0].bucket);
          }
        }
      } catch (e) {
        console.error('Failed to parse recent deployments:', e);
      }
    }
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchDashboardData();
      }, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchDashboardData = async () => {
    try {
      const [summaryData, alertsData, testsData] = await Promise.all([
        apiClient.get('/api/v1/advanced-monitoring/dashboard/summary'),
        apiClient.get('/api/v1/advanced-monitoring/alerts', { params: { limit: 20 } }),
        apiClient.get('/api/v1/advanced-monitoring/tests/active')
      ]);

      setSummary(summaryData);
      setAlerts(alertsData.alerts || []);
      setTests(testsData.tests || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);

      // Show demo data when no backend connection
      setSummary({
        system_health: {
          cpu_percent: 35.2,
          memory_percent: 62.8,
          disk_percent: 45.1,
          active_threads: 42,
          status: 'healthy'
        },
        alerts: {
          critical: 0,
          high: 0,
          total_active: 0
        },
        tests: {
          active: 0,
          total: 0,
          completed: 0
        },
        remediation: {
          total_actions: 0,
          success_rate_percent: 0
        }
      });
      setAlerts([]);
      setTests([]);
      setLoading(false);
    }
  };

  const runLoadTest = async () => {
    if (!targetUrl) {
      alert('Please enter target URL');
      return;
    }

    try {
      setTestRunning(true);
      const response = await apiClient.post('/api/v1/advanced-monitoring/tests/load', {
        target_url: targetUrl,
        duration_seconds: 60,
        concurrent_users: 20,
        requests_per_second: 100,
        ramp_up_seconds: 10,
        test_type: 'load_test'
      });

      alert(`Load test started: ${response.test_id}\nMonitor the Tests tab for results.`);
      fetchDashboardData();
    } catch (error: any) {
      alert(`Failed to start load test: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestRunning(false);
    }
  };

  const runSecurityScan = async () => {
    if (!targetUrl || !bucketName) {
      alert('Please enter target URL and bucket name');
      return;
    }

    try {
      setTestRunning(true);
      const response = await apiClient.post('/api/v1/advanced-monitoring/tests/security', {
        target_url: targetUrl,
        bucket_name: bucketName,
        region: 'us-east-1',
        scan_depth: 'comprehensive',
        check_ssl: true,
        check_headers: true,
        check_vulnerabilities: true
      });

      alert(`Security scan started: ${response.test_id}\nMonitor the Tests tab for results.`);
      fetchDashboardData();
    } catch (error: any) {
      alert(`Failed to start security scan: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestRunning(false);
    }
  };

  const runCrashSimulation = async (crashType: string) => {
    if (!targetUrl) {
      alert('Please enter target URL');
      return;
    }

    try {
      setTestRunning(true);
      const response = await apiClient.post('/api/v1/advanced-monitoring/tests/crash', {
        target_url: targetUrl,
        crash_type: crashType,
        duration_seconds: 30,
        intensity: 5
      });

      alert(`Crash simulation started: ${response.test_id}\nMonitor system metrics and alerts.`);
      fetchDashboardData();
    } catch (error: any) {
      alert(`Failed to start crash simulation: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestRunning(false);
    }
  };

  const triggerRemediation = async (alertId: string) => {
    try {
      const response = await apiClient.post(`/api/v1/advanced-monitoring/remediate/${alertId}`);
      alert(`Remediation started for alert ${alertId}`);
      fetchDashboardData();
    } catch (error: any) {
      alert(`Failed to trigger remediation: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'critical': return '#dc2626';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>
          <div className="loading-spinner"></div>
          <p>Loading monitoring dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>
          <span style={{ fontSize: '40px' }}>🛡️</span>
          Security & Performance Monitoring
        </h1>
        <p style={styles.subtitle}>
          Real-time monitoring, load testing, security scanning, and auto-remediation
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={styles.tabContainer}>
        {(['overview', 'tests', 'alerts', 'remediation'] as const).map(tab => (
          <button
            key={tab}
            style={{
              ...styles.tab,
              ...(selectedTab === tab ? styles.tabActive : {})
            }}
            onClick={() => setSelectedTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
        <label style={styles.autoRefreshLabel}>
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
          />
          Auto-refresh (10s)
        </label>
      </div>

      {/* Overview Tab */}
      {selectedTab === 'overview' && summary && (
        <>
          {/* System Health Cards */}
          <div style={styles.cardGrid}>
            <div style={styles.card} className="glass-card">
              <div style={styles.cardIcon}>💻</div>
              <div style={styles.cardTitle}>CPU Usage</div>
              <div style={styles.cardValue}>{summary.system_health.cpu_percent.toFixed(1)}%</div>
              <div style={styles.progressBar}>
                <div
                  style={{
                    ...styles.progressFill,
                    width: `${summary.system_health.cpu_percent}%`,
                    backgroundColor: summary.system_health.cpu_percent > 80 ? '#dc2626' : '#10b981'
                  }}
                />
              </div>
            </div>

            <div style={styles.card} className="glass-card">
              <div style={styles.cardIcon}>🧠</div>
              <div style={styles.cardTitle}>Memory Usage</div>
              <div style={styles.cardValue}>{summary.system_health.memory_percent.toFixed(1)}%</div>
              <div style={styles.progressBar}>
                <div
                  style={{
                    ...styles.progressFill,
                    width: `${summary.system_health.memory_percent}%`,
                    backgroundColor: summary.system_health.memory_percent > 80 ? '#dc2626' : '#10b981'
                  }}
                />
              </div>
            </div>

            <div style={styles.card} className="glass-card">
              <div style={styles.cardIcon}>💾</div>
              <div style={styles.cardTitle}>Disk Usage</div>
              <div style={styles.cardValue}>{summary.system_health.disk_percent.toFixed(1)}%</div>
              <div style={styles.progressBar}>
                <div
                  style={{
                    ...styles.progressFill,
                    width: `${summary.system_health.disk_percent}%`,
                    backgroundColor: summary.system_health.disk_percent > 90 ? '#dc2626' : '#10b981'
                  }}
                />
              </div>
            </div>

            <div style={styles.card} className="glass-card">
              <div style={styles.cardIcon}>🔄</div>
              <div style={styles.cardTitle}>Active Threads</div>
              <div style={styles.cardValue}>{summary.system_health.active_threads}</div>
              <div style={styles.cardSubtext}>threads</div>
            </div>
          </div>

          {/* Alerts Summary */}
          <div style={styles.alertsSummary} className="glass-card">
            <h3 style={styles.sectionTitle}>🚨 Active Alerts</h3>
            <div style={styles.alertsGrid}>
              <div style={{ ...styles.alertBadge, backgroundColor: '#dc2626' }}>
                <div style={styles.alertBadgeCount}>{summary.alerts.critical}</div>
                <div style={styles.alertBadgeLabel}>Critical</div>
              </div>
              <div style={{ ...styles.alertBadge, backgroundColor: '#ea580c' }}>
                <div style={styles.alertBadgeCount}>{summary.alerts.high}</div>
                <div style={styles.alertBadgeLabel}>High</div>
              </div>
              <div style={{ ...styles.alertBadge, backgroundColor: '#3b82f6' }}>
                <div style={styles.alertBadgeCount}>{summary.alerts.total_active}</div>
                <div style={styles.alertBadgeLabel}>Total Active</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div style={styles.quickActions} className="glass-card">
            <h3 style={styles.sectionTitle}>⚡ Quick Actions</h3>

            {!targetUrl && (
              <div style={{
                padding: '12px',
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '8px',
                marginBottom: '16px',
                fontSize: '14px',
                color: 'rgba(255, 255, 255, 0.9)'
              }}>
                💡 <strong>Quick Start:</strong> Deploy an app first from the Home page, then return here to test it. The URL will auto-populate.
              </div>
            )}

            <div style={styles.inputGroup}>
              <label style={styles.inputLabel}>Target URL:</label>
              <input
                type="url"
                style={styles.input}
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://your-app.s3-website-us-east-1.amazonaws.com"
              />
            </div>
            <div style={styles.inputGroup}>
              <label style={styles.inputLabel}>S3 Bucket Name:</label>
              <input
                type="text"
                style={styles.input}
                value={bucketName}
                onChange={(e) => setBucketName(e.target.value)}
                placeholder="your-bucket-name"
              />
            </div>
            <div style={styles.buttonGrid}>
              <button
                style={styles.actionButton}
                onClick={runLoadTest}
                disabled={testRunning}
                className="gradient-button"
              >
                🚀 Run Load Test
              </button>
              <button
                style={styles.actionButton}
                onClick={runSecurityScan}
                disabled={testRunning}
                className="gradient-button"
              >
                🔒 Security Scan
              </button>
              <button
                style={styles.actionButton}
                onClick={() => runCrashSimulation('high_load')}
                disabled={testRunning}
                className="gradient-button"
              >
                💥 Test High Load
              </button>
              <button
                style={styles.actionButton}
                onClick={() => runCrashSimulation('cpu_spike')}
                disabled={testRunning}
                className="gradient-button"
              >
                📈 Test CPU Spike
              </button>
            </div>
          </div>
        </>
      )}

      {/* Tests Tab */}
      {selectedTab === 'tests' && (
        <div style={styles.testsContainer}>
          <h3 style={styles.sectionTitle}>🧪 Test Results</h3>
          {tests.length === 0 ? (
            <div style={styles.emptyState}>
              <p style={{ fontSize: '18px', marginBottom: '8px' }}>
                ℹ️ No tests running. Use Quick Actions to start tests.
              </p>
              <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.7)' }}>
                💡 Tip: {targetUrl ? 'Click "Run Load Test" or "Run Security Scan" above' : 'Deploy an app first, then return here to test it'}
              </p>
            </div>
          ) : (
            <div style={styles.testsList}>
              {tests.map(test => (
                <div key={test.test_id} style={styles.testCard} className="glass-card">
                  <div style={styles.testHeader}>
                    <div>
                      <div style={styles.testId}>{test.test_id}</div>
                      <div style={styles.testType}>{test.test_type}</div>
                    </div>
                    <div style={{
                      ...styles.testStatus,
                      backgroundColor: test.status === 'completed' ? '#10b981' :
                                      test.status === 'failed' ? '#dc2626' : '#f59e0b'
                    }}>
                      {test.status}
                    </div>
                  </div>
                  <div style={styles.testDetails}>
                    <div>Started: {new Date(test.started_at).toLocaleString()}</div>
                    {test.duration_seconds && (
                      <div>Duration: {test.duration_seconds.toFixed(2)}s</div>
                    )}
                  </div>
                  {test.metrics && test.status === 'completed' && (
                    <div style={styles.testMetrics}>
                      <pre>{JSON.stringify(test.metrics, null, 2)}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {selectedTab === 'alerts' && (
        <div style={styles.alertsContainer}>
          <h3 style={styles.sectionTitle}>⚠️ Monitoring Alerts</h3>
          {alerts.length === 0 ? (
            <div style={styles.emptyState}>
              <p style={{ fontSize: '18px', marginBottom: '8px' }}>
                ✅ No active alerts. System is healthy!
              </p>
              <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.7)' }}>
                💡 Alerts will appear here when security issues or performance problems are detected
              </p>
            </div>
          ) : (
            <div style={styles.alertsList}>
              {alerts.map(alert => (
                <div
                  key={alert.id}
                  style={{
                    ...styles.alertCard,
                    borderLeftColor: getSeverityColor(alert.severity)
                  }}
                  className="glass-card"
                >
                  <div style={styles.alertCardHeader}>
                    <div style={{
                      ...styles.severityBadge,
                      backgroundColor: getSeverityColor(alert.severity)
                    }}>
                      {alert.severity.toUpperCase()}
                    </div>
                    <div style={styles.alertTitle}>{alert.title}</div>
                  </div>
                  <div style={styles.alertDescription}>{alert.description}</div>
                  <div style={styles.alertMeta}>
                    <div>Resource: {alert.resource}</div>
                    <div>Detected: {new Date(alert.detected_at).toLocaleString()}</div>
                  </div>
                  {alert.remediation_suggested && !alert.auto_remediated && (
                    <button
                      style={styles.remediateButton}
                      onClick={() => triggerRemediation(alert.id)}
                      className="gradient-button"
                    >
                      🔧 Auto-Remediate
                    </button>
                  )}
                  {alert.auto_remediated && (
                    <div style={styles.remediatedBadge}>✅ Auto-remediated</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Remediation Tab */}
      {selectedTab === 'remediation' && summary && (
        <div style={styles.remediationContainer}>
          <h3 style={styles.sectionTitle}>🔧 Auto-Remediation</h3>
          <div style={styles.remediationStats} className="glass-card">
            <div style={styles.statItem}>
              <div style={styles.statValue}>{summary.remediation.total_actions}</div>
              <div style={styles.statLabel}>Total Actions</div>
            </div>
            <div style={styles.statItem}>
              <div style={styles.statValue}>{summary.remediation.success_rate_percent.toFixed(1)}%</div>
              <div style={styles.statLabel}>Success Rate</div>
            </div>
          </div>
          <div style={styles.remediationInfo}>
            <h4>Auto-Remediation Capabilities:</h4>
            <ul style={styles.capabilitiesList}>
              <li>🔄 Automatic service restarts on failures</li>
              <li>📈 Auto-scaling based on load patterns</li>
              <li>🧹 Cache clearing for memory issues</li>
              <li>🔒 Resource isolation for security threats</li>
              <li>📧 Team alerts for critical issues</li>
              <li>⏪ Rollback deployments on errors</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '32px',
    maxWidth: '1400px',
    margin: '0 auto',
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e3a8a 100%)'
  },
  header: {
    marginBottom: '32px',
    textAlign: 'center' as const
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    marginBottom: '12px'
  },
  subtitle: {
    fontSize: '16px',
    color: '#c7d2fe'
  },
  loading: {
    textAlign: 'center' as const,
    padding: '48px',
    color: '#ffffff'
  },
  tabContainer: {
    display: 'flex',
    gap: '8px',
    marginBottom: '24px',
    alignItems: 'center',
    flexWrap: 'wrap' as const
  },
  tab: {
    padding: '12px 24px',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '12px',
    color: '#e0e7ff',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '14px',
    transition: 'all 0.3s ease'
  },
  tabActive: {
    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
    color: 'white',
    borderColor: '#8b5cf6'
  },
  autoRefreshLabel: {
    marginLeft: 'auto',
    color: '#e0e7ff',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '20px',
    marginBottom: '24px'
  },
  card: {
    padding: '24px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    textAlign: 'center' as const
  },
  cardIcon: {
    fontSize: '40px',
    marginBottom: '12px'
  },
  cardTitle: {
    fontSize: '14px',
    color: '#c7d2fe',
    marginBottom: '8px',
    fontWeight: '600'
  },
  cardValue: {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: '12px'
  },
  cardSubtext: {
    fontSize: '12px',
    color: '#a5b4fc',
    marginTop: '4px'
  },
  progressBar: {
    width: '100%',
    height: '8px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  progressFill: {
    height: '100%',
    transition: 'width 0.3s ease',
    borderRadius: '4px'
  },
  alertsSummary: {
    padding: '24px',
    marginBottom: '24px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: '16px'
  },
  alertsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px'
  },
  alertBadge: {
    padding: '20px',
    borderRadius: '12px',
    textAlign: 'center' as const,
    color: 'white'
  },
  alertBadgeCount: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '8px'
  },
  alertBadgeLabel: {
    fontSize: '14px',
    opacity: 0.9
  },
  quickActions: {
    padding: '24px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  inputGroup: {
    marginBottom: '16px'
  },
  inputLabel: {
    display: 'block',
    marginBottom: '8px',
    fontSize: '14px',
    fontWeight: '600',
    color: '#e0e7ff'
  },
  input: {
    width: '100%',
    padding: '12px 16px',
    background: 'rgba(255, 255, 255, 0.15)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '8px',
    color: '#ffffff',
    fontSize: '14px'
  },
  buttonGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '12px',
    marginTop: '16px'
  },
  actionButton: {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
    border: 'none',
    borderRadius: '12px',
    color: 'white',
    fontWeight: '600',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'all 0.3s ease'
  },
  testsContainer: {
    padding: '24px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  testsList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px'
  },
  testCard: {
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  testHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'start',
    marginBottom: '12px'
  },
  testId: {
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#ffffff',
    fontFamily: 'monospace'
  },
  testType: {
    fontSize: '12px',
    color: '#a5b4fc',
    marginTop: '4px'
  },
  testStatus: {
    padding: '4px 12px',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: '600',
    color: 'white'
  },
  testDetails: {
    fontSize: '13px',
    color: '#c7d2fe',
    marginBottom: '12px'
  },
  testMetrics: {
    padding: '12px',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '8px',
    fontSize: '12px',
    color: '#e0e7ff',
    fontFamily: 'monospace',
    overflow: 'auto'
  },
  alertsContainer: {
    padding: '24px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  alertsList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px'
  },
  alertCard: {
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    borderLeft: '4px solid',
    border: '1px solid rgba(255, 255, 255, 0.1)'
  },
  alertCardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '12px'
  },
  severityBadge: {
    padding: '4px 12px',
    borderRadius: '6px',
    fontSize: '11px',
    fontWeight: 'bold',
    color: 'white'
  },
  alertTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#ffffff'
  },
  alertDescription: {
    fontSize: '14px',
    color: '#c7d2fe',
    marginBottom: '12px'
  },
  alertMeta: {
    fontSize: '12px',
    color: '#a5b4fc',
    marginBottom: '12px'
  },
  remediateButton: {
    padding: '8px 16px',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    border: 'none',
    borderRadius: '8px',
    color: 'white',
    fontWeight: '600',
    fontSize: '13px',
    cursor: 'pointer',
    marginTop: '12px'
  },
  remediatedBadge: {
    padding: '8px 16px',
    background: 'rgba(16, 185, 129, 0.2)',
    borderRadius: '8px',
    color: '#10b981',
    fontSize: '13px',
    fontWeight: '600',
    marginTop: '12px',
    display: 'inline-block'
  },
  remediationContainer: {
    padding: '24px',
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  remediationStats: {
    display: 'flex',
    gap: '32px',
    padding: '24px',
    marginBottom: '24px',
    justifyContent: 'center'
  },
  statItem: {
    textAlign: 'center' as const
  },
  statValue: {
    fontSize: '48px',
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: '8px'
  },
  statLabel: {
    fontSize: '14px',
    color: '#c7d2fe'
  },
  remediationInfo: {
    padding: '20px',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    color: '#e0e7ff'
  },
  capabilitiesList: {
    marginTop: '16px',
    paddingLeft: '20px',
    lineHeight: '2'
  },
  emptyState: {
    textAlign: 'center' as const,
    padding: '48px',
    color: '#c7d2fe',
    fontSize: '16px'
  }
};
