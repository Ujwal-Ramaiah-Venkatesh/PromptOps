/**
 * Error Boundary Component
 * =========================
 *
 * React error boundary with user-friendly error display and
 * automatic error reporting.
 *
 * Features:
 * - Catches React component errors
 * - User-friendly error messages
 * - Error stack traces (dev mode)
 * - Automatic error reporting
 * - Recovery actions
 * - Fallback UI
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import React, { Component, ReactNode, ErrorInfo } from 'react';
import './ErrorBoundary.css';

// ============================================================================
// Type Definitions
// ============================================================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  enableReporting?: boolean;
  reportingEndpoint?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

// ============================================================================
// Error Boundary Component
// ============================================================================

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorId: `ERR-${Date.now()}-${Math.random().toString(36).substring(7)}`
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report error to backend
    if (this.props.enableReporting && this.props.reportingEndpoint) {
      this.reportError(error, errorInfo);
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  reportError = async (error: Error, errorInfo: ErrorInfo): Promise<void> => {
    try {
      const payload = {
        error_id: this.state.errorId,
        message: error.message,
        stack: error.stack,
        component_stack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        url: window.location.href
      };

      await fetch(this.props.reportingEndpoint!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="error-boundary">
          <div className="error-boundary-container">
            <div className="error-icon">⚠️</div>
            <h1 className="error-title">Something went wrong</h1>
            <p className="error-message">
              We're sorry, but something unexpected happened. The error has been logged
              and our team will investigate.
            </p>

            {this.state.errorId && (
              <div className="error-id">
                <strong>Error ID:</strong> <code>{this.state.errorId}</code>
              </div>
            )}

            <div className="error-actions">
              <button className="error-button error-button--primary" onClick={this.handleReset}>
                Try Again
              </button>
              <button className="error-button error-button--secondary" onClick={this.handleReload}>
                Reload Page
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary className="error-details-summary">
                  Show Error Details (Development Mode)
                </summary>
                <div className="error-stack">
                  <h3>Error Message:</h3>
                  <pre>{this.state.error.message}</pre>

                  <h3>Stack Trace:</h3>
                  <pre>{this.state.error.stack}</pre>

                  {this.state.errorInfo && (
                    <>
                      <h3>Component Stack:</h3>
                      <pre>{this.state.errorInfo.componentStack}</pre>
                    </>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// ============================================================================
// Toast Notification Component
// ============================================================================

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  dismissible?: boolean;
}

interface ToastNotificationProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

export function ToastNotification({ toast, onDismiss }: ToastNotificationProps): JSX.Element {
  const [isExiting, setIsExiting] = React.useState(false);

  React.useEffect(() => {
    if (toast.duration) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, toast.duration);
      return () => clearTimeout(timer);
    }
  }, [toast.duration]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(toast.id);
    }, 300); // Match CSS animation duration
  };

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  return (
    <div className={`toast toast--${toast.type} ${isExiting ? 'toast--exiting' : ''}`}>
      <div className="toast-icon">{icons[toast.type]}</div>
      <div className="toast-content">
        <div className="toast-title">{toast.title}</div>
        {toast.message && <div className="toast-message">{toast.message}</div>}
      </div>
      {toast.dismissible !== false && (
        <button className="toast-dismiss" onClick={handleDismiss} aria-label="Dismiss">
          ×
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Toast Container Component
// ============================================================================

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

export function ToastContainer({
  toasts,
  onDismiss,
  position = 'top-right'
}: ToastContainerProps): JSX.Element {
  return (
    <div className={`toast-container toast-container--${position}`}>
      {toasts.map(toast => (
        <ToastNotification key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

// ============================================================================
// useToast Hook
// ============================================================================

export function useToast() {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const addToast = React.useCallback((
    type: Toast['type'],
    title: string,
    message: string = '',
    duration: number = 5000
  ): string => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    const toast: Toast = {
      id,
      type,
      title,
      message,
      duration,
      dismissible: true
    };

    setToasts(prev => [...prev, toast]);
    return id;
  }, []);

  const dismissToast = React.useCallback((id: string): void => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = React.useCallback((): void => {
    setToasts([]);
  }, []);

  // Convenience methods
  const success = React.useCallback((title: string, message?: string, duration?: number) => {
    return addToast('success', title, message || '', duration);
  }, [addToast]);

  const error = React.useCallback((title: string, message?: string, duration?: number) => {
    return addToast('error', title, message || '', duration);
  }, [addToast]);

  const warning = React.useCallback((title: string, message?: string, duration?: number) => {
    return addToast('warning', title, message || '', duration);
  }, [addToast]);

  const info = React.useCallback((title: string, message?: string, duration?: number) => {
    return addToast('info', title, message || '', duration);
  }, [addToast]);

  return {
    toasts,
    addToast,
    dismissToast,
    clearAllToasts,
    success,
    error,
    warning,
    info
  };
}

// ============================================================================
// Loading Overlay Component
// ============================================================================

interface LoadingOverlayProps {
  show: boolean;
  message?: string;
  progress?: number; // 0-100
  cancelable?: boolean;
  onCancel?: () => void;
}

export function LoadingOverlay({
  show,
  message = 'Processing...',
  progress,
  cancelable = false,
  onCancel
}: LoadingOverlayProps): JSX.Element | null {
  if (!show) return null;

  return (
    <div className="loading-overlay">
      <div className="loading-overlay-content">
        <div className="loading-spinner"></div>
        <p className="loading-message">{message}</p>

        {progress !== undefined && (
          <div className="loading-progress">
            <div className="loading-progress-bar">
              <div
                className="loading-progress-fill"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              ></div>
            </div>
            <div className="loading-progress-text">{Math.round(progress)}%</div>
          </div>
        )}

        {cancelable && onCancel && (
          <button className="loading-cancel-button" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}

export default ErrorBoundary;
