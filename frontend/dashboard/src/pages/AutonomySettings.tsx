/**
 * Autonomy Settings Dashboard
 * ENHANCEMENT-001: Configure risk-based auto-execution tiers
 *
 * Features:
 * - View and toggle autonomy tiers (LOW/MEDIUM/HIGH/CRITICAL)
 * - Browse action types and their risk levels
 * - View auto-execution history
 * - Statistics and metrics
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

interface AutonomyTier {
  risk_level: string;
  auto_execute: boolean;
  requires_2fa: boolean;
  can_modify: boolean;
}

interface ActionType {
  action_type: string;
  base_risk: string;
  description: string;
  example: string;
  total_executed: number;
}

interface AutonomySettings {
  user_email: string;
  tiers: AutonomyTier[];
  last_modified: string;
}

interface Stats {
  total_actions: number;
  auto_executed: number;
  manual_approved: number;
  blocked: number;
  auto_execution_rate: number;
  top_auto_executed_actions: Array<{action_type: string; count: number}>;
}

export const AutonomySettings: React.FC = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<AutonomySettings | null>(null);
  const [actionTypes, setActionTypes] = useState<ActionType[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'settings' | 'actions' | 'history'>('settings');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsData, actionsData, statsData] = await Promise.all([
        apiClient.get<AutonomySettings>('/api/v1/autonomy/settings'),
        apiClient.get<{action_types: ActionType[]}>('/api/v1/autonomy/action-types'),
        apiClient.get<Stats>('/api/v1/autonomy/stats')
      ]);

      setSettings(settingsData);
      setActionTypes(actionsData.action_types);
      setStats(statsData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load autonomy settings');
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleTier = async (riskLevel: string, currentValue: boolean) => {
    if (!settings) return;

    try {
      setSaving(true);
      const updatedSettings = await apiClient.put<AutonomySettings>(
        '/api/v1/autonomy/settings',
        {
          tiers: settings.tiers.map(tier =>
            tier.risk_level === riskLevel
              ? { ...tier, auto_execute: !currentValue }
              : tier
          )
        }
      );

      setSettings(updatedSettings);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to update settings');
      console.error('Update error:', err);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = async () => {
    if (!confirm('Reset all autonomy settings to defaults?')) return;

    try {
      setSaving(true);
      const defaultSettings = await apiClient.post<AutonomySettings>(
        '/api/v1/autonomy/reset',
        {}
      );

      setSettings(defaultSettings);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to reset settings');
      console.error('Reset error:', err);
    } finally {
      setSaving(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk.toUpperCase()) {
      case 'LOW': return '#34a853';
      case 'MEDIUM': return '#f9ab00';
      case 'HIGH': return '#ea4335';
      case 'CRITICAL': return '#8b0000';
      default: return '#718096';
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk.toUpperCase()) {
      case 'LOW': return '✓';
      case 'MEDIUM': return '⚠';
      case 'HIGH': return '⚡';
      case 'CRITICAL': return '🔒';
      default: return '○';
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        color: '#718096'
      }}>
        Loading autonomy settings...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#1a202c', marginBottom: '8px' }}>
          ⚙️ Autonomy Settings
        </h1>
        <p style={{ color: '#718096', fontSize: '16px' }}>
          Configure risk-based auto-execution to reduce approval fatigue
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{
          padding: '16px',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#991b1b',
          marginBottom: '24px'
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '32px'
        }}>
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Total Actions</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#1a202c' }}>{stats.total_actions}</div>
          </div>

          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Auto-Executed</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#34a853' }}>{stats.auto_executed}</div>
          </div>

          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Manual Approved</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#f9ab00' }}>{stats.manual_approved}</div>
          </div>

          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Auto Rate</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#667eea' }}>
              {stats.auto_execution_rate.toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        borderBottom: '2px solid #e2e8f0'
      }}>
        {(['settings', 'actions', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '12px 24px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === tab ? '2px solid #667eea' : '2px solid transparent',
              color: activeTab === tab ? '#667eea' : '#718096',
              fontWeight: activeTab === tab ? '600' : '400',
              cursor: 'pointer',
              marginBottom: '-2px',
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Settings Tab */}
      {activeTab === 'settings' && settings && (
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '24px'
          }}>
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a202c', marginBottom: '4px' }}>
                Risk Tier Configuration
              </h2>
              <p style={{ fontSize: '14px', color: '#718096' }}>
                Enable auto-execution for LOW and MEDIUM risk operations
              </p>
            </div>
            <button
              onClick={resetToDefaults}
              disabled={saving}
              style={{
                padding: '8px 16px',
                background: '#f7fafc',
                border: '2px solid #e2e8f0',
                borderRadius: '6px',
                color: '#4a5568',
                cursor: saving ? 'not-allowed' : 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              Reset to Defaults
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {settings.tiers.map(tier => (
              <div
                key={tier.risk_level}
                style={{
                  padding: '20px',
                  background: '#f7fafc',
                  borderRadius: '8px',
                  border: `2px solid ${getRiskColor(tier.risk_level)}20`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '8px',
                    background: `${getRiskColor(tier.risk_level)}20`,
                    color: getRiskColor(tier.risk_level),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '24px',
                    fontWeight: '700'
                  }}>
                    {getRiskIcon(tier.risk_level)}
                  </div>

                  <div>
                    <div style={{
                      fontSize: '18px',
                      fontWeight: '600',
                      color: '#1a202c',
                      marginBottom: '4px'
                    }}>
                      {tier.risk_level} Risk
                    </div>
                    <div style={{ fontSize: '14px', color: '#718096' }}>
                      {tier.requires_2fa && '🔒 Requires 2FA • '}
                      {!tier.can_modify && 'Locked by policy'}
                    </div>
                  </div>
                </div>

                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: tier.can_modify ? 'pointer' : 'not-allowed',
                  opacity: tier.can_modify ? 1 : 0.5
                }}>
                  <span style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568' }}>
                    Auto-Execute
                  </span>
                  <div
                    onClick={() => tier.can_modify && toggleTier(tier.risk_level, tier.auto_execute)}
                    style={{
                      width: '48px',
                      height: '24px',
                      borderRadius: '12px',
                      background: tier.auto_execute ? '#34a853' : '#cbd5e0',
                      position: 'relative',
                      transition: 'background 0.2s'
                    }}
                  >
                    <div style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      background: 'white',
                      position: 'absolute',
                      top: '2px',
                      left: tier.auto_execute ? '26px' : '2px',
                      transition: 'left 0.2s',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }} />
                  </div>
                </label>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: '24px',
            padding: '16px',
            background: '#eef2ff',
            borderRadius: '8px',
            fontSize: '14px',
            color: '#4c51bf'
          }}>
            💡 <strong>Tip:</strong> HIGH and CRITICAL risk actions always require manual approval for safety.
            Enable auto-execution for LOW and MEDIUM to reduce approval requests by ~80%.
          </div>
        </div>
      )}

      {/* Action Types Tab */}
      {activeTab === 'actions' && (
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a202c', marginBottom: '16px' }}>
            Action Types & Risk Levels
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {actionTypes.map(action => (
              <div
                key={action.action_type}
                style={{
                  padding: '16px',
                  background: '#f7fafc',
                  borderRadius: '8px',
                  border: '2px solid #e2e8f0'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '8px'
                }}>
                  <div>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#1a202c',
                      marginBottom: '4px'
                    }}>
                      {action.action_type.replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontSize: '14px', color: '#718096' }}>
                      {action.description}
                    </div>
                  </div>

                  <div style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: '600',
                    background: `${getRiskColor(action.base_risk)}20`,
                    color: getRiskColor(action.base_risk),
                    whiteSpace: 'nowrap'
                  }}>
                    {getRiskIcon(action.base_risk)} {action.base_risk}
                  </div>
                </div>

                <div style={{
                  fontSize: '13px',
                  color: '#718096',
                  fontStyle: 'italic'
                }}>
                  Example: {action.example}
                </div>

                {action.total_executed > 0 && (
                  <div style={{
                    marginTop: '8px',
                    fontSize: '12px',
                    color: '#4a5568'
                  }}>
                    Executed {action.total_executed} times
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a202c', marginBottom: '16px' }}>
            Auto-Execution History
          </h2>

          <div style={{
            padding: '40px',
            textAlign: 'center',
            color: '#718096'
          }}>
            History view coming soon. Will show recent auto-executed actions with timestamps and outcomes.
          </div>
        </div>
      )}
    </div>
  );
};
