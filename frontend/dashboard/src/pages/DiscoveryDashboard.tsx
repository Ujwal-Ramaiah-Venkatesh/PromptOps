/**
 * Discovery Dashboard
 * ENHANCEMENT-003: AWS resource scanning and onboarding
 *
 * Features:
 * - Start discovery scans across AWS accounts
 * - View scan progress and results
 * - Review inferred environment/project/owner tags
 * - Visualize dependency graph
 * - Bulk import discovered resources
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import './PremiumWorkflows.css';

interface ScanStatus {
  scan_id: string;
  status: 'running' | 'completed' | 'failed';
  total_resources: number;
  progress_percent: number;
  started_at: string;
  completed_at?: string;
  error?: string;
}

interface DiscoveredResource {
  resource_id: string;
  resource_type: string;
  name: string;
  region: string;
  inferred_environment?: string;
  inferred_project?: string;
  inferred_owner?: string;
  confidence_score: number;
  tags: Record<string, string>;
}

interface ScanReport {
  scan_id: string;
  total_resources: number;
  by_type: Record<string, number>;
  by_region: Record<string, number>;
  by_environment: Record<string, number>;
  resources: DiscoveredResource[];
  coverage: {
    tagged_count: number;
    untagged_count: number;
    inferred_count: number;
    high_confidence_count: number;
  };
  patterns: {
    tag_consistency: number;
    naming_conventions: string[];
  };
}

export const DiscoveryDashboard: React.FC = () => {
  const [currentScan, setCurrentScan] = useState<ScanStatus | null>(null);
  const [scanReport, setScanReport] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [regions, setRegions] = useState<string[]>(['us-east-1']);
  const [resourceTypes, setResourceTypes] = useState<string[]>([
    'ec2_instance',
    'rds_instance',
    's3_bucket',
    'vpc',
    'subnet',
    'security_group'
  ]);
  const [selectedResources, setSelectedResources] = useState<Set<string>>(new Set());
  const [activeView, setActiveView] = useState<'scan' | 'results' | 'import'>('scan');

  // Poll scan status
  useEffect(() => {
    if (!currentScan || currentScan.status !== 'running') return;

    const interval = setInterval(async () => {
      try {
        const status = await apiClient.get<ScanStatus>(
          `/api/v1/discovery/scan/${currentScan.scan_id}`
        );
        setCurrentScan(status);

        if (status.status === 'completed') {
          loadScanReport(status.scan_id);
        }
      } catch (err: any) {
        console.error('Poll error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [currentScan]);

  const startScan = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.post<ScanStatus>('/api/v1/discovery/scan', {
        regions,
        resource_types: resourceTypes
      });

      setCurrentScan(response);
      setActiveView('results');
    } catch (err: any) {
      setError(err.message || 'Failed to start scan');
      console.error('Scan error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadScanReport = async (scanId: string) => {
    try {
      const report = await apiClient.get<ScanReport>(
        `/api/v1/discovery/report/${scanId}`
      );
      setScanReport(report);
    } catch (err: any) {
      setError(err.message || 'Failed to load scan report');
      console.error('Report error:', err);
    }
  };

  const importResources = async () => {
    if (selectedResources.size === 0) {
      alert('Please select at least one resource to import');
      return;
    }

    if (!confirm(`Import ${selectedResources.size} resources into Terraform?`)) {
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.post('/api/v1/discovery/import', {
        scan_id: currentScan?.scan_id,
        resource_ids: Array.from(selectedResources),
        auto_apply: false
      });

      alert(`Successfully imported ${selectedResources.size} resources!`);
      setSelectedResources(new Set());
    } catch (err: any) {
      setError(err.message || 'Failed to import resources');
      console.error('Import error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleResourceSelection = (resourceId: string) => {
    const newSet = new Set(selectedResources);
    if (newSet.has(resourceId)) {
      newSet.delete(resourceId);
    } else {
      newSet.add(resourceId);
    }
    setSelectedResources(newSet);
  };

  const selectAll = () => {
    if (scanReport) {
      setSelectedResources(new Set(scanReport.resources.map(r => r.resource_id)));
    }
  };

  const clearSelection = () => {
    setSelectedResources(new Set());
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return '#34a853';
    if (confidence >= 0.7) return '#f9ab00';
    return '#ea4335';
  };

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div className="workflow-eyebrow">Discovery & Onboarding</div>
        <h1 className="workflow-title">Scan AWS and onboard existing resources fast</h1>
        <p className="workflow-subtitle">Read-only scan, resource inference, and guided Terraform import.</p>
      </header>

      <section className="workflow-onboarding">
        <h3>Recommended Flow</h3>
        <p>Run these steps in order for clean onboarding.</p>
        <div className="workflow-onboarding-grid">
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">1. Configure scan scope</div>
            <div className="workflow-step-card-text">Select regions and resource types to avoid noisy results.</div>
          </div>
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">2. Review inferred metadata</div>
            <div className="workflow-step-card-text">Check confidence before selecting resources for import.</div>
          </div>
          <div className="workflow-step-card">
            <div className="workflow-step-card-title">3. Import in batches</div>
            <div className="workflow-step-card-text">Start small, validate outputs, then continue with remaining resources.</div>
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
        {(['scan', 'results', 'import'] as const).map(view => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`workflow-tab ${activeView === view ? 'is-active' : ''}`}
          >
            {view === 'scan' ? 'Scan Setup' : view === 'results' ? 'Scan Results' : 'Import'}
          </button>
        ))}
      </div>

      {activeView === 'scan' && (
        <section className="workflow-card">
          <h2>Configure Discovery Scan</h2>
          <div className="workflow-card-subtitle">Discovery is read-only and does not modify AWS resources.</div>

          <div style={{ marginTop: '16px' }}>
            <label className="workflow-inline-label">AWS Regions</label>
            <div className="workflow-chip-grid">
              {['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'].map(region => (
                <label key={region} className="workflow-chip" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={regions.includes(region)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setRegions([...regions, region]);
                      } else {
                        setRegions(regions.filter(r => r !== region));
                      }
                    }}
                  />
                  {region}
                </label>
              ))}
            </div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <label className="workflow-inline-label">Resource Types</label>
            <div className="workflow-chip-grid">
              {[
                { value: 'ec2_instance', label: 'EC2' },
                { value: 'rds_instance', label: 'RDS' },
                { value: 's3_bucket', label: 'S3' },
                { value: 'vpc', label: 'VPC' },
                { value: 'subnet', label: 'Subnet' },
                { value: 'security_group', label: 'Security Group' }
              ].map(type => (
                <label key={type.value} className="workflow-chip" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={resourceTypes.includes(type.value)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setResourceTypes([...resourceTypes, type.value]);
                      } else {
                        setResourceTypes(resourceTypes.filter(t => t !== type.value));
                      }
                    }}
                  />
                  {type.label}
                </label>
              ))}
            </div>
          </div>

          <div className="workflow-actions" style={{ marginTop: '20px' }}>
            <button
              onClick={startScan}
              disabled={loading || regions.length === 0 || resourceTypes.length === 0}
              className="workflow-btn workflow-btn-primary"
            >
              {loading ? 'Starting Scan...' : 'Start Discovery Scan'}
            </button>
          </div>
        </section>
      )}

      {activeView === 'results' && (
        <section>
          {currentScan && (
            <article className="workflow-card">
              <h2>Current Scan</h2>
              <div className="workflow-card-subtitle">
                Status: <strong>{currentScan.status.toUpperCase()}</strong> · {currentScan.total_resources} resources discovered
              </div>
              <div className="workflow-card-subtitle">Started: {new Date(currentScan.started_at).toLocaleString()}</div>
              {currentScan.status === 'running' && (
                <div style={{ marginTop: '10px' }}>
                  <div style={{ height: '8px', borderRadius: '8px', background: '#e2e8f0', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${currentScan.progress_percent}%`,
                        height: '100%',
                        transition: 'width 0.3s',
                        background: 'linear-gradient(90deg, #0ea5e9 0%, #0f766e 100%)'
                      }}
                    />
                  </div>
                  <div style={{ marginTop: '6px', fontSize: '12px', color: '#475569' }}>{currentScan.progress_percent}% complete</div>
                </div>
              )}
            </article>
          )}

          {scanReport ? (
            <>
              <div className="workflow-stats-grid">
                <article className="workflow-stat">
                  <div className="workflow-stat-label">Total Resources</div>
                  <div className="workflow-stat-value">{scanReport.total_resources}</div>
                </article>
                <article className="workflow-stat">
                  <div className="workflow-stat-label">High Confidence</div>
                  <div className="workflow-stat-value" style={{ color: '#16a34a' }}>{scanReport.coverage.high_confidence_count}</div>
                </article>
                <article className="workflow-stat">
                  <div className="workflow-stat-label">Tagged</div>
                  <div className="workflow-stat-value" style={{ color: '#0284c7' }}>{scanReport.coverage.tagged_count}</div>
                </article>
                <article className="workflow-stat">
                  <div className="workflow-stat-label">Tag Consistency</div>
                  <div className="workflow-stat-value" style={{ color: '#d97706' }}>{(scanReport.patterns.tag_consistency * 100).toFixed(0)}%</div>
                </article>
              </div>

              <article className="workflow-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <h2>Discovered Resources ({scanReport.resources.length})</h2>
                  <div className="workflow-actions">
                    <button onClick={selectAll} className="workflow-btn workflow-btn-secondary">Select All</button>
                    <button onClick={clearSelection} className="workflow-btn workflow-btn-secondary">Clear</button>
                    <button
                      onClick={() => setActiveView('import')}
                      disabled={selectedResources.size === 0}
                      className="workflow-btn workflow-btn-primary"
                    >
                      Import ({selectedResources.size})
                    </button>
                  </div>
                </div>

                <div className="workflow-list" style={{ marginTop: '12px', maxHeight: '520px', overflowY: 'auto' }}>
                  {scanReport.resources.map(resource => {
                    const selected = selectedResources.has(resource.resource_id);
                    return (
                      <article
                        key={resource.resource_id}
                        className={`workflow-list-item ${selected ? 'is-selected' : ''}`}
                        onClick={() => toggleResourceSelection(resource.resource_id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="workflow-item-header">
                          <div>
                            <div className="workflow-item-title">{resource.name || resource.resource_id}</div>
                            <div className="workflow-item-meta">{resource.resource_type} · {resource.region}</div>
                            <div className="workflow-chip-grid" style={{ marginTop: '6px' }}>
                              {resource.inferred_environment && <span className="workflow-chip">Env: {resource.inferred_environment}</span>}
                              {resource.inferred_project && <span className="workflow-chip">Project: {resource.inferred_project}</span>}
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div className="workflow-badge" style={{ background: `${getConfidenceColor(resource.confidence_score)}20`, color: getConfidenceColor(resource.confidence_score) }}>
                              {(resource.confidence_score * 100).toFixed(0)}% confidence
                            </div>
                            <input
                              type="checkbox"
                              checked={selected}
                              onChange={() => toggleResourceSelection(resource.resource_id)}
                              onClick={(e) => e.stopPropagation()}
                              style={{ marginTop: '8px', width: '17px', height: '17px' }}
                            />
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </article>
            </>
          ) : (
            <div className="workflow-empty">No scan report yet. Start a scan from the setup tab.</div>
          )}
        </section>
      )}

      {activeView === 'import' && (
        <section className="workflow-card">
          <h2>Import Selected Resources</h2>
          <div className="workflow-card-subtitle">Generate Terraform-aligned state from discovered infrastructure.</div>
          {selectedResources.size > 0 ? (
            <>
              <p style={{ marginTop: '12px', color: '#475569' }}>
                You selected <strong>{selectedResources.size}</strong> resources for import.
              </p>
              <div className="workflow-actions" style={{ marginTop: '14px' }}>
                <button onClick={importResources} disabled={loading} className="workflow-btn workflow-btn-primary">
                  {loading ? 'Importing...' : `Import ${selectedResources.size} Resources`}
                </button>
                <button onClick={() => setActiveView('results')} className="workflow-btn workflow-btn-secondary">
                  Back to Results
                </button>
              </div>
            </>
          ) : (
            <div className="workflow-empty" style={{ marginTop: '14px' }}>
              No resources selected yet. Pick resources from Scan Results.
            </div>
          )}
        </section>
      )}
    </div>
  );
};
