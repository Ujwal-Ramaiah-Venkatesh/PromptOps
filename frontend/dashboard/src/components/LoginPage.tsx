/**
 * Login Page Component
 * Week 13-15: SECURITY-007
 *
 * Handles user authentication with email and password
 */

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

export const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="premium-login-screen">
      <div className="premium-login-orb premium-login-orb-one" />
      <div className="premium-login-orb premium-login-orb-two" />

      <div className="premium-login-card">
        {/* Logo */}
        <div className="premium-login-header">
          <img
            src="/promptops-logo.png"
            alt="PromptOps Logo"
            className="premium-login-logo"
            style={{
              width: '100px',
              height: '100px',
              objectFit: 'contain',
              borderRadius: '12px'
            }}
          />
          <h1>PromptOps</h1>
          <p>Secure command center for modern infrastructure teams.</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="premium-login-error">
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="premium-login-form">
          <div className="premium-login-field">
            <label>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@promptops.com"
              disabled={isLoading}
            />
          </div>

          <div className="premium-login-field">
            <label>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="premium-login-submit"
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* Test Accounts */}
        <div className="premium-login-accounts">
          <div className="premium-login-accounts-title">Test Accounts</div>
          <div>Admin: admin@promptops.com / admin123</div>
          <div>PM: pm@promptops.com / pm123</div>
        </div>
      </div>
    </div>
  );
};
