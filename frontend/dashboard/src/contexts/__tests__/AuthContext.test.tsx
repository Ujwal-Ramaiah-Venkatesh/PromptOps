import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import { apiClient } from '../../api/client';

// Mock API client
vi.mock('../../api/client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Test component that uses auth
const TestComponent = () => {
  const { user, login, logout, isAuthenticated } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      {user && <div data-testid="user-email">{user.email}</div>}
      <button onClick={() => login('test@example.com', 'password')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('provides authentication state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
  });

  it('handles successful login', async () => {
    // Mock fetch instead of apiClient
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'test-token',
        token_type: 'bearer',
        user: {
          email: 'test@example.com',
          role: 'admin',
        },
      }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    loginButton.click();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    }, { timeout: 3000 });
  });

  it('handles logout', async () => {
    localStorage.setItem('promptops_token', 'test-token');
    localStorage.setItem('promptops_user', JSON.stringify({ email: 'test@example.com', role: 'admin' }));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const logoutButton = screen.getByText('Logout');
    logoutButton.click();

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(localStorage.getItem('promptops_token')).toBeNull();
    });
  });

  it.skip('restores session from localStorage', async () => {
    localStorage.setItem('promptops_token', 'test-token');
    localStorage.setItem('promptops_user', JSON.stringify({
      email: 'restored@example.com',
      role: 'pm'
    }));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('user-email')).toHaveTextContent('restored@example.com');
  });

  it.skip('handles login failure', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({
        detail: 'Invalid credentials',
      }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');

    // Wrap in try-catch to handle expected error
    try {
      loginButton.click();
    } catch (error) {
      // Expected error
    }

    // Wait a bit for async operation
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
  });
});
