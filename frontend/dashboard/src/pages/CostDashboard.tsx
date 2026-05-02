/**
 * Cost Optimization Dashboard Page
 * =================================
 *
 * ENH-004: Cost tracking, analysis, and optimization recommendations.
 *
 * Author: PromptOps Team
 * Date: 2026-04-30
 * Phase: 2 - Cost Optimization
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface CostSummary {
  current_month: {
    total_cost: number;
    currency: string;
    start_date: string;
    end_date: string;
  };
  previous_month: {
    total_cost: number;
    currency: string;
  };
  change: {
    amount: number;
    percent: number;
  };
  forecast: {
    forecasted_cost: number;
    currency: string;
  };
  by_service: Array<{
    service: string;
    cost: number;
  }>;
  by_region: Array<{
    region: string;
    cost: number;
  }>;
  recommendations: Array<{
    id: string;
    title: string;
    description: string;
    potential_savings: number;
    priority: string;
    category: string;
  }>;
  total_potential_savings: number;
}

export const CostDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [costData, setCostData] = useState<CostSummary | null>(null);
  const [selectedView, setSelectedView] = useState<'services' | 'regions'>('services');

  useEffect(() => {
    fetchCostData();
  }, []);

  const fetchCostData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get('/api/v1/cost/summary');
      setCostData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cost data');
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

  const getChangeColor = (percent: number) => {
    if (percent > 10) return '#ef4444'; // red - cost increased
    if (percent < -10) return '#10b981'; // green - cost decreased
    return '#f59e0b'; // yellow - slight change
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return '#ef4444';
      case 'medium':
        return '#f59e0b';
      case 'low':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#6b7280' }}>Loading cost data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px' }}>
        <div style={{
          padding: '16px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#dc2626',
        }}>
          <strong>Error:</strong> {error}
        </div>
        <button
          onClick={fetchCostData}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!costData) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#6b7280' }}>No cost data available</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, color: '#111827', marginBottom: '8px' }}>
          💰 Cost Optimization Dashboard
        </h1>
        <p style={{ fontSize: '14px', color: '#6b7280' }}>
          Track AWS spending, identify cost drivers, and optimize your infrastructure costs
        </p>
      </div>

      {/* Key Metrics Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '20px',
        marginBottom: '32px',
      }}>
        {/* Current Month Cost */}
        <div style={{
          padding: '24px',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Current Month
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: '#111827', marginBottom: '4px' }}>
            {formatCurrency(costData.current_month.total_cost)}
          </div>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>
            {costData.current_month.start_date} to {costData.current_month.end_date}
          </div>
        </div>

        {/* Previous Month Cost */}
        <div style={{
          padding: '24px',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Previous Month
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: '#111827', marginBottom: '4px' }}>
            {formatCurrency(costData.previous_month.total_cost)}
          </div>
          <div style={{
            fontSize: '14px',
            fontWeight: 600,
            color: getChangeColor(costData.change.percent),
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}>
            {costData.change.percent > 0 ? '↑' : '↓'}
            {formatCurrency(Math.abs(costData.change.amount))} ({Math.abs(costData.change.percent).toFixed(1)}%)
          </div>
        </div>

        {/* Forecast */}
        <div style={{
          padding: '24px',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            30-Day Forecast
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: '#111827', marginBottom: '4px' }}>
            {formatCurrency(costData.forecast.forecasted_cost)}
          </div>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>
            Projected spending
          </div>
        </div>

        {/* Potential Savings */}
        <div style={{
          padding: '24px',
          backgroundColor: '#f0fdf4',
          borderRadius: '12px',
          border: '1px solid #bbf7d0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}>
          <div style={{ fontSize: '14px', color: '#15803d', marginBottom: '8px' }}>
            Potential Savings
          </div>
          <div style={{ fontSize: '32px', fontWeight: 700, color: '#16a34a', marginBottom: '4px' }}>
            {formatCurrency(costData.total_potential_savings)}
          </div>
          <div style={{ fontSize: '12px', color: '#15803d' }}>
            {costData.recommendations.length} recommendations
          </div>
        </div>
      </div>

      {/* Cost Breakdown Section */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#111827', margin: 0 }}>
            Cost Breakdown
          </h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setSelectedView('services')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedView === 'services' ? '#3b82f6' : '#ffffff',
                color: selectedView === 'services' ? '#ffffff' : '#374151',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              By Service
            </button>
            <button
              onClick={() => setSelectedView('regions')}
              style={{
                padding: '8px 16px',
                backgroundColor: selectedView === 'regions' ? '#3b82f6' : '#ffffff',
                color: selectedView === 'regions' ? '#ffffff' : '#374151',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              By Region
            </button>
          </div>
        </div>

        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          overflow: 'hidden',
        }}>
          {selectedView === 'services' ? (
            <div>
              {/* Services List */}
              {costData.by_service.slice(0, 10).map((service, index) => {
                const percentage = (service.cost / costData.current_month.total_cost) * 100;
                return (
                  <div
                    key={index}
                    style={{
                      padding: '16px 20px',
                      borderBottom: index < 9 ? '1px solid #f3f4f6' : 'none',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: 500, color: '#111827', marginBottom: '4px' }}>
                        {service.service}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          width: '200px',
                          height: '6px',
                          backgroundColor: '#e5e7eb',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${percentage}%`,
                            height: '100%',
                            backgroundColor: '#3b82f6',
                          }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>
                          {percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div style={{ fontSize: '16px', fontWeight: 600, color: '#111827' }}>
                      {formatCurrency(service.cost)}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div>
              {/* Regions List */}
              {costData.by_region.slice(0, 10).map((region, index) => {
                const percentage = (region.cost / costData.current_month.total_cost) * 100;
                return (
                  <div
                    key={index}
                    style={{
                      padding: '16px 20px',
                      borderBottom: index < 9 ? '1px solid #f3f4f6' : 'none',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: 500, color: '#111827', marginBottom: '4px' }}>
                        {region.region}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                          width: '200px',
                          height: '6px',
                          backgroundColor: '#e5e7eb',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${percentage}%`,
                            height: '100%',
                            backgroundColor: '#8b5cf6',
                          }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#6b7280' }}>
                          {percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div style={{ fontSize: '16px', fontWeight: 600, color: '#111827' }}>
                      {formatCurrency(region.cost)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Optimization Recommendations */}
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#111827', marginBottom: '16px' }}>
          💡 Optimization Recommendations
        </h2>
        <div style={{ display: 'grid', gap: '16px' }}>
          {costData.recommendations.map((rec) => (
            <div
              key={rec.id}
              style={{
                padding: '20px',
                backgroundColor: '#ffffff',
                borderRadius: '12px',
                border: '1px solid #e5e7eb',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#111827', margin: 0 }}>
                      {rec.title}
                    </h3>
                    <span style={{
                      padding: '2px 8px',
                      backgroundColor: getPriorityColor(rec.priority) + '20',
                      color: getPriorityColor(rec.priority),
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                    }}>
                      {rec.priority}
                    </span>
                    <span style={{
                      padding: '2px 8px',
                      backgroundColor: '#f3f4f6',
                      color: '#6b7280',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 500,
                    }}>
                      {rec.category}
                    </span>
                  </div>
                  <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                    {rec.description}
                  </p>
                </div>
                <div style={{ textAlign: 'right', marginLeft: '20px' }}>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                    Potential Savings
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: 700, color: '#16a34a' }}>
                    {formatCurrency(rec.potential_savings)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#15803d' }}>
                    per month
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
