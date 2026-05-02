/**
 * Scan Progress Component with Real-Time Updates
 * ===============================================
 *
 * Shows live scan progress using WebSocket updates.
 *
 * Author: PromptOps Team
 * Date: 2026-04-30
 * Phase: 2 - Real-Time Updates
 */

import React, { useEffect, useState } from 'react';
import { useScanUpdates } from '../hooks/useWebSocket';

interface ScanProgressProps {
  scanId: string;
  onComplete?: (resourcesFound: number) => void;
}

export const ScanProgress: React.FC<ScanProgressProps> = ({ scanId, onComplete }) => {
  const connectionId = `scan-viewer-${Date.now()}`;
  const { isConnected, scanStatus, progress } = useScanUpdates(scanId, connectionId);
  const [startTime] = useState(Date.now());
  const [duration, setDuration] = useState(0);

  // Update duration every second
  useEffect(() => {
    const interval = setInterval(() => {
      setDuration(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // Call onComplete when scan finishes
  useEffect(() => {
    if (scanStatus?.status === 'completed' && onComplete) {
      onComplete(scanStatus.resources_found || 0);
    }
  }, [scanStatus, onComplete]);

  const getStatusColor = () => {
    if (!scanStatus) return '#3b82f6'; // blue
    switch (scanStatus.status) {
      case 'completed':
        return '#10b981'; // green
      case 'failed':
        return '#ef4444'; // red
      case 'running':
        return '#3b82f6'; // blue
      default:
        return '#6b7280'; // gray
    }
  };

  const getStatusText = () => {
    if (!isConnected) return 'Connecting...';
    if (!scanStatus) return 'Initializing...';

    switch (scanStatus.status) {
      case 'completed':
        return 'Scan Complete!';
      case 'failed':
        return 'Scan Failed';
      case 'running':
        return 'Scanning AWS Resources...';
      default:
        return 'Unknown Status';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <div style={{
      padding: '24px',
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#111827' }}>
            {getStatusText()}
          </h3>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            {/* Connection indicator */}
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isConnected ? '#10b981' : '#ef4444',
            }} />
            <span style={{ fontSize: '12px', color: '#6b7280' }}>
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
        <div style={{ marginTop: '8px', fontSize: '14px', color: '#6b7280' }}>
          Scan ID: {scanId}
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '14px', fontWeight: 500, color: '#374151' }}>
            Progress
          </span>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#111827' }}>
            {progress}%
          </span>
        </div>
        <div style={{
          width: '100%',
          height: '8px',
          backgroundColor: '#e5e7eb',
          borderRadius: '4px',
          overflow: 'hidden',
        }}>
          <div style={{
            width: `${progress}%`,
            height: '100%',
            backgroundColor: getStatusColor(),
            transition: 'width 0.3s ease, background-color 0.3s ease',
          }} />
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '16px',
        marginBottom: '16px',
      }}>
        {/* Resources Found */}
        <div style={{
          padding: '12px',
          backgroundColor: '#f9fafb',
          borderRadius: '6px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
            Resources Found
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#111827' }}>
            {scanStatus?.resources_found || 0}
          </div>
        </div>

        {/* Duration */}
        <div style={{
          padding: '12px',
          backgroundColor: '#f9fafb',
          borderRadius: '6px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
            Duration
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: '#111827' }}>
            {formatDuration(duration)}
          </div>
        </div>

        {/* Status */}
        <div style={{
          padding: '12px',
          backgroundColor: '#f9fafb',
          borderRadius: '6px',
          border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
            Status
          </div>
          <div style={{
            fontSize: '16px',
            fontWeight: 600,
            color: getStatusColor(),
            textTransform: 'capitalize',
          }}>
            {scanStatus?.status || 'Pending'}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {scanStatus?.status === 'failed' && scanStatus?.error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '6px',
          marginTop: '12px',
        }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#dc2626', marginBottom: '4px' }}>
            Error
          </div>
          <div style={{ fontSize: '13px', color: '#991b1b' }}>
            {scanStatus.error}
          </div>
        </div>
      )}

      {/* Success Message */}
      {scanStatus?.status === 'completed' && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: '6px',
          marginTop: '12px',
        }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#16a34a', marginBottom: '4px' }}>
            ✓ Scan Complete
          </div>
          <div style={{ fontSize: '13px', color: '#15803d' }}>
            Successfully discovered {scanStatus.resources_found} AWS resources in {formatDuration(duration)}
          </div>
        </div>
      )}

      {/* Real-time indicator */}
      {isConnected && scanStatus?.status === 'running' && (
        <div style={{
          marginTop: '16px',
          padding: '8px 12px',
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '6px',
          fontSize: '12px',
          color: '#1e40af',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: '#3b82f6',
            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          }} />
          Real-time updates enabled
        </div>
      )}
    </div>
  );
};
