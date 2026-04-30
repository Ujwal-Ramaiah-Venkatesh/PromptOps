/**
 * Ingestion Workflow UI
 * ENHANCEMENT-002: Import manual AWS changes into Terraform
 *
 * Features:
 * - View detected drift events
 * - Preview manual AWS changes
 * - Generate Terraform code from AWS state
 * - Import changes into Terraform state
 * - Rollback imported changes if needed
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

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
      // Note: These endpoints would need to be implemented on backend
      // For now, using mock data
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
      const response = await apiClient.get<{ imports: ImportedChange[] }>(
        '/api/v1/ingestion/history'
      );
      setImportHistory(response.imports);
    } catch (err: any) {
      console.error('History error:', err);
    }
  };

  const previewImport = async (drift: DriftEvent) => {
    try {
      setLoading(true);
      setSelectedDrift(drift);

      const response = await apiClient.post<ImportPreview>(
        '/api/v1/ingestion/preview',
        {
          resource_id: drift.resource_id,
          resource_type: drift.resource_type,
          aws_state: {} // Would include actual AWS state
        }
      );

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

      const response = await apiClient.post<ImportedChange>(
        '/api/v1/ingestion/import',
        {
          resource_id: selectedDrift.resource_id,
          resource_type: selectedDrift.resource_type,
          aws_state: {} // Would include actual AWS state
        }
      );

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
      case 'pending': return '#f9ab00';
      case 'imported':
      case 'applied': return '#34a853';
      case 'reverted':
      case 'rolled_back': return '#718096';
      case 'failed': return '#ea4335';
      case 'acknowledged': return '#667eea';
      default: return '#718096';
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
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#1a202c', marginBottom: '8px' }}>
          📥 Infrastructure Ingestion
        </h1>
        <p style={{ color: '#718096', fontSize: '16px' }}>
          Import manual AWS Console changes into Terraform state
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
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>⚠ {error}</span>
          <button
            onClick={() => setError(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#991b1b',
              cursor: 'pointer',
              fontSize: '18px'
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        borderBottom: '2px solid #e2e8f0'
      }}>
        {(['drift', 'history'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              if (tab === 'history') loadImportHistory();
            }}
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
            {tab === 'drift' ? 'Drift Events' : 'Import History'}
          </button>
        ))}
      </div>

      {/* Drift Events Tab */}
      {activeTab === 'drift' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Drift List */}
          <div style={{
            background: 'white',
            padding: '24px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            maxHeight: '700px',
            overflowY: 'auto'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '16px' }}>
              Detected Drift ({driftEvents.length})
            </h2>

            {driftEvents.length === 0 ? (
              <div style={{
                padding: '40px',
                textAlign: 'center',
                color: '#718096'
              }}>
                No drift detected. Your Terraform state matches AWS reality.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {driftEvents.map(drift => (
                  <div
                    key={drift.id}
                    onClick={() => previewImport(drift)}
                    style={{
                      padding: '16px',
                      background: selectedDrift?.id === drift.id ? '#eef2ff' : '#f7fafc',
                      border: selectedDrift?.id === drift.id ? '2px solid #667eea' : '2px solid #e2e8f0',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      marginBottom: '8px'
                    }}>
                      <div>
                        <div style={{ fontSize: '15px', fontWeight: '600', color: '#1a202c', marginBottom: '4px' }}>
                          {drift.resource_id}
                        </div>
                        <div style={{ fontSize: '13px', color: '#718096' }}>
                          {drift.resource_type}
                        </div>
                      </div>

                      <div style={{
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '600',
                        background: `${getStatusColor(drift.status)}20`,
                        color: getStatusColor(drift.status)
                      }}>
                        {getStatusIcon(drift.status)} {drift.status}
                      </div>
                    </div>

                    <div style={{ fontSize: '13px', color: '#718096', marginBottom: '8px' }}>
                      {drift.changes.length} changes detected
                    </div>

                    <div style={{ fontSize: '12px', color: '#a0aec0' }}>
                      {new Date(drift.detected_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Preview Panel */}
          <div style={{
            background: 'white',
            padding: '24px',
            borderRadius: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            {selectedDrift ? (
              <>
                <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c', marginBottom: '16px' }}>
                  Import Preview
                </h2>

                {/* Changes Summary */}
                <div style={{ marginBottom: '24px' }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', marginBottom: '12px' }}>
                    Detected Changes:
                  </div>

                  {selectedDrift.changes.map((change, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '12px',
                        background: '#f7fafc',
                        borderRadius: '6px',
                        marginBottom: '8px'
                      }}
                    >
                      <div style={{ fontSize: '13px', fontWeight: '600', color: '#1a202c', marginBottom: '4px' }}>
                        {change.field}
                      </div>
                      <div style={{ fontSize: '12px', color: '#718096', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                        <div>
                          <div style={{ fontWeight: '600', marginBottom: '2px' }}>Terraform:</div>
                          <code style={{ fontSize: '11px', background: '#fef2f2', padding: '2px 4px', borderRadius: '3px' }}>
                            {JSON.stringify(change.terraform_value)}
                          </code>
                        </div>
                        <div>
                          <div style={{ fontWeight: '600', marginBottom: '2px' }}>AWS:</div>
                          <code style={{ fontSize: '11px', background: '#f0fdf4', padding: '2px 4px', borderRadius: '3px' }}>
                            {JSON.stringify(change.aws_value)}
                          </code>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Generated Terraform Code */}
                {importPreview && (
                  <>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', marginBottom: '12px' }}>
                      Generated Terraform:
                    </div>

                    <pre style={{
                      padding: '16px',
                      background: '#1a202c',
                      color: '#e2e8f0',
                      borderRadius: '8px',
                      fontSize: '12px',
                      overflowX: 'auto',
                      marginBottom: '16px',
                      fontFamily: 'monospace'
                    }}>
                      {importPreview.terraform_code}
                    </pre>

                    {/* Validation Status */}
                    <div style={{
                      padding: '12px',
                      background: importPreview.validation_status === 'valid' ? '#f0fdf4' : '#fef2f2',
                      border: `1px solid ${importPreview.validation_status === 'valid' ? '#86efac' : '#fecaca'}`,
                      borderRadius: '8px',
                      marginBottom: '16px'
                    }}>
                      <div style={{
                        fontSize: '13px',
                        fontWeight: '600',
                        color: importPreview.validation_status === 'valid' ? '#166534' : '#991b1b',
                        marginBottom: '4px'
                      }}>
                        {importPreview.validation_status === 'valid' ? '✓ Validation Passed' : '✗ Validation Failed'}
                      </div>
                      {importPreview.validation_errors.length > 0 && (
                        <div style={{ fontSize: '12px', color: '#991b1b' }}>
                          {importPreview.validation_errors.join(', ')}
                        </div>
                      )}
                      {importPreview.warnings.length > 0 && (
                        <div style={{ fontSize: '12px', color: '#f9ab00', marginTop: '4px' }}>
                          ⚠ {importPreview.warnings.join(', ')}
                        </div>
                      )}
                    </div>

                    {/* Dependencies */}
                    {importPreview.dependencies.length > 0 && (
                      <div style={{
                        padding: '12px',
                        background: '#eef2ff',
                        borderRadius: '8px',
                        marginBottom: '16px'
                      }}>
                        <div style={{ fontSize: '13px', fontWeight: '600', color: '#4c51bf', marginBottom: '4px' }}>
                          Dependencies:
                        </div>
                        <div style={{ fontSize: '12px', color: '#4c51bf' }}>
                          {importPreview.dependencies.join(', ')}
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                  <button
                    onClick={executeImport}
                    disabled={loading || (importPreview?.validation_status === 'invalid')}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: (loading || importPreview?.validation_status === 'invalid') ? 'not-allowed' : 'pointer',
                      fontWeight: '600',
                      fontSize: '14px',
                      opacity: (loading || importPreview?.validation_status === 'invalid') ? 0.5 : 1
                    }}
                  >
                    {loading ? 'Importing...' : '✓ Import Change'}
                  </button>

                  <button
                    onClick={() => {
                      setSelectedDrift(null);
                      setImportPreview(null);
                    }}
                    style={{
                      flex: 1,
                      padding: '12px',
                      background: '#f7fafc',
                      color: '#4a5568',
                      border: '2px solid #e2e8f0',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontWeight: '600',
                      fontSize: '14px'
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div style={{
                padding: '60px 20px',
                textAlign: 'center',
                color: '#718096'
              }}>
                Select a drift event to preview import
              </div>
            )}
          </div>
        </div>
      )}

      {/* Import History Tab */}
      {activeTab === 'history' && (
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a202c', marginBottom: '24px' }}>
            Import History
          </h2>

          {importHistory.length === 0 ? (
            <div style={{
              padding: '60px 20px',
              textAlign: 'center',
              color: '#718096'
            }}>
              No imports yet. Import drift events to see history here.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {importHistory.map(item => (
                <div
                  key={item.import_id}
                  style={{
                    padding: '20px',
                    background: '#f7fafc',
                    borderRadius: '8px',
                    border: '2px solid #e2e8f0'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '12px'
                  }}>
                    <div>
                      <div style={{ fontSize: '16px', fontWeight: '600', color: '#1a202c', marginBottom: '4px' }}>
                        {item.resource_id}
                      </div>
                      <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>
                        {item.resource_type}
                      </div>
                      <div style={{ fontSize: '13px', color: '#a0aec0' }}>
                        Imported by {item.imported_by} • {new Date(item.imported_at).toLocaleString()}
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <div style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '600',
                        background: `${getStatusColor(item.status)}20`,
                        color: getStatusColor(item.status)
                      }}>
                        {getStatusIcon(item.status)} {item.status}
                      </div>

                      {(item.status === 'applied' || item.status === 'pending') && user?.role && ['lead', 'admin'].includes(user.role) && (
                        <button
                          onClick={() => rollbackImport(item.import_id)}
                          style={{
                            padding: '6px 12px',
                            background: '#fef2f2',
                            border: '1px solid #fecaca',
                            borderRadius: '6px',
                            color: '#991b1b',
                            cursor: 'pointer',
                            fontSize: '12px',
                            fontWeight: '600'
                          }}
                        >
                          Rollback
                        </button>
                      )}
                    </div>
                  </div>

                  <details style={{ fontSize: '13px', color: '#4a5568' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: '600', marginBottom: '8px' }}>
                      View Terraform Code
                    </summary>
                    <pre style={{
                      padding: '12px',
                      background: '#1a202c',
                      color: '#e2e8f0',
                      borderRadius: '6px',
                      fontSize: '11px',
                      overflowX: 'auto',
                      fontFamily: 'monospace'
                    }}>
                      {item.terraform_code}
                    </pre>
                  </details>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
