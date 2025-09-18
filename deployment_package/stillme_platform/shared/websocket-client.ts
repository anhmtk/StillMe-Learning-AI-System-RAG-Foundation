// StillMe Platform - WebSocket Client
/**
 * Universal WebSocket client for StillMe multi-platform system
 */

import { EventEmitter } from 'events';
import { Message, MessageType, ConnectionStatus, ConnectionType } from './types';

export interface WebSocketClientConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  timeout?: number;
  protocols?: string[];
}

export class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: WebSocketClientConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private status: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private messageQueue: Message[] = [];

  constructor(config: WebSocketClientConfig) {
    super();
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      timeout: 10000,
      ...config,
    };
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.setStatus(ConnectionStatus.CONNECTING);
        
        this.ws = new WebSocket(this.config.url, this.config.protocols);
        
        const timeout = setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('Connection timeout'));
          }
        }, this.config.timeout);

        this.ws.onopen = () => {
          clearTimeout(timeout);
          this.setStatus(ConnectionStatus.CONNECTED);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.processMessageQueue();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          clearTimeout(timeout);
          this.setStatus(ConnectionStatus.DISCONNECTED);
          this.stopHeartbeat();
          this.emit('disconnected', event);
          
          if (!event.wasClean && this.reconnectAttempts < this.config.maxReconnectAttempts!) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          this.setStatus(ConnectionStatus.ERROR);
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.clearReconnectTimer();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.setStatus(ConnectionStatus.DISCONNECTED);
  }

  async sendMessage(message: Message): Promise<void> {
    if (this.status === ConnectionStatus.CONNECTED && this.ws) {
      try {
        const data = JSON.stringify(message);
        this.ws.send(data);
        this.emit('message_sent', message);
      } catch (error) {
        this.emit('error', error);
        throw error;
      }
    } else {
      // Queue message for later
      this.messageQueue.push(message);
      this.emit('message_queued', message);
    }
  }

  async sendCommand(command: string, parameters: Record<string, any> = {}): Promise<void> {
    const message: Message = {
      id: this.generateMessageId(),
      type: MessageType.COMMAND,
      timestamp: Date.now(),
      source: 'client',
      command,
      parameters,
      context: {},
      async_execution: true,
      timeout: 300,
    };

    return this.sendMessage(message);
  }

  async sendHeartbeat(): Promise<void> {
    const message: Message = {
      id: this.generateMessageId(),
      type: MessageType.HEARTBEAT,
      timestamp: Date.now(),
      source: 'client',
      client_info: this.getClientInfo(),
      system_info: this.getSystemInfo(),
      health_status: 'healthy',
    };

    return this.sendMessage(message);
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      const message = data as Message;
      
      this.emit('message', message);
      
      // Handle specific message types
      switch (message.type) {
        case MessageType.HEARTBEAT:
          this.emit('heartbeat', message);
          break;
        case MessageType.NOTIFICATION:
          this.emit('notification', message);
          break;
        case MessageType.STATUS:
          this.emit('status', message);
          break;
        case MessageType.RESPONSE:
          this.emit('response', message);
          break;
        case MessageType.ERROR:
          this.emit('error_message', message);
          break;
      }
    } catch (error) {
      this.emit('error', new Error(`Failed to parse message: ${error}`));
    }
  }

  private setStatus(status: ConnectionStatus): void {
    if (this.status !== status) {
      this.status = status;
      this.emit('status_change', status);
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.status === ConnectionStatus.CONNECTED) {
        this.sendHeartbeat().catch((error) => {
          this.emit('error', error);
        });
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    
    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval! * Math.pow(2, this.reconnectAttempts - 1);
    
    this.reconnectTimer = setTimeout(() => {
      this.emit('reconnecting', this.reconnectAttempts);
      this.connect().catch((error) => {
        this.emit('error', error);
      });
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.status === ConnectionStatus.CONNECTED) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message).catch((error) => {
          this.emit('error', error);
        });
      }
    }
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getClientInfo(): Record<string, any> {
    return {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Node.js',
      platform: typeof navigator !== 'undefined' ? navigator.platform : process.platform,
      language: typeof navigator !== 'undefined' ? navigator.language : 'en',
      timestamp: Date.now(),
    };
  }

  private getSystemInfo(): Record<string, any> {
    return {
      memory: typeof performance !== 'undefined' && performance.memory ? {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit,
      } : undefined,
      timestamp: Date.now(),
    };
  }

  // Public getters
  get isConnected(): boolean {
    return this.status === ConnectionStatus.CONNECTED;
  }

  get connectionStatus(): ConnectionStatus {
    return this.status;
  }

  get queuedMessages(): number {
    return this.messageQueue.length;
  }

  get reconnectAttempts(): number {
    return this.reconnectAttempts;
  }
}

