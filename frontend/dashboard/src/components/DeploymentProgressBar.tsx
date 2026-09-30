/**
 * Deployment Progress Bar Component
 * ==================================
 *
 * Real-time deployment progress visualization with step tracking.
 *
 * Features:
 * - Live progress updates via WebSocket
 * - Step-by-step progress indication
 * - Status colors (running, success, error)
 * - Elapsed time tracking
 * - ETA calculation
 *
 * @author PromptOps Team - Q3 2026
 * @date July 8, 2026
 */

import React, { useState, useEffect } from 'react';
import { useDeploymentProgress } from '../hooks/useWebSocket';

interface DeploymentProgressBarProps {
  deploymentId: string;
  onComplete?: (status: string) => void;
}

export const DeploymentProgressBar: React.FC<DeploymentProgressBarProps> = ({
  deploymentId,
  onComplete,
}) => {
  const { progress, isConnected } = useDeploymentProgress(deploymentId);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [elapsedTime, setElapsedTime] = useState<string>('0:00');

  // Update elapsed time every second
  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      setElapsedTime(`${minutes}:${seconds.toString().padStart(2, '0')}`);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // Reset start time when deployment starts
  useEffect(() => {
    if (progress?.status === 'running') {
      setStartTime(Date.now());
    }
  }, [progress?.deployment_id]);

  // Call onComplete when deployment finishes
  useEffect(() => {
    if (progress?.status === 'completed' || progress?.status === 'failed') {
      onComplete?.(progress.status);
    }
  }, [progress?.status, onComplete]);

  if (!progress) {
    return (
      <div style={{
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#10b981' : '#ef4444',
          }} />
          <span style={{ color: '#6b7280', fontSize: '14px' }}>
            {isConnected ? 'Waiting for deployment...' : 'Connecting...'}
          </span>
        </div>
      </div>
    );
  }

  const { status, progress: percent, current_step, total_steps, completed_steps, metadata } = progress;

  // Status colors
  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return '#3b82f6';
      case 'completed':
        return '#10b981';
      case 'failed':
        return '#ef4444';
      case 'pending':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return 'Deploying...';
      case 'completed':
        return 'Deployment Complete';
      case 'failed':
        return 'Deployment Failed';
      case 'pending':
        return 'Pending';
      default:
        return 'Unknown';
    }
  };

  // Calculate ETA (rough estimate)
  const calculateETA = () => {
    if (!percent || percent === 0 || status !== 'running') return null;

    const elapsed = (Date.now() - startTime) / 1000;
    const rate = percent / elapsed;
    const remaining = (100 - percent) / rate;
    const minutes = Math.floor(remaining / 60);
    const seconds = Math.floor(remaining % 60);

    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const eta = calculateETA();

  return (
    <div style={{
      padding: '20px',
      backgroundColor: 'white',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(),
            animation: status === 'running' ? 'pulse 2s infinite' : 'none',
          }} />
          <span style={{ fontWeight: '600', fontSize: '16px' }}>
            {getStatusText()}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', fontSize: '14px', color: '#6b7280' }}>
          {status === 'running' && (
            <>
              <span>Elapsed: {elapsedTime}</span>
              {eta && <span>ETA: {eta}</span>}
            </>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div style={{
        width: '100%',
        height: '8px',
        backgroundColor: '#e5e7eb',
        borderRadius: '4px',
        overflow: 'hidden',
        marginBottom: '12px',
      }}>
        <div
          style={{
            width: `${percent || 0}%`,
            height: '100%',
            backgroundColor: getStatusColor(),
            transition: 'width 0.3s ease-out',
          }}
        />
      </div>

      {/* Progress text */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <span style={{ fontSize: '14px', color: '#6b7280' }}>
          {current_step || 'Initializing...'}
        </span>
        <span style={{ fontSize: '14px', fontWeight: '600' }}>
          {Math.round(percent || 0)}%
        </span>
      </div>

      {/* Step progress */}
      {total_steps && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f9fafb',
          borderRadius: '6px',
          marginBottom: '12px',
        }}>
          <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>
            Progress: Step {completed_steps || 0} of {total_steps}
          </div>
          <div style={{ display: 'flex', gap: '4px' }}>
            {Array.from({ length: total_steps }).map((_, index) => (
              <div
                key={index}
                style={{
                  flex: 1,
                  height: '4px',
                  backgroundColor: index < (completed_steps || 0)
                    ? getStatusColor()
                    : '#e5e7eb',
                  borderRadius: '2px',
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      {metadata && (
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          {metadata.environment && (
            <span>Environment: <strong>{metadata.environment}</strong></span>
          )}
          {metadata.service && (
            <span>Service: <strong>{metadata.service}</strong></span>
          )}
          {metadata.version && (
            <span>Version: <strong>{metadata.version}</strong></span>
          )}
        </div>
      )}

      {/* Inline styles for animation */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.5;
            }
          }
        `}
      </style>
    </div>
  );
};

export default DeploymentProgressBar;
