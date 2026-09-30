/**
 * WebSocket Client Manager
 * =========================
 *
 * Manages WebSocket connection to backend with auto-reconnect,
 * authentication, and event handling.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - JWT authentication
 * - Event subscription/unsubscription
 * - Connection state management
 * - Heartbeat monitoring
 *
 * @author PromptOps Team - Q3 2026
 * @date July 8, 2026
 */

export enum ConnectionState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTING = 'DISCONNECTING',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  ERROR = 'ERROR',
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}

export interface WebSocketConfig {
  url: string;
  token: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  debug?: boolean;
}

type MessageHandler = (message: WebSocketMessage) => void;
type StateChangeHandler = (state: ConnectionState) => void;

export class WSClient {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private lastPingTime: number = 0;

  // Event handlers
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private stateChangeHandlers: Set<StateChangeHandler> = new Set();

  constructor(config: WebSocketConfig) {
    this.config = {
      autoReconnect: true,
      maxReconnectAttempts: 5,
      reconnectInterval: 3000,
      heartbeatInterval: 30000,
      debug: false,
      ...config,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.log('Already connected');
      return;
    }

    this.setState(ConnectionState.CONNECTING);
    this.log('Connecting to WebSocket...');

    try {
      // Build WebSocket URL with token
      const wsUrl = `${this.config.url}?token=${encodeURIComponent(this.config.token)}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      this.log('Connection error:', error);
      this.setState(ConnectionState.ERROR);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.log('Disconnecting...');
    this.setState(ConnectionState.DISCONNECTING);

    // Clear timers
    this.clearReconnectTimer();
    this.clearHeartbeatTimer();

    // Close WebSocket
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
  }

  /**
   * Send message to server
   */
  send(message: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.log('Cannot send message: Not connected');
      return;
    }

    try {
      const payload = typeof message === 'string'
        ? message
        : JSON.stringify(message);

      this.ws.send(payload);
      this.log('Sent message:', message);
    } catch (error) {
      this.log('Error sending message:', error);
    }
  }

  /**
   * Subscribe to specific event type
   */
  subscribe(eventType: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, new Set());
    }

    this.messageHandlers.get(eventType)!.add(handler);
    this.log(`Subscribed to ${eventType}`);

    // Send subscription message to server
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send({
        type: 'subscribe',
        events: [eventType],
      });
    }

    // Return unsubscribe function
    return () => this.unsubscribe(eventType, handler);
  }

  /**
   * Unsubscribe from specific event type
   */
  unsubscribe(eventType: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);

      if (handlers.size === 0) {
        this.messageHandlers.delete(eventType);

        // Send unsubscription message to server
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.send({
            type: 'unsubscribe',
            events: [eventType],
          });
        }
      }

      this.log(`Unsubscribed from ${eventType}`);
    }
  }

  /**
   * Add state change listener
   */
  onStateChange(handler: StateChangeHandler): () => void {
    this.stateChangeHandlers.add(handler);

    // Return function to remove listener
    return () => this.stateChangeHandlers.delete(handler);
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === ConnectionState.CONNECTED &&
           this.ws?.readyState === WebSocket.OPEN;
  }

  // ============================================================================
  // Private Methods
  // ============================================================================

  private handleOpen(): void {
    this.log('WebSocket connected');
    this.setState(ConnectionState.CONNECTED);
    this.reconnectAttempts = 0;

    // Start heartbeat
    this.startHeartbeat();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.log('Received message:', message);

      // Handle special message types
      if (message.type === 'ping') {
        // Respond with pong
        this.send({ type: 'pong', timestamp: new Date().toISOString() });
        return;
      }

      if (message.type === 'connected') {
        this.log('Connection acknowledged by server');
        return;
      }

      // Dispatch to handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            this.log('Error in message handler:', error);
          }
        });
      }

      // Also dispatch to wildcard handlers
      const wildcardHandlers = this.messageHandlers.get('*');
      if (wildcardHandlers) {
        wildcardHandlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            this.log('Error in wildcard handler:', error);
          }
        });
      }
    } catch (error) {
      this.log('Error parsing message:', error);
    }
  }

  private handleError(event: Event): void {
    this.log('WebSocket error:', event);
    this.setState(ConnectionState.ERROR);
  }

  private handleClose(event: CloseEvent): void {
    this.log(`WebSocket closed (code: ${event.code}, reason: ${event.reason})`);

    this.clearHeartbeatTimer();
    this.ws = null;

    if (event.code === 1000) {
      // Normal closure
      this.setState(ConnectionState.DISCONNECTED);
    } else {
      // Abnormal closure, attempt reconnect
      this.setState(ConnectionState.DISCONNECTED);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (!this.config.autoReconnect) {
      this.log('Auto-reconnect disabled');
      return;
    }

    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnect attempts reached');
      this.setState(ConnectionState.ERROR);
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);

    this.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    this.setState(ConnectionState.RECONNECTING);

    this.reconnectTimer = setTimeout(() => {
      this.log(`Reconnect attempt ${this.reconnectAttempts}`);
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.clearHeartbeatTimer();

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.lastPingTime = Date.now();
        // Server sends ping, we respond with pong
        // No need to send ping from client
      }
    }, this.config.heartbeatInterval);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private clearHeartbeatTimer(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.log(`State change: ${this.state} -> ${newState}`);
      this.state = newState;

      // Notify listeners
      this.stateChangeHandlers.forEach(handler => {
        try {
          handler(newState);
        } catch (error) {
          this.log('Error in state change handler:', error);
        }
      });
    }
  }

  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[WSClient]', ...args);
    }
  }
}

// Singleton instance
let wsClientInstance: WSClient | null = null;

/**
 * Get or create WebSocket client instance
 */
export function getWSClient(config?: WebSocketConfig): WSClient {
  if (!wsClientInstance && config) {
    wsClientInstance = new WSClient(config);
  }

  if (!wsClientInstance) {
    throw new Error('WebSocket client not initialized. Provide config on first call.');
  }

  return wsClientInstance;
}

/**
 * Reset WebSocket client (useful for testing)
 */
export function resetWSClient(): void {
  if (wsClientInstance) {
    wsClientInstance.disconnect();
    wsClientInstance = null;
  }
}
