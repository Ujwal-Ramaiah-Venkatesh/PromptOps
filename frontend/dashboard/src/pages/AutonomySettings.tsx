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
import './PremiumWorkflows.css';

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
      <div className="workflow-page">
        <div className="workflow-empty">Loading autonomy settings...</div>
      </div>
    );
  }

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div className="workflow-eyebrow">Autonomy Controls</div>
        <h1 className="workflow-title">Risk-based automation with guardrails</h1>
        <p className="workflow-subtitle">
          Decide which actions can run automatically and which always require explicit approval.
        </p>
      </header>

      <section className="workflow-onboarding">
        <h3>How to Configure Safely</h3>
        <p>Use these three steps to avoid risky automation mistakes.</p>
        <div className="workflow-onboarding-grid">
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">1. Enable low-risk first</div>
            <div className="workflow-step-card-text">Start with LOW and MEDIUM tiers to build confidence.</div>
          </div>
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">2. Keep high-risk manual</div>
            <div className="workflow-step-card-text">HIGH and CRITICAL should usually remain approval-gated.</div>
          </div>
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">3. Monitor execution rate</div>
            <div className="workflow-step-card-text">Use stats below to confirm the policy behaves as intended.</div>
          </div>
        </div>
      </section>

      {error && (
        <div className="workflow-alert">
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      {stats && (
        <section className="workflow-stats-grid">
          <article className="workflow-stat">
            <div className="workflow-stat-label">Total Actions</div>
            <div className="workflow-stat-value">{stats.total_actions}</div>
          </article>
          <article className="workflow-stat">
            <div className="workflow-stat-label">Auto Executed</div>
            <div className="workflow-stat-value" style={{ color: '#16a34a' }}>{stats.auto_executed}</div>
          </article>
          <article className="workflow-stat">
            <div className="workflow-stat-label">Manual Approved</div>
            <div className="workflow-stat-value" style={{ color: '#d97706' }}>{stats.manual_approved}</div>
          </article>
          <article className="workflow-stat">
            <div className="workflow-stat-label">Auto Execution Rate</div>
            <div className="workflow-stat-value" style={{ color: '#0284c7' }}>{stats.auto_execution_rate.toFixed(1)}%</div>
          </article>
        </section>
      )}

      <div className="workflow-tabs">
        {(['settings', 'actions', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`workflow-tab ${activeTab === tab ? 'is-active' : ''}`}
          >
            {tab === 'settings' ? 'Tier Settings' : tab === 'actions' ? 'Action Catalog' : 'Execution History'}
          </button>
        ))}
      </div>

      {activeTab === 'settings' && settings && (
        <section className="workflow-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div>
              <h2>Risk Tier Configuration</h2>
              <div className="workflow-card-subtitle">Toggle auto-execution per risk level.</div>
            </div>
            <button onClick={resetToDefaults} disabled={saving} className="workflow-btn workflow-btn-secondary">
              Reset to Defaults
            </button>
          </div>

          <div className="workflow-list" style={{ marginTop: '14px' }}>
            {settings.tiers.map(tier => (
              <article key={tier.risk_level} className="workflow-list-item">
                <div className="workflow-item-header">
                  <div>
                    <div className="workflow-item-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: getRiskColor(tier.risk_level) }}>{getRiskIcon(tier.risk_level)}</span>
                      {tier.risk_level} Risk
                    </div>
                    <div className="workflow-item-meta">
                      {tier.requires_2fa ? 'Requires 2FA' : 'No 2FA required'}
                      {' · '}
                      {tier.can_modify ? 'Editable' : 'Locked by policy'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '13px', color: '#475569', fontWeight: 700 }}>Auto Execute</span>
                    <button
                      aria-label={`Toggle ${tier.risk_level} risk auto execution`}
                      className={`workflow-switch ${tier.auto_execute ? 'is-on' : ''}`}
                      onClick={() => tier.can_modify && toggleTier(tier.risk_level, tier.auto_execute)}
                      disabled={!tier.can_modify || saving}
                    >
                      <span className="workflow-switch-knob" />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'actions' && (
        <section className="workflow-card">
          <h2>Action Catalog by Base Risk</h2>
          <div className="workflow-card-subtitle">Use this to understand what each automation decision affects.</div>
          <div className="workflow-list" style={{ marginTop: '14px' }}>
            {actionTypes.map(action => (
              <article key={action.action_type} className="workflow-list-item">
                <div className="workflow-item-header">
                  <div>
                    <div className="workflow-item-title">{action.action_type.replace(/_/g, ' ')}</div>
                    <div className="workflow-item-meta">{action.description}</div>
                  </div>
                  <div className="workflow-badge" style={{ background: `${getRiskColor(action.base_risk)}20`, color: getRiskColor(action.base_risk) }}>
                    {getRiskIcon(action.base_risk)} {action.base_risk}
                  </div>
                </div>
                <div style={{ marginTop: '8px', fontSize: '13px', color: '#64748b' }}>Example: {action.example}</div>
                {action.total_executed > 0 && (
                  <div style={{ marginTop: '6px', fontSize: '12px', color: '#475569' }}>
                    Executed {action.total_executed} times
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'history' && (
        <section className="workflow-card">
          <h2>Execution History</h2>
          <div className="workflow-card-subtitle">Recent auto-executed actions and outcomes.</div>
          <div className="workflow-empty" style={{ marginTop: '14px' }}>
            History view is coming soon. This section will show who triggered what and when.
          </div>
        </section>
      )}

      <section className="workflow-card">
        <h2>Recommended Policy Baseline</h2>
        <div className="workflow-chip-grid" style={{ marginTop: '10px' }}>
          <span className="workflow-chip">LOW: Auto Execute</span>
          <span className="workflow-chip">MEDIUM: Auto Execute + Optional 2FA</span>
          <span className="workflow-chip">HIGH: Manual Approval</span>
          <span className="workflow-chip">CRITICAL: Manual Approval + 2FA</span>
        </div>
      </section>
    </div>
  );
};
