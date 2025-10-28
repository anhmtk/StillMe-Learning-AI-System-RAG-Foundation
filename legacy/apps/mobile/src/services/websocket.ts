// StillMe Mobile - WebSocket Service
import { EventEmitter } from 'events';
import { Platform } from 'react-native';
import DeviceInfo from 'react-native-device-info';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Types
import { Message, MessageType, ConnectionStatus } from '../../../shared/types';

interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
}

interface ClientInfo {
  deviceId: string;
  platform: string;
  version: string;
  appVersion: string;
}

export class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private clientInfo: ClientInfo;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private connectionStatus: ConnectionStatus = ConnectionStatus.DISCONNECTED;

  constructor() {
    super();
    this.config = {
      url: 'ws://localhost:8000/ws', // Default Gateway URL
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
    };
    this.clientInfo = {
      deviceId: '',
      platform: Platform.OS,
      version: Platform.Version.toString(),
      appVersion: '1.0.0',
    };
  }

  async initialize(): Promise<void> {
    try {
      // Get device ID
      this.clientInfo.deviceId = await DeviceInfo.getUniqueId();
      this.clientInfo.appVersion = await DeviceInfo.getVersion();

      // Load config from storage
      const savedConfig = await AsyncStorage.getItem('websocket_config');
      if (savedConfig) {
        this.config = { ...this.config, ...JSON.parse(savedConfig) };
      }

      // Connect to WebSocket
      await this.connect();
    } catch (error) {
      console.error('Failed to initialize WebSocket service:', error);
      this.emit('error', error);
    }
  }

  async connect(): Promise<void> {
    if (this.isConnecting || this.connectionStatus === ConnectionStatus.CONNECTED) {
      return;
    }

    this.isConnecting = true;
    this.connectionStatus = ConnectionStatus.CONNECTING;
    this.emit('status_change', this.connectionStatus);

    try {
      const wsUrl = `${this.config.url}/${this.clientInfo.deviceId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.connectionStatus = ConnectionStatus.CONNECTED;
        this.reconnectAttempts = 0;
        this.emit('connected');
        this.emit('status_change', this.connectionStatus);
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.connectionStatus = ConnectionStatus.DISCONNECTED;
        this.emit('disconnected', event);
        this.emit('status_change', this.connectionStatus);
        this.stopHeartbeat();
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.connectionStatus = ConnectionStatus.ERROR;
        this.emit('error', error);
        this.emit('status_change', this.connectionStatus);
      };

    } catch (error) {
      this.isConnecting = false;
      this.connectionStatus = ConnectionStatus.ERROR;
      this.emit('error', error);
      this.emit('status_change', this.connectionStatus);
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.stopReconnect();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.connectionStatus = ConnectionStatus.DISCONNECTED;
    this.emit('status_change', this.connectionStatus);
  }

  send(message: Message): boolean {
    if (this.ws && this.connectionStatus === ConnectionStatus.CONNECTED) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send message:', error);
        this.emit('error', error);
        return false;
      }
    }
    return false;
  }

  sendCommand(command: string, parameters: Record<string, any> = {}): boolean {
    const message: Message = {
      id: `cmd_${Date.now()}`,
      type: MessageType.COMMAND,
      timestamp: Date.now(),
      source: this.clientInfo.deviceId,
      command,
      parameters,
      context: {
        platform: this.clientInfo.platform,
        version: this.clientInfo.version,
        appVersion: this.clientInfo.appVersion,
      },
      async_execution: true,
      timeout: 300,
    };

    return this.send(message);
  }

  sendHeartbeat(): boolean {
    const message: Message = {
      id: `hb_${Date.now()}`,
      type: MessageType.HEARTBEAT,
      timestamp: Date.now(),
      source: this.clientInfo.deviceId,
      client_info: this.clientInfo,
      system_info: {
        platform: this.clientInfo.platform,
        version: this.clientInfo.version,
        appVersion: this.clientInfo.appVersion,
      },
      health_status: 'healthy',
      last_activity: Date.now(),
    };

    return this.send(message);
  }

  private handleMessage(message: any): void {
    console.log('Received message:', message);

    switch (message.type) {
      case 'heartbeat_ack':
        // Heartbeat acknowledged
        break;
      
      case 'command_received':
        this.emit('command_received', message);
        break;
      
      case 'command_response':
        this.emit('command_response', message);
        break;
      
      case 'status_update':
        this.emit('status_update', message);
        break;
      
      case 'notification':
        this.emit('notification', message);
        break;
      
      case 'error':
        this.emit('error', message);
        break;
      
      default:
        this.emit('message', message);
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      this.emit('max_reconnect_attempts_reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${this.config.reconnectInterval}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.config.reconnectInterval);
  }

  private stopReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // Getters
  get isConnected(): boolean {
    return this.connectionStatus === ConnectionStatus.CONNECTED;
  }

  get status(): ConnectionStatus {
    return this.connectionStatus;
  }

  get deviceId(): string {
    return this.clientInfo.deviceId;
  }

  // Configuration
  async updateConfig(newConfig: Partial<WebSocketConfig>): Promise<void> {
    this.config = { ...this.config, ...newConfig };
    await AsyncStorage.setItem('websocket_config', JSON.stringify(this.config));
  }

  async getConfig(): Promise<WebSocketConfig> {
    return { ...this.config };
  }
}
