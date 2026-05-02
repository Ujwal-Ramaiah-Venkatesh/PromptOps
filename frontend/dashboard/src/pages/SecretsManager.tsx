/**
 * Secrets Management Page
 * ========================
 *
 * ENH-005: Secret rotation UI and management.
 *
 * Author: PromptOps Team
 * Date: 2026-04-30
 * Phase: 2 - Secret Rotation
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Secret {
  path: string;
  secret_type?: string;
  rotation_enabled?: boolean;
  next_rotation_at?: string;
}

interface SecretVersion {
  version: number;
  created_time: string;
  deleted: boolean;
}

export const SecretsManager: React.FC = () => {
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSecret, setSelectedSecret] = useState<string | null>(null);
  const [versions, setVersions] = useState<SecretVersion[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [rotatingSecret, setRotatingSecret] = useState<string | null>(null);

  useEffect(() => {
    fetchSecrets();
  }, []);

  const fetchSecrets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get('/api/v1/secrets/');
      setSecrets(data.secrets || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch secrets');
    } finally {
      setLoading(false);
    }
  };

  const fetchVersions = async (path: string) => {
    try {
      const data = await apiClient.get(`/api/v1/secrets/${path}/versions`);
      setVersions(data.versions || []);
      setSelectedSecret(path);
    } catch (err: any) {
      console.error('Failed to fetch versions:', err);
    }
  };

  const rotateSecret = async (path: string) => {
    if (!confirm(`Rotate secret "${path}"? This will generate a new version.`)) {
      return;
    }

    try {
      setRotatingSecret(path);
      await apiClient.post('/api/v1/secrets/rotate', {
        path,
        auto_generate: true,
      });
      alert(`Secret "${path}" rotated successfully!`);
      fetchSecrets();
      if (selectedSecret === path) {
        fetchVersions(path);
      }
    } catch (err: any) {
      alert(`Failed to rotate secret: ${err.message}`);
    } finally {
      setRotatingSecret(null);
    }
  };

  const deleteSecret = async (path: string) => {
    if (!confirm(`Delete secret "${path}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await apiClient.delete(`/api/v1/secrets/${path}`);
      alert(`Secret "${path}" deleted successfully!`);
      fetchSecrets();
      if (selectedSecret === path) {
        setSelectedSecret(null);
        setVersions([]);
      }
    } catch (err: any) {
      alert(`Failed to delete secret: ${err.message}`);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getDaysUntilRotation = (dateString?: string) => {
    if (!dateString) return null;
    const rotationDate = new Date(dateString);
    const now = new Date();
    const days = Math.ceil((rotationDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return days;
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '18px', color: '#6b7280' }}>Loading secrets...</div>
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
          onClick={fetchSecrets}
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

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, color: '#111827', marginBottom: '8px' }}>
            🔐 Secrets Manager
          </h1>
          <p style={{ fontSize: '14px', color: '#6b7280' }}>
            Manage and rotate secrets securely with HashiCorp Vault
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          + Create Secret
        </button>
      </div>

      {/* Secrets List */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedSecret ? '1fr 1fr' : '1fr', gap: '24px' }}>
        {/* Left Panel: Secrets List */}
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#111827', marginBottom: '16px' }}>
            All Secrets ({secrets.length})
          </h2>

          {secrets.length === 0 ? (
            <div style={{
              padding: '40px',
              backgroundColor: '#f9fafb',
              borderRadius: '12px',
              border: '1px solid #e5e7eb',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔒</div>
              <div style={{ fontSize: '16px', fontWeight: 500, color: '#6b7280', marginBottom: '8px' }}>
                No secrets yet
              </div>
              <div style={{ fontSize: '14px', color: '#9ca3af' }}>
                Create your first secret to get started
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '12px' }}>
              {secrets.map((secret) => {
                const daysUntilRotation = getDaysUntilRotation(secret.next_rotation_at);
                const needsRotation = daysUntilRotation !== null && daysUntilRotation <= 7;

                return (
                  <div
                    key={secret.path}
                    onClick={() => fetchVersions(secret.path)}
                    style={{
                      padding: '16px',
                      backgroundColor: selectedSecret === secret.path ? '#eff6ff' : '#ffffff',
                      borderRadius: '12px',
                      border: selectedSecret === secret.path ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '14px', fontWeight: 600, color: '#111827', marginBottom: '4px' }}>
                          {secret.path}
                        </div>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          {secret.secret_type && (
                            <span style={{
                              padding: '2px 8px',
                              backgroundColor: '#f3f4f6',
                              color: '#6b7280',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 500,
                            }}>
                              {secret.secret_type}
                            </span>
                          )}
                          {secret.rotation_enabled && (
                            <span style={{
                              padding: '2px 8px',
                              backgroundColor: needsRotation ? '#fef2f2' : '#f0fdf4',
                              color: needsRotation ? '#dc2626' : '#16a34a',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 600,
                            }}>
                              {needsRotation ? `⚠️ Rotate in ${daysUntilRotation}d` : '✓ Auto-rotate'}
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          rotateSecret(secret.path);
                        }}
                        disabled={rotatingSecret === secret.path}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: rotatingSecret === secret.path ? '#d1d5db' : '#3b82f6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 500,
                          cursor: rotatingSecret === secret.path ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {rotatingSecret === secret.path ? 'Rotating...' : '🔄 Rotate'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Panel: Secret Details */}
        {selectedSecret && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#111827', margin: 0 }}>
                Version History
              </h2>
              <button
                onClick={() => deleteSecret(selectedSecret)}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                🗑️ Delete
              </button>
            </div>

            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              border: '1px solid #e5e7eb',
              padding: '16px',
            }}>
              <div style={{ fontSize: '14px', fontWeight: 500, color: '#6b7280', marginBottom: '12px' }}>
                {selectedSecret}
              </div>

              {versions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#9ca3af' }}>
                  No versions found
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '8px' }}>
                  {versions.map((version) => (
                    <div
                      key={version.version}
                      style={{
                        padding: '12px',
                        backgroundColor: version.deleted ? '#fef2f2' : '#f9fafb',
                        borderRadius: '8px',
                        border: '1px solid',
                        borderColor: version.deleted ? '#fecaca' : '#e5e7eb',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: 600, color: '#111827', marginBottom: '2px' }}>
                            Version {version.version}
                            {version.version === versions[0].version && !version.deleted && (
                              <span style={{
                                marginLeft: '8px',
                                padding: '2px 6px',
                                backgroundColor: '#10b981',
                                color: 'white',
                                borderRadius: '4px',
                                fontSize: '10px',
                              }}>
                                CURRENT
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '11px', color: '#6b7280' }}>
                            {formatDate(version.created_time)}
                          </div>
                        </div>
                        {version.deleted && (
                          <span style={{
                            padding: '2px 8px',
                            backgroundColor: '#dc2626',
                            color: 'white',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 600,
                          }}>
                            DELETED
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create Modal (placeholder) */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '500px',
            width: '100%',
          }}>
            <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px' }}>
              Create New Secret
            </h3>
            <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '16px' }}>
              Feature coming soon! Use Vault CLI or API to create secrets for now.
            </p>
            <button
              onClick={() => setShowCreateModal(false)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
