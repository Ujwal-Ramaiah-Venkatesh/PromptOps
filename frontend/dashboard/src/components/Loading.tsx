import React from 'react';
import './Loading.css';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'white' | 'gray';
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'primary',
}) => {
  return (
    <div className={`premium-spinner premium-spinner-${size} premium-spinner-${variant}`} role="status" aria-label="Loading">
      <div className="premium-spinner-circle"></div>
    </div>
  );
};

export interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  className = '',
}) => {
  const style: React.CSSProperties = {};

  if (width) {
    style.width = typeof width === 'number' ? `${width}px` : width;
  }

  if (height) {
    style.height = typeof height === 'number' ? `${height}px` : height;
  }

  return (
    <div
      className={`premium-skeleton premium-skeleton-${variant} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
};

export interface LoadingOverlayProps {
  message?: string;
  transparent?: boolean;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  message = 'Loading...',
  transparent = false,
}) => {
  return (
    <div className={`premium-loading-overlay ${transparent ? 'is-transparent' : ''}`}>
      <div className="premium-loading-content">
        <Spinner size="lg" />
        {message && <div className="premium-loading-message">{message}</div>}
      </div>
    </div>
  );
};

export interface CardSkeletonProps {
  count?: number;
}

export const CardSkeleton: React.FC<CardSkeletonProps> = ({ count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="premium-card-skeleton">
          <Skeleton variant="rectangular" height={200} />
          <div className="premium-card-skeleton-content">
            <Skeleton variant="text" width="60%" height={24} />
            <Skeleton variant="text" width="100%" height={16} />
            <Skeleton variant="text" width="90%" height={16} />
            <div className="premium-card-skeleton-footer">
              <Skeleton variant="circular" width={40} height={40} />
              <Skeleton variant="text" width="40%" height={16} />
            </div>
          </div>
        </div>
      ))}
    </>
  );
};

export interface ProgressBarProps {
  value: number;
  max?: number;
  variant?: 'primary' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  animated?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  variant = 'primary',
  showLabel = true,
  animated = true,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className="premium-progress-bar" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
      <div className="premium-progress-track">
        <div
          className={`premium-progress-fill premium-progress-${variant} ${animated ? 'is-animated' : ''}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="premium-progress-label">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
};

export interface PulseLoaderProps {
  size?: number;
  color?: string;
}

export const PulseLoader: React.FC<PulseLoaderProps> = ({
  size = 12,
  color = 'var(--primary)',
}) => {
  return (
    <div className="premium-pulse-loader">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="premium-pulse-dot"
          style={{
            width: size,
            height: size,
            backgroundColor: color,
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
    </div>
  );
};
