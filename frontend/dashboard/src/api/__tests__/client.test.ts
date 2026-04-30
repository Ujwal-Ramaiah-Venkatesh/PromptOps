import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '../client';

// Mock fetch
global.fetch = vi.fn();

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('GET requests', () => {
    it('makes GET request with correct URL', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('includes auth token in headers when available', async () => {
      localStorage.setItem('promptops_token', 'test-token');

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      });

      await apiClient.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });

    it('returns parsed JSON response', async () => {
      const mockData = { id: 1, name: 'test' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiClient.get('/test');

      expect(result).toEqual(mockData);
    });

    it('throws error on non-ok response', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      });

      await expect(apiClient.get('/test')).rejects.toThrow();
    });
  });

  describe('POST requests', () => {
    it('makes POST request with correct body', async () => {
      const postData = { email: 'test@example.com', password: 'pass' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await apiClient.post('/login', postData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
        })
      );
    });

    it('includes Content-Type header for POST', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await apiClient.post('/test', { data: 'test' });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });
  });

  describe('PUT requests', () => {
    it('makes PUT request with correct body', async () => {
      const putData = { id: 1, name: 'updated' };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => putData,
      });

      await apiClient.put('/resource/1', putData);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/resource/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData),
        })
      );
    });
  });

  describe('Error handling', () => {
    it('handles network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(apiClient.get('/test')).rejects.toThrow('Network error');
    });

    it('handles JSON parse errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(apiClient.get('/test')).rejects.toThrow();
    });

    it('handles 401 unauthorized', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      await expect(apiClient.get('/protected')).rejects.toThrow();
    });

    it('handles 500 server error', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      await expect(apiClient.get('/test')).rejects.toThrow();
    });
  });
});
