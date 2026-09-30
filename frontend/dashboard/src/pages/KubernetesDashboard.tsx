import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface Cluster {
  id: string;
  name: string;
  provider: string;
  region?: string;
  status: string;
  version?: string;
  node_count?: number;
}

interface InventoryItem {
  name: string;
  namespace?: string;
  status?: string;
  desired_replicas?: number;
  available_replicas?: number;
}

const PROVIDERS = [
  { id: 'all', label: 'All clusters' },
  { id: 'eks', label: 'Amazon EKS' },
  { id: 'aks', label: 'Azure AKS' },
  { id: 'gke', label: 'Google GKE' },
];

export const KubernetesDashboard: React.FC = () => {
  const [provider, setProvider] = useState('all');
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [selectedCluster, setSelectedCluster] = useState<Cluster | null>(null);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [inventoryKind, setInventoryKind] = useState<'nodes' | 'workloads'>('nodes');
  const [loading, setLoading] = useState(false);
  const [inventoryLoading, setInventoryLoading] = useState(false);

  const loadClusters = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/v1/kubernetes/clusters', {
        params: { provider },
      });
      setClusters(response.data.clusters || []);
      setErrors((response.data.errors || []).map((item: { provider: string; error: string }) => `${item.provider}: ${item.error}`));
    } catch (error) {
      setClusters([]);
      setErrors(['Unable to load Kubernetes clusters. Check provider credentials and configuration.']);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadClusters();
  }, [provider]);

  const inspectCluster = async (cluster: Cluster, kind: 'nodes' | 'workloads') => {
    setSelectedCluster(cluster);
    setInventoryKind(kind);
    setInventoryLoading(true);
    try {
      const response = await apiClient.get(`/api/v1/kubernetes/clusters/${encodeURIComponent(cluster.id)}/${kind}`);
      setInventory(response.data[kind] || []);
    } catch (error) {
      setInventory([]);
      setErrors((current) => [...current.filter((item) => !item.startsWith('Kubernetes API:')), 'Kubernetes API: configure a valid kubeconfig context for inventory.']);
    } finally {
      setInventoryLoading(false);
    }
  };

  return (
    <section style={{ maxWidth: 1400, margin: '0 auto', padding: '32px 24px', color: '#172033' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 20, alignItems: 'end', flexWrap: 'wrap' }}>
        <div>
          <p style={{ margin: 0, color: '#64748b', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>Cloud control plane</p>
          <h1 style={{ margin: '8px 0', fontSize: 36 }}>Kubernetes Operations</h1>
          <p style={{ margin: 0, color: '#64748b' }}>Discover and inspect EKS, AKS, and GKE from one operational surface.</p>
        </div>
        <button onClick={() => void loadClusters()} disabled={loading} style={{ padding: '12px 18px', border: 0, borderRadius: 8, background: '#172033', color: 'white', cursor: 'pointer' }}>
          {loading ? 'Refreshing...' : 'Refresh inventory'}
        </button>
      </div>

      <div style={{ display: 'flex', gap: 8, margin: '28px 0', flexWrap: 'wrap' }}>
        {PROVIDERS.map((item) => (
          <button key={item.id} onClick={() => setProvider(item.id)} style={{ padding: '10px 14px', borderRadius: 8, border: provider === item.id ? '2px solid #172033' : '1px solid #cbd5e1', background: provider === item.id ? '#e2e8f0' : 'white', cursor: 'pointer', fontWeight: 700 }}>
            {item.label}
          </button>
        ))}
      </div>

      {errors.length > 0 && <div style={{ padding: 16, marginBottom: 20, borderRadius: 8, background: '#fff7ed', color: '#9a3412' }}>{errors.map((error) => <div key={error}>{error}</div>)}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: selectedCluster ? 'minmax(0, 1fr) minmax(320px, 0.8fr)' : '1fr', gap: 20 }}>
        <div style={{ display: 'grid', gap: 12 }}>
          {clusters.length === 0 && !loading && <div style={{ padding: 32, border: '1px dashed #cbd5e1', borderRadius: 8, color: '#64748b' }}>No managed clusters returned for this provider filter.</div>}
          {clusters.map((cluster) => (
            <article key={cluster.id} style={{ padding: 20, border: selectedCluster?.id === cluster.id ? '2px solid #2563eb' : '1px solid #e2e8f0', borderRadius: 8, background: 'white', boxShadow: '0 4px 16px rgba(15,23,42,0.06)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <div><h2 style={{ margin: 0, fontSize: 20 }}>{cluster.name}</h2><p style={{ margin: '6px 0', color: '#64748b' }}>{cluster.provider.toUpperCase()} · {cluster.region || 'regional'}</p></div>
                <strong style={{ color: cluster.status === 'active' || cluster.status === 'running' ? '#15803d' : '#b45309' }}>{cluster.status}</strong>
              </div>
              <div style={{ display: 'flex', gap: 22, color: '#475569', margin: '16px 0' }}><span>Kubernetes {cluster.version || 'unknown'}</span><span>{cluster.node_count ?? '—'} nodes</span></div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => void inspectCluster(cluster, 'nodes')} style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6, background: 'white', cursor: 'pointer' }}>Nodes</button>
                <button onClick={() => void inspectCluster(cluster, 'workloads')} style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6, background: 'white', cursor: 'pointer' }}>Workloads</button>
              </div>
            </article>
          ))}
        </div>

        {selectedCluster && <aside style={{ padding: 20, borderRadius: 8, background: '#f8fafc', border: '1px solid #e2e8f0', alignSelf: 'start' }}>
          <h2 style={{ marginTop: 0 }}>{selectedCluster.name}</h2>
          <p style={{ color: '#64748b' }}>{inventoryKind === 'nodes' ? 'Node inventory' : 'Deployment inventory'}</p>
          {inventoryLoading && <p>Loading Kubernetes API...</p>}
          {!inventoryLoading && inventory.length === 0 && <p style={{ color: '#64748b' }}>No inventory available. Configure kubeconfig access for this cluster.</p>}
          {!inventoryLoading && inventory.map((item) => <div key={`${item.namespace || 'cluster'}:${item.name}`} style={{ padding: '12px 0', borderTop: '1px solid #e2e8f0' }}><strong>{item.name}</strong><div style={{ color: '#64748b', fontSize: 13 }}>{item.namespace || item.status || 'Ready'}{item.desired_replicas !== undefined ? ` · ${item.available_replicas || 0}/${item.desired_replicas} available` : ''}</div></div>)}
        </aside>}
      </div>
    </section>
  );
};
