/**
 * API Client Utilities
 * =====================
 *
 * Centralized API client with error handling and retries.
 *
 * Author: PromptOps Team - Week 11-12
 * Date: 2026-04-29
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

// ============================================================================
// API Error Class
// ============================================================================

export class APIError extends Error {
  status: number;
  response?: any;

  constructor(message: string, status: number, response?: any) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
  }
}

// ============================================================================
// Fetch Wrapper with Error Handling
// ============================================================================

interface FetchOptions extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = 30000, retries = 3, retryDelay = 1000, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return response;
    } catch (error: any) {
      lastError = error;

      // Don't retry on 4xx errors (client errors)
      if (error instanceof APIError && error.status >= 400 && error.status < 500) {
        throw error;
      }

      // Don't retry on last attempt
      if (attempt === retries) {
        break;
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
    }
  }

  clearTimeout(timeoutId);
  throw lastError || new Error('Request failed after retries');
}

// ============================================================================
// API Client Methods
// ============================================================================

export const apiClient = {
  /**
   * Parse natural language command into intent
   */
  async parseIntent(command: string, user: string) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/parse-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, user })
    });

    return response.json();
  },

  /**
   * Decompose intent into executable sub-tasks
   */
  async decompose(intent: any, user: string) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/decompose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ intent, user }),
      timeout: 60000 // 60s timeout for decomposition
    });

    return response.json();
  },

  /**
   * Execute approved task plan
   */
  async execute(decompositionId: string, user: string, approved: boolean, approvalPhrase?: string) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decomposition_id: decompositionId,
        user,
        approved,
        approval_phrase: approvalPhrase
      })
    });

    return response.json();
  },

  /**
   * Get execution status
   */
  async getExecutionStatus(executionId: string) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/execution/${executionId}`, {
      method: 'GET'
    });

    return response.json();
  },

  /**
   * Get audit trail with filters
   */
  async getAudit(params: {
    limit?: number;
    offset?: number;
    user?: string;
    env?: string;
    status?: string;
  } = {}) {
    const queryParams = new URLSearchParams();

    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset) queryParams.append('offset', params.offset.toString());
    if (params.user) queryParams.append('user', params.user);
    if (params.env) queryParams.append('env', params.env);
    if (params.status) queryParams.append('status', params.status);

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/audit?${queryParams.toString()}`,
      { method: 'GET' }
    );

    return response.json();
  },

  /**
   * Export audit trail to CSV or JSON
   */
  async exportAudit(format: 'csv' | 'json' = 'csv') {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/audit/export?format=${format}`,
      { method: 'GET' }
    );

    if (format === 'csv') {
      return response.text();
    } else {
      return response.json();
    }
  },

  /**
   * Get recent drift events
   */
  async getDrift() {
    const response = await fetchWithTimeout(`${API_BASE_URL}/drift/recent`, {
      method: 'GET'
    });

    return response.json();
  },

  /**
   * Acknowledge drift event
   */
  async acknowledgeDrift(driftId: string, user: string) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/drift/${driftId}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user })
    });

    return response.json();
  },

  /**
   * Revert drift to expected state
   */
  async revertDrift(driftId: string, user: string) {
    const response = await fetchWithTimeout(`${API_BASE_URL}/drift/${driftId}/revert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user })
    });

    return response.json();
  },

  /**
   * Health check
   */
  async health() {
    const response = await fetchWithTimeout(`${API_BASE_URL.replace('/api/v1', '')}/health`, {
      method: 'GET',
      retries: 0
    });

    return response.json();
  }
};

// ============================================================================
// Error Handler Utility
// ============================================================================

export function handleAPIError(error: any): string {
  if (error instanceof APIError) {
    return error.message;
  }

  if (error.name === 'AbortError') {
    return 'Request timed out. Please try again.';
  }

  if (error.message.includes('Failed to fetch')) {
    return 'Cannot connect to server. Please check your connection.';
  }

  return error.message || 'An unexpected error occurred';
}

// ============================================================================
// Export
// ============================================================================

export default apiClient;
