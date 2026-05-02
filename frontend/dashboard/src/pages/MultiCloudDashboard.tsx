/**
 * Multi-Cloud Dashboard Component
 * ================================
 *
 * Unified dashboard for AWS, GCP, and Azure resources.
 * Phase 3 - Multi-Cloud Support
 *
 * Author: PromptOps Team
 * Date: 2026-05-01
 */

import React, { useState, useEffect } from 'react';
import { useScanUpdates } from '../hooks/useWebSocket';

interface CloudProvider {
  name: string;
  displayName: string;
  color: string;
  icon: string;
}

interface ResourceSummary {
  cloud_provider: string;
  total_resources: number;
  resource_counts: { [key: string]: number };
  regions: string[];
  last_scan?: string;
}

interface MultiCloudSummary {
  total_resources: number;
  providers: { [key: string]: ResourceSummary };
  scan_time: string;
}

interface ScanStatus {
  scan_id: string;
  status: string;
  providers: string[];
  progress: { [key: string]: number };
  started_at: string;
  completed_at?: string;
  total_resources: number;
  errors: string[];
}

const CLOUD_PROVIDERS: CloudProvider[] = [
  { name: 'aws', displayName: 'AWS', color: '#FF9900', icon: '☁️' },
  { name: 'gcp', displayName: 'GCP', color: '#4285F4', icon: '🌐' },
  { name: 'azure', displayName: 'Azure', color: '#0089D6', icon: '⚡' },
];

export const MultiCloudDashboard: React.FC = () => {
  const [summary, setSummary] = useState<MultiCloudSummary | null>(null);
  const [currentScan, setCurrentScan] = useState<ScanStatus | null>(null);
  const [selectedProviders, setSelectedProviders] = useState<string[]>(['all']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket for real-time scan updates
  const scanUpdates = useScanUpdates(currentScan?.scan_id || null);

  // Fetch multi-cloud summary
  const fetchSummary = async () => {
    try {
      const response = await fetch('/api/v1/multicloud/summary');
      if (!response.ok) throw new Error('Failed to fetch summary');
      const data = await response.json();
      setSummary(data);
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch summary');
    }
  };

  // Start multi-cloud scan
  const startScan = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/multicloud/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ providers: selectedProviders }),
      });

      if (!response.ok) throw new Error('Failed to start scan');

      const data = await response.json();
      setCurrentScan({
        scan_id: data.scan_id,
        status: data.status,
        providers: data.providers,
        progress: data.providers.reduce((acc: any, p: string) => ({ ...acc, [p]: 0 }), {}),
        started_at: new Date().toISOString(),
        total_resources: 0,
        errors: [],
      });
    } catch (err) {
      console.error('Error starting scan:', err);
      setError(err instanceof Error ? err.message : 'Failed to start scan');
    } finally {
      setLoading(false);
    }
  };

  // Update scan status from WebSocket
  useEffect(() => {
    if (scanUpdates && currentScan) {
      if (scanUpdates.status === 'completed') {
        fetchSummary();
        setCurrentScan(null);
      } else if (scanUpdates.provider) {
        setCurrentScan({
          ...currentScan,
          progress: {
            ...currentScan.progress,
            [scanUpdates.provider]: scanUpdates.progress || 0,
          },
        });
      }
    }
  }, [scanUpdates]);

  // Load summary on mount
  useEffect(() => {
    fetchSummary();
  }, []);

  const toggleProvider = (provider: string) => {
    if (provider === 'all') {
      setSelectedProviders(['all']);
    } else {
      const newSelection = selectedProviders.includes(provider)
        ? selectedProviders.filter((p) => p !== provider)
        : [...selectedProviders.filter((p) => p !== 'all'), provider];

      setSelectedProviders(newSelection.length > 0 ? newSelection : ['all']);
    }
  };

  const getTotalResources = () => {
    if (!summary) return 0;
    return summary.total_resources;
  };

  const getProviderPercentage = (providerSummary: ResourceSummary) => {
    if (!summary || summary.total_resources === 0) return 0;
    return (providerSummary.total_resources / summary.total_resources) * 100;
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>
          Multi-Cloud Dashboard
        </h1>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Unified view of resources across AWS, GCP, and Azure
        </p>
      </div>

      {error && (
        <div
          style={{
            padding: '15px',
            backgroundColor: '#FEE',
            border: '1px solid #FCC',
            borderRadius: '5px',
            marginBottom: '20px',
            color: '#C00',
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Provider Selection & Scan Control */}
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
          Scan Configuration
        </h2>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: '500' }}>
            Select Cloud Providers:
          </label>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={() => toggleProvider('all')}
              style={{
                padding: '8px 16px',
                border: selectedProviders.includes('all') ? '2px solid #000' : '1px solid #CCC',
                borderRadius: '5px',
                backgroundColor: selectedProviders.includes('all') ? '#F0F0F0' : '#FFF',
                cursor: 'pointer',
                fontWeight: selectedProviders.includes('all') ? '600' : '400',
              }}
            >
              All Providers
            </button>
            {CLOUD_PROVIDERS.map((provider) => (
              <button
                key={provider.name}
                onClick={() => toggleProvider(provider.name)}
                style={{
                  padding: '8px 16px',
                  border: selectedProviders.includes(provider.name) ? '2px solid #000' : '1px solid #CCC',
                  borderRadius: '5px',
                  backgroundColor: selectedProviders.includes(provider.name) ? '#F0F0F0' : '#FFF',
                  cursor: 'pointer',
                  fontWeight: selectedProviders.includes(provider.name) ? '600' : '400',
                }}
              >
                {provider.icon} {provider.displayName}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={startScan}
          disabled={loading || currentScan !== null}
          style={{
            padding: '12px 24px',
            backgroundColor: loading || currentScan ? '#CCC' : '#000',
            color: '#FFF',
            border: 'none',
            borderRadius: '5px',
            cursor: loading || currentScan ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '600',
          }}
        >
          {loading ? 'Starting Scan...' : currentScan ? 'Scan In Progress' : 'Start Multi-Cloud Scan'}
        </button>
      </div>

      {/* Active Scan Progress */}
      {currentScan && (
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
            Scan Progress
          </h2>

          {currentScan.providers.map((provider) => {
            const providerInfo = CLOUD_PROVIDERS.find((p) => p.name === provider);
            const progress = currentScan.progress[provider] || 0;

            return (
              <div key={provider} style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontWeight: '500' }}>
                    {providerInfo?.icon} {providerInfo?.displayName || provider}
                  </span>
                  <span style={{ color: '#666' }}>{progress}%</span>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: '#EEE',
                    borderRadius: '4px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${progress}%`,
                      height: '100%',
                      backgroundColor: providerInfo?.color || '#000',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary Cards */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '15px' }}>
          Resource Summary
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
          {/* Total Resources Card */}
          <div
            style={{
              backgroundColor: '#FFF',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Total Resources</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{getTotalResources()}</div>
            <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
              Across all cloud providers
            </div>
          </div>

          {/* Provider Cards */}
          {CLOUD_PROVIDERS.map((provider) => {
            const providerSummary = summary?.providers[provider.name];
            if (!providerSummary) return null;

            const percentage = getProviderPercentage(providerSummary);

            return (
              <div
                key={provider.name}
                style={{
                  backgroundColor: '#FFF',
                  padding: '20px',
                  borderRadius: '8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  borderLeft: `4px solid ${provider.color}`,
                }}
              >
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>
                  {provider.icon} {provider.displayName}
                </div>
                <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                  {providerSummary.total_resources}
                </div>
                <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                  {percentage.toFixed(1)}% of total | {providerSummary.regions.length} regions
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Resource Breakdown by Provider */}
      {summary && (
        <div
          style={{
            backgroundColor: '#FFF',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '15px' }}>
            Resource Breakdown
          </h2>

          {CLOUD_PROVIDERS.map((provider) => {
            const providerSummary = summary.providers[provider.name];
            if (!providerSummary || providerSummary.total_resources === 0) return null;

            return (
              <div key={provider.name} style={{ marginBottom: '25px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '10px' }}>
                  {provider.icon} {provider.displayName}
                </h3>

                <div style={{ paddingLeft: '20px' }}>
                  {Object.entries(providerSummary.resource_counts).map(([resourceType, count]) => {
                    const percentage = (count / providerSummary.total_resources) * 100;

                    return (
                      <div key={resourceType} style={{ marginBottom: '12px' }}>
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            marginBottom: '5px',
                          }}
                        >
                          <span style={{ fontSize: '14px' }}>{resourceType.replace(/_/g, ' ')}</span>
                          <span style={{ fontSize: '14px', fontWeight: '600' }}>{count}</span>
                        </div>
                        <div
                          style={{
                            width: '100%',
                            height: '6px',
                            backgroundColor: '#EEE',
                            borderRadius: '3px',
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              width: `${percentage}%`,
                              height: '100%',
                              backgroundColor: provider.color,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Footer */}
      <div style={{ marginTop: '30px', padding: '15px', textAlign: 'center', color: '#999', fontSize: '12px' }}>
        Last updated: {summary?.scan_time ? new Date(summary.scan_time).toLocaleString() : 'Never'}
      </div>
    </div>
  );
};

export default MultiCloudDashboard;
