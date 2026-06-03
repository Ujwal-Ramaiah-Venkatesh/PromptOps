/**
 * Ingestion Workflow UI
 * ENHANCEMENT-002: Import manual AWS changes into Terraform
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import './PremiumWorkflows.css';

interface DriftEvent {
  id: string;
  resource_id: string;
  resource_type: string;
  detected_at: string;
  changes: Array<{
    field: string;
    terraform_value: any;
    aws_value: any;
  }>;
  status: 'pending' | 'imported' | 'reverted' | 'acknowledged';
}

interface ImportedChange {
  import_id: string;
  resource_id: string;
  resource_type: string;
  terraform_code: string;
  imported_at: string;
  imported_by: string;
  status: 'pending' | 'applied' | 'failed' | 'rolled_back';
}

interface ImportPreview {
  terraform_code: string;
  validation_status: 'valid' | 'invalid';
  validation_errors: string[];
  warnings: string[];
  dependencies: string[];
  estimated_resources: number;
}

export const IngestionWorkflow: React.FC = () => {
  const { user } = useAuth();
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [importHistory, setImportHistory] = useState<ImportedChange[]>([]);
  const [selectedDrift, setSelectedDrift] = useState<DriftEvent | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'drift' | 'history'>('drift');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // Mock until backend ingestion endpoints are fully wired.
      setDriftEvents([
        {
          id: 'drift-001',
          resource_id: 'i-abc123',
          resource_type: 'ec2_instance',
          detected_at: new Date().toISOString(),
          changes: [
            {
              field: 'instance_type',
              terraform_value: 't3.medium',
              aws_value: 't3.large'
            },
            {
              field: 'tags',
              terraform_value: { Environment: 'staging' },
              aws_value: { Environment: 'staging', Owner: 'alice@company.com' }
            }
          ],
          status: 'pending'
        }
      ]);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load drift events');
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadImportHistory = async () => {
    try {
      const response = await apiClient.get<{ imports: ImportedChange[] }>('/api/v1/ingestion/history');
      setImportHistory(response.imports);
    } catch (err: any) {
      console.error('History error:', err);
    }
  };

  const previewImport = async (drift: DriftEvent) => {
    try {
      setLoading(true);
      setSelectedDrift(drift);

      const response = await apiClient.post<ImportPreview>('/api/v1/ingestion/preview', {
        resource_id: drift.resource_id,
        resource_type: drift.resource_type,
        aws_state: {}
      });

      setImportPreview(response);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to preview import');
      console.error('Preview error:', err);
    } finally {
      setLoading(false);
    }
  };

  const executeImport = async () => {
    if (!selectedDrift) return;

    if (!confirm('Import this change into Terraform state?')) return;

    try {
      setLoading(true);
      await apiClient.post<ImportedChange>('/api/v1/ingestion/import', {
        resource_id: selectedDrift.resource_id,
        resource_type: selectedDrift.resource_type,
        aws_state: {}
      });

      alert('Successfully imported change!');
      setSelectedDrift(null);
      setImportPreview(null);
      loadData();
      loadImportHistory();
    } catch (err: any) {
      setError(err.message || 'Failed to import change');
      console.error('Import error:', err);
    } finally {
      setLoading(false);
    }
  };

  const rollbackImport = async (importId: string) => {
    if (!confirm('Rollback this imported change? This will restore the previous Terraform state.')) {
      return;
    }

    try {
      setLoading(true);
      await apiClient.post(`/api/v1/ingestion/rollback/${importId}`, {});
      alert('Successfully rolled back import!');
      loadImportHistory();
    } catch (err: any) {
      setError(err.message || 'Failed to rollback');
      console.error('Rollback error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'imported':
      case 'applied': return '#16a34a';
      case 'reverted':
      case 'rolled_back': return '#64748b';
      case 'failed': return '#dc2626';
      case 'acknowledged': return '#0284c7';
      default: return '#64748b';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'imported':
      case 'applied': return '✓';
      case 'reverted':
      case 'rolled_back': return '↶';
      case 'failed': return '✗';
      case 'acknowledged': return '👁';
      default: return '○';
    }
  };

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div className="workflow-eyebrow">Infrastructure Ingestion</div>
        <h1 className="workflow-title">Bring manual AWS changes back to Terraform</h1>
        <p className="workflow-subtitle">Detect drift, preview generated code, import safely, and rollback when needed.</p>
      </header>

      <section className="workflow-onboarding">
        <h3>Safe Import Sequence</h3>
        <p>Use this sequence to avoid state corruption and reduce recovery time.</p>
        <div className="workflow-onboarding-grid">
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">1. Review drift details</div>
            <div className="workflow-step-card-text">Compare Terraform value vs AWS value before import.</div>
          </div>
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">2. Validate generated code</div>
            <div className="workflow-step-card-text">Check validation status, warnings, and dependencies.</div>
          </div>
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">3. Import and monitor history</div>
            <div className="workflow-step-card-text">Use rollback if an imported state needs correction.</div>
          </div>
        </div>
      </section>

      {error && (
        <div className="workflow-alert">
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      <div className="workflow-tabs">
        {(['drift', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              if (tab === 'history') {
                loadImportHistory();
              }
            }}
            className={`workflow-tab ${activeTab === tab ? 'is-active' : ''}`}
          >
            {tab === 'drift' ? 'Drift Queue' : 'Import History'}
          </button>
        ))}
      </div>

      {activeTab === 'drift' && (
        <div className="workflow-two-col">
          <section className="workflow-card" style={{ maxHeight: '720px', overflowY: 'auto' }}>
            <h2>Detected Drift ({driftEvents.length})</h2>
            <div className="workflow-card-subtitle">Select one event to preview import output.</div>

            {driftEvents.length === 0 ? (
              <div className="workflow-empty" style={{ marginTop: '12px' }}>
                No drift detected. Terraform and AWS are in sync.
              </div>
            ) : (
              <div className="workflow-list" style={{ marginTop: '12px' }}>
                {driftEvents.map(drift => {
                  const selected = selectedDrift?.id === drift.id;
                  return (
                    <article
                      key={drift.id}
                      className={`workflow-list-item ${selected ? 'is-selected' : ''}`}
                      onClick={() => previewImport(drift)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="workflow-item-header">
                        <div>
                          <div className="workflow-item-title">{drift.resource_id}</div>
                          <div className="workflow-item-meta">{drift.resource_type} · {drift.changes.length} changes</div>
                          <div className="workflow-item-meta">{new Date(drift.detected_at).toLocaleString()}</div>
                        </div>
                        <div className="workflow-badge" style={{ background: `${getStatusColor(drift.status)}20`, color: getStatusColor(drift.status) }}>
                          {getStatusIcon(drift.status)} {drift.status}
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>

          <section className="workflow-card">
            {selectedDrift ? (
              <>
                <h2>Import Preview</h2>
                <div className="workflow-card-subtitle">{selectedDrift.resource_id} · {selectedDrift.resource_type}</div>

                <div className="workflow-list" style={{ marginTop: '12px' }}>
                  {selectedDrift.changes.map((change, idx) => (
                    <article key={idx} className="workflow-list-item">
                      <div className="workflow-item-title">{change.field}</div>
                      <div className="workflow-two-col" style={{ marginTop: '8px' }}>
                        <div>
                          <div className="workflow-item-meta">Terraform</div>
                          <code className="workflow-chip" style={{ display: 'block', marginTop: '4px', borderRadius: '8px' }}>
                            {JSON.stringify(change.terraform_value)}
                          </code>
                        </div>
                        <div>
                          <div className="workflow-item-meta">AWS</div>
                          <code className="workflow-chip" style={{ display: 'block', marginTop: '4px', borderRadius: '8px' }}>
                            {JSON.stringify(change.aws_value)}
                          </code>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>

                {importPreview && (
                  <>
                    <h3 style={{ marginTop: '14px', marginBottom: '8px', fontSize: '15px' }}>Generated Terraform</h3>
                    <pre className="workflow-code">{importPreview.terraform_code}</pre>

                    <div style={{ marginTop: '10px' }} className="workflow-chip-grid">
                      <span className="workflow-chip" style={{ borderColor: importPreview.validation_status === 'valid' ? '#86efac' : '#fecaca' }}>
                        {importPreview.validation_status === 'valid' ? 'Validation Passed' : 'Validation Failed'}
                      </span>
                      {importPreview.warnings.length > 0 && <span className="workflow-chip">Warnings: {importPreview.warnings.length}</span>}
                      {importPreview.dependencies.length > 0 && <span className="workflow-chip">Dependencies: {importPreview.dependencies.length}</span>}
                    </div>

                    {importPreview.validation_errors.length > 0 && (
                      <div className="workflow-alert" style={{ marginTop: '10px' }}>
                        <span>Validation errors: {importPreview.validation_errors.join(', ')}</span>
                      </div>
                    )}
                  </>
                )}

                <div className="workflow-actions" style={{ marginTop: '14px' }}>
                  <button
                    onClick={executeImport}
                    disabled={loading || importPreview?.validation_status === 'invalid'}
                    className="workflow-btn workflow-btn-primary"
                  >
                    {loading ? 'Importing...' : 'Import Change'}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedDrift(null);
                      setImportPreview(null);
                    }}
                    className="workflow-btn workflow-btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="workflow-empty">Select a drift event to preview the import plan.</div>
            )}
          </section>
        </div>
      )}

      {activeTab === 'history' && (
        <section className="workflow-card">
          <h2>Import History</h2>
          <div className="workflow-card-subtitle">Track imports, review generated code, and rollback when necessary.</div>

          {importHistory.length === 0 ? (
            <div className="workflow-empty" style={{ marginTop: '12px' }}>
              No imports yet. Imported resources will appear here.
            </div>
          ) : (
            <div className="workflow-list" style={{ marginTop: '12px' }}>
              {importHistory.map(item => (
                <article key={item.import_id} className="workflow-list-item">
                  <div className="workflow-item-header">
                    <div>
                      <div className="workflow-item-title">{item.resource_id}</div>
                      <div className="workflow-item-meta">{item.resource_type}</div>
                      <div className="workflow-item-meta">Imported by {item.imported_by} · {new Date(item.imported_at).toLocaleString()}</div>
                    </div>
                    <div className="workflow-actions">
                      <span className="workflow-badge" style={{ background: `${getStatusColor(item.status)}20`, color: getStatusColor(item.status) }}>
                        {getStatusIcon(item.status)} {item.status}
                      </span>
                      {(item.status === 'applied' || item.status === 'pending') && user?.role && ['lead', 'admin'].includes(user.role) && (
                        <button onClick={() => rollbackImport(item.import_id)} className="workflow-btn workflow-btn-danger">
                          Rollback
                        </button>
                      )}
                    </div>
                  </div>

                  <details style={{ marginTop: '10px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 700, color: '#334155' }}>View Terraform Code</summary>
                    <pre className="workflow-code" style={{ marginTop: '8px' }}>{item.terraform_code}</pre>
                  </details>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
};
