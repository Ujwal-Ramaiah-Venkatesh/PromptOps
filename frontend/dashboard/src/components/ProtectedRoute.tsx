/**
 * Protected Route Component
 * Week 13-15: SECURITY-007
 *
 * Wraps routes that require authentication
 */

import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="premium-login-screen">
        <div className="premium-login-orb premium-login-orb-one" />
        <div className="premium-login-orb premium-login-orb-two" />
        <div className="premium-loading-card">
          <div className="premium-loading-spinner" />
          <div className="premium-loading-text">Loading your command center...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will show LoginPage instead
  }

  return <>{children}</>;
};
