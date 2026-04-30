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
import { useAuth } from '../contexts/AuthContext';

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
  const { user } = useAuth();
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
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#1a202c', marginBottom: '8px' }}>
          🔍 Discovery & Onboarding
        </h1>
        <p style={{ color: '#718096', fontSize: '16px' }}>
          Scan AWS accounts, infer context, and import existing infrastructure
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
        {(['scan', 'results', 'import'] as const).map(view => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            style={{
              padding: '12px 24px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeView === view ? '2px solid #667eea' : '2px solid transparent',
              color: activeView === view ? '#667eea' : '#718096',
              fontWeight: activeView === view ? '600' : '400',
              cursor: 'pointer',
              marginBottom: '-2px',
              textTransform: 'capitalize'
            }}
          >
            {view}
          </button>
        ))}
      </div>

      {/* Scan Configuration */}
      {activeView === 'scan' && (
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a202c', marginBottom: '24px' }}>
            Configure Discovery Scan
          </h2>

          {/* Regions */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', marginBottom: '8px', display: 'block' }}>
              AWS Regions
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'].map(region => (
                <label key={region} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
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
                  <span style={{ fontSize: '14px', color: '#4a5568' }}>{region}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Resource Types */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ fontSize: '14px', fontWeight: '600', color: '#4a5568', marginBottom: '8px', display: 'block' }}>
              Resource Types
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {[
                { value: 'ec2_instance', label: 'EC2 Instances' },
                { value: 'rds_instance', label: 'RDS Databases' },
                { value: 's3_bucket', label: 'S3 Buckets' },
                { value: 'vpc', label: 'VPCs' },
                { value: 'subnet', label: 'Subnets' },
                { value: 'security_group', label: 'Security Groups' }
              ].map(type => (
                <label key={type.value} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
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
                  <span style={{ fontSize: '14px', color: '#4a5568' }}>{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Start Button */}
          <button
            onClick={startScan}
            disabled={loading || regions.length === 0 || resourceTypes.length === 0}
            style={{
              padding: '12px 32px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: (loading || regions.length === 0 || resourceTypes.length === 0) ? 'not-allowed' : 'pointer',
              fontWeight: '600',
              fontSize: '16px',
              opacity: (loading || regions.length === 0 || resourceTypes.length === 0) ? 0.5 : 1
            }}
          >
            {loading ? 'Starting Scan...' : '🔍 Start Discovery Scan'}
          </button>

          <div style={{
            marginTop: '24px',
            padding: '16px',
            background: '#eef2ff',
            borderRadius: '8px',
            fontSize: '14px',
            color: '#4c51bf'
          }}>
            💡 <strong>Note:</strong> Discovery scan is read-only and makes no changes to your infrastructure.
            Typical scan takes 5-10 minutes for 250 resources.
          </div>
        </div>
      )}

      {/* Scan Results */}
      {activeView === 'results' && (
        <div>
          {/* Scan Status */}
          {currentScan && (
            <div style={{
              background: 'white',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              marginBottom: '24px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '600', color: '#1a202c', marginBottom: '4px' }}>
                    Scan Status: <span style={{ color: currentScan.status === 'completed' ? '#34a853' : '#f9ab00' }}>
                      {currentScan.status.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '14px', color: '#718096' }}>
                    Discovered {currentScan.total_resources} resources • Started {new Date(currentScan.started_at).toLocaleString()}
                  </div>
                </div>

                {currentScan.status === 'running' && (
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#667eea' }}>
                    {currentScan.progress_percent}%
                  </div>
                )}
              </div>

              {currentScan.status === 'running' && (
                <div style={{
                  marginTop: '16px',
                  height: '8px',
                  background: '#e2e8f0',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${currentScan.progress_percent}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                    transition: 'width 0.5s'
                  }} />
                </div>
              )}
            </div>
          )}

          {/* Report Summary */}
          {scanReport && (
            <>
              {/* Stats Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '16px',
                marginBottom: '24px'
              }}>
                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}>
                  <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Total Resources</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#1a202c' }}>{scanReport.total_resources}</div>
                </div>

                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}>
                  <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>High Confidence</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#34a853' }}>
                    {scanReport.coverage.high_confidence_count}
                  </div>
                </div>

                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}>
                  <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Tagged</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#667eea' }}>
                    {scanReport.coverage.tagged_count}
                  </div>
                </div>

                <div style={{
                  background: 'white',
                  padding: '20px',
                  borderRadius: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                }}>
                  <div style={{ fontSize: '14px', color: '#718096', marginBottom: '4px' }}>Tag Consistency</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f9ab00' }}>
                    {(scanReport.patterns.tag_consistency * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Resources Table */}
              <div style={{
                background: 'white',
                padding: '24px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '16px'
                }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a202c' }}>
                    Discovered Resources ({scanReport.resources.length})
                  </h3>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={selectAll}
                      style={{
                        padding: '6px 12px',
                        background: '#f7fafc',
                        border: '2px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '13px',
                        cursor: 'pointer'
                      }}
                    >
                      Select All
                    </button>
                    <button
                      onClick={clearSelection}
                      style={{
                        padding: '6px 12px',
                        background: '#f7fafc',
                        border: '2px solid #e2e8f0',
                        borderRadius: '6px',
                        fontSize: '13px',
                        cursor: 'pointer'
                      }}
                    >
                      Clear
                    </button>
                    <button
                      onClick={() => setActiveView('import')}
                      disabled={selectedResources.size === 0}
                      style={{
                        padding: '6px 12px',
                        background: selectedResources.size > 0 ? '#667eea' : '#e2e8f0',
                        color: selectedResources.size > 0 ? 'white' : '#a0aec0',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontWeight: '600',
                        cursor: selectedResources.size > 0 ? 'pointer' : 'not-allowed'
                      }}
                    >
                      Import ({selectedResources.size})
                    </button>
                  </div>
                </div>

                <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                  {scanReport.resources.map(resource => (
                    <div
                      key={resource.resource_id}
                      style={{
                        padding: '16px',
                        background: selectedResources.has(resource.resource_id) ? '#eef2ff' : '#f7fafc',
                        borderRadius: '8px',
                        marginBottom: '8px',
                        border: selectedResources.has(resource.resource_id) ? '2px solid #667eea' : '2px solid #e2e8f0',
                        cursor: 'pointer'
                      }}
                      onClick={() => toggleResourceSelection(resource.resource_id)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '15px', fontWeight: '600', color: '#1a202c', marginBottom: '4px' }}>
                            {resource.name || resource.resource_id}
                          </div>
                          <div style={{ fontSize: '13px', color: '#718096', marginBottom: '8px' }}>
                            {resource.resource_type} • {resource.region}
                          </div>

                          {(resource.inferred_environment || resource.inferred_project) && (
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                              {resource.inferred_environment && (
                                <span style={{
                                  padding: '2px 8px',
                                  background: `${getConfidenceColor(resource.confidence_score)}20`,
                                  color: getConfidenceColor(resource.confidence_score),
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  fontWeight: '600'
                                }}>
                                  Environment: {resource.inferred_environment}
                                </span>
                              )}
                              {resource.inferred_project && (
                                <span style={{
                                  padding: '2px 8px',
                                  background: '#e2e8f0',
                                  color: '#4a5568',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  fontWeight: '600'
                                }}>
                                  Project: {resource.inferred_project}
                                </span>
                              )}
                            </div>
                          )}
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <div style={{
                            padding: '4px 8px',
                            background: `${getConfidenceColor(resource.confidence_score)}20`,
                            color: getConfidenceColor(resource.confidence_score),
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '600',
                            marginBottom: '4px'
                          }}>
                            {(resource.confidence_score * 100).toFixed(0)}% confidence
                          </div>
                          <input
                            type="checkbox"
                            checked={selectedResources.has(resource.resource_id)}
                            onChange={() => {}}
                            style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {!currentScan && !scanReport && (
            <div style={{
              background: 'white',
              padding: '60px 32px',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              textAlign: 'center',
              color: '#718096'
            }}>
              No scan results yet. Start a discovery scan to view resources.
            </div>
          )}
        </div>
      )}

      {/* Import Preview */}
      {activeView === 'import' && (
        <div style={{
          background: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#1a202c', marginBottom: '16px' }}>
            Import Preview
          </h2>

          {selectedResources.size > 0 ? (
            <>
              <div style={{ marginBottom: '24px', fontSize: '14px', color: '#4a5568' }}>
                Ready to import <strong>{selectedResources.size}</strong> resources into Terraform state.
                This will generate Terraform code for each resource.
              </div>

              <button
                onClick={importResources}
                disabled={loading}
                style={{
                  padding: '12px 32px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  fontSize: '16px',
                  opacity: loading ? 0.5 : 1
                }}
              >
                {loading ? 'Importing...' : `✓ Import ${selectedResources.size} Resources`}
              </button>
            </>
          ) : (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              color: '#718096'
            }}>
              No resources selected. Go to Results tab and select resources to import.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
