/**
 * WebSocket Hook for Real-Time Updates
 * =====================================
 *
 * Custom React hook for WebSocket connection management.
 *
 * Author: PromptOps Team
 * Date: 2026-04-30
 * Phase: 2 - Real-Time Updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  send: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
  reconnectAttempts: number;
}

/**
 * Custom hook for WebSocket connection with auto-reconnect.
 *
 * @example
 * ```typescript
 * const { isConnected, send, lastMessage } = useWebSocket({
 *   url: 'ws://localhost:8000/ws/user-123',
 *   autoConnect: true,
 *   onMessage: (msg) => console.log('Received:', msg)
 * });
 *
 * // Subscribe to scan updates
 * send({ action: 'subscribe', scan_id: 'scan_123' });
 * ```
 */
export function useWebSocket({
  url,
  autoConnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  /**
   * Send message through WebSocket.
   */
  const send = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected. Message not sent:', message);
    }
  }, []);

  /**
   * Connect to WebSocket server.
   */
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      console.log(`[WebSocket] Connecting to ${url}...`);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setIsConnected(true);
        setReconnectAttempts(0);
        shouldReconnectRef.current = true;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);
        wsRef.current = null;
        onDisconnect?.();

        // Attempt reconnect if enabled
        if (shouldReconnectRef.current && reconnectAttempts < maxReconnectAttempts) {
          console.log(`[WebSocket] Reconnecting in ${reconnectInterval}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error('[WebSocket] Max reconnect attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
    }
  }, [url, reconnectAttempts, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onError, onMessage]);

  /**
   * Disconnect from WebSocket server.
   */
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Auto-connect on mount if enabled.
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoConnect, connect]);

  return {
    isConnected,
    send,
    connect,
    disconnect,
    lastMessage,
    reconnectAttempts,
  };
}

/**
 * Hook for subscribing to scan updates.
 */
export function useScanUpdates(scanId: string | null, connectionId: string) {
  const [scanStatus, setScanStatus] = useState<any>(null);
  const [progress, setProgress] = useState(0);

  const { isConnected, send, lastMessage } = useWebSocket({
    url: `ws://localhost:8000/ws/${connectionId}`,
    autoConnect: true,
    onConnect: () => {
      console.log('[Scan] WebSocket connected');
      // Subscribe to scan updates when connected
      if (scanId) {
        send({ action: 'subscribe', scan_id: scanId });
      }
    },
    onMessage: (message) => {
      if (message.type === 'scan_update' && message.scan_id === scanId) {
        setScanStatus(message);
        setProgress(message.progress || 0);
      }
    },
  });

  // Subscribe when scanId changes
  useEffect(() => {
    if (isConnected && scanId) {
      send({ action: 'subscribe', scan_id: scanId });
    }
  }, [scanId, isConnected, send]);

  return {
    isConnected,
    scanStatus,
    progress,
    send,
  };
}

/**
 * Hook for real-time notifications.
 */
export function useNotifications(connectionId: string) {
  const [notifications, setNotifications] = useState<any[]>([]);

  const { isConnected } = useWebSocket({
    url: `ws://localhost:8000/ws/${connectionId}`,
    autoConnect: true,
    onMessage: (message) => {
      if (message.type === 'notification') {
        setNotifications((prev) => [message, ...prev].slice(0, 50)); // Keep last 50
      }
    },
  });

  const clearNotifications = () => setNotifications([]);

  return {
    isConnected,
    notifications,
    clearNotifications,
  };
}
