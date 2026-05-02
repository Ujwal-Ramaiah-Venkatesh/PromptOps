/**
 * Multi-Cloud Cost Comparison Component
 * ======================================
 *
 * Compare costs across AWS, GCP, and Azure.
 * Phase 3 - Multi-Cloud Support
 *
 * Author: PromptOps Team
 * Date: 2026-05-01
 */

import React, { useState, useEffect } from 'react';

interface CostSummary {
  cloud_provider: string;
  current_month_cost: number;
  previous_month_cost: number;
  month_over_month_change: number;
  forecast_30_day: number;
  currency: string;
  top_services: Array<{
    service_name: string;
    total_cost: number;
    percentage: number;
  }>;
  recommendations_count: number;
}

interface MultiCloudCostSummary {
  total_current_cost: number;
  total_previous_cost: number;
  total_forecast: number;
  currency: string;
  providers: { [key: string]: CostSummary };
  generated_at: string;
}

interface CostComparison {
  service_type: string;
  aws_cost: number;
  gcp_cost: number;
  azure_cost: number;
  cheapest_provider: string;
  savings_opportunity: number;
}

interface Recommendation {
  id: string;
  category: string;
  title: string;
  description: string;
  potential_savings: string;
  priority: 'high' | 'medium' | 'low';
  cloud_provider: string;
  implementation: string;
  effort: string;
}

const CLOUD_COLORS: { [key: string]: string } = {
  aws: '#FF9900',
  gcp: '#4285F4',
  azure: '#0089D6',
};

const CLOUD_ICONS: { [key: string]: string } = {
  aws: '☁️',
  gcp: '🌐',
  azure: '⚡',
};

export const MultiCloudCostComparison: React.FC = () => {
  const [summary, setSummary] = useState<MultiCloudCostSummary | null>(null);
  const [comparisons, setComparisons] = useState<CostComparison[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'comparison' | 'recommendations'>('overview');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch cost summary
      const summaryRes = await fetch('/api/v1/multicloud/cost/summary');
      if (!summaryRes.ok) throw new Error('Failed to fetch cost summary');
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // Fetch cost comparisons
      const comparisonRes = await fetch('/api/v1/multicloud/cost/comparison');
      if (!comparisonRes.ok) throw new Error('Failed to fetch cost comparison');
      const comparisonData = await comparisonRes.json();
      setComparisons(comparisonData);

      // Fetch recommendations
      const recsRes = await fetch('/api/v1/multicloud/cost/recommendations');
      if (!recsRes.ok) throw new Error('Failed to fetch recommendations');
      const recsData = await recsRes.json();
      setRecommendations(recsData);
    } catch (err) {
      console.error('Error fetching cost data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch cost data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#DC2626';
      case 'medium':
        return '#F59E0B';
      case 'low':
        return '#10B981';
      default:
        return '#6B7280';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return '🔥';
      case 'medium':
        return '⚠️';
      case 'low':
        return 'ℹ️';
      default:
        return '📌';
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#666' }}>Loading cost data...</div>
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
          Multi-Cloud Cost Comparison
        </h1>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Analyze and optimize costs across AWS, GCP, and Azure
        </p>
      </div>

      {/* Tabs */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #EEE' }}>
        <div style={{ display: 'flex', gap: '20px' }}>
          {(['overview', 'comparison', 'recommendations'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab)}
              style={{
                padding: '12px 20px',
                border: 'none',
                backgroundColor: 'transparent',
                borderBottom: selectedTab === tab ? '3px solid #000' : '3px solid transparent',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: selectedTab === tab ? '600' : '400',
                textTransform: 'capitalize',
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Tab */}
      {selectedTab === 'overview' && summary && (
        <>
          {/* Total Cost Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '30px' }}>
            <div
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Current Month</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                {formatCurrency(summary.total_current_cost)}
              </div>
              {summary.total_previous_cost > 0 && (
                <div
                  style={{
                    fontSize: '12px',
                    marginTop: '5px',
                    color: summary.total_current_cost > summary.total_previous_cost ? '#DC2626' : '#10B981',
                  }}
                >
                  {summary.total_current_cost > summary.total_previous_cost ? '↑' : '↓'}
                  {' '}
                  {Math.abs(
                    ((summary.total_current_cost - summary.total_previous_cost) / summary.total_previous_cost) * 100
                  ).toFixed(1)}
                  % vs last month
                </div>
              )}
            </div>

            <div
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>30-Day Forecast</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                {formatCurrency(summary.total_forecast)}
              </div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                Projected spend
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
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Active Providers</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                {Object.keys(summary.providers).length}
              </div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                Cloud platforms
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
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Recommendations</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                {recommendations.length}
              </div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                Ways to save
              </div>
            </div>
          </div>

          {/* Cost by Provider */}
          <div
            style={{
              backgroundColor: '#FFF',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              marginBottom: '20px',
            }}
          >
            <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
              Cost by Provider
            </h2>

            {Object.entries(summary.providers).map(([provider, data]) => {
              const percentage = summary.total_current_cost > 0
                ? (data.current_month_cost / summary.total_current_cost) * 100
                : 0;

              return (
                <div key={provider} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontWeight: '600' }}>
                      {CLOUD_ICONS[provider]} {provider.toUpperCase()}
                    </span>
                    <span style={{ fontWeight: '600' }}>
                      {formatCurrency(data.current_month_cost)}
                    </span>
                  </div>

                  <div
                    style={{
                      width: '100%',
                      height: '10px',
                      backgroundColor: '#EEE',
                      borderRadius: '5px',
                      overflow: 'hidden',
                      marginBottom: '8px',
                    }}
                  >
                    <div
                      style={{
                        width: `${percentage}%`,
                        height: '100%',
                        backgroundColor: CLOUD_COLORS[provider],
                      }}
                    />
                  </div>

                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {percentage.toFixed(1)}% of total | {data.recommendations_count} recommendations
                  </div>

                  {/* Top Services */}
                  {data.top_services.length > 0 && (
                    <div style={{ marginTop: '10px', paddingLeft: '15px' }}>
                      <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '5px' }}>
                        Top Services:
                      </div>
                      {data.top_services.slice(0, 3).map((service, idx) => (
                        <div key={idx} style={{ fontSize: '12px', color: '#666', marginBottom: '3px' }}>
                          • {service.service_name}: {formatCurrency(service.total_cost)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Comparison Tab */}
      {selectedTab === 'comparison' && (
        <div
          style={{
            backgroundColor: '#FFF',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
            Service Cost Comparison
          </h2>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #EEE' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Service Type</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>AWS</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>GCP</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>Azure</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600' }}>Cheapest</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>Savings</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((comparison, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #EEE' }}>
                    <td style={{ padding: '12px', fontWeight: '500' }}>{comparison.service_type}</td>
                    <td
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        backgroundColor: comparison.cheapest_provider === 'aws' ? '#FFF9E6' : 'transparent',
                      }}
                    >
                      {formatCurrency(comparison.aws_cost)}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        backgroundColor: comparison.cheapest_provider === 'gcp' ? '#E6F4FF' : 'transparent',
                      }}
                    >
                      {formatCurrency(comparison.gcp_cost)}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        backgroundColor: comparison.cheapest_provider === 'azure' ? '#E6F9FF' : 'transparent',
                      }}
                    >
                      {formatCurrency(comparison.azure_cost)}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span
                        style={{
                          padding: '4px 8px',
                          backgroundColor: CLOUD_COLORS[comparison.cheapest_provider] + '22',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                        }}
                      >
                        {comparison.cheapest_provider}
                      </span>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: '#10B981' }}>
                      {formatCurrency(comparison.savings_opportunity)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations Tab */}
      {selectedTab === 'recommendations' && (
        <div style={{ display: 'grid', gap: '15px' }}>
          {recommendations.map((rec) => (
            <div
              key={rec.id}
              style={{
                backgroundColor: '#FFF',
                padding: '20px',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                borderLeft: `4px solid ${getPriorityColor(rec.priority)}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px' }}>{getPriorityIcon(rec.priority)}</span>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', margin: 0 }}>
                    {rec.title}
                  </h3>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span
                    style={{
                      padding: '4px 8px',
                      backgroundColor: CLOUD_COLORS[rec.cloud_provider] + '22',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                    }}
                  >
                    {rec.cloud_provider}
                  </span>
                  <span
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#F3F4F6',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                    }}
                  >
                    {rec.category}
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
                {rec.description}
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#999', marginBottom: '3px' }}>SAVINGS</div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#10B981' }}>
                    {rec.potential_savings}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#999', marginBottom: '3px' }}>PRIORITY</div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: getPriorityColor(rec.priority) }}>
                    {rec.priority.toUpperCase()}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#999', marginBottom: '3px' }}>EFFORT</div>
                  <div style={{ fontSize: '13px', fontWeight: '600' }}>
                    {rec.effort.toUpperCase()}
                  </div>
                </div>
              </div>

              <div
                style={{
                  padding: '10px',
                  backgroundColor: '#F9FAFB',
                  borderRadius: '4px',
                  fontSize: '13px',
                }}
              >
                <strong>Implementation:</strong> {rec.implementation}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MultiCloudCostComparison;
