/**
 * Anomaly Detection Dashboard
 * ============================
 *
 * Real-time cost anomaly detection and alerting.
 * Phase 4 - Advanced Intelligence
 *
 * Author: PromptOps Team
 * Date: 2026-05-01
 */

import React, { useState, useEffect } from 'react';

interface Anomaly {
  date: string;
  cost: number;
  expected_cost: number;
  deviation: number;
  deviation_pct: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  z_score: number;
  methods: {
    z_score: boolean;
    iqr: boolean;
    ml: boolean;
  };
}

interface AnomalyResults {
  success: boolean;
  total_days: number;
  anomaly_days: number;
  anomaly_rate: number;
  total_cost: number;
  anomaly_cost: number;
  sensitivity: string;
  methods_used: string[];
  anomalies: Anomaly[];
  summary: {
    message: string;
    severity_breakdown: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    recommendation: string;
  };
}

const SEVERITY_COLORS = {
  critical: '#DC2626',
  high: '#F59E0B',
  medium: '#3B82F6',
  low: '#10B981',
};

const SEVERITY_ICONS = {
  critical: '🔥',
  high: '⚠️',
  medium: 'ℹ️',
  low: '✓',
};

export const AnomalyDashboard: React.FC = () => {
  const [results, setResults] = useState<AnomalyResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sensitivity, setSensitivity] = useState<'low' | 'medium' | 'high'>('medium');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');

  // Mock data for demonstration
  const loadAnomalies = async () => {
    setLoading(true);
    setError(null);

    try {
      // In production, fetch from API:
      // const response = await fetch('/api/v1/ml/anomalies/detect', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ cost_data: historicalData, sensitivity })
      // });

      // Mock data for demo
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const mockResults: AnomalyResults = {
        success: true,
        total_days: 90,
        anomaly_days: 8,
        anomaly_rate: 8.9,
        total_cost: 12500.0,
        anomaly_cost: 2100.0,
        sensitivity: sensitivity,
        methods_used: ['z_score', 'iqr', 'ml'],
        anomalies: [
          {
            date: '2026-04-28',
            cost: 285.5,
            expected_cost: 145.0,
            deviation: 140.5,
            deviation_pct: 96.9,
            severity: 'critical',
            z_score: 4.2,
            methods: { z_score: true, iqr: true, ml: true },
          },
          {
            date: '2026-04-25',
            cost: 225.0,
            expected_cost: 140.0,
            deviation: 85.0,
            deviation_pct: 60.7,
            severity: 'high',
            z_score: 3.5,
            methods: { z_score: true, iqr: true, ml: false },
          },
          {
            date: '2026-04-20',
            cost: 65.0,
            expected_cost: 138.0,
            deviation: -73.0,
            deviation_pct: -52.9,
            severity: 'high',
            z_score: 3.1,
            methods: { z_score: true, iqr: false, ml: true },
          },
          {
            date: '2026-04-15',
            cost: 180.0,
            expected_cost: 135.0,
            deviation: 45.0,
            deviation_pct: 33.3,
            severity: 'medium',
            z_score: 2.8,
            methods: { z_score: true, iqr: false, ml: false },
          },
          {
            date: '2026-04-10',
            cost: 175.0,
            expected_cost: 132.0,
            deviation: 43.0,
            deviation_pct: 32.6,
            severity: 'medium',
            z_score: 2.7,
            methods: { z_score: false, iqr: true, ml: true },
          },
        ],
        summary: {
          message: 'Detected 8 anomalies',
          severity_breakdown: {
            critical: 1,
            high: 2,
            medium: 4,
            low: 1,
          },
          recommendation: 'Review high-severity anomalies and identify root causes',
        },
      };

      setResults(mockResults);
    } catch (err) {
      console.error('Error loading anomalies:', err);
      setError(err instanceof Error ? err.message : 'Failed to load anomalies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnomalies();
  }, [sensitivity]);

  const filteredAnomalies =
    results?.anomalies.filter((a) => selectedFilter === 'all' || a.severity === selectedFilter) || [];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  if (loading && !results) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#666' }}>Analyzing cost anomalies...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div
          style={{
            padding: '15px',
            backgroundColor: '#FEE',
            border: '1px solid #FCC',
            borderRadius: '5px',
            color: '#C00',
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Header */}
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>
          Cost Anomaly Detection
        </h1>
        <p style={{ color: '#666', fontSize: '14px' }}>
          ML-powered anomaly detection for cost spikes and unusual patterns
        </p>
      </div>

      {/* Controls */}
      <div
        style={{
          backgroundColor: '#FFF',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
              Detection Sensitivity:
            </label>
            <select
              value={sensitivity}
              onChange={(e) => setSensitivity(e.target.value as any)}
              style={{
                padding: '8px',
                borderRadius: '5px',
                border: '1px solid #CCC',
                width: '200px',
              }}
            >
              <option value="low">Low (fewer alerts)</option>
              <option value="medium">Medium (balanced)</option>
              <option value="high">High (more alerts)</option>
            </select>
          </div>

          <button
            onClick={loadAnomalies}
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: loading ? '#CCC' : '#000',
              color: '#FFF',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: '600',
            }}
          >
            {loading ? 'Analyzing...' : 'Refresh Analysis'}
          </button>
        </div>
      </div>

      {results && (
        <>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
            <div
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Total Days Analyzed</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{results.total_days}</div>
            </div>

            <div
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Anomalies Detected</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#F59E0B' }}>
                {results.anomaly_days}
              </div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                {results.anomaly_rate.toFixed(1)}% of days
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Total Cost</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                {formatCurrency(results.total_cost)}
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Anomaly Cost</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#DC2626' }}>
                {formatCurrency(results.anomaly_cost)}
              </div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                {((results.anomaly_cost / results.total_cost) * 100).toFixed(1)}% of total
              </div>
            </div>
          </div>

          {/* Recommendation Alert */}
          <div
            style={{
              padding: '15px',
              backgroundColor: results.summary.severity_breakdown.critical > 0 ? '#FEE' : '#FFF3CD',
              border: `1px solid ${results.summary.severity_breakdown.critical > 0 ? '#FCC' : '#FFE5A1'}`,
              borderRadius: '5px',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontWeight: '600', marginBottom: '5px' }}>
              {SEVERITY_ICONS[results.summary.severity_breakdown.critical > 0 ? 'critical' : 'high']}{' '}
              {results.summary.message}
            </div>
            <div>{results.summary.recommendation}</div>
          </div>

          {/* Severity Breakdown */}
          <div
            style={{
              backgroundColor: '#FFF',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              marginBottom: '20px',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '15px' }}>
              Severity Breakdown
            </h2>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
              <button
                onClick={() => setSelectedFilter('all')}
                style={{
                  padding: '8px 16px',
                  border: selectedFilter === 'all' ? '2px solid #000' : '1px solid #CCC',
                  borderRadius: '5px',
                  backgroundColor: selectedFilter === 'all' ? '#F0F0F0' : '#FFF',
                  cursor: 'pointer',
                  fontWeight: selectedFilter === 'all' ? '600' : '400',
                }}
              >
                All ({results.anomaly_days})
              </button>
              {Object.entries(results.summary.severity_breakdown).map(([severity, count]) => (
                <button
                  key={severity}
                  onClick={() => setSelectedFilter(severity as any)}
                  style={{
                    padding: '8px 16px',
                    border: selectedFilter === severity ? '2px solid #000' : '1px solid #CCC',
                    borderRadius: '5px',
                    backgroundColor: selectedFilter === severity ? '#F0F0F0' : '#FFF',
                    cursor: 'pointer',
                    fontWeight: selectedFilter === severity ? '600' : '400',
                  }}
                >
                  {SEVERITY_ICONS[severity as keyof typeof SEVERITY_ICONS]}{' '}
                  {severity.charAt(0).toUpperCase() + severity.slice(1)} ({count})
                </button>
              ))}
            </div>
          </div>

          {/* Anomaly List */}
          <div
            style={{
              backgroundColor: '#FFF',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '15px' }}>
              Detected Anomalies ({filteredAnomalies.length})
            </h2>

            <div style={{ display: 'grid', gap: '15px' }}>
              {filteredAnomalies.map((anomaly, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '15px',
                    border: `2px solid ${SEVERITY_COLORS[anomaly.severity]}`,
                    borderRadius: '5px',
                    backgroundColor: '#FAFAFA',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <div>
                      <div style={{ fontSize: '16px', fontWeight: '600' }}>
                        {new Date(anomaly.date).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        Detected by: {Object.entries(anomaly.methods)
                          .filter(([_, v]) => v)
                          .map(([k]) => k)
                          .join(', ')}
                      </div>
                    </div>
                    <div
                      style={{
                        padding: '4px 12px',
                        backgroundColor: SEVERITY_COLORS[anomaly.severity] + '22',
                        color: SEVERITY_COLORS[anomaly.severity],
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600',
                        textTransform: 'uppercase',
                        height: 'fit-content',
                      }}
                    >
                      {SEVERITY_ICONS[anomaly.severity]} {anomaly.severity}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#999', marginBottom: '3px' }}>ACTUAL COST</div>
                      <div style={{ fontSize: '18px', fontWeight: '600' }}>
                        {formatCurrency(anomaly.cost)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#999', marginBottom: '3px' }}>EXPECTED COST</div>
                      <div style={{ fontSize: '18px', fontWeight: '600', color: '#666' }}>
                        {formatCurrency(anomaly.expected_cost)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#999', marginBottom: '3px' }}>DEVIATION</div>
                      <div
                        style={{
                          fontSize: '18px',
                          fontWeight: '600',
                          color: anomaly.deviation > 0 ? '#DC2626' : '#10B981',
                        }}
                      >
                        {anomaly.deviation > 0 ? '+' : ''}
                        {formatCurrency(anomaly.deviation)}
                        <span style={{ fontSize: '14px', marginLeft: '5px' }}>
                          ({anomaly.deviation_pct > 0 ? '+' : ''}
                          {anomaly.deviation_pct.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
                    Z-Score: {anomaly.z_score.toFixed(2)}
                  </div>
                </div>
              ))}

              {filteredAnomalies.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  No anomalies found for the selected filter
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnomalyDashboard;
